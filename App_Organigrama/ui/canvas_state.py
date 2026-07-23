"""Explicit interaction state machine for the organigram canvas."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


GridPoint = tuple[float, float]


class InteractionMode(Enum):
    IDLE = auto()
    CONNECTING = auto()
    EDITING_ROUTE = auto()
    PANNING = auto()
    MOVING_NODE = auto()


@dataclass(slots=True)
class CanvasInteractionState:
    mode: InteractionMode = InteractionMode.IDLE
    drag_press: tuple[int, int, float, float] | None = None
    pan_drag_press: tuple[int, int, float, float] | None = None
    dragged: bool = False
    pan_dragged: bool = False
    pending_connection_source_id: str | None = None
    pending_source_port: str | None = None
    hover_port: tuple[str, str] | None = None
    last_hover_cell: tuple[int, int] | None = None
    drag_node_id: str | None = None
    drag_screen_point: tuple[int, int] | None = None
    drag_node_offset: tuple[float, float] | None = None
    connection_drag_source_id: str | None = None
    connection_drag_source_port: str | None = None
    connection_drag_screen_point: tuple[int, int] | None = None
    connection_press_source_id: str | None = None
    connection_press_source_port: str | None = None
    manual_drag_connection_id: str | None = None
    manual_drag_kind: str | None = None
    manual_drag_segment_index: int | None = None
    manual_drag_point_index: int | None = None
    manual_drag_original_route: tuple[GridPoint, ...] | None = None
    manual_drag_candidate_route: tuple[GridPoint, ...] | None = None
    manual_drag_collision_node_ids: tuple[str, ...] = ()

    def transition(self, mode: InteractionMode) -> None:
        self.mode = mode

    def reset_pointer_action(self) -> None:
        self.drag_press = None
        self.pan_drag_press = None
        self.dragged = False
        self.pan_dragged = False
        self.drag_node_id = None
        self.drag_screen_point = None
        self.drag_node_offset = None
        self.connection_drag_source_id = None
        self.connection_drag_source_port = None
        self.connection_drag_screen_point = None
        self.connection_press_source_id = None
        self.connection_press_source_port = None
        self.manual_drag_connection_id = None
        self.manual_drag_kind = None
        self.manual_drag_segment_index = None
        self.manual_drag_point_index = None
        self.manual_drag_original_route = None
        self.manual_drag_candidate_route = None
        self.manual_drag_collision_node_ids = ()
        self.mode = InteractionMode.IDLE


__all__ = ["CanvasInteractionState", "InteractionMode"]
