import sys


def _run_testdata():
    from App_TestData.App import TestDataGeneratorApp

    app = TestDataGeneratorApp()
    app.mainloop()


def _run_organigrama():
    from App_Organigrama.App import AppOrganigrama

    app = AppOrganigrama()
    app.mainloop()


def _run_launcher():
    from components.launcher.app import SuiteLauncher

    app = SuiteLauncher()
    app.mainloop()


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "--app":
        app_id = sys.argv[2].strip().lower()
        if app_id == "testdata":
            _run_testdata()
            return
        if app_id == "organigrama":
            _run_organigrama()
            return

    _run_launcher()


if __name__ == "__main__":
    main()
