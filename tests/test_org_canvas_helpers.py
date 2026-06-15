import unittest

from App_Organigrama.models.document import Connection, OrgNode
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.routing.manhattan_router import ConnectionRoute
from App_Organigrama.ui.canvas_hit_testing import distance_to_segment, find_connection_at_screen, nearest_port
from App_Organigrama.ui.canvas_viewport import screen_to_grid, screen_to_subgrid, world_to_screen


class OrgCanvasHelperTests(unittest.TestCase):
    def test_viewport_coordinate_conversions(self):
        engine = RenderingEngine()
        self.assertEqual(world_to_screen(10, 20, pan_x=5, pan_y=7, zoom=2), (25, 47))
        self.assertEqual(screen_to_grid(505, 527, pan_x=5, pan_y=7, zoom=2, rendering_engine=engine), (1, 1))
        self.assertEqual(screen_to_subgrid(255, 267, pan_x=5, pan_y=7, zoom=2, rendering_engine=engine), (0.5, 0.5))

    def test_connection_hit_testing(self):
        engine = RenderingEngine()
        route = ConnectionRoute(
            connection=Connection(source_id="a", target_id="b"),
            points=((0, 0), (1, 0)),
        )

        self.assertEqual(distance_to_segment(10, 5, (0, 0), (20, 0)), 5)
        self.assertIs(route, find_connection_at_screen([route], 125, 2, engine, lambda x, y: (x, y)))

    def test_nearest_port(self):
        engine = RenderingEngine()
        node = OrgNode("Nombre", "Cargo", 0, 0, "#09519F")
        layout = engine.layout_node(node, include_logo=False)

        self.assertEqual(nearest_port(node, 0, -50, layout, 1.0, lambda x, y: (x, y)), "top")
        self.assertEqual(nearest_port(node, int(layout.box.right + 1), int(layout.center_y), layout, 1.0, lambda x, y: (x, y)), "right")


if __name__ == "__main__":
    unittest.main()
