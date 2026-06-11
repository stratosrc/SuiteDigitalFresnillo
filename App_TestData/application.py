from App_TestData.App import TestDataGeneratorApp

__all__ = ["TestDataGeneratorApp", "main"]


def main() -> None:
    """Run the canonical Test Data application entry point."""
    application = TestDataGeneratorApp()
    application.mainloop()


if __name__ == "__main__":
    main()
