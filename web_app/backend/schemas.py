from __future__ import annotations

from pydantic import BaseModel, Field


class PersonPayload(BaseModel):
    rank: str = ""
    name: str = ""
    position: str = ""
    email: str = ""
    start_date: str = ""


class AreaPayload(BaseModel):
    name: str = ""
    personnel: list[PersonPayload] = Field(default_factory=list)


class DirectoryPayload(BaseModel):
    title: str = "Directorio"
    period: str = ""
    areas: list[AreaPayload] = Field(default_factory=list)


class RedactionPayload(BaseModel):
    session_id: str
    rectangles: list[dict] = Field(default_factory=list)
    committee_data: dict[str, str] = Field(default_factory=dict)


class PdfBase64Payload(BaseModel):
    filename: str = "proyecto.pdf"
    data: str


class OrgPayload(BaseModel):
    document: dict
