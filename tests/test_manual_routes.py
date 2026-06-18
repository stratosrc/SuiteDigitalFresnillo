import unittest

from App_Organigrama.routing.manual_routes import (
    GridBox,
    build_manual_route,
    move_bend_point,
    move_intermediate_segment,
    route_crosses_boxes,
)


class ManualRouteTests(unittest.TestCase):
    def test_moves_horizontal_segment_only_vertically(self):
        route = [(0.0, 0.0), (0.0, 0.5), (2.0, 0.5), (2.0, 0.0)]
        moved = move_intermediate_segment(route, 1, (9.0, 1.5))
        self.assertEqual(moved, [(0.0, 0.0), (0.0, 1.5), (2.0, 1.5), (2.0, 0.0)])

    def test_moves_vertical_segment_only_horizontally(self):
        route = [(0.0, 0.0), (0.5, 0.0), (0.5, 2.0), (0.0, 2.0)]
        moved = move_intermediate_segment(route, 1, (1.5, 9.0))
        self.assertEqual(moved, [(0.0, 0.0), (1.5, 0.0), (1.5, 2.0), (0.0, 2.0)])

    def test_segment_move_preserves_exact_port_endpoints(self):
        route = [(0.4536, 0.0), (0.5, 0.0), (0.5, 1.0), (1.5, 1.0), (1.5464, 1.0)]

        moved = move_intermediate_segment(route, 2, (9.0, 2.0))

        self.assertEqual(moved[0], (0.4536, 0.0))
        self.assertEqual(moved[-1], (1.5464, 1.0))

    def test_bend_point_can_move_freely_and_keeps_route_orthogonal(self):
        route = [(0.4536, 0.0), (0.5, 0.0), (0.5, 1.0), (1.5, 1.0), (1.5464, 1.0)]

        moved = move_bend_point(route, 2, (1.0, 1.5))

        self.assertEqual(moved[0], route[0])
        self.assertEqual(moved[-1], route[-1])
        for start, end in zip(moved, moved[1:]):
            self.assertTrue(start[0] == end[0] or start[1] == end[1])

    def test_free_bend_shape_survives_manual_route_rebuild(self):
        route = [(0.4536, 0.0), (0.5, 0.0), (0.5, 1.0), (1.5464, 1.0)]
        moved = move_bend_point(route, 2, (1.0, 2.0))

        rebuilt = build_manual_route(
            route[0],
            route[-1],
            moved[1:-1],
            "right",
            "left",
        )

        self.assertEqual(rebuilt, moved)

    def test_reconnects_manual_route_when_endpoint_moves(self):
        rebuilt = build_manual_route(
            (1.0, 3.0),
            (4.0, 5.0),
            [(0.0, 1.0), (2.0, 1.0), (2.0, 4.0)],
            "bottom",
            "top",
        )
        self.assertEqual(rebuilt[0], (1.0, 3.0))
        self.assertEqual(rebuilt[1][0], 1.0)
        self.assertEqual(rebuilt[-2][0], 4.0)
        self.assertEqual(rebuilt[-1], (4.0, 5.0))

    def test_detects_route_crossing_node_interior(self):
        box = GridBox(left=0.6, top=0.6, right=1.4, bottom=1.4)
        self.assertTrue(route_crosses_boxes([(0.0, 1.0), (2.0, 1.0)], [box]))
        self.assertFalse(route_crosses_boxes([(0.0, 0.5), (2.0, 0.5)], [box]))


if __name__ == "__main__":
    unittest.main()
