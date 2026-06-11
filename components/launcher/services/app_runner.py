import os
import subprocess
import sys
from tkinter import messagebox

from components.launcher.paths import base_path, is_frozen


class ApplicationRunner:
    def __init__(self, parent):
        self.parent = parent
        self._running_processes = {}

    def launch(self, app_config):
        app_id = app_config.get("app_id") or app_config["name"]
        if self._is_already_running(app_id):
            messagebox.showinfo(
                "Aplicacion en ejecucion",
                f"{app_config['name']} ya esta abierta. Cierra esa ventana antes de iniciar otra instancia.",
                parent=self.parent,
            )
            return

        process = self._launch_packaged_app(app_config) if is_frozen() else self._launch_development_app(app_config)
        if process is not None:
            self._running_processes[app_id] = process

    def _is_already_running(self, app_id):
        process = self._running_processes.get(app_id)
        if process is None:
            return False

        if process.poll() is None:
            return True

        del self._running_processes[app_id]
        return False

    def _launch_development_app(self, app_config):
        module_path = app_config.get("module_path")
        if not module_path:
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
                [sys.executable, "-m", module_path],
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

    def _launch_packaged_app(self, app_config):
        app_id = app_config.get("app_id")
        if not app_id:
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
                [sys.executable, "--app", app_id],
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
