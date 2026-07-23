import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from App_TestData.ui.interactions.canvas_redactions import cancel_active_interaction


class CancelInteractionTests(unittest.TestCase):
    def test_cancel_draw_deletes_draft_rectangle_and_resets_state(self):
        canvas = Mock()
        app = SimpleNamespace(
            drag_mode="draw",
            current_rect=42,
            pdf_canvas=canvas,
            active_rect_data=None,
            active_resize_corner="se",
            drag_start_x=10,
            drag_start_y=20,
            drag_original_coords=(10, 20, 30, 40),
            drag_original_rectangle=None,
        )

        cancel_active_interaction(app)

        canvas.delete.assert_called_once_with(42)
        self.assertIsNone(app.current_rect)
        self.assertIsNone(app.drag_mode)
        self.assertIsNone(app.active_resize_corner)

    def test_cancel_move_restores_original_rectangle_coordinates(self):
        canvas = Mock()
        pdf_manager = Mock()
        pdf_manager.pdf_rect_to_canvas.return_value = (10.0, 20.0, 30.0, 40.0)
        rectangle = {
            "x1": 100.0,
            "y1": 110.0,
            "x2": 120.0,
            "y2": 130.0,
            "canvas_rect_id": 7,
            "canvas_text_id": 8,
        }
        app = SimpleNamespace(
            drag_mode="move",
            current_rect=None,
            pdf_canvas=canvas,
            pdf_manager=pdf_manager,
            active_rect_data=rectangle,
            active_resize_corner=None,
            drag_start_x=0,
            drag_start_y=0,
            drag_original_coords=(1, 2, 3, 4),
            drag_original_rectangle={"x1": 10.0, "y1": 20.0, "x2": 30.0, "y2": 40.0},
        )

        cancel_active_interaction(app)

        self.assertEqual(
            (rectangle["x1"], rectangle["y1"], rectangle["x2"], rectangle["y2"]),
            (10.0, 20.0, 30.0, 40.0),
        )
        canvas.coords.assert_any_call(7, 10.0, 20.0, 30.0, 40.0)
        canvas.coords.assert_any_call(8, 20.0, 30.0)
        self.assertIsNone(app.drag_mode)


if __name__ == "__main__":
    unittest.main()
