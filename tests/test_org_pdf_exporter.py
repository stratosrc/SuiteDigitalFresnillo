import tempfile
import unittest
from pathlib import Path

import fitz

from App_Organigrama.exporters import PdfOrgChartExporter
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.engine import (
    HORIZONTAL_ORIENTATION,
    PageLayout,
    RenderingEngine,
    VERTICAL_ORIENTATION,
)
from App_Organigrama.routing.manhattan_router import ManhattanRouter


class OrgPdfExporterTests(unittest.TestCase):
    def test_watermark_fits_inside_centered_eighty_percent_page_area(self):
        engine = RenderingEngine()
        exporter = PdfOrgChartExporter(engine, ManhattanRouter(engine))

        for page_width, page_height in ((1000.0, 500.0), (500.0, 1000.0)):
            with self.subTest(page=(page_width, page_height)):
                layout = PageLayout(
                    width=page_width,
                    height=page_height,
                    margin_left=0,
                    margin_top=0,
                    margin_right=0,
                    margin_bottom=0,
                    header_height=0,
                )
                watermark_width, watermark_height = (
                    exporter._watermark_dimensions(layout)
                )

                self.assertLessEqual(watermark_width, page_width * 0.8)
                self.assertLessEqual(watermark_height, page_height * 0.8)
                self.assertTrue(
                    abs(watermark_width - (page_width * 0.8)) < 0.001
                    or abs(watermark_height - (page_height * 0.8)) < 0.001
                )
                self.assertAlmostEqual(
                    watermark_width / watermark_height,
                    465 / 633,
                )

    def test_role_lines_are_not_underlined_in_shared_layout(self):
        document = self._build_document(HORIZONTAL_ORIENTATION)
        node = next(iter(document.nodes.values()))

        role_lines = [
            line
            for line in RenderingEngine().layout_node(node).lines
            if not line.is_bold
        ]

        self.assertTrue(role_lines)
        self.assertTrue(all(not line.is_underlined for line in role_lines))

    def test_exports_single_page_for_horizontal_and_vertical_orientation(self):
        for orientation in (HORIZONTAL_ORIENTATION, VERTICAL_ORIENTATION):
            with self.subTest(orientation=orientation):
                document = self._build_document(orientation)
                with tempfile.TemporaryDirectory() as temp_dir:
                    output_path = Path(temp_dir) / f"organigrama-{orientation}.pdf"
                    exporter = PdfOrgChartExporter(RenderingEngine(), ManhattanRouter(RenderingEngine()))

                    result_path = exporter.export(document, output_path)

                    self.assertTrue(result_path.exists())
                    with fitz.open(result_path) as pdf:
                        self.assertEqual(len(pdf), 1)

    def test_digital_pdf_page_expands_to_content_width(self):
        document = OrgGridDocument(
            title="Organigrama digital",
            period="2026",
            show_logos=False,
        )
        document.add_node("Persona Uno", "Cargo Uno", 0, 0, "#09519F")
        document.add_node("Persona Dos", "Cargo Dos", 20, 0, "#3C8AC9")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "organigrama-digital.pdf"
            engine = RenderingEngine()
            PdfOrgChartExporter(engine, ManhattanRouter(engine)).export(
                document,
                output_path,
            )

            with fitz.open(output_path) as pdf:
                self.assertEqual(len(pdf), 1)
                self.assertGreater(pdf[0].rect.width, 792)
                self.assertGreaterEqual(pdf[0].rect.height, 612)

    def test_very_wide_digital_pdf_uses_compatible_media_box_and_user_unit(self):
        document = OrgGridDocument(
            title="Organigrama digital ancho",
            show_logos=False,
        )
        document.add_node("Persona Uno", "Cargo Uno", 0, 0, "#09519F")
        document.add_node("Persona Dos", "Cargo Dos", 100, 0, "#3C8AC9")

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "organigrama-digital-ancho.pdf"
            engine = RenderingEngine()
            PdfOrgChartExporter(engine, ManhattanRouter(engine)).export(
                document,
                output_path,
            )

            with fitz.open(output_path) as pdf:
                page = pdf[0]
                user_unit_type, user_unit_value = pdf.xref_get_key(
                    page.xref,
                    "UserUnit",
                )
                spans = [
                    span
                    for block in page.get_text("dict")["blocks"]
                    if "lines" in block
                    for line in block["lines"]
                    for span in line["spans"]
                ]

                self.assertEqual(user_unit_type, "int")
                self.assertGreater(int(user_unit_value), 1)
                self.assertLessEqual(page.mediabox.width, 14_000)
                self.assertGreater(page.rect.width, page.mediabox.width)
                self.assertGreaterEqual(
                    min(span["size"] for span in spans),
                    8,
                )
                self.assertGreaterEqual(
                    max(span["size"] for span in spans),
                    70,
                )

    def test_internal_page_mode_remains_available_for_image_conversion(self):
        document = self._build_document(HORIZONTAL_ORIENTATION)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "organigrama-para-imagen.pdf"
            engine = RenderingEngine()
            PdfOrgChartExporter(engine, ManhattanRouter(engine)).export(
                document,
                output_path,
                digital=False,
            )

            with fitz.open(output_path) as pdf:
                page_layout = engine.get_page_layout(HORIZONTAL_ORIENTATION)
                self.assertAlmostEqual(pdf[0].rect.width, page_layout.width)
                self.assertAlmostEqual(pdf[0].rect.height, page_layout.height)

    def _build_document(self, orientation):
        document = OrgGridDocument(title="Directorio", period="2026", page_orientation=orientation)
        first = document.add_node("Persona Uno", "Cargo Uno", 0, 0, "#09519F")
        second = document.add_node("Persona Dos", "Cargo Dos", 1, 1, "#09519F")
        third = document.add_node("Persona Tres", "Cargo Tres", -1, 1, "#09519F")
        document.add_connection(first.id, second.id)
        document.add_connection(first.id, third.id)
        return document


if __name__ == "__main__":
    unittest.main()
