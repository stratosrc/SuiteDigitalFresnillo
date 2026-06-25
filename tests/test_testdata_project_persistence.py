from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import fitz

from App_TestData.domain.document_state import DocumentState
from App_TestData.services.project_persistence import (
    EMBEDDED_PDF_NAME,
    PROJECT_METADATA_NAME,
    load_project,
    save_project,
)


class TestDataProjectPersistenceTests(unittest.TestCase):
    def test_portable_project_opens_without_original_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_pdf = root / "original.pdf"
            project_path = root / "portable.td"
            self._create_pdf(source_pdf)

            state = DocumentState(
                current_pdf_path=str(source_pdf),
                current_page=0,
                current_zoom=1.25,
                censored_rectangles=[
                    {
                        "id": 1,
                        "page": 0,
                        "x1": 10.0,
                        "y1": 20.0,
                        "x2": 100.0,
                        "y2": 120.0,
                        "label": "Prueba",
                    }
                ],
            )
            save_project(state, project_path)
            source_pdf.unlink()

            loaded = load_project(project_path)
            try:
                self.assertTrue(loaded.pdf_path.is_file())
                self.assertEqual(loaded.payload["version"], 2)
                self.assertEqual(loaded.payload["current_zoom"], 1.25)
                self.assertEqual(len(loaded.payload["rectangles"]), 1)
                with fitz.open(loaded.pdf_path) as document:
                    self.assertEqual(len(document), 1)
            finally:
                extracted_path = loaded.pdf_path
                loaded.close()

            self.assertFalse(extracted_path.exists())

    def test_portable_project_contains_metadata_and_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_pdf = root / "source.pdf"
            project_path = root / "project.td"
            self._create_pdf(source_pdf)

            save_project(DocumentState(current_pdf_path=str(source_pdf)), project_path)

            self.assertTrue(zipfile.is_zipfile(project_path))
            with zipfile.ZipFile(project_path) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {PROJECT_METADATA_NAME, EMBEDDED_PDF_NAME},
                )

    def test_legacy_json_project_remains_supported(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source_pdf = root / "legacy.pdf"
            project_path = root / "legacy.td"
            self._create_pdf(source_pdf)
            project_path.write_text(
                json.dumps(
                    {
                        "app": "testdata",
                        "version": 1,
                        "pdf_path": str(source_pdf),
                        "pdf_sha256": "",
                        "rectangles": [],
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_project(project_path)
            try:
                self.assertEqual(loaded.pdf_path, source_pdf)
            finally:
                loaded.close()
            self.assertTrue(source_pdf.exists())

    @staticmethod
    def _create_pdf(path: Path) -> None:
        document = fitz.open()
        document.new_page()
        document.save(path)
        document.close()


if __name__ == "__main__":
    unittest.main()
