import unittest

from App_Organigrama.rendering.palette import (
    LIGHT_BLUE,
    NEUTRAL_GRAY,
    PRIMARY_BLUE,
    SECONDARY_BLUE,
)
from App_Organigrama.samples.generate_performance_sample import (
    build_performance_document,
)


class OrgPerformanceSampleTests(unittest.TestCase):
    def test_sample_has_expected_hierarchy_and_connections(self):
        document = build_performance_document()

        color_counts = {
            color: sum(node.color == color for node in document.nodes.values())
            for color in (PRIMARY_BLUE, SECONDARY_BLUE, LIGHT_BLUE, NEUTRAL_GRAY)
        }

        self.assertEqual(len(document.nodes), 300)
        self.assertEqual(len(document.connections), 299)
        self.assertEqual(
            color_counts,
            {
                PRIMARY_BLUE: 1,
                SECONDARY_BLUE: 9,
                LIGHT_BLUE: 45,
                NEUTRAL_GRAY: 245,
            },
        )
        self.assertTrue(
            all(connection.source_id in document.nodes for connection in document.connections)
        )
        self.assertTrue(
            all(connection.target_id in document.nodes for connection in document.connections)
        )

    def test_sample_is_deterministic(self):
        first = build_performance_document().to_dict()
        second = build_performance_document().to_dict()

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
