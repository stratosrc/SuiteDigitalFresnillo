from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from App_Organigrama.ui.canvas_node_controller import CanvasNodeController


class FakeMenu:
    latest = None

    def __init__(self, *_args, **_kwargs):
        self.labels = []
        FakeMenu.latest = self

    def add_command(self, *, label, **_kwargs):
        self.labels.append(label)

    def add_separator(self):
        self.labels.append("---")

    def tk_popup(self, *_args):
        return None

    def grab_release(self):
        return None


class OrgContextMenuIntegrationTests(unittest.TestCase):
    def test_keyboard_context_menu_exposes_node_actions(self):
        controller = CanvasNodeController()
        node = SimpleNamespace(id="node-1")
        controller.canvas = Mock()
        controller.document = SimpleNamespace(nodes={"node-1": node})
        controller.selected_node_id = "node-1"
        controller._node_at_screen = Mock(return_value=None)
        controller._connection_at_screen = Mock(return_value=None)
        controller._selected_connection_route = Mock(return_value=None)
        controller._set_selection = Mock()
        controller.delete_selected_item = Mock()

        event = SimpleNamespace(
            x=0,
            y=0,
            x_root=10,
            y_root=20,
            keyboard=True,
        )
        with patch("App_Organigrama.ui.canvas_node_controller.tk.Menu", FakeMenu):
            controller._show_context_menu(event)

        self.assertEqual(
            FakeMenu.latest.labels,
            ["Editar nodo", "Duplicar nodo", "---", "Eliminar"],
        )


if __name__ == "__main__":
    unittest.main()
