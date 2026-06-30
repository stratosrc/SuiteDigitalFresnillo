from __future__ import annotations

from pydantic import BaseModel


class OrgPayload(BaseModel):
    document: dict


class OrgNodePayload(BaseModel):
    document: dict
    name: str
    role: str
    grid_x: int
    grid_y: int
    color: str


class OrgConnectionPayload(BaseModel):
    document: dict
    source_id: str
    target_id: str
    source_port: str = "bottom"
    target_port: str = "top"
    kind: str = "direct"


class OrgNodeUpdatePayload(BaseModel):
    document: dict
    node_id: str
    name: str
    role: str
    color: str


class OrgManualRoutePayload(BaseModel):
    document: dict
    connection_id: str
    kind: str
    index: int
    pointer: tuple[float, float]
    commit: bool = False
