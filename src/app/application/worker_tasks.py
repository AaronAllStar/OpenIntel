import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.adapters.osint_executor import execute_adapters, get_adapters_for_target
from src.app.application.cancellation_manager import cancellation_manager
from src.app.application.normalizer import EntityNormalizer
from src.app.domain.enums import InvestigationStatus, TargetKind
from src.app.domain.ports.adapter import (
    AdapterInput,
    AdapterOptions,
    EngineStatusEvent,
    EntityEvent,
    ErrorEvent,
    LogEvent,
    ProgressEvent,
    RelationshipEvent,
)
from src.app.domain.value_objects import Target
from src.app.infrastructure.celery_app import celery_app
from src.app.infrastructure.database import SessionLocal
from src.app.infrastructure.logging import logger
from src.app.infrastructure.models import InvestigationModel
from src.app.infrastructure.redis_bus import publish_event_sync


async def execute_investigation_async(investigation_id_str: str) -> None:
    """
    Main asynchronous investigation worker loop.
    Enforces per-engine isolation, timeout limits, in-flight cancellation,
    relational database consistency, and per-engine status tracking.
    """
    investigation_id = UUID(investigation_id_str)
    db: Session = SessionLocal()
    cancel_event = cancellation_manager.get_or_create(investigation_id_str)
    engine_statuses: dict[str, str] = {}
    inv: InvestigationModel | None = None

    try:
        inv = db.query(InvestigationModel).filter_by(id=investigation_id).first()
        if not inv:
            logger.error("Investigation not found in worker", id=investigation_id_str)
            return

        # Check if already cancelled
        if cancel_event.is_set():
            inv.status = InvestigationStatus.CANCELLED.value
            inv.finished_at = datetime.now(UTC)
            db.commit()
            publish_event_sync(investigation_id_str, {
                "type": "cancelled",
                "status": inv.status,
                "message": "Investigation cancelled prior to start",
            })
            return

        inv.status = InvestigationStatus.RUNNING.value
        inv.started_at = datetime.now(UTC)
        db.commit()

        publish_event_sync(investigation_id_str, {
            "type": "progress",
            "step": "Investigation started",
            "pct": 5.0,
            "status": inv.status,
        })

        target_obj = Target(
            kind=TargetKind(inv.target_kind),
            value=inv.target_value,
            allow_private=inv.settings.get("allow_private_targets", False),
        )

        selected_engines = inv.settings.get("selected_engines", [])
        adapters = get_adapters_for_target(target_obj.kind, selected_engines)

        adapter_input = AdapterInput(
            target=target_obj,
            investigation_id=investigation_id,
            options=AdapterOptions(
                timeout_ms=inv.settings.get("timeout_ms", 30000),
                max_results=inv.settings.get("max_results", 500),
                depth=inv.settings.get("depth", 1),
            ),
        )

        inv.status = InvestigationStatus.WORKING.value
        db.commit()

        normalizer = EntityNormalizer(investigation_id)

        async for event in execute_adapters(
            adapters=adapters,
            adapter_input=adapter_input,
            cancel_event=cancel_event,
            max_concurrency=inv.settings.get("concurrency", 2),
        ):
            # Check for cancellation during streaming
            if cancel_event.is_set():
                break

            match event:
                case EngineStatusEvent(engine=eng, status=st, duration_ms=dur, error=err):
                    engine_statuses[eng] = st
                    publish_event_sync(investigation_id_str, {
                        "type": "engine_status",
                        "engine": eng,
                        "status": st,
                        "duration_ms": dur,
                        "error": err,
                    })

                case ProgressEvent(step=s, pct=p):
                    publish_event_sync(investigation_id_str, {
                        "type": "progress",
                        "step": s,
                        "pct": p,
                    })

                case EntityEvent(entity=e, evidence=ev):
                    ent_model, is_new = normalizer.normalize_entity(e)
                    if is_new:
                        db.add(ent_model)
                        db.flush()

                    ev_model = normalizer.create_evidence(ev, entity_id=ent_model.id)
                    db.add(ev_model)
                    db.commit()

                    publish_event_sync(investigation_id_str, {
                        "type": "entity",
                        "entity": {
                            "id": str(ent_model.id),
                            "kind": ent_model.kind,
                            "value": ent_model.value,
                            "confidence": ent_model.confidence,
                            "attributes": ent_model.attributes,
                        },
                        "evidence": {
                            "id": str(ev_model.id),
                            "source": ev_model.source,
                            "tool": ev_model.tool,
                            "confidence": ev_model.confidence,
                            "info_classification": ev_model.info_classification,
                        },
                    })

                case RelationshipEvent(relationship=rel, evidence=ev):
                    rel_model, new_entities = normalizer.normalize_relationship(rel)

                    # Ensure any auto-created endpoints are persisted prior to relationship
                    for new_ent in new_entities:
                        db.add(new_ent)
                    if new_entities:
                        db.flush()

                    if rel_model:
                        db.add(rel_model)
                        db.commit()

                        publish_event_sync(investigation_id_str, {
                            "type": "relationship",
                            "relationship": {
                                "id": str(rel_model.id),
                                "source_id": str(rel_model.source_entity_id),
                                "target_id": str(rel_model.target_entity_id),
                                "predicate": rel_model.predicate,
                                "confidence": rel_model.confidence,
                                "reasoning": rel_model.reasoning,
                            },
                        })

                case LogEvent(level=lvl, message=msg):
                    publish_event_sync(investigation_id_str, {
                        "type": "log",
                        "level": lvl,
                        "message": msg,
                    })

                case ErrorEvent(error=err):
                    publish_event_sync(investigation_id_str, {
                        "type": "error",
                        "message": str(err),
                    })

        # Finalize investigation status
        inv = db.query(InvestigationModel).filter_by(id=investigation_id).first()
        if inv:
            # Store per-engine execution statuses in settings
            updated_settings = dict(inv.settings) if inv.settings else {}
            updated_settings["engine_statuses"] = engine_statuses
            inv.settings = updated_settings

            if cancel_event.is_set():
                inv.status = InvestigationStatus.CANCELLED.value
                inv.finished_at = datetime.now(UTC)
                db.commit()
                publish_event_sync(investigation_id_str, {
                    "type": "cancelled",
                    "status": InvestigationStatus.CANCELLED.value,
                    "engine_statuses": engine_statuses,
                    "message": "Investigation cancelled by user request",
                })
            else:
                inv.status = InvestigationStatus.REVIEW.value
                inv.finished_at = datetime.now(UTC)
                db.commit()
                publish_event_sync(investigation_id_str, {
                    "type": "completed",
                    "status": InvestigationStatus.REVIEW.value,
                    "engine_statuses": engine_statuses,
                    "message": "Investigation completed and ready for review",
                })

    except Exception as exc:
        logger.exception("Investigation worker task failed", error=str(exc))
        if inv:
            inv.status = InvestigationStatus.ERROR.value
            inv.error_message = str(exc)
            inv.finished_at = datetime.now(UTC)
            db.commit()
        publish_event_sync(investigation_id_str, {
            "type": "error",
            "message": f"Execution error: {exc}",
            "status": InvestigationStatus.ERROR.value,
        })
    finally:
        cancellation_manager.remove(investigation_id_str)
        db.close()


def _execute_investigation_sync(investigation_id_str: str) -> None:
    """Synchronous entry point called by Celery workers or background threads."""
    asyncio.run(execute_investigation_async(investigation_id_str))


@celery_app.task(name="run_investigation_task")
def run_investigation_task(investigation_id_str: str) -> None:
    _execute_investigation_sync(investigation_id_str)
