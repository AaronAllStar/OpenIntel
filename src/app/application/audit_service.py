from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from src.app.infrastructure.logging import logger
from src.app.infrastructure.models import AuditLogModel


class AuditService:
    """
    Immutable audit logging service.
    Tracks all security-critical operations, investigation access, exports, and administration.
    """

    @staticmethod
    def record_audit_event(
        db: Session,
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: str = "anonymous",
        role: str = "analyst",
        ip_address: str = "127.0.0.1",
        status: str = "SUCCESS",
        details: dict[str, Any] | None = None,
    ) -> AuditLogModel:
        audit_entry = AuditLogModel(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            user_id=user_id,
            role=role,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            status=status,
            details_json=details or {},
        )
        db.add(audit_entry)
        db.commit()
        logger.info(
            "Audit event recorded",
            action=action,
            user_id=user_id,
            resource=f"{resource_type}:{resource_id}",
            status=status,
        )
        return audit_entry

    @staticmethod
    def list_audit_logs(
        db: Session,
        skip: int = 0,
        limit: int = 50,
        action: str | None = None,
        user_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query = db.query(AuditLogModel).order_by(AuditLogModel.timestamp.desc())
        if action:
            query = query.filter(AuditLogModel.action == action)
        if user_id:
            query = query.filter(AuditLogModel.user_id == user_id)

        rows = query.offset(skip).limit(limit).all()
        return [
            {
                "id": str(r.id),
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "user_id": r.user_id,
                "role": r.role,
                "action": r.action,
                "resource_type": r.resource_type,
                "resource_id": r.resource_id,
                "ip_address": r.ip_address,
                "status": r.status,
                "details": r.details_json,
            }
            for r in rows
        ]
