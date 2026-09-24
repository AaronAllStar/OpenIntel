import threading
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from src.app.application.worker_tasks import _execute_investigation_sync, run_investigation_task
from src.app.domain.enums import InvestigationStatus, InvestigationType, TargetKind
from src.app.domain.errors import InvestigationNotFoundError
from src.app.domain.value_objects import Target
from src.app.infrastructure.logging import logger
from src.app.infrastructure.models import (
    InvestigationModel,
)


class InvestigationService:

    @staticmethod
    def create_investigation(
        db: Session,
        name: str,
        target_kind: TargetKind,
        target_value: str,
        investigation_type: InvestigationType = InvestigationType.QUICK,
        settings: dict[str, Any] | None = None,
        created_by: UUID | None = None,
    ) -> InvestigationModel:
        # Strict domain validation
        allow_private = (settings or {}).get("allow_private_targets", False)
        valid_target = Target(kind=target_kind, value=target_value, allow_private=allow_private)

        inv = InvestigationModel(
            id=uuid4(),
            name=name or f"Investigation of {valid_target.value}",
            target_kind=valid_target.kind.value,
            target_value=valid_target.value,
            investigation_type=investigation_type.value,
            status=InvestigationStatus.PENDING.value,
            created_at=datetime.now(UTC),
            created_by=created_by or uuid4(),
            settings=settings or {},
        )

        db.add(inv)
        db.commit()
        db.refresh(inv)

        # Dispatch execution
        inv_id_str = str(inv.id)
        from src.app.infrastructure.config import get_settings
        current_settings = get_settings()

        if current_settings.ENV != "test":
            try:
                run_investigation_task.delay(inv_id_str)
                logger.info("Dispatched investigation to Celery worker", id=inv_id_str)
            except Exception as exc:
                logger.info("Celery broker unavailable, running via local background worker", error=str(exc))
                t = threading.Thread(target=_execute_investigation_sync, args=(inv_id_str,), daemon=True)
                t.start()

        return inv

    @staticmethod
    def list_investigations(
        db: Session,
        skip: int = 0,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        records = (
            db.query(InvestigationModel)
            .order_by(InvestigationModel.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        results = []
        for inv in records:
            results.append({
                "id": str(inv.id),
                "name": inv.name,
                "target_kind": inv.target_kind,
                "target_value": inv.target_value,
                "type": inv.investigation_type,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None,
                "started_at": inv.started_at.isoformat() if inv.started_at else None,
                "finished_at": inv.finished_at.isoformat() if inv.finished_at else None,
                "entities_count": len(inv.entities),
                "evidence_count": len(inv.evidence),
                "relationships_count": len(inv.relationships),
            })
        return results

    @staticmethod
    def get_investigation_detail(db: Session, investigation_id: UUID) -> dict[str, Any]:
        inv: InvestigationModel | None = (
            db.query(InvestigationModel).filter_by(id=investigation_id).first()
        )
        if not inv:
            raise InvestigationNotFoundError(f"Investigation {investigation_id} not found")

        return {
            "id": str(inv.id),
            "name": inv.name,
            "target_kind": inv.target_kind,
            "target_value": inv.target_value,
            "type": inv.investigation_type,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "started_at": inv.started_at.isoformat() if inv.started_at else None,
            "finished_at": inv.finished_at.isoformat() if inv.finished_at else None,
            "settings": inv.settings,
            "error_message": inv.error_message,
            "entities": [
                {
                    "id": str(e.id),
                    "kind": e.kind,
                    "value": e.value,
                    "confidence": e.confidence,
                    "attributes": e.attributes,
                    "first_seen": e.first_seen.isoformat() if e.first_seen else None,
                }
                for e in inv.entities
            ],
            "evidence": [
                {
                    "id": str(ev.id),
                    "entity_id": str(ev.entity_id) if ev.entity_id else None,
                    "source": ev.source,
                    "tool": ev.tool,
                    "timestamp": ev.timestamp.isoformat() if ev.timestamp else None,
                    "raw_observation": ev.raw_observation,
                    "confidence": ev.confidence,
                    "info_classification": getattr(ev, "info_classification", "PUBLIC_OBSERVATION"),
                    "metadata": ev.metadata_json,
                }
                for ev in inv.evidence
            ],
            "relationships": [
                {
                    "id": str(r.id),
                    "source_entity_id": str(r.source_entity_id),
                    "target_entity_id": str(r.target_entity_id),
                    "predicate": r.predicate,
                    "confidence": r.confidence,
                    "reasoning": r.reasoning,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in inv.relationships
            ],
        }

    @staticmethod
    def cancel_investigation(db: Session, investigation_id: UUID) -> bool:
        inv: InvestigationModel | None = (
            db.query(InvestigationModel).filter_by(id=investigation_id).first()
        )
        if not inv:
            raise InvestigationNotFoundError(f"Investigation {investigation_id} not found")

        if inv.status in (InvestigationStatus.PENDING.value, InvestigationStatus.RUNNING.value, InvestigationStatus.WORKING.value):
            inv.status = InvestigationStatus.CANCELLED.value
            inv.finished_at = datetime.now(UTC)
            db.commit()
            return True
        return False

    @staticmethod
    def export_report_markdown(db: Session, investigation_id: UUID) -> str:
        detail = InvestigationService.get_investigation_detail(db, investigation_id)

        lines = [
            f"# OpenIntel Investigation Report: {detail['name']}",
            "",
            "## Summary",
            f"- **Target**: `{detail['target_value']}` ({detail['target_kind']})",
            f"- **Type**: `{detail['type']}`",
            f"- **Status**: `{detail['status']}`",
            f"- **Date**: {detail['created_at']}",
            f"- **Total Entities**: {len(detail['entities'])}",
            f"- **Total Evidence Items**: {len(detail['evidence'])}",
            f"- **Total Relationships**: {len(detail['relationships'])}",
            "",
            "## Discovered Entities",
            "| Kind | Value | Confidence |",
            "|---|---|---|",
        ]

        for e in detail["entities"]:
            lines.append(f"| {e['kind']} | `{e['value']}` | {e['confidence']} |")

        lines.extend([
            "",
            "## Relationships",
            "| Subject ID | Predicate | Object ID | Confidence | Reasoning |",
            "|---|---|---|---|---|",
        ])

        for r in detail["relationships"]:
            lines.append(f"| `{r['source_entity_id'][:8]}` | {r['predicate']} | `{r['target_entity_id'][:8]}` | {r['confidence']} | {r['reasoning']} |")

        lines.extend([
            "",
            "## Evidence Provenance & Classification",
            "| Source | Tool | Classification | Confidence | Timestamp | Raw Observation |",
            "|---|---|---|---|---|---|",
        ])

        for ev in detail["evidence"]:
            obs_preview = ev["raw_observation"].replace("\n", " ")[:80]
            classification = ev.get("info_classification", "PUBLIC_OBSERVATION")
            lines.append(f"| {ev['source']} | {ev['tool']} | `{classification}` | {ev['confidence']} | {ev['timestamp']} | `{obs_preview}` |")

        lines.extend([
            "",
            "---",
            "*Generated by OpenIntel*",
        ])

        return "\n".join(lines)
