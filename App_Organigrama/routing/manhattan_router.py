from dataclasses import dataclass
from heapq import heappop, heappush
import math
from typing import TYPE_CHECKING

from App_Organigrama.models.document import Connection, OrgGridDocument, OrgNode
from App_Organigrama.routing.manual_routes import (
    GridBox,
    build_manual_route,
    route_crosses_boxes,
    simplify_orthogonal_route,
)

if TYPE_CHECKING:
    from App_Organigrama.rendering.engine import RenderingEngine


GridPoint = tuple[float, float]
SubGridPoint = tuple[int, int]


@dataclass(frozen=True, slots=True)
class ConnectionRoute:
    connection: Connection
    points: tuple[GridPoint, ...]


class ManhattanRouter:
    """Orthogonal A* router with half-grid precision and bend penalties."""

    def __init__(self, rendering_engine: "RenderingEngine", padding: int = 6, bend_penalty: float = 40.0) -> None:
        self.rendering_engine = rendering_engine
        self.padding = padding
        self.bend_penalty = bend_penalty

    def route_document(self, document: OrgGridDocument) -> list[ConnectionRoute]:
        occupied = {(node.grid_x, node.grid_y) for node in document.nodes.values()}
        routes: list[ConnectionRoute] = []
        traffic_by_source: dict[str, set[GridPoint]] = {}

        for connection in document.connections:
            source = document.nodes.get(connection.source_id)
            target = document.nodes.get(connection.target_id)
            if source is None or target is None:
                continue

            blocked_paths: set[GridPoint] = set()
            for source_id, traffic_points in traffic_by_source.items():
                if source_id != connection.source_id:
                    blocked_paths.update(traffic_points)

            if connection.manual_points:
                manual_route = build_manual_route(
                    self.rendering_engine.get_node_port_grid_position(
                        source,
                        connection.source_port,
                    ),
                    self.rendering_engine.get_node_port_grid_position(
                        target,
                        connection.target_port,
                    ),
                    connection.manual_points,
                    connection.source_port,
                    connection.target_port,
                )
                obstacle_boxes = self._node_obstacle_boxes(
                    document,
                    excluded_node_ids={source.id, target.id},
                )
                points = (
                    self.route(
                        source=source,
                        target=target,
                        occupied=occupied,
                        source_port=connection.source_port,
                        target_port=connection.target_port,
                        blocked_paths=blocked_paths,
                        custom_obstacles=set(document.blocked_points),
                    )
                    if route_crosses_boxes(manual_route, obstacle_boxes)
                    else manual_route
                )
            else:
                points = self.route(
                    source=source,
                    target=target,
                    occupied=occupied,
                    source_port=connection.source_port,
                    target_port=connection.target_port,
                    blocked_paths=blocked_paths,
                    custom_obstacles=set(document.blocked_points),
                )
            routes.append(ConnectionRoute(connection=connection, points=tuple(points)))
            traffic_by_source.setdefault(connection.source_id, set()).update(self.route_traffic_points(points))

        return routes

    def _node_obstacle_boxes(
        self,
        document: OrgGridDocument,
        *,
        excluded_node_ids: set[str] | None = None,
    ) -> list[GridBox]:
        excluded = excluded_node_ids or set()
        cell_width = self.rendering_engine.base_cell_width
        cell_height = self.rendering_engine.base_cell_height
        boxes: list[GridBox] = []
        for node in document.nodes.values():
            if node.id in excluded:
                continue
            box = self.rendering_engine.get_node_box(node, include_logo=False)
            boxes.append(
                GridBox(
                    left=box.left / cell_width,
                    top=box.top / cell_height,
                    right=box.right / cell_width,
                    bottom=box.bottom / cell_height,
                )
            )
        return boxes

    def route(
        self,
        source: OrgNode,
        target: OrgNode,
        occupied: set[tuple[int, int]],
        source_port: str = "bottom",
        target_port: str = "top",
        blocked_paths: set[GridPoint] | None = None,
        custom_obstacles: set[GridPoint] | None = None,
    ) -> list[GridPoint]:
        exact_start = self.rendering_engine.get_node_port_grid_position(source, source_port)
        exact_goal = self.rendering_engine.get_node_port_grid_position(target, target_port)
        start = self._to_subgrid(self._gateway_point(exact_start, source_port))
        goal = self._to_subgrid(self._gateway_point(exact_goal, target_port))

        blocked = {self._to_subgrid(point) for point in occupied}
        if blocked_paths:
            blocked.update(self._to_subgrid(point) for point in blocked_paths)
        if custom_obstacles:
            blocked.update(self._to_subgrid(point) for point in custom_obstacles)

        blocked.discard(start)
        blocked.discard(goal)

        min_x, min_y, max_x, max_y = self._search_bounds(start, goal, blocked)
        path = self._astar(start, goal, blocked, min_x, min_y, max_x, max_y)
        growth = self.padding * 2
        while path is None and growth <= self.padding * 16:
            path = self._astar(
                start,
                goal,
                blocked,
                min_x - growth,
                min_y - growth,
                max_x + growth,
                max_y + growth,
            )
            growth *= 2

        simplified = self._simplify(path or self._orthogonal_fallback(start, goal))
        route = [self._from_subgrid(point) for point in simplified]
        if route[0] != exact_start:
            route.insert(0, exact_start)
        if route[-1] != exact_goal:
            route.append(exact_goal)
        return simplify_orthogonal_route(route)

    def route_traffic_points(self, route: list[GridPoint]) -> set[GridPoint]:
        points: set[GridPoint] = set()
        if len(route) < 2:
            return points

        subgrid_route = [self._to_subgrid(point) for point in route]
        for start, end in zip(subgrid_route, subgrid_route[1:]):
            x1, y1 = start
            x2, y2 = end
            dx = 0 if x2 == x1 else (1 if x2 > x1 else -1)
            dy = 0 if y2 == y1 else (1 if y2 > y1 else -1)
            x, y = x1, y1
            points.add(self._from_subgrid((x, y)))
            while (x, y) != (x2, y2):
                x += dx
                y += dy
                points.add(self._from_subgrid((x, y)))
        return points

    def _gateway_point(self, exact_point: GridPoint, port: str) -> GridPoint:
        x, y = exact_point
        if port == "right":
            return (math.ceil(x * 2) / 2, y)
        if port == "left":
            return (math.floor(x * 2) / 2, y)
        if port == "bottom":
            return (x, math.ceil(y * 2) / 2)
        if port == "top":
            return (x, math.floor(y * 2) / 2)
        return self._from_subgrid(self._to_subgrid(exact_point))

    def _orthogonal_fallback(self, start: SubGridPoint, goal: SubGridPoint) -> list[SubGridPoint]:
        if start[0] == goal[0] or start[1] == goal[1]:
            return [start, goal]
        return [start, (start[0], goal[1]), goal]

    def _search_bounds(
        self,
        start: SubGridPoint,
        goal: SubGridPoint,
        blocked: set[SubGridPoint],
    ) -> tuple[int, int, int, int]:
        xs = [start[0], goal[0], *(x for x, _ in blocked)]
        ys = [start[1], goal[1], *(y for _, y in blocked)]
        pad = self.padding * 2
        return (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)

    def _astar(
        self,
        start: SubGridPoint,
        goal: SubGridPoint,
        blocked: set[SubGridPoint],
        min_x: int,
        min_y: int,
        max_x: int,
        max_y: int,
    ) -> list[SubGridPoint] | None:
        queue: list[tuple[float, int, tuple[SubGridPoint, str | None]]] = []
        start_state = (start, None)
        heappush(queue, (0.0, 0, start_state))
        came_from: dict[tuple[SubGridPoint, str | None], tuple[SubGridPoint, str | None]] = {}
        g_score: dict[tuple[SubGridPoint, str | None], float] = {start_state: 0.0}
        sequence = 0

        while queue:
            _priority, _sequence, current_state = heappop(queue)
            current, direction = current_state
            if current == goal:
                return self._reconstruct(came_from, current_state)

            for neighbor, next_direction in self._neighbors(current, goal):
                x, y = neighbor
                if x < min_x or x > max_x or y < min_y or y > max_y:
                    continue
                if neighbor in blocked:
                    continue

                turn_cost = 0.0
                if direction is not None and direction != next_direction:
                    endpoint_bias = min(self._manhattan(current, start), self._manhattan(current, goal))
                    turn_cost = self.bend_penalty + endpoint_bias

                next_state = (neighbor, next_direction)
                candidate = g_score[current_state] + 1.0 + turn_cost
                if candidate >= g_score.get(next_state, float("inf")):
                    continue

                came_from[next_state] = current_state
                g_score[next_state] = candidate
                sequence += 1
                priority = candidate + self._manhattan(neighbor, goal)
                heappush(queue, (priority, sequence, next_state))

        return None

    def _neighbors(self, current: SubGridPoint, goal: SubGridPoint) -> list[tuple[SubGridPoint, str]]:
        x, y = current
        vertical = [((x, y + 1), "v"), ((x, y - 1), "v")] if goal[1] >= y else [((x, y - 1), "v"), ((x, y + 1), "v")]
        horizontal = [((x + 1, y), "h"), ((x - 1, y), "h")] if goal[0] >= x else [((x - 1, y), "h"), ((x + 1, y), "h")]
        return vertical + horizontal

    def _manhattan(self, a: SubGridPoint, b: SubGridPoint) -> int:
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _reconstruct(
        self,
        came_from: dict[tuple[SubGridPoint, str | None], tuple[SubGridPoint, str | None]],
        current_state: tuple[SubGridPoint, str | None],
    ) -> list[SubGridPoint]:
        path = [current_state[0]]
        current = current_state
        while current in came_from:
            current = came_from[current]
            path.append(current[0])
        path.reverse()
        return path

    def _simplify(self, path: list[SubGridPoint]) -> list[SubGridPoint]:
        if len(path) <= 2:
            return path

        simplified = [path[0]]
        previous_dx = path[1][0] - path[0][0]
        previous_dy = path[1][1] - path[0][1]

        for index in range(1, len(path) - 1):
            current = path[index]
            nxt = path[index + 1]
            dx = nxt[0] - current[0]
            dy = nxt[1] - current[1]
            if (dx, dy) != (previous_dx, previous_dy):
                simplified.append(current)
            previous_dx, previous_dy = dx, dy

        simplified.append(path[-1])
        return simplified

    def _to_subgrid(self, point: GridPoint) -> SubGridPoint:
        return (int(round(point[0] * 2)), int(round(point[1] * 2)))

    def _from_subgrid(self, point: SubGridPoint) -> GridPoint:
        return (point[0] / 2, point[1] / 2)
