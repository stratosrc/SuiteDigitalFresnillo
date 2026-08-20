import unittest

from App_Organigrama.ui.canvas_visibility import (
    screen_box_intersects_viewport,
    screen_points_intersect_viewport,
)
from App_Organigrama.ui.canvas_hit_testing import find_tagged_entity_ids


class FakeCanvas:
    def find_overlapping(self, *_bounds):
        return (1, 2, 3)

    def gettags(self, item_id):
        return {
            1: ("connection", "connection:a"),
            2: ("node", "node:n1"),
            3: ("connection", "connection:b"),
        }[item_id]


class OrgCanvasVisibilityTests(unittest.TestCase):
    def test_box_inside_or_within_overscan_is_visible(self):
        self.assertTrue(screen_box_intersects_viewport(20, 30, 80, 90, 800, 600))
        self.assertTrue(
            screen_box_intersects_viewport(-120, 20, -80, 80, 800, 600)
        )

    def test_box_beyond_overscan_is_culled(self):
        self.assertFalse(
            screen_box_intersects_viewport(-400, 20, -300, 80, 800, 600)
        )
        self.assertFalse(
            screen_box_intersects_viewport(1100, 20, 1200, 80, 800, 600)
        )

    def test_route_bounding_box_crossing_viewport_is_visible(self):
        self.assertTrue(
            screen_points_intersect_viewport(
                [(-500, 300), (1200, 300)],
                800,
                600,
            )
        )

    def test_tagged_hit_testing_returns_only_requested_visible_entities(self):
        self.assertEqual(
            find_tagged_entity_ids(FakeCanvas(), 10, 10, "connection"),
            ["b", "a"],
        )


if __name__ == "__main__":
    unittest.main()
