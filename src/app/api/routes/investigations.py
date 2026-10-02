import json
from collections.abc import AsyncIterator
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from src.app.api.middleware.rate_limiter import RateLimiter
from src.app.application.investigation_service import InvestigationService
from src.app.domain.errors import InvestigationNotFoundError, ValidationError
from src.app.infrastructure.database import get_db
from src.app.infrastructure.redis_bus import subscribe_events_async
from src.schemas.investigation import (
    CreateInvestigationRequest,
    EvidenceResponse,
    GraphResponse,
    InvestigationDetailResponse,
    InvestigationListItemResponse,
)

router = APIRouter(prefix="/investigations", tags=["investigations"])

create_rate_limiter = RateLimiter(times=10, seconds=60, key_prefix="create_inv")
export_rate_limiter = RateLimiter(times=30, seconds=60, key_prefix="export_inv")


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=dict,
    dependencies=[Depends(create_rate_limiter)],
)
def create_investigation(
    payload: CreateInvestigationRequest,
    db: Session = Depends(get_db),
) -> dict:

    try:
        inv = InvestigationService.create_investigation(
            db=db,
            name=payload.name or "",
            target_kind=payload.target_kind,
            target_value=payload.target_value,
            investigation_type=payload.investigation_type,
            settings=payload.settings,
        )
        return {
            "id": str(inv.id),
            "name": inv.name,
            "status": inv.status,
            "target_kind": inv.target_kind,
            "target_value": inv.target_value,
        }
    except ValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[InvestigationListItemResponse])
def list_investigations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[dict]:
    return InvestigationService.list_investigations(db, skip=skip, limit=limit)


@router.get("/{investigation_id}", response_model=InvestigationDetailResponse)
def get_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    try:
        return InvestigationService.get_investigation_detail(db, investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{investigation_id}/events")
async def stream_investigation_events(
    investigation_id: UUID,
    since_seq: int | None = Query(None, ge=0, description="Sequence cursor to resume missed events from"),
    last_event_id: str | None = Header(None, alias="Last-Event-ID", description="Standard SSE event cursor"),
) -> EventSourceResponse:
    """Streams live real-time investigation events via Server-Sent Events (SSE) with replay support."""
    cursor = 0
    if since_seq is not None:
        cursor = max(0, since_seq)
    elif last_event_id is not None:
        try:
            cursor = max(0, int(last_event_id))
        except ValueError:
            cursor = 0

    async def event_generator() -> AsyncIterator[dict]:
        # Initial ping / connected handshake with acknowledged cursor
        yield {
            "id": str(cursor),
            "event": "connected",
            "data": json.dumps({"investigation_id": str(investigation_id), "cursor": cursor}),
        }

        async for event in subscribe_events_async(str(investigation_id), since_seq=cursor):
            event_type = event.get("type", "update")
            seq = event.get("seq", 0)
            yield {
                "id": str(seq),
                "event": event_type,
                "data": json.dumps(event),
            }
            if event_type in ("completed", "error"):
                break

    return EventSourceResponse(event_generator())


@router.post("/{investigation_id}/cancel")
def cancel_investigation(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    try:
        success = InvestigationService.cancel_investigation(db, investigation_id)
        return {"cancelled": success}
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{investigation_id}/graph", response_model=GraphResponse)
def get_investigation_graph(
    investigation_id: UUID,
    db: Session = Depends(get_db),
) -> dict:
    """
    High-performance graph retrieval endpoint (p95 < 200ms for 10,000+ nodes).
    Returns complete nodes, edges, and direct evidence provenance links with 0 N+1 queries.
    """
    try:
        return InvestigationService.get_graph(db, investigation_id)
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{investigation_id}/provenance", response_model=list[EvidenceResponse])
def get_investigation_provenance(
    investigation_id: UUID,
    entity_id: UUID | None = Query(None, description="Optional entity ID filter"),
    relationship_id: UUID | None = Query(None, description="Optional relationship ID filter"),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Traces any graph node (entity) or edge (relationship) back to its exact raw observations,
    tool provenance, and legal classification.
    """
    return InvestigationService.get_provenance(
        db=db,
        investigation_id=investigation_id,
        entity_id=entity_id,
        relationship_id=relationship_id,
    )


@router.get(
    "/{investigation_id}/export",
    response_model=None,
    dependencies=[Depends(export_rate_limiter)],
)
def export_investigation(
    investigation_id: UUID,
    format: Literal["markdown", "json"] = "markdown",
    db: Session = Depends(get_db),
) -> PlainTextResponse | dict:
    try:
        if format == "json":
            return InvestigationService.get_investigation_detail(db, investigation_id)
        report_md = InvestigationService.export_report_markdown(db, investigation_id)
        return PlainTextResponse(
            content=report_md,
            media_type="text/markdown",
            headers={"Content-Disposition": f'attachment; filename="investigation_{investigation_id}.md"'},
        )
    except InvestigationNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

