import unittest

from App_TestData.domain.redaction_editing import get_classification_display_name
from App_TestData.domain.redaction_history import make_history_action, redo_last_action, undo_last_action
from App_TestData.ui.interactions.canvas_redactions import _apply_dialog_result_to_rectangle


def rectangle(rectangle_id=1, x1=10, x2=20):
    return {
        "id": rectangle_id,
        "order": rectangle_id,
        "page": 0,
        "x1": x1,
        "y1": 10,
        "x2": x2,
        "y2": 20,
        "canvas_rect_id": 99,
        "canvas_text_id": 100,
    }


class RedactionHistoryTests(unittest.TestCase):
    def test_classification_display_names_preserve_accents(self):
        self.assertEqual(
            get_classification_display_name("reserved"),
            "Información Reservada",
        )
        self.assertEqual(
            get_classification_display_name("confidential"),
            "Información Confidencial",
        )

    def test_editing_reserved_rectangle_keeps_correct_encoding(self):
        rectangle_data = rectangle()
        _apply_dialog_result_to_rectangle(
            None,
            rectangle_data,
            {
                "classification": "reserved",
                "rows": 1,
                "paragraphs": 1,
                "legal_basis": "",
                "reason": "",
            },
        )

        self.assertEqual(rectangle_data["concept_name"], "Información Reservada")
        self.assertEqual(rectangle_data["display_text"], "Información Reservada")

    def test_editing_custom_rectangle_preserves_text(self):
        rectangle_data = rectangle()
        _apply_dialog_result_to_rectangle(
            None,
            rectangle_data,
            {
                "classification": "custom",
                "rows": 1,
                "paragraphs": 1,
                "custom_text": "Texto exactamente como lo escribí.",
            },
        )

        self.assertEqual(rectangle_data["label"], "P")
        self.assertEqual(rectangle_data["display_text"], "Personalizado")
        self.assertEqual(rectangle_data["custom_text"], "Texto exactamente como lo escribí.")

    def test_undo_and_redo_create(self):
        created = rectangle()
        action = make_history_action("create", rectangle=created)

        rectangles, undo_stack, redo_stack, affected = undo_last_action([created], [action], [])
        self.assertEqual(rectangles, [])
        self.assertEqual(affected["id"], 1)
        self.assertEqual(len(undo_stack), 0)
        self.assertEqual(len(redo_stack), 1)

        rectangles, undo_stack, redo_stack, affected = redo_last_action(rectangles, undo_stack, redo_stack)
        self.assertEqual(rectangles[0]["id"], 1)
        self.assertIsNone(rectangles[0]["canvas_rect_id"])
        self.assertIsNone(rectangles[0]["canvas_text_id"])
        self.assertEqual(affected["id"], 1)

    def test_undo_and_redo_update(self):
        before = rectangle(x1=10, x2=20)
        after = rectangle(x1=30, x2=40)
        action = make_history_action("update", before=before, after=after)

        rectangles, undo_stack, redo_stack, _affected = undo_last_action([after], [action], [])
        self.assertEqual(rectangles[0]["x1"], 10)

        rectangles, _undo_stack, _redo_stack, _affected = redo_last_action(rectangles, undo_stack, redo_stack)
        self.assertEqual(rectangles[0]["x1"], 30)


if __name__ == "__main__":
    unittest.main()
