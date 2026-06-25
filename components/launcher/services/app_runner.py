from __future__ import annotations

import typing

from typing import Mapping
import os
import subprocess
import sys
from tkinter import messagebox

from components.shared.paths import base_path, is_frozen
from components.shared.windowing import prepare_window_for_open, reveal_window_maximized

LauncherAppConfig = Mapping[str, typing.Union[str, bool]]
PROCESS_POLL_INTERVAL_MS = 500


class ApplicationRunner:
    def __init__(self, parent: object) -> None:
        self.parent = parent
        self._running_processes: dict[str, subprocess.Popen[bytes]] = {}

    def launch(self, app_config: LauncherAppConfig) -> None:
        app_id = str(app_config.get("app_id") or app_config["name"])
        if self._is_already_running(app_id):
            messagebox.showinfo(
                "Aplicacion en ejecucion",
                f"{app_config['name']} ya esta abierta. Cierra esa ventana antes de iniciar otra instancia.",
                parent=self.parent,
            )
            return

        process = self._launch_packaged_app(app_config) if is_frozen() else self._launch_development_app(app_config)
        if process is None:
            return

        self._running_processes[app_id] = process
        self._hide_launcher()
        self._watch_process(app_id, process)

    def _is_already_running(self, app_id: str) -> bool:
        process = self._running_processes.get(app_id)
        if process is None:
            return False

        if process.poll() is None:
            return True

        del self._running_processes[app_id]
        return False

    def _launch_development_app(self, app_config: LauncherAppConfig) -> subprocess.Popen[bytes] | None:
        module_path_value = app_config.get("module_path")
        if not module_path_value:
            messagebox.showwarning(
                "Aplicacion no disponible",
                f"No se encontro el modulo para {app_config['name']}.",
                parent=self.parent,
            )
            return None

        if not app_config.get("available", True):
            messagebox.showwarning(
                "Aplicacion no disponible",
                f"El modulo {app_config['name']} no esta incluido actualmente en el proyecto.",
                parent=self.parent,
            )
            return None

        try:
            return subprocess.Popen(
                [sys.executable, "-m", str(module_path_value)],
                cwd=base_path(),
                shell=False,
            )
        except OSError as exc:
            messagebox.showerror(
                "Error al abrir aplicacion",
                f"No fue posible iniciar {app_config['name']}:\n{exc}",
                parent=self.parent,
            )
            return None

    def _launch_packaged_app(self, app_config: LauncherAppConfig) -> subprocess.Popen[bytes] | None:
        app_id_value = app_config.get("app_id")
        if not app_id_value:
            messagebox.showwarning(
                "Aplicacion no disponible",
                f"No se encontro el identificador interno para {app_config['name']}.",
                parent=self.parent,
            )
            return None

        if not app_config.get("available", True):
            messagebox.showwarning(
                "Aplicacion no disponible",
                f"El modulo {app_config['name']} no esta incluido actualmente en el proyecto.",
                parent=self.parent,
            )
            return None

        try:
            return subprocess.Popen(
                [sys.executable, "--app", str(app_id_value)],
                cwd=os.path.dirname(sys.executable),
                shell=False,
            )
        except OSError as exc:
            messagebox.showerror(
                "Error al abrir aplicacion",
                f"No fue posible iniciar {app_config['name']}:\n{exc}",
                parent=self.parent,
            )
            return None

    def _hide_launcher(self) -> None:
        prepare_window_for_open(self.parent)

    def _show_launcher(self) -> None:
        reveal_window_maximized(self.parent)
        focus_force = getattr(self.parent, "focus_force", None)
        if callable(focus_force):
            focus_force()

    def _watch_process(self, app_id: str, process: subprocess.Popen[bytes]) -> None:
        if process.poll() is None:
            after = getattr(self.parent, "after", None)
            if callable(after):
                after(PROCESS_POLL_INTERVAL_MS, lambda: self._watch_process(app_id, process))
            return

        self._running_processes.pop(app_id, None)
        if not self._running_processes:
            self._show_launcher()
