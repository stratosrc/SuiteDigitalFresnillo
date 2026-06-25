"""Public TestData application entry point."""

from App_TestData.ui.application_controller import TestDataGeneratorApp


__all__ = ["TestDataGeneratorApp"]


if __name__ == "__main__":
    TestDataGeneratorApp().mainloop()
