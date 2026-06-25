"""Main layout composition for the application window."""

from __future__ import annotations


from App_TestData.ui.layout.content_view import build_content_view
from App_TestData.ui.layout.header_bar import build_header
from App_TestData.ui.layout.navigation_bar import build_navigation_bar
from App_TestData.ui.layout.top_toolbar import build_action_toolbar, build_menu_toolbar
from components.styles.styles import APP_BG


def build_main_layout(parent, callbacks: dict):
    """Build and compose the complete main window layout."""
    widgets = {}
    widgets.update(build_menu_toolbar(parent, callbacks))
    widgets.update(build_header(parent))

    parent.configure(fg_color=APP_BG)
    widgets.update(build_action_toolbar(parent, callbacks))
    widgets.update(build_content_view(parent, callbacks["on_canvas_resize"]))
    widgets.update(build_navigation_bar(parent, callbacks))
    return widgets
