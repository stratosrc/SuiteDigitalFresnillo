from App_Organigrama.ui.app import OrgChartApplication


class AppOrganigrama(OrgChartApplication):
    """Backward-compatible entry point used by the suite launcher."""


def main() -> None:
    application = AppOrganigrama()
    application.mainloop()


if __name__ == "__main__":
    main()
