from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from App_ConversorPDF.services import libreoffice


class LibreOfficeResolverTests(unittest.TestCase):
    def test_get_soffice_path_prefers_development_vendor_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            app_root = root / "App_ConversorPDF"
            project_root = root
            soffice_path = app_root / "vendor" / "libreoffice" / "program" / "soffice.exe"
            soffice_path.parent.mkdir(parents=True)
            soffice_path.write_text("", encoding="utf-8")

            with (
                patch.object(libreoffice, "_app_root", return_value=app_root),
                patch.object(libreoffice, "_project_root", return_value=project_root),
                patch.object(libreoffice, "WINDOWS_INSTALL_PATHS", ()),
                patch.object(sys, "frozen", False, create=True),
            ):
                self.assertEqual(libreoffice.get_soffice_path(), soffice_path)

    def test_get_soffice_path_supports_pyinstaller_internal_vendor_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            frozen_root = Path(temp_dir)
            soffice_path = frozen_root / "_internal" / "vendor" / "libreoffice" / "program" / "soffice.exe"
            soffice_path.parent.mkdir(parents=True)
            soffice_path.write_text("", encoding="utf-8")

            with (
                patch.object(libreoffice, "_frozen_root", return_value=frozen_root),
                patch.object(libreoffice, "WINDOWS_INSTALL_PATHS", ()),
                patch.object(sys, "frozen", True, create=True),
            ):
                self.assertEqual(libreoffice.get_soffice_path(), soffice_path)


if __name__ == "__main__":
    unittest.main()
