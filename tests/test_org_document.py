import unittest

from App_Organigrama.models.document import OrgGridDocument


class OrgGridDocumentTests(unittest.TestCase):
    def test_prevents_duplicate_node_cell_and_removes_connections(self):
        document = OrgGridDocument()
        first = document.add_node("A", "Directora", 0, 0, "#09519F")
        second = document.add_node("B", "Jefe", 1, 1, "#3C8AC9")
        with self.assertRaises(ValueError):
            document.add_node("C", "Analista", 0, 0, "#797E85")

        connection = document.add_connection(first.id, second.id)
        self.assertIsNotNone(connection)
        document.remove_node(first.id)
        self.assertEqual(document.connections, [])

    def test_blocked_points_are_normalized_and_toggleable(self):
        document = OrgGridDocument()
        self.assertTrue(document.toggle_blocked_point((1, 1)))
        self.assertTrue(document.has_blocked_point((1.0, 1.0)))
        self.assertFalse(document.toggle_blocked_point((1.0, 1.0)))
        self.assertFalse(document.has_blocked_point((1.0, 1.0)))


if __name__ == "__main__":
    unittest.main()
