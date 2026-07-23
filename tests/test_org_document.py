import unittest

from App_Organigrama.models.document import OrgGridDocument


class OrgGridDocumentTests(unittest.TestCase):
    def test_new_document_uses_empty_title_for_placeholder(self):
        document = OrgGridDocument()
        self.assertEqual(document.title, "")

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

if __name__ == "__main__":
    unittest.main()
