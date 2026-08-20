import os
import tempfile
import unittest
from unittest.mock import Mock

import fitz

from App_TestData.domain.document_state import DocumentState
from App_TestData.services.pdf_service import PDFManager


class DummyCallbacks:
    def request_pdf_file_path(self):
        return None

    def clear_document_view(self):
        return None

    def set_status(self, message):
        self.status = message

    def show_error(self, title, message):
        raise AssertionError(f"{title}: {message}")

    def get_canvas_width(self):
        return 200

    def draw_page_image(self, image, width, height):
        return None

    def update_page_controls(self, current_page, total_pages):
        return None

    def update_zoom_label(self):
        return None

    def draw_rectangle(self, rectangle, coords, is_selected):
        return {}


class PdfManagerTests(unittest.TestCase):
    def test_generate_pdf_forwards_compact_quality(self):
        manager = PDFManager(DocumentState(), DummyCallbacks(), {})
        manager._redaction_exporter = Mock()

        manager.generate_pdf(
            "output.pdf",
            pdf_bytes=b"pdf",
            rectangles=[],
            export_quality="compact",
        )

        manager._redaction_exporter.export.assert_called_once_with(
            b"pdf",
            "output.pdf",
            [],
            None,
            None,
            "compact",
        )

    def test_canvas_to_pdf_rect_clamps_to_current_page(self):
        state = DocumentState()
        state.pdf_document = fitz.open()
        state.pdf_document.new_page(width=100, height=120)
        state.current_zoom = 1
        manager = PDFManager(state, DummyCallbacks(), {})

        self.assertEqual(manager.canvas_to_pdf_rect(-10, -5, 130, 150), (0, 0, 100, 120))
        state.pdf_document.close()

    def test_generate_pdf_uses_copied_rectangle_data(self):
        source = fitz.open()
        source.new_page(width=100, height=100)
        pdf_bytes = source.tobytes()
        source.close()

        state = DocumentState()
        manager = PDFManager(state, DummyCallbacks(), {})
        rectangles = [
            {
                "id": 1,
                "order": 1,
                "page": 0,
                "x1": 10,
                "y1": 10,
                "x2": 40,
                "y2": 30,
                "classification": "general",
                "concept_id": 1,
                "concept_name": "Nombre",
                "rows": 1,
                "paragraphs": 1,
                "label": "#1",
            }
        ]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as target:
            target_path = target.name
        try:
            manager.generate_pdf(target_path, pdf_bytes=pdf_bytes, rectangles=rectangles)
            self.assertTrue(os.path.getsize(target_path) > 0)
            self.assertNotIn("final_number", rectangles[0])
        finally:
            os.unlink(target_path)

    def test_generate_pdf_can_open_source_path_without_pdf_bytes(self):
        source = fitz.open()
        source.new_page(width=100, height=100)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as source_file:
            source_path = source_file.name
        source.save(source_path)
        source.close()

        state = DocumentState()
        manager = PDFManager(state, DummyCallbacks(), {})
        rectangles = [
            {
                "id": 1,
                "order": 1,
                "page": 0,
                "x1": 10,
                "y1": 10,
                "x2": 40,
                "y2": 30,
                "classification": "general",
                "concept_id": 1,
                "concept_name": "Nombre",
                "rows": 1,
                "paragraphs": 1,
                "label": "#1",
            }
        ]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as target:
            target_path = target.name
        try:
            manager.generate_pdf(target_path, source_path=source_path, rectangles=rectangles)
            self.assertTrue(os.path.getsize(target_path) > 0)
        finally:
            os.unlink(source_path)
            os.unlink(target_path)


if __name__ == "__main__":
    unittest.main()
