import unittest
from concurrent.futures import Future
from unittest.mock import Mock, patch
from pathlib import Path
import tempfile

from App_Directorio.models import DirectoryReportData
from App_Directorio.ui.main_frame import DirectoryMainFrame
from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.ui.main_frame import MainFrame
from App_TestData.ui.app import TestDataGeneratorApp


class WorkflowRegressionTests(unittest.TestCase):
    def test_organigram_open_project_uses_background_loading(self):
        frame = Mock()
        frame._is_operation_running.return_value = False
        frame._confirm_discard_changes.return_value = True

        with patch(
            "App_Organigrama.ui.workspace_controller.filedialog.askopenfilename",
            return_value="organigrama.og",
        ):
            MainFrame.open_project(frame)

        frame._start_project_load.assert_called_once_with("organigrama.og")
        frame.persistence_manager.load.assert_not_called()

    def test_organigram_completed_load_updates_ui_and_hides_progress(self):
        document = OrgGridDocument(title="CARGADO")
        source_path = Path("organigrama.og")
        future = Future()
        future.set_result(document)
        frame = Mock()
        frame._pending_task = future

        MainFrame._poll_project_load(frame, future, source_path, False)

        self.assertIs(frame.document, document)
        self.assertEqual(frame.current_project_path, source_path)
        frame._load_document_into_ui.assert_called_once_with(document)
        frame.progress_overlay.hide.assert_called_once_with()
        frame._set_busy_state.assert_called_once_with("normal")
        self.assertIsNone(frame._pending_task)

    def test_directory_open_project_uses_background_loading(self):
        frame = Mock()
        frame._is_operation_running.return_value = False
        frame.project_lifecycle.confirm_discard.return_value = True

        with patch(
            "App_Directorio.ui.main_frame.filedialog.askopenfilename",
            return_value="directorio.dir",
        ):
            DirectoryMainFrame.open_project(frame)

        frame._start_project_load.assert_called_once_with("directorio.dir")
        frame.persistence_manager.load.assert_not_called()

    def test_directory_completed_load_updates_form_and_hides_progress(self):
        data = DirectoryReportData(title="DIRECTORIO", period="2026", areas=[])
        source_path = Path("directorio.dir")
        future = Future()
        future.set_result(data)
        frame = Mock()
        frame._pending_operation = future

        DirectoryMainFrame._poll_project_load(
            frame,
            future,
            source_path,
            False,
        )

        self.assertEqual(frame.current_project_path, source_path)
        frame.directory_form.set_report_data.assert_called_once_with(data)
        frame.progress_overlay.hide.assert_called_once_with()
        frame._set_busy_state.assert_called_once_with("normal")
        self.assertIsNone(frame._pending_operation)

    def test_organigram_undo_and_redo_preserve_the_viewport(self):
        restored_by_undo = OrgGridDocument(title="UNDO")
        restored_by_redo = OrgGridDocument(title="REDO")
        frame = Mock()
        frame.document_history.undo.return_value = restored_by_undo
        frame.document_history.redo.return_value = restored_by_redo

        MainFrame.undo(frame)
        frame._load_document_into_ui.assert_called_once_with(
            restored_by_undo,
            preserve_viewport=True,
        )

        frame._load_document_into_ui.reset_mock()
        MainFrame.redo(frame)
        frame._load_document_into_ui.assert_called_once_with(
            restored_by_redo,
            preserve_viewport=True,
        )

    def test_loading_history_snapshot_does_not_fit_or_reset_camera(self):
        frame = Mock()
        frame.grid_canvas.zoom = 1.65
        frame.grid_canvas.pan_x = -1840.0
        frame.grid_canvas.pan_y = 725.0
        document = OrgGridDocument(title="Historial", period="2026")

        MainFrame._load_document_into_ui(
            frame,
            document,
            preserve_viewport=True,
        )

        self.assertEqual(frame.grid_canvas.zoom, 1.65)
        self.assertEqual(frame.grid_canvas.pan_x, -1840.0)
        self.assertEqual(frame.grid_canvas.pan_y, 725.0)
        frame.grid_canvas.set_document.assert_called_once_with(document)
        frame.grid_canvas.fit_document_to_content_top.assert_not_called()
        frame._update_zoom_label.assert_called_once_with()

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
            frame._can_start_export.return_value = True
            MainFrame.export_pdf(frame)
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
