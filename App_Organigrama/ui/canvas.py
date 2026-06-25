from __future__ import annotations

import typing

from typing import Callable
import tkinter as tk

import customtkinter as ctk
from PIL import ImageTk

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.engine import NodeLayout, RenderingEngine
from App_Organigrama.routing.manhattan_router import ConnectionRoute, ManhattanRouter
from App_Organigrama.ui.canvas_connection_controller import CanvasConnectionController
from App_Organigrama.ui.canvas_drawing import CanvasDrawingMixin
from App_Organigrama.ui.canvas_node_controller import CanvasNodeController
from App_Organigrama.ui.canvas_interaction_controller import CanvasInteractionController
from App_Organigrama.ui.canvas_selection import draw_connection_selection_overlay, draw_node_selection_overlay
from App_Organigrama.ui.canvas_state import CanvasInteractionState, InteractionMode
from App_Organigrama.ui.canvas_viewport_controller import CanvasViewportController
from App_Organigrama.ui.theme import (
    BORDER_COLOR,
    SURFACE_BACKGROUND,
)


GridPoint = typing.Tuple[float, float]


class OrgGridCanvas(
    CanvasInteractionController,
    CanvasConnectionController,
    CanvasNodeController,
    CanvasViewportController,
    CanvasDrawingMixin,
    ctk.CTkFrame,
):
    _INTERACTION_FIELDS = frozenset(CanvasInteractionState.__dataclass_fields__)

    def __getattr__(self, name: str):
        if name in self._INTERACTION_FIELDS and "interaction" in self.__dict__:
            return getattr(self.interaction, name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value) -> None:
        if (
            name in self._INTERACTION_FIELDS
            and "interaction" in self.__dict__
            and name != "interaction"
        ):
            setattr(self.interaction, name, value)
            return
        super().__setattr__(name, value)

    def __init__(
        self,
        master: tk.Misc,
        document: OrgGridDocument,
        rendering_engine: RenderingEngine,
        router: ManhattanRouter,
        on_selection_change: Callable[[bool], None] | None = None,
        on_zoom_change: Callable[[int], None] | None = None,
        on_document_change: Callable[[], None] | None = None,
        on_context_change: Callable[[str], None] | None = None,
        **kwargs: object,
    ) -> None:
        super().__init__(
            master,
            fg_color=SURFACE_BACKGROUND,
            border_color=BORDER_COLOR,
            border_width=1,
            **kwargs,
        )
        self.document = document
        self.rendering_engine = rendering_engine
        self.router = router
        self.on_selection_change = on_selection_change
        self.on_zoom_change = on_zoom_change
        self.on_document_change = on_document_change
        self.on_context_change = on_context_change

        self.zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.0
        self.pan_x = 560.0
        self.pan_y = 320.0
        self.interaction = CanvasInteractionState()
        self.block_mode = False
        self.selected_node_id: str | None = None
        self.selected_connection_id: str | None = None
        self.selected_blocked_point: GridPoint | None = None
        self.selection_blink_visible = True
        self.selection_blink_after_id: str | None = None
        self.node_history: list[str] = []
        self.last_node_id: str | None = None
        self.route_cache: list[ConnectionRoute] = []
        self._routes_dirty = True
        self._node_layout_cache: dict[tuple[str, bool], NodeLayout] = {}
        self.manual_ghost_after_id: str | None = None
        self.redraw_after_id: str | None = None
        self.logo_source_image = self._load_logo_source()
        self.logo_cache: dict[int, ImageTk.PhotoImage] = {}
        self.cross_cursor_source_image = self._load_cross_cursor_source()
        self.cross_cursor_cache: dict[int, ImageTk.PhotoImage] = {}
        self.custom_cursor_canvas_id: int | None = None
        self.custom_cursor_position: tuple[int, int] | None = None
        self.custom_cursor_visible = False

        self.canvas = tk.Canvas(self, bg=SURFACE_BACKGROUND, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self._bind_events()
        self._emit_context_change()

    def set_document(self, document: OrgGridDocument) -> None:
        self.document = document
        self.selected_node_id = None
        self.selected_connection_id = None
        self.selected_blocked_point = None
        self._sync_selection_blink()
        self.pending_connection_source_id = None
        self.pending_source_port = None
        self.hover_port = None
        self.connection_drag_source_id = None
        self.connection_drag_source_port = None
        self.connection_drag_screen_point = None
        self.connection_press_source_id = None
        self.connection_press_source_port = None
        self._clear_manual_drag()
        self.preview_obstacle = None
        self.node_history = []
        self.last_node_id = None
        self.route_cache = []
        self._routes_dirty = True
        self._invalidate_layout_cache()
        self._update_custom_cursor(visible=False)
        self.after_idle(self.fit_document_to_content_top)
        self._emit_selection_change()

    def set_block_mode(self, enabled: bool) -> None:
        self.block_mode = enabled
        self.interaction.transition(
            InteractionMode.BLOCKING if enabled else InteractionMode.IDLE
        )
        self.preview_obstacle = None
        if enabled:
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self.hover_port = None
        self._update_custom_cursor(visible=enabled)
        self.request_redraw()
        self._emit_context_change()

    def set_show_logos(self, enabled: bool) -> None:
        self.document.show_logos = enabled
        self._invalidate_layout_cache()
        self._emit_document_change()
        self.request_redraw()

    def delete_selected_item(self) -> None:
        self._delete_selected()

    def redraw(self) -> None:
        self.redraw_after_id = None
        self.canvas.delete("all")
        self.custom_cursor_canvas_id = None
        if self._routes_dirty:
            self.route_cache = self.router.route_document(self.document)
            self._routes_dirty = False
        self._draw_grid()
        if not self.document.nodes:
            self.canvas.create_text(
                self.canvas.winfo_width() / 2,
                self.canvas.winfo_height() / 2,
                text=(
                    "Organigrama vacío\n"
                    "Haz clic en una celda para crear el primer nodo.\n"
                    "También puedes abrir un proyecto con Ctrl+O."
                ),
                fill="#64748B",
                font=("Arial", 14),
                justify="center",
                tags=("empty-state",),
            )
        self._draw_connections(self.route_cache)
        self._draw_manual_route_ghost()
        self._draw_connection_drag_preview()
        self._draw_preview_routes()
        draw_connection_selection_overlay(self)
        self._draw_nodes()
        self._draw_blocked_points()
        self._draw_hover_port()
        self._draw_ghost()
        draw_node_selection_overlay(self)
        self._draw_manual_route_handles()
        self._draw_custom_cursor()

    def request_redraw(self) -> None:
        if self.redraw_after_id is not None:
            return
        self.redraw_after_id = self.after(16, self.redraw)


__all__ = ["OrgGridCanvas"]
