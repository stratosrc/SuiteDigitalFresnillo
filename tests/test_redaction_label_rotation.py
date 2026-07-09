import unittest
from unittest.mock import Mock, patch

import fitz

from App_TestData.services.redaction_exporter import RedactionPdfExporter


class RedactionLabelRotationTests(unittest.TestCase):
    def test_rotated_page_uses_rotation_for_label_text(self):
        exporter = RedactionPdfExporter({})
        page = Mock()
        page.rotation = 90
        document = [page]
        rectangles = [
            {
                "page": 0,
                "x1": 10.0,
                "y1": 20.0,
                "x2": 30.0,
                "y2": 40.0,
                "rect": fitz.Rect(10, 20, 30, 40),
                "final_number": "#1.1",
            }
        ]

        with patch("App_TestData.services.redaction_exporter.fitz_text_width", return_value=12.0):
            exporter._draw_rectangle_labels(document, rectangles)

        self.assertTrue(page.draw_rect.called)
        page.insert_textbox.assert_called_once()
        self.assertEqual(page.insert_textbox.call_args.kwargs["rotate"], 90)
        self.assertEqual(page.insert_textbox.call_args.kwargs["align"], fitz.TEXT_ALIGN_CENTER)

    def test_unrotated_page_keeps_default_label_rotation(self):
        exporter = RedactionPdfExporter({})
        page = Mock()
        page.rotation = 0
        document = [page]
        rectangles = [
            {
                "page": 0,
                "x1": 10.0,
                "y1": 20.0,
                "x2": 30.0,
                "y2": 40.0,
                "rect": fitz.Rect(10, 20, 30, 40),
                "final_number": "#1.1",
            }
        ]

        with patch("App_TestData.services.redaction_exporter.fitz_text_width", return_value=12.0):
            exporter._draw_rectangle_labels(document, rectangles)

        self.assertEqual(page.insert_textbox.call_args.kwargs["rotate"], 0)


if __name__ == "__main__":
    unittest.main()
