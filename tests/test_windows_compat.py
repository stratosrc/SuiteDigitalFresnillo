from __future__ import annotations

from types import SimpleNamespace

import components.shared.windows_compat as windows_compat


class _FakeCustomTkinter:
    def __init__(self) -> None:
        self.deactivated = False

    def deactivate_automatic_dpi_awareness(self) -> None:
        self.deactivated = True


def test_windows_8_falls_back_to_legacy_dpi_api(monkeypatch) -> None:
    calls = []
    fake_ctk = _FakeCustomTkinter()
    fake_ctypes = SimpleNamespace(
        windll=SimpleNamespace(
            shcore=SimpleNamespace(),
            user32=SimpleNamespace(SetProcessDPIAware=lambda: calls.append("legacy")),
        )
    )

    monkeypatch.setattr(windows_compat.sys, "platform", "win32")
    monkeypatch.setitem(__import__("sys").modules, "ctypes", fake_ctypes)

    windows_compat.configure_customtkinter_dpi(fake_ctk)

    assert fake_ctk.deactivated is True
    assert calls == ["legacy"]
