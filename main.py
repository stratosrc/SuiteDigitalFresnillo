import sys

from components.shared.app_registry import get_application, run_application


def _run_launcher() -> None:
    from components.launcher.app import SuiteLauncher

    app = SuiteLauncher()
    app.mainloop()


def main() -> None:
    if len(sys.argv) >= 3 and sys.argv[1] == "--app":
        app_id = sys.argv[2].strip().lower()
        definition = get_application(app_id)
        if definition is None:
            raise SystemExit(f"Unknown application id: {app_id}")
        if not definition.is_available:
            raise SystemExit(f"Application '{definition.name}' is not available in this build.")

        run_application(app_id)
        return

    _run_launcher()


if __name__ == "__main__":
    main()
