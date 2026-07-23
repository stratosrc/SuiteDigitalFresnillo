"""Export selected spreadsheet tabs through LibreOffice UNO."""

from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import tempfile
import textwrap

from App_ConversorPDF.services.libreoffice import (
    build_libreoffice_subprocess_env,
    get_libreoffice_python_path,
    require_soffice_path,
)
from App_ConversorPDF.services.process_control import run_cancellable_process


SPREADSHEET_EXPORT_TIMEOUT_SECONDS = 180

_UNO_WORKER_SCRIPT = r'''
import json
from pathlib import Path
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue


def prop(name, value):
    item = PropertyValue()
    item.Name = name
    item.Value = value
    return item


def parse_selection(raw_value, total_sheets):
    if not raw_value.strip():
        return list(range(total_sheets))

    selected = []
    for raw_part in raw_value.replace(";", ",").split(","):
        part = raw_part.strip()
        if not part:
            continue
        if "-" not in part:
            selected.append(parse_number(part, total_sheets))
            continue
        values = [value.strip() for value in part.split("-")]
        if len(values) != 2:
            raise ValueError("Rango de hojas invalido: " + part)
        start = parse_number(values[0], total_sheets)
        end = parse_number(values[1], total_sheets)
        if start > end:
            raise ValueError("Rango de hojas invalido: " + part)
        selected.extend(range(start, end + 1))

    return list(dict.fromkeys(selected)) or list(range(total_sheets))


def parse_number(raw_value, total_sheets):
    if not raw_value.isdigit():
        raise ValueError("Hoja invalida: " + raw_value)
    sheet_number = int(raw_value)
    if sheet_number < 1 or sheet_number > total_sheets:
        raise ValueError(
            "La hoja {} esta fuera del rango 1-{}.".format(sheet_number, total_sheets)
        )
    return sheet_number - 1


def connect(port):
    local_context = uno.getComponentContext()
    resolver = local_context.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver",
        local_context,
    )
    connection = (
        "uno:socket,host=127.0.0.1,port={};urp;"
        "StarOffice.ComponentContext"
    ).format(port)
    last_error = None
    for _ in range(100):
        try:
            return resolver.resolve(connection)
        except Exception as error:
            last_error = error
            time.sleep(0.1)
    raise RuntimeError("No fue posible conectar con LibreOffice.") from last_error


def main():
    source_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve()
    selection = sys.argv[3]
    soffice_path = Path(sys.argv[4]).resolve()
    profile_uri = sys.argv[5]
    port = int(sys.argv[6])

    command = [
        str(soffice_path),
        "--headless",
        "--nologo",
        "--nodefault",
        "--nolockcheck",
        "--nofirststartwizard",
        "-env:UserInstallation=" + profile_uri,
        "--accept=socket,host=127.0.0.1,port={};urp;StarOffice.ServiceManager".format(port),
    ]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    office_process = subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creationflags,
    )
    document = None
    desktop = None
    try:
        context = connect(port)
        service_manager = context.ServiceManager
        desktop = service_manager.createInstanceWithContext(
            "com.sun.star.frame.Desktop",
            context,
        )
        document = desktop.loadComponentFromURL(
            source_path.as_uri(),
            "_blank",
            0,
            (prop("Hidden", True),),
        )
        if document is None or not document.supportsService(
            "com.sun.star.sheet.SpreadsheetDocument"
        ):
            raise ValueError("El archivo no es una hoja de calculo compatible.")

        sheets = document.getSheets()
        sheet_names = list(sheets.getElementNames())
        selected_indexes = parse_selection(selection, len(sheet_names))
        selected_set = set(selected_indexes)
        for index, sheet_name in enumerate(sheet_names):
            sheets.getByName(sheet_name).IsVisible = index in selected_set

        output_path.parent.mkdir(parents=True, exist_ok=True)
        document.storeToURL(
            output_path.as_uri(),
            (
                prop("FilterName", "calc_pdf_Export"),
                prop("Overwrite", True),
            ),
        )
        print(json.dumps({
            "sheet_count": len(sheet_names),
            "selected_sheets": [sheet_names[index] for index in selected_indexes],
        }, ensure_ascii=False))
    finally:
        if document is not None:
            try:
                document.close(True)
            except Exception:
                document.dispose()
        if desktop is not None:
            try:
                desktop.terminate()
            except Exception:
                pass
        try:
            office_process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            office_process.terminate()
            office_process.wait(timeout=5)


if __name__ == "__main__":
    main()
'''


class SpreadsheetPdfExporter:
    """Convert selected workbook tabs to one PDF."""

    def export(
        self,
        source_path: Path,
        target_path: Path,
        sheet_selection: str | None,
        *,
        cancel_check=None,
    ) -> Path:
        soffice_path = require_soffice_path()
        python_path = get_libreoffice_python_path(soffice_path)
        if python_path is None:
            raise FileNotFoundError(
                "La copia de LibreOffice no incluye un interprete Python compatible con UNO."
            )
        worker_env = build_libreoffice_subprocess_env(soffice_path)

        with tempfile.TemporaryDirectory(prefix="calc-export-") as temp_dir:
            temp_root = Path(temp_dir)
            profile_dir = temp_root / "profile"
            profile_dir.mkdir()
            worker_path = temp_root / "export_selected_sheets.py"
            worker_path.write_text(
                textwrap.dedent(_UNO_WORKER_SCRIPT),
                encoding="utf-8",
            )
            port = _find_available_port()
            command = [
                str(python_path),
                str(worker_path),
                str(source_path),
                str(target_path),
                sheet_selection or "",
                str(soffice_path),
                profile_dir.as_uri(),
                str(port),
            ]
            completed = _run_worker(command, env=worker_env, cancel_check=cancel_check)

        if not target_path.is_file():
            details = _format_process_output(completed.stdout, completed.stderr)
            raise RuntimeError(
                "LibreOffice termino, pero no genero el PDF de las hojas seleccionadas."
                + details
            )
        return target_path


def _find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def _run_worker(
    command: list[str],
    *,
    env: dict[str, str] | None = None,
    cancel_check=None,
) -> subprocess.CompletedProcess[str]:
    try:
        completed = run_cancellable_process(
            command,
            env=env,
            timeout_seconds=SPREADSHEET_EXPORT_TIMEOUT_SECONDS,
            cancel_check=cancel_check,
        )
    except subprocess.TimeoutExpired as error:
        raise TimeoutError(
            "LibreOffice excedio el tiempo limite al exportar las hojas seleccionadas."
        ) from error
    except PermissionError as error:
        raise PermissionError(
            "No se pudo ejecutar el interprete interno de LibreOffice por permisos."
        ) from error

    if completed.returncode != 0:
        details = _format_process_output(completed.stdout, completed.stderr)
        raise RuntimeError("No se pudieron exportar las hojas seleccionadas." + details)
    return completed


def _format_process_output(stdout: str | None, stderr: str | None) -> str:
    parts: list[str] = []
    if stderr and stderr.strip():
        parts.append(f"Error: {stderr.strip()}")
    if stdout and stdout.strip():
        parts.append(f"Salida: {stdout.strip()}")
    return " " + " ".join(parts) if parts else " LibreOffice no devolvio detalles."


__all__ = ["SpreadsheetPdfExporter"]
