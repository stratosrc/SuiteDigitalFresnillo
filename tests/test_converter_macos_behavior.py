import unittest
from pathlib import Path


class ConverterMacOsBehaviorTests(unittest.TestCase):
    def test_launcher_uses_convert_icon(self):
        from components.shared.app_registry import get_application

        definition = get_application("conversorpdf")

        self.assertIsNotNone(definition)
        self.assertEqual(definition.icon_path, "components/assets/convert.png")

    def test_package_skips_vendor_python_on_macos(self):
        package_init = Path("App_ConversorPDF/__init__.py").read_text(encoding="utf-8")

        self.assertIn('sys.platform != "darwin"', package_init)


if __name__ == "__main__":
    unittest.main()
