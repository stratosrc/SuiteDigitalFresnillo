import tempfile
import unittest
from pathlib import Path

import fitz

from App_Organigrama.exporters import PdfOrgChartExporter
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.rendering.engine import HORIZONTAL_ORIENTATION, RenderingEngine, VERTICAL_ORIENTATION
from App_Organigrama.routing.manhattan_router import ManhattanRouter


class OrgPdfExporterTests(unittest.TestCase):
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
