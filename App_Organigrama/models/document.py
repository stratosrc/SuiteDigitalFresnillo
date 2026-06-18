from dataclasses import dataclass, field
from uuid import uuid4

GridCell = tuple[int, int]
GridPoint = tuple[float, float]


@dataclass(slots=True)
class OrgNode:
    name: str
    role: str
    grid_x: int
    grid_y: int
    color: str
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(slots=True)
class Connection:
    source_id: str
    target_id: str
    source_port: str = "bottom"
    target_port: str = "top"
    kind: str = "direct"
    manual_points: tuple[GridPoint, ...] = ()
    id: str = field(default_factory=lambda: uuid4().hex)


@dataclass(slots=True)
class OrgGridDocument:
    title: str = "Título del organigrama"
    period: str = ""
    page_orientation: str = "horizontal"
    show_logos: bool = True
    nodes: dict[str, OrgNode] = field(default_factory=dict)
    connections: list[Connection] = field(default_factory=list)
    blocked_points: list[GridPoint] = field(default_factory=list)
    _node_ids_by_position: dict[GridCell, str] = field(default_factory=dict, init=False, repr=False)
    _blocked_points_index: set[GridPoint] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        self._rebuild_indexes()

    def _rebuild_indexes(self) -> None:
        self._node_ids_by_position = {
            (node.grid_x, node.grid_y): node_id
            for node_id, node in self.nodes.items()
        }
        self._blocked_points_index = {self._normalize_blocked_point(point) for point in self.blocked_points}
        self.blocked_points = sorted(self._blocked_points_index, key=lambda item: (item[1], item[0]))

    def _normalize_blocked_point(self, point: GridPoint) -> GridPoint:
        return (float(point[0]), float(point[1]))

    def to_dict(self) -> dict[str, object]:
        return {
            "title": self.title,
            "period": self.period,
            "page_orientation": self.page_orientation,
            "show_logos": self.show_logos,
            "nodes": {
                node_id: {
                    "name": node.name,
                    "role": node.role,
                    "grid_x": node.grid_x,
                    "grid_y": node.grid_y,
                    "color": node.color,
                    "id": node.id,
                }
                for node_id, node in self.nodes.items()
            },
            "connections": [
                {
                    "source_id": connection.source_id,
                    "target_id": connection.target_id,
                    "source_port": connection.source_port,
                    "target_port": connection.target_port,
                    "kind": connection.kind,
                    "manual_points": list(connection.manual_points),
                    "id": connection.id,
                }
                for connection in self.connections
            ],
            "blocked_points": list(self.blocked_points),
        }

    def add_node(
        self,
        name: str,
        role: str,
        grid_x: int,
        grid_y: int,
        color: str,
    ) -> OrgNode:
        if self.get_node_at(grid_x, grid_y) is not None:
            raise ValueError("La celda seleccionada ya contiene un nodo.")

        node = OrgNode(
            name=name,
            role=role,
            grid_x=grid_x,
            grid_y=grid_y,
            color=color,
        )
        self.nodes[node.id] = node
        self._node_ids_by_position[(grid_x, grid_y)] = node.id
        return node

    def update_node(self, node_id: str, name: str, role: str, color: str) -> OrgNode:
        node = self.nodes[node_id]
        node.name = name
        node.role = role
        node.color = color
        return node

    def move_node(self, node_id: str, grid_x: int, grid_y: int) -> bool:
        occupant = self.get_node_at(grid_x, grid_y)
        if occupant is not None and occupant.id != node_id:
            return False

        node = self.nodes[node_id]
        previous_cell = (node.grid_x, node.grid_y)
        next_cell = (grid_x, grid_y)
        if previous_cell == next_cell:
            return True

        self._node_ids_by_position.pop(previous_cell, None)
        self._node_ids_by_position[next_cell] = node_id
        node.grid_x = grid_x
        node.grid_y = grid_y
        return True

    def get_node_at(self, grid_x: int, grid_y: int) -> OrgNode | None:
        node_id = self._node_ids_by_position.get((grid_x, grid_y))
        return self.nodes.get(node_id) if node_id is not None else None

    def add_connection(
        self,
        source_id: str,
        target_id: str,
        kind: str = "direct",
        source_port: str = "bottom",
        target_port: str = "top",
    ) -> Connection | None:
        if source_id == target_id:
            return None
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        for connection in self.connections:
            if (
                connection.source_id == source_id
                and connection.target_id == target_id
                and connection.source_port == source_port
                and connection.target_port == target_port
            ):
                return connection

        connection = Connection(
            source_id=source_id,
            target_id=target_id,
            source_port=source_port,
            target_port=target_port,
            kind=kind,
        )
        self.connections.append(connection)
        return connection

    def remove_node(self, node_id: str) -> None:
        node = self.nodes.pop(node_id, None)
        if node is None:
            return

        self._node_ids_by_position.pop((node.grid_x, node.grid_y), None)
        self.connections = [
            connection
            for connection in self.connections
            if connection.source_id != node_id and connection.target_id != node_id
        ]

    def remove_connection(self, connection_id: str) -> bool:
        before_count = len(self.connections)
        self.connections = [connection for connection in self.connections if connection.id != connection_id]
        return len(self.connections) != before_count

    def set_connection_manual_points(
        self,
        connection_id: str,
        points: list[GridPoint] | tuple[GridPoint, ...],
    ) -> bool:
        connection = self.get_connection(connection_id)
        if connection is None:
            return False
        connection.manual_points = tuple(
            (float(point[0]), float(point[1]))
            for point in points
        )
        return True

    def reset_connection_route(self, connection_id: str) -> bool:
        connection = self.get_connection(connection_id)
        if connection is None or not connection.manual_points:
            return False
        connection.manual_points = ()
        return True

    def get_connection(self, connection_id: str) -> Connection | None:
        return next(
            (
                connection
                for connection in self.connections
                if connection.id == connection_id
            ),
            None,
        )

    def has_blocked_point(self, point: GridPoint) -> bool:
        return self._normalize_blocked_point(point) in self._blocked_points_index

    def toggle_blocked_point(self, point: GridPoint) -> bool:
        normalized = self._normalize_blocked_point(point)
        if normalized in self._blocked_points_index:
            self._blocked_points_index.remove(normalized)
            self.blocked_points = [existing for existing in self.blocked_points if existing != normalized]
            return False

        self._blocked_points_index.add(normalized)
        self.blocked_points.append(normalized)
        self.blocked_points.sort(key=lambda item: (item[1], item[0]))
        return True

    def remove_blocked_point(self, point: GridPoint) -> bool:
        normalized = self._normalize_blocked_point(point)
        if normalized not in self._blocked_points_index:
            return False

        self._blocked_points_index.remove(normalized)
        self.blocked_points = [existing for existing in self.blocked_points if existing != normalized]
        return True

    def clear(self) -> None:
        self.nodes.clear()
        self.connections.clear()
        self.blocked_points.clear()
        self._node_ids_by_position.clear()
        self._blocked_points_index.clear()

    def bounds(self) -> tuple[int, int, int, int]:
        if not self.nodes:
            return (0, 0, 0, 0)

        xs = [node.grid_x for node in self.nodes.values()]
        ys = [node.grid_y for node in self.nodes.values()]
        return (min(xs), min(ys), max(xs), max(ys))
