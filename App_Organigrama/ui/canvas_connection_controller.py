"""Connection creation, hit testing, and manual-route editing controller."""

from __future__ import annotations

from tkinter import messagebox

from App_Organigrama.models.document import OrgNode
from App_Organigrama.rendering.palette import NODE_HIERARCHY_RANK_BY_COLOR
from App_Organigrama.routing.manhattan_router import ConnectionRoute
from App_Organigrama.routing.manual_routes import (
    GridBox,
    move_bend_point,
    move_intermediate_segment,
    route_box_collisions,
)
from App_Organigrama.ui.canvas_hit_testing import (
    find_bend_point_at_screen,
    find_connection_at_screen,
    find_movable_segment_at_screen,
    nearest_port,
)
from App_Organigrama.ui.canvas_state import InteractionMode


GridPoint = tuple[float, float]


class CanvasConnectionController:
    def can_reset_selected_route(self) -> bool:
        connection = self.document.get_connection(self.selected_connection_id or "")
        return connection is not None and bool(connection.manual_points)

    def reset_selected_route(self) -> None:
        if self.selected_connection_id is None:
            return
        if self.document.reset_connection_route(self.selected_connection_id):
            self._mark_document_changed()
            self._emit_selection_change()

    def _selected_movable_segment_at_screen(
        self,
        screen_x: int,
        screen_y: int,
    ) -> tuple[ConnectionRoute, int] | None:
        route = self._selected_connection_route()
        if route is None:
            return None
        segment_index = find_movable_segment_at_screen(
            route,
            screen_x,
            screen_y,
            self.rendering_engine,
            self._world_to_screen,
            max_distance=max(10.0, 12.0 * self.zoom),
        )
        return (route, segment_index) if segment_index is not None else None

    def _selected_bend_point_at_screen(
        self,
        screen_x: int,
        screen_y: int,
    ) -> tuple[ConnectionRoute, int] | None:
        route = self._selected_connection_route()
        if route is None:
            return None
        point_index = find_bend_point_at_screen(
            route,
            screen_x,
            screen_y,
            self.rendering_engine,
            self._world_to_screen,
            max_distance=max(9.0, 10.0 * self.zoom),
        )
        return (route, point_index) if point_index is not None else None

    def _preview_manual_segment_drag(self, screen_x: int, screen_y: int) -> None:
        route = self.manual_drag_original_route
        if route is None:
            return
        pointer = self._screen_to_subgrid(screen_x, screen_y)
        if self.manual_drag_kind == "bend" and self.manual_drag_point_index is not None:
            candidate = move_bend_point(route, self.manual_drag_point_index, pointer)
        elif self.manual_drag_kind == "segment" and self.manual_drag_segment_index is not None:
            candidate = move_intermediate_segment(
                route,
                self.manual_drag_segment_index,
                pointer,
            )
        else:
            return
        self.manual_drag_candidate_route = tuple(candidate)
        self.manual_drag_collision_node_ids = self._route_collision_node_ids(candidate)
        self._emit_context_change(
            "Posición no válida: el ghost rojo muestra la ruta y los nodos atravesados"
            if self.manual_drag_collision_node_ids
            else "Ghost verde: suelta para guardar esta ruta"
        )
        self.request_redraw()

    def _finish_manual_segment_drag(self) -> None:
        connection_id = self.manual_drag_connection_id
        original = self.manual_drag_original_route
        candidate = self.manual_drag_candidate_route
        is_valid = not self.manual_drag_collision_node_ids
        changed = (
            connection_id is not None
            and candidate is not None
            and original is not None
            and candidate != original
            and is_valid
        )
        invalid_candidate = (
            candidate
            if candidate is not None
            and original is not None
            and candidate != original
            and not is_valid
            else None
        )
        collision_node_ids = self.manual_drag_collision_node_ids
        self._clear_manual_drag()
        if changed and connection_id is not None and candidate is not None:
            self.document.set_connection_manual_points(connection_id, candidate[1:-1])
            self._mark_document_changed()
            self._emit_selection_change()
        elif invalid_candidate is not None:
            self.manual_drag_candidate_route = invalid_candidate
            self.manual_drag_collision_node_ids = collision_node_ids
            self.manual_ghost_after_id = self.after(
                1400,
                self._expire_retained_manual_ghost,
            )
            self.request_redraw()
        else:
            self.request_redraw()
        self.interaction.transition(
            InteractionMode.BLOCKING if self.block_mode else InteractionMode.IDLE
        )
        self._emit_context_change()

    def _clear_manual_drag(self) -> None:
        if self.manual_ghost_after_id is not None:
            self.after_cancel(self.manual_ghost_after_id)
            self.manual_ghost_after_id = None
        self.manual_drag_connection_id = None
        self.manual_drag_kind = None
        self.manual_drag_segment_index = None
        self.manual_drag_point_index = None
        self.manual_drag_original_route = None
        self.manual_drag_candidate_route = None
        self.manual_drag_collision_node_ids = ()

    def _clear_retained_manual_ghost(self) -> None:
        if self.manual_ghost_after_id is not None:
            self.after_cancel(self.manual_ghost_after_id)
            self.manual_ghost_after_id = None
        if self.manual_drag_connection_id is None:
            self.manual_drag_candidate_route = None
            self.manual_drag_collision_node_ids = ()
            self.request_redraw()

    def _expire_retained_manual_ghost(self) -> None:
        self.manual_ghost_after_id = None
        self.manual_drag_candidate_route = None
        self.manual_drag_collision_node_ids = ()
        self.request_redraw()

    def _routes_for_display(self) -> list[ConnectionRoute]:
        return self.route_cache

    def _selected_connection_route(self) -> ConnectionRoute | None:
        return next(
            (
                route
                for route in self._routes_for_display()
                if route.connection.id == self.selected_connection_id
            ),
            None,
        )

    def _route_collision_node_ids(
        self,
        route_points: list[GridPoint],
    ) -> tuple[str, ...]:
        node_ids: list[str] = []
        boxes: list[GridBox] = []
        cell_width = self.rendering_engine.base_cell_width
        cell_height = self.rendering_engine.base_cell_height
        for node in self.document.nodes.values():
            node_ids.append(node.id)
            box = self._get_node_layout(node, include_logo=False).box
            boxes.append(
                GridBox(
                    left=box.left / cell_width,
                    top=box.top / cell_height,
                    right=box.right / cell_width,
                    bottom=box.bottom / cell_height,
                )
            )
        collisions = route_box_collisions(route_points, boxes)
        return tuple(node_ids[index] for index in sorted(collisions))

    def _connection_at_screen(
        self,
        screen_x: int,
        screen_y: int,
    ) -> ConnectionRoute | None:
        return find_connection_at_screen(
            self.route_cache,
            screen_x,
            screen_y,
            self.rendering_engine,
            self._world_to_screen,
        )

    def _connection_at_hover_cell(self) -> ConnectionRoute | None:
        if self.last_hover_cell is None:
            return None
        world_x, world_y = self.rendering_engine.grid_to_world(*self.last_hover_cell)
        screen_x, screen_y = self._world_to_screen(world_x, world_y)
        return self._connection_at_screen(int(screen_x), int(screen_y))

    def _nearest_port(
        self,
        node: OrgNode,
        screen_x: int,
        screen_y: int,
    ) -> str:
        layout = self._get_node_layout(node, include_logo=False)
        return nearest_port(
            node,
            screen_x,
            screen_y,
            layout,
            self.zoom,
            self._world_to_screen,
        )

    def _connect_by_click(
        self,
        source_id: str,
        source_port: str,
        screen_x: int,
        screen_y: int,
    ) -> None:
        target_node = self._node_at_screen(screen_x, screen_y) or self._node_near_screen(
            screen_x,
            screen_y,
        )
        if (
            self.pending_connection_source_id is None
            or self.pending_connection_source_id == source_id
        ):
            self.pending_connection_source_id = source_id
            self.pending_source_port = source_port
            self._set_selection(node_id=source_id)
            return
        if target_node is not None:
            self._create_connection_to_target(target_node, screen_x, screen_y)

    def _finish_connection_drag(
        self,
        source_id: str,
        source_port: str,
        screen_x: int,
        screen_y: int,
    ) -> None:
        target_node = self._node_at_screen(screen_x, screen_y) or self._node_near_screen(
            screen_x,
            screen_y,
        )
        if target_node is None or target_node.id == source_id:
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self.hover_port = None
            return
        self.pending_connection_source_id = source_id
        self.pending_source_port = source_port
        self._create_connection_to_target(target_node, screen_x, screen_y)

    def _create_connection_to_target(
        self,
        target_node: OrgNode,
        screen_x: int,
        screen_y: int,
    ) -> None:
        source_id = self.pending_connection_source_id
        if source_id is None:
            return
        source_node = self.document.nodes.get(source_id)
        if source_node is None:
            return
        if not self._confirm_inverse_hierarchy_connection(source_node, target_node):
            self.pending_connection_source_id = None
            self.pending_source_port = None
            self.hover_port = None
            return
        target_port = self._nearest_port(target_node, screen_x, screen_y)
        new_connection = self.document.add_connection(
            source_id,
            target_node.id,
            source_port=self.pending_source_port or "bottom",
            target_port=target_port,
        )
        self.pending_connection_source_id = None
        self.pending_source_port = None
        self.hover_port = None
        if new_connection is not None:
            self._set_selection(connection_id=new_connection.id)
            self._mark_document_changed()

    def _confirm_inverse_hierarchy_connection(self, source_node: OrgNode, target_node: OrgNode) -> bool:
        source_rank = NODE_HIERARCHY_RANK_BY_COLOR.get(source_node.color)
        target_rank = NODE_HIERARCHY_RANK_BY_COLOR.get(target_node.color)
        if source_rank is None or target_rank is None or source_rank >= target_rank:
            return True

        source_label = self._node_flow_label(source_node)
        target_label = self._node_flow_label(target_node)
        return messagebox.askyesno(
            "Conexión jerárquica inversa",
            (
                "Estás conectando de una jerarquía menor hacia una jerarquía mayor.\n\n"
                f"Origen: {source_label}\n"
                f"Destino: {target_label}\n\n"
                "Esto podría invertir el sentido natural del organigrama. ¿Quieres continuar?"
            ),
            parent=self,
        )

    def _hover_target_id(self, source_id: str) -> str | None:
        if self.hover_port is None or self.hover_port[0] == source_id:
            return None
        return self.hover_port[0]

    def _connection_flow_message(
        self,
        source_id: str,
        target_id: str,
        prefix: str,
    ) -> str:
        source = self.document.nodes.get(source_id)
        target = self.document.nodes.get(target_id)
        if source is None or target is None:
            return f"{prefix}: origen → destino"
        return (
            f"{prefix}: {self._node_flow_label(source)} "
            f"→ {self._node_flow_label(target)}"
        )

    @staticmethod
    def _node_flow_label(node: OrgNode) -> str:
        name = node.name.strip() or "Sin nombre"
        role = node.role.strip()
        return f"{name} — {role}" if role else name


__all__ = ["CanvasConnectionController"]
