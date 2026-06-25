import unittest
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.ui.main_frame import MainFrame
from App_TestData.ui.app import TestDataGeneratorApp


class WorkflowRegressionTests(unittest.TestCase):
    def test_testdata_cancelled_pdf_selection_preserves_current_job(self):
        app = Mock()
        app.request_pdf_file_path.return_value = None

        TestDataGeneratorApp._start_new_job(app)

        app.pdf_manager.reset_current_job.assert_not_called()
        app._release_loaded_project.assert_not_called()

    def test_cancelled_organigram_export_does_not_change_orientation(self):
        frame = Mock()
        frame.document = OrgGridDocument(page_orientation="horizontal")

        with patch(
            "App_Organigrama.ui.main_frame.filedialog.asksaveasfilename",
            return_value="",
        ):
            MainFrame._export_pdf_for_orientation(frame, "vertical")
            MainFrame._export_image_for_orientation(frame, "vertical")

        self.assertEqual(frame.document.page_orientation, "horizontal")
        frame._run_background_task.assert_not_called()

    def test_testdata_recovery_keeps_its_own_pdf_copy(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "temporary-source.pdf"
            source.write_bytes(b"%PDF recovery")
            recovery_dir = root / "recovery"
            app = Mock()
            app.current_pdf_path = str(source)

            prepared = TestDataGeneratorApp._prepare_recovery_snapshot(
                app,
                {"pdf": str(source), "rectangles": []},
                recovery_dir,
            )

            recovery_pdf = recovery_dir / "source.pdf"
            self.assertEqual(prepared["pdf"], str(recovery_pdf))
            self.assertEqual(recovery_pdf.read_bytes(), source.read_bytes())


if __name__ == "__main__":
    unittest.main()
