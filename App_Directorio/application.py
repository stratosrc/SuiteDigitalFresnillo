from __future__ import annotations

from App_Directorio.ui import DirectoryApplication

__all__ = ["AppDirectorio", "main"]


class AppDirectorio(DirectoryApplication):
    """Canonical application entry point used by the suite launcher."""


def main() -> None:
    application = AppDirectorio()
    application.mainloop()


if __name__ == "__main__":
    main()
