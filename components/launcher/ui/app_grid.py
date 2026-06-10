from components.launcher.ui.app_card import ApplicationCard
from components.launcher.ui.scrollable_frame import ScrollableFrame


class ApplicationGrid(ScrollableFrame):
    def __init__(self, parent, applications_config, image_loader, launch_callback):
        super().__init__(parent)

        self.applications_config = applications_config
        self.image_loader = image_loader
        self.launch_callback = launch_callback
        self.cards = []
        self.current_columns = 0

        self.content.bind("<Configure>", self._refresh_grid_columns, add="+")
        self._render_cards()

    def _render_cards(self):
        for index, app_config in enumerate(self.applications_config):
            card = ApplicationCard(
                self.content,
                app_config=app_config,
                image_loader=self.image_loader,
                launch_callback=self.launch_callback,
            )
            self.cards.append(card)
            card.grid(row=index // 3, column=index % 3, padx=12, pady=12, sticky="nsew")

        self._refresh_grid_columns()

    def _refresh_grid_columns(self, event=None):
        width = event.width if event else self.content.winfo_width()
        columns = max(1, min(4, width // 230))

        if columns == self.current_columns:
            return

        self.current_columns = columns

        for column in range(4):
            self.content.columnconfigure(column, weight=0)

        for column in range(columns):
            self.content.columnconfigure(column, weight=1, uniform="app_cards")

        for index, card in enumerate(self.cards):
            card.grid_configure(row=index // columns, column=index % columns, sticky="nsew")
