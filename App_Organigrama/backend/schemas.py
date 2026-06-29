from __future__ import annotations

from pydantic import BaseModel


class OrgPayload(BaseModel):
    document: dict
