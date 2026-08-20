# Referencia de APIs internas

Contratos reutilizables. Los nombres con `_` son implementación privada.

## Núcleo

- `get_application`, `get_launcher_applications`, `run_application`: registro/arranque.
- `write_atomic_output` y `atomic_write_*`: salidas seguras.
- `ProjectLifecycle`: estado sucio, recientes, autosave y recuperación.
- `bind_common_shortcuts`, `build_topbar`, `ProgressOverlay`: UI compartida.
- `resource_path`: rutas en fuente y PyInstaller.

## Test Data

- `DocumentState.reset_for_new_job`.
- `delete_selected_rectangle`, `undo_last_rectangle`, `redo_last_rectangle`.
- `PDFManager.load_pdf_path`, `render_current_page`, transformaciones canvas/PDF y `generate_pdf`.
- `RedactionPdfExporter.export`.
- `save_project`, `load_project`, `calculate_file_hash`; cerrar `LoadedProject` libera temporales.
- `SummaryPagesWriter` y `CommitteeCoverWriter`.

## Organigrama

- `OrgGridDocument`: nodos, conexiones, rutas manuales, `to_dict` y `bounds`.
- `DocumentHistory`: `record`, `undo`, `redo`, `mark_saved`.
- `RenderingEngine`: layout, texto y límites.
- `ManhattanRouter.route_document`.
- Helpers de `manual_routes`.
- `PersistenceManager.save/load/from_dict`.
- `PdfOrgChartExporter.export` y `export_pdf_as_image`.

## Directorio

- Dataclasses `PersonReportRow`, `AreaReportData`, `DirectoryReportData`.
- `DirectoryPersistenceManager.save/load/from_dict`.
- `DirectoryPdfExporter.export`.
- `DirectoryFormFrame.get_report_data`, `set_report_data`, validaciones y resumen.
- `virtual_window`, `start_from_fraction`, `is_valid_date`.

## Conversor

- `build_output_plan`, `normalize_selection`, `expand_selection`, `safe_filename`.
- `ConversionRequest` y `PdfConverter.convert`.
- `PdfMerger.merge`.
- `get_soffice_path` / `require_soffice_path`.
- `run_cancellable_process` / `terminate_process_tree`.
- `SpreadsheetPdfExporter.export`.

## Estabilidad

Las fachadas `ui/main_frame.py`, `ui/app.py` y `directory_form.py` estabilizan imports. Los atributos compartidos por coordinadores/mixins son contratos internos. No existe API de red, plugins ni CLI de automatización pública.
