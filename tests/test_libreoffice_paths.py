import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from App_ConversorPDF.services import libreoffice
from components.shared.app_registry import get_application


class LibreOfficePathTests(unittest.TestCase):
    def test_mac_vendor_soffice_is_detected(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            soffice_path = project_root / "App_ConversorPDF" / "vendor" / "LibreOffice" / "Contents" / "MacOS" / "soffice"
            soffice_path.parent.mkdir(parents=True)
            soffice_path.write_text("", encoding="utf-8")

            with patch.object(libreoffice, "_project_root", return_value=project_root):
                with patch.object(libreoffice, "_app_root", return_value=project_root / "App_ConversorPDF"):
                    detected_path = libreoffice.get_soffice_path()

        self.assertEqual(detected_path, soffice_path)

    def test_mac_vendor_python_is_resolved_from_framework(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            contents_root = Path(temp_dir) / "LibreOffice" / "Contents"
            soffice_path = contents_root / "MacOS" / "soffice"
            python_path = contents_root / "Frameworks" / "LibreOfficePython.framework" / "LibreOfficePython"
            soffice_path.parent.mkdir(parents=True)
            python_path.parent.mkdir(parents=True)
            soffice_path.write_text("", encoding="utf-8")
            python_path.write_text("", encoding="utf-8")

            detected_python = libreoffice.get_libreoffice_python_path(soffice_path)
            worker_env = libreoffice.build_libreoffice_subprocess_env(soffice_path)

        self.assertEqual(detected_python, python_path)
        self.assertEqual(worker_env["PYTHONHOME"], str(python_path.parent))
        self.assertIn(str(contents_root / "Frameworks"), worker_env["PYTHONPATH"])
        self.assertEqual(worker_env["UNO_PATH"], str(contents_root / "MacOS"))
        self.assertEqual(worker_env["SAL_USE_VCLPLUGIN"], "svp")

    def test_frozen_macos_bundle_detects_vendor_soffice_in_resources(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            app_root = Path(temp_dir) / "SuiteFresnillo.app" / "Contents"
            executable_path = app_root / "MacOS" / "SuiteFresnillo"
            soffice_path = (
                app_root
                / "Resources"
                / "App_ConversorPDF"
                / "vendor"
                / "LibreOffice"
                / "Contents"
                / "MacOS"
                / "soffice"
            )
            executable_path.parent.mkdir(parents=True)
            soffice_path.parent.mkdir(parents=True)
            executable_path.write_text("", encoding="utf-8")
            soffice_path.write_text("", encoding="utf-8")

            with patch.object(libreoffice.sys, "frozen", True, create=True):
                with patch.object(libreoffice.sys, "executable", str(executable_path)):
                    detected_path = libreoffice.get_soffice_path()

        self.assertEqual(detected_path, soffice_path)

    def test_converter_is_registered_in_launcher(self):
        definition = get_application("conversorpdf")

        self.assertIsNotNone(definition)
        self.assertEqual(definition.package_name, "App_ConversorPDF")


if __name__ == "__main__":
    unittest.main()
