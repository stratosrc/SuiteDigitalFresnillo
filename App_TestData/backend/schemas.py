from __future__ import annotations

from pydantic import BaseModel, Field


class RedactionPayload(BaseModel):
    session_id: str
    rectangles: list[dict] = Field(default_factory=list)
    committee_data: dict[str, str] = Field(default_factory=dict)


class DeleteRectanglePayload(BaseModel):
    session_id: str = "draft"
    rectangles: list[dict] = Field(default_factory=list)
    selected_rect_id: str | int | None = None


class PdfBase64Payload(BaseModel):
    filename: str = "proyecto.pdf"
    data: str
