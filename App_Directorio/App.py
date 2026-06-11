"""Launcher entry point for the Directorio application."""

from App_Directorio.ui.app import DirectoryApplication


class AppDirectorio(DirectoryApplication):
    """Backward-compatible entry point used by the suite launcher."""


def main() -> None:
    application = AppDirectorio()
    application.mainloop()


if __name__ == "__main__":
    main()
