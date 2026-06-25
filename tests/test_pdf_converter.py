from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

import fitz

from App_ConversorPDF.services.converter import ConversionRequest, PdfConverter


class PdfConverterTests(unittest.TestCase):
    def test_extracts_selected_pages_from_existing_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "source.pdf"
            target_path = root / "selected.pdf"

            source_document = fitz.open()
            try:
                for page_number in range(1, 5):
                    page = source_document.new_page()
                    page.insert_text((72, 72), f"Pagina {page_number}")
                source_document.save(source_path)
            finally:
                source_document.close()

            saved_path = PdfConverter().convert(
                ConversionRequest(
                    source_path=source_path,
                    target_path=target_path,
                    sheet_name="2-3",
                )
            )

            with fitz.open(saved_path) as result_document:
                self.assertEqual(len(result_document), 2)

    def test_spreadsheet_selection_is_delegated_as_workbook_tabs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_path = root / "book.xlsx"
            target_path = root / "selected.pdf"
            source_path.write_bytes(b"spreadsheet")
            converter = PdfConverter()
            exporter = Mock()
            exporter.export.side_effect = (
                lambda _source, temporary, _selection: Path(temporary).write_bytes(b"%PDF")
            )
            converter._spreadsheet_exporter = exporter

            saved_path = converter.convert(
                ConversionRequest(
                    source_path=source_path,
                    target_path=target_path,
                    sheet_name="2-4",
                )
            )

            self.assertEqual(saved_path, target_path)
            exporter.export.assert_called_once()
            call_source, temporary_path, selection = exporter.export.call_args.args
            self.assertEqual(call_source, source_path)
            self.assertEqual(selection, "2-4")
            self.assertNotEqual(Path(temporary_path), target_path)


if __name__ == "__main__":
    unittest.main()
