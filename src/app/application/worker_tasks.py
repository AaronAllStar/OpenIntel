import asyncio
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from src.adapters.osint_executor import execute_adapters, get_adapters_for_target
from src.app.application.normalizer import EntityNormalizer
from src.app.domain.enums import InvestigationStatus, TargetKind
from src.app.domain.ports.adapter import (
    AdapterInput,
    AdapterOptions,
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


def _execute_investigation_sync(investigation_id_str: str) -> None:
    investigation_id = UUID(investigation_id_str)
    db: Session = SessionLocal()

    try:
        inv: InvestigationModel | None = db.query(InvestigationModel).filter_by(id=investigation_id).first()
        if not inv:
            logger.error("Investigation not found in worker", id=investigation_id_str)
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
        cancel_event = asyncio.Event()

        async def _run_all() -> None:
            async for event in execute_adapters(
                adapters=adapters,
                adapter_input=adapter_input,
                cancel_event=cancel_event,
                max_concurrency=inv.settings.get("concurrency", 2),
            ):
                match event:
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
                        rel_model = normalizer.normalize_relationship(rel)
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

        asyncio.run(_run_all())

        inv.status = InvestigationStatus.REVIEW.value
        inv.finished_at = datetime.now(UTC)
        db.commit()

        publish_event_sync(investigation_id_str, {
            "type": "completed",
            "status": InvestigationStatus.REVIEW.value,
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
        db.close()


@celery_app.task(name="run_investigation_task")
def run_investigation_task(investigation_id_str: str) -> None:
    _execute_investigation_sync(investigation_id_str)
