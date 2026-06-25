from __future__ import annotations

from App_TestData.ui import TestDataGeneratorApp

__all__ = ["TestDataGeneratorApp", "main"]


def main() -> None:
    """Run the canonical Test Data application entry point."""
    application = TestDataGeneratorApp()
    application.mainloop()


if __name__ == "__main__":
    main()
