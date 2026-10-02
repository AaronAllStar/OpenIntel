from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from src.app.api.middleware.auth import UserPrincipal, get_current_user, require_role
from src.app.application.audit_service import AuditService
from src.app.infrastructure.database import get_db

router = APIRouter(prefix="", tags=["governance"])


@router.get("/audit", dependencies=[Depends(require_role("admin"))])
def list_audit_trail(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: str | None = Query(None, description="Filter by audit action"),
    user_id: str | None = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    _user: UserPrincipal = Depends(get_current_user),
) -> list[dict]:
    """Admin-only endpoint retrieving immutable audit log records."""
    return AuditService.list_audit_logs(db=db, skip=skip, limit=limit, action=action, user_id=user_id)


@router.get("/legal/notice")
def get_legal_ethical_notice() -> dict:
    """Returns the mandatory OpenIntel Ethical and Authorized Use Charter."""
    return {
        "title": "OpenIntel Ethical & Authorized Use Charter",
        "version": "1.0",
        "summary": "OpenIntel is designed strictly for defensive cybersecurity, authorized threat intelligence, academic research, and lawful investigative purposes.",
        "requirements": [
            "You must possess verified authorization or documented legitimate investigative authority for all queried targets.",
            "Targeting private individuals without authorization, harassment, stalking, and bulk harvesting of personal data are strictly prohibited.",
            "All queries are immutably logged with source IP, timestamp, user principal, and target parameters.",
            "OpenIntel strictly adheres to CFAA (Computer Fraud and Abuse Act), GDPR Data Minimization principles, and regional privacy frameworks.",
        ],
        "compliance": {
            "cfaa_compliant": True,
            "gdpr_article_5_minimization": True,
            "provenance_tracking": True,
        },
    }
