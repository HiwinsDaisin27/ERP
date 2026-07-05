from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.auth import AssistantChatMessage, WebUser
from app.schemas.assistant import AssistantChatRequest, AssistantChatResponse, AssistantMessageResponse, ReportExportInfo
from app.services.intelligence_service import IntelligenceService
from app.services.report_export_service import ReportExportService

router = APIRouter(prefix="/assistant", tags=["assistant"])


def _export_info(items: list[dict] | None) -> list[ReportExportInfo]:
    return [
        ReportExportInfo(
            report_id=item["report_id"],
            filename=item["filename"],
            format=item["format"],
            download_url=item["download_url"],
            row_count=item.get("row_count"),
            google_sheets_hint=item.get("google_sheets_hint"),
        )
        for item in items or []
    ]


@router.post("/chat", response_model=AssistantChatResponse)
async def assistant_chat(
    payload: AssistantChatRequest,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> AssistantChatResponse:
    try:
        result = await IntelligenceService(db).ask(payload.question, user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return AssistantChatResponse(
        answer=result["answer"],
        tools_used=result["tools_used"],
        exports=_export_info(result["exports"]),
    )


@router.get("/history", response_model=list[AssistantMessageResponse])
def assistant_history(
    limit: int = 100,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> list[AssistantMessageResponse]:
    rows = db.scalars(
        select(AssistantChatMessage)
        .where(AssistantChatMessage.user_id == user.user_id)
        .order_by(AssistantChatMessage.created_at.desc(), AssistantChatMessage.message_id.desc())
        .limit(min(max(limit, 1), 300))
    ).all()

    return [
        AssistantMessageResponse(
            message_id=row.message_id,
            role=row.role,
            text=row.text,
            tools_used=row.tools_used,
            exports=_export_info(row.exports),
            created_at=row.created_at.isoformat(),
        )
        for row in reversed(rows)
    ]


@router.get("/reports/{report_id}/download")
def download_report(
    report_id: str,
    db: Session = Depends(get_db),
    user: WebUser = Depends(require_roles("MANAGEMENT", "ADMIN")),
) -> FileResponse:
    try:
        path, filename = ReportExportService(db).get_report_path(report_id, user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    media = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    if filename.endswith(".csv"):
        media = "text/csv"

    return FileResponse(path, filename=filename, media_type=media)
