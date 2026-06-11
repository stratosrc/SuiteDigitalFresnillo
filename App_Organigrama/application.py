from App_Organigrama.ui import OrgChartApplication

__all__ = ["AppOrganigrama", "main"]


class AppOrganigrama(OrgChartApplication):
    """Canonical application entry point used by the suite launcher."""


def main() -> None:
    application = AppOrganigrama()
    application.mainloop()


if __name__ == "__main__":
    main()
