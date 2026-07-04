from App_ConversorPDF.ui import PdfConverterApplication

__all__ = ["AppConversorPDF", "main"]


class AppConversorPDF(PdfConverterApplication):
    """Canonical application entry point used by the suite launcher."""


def main() -> None:
    application = AppConversorPDF()
    application.mainloop()


if __name__ == "__main__":
    main()
