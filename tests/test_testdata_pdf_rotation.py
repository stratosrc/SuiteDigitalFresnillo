import unittest

import fitz

from App_TestData.domain.document_state import DocumentState
from App_TestData.services.pdf_service import PDFManager


class _CallbacksStub:
    def request_pdf_file_path(self):
        return None

    def clear_document_view(self) -> None:
        pass

    def set_status(self, message: str) -> None:
        pass

    def show_error(self, title: str, message: str) -> None:
        pass

    def get_canvas_width(self) -> int:
        return 1000

    def draw_page_image(self, image, width: int, height: int) -> None:
        pass

    def update_page_controls(self, current_page: int, total_pages: int) -> None:
        pass

    def update_zoom_label(self) -> None:
        pass

    def draw_rectangle(self, rectangle, coords, is_selected):
        return {}


class PdfRotationCoordinateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = fitz.open()
        self.page = self.document.new_page(width=100, height=200)
        self.state = DocumentState(
            pdf_document=self.document,
            current_page=0,
            current_zoom=2,
        )
        self.manager = PDFManager(self.state, _CallbacksStub(), {})

    def tearDown(self) -> None:
        self.document.close()

    def test_pdf_rect_to_canvas_respects_page_rotation(self):
        self.page.set_rotation(90)
        rectangle = {"x1": 10.0, "y1": 20.0, "x2": 30.0, "y2": 40.0}

        canvas_rect = self.manager.pdf_rect_to_canvas(rectangle)

        self.assertEqual(canvas_rect, (320.0, 20.0, 360.0, 60.0))

    def test_canvas_to_pdf_rect_round_trips_across_rotations(self):
        rectangle = {"x1": 10.0, "y1": 20.0, "x2": 30.0, "y2": 40.0}

        for rotation in (0, 90, 180, 270):
            with self.subTest(rotation=rotation):
                self.page.set_rotation(rotation)
                canvas_rect = self.manager.pdf_rect_to_canvas(rectangle)
                pdf_rect = self.manager.canvas_to_pdf_rect(*canvas_rect)
                self.assertEqual(pdf_rect, (10.0, 20.0, 30.0, 40.0))


if __name__ == "__main__":
    unittest.main()
