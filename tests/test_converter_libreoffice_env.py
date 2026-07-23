import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from App_ConversorPDF.services.converter import PdfConverter


class ConverterLibreOfficeEnvTests(unittest.TestCase):
    def test_office_document_conversion_uses_libreoffice_env(self):
        source_path = Path("input.docx")
        target_path = Path("output.pdf")
        soffice_path = Path("/tmp/LibreOffice/Contents/MacOS/soffice")
        expected_env = {"SAL_USE_VCLPLUGIN": "svp"}
        converter = PdfConverter()

        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout="",
            stderr="",
        )

        with patch("App_ConversorPDF.services.converter.require_soffice_path", return_value=soffice_path):
            with patch(
                "App_ConversorPDF.services.converter.build_libreoffice_subprocess_env",
                return_value=expected_env,
            ) as build_env:
                with patch.object(converter, "_ensure_output_dir"):
                    with patch.object(converter, "_run_libreoffice", return_value=completed) as run_libreoffice:
                        with patch("App_ConversorPDF.services.converter.tempfile.TemporaryDirectory") as temporary_directory:
                            temp_root = Path.cwd() / "temp-conversion"
                            temporary_directory.return_value.__enter__.return_value = str(temp_root)
                            temporary_directory.return_value.__exit__.return_value = None
                            generated_pdf = temp_root / "out" / "input.pdf"

                            with patch("App_ConversorPDF.services.converter.shutil.copyfile"):
                                with patch.object(Path, "exists", autospec=True) as path_exists:
                                    path_exists.side_effect = lambda candidate: candidate == generated_pdf
                                    result = converter._convert_office_document(
                                        source_path,
                                        target_path,
                                        None,
                                    )

        build_env.assert_called_once_with(soffice_path)
        run_libreoffice.assert_called_once()
        self.assertEqual(run_libreoffice.call_args.args[1], expected_env)
        self.assertEqual(result, target_path)


if __name__ == "__main__":
    unittest.main()
