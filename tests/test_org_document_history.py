import unittest

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.models.history import DocumentHistory


class OrgDocumentHistoryTests(unittest.TestCase):
    def test_undo_and_redo_restore_document_snapshots(self):
        document = OrgGridDocument()
        history = DocumentHistory(document)

        node = document.add_node("Persona", "Cargo", 0, 0, "#09519F")
        history.record(document)
        document.update_node(node.id, "Persona editada", "Cargo", "#09519F")
        history.record(document)

        restored = history.undo()
        self.assertEqual(restored.nodes[node.id].name, "Persona")
        self.assertTrue(history.can_redo)

        restored = history.redo()
        self.assertEqual(restored.nodes[node.id].name, "Persona editada")

    def test_new_change_clears_redo_and_saved_state_controls_dirty_flag(self):
        document = OrgGridDocument()
        history = DocumentHistory(document)
        document.add_node("Uno", "Cargo", 0, 0, "#09519F")
        history.record(document)
        self.assertTrue(history.is_dirty)

        document = history.undo()
        self.assertFalse(history.is_dirty)
        document.add_node("Dos", "Cargo", 1, 0, "#09519F")
        history.record(document)

        self.assertFalse(history.can_redo)
        history.mark_saved(document)
        self.assertFalse(history.is_dirty)


if __name__ == "__main__":
    unittest.main()
