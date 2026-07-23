import unittest
from unittest.mock import Mock, patch

import fitz

from App_TestData.domain.document_state import DocumentState
from App_TestData.services.pdf_service import PDFManager
from App_TestData.services.redaction_exporter import RedactionPdfExporter


class _CallbacksStub:
    def request_pdf_file_path(self):
        return None

    def clear_document_view(self):
        pass

    def set_status(self, message):
        pass

    def show_error(self, title, message):
        pass

    def get_canvas_width(self):
        return 800

    def draw_page_image(self, image, width, height):
        pass

    def update_page_controls(self, current_page, total_pages):
        pass

    def update_zoom_label(self):
        pass

    def draw_rectangle(self, rectangle, coords, is_selected):
        return {}


def _rects_are_close(first, second, tolerance=0.01):
    return all(
        abs(first_value - second_value) <= tolerance
        for first_value, second_value in zip(first, second)
    )


def _transform_direction(direction, matrix):
    x, y = direction
    return (
        (x * matrix.a) + (y * matrix.c),
        (x * matrix.b) + (y * matrix.d),
    )


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

    def test_real_drawing_keeps_box_and_label_upright_across_rotations(self):
        document = fitz.open()
        for rotation in (0, 90, 180, 270):
            page = document.new_page(width=400, height=600)
            page.set_rotation(rotation)

        state = DocumentState(pdf_document=document, current_zoom=1)
        manager = PDFManager(state, _CallbacksStub(), {})
        rectangles = []
        expected_canvas_rectangles = {}

        for page_index, rotation in enumerate((0, 90, 180, 270)):
            state.current_page = page_index
            page = document[page_index]
            canvas_rectangles = (
                fitz.Rect(40, 40, 220, 100),
                fitz.Rect(
                    page.rect.width - 220,
                    page.rect.height - 100,
                    page.rect.width - 40,
                    page.rect.height - 40,
                ),
            )
            expected_canvas_rectangles[page_index] = canvas_rectangles
            for label_index, canvas_rect in enumerate(canvas_rectangles, start=1):
                pdf_rect = manager.canvas_to_pdf_rect(*canvas_rect)
                rectangles.append(
                    {
                        "page": page_index,
                        "x1": pdf_rect[0],
                        "y1": pdf_rect[1],
                        "x2": pdf_rect[2],
                        "y2": pdf_rect[3],
                        "final_number": f"#{rotation}.{label_index}",
                    }
                )

        exporter = RedactionPdfExporter({})
        exporter._apply_redactions(document, rectangles)
        exporter._draw_rectangle_labels(document, rectangles)

        for page_index, rotation in enumerate((0, 90, 180, 270)):
            with self.subTest(rotation=rotation):
                page = document[page_index]
                page_text = page.get_text()
                self.assertIn(f"#{rotation}.1", page_text)
                self.assertIn(f"#{rotation}.2", page_text)

                visible_drawing_rectangles = [
                    fitz.Rect(drawing["rect"]) * page.rotation_matrix
                    for drawing in page.get_drawings()
                    if drawing["color"] == (0.0, 0.0, 0.0)
                ]
                for expected in expected_canvas_rectangles[page_index]:
                    self.assertTrue(
                        any(_rects_are_close(actual, expected) for actual in visible_drawing_rectangles)
                    )

                text_lines = [
                    line
                    for block in page.get_text("dict")["blocks"]
                    if "lines" in block
                    for line in block["lines"]
                ]
                for line in text_lines:
                    visible_direction = _transform_direction(
                        line["dir"],
                        page.rotation_matrix,
                    )
                    self.assertAlmostEqual(visible_direction[0], 1.0)
                    self.assertAlmostEqual(visible_direction[1], 0.0)

        document.close()


if __name__ == "__main__":
    unittest.main()
