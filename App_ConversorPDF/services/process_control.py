"""Cancelable subprocess execution for LibreOffice conversions."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import os
import subprocess
import time

from components.shared.atomic_output import OutputCancelled


def run_cancellable_process(
    command: Sequence[str],
    *,
    timeout_seconds: float,
    cancel_check: Callable[[], bool] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a process while allowing termination of its full process tree."""
    creationflags = 0
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

    try:
        process = subprocess.Popen(
            list(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creationflags,
        )
    except PermissionError as error:
        raise PermissionError("No se pudo ejecutar LibreOffice por permisos.") from error

    deadline = time.monotonic() + timeout_seconds
    while True:
        if cancel_check is not None and cancel_check():
            terminate_process_tree(process)
            raise OutputCancelled("La conversión fue cancelada.")
        if time.monotonic() >= deadline:
            terminate_process_tree(process)
            raise TimeoutError(
                f"LibreOffice excedió el tiempo límite de {timeout_seconds:g} segundos."
            )
        try:
            stdout, stderr = process.communicate(timeout=0.15)
            return subprocess.CompletedProcess(
                args=list(command),
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
            )
        except subprocess.TimeoutExpired:
            continue


def terminate_process_tree(process: subprocess.Popen[str]) -> None:
    """Terminate a process and any child processes it created."""
    if process.poll() is not None:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    else:
        process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=3)


__all__ = ["run_cancellable_process", "terminate_process_tree"]
