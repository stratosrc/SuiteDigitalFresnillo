from pathlib import Path
import tempfile
import unittest

import fitz

from App_TestData.services.redaction_exporter import RedactionPdfExporter
from components.shared.atomic_output import OutputCancelled, write_atomic_output


class AtomicOutputTests(unittest.TestCase):
    def test_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "output.pdf"
            target.write_bytes(b"previous")

            with self.assertRaises(RuntimeError):
                write_atomic_output(
                    target,
                    lambda temporary: (
                        temporary.write_bytes(b"partial"),
                        (_ for _ in ()).throw(RuntimeError("failed")),
                    ),
                )

            self.assertEqual(target.read_bytes(), b"previous")

    def test_cancelled_testdata_export_preserves_existing_pdf(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.pdf"
            target = root / "output.pdf"
            source_document = fitz.open()
            source_document.new_page()
            source_document.save(source)
            source_document.close()
            target.write_bytes(b"previous")

            with self.assertRaises(OutputCancelled):
                RedactionPdfExporter({}).export(
                    str(source),
                    str(target),
                    [],
                    cancel_check=lambda: True,
                )

            self.assertEqual(target.read_bytes(), b"previous")

    def test_cancelled_output_is_not_committed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "output.pdf"
            target.write_bytes(b"previous")

            with self.assertRaises(OutputCancelled):
                write_atomic_output(
                    target,
                    lambda temporary: temporary.write_bytes(b"new"),
                    should_commit=lambda: False,
                )

            self.assertEqual(target.read_bytes(), b"previous")


if __name__ == "__main__":
    unittest.main()
