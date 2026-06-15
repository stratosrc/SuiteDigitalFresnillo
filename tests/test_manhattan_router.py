import unittest

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ManhattanRouter


class ManhattanRouterTests(unittest.TestCase):
    def setUp(self):
        self.engine = RenderingEngine()
        self.router = ManhattanRouter(self.engine)

    def test_route_avoids_custom_obstacles(self):
        source = self._node(0, 0)
        target = self._node(2, 0)

        route = self.router.route(
            source,
            target,
            occupied={(0, 0), (2, 0)},
            source_port="right",
            target_port="left",
            custom_obstacles={(1.0, 0.0)},
        )

        self.assertNotIn((1.0, 0.0), self.router.route_traffic_points(route))

    def test_route_avoids_occupied_nodes_between_endpoints(self):
        source = self._node(0, 0)
        middle = self._node(1, 0)
        target = self._node(2, 0)

        route = self.router.route(
            source,
            target,
            occupied={(source.grid_x, source.grid_y), (middle.grid_x, middle.grid_y), (target.grid_x, target.grid_y)},
            source_port="right",
            target_port="left",
        )

        self.assertNotIn((1.0, 0.0), self.router.route_traffic_points(route))

    def test_duplicate_connection_returns_existing_connection(self):
        document = OrgGridDocument()
        source = document.add_node("A", "Uno", 0, 0, "#09519F")
        target = document.add_node("B", "Dos", 1, 0, "#09519F")

        first = document.add_connection(source.id, target.id, source_port="right", target_port="left")
        second = document.add_connection(source.id, target.id, source_port="right", target_port="left")

        self.assertIs(first, second)
        self.assertEqual(len(document.connections), 1)
        self.assertEqual(len(self.router.route_document(document)), 1)

    def test_fallback_route_is_orthogonal_when_astar_fails(self):
        router = ManhattanRouter(self.engine)
        router._astar = lambda *args, **kwargs: None

        route = router.route(
            self._node(0, 0),
            self._node(2, 1),
            occupied={(0, 0), (2, 1)},
            source_port="right",
            target_port="left",
        )

        for start, end in zip(route, route[1:]):
            self.assertTrue(start[0] == end[0] or start[1] == end[1])

    def _node(self, grid_x, grid_y):
        return OrgGridDocument().add_node("Nombre", "Cargo", grid_x, grid_y, "#09519F")


if __name__ == "__main__":
    unittest.main()
