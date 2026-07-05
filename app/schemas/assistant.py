from pydantic import BaseModel, Field


class AssistantChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)


class ReportExportInfo(BaseModel):
    report_id: str
    filename: str
    format: str
    download_url: str
    row_count: int | None = None
    google_sheets_hint: str | None = None


class AssistantChatResponse(BaseModel):
    answer: str
    tools_used: list[str]
    exports: list[ReportExportInfo]


class AssistantMessageResponse(BaseModel):
    message_id: int
    role: str
    text: str
    tools_used: list[str] | None = None
    exports: list[ReportExportInfo] = []
    created_at: str
