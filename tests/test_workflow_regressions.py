import unittest
from unittest.mock import Mock, patch

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


if __name__ == "__main__":
    unittest.main()
