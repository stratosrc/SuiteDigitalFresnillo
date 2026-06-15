import unittest

from App_TestData.domain.redaction_history import make_history_action, redo_last_action, undo_last_action


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
