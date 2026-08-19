from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import Mock

import fitz
from PIL import Image

from App_TestData.config.settings import PDF_WATERMARK_LOGO_PATH
from App_TestData.services.redaction_exporter import (
    EXPORT_QUALITY_COMPACT,
    RedactionPdfExporter,
)
from App_TestData.ui.dialogs.export_dialog import ExportDialog


class TestDataPdfOptimizationTests(unittest.TestCase):
    def test_export_subsets_fonts_and_uses_lossless_compression(self):
        document = Mock()

        RedactionPdfExporter._save_optimized(document, "output.pdf")

        document.subset_fonts.assert_called_once_with()
        document.save.assert_called_once_with(
            "output.pdf",
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            use_objstms=1,
            compression_effort=100,
        )

    def test_compact_export_reduces_high_resolution_images(self):
        document = Mock()

        RedactionPdfExporter._rewrite_images_for_quality(
            document,
            EXPORT_QUALITY_COMPACT,
        )

        document.rewrite_images.assert_called_once_with(
            dpi_threshold=200,
            dpi_target=150,
            quality=82,
            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True,
            set_to_gray=False,
        )

    def test_standard_export_does_not_rewrite_images(self):
        document = Mock()

        RedactionPdfExporter._rewrite_images_for_quality(document, "standard")

        document.rewrite_images.assert_not_called()

    def test_export_dialog_forwards_selected_quality(self):
        callback = Mock()
        dialog = SimpleNamespace(
            destroy=Mock(),
            export_callback=callback,
            quality_var=Mock(get=Mock(return_value=EXPORT_QUALITY_COMPACT)),
        )

        ExportDialog._export_standard(dialog)

        callback.assert_called_once_with(export_quality=EXPORT_QUALITY_COMPACT)

    def test_invalid_export_quality_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Calidad de exportación no compatible"):
            RedactionPdfExporter({}).export(b"", "output.pdf", [], export_quality="unknown")

    def test_compact_export_keeps_redaction_label_visibly_rendered(self):
        scan = Image.new("RGB", (2000, 2800), "white")
        scan_stream = BytesIO()
        scan.save(scan_stream, format="JPEG", quality=90)

        source = fitz.open()
        source_page = source.new_page(width=595, height=842)
        source_page.insert_image(source_page.rect, stream=scan_stream.getvalue())
        source_bytes = source.tobytes()
        source.close()

        rectangles = [
            {
                "id": 1,
                "order": 1,
                "page": 0,
                "x1": 150,
                "y1": 100,
                "x2": 450,
                "y2": 160,
                "classification": "custom",
                "concept_id": None,
                "concept_name": "Personalizado",
                "custom_text": "Dato testado.",
                "rows": 1,
                "paragraphs": 1,
                "label": "P",
                "description": "Dato testado.",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / "compact.pdf"
            RedactionPdfExporter({}).export(
                source_bytes,
                str(target_path),
                rectangles,
                export_quality=EXPORT_QUALITY_COMPACT,
            )
            result = fitz.open(target_path)
            page = result[0]
            label_span = next(
                span
                for block in page.get_text("dict")["blocks"]
                if "lines" in block
                for line in block["lines"]
                for span in line["spans"]
                if span["text"] == "P.1"
            )
            label_pixmap = page.get_pixmap(
                matrix=fitz.Matrix(2, 2),
                clip=fitz.Rect(label_span["bbox"]),
                colorspace=fitz.csRGB,
                alpha=False,
            )
            dark_samples = sum(value < 100 for value in label_pixmap.samples)
            result.close()

        self.assertGreater(dark_samples, 0)

    def test_watermark_is_downscaled_and_keeps_transparency(self):
        watermark_path = Path(PDF_WATERMARK_LOGO_PATH)

        with Image.open(watermark_path) as watermark:
            rgba = watermark.convert("RGBA")
            alpha_min, alpha_max = rgba.getchannel("A").getextrema()

            self.assertLessEqual(watermark.width, 955)
            self.assertLessEqual(watermark.height, 1262)
            self.assertLess(watermark_path.stat().st_size, 100_000)
            self.assertEqual(alpha_min, 0)
            self.assertGreaterEqual(alpha_max, 250)


if __name__ == "__main__":
    unittest.main()
