import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from App_Organigrama.models.document import OrgNode
from App_Organigrama.rendering.palette import (
    LIGHT_BLUE,
    NEUTRAL_GRAY,
    PRIMARY_BLUE,
    SECONDARY_BLUE,
    is_inverse_hierarchy,
)
from App_Organigrama.ui.canvas_connection_controller import CanvasConnectionController
from App_Organigrama.ui.canvas_interaction_controller import (
    CanvasInteractionController,
    connection_autoscroll_delta,
)
from App_Organigrama.ui.canvas_state import InteractionMode


class OrgHierarchyInteractionTests(unittest.TestCase):
    def test_hierarchy_direction_uses_color_order(self):
        self.assertFalse(is_inverse_hierarchy(PRIMARY_BLUE, SECONDARY_BLUE))
        self.assertFalse(is_inverse_hierarchy(SECONDARY_BLUE, LIGHT_BLUE))
        self.assertFalse(is_inverse_hierarchy(LIGHT_BLUE, NEUTRAL_GRAY))
        self.assertFalse(is_inverse_hierarchy(SECONDARY_BLUE, SECONDARY_BLUE))
        self.assertTrue(is_inverse_hierarchy(NEUTRAL_GRAY, PRIMARY_BLUE))
        self.assertTrue(is_inverse_hierarchy(LIGHT_BLUE, SECONDARY_BLUE))

    def test_inverse_connection_asks_for_confirmation(self):
        source = OrgNode("Auxiliar", "Administrativo", 0, 0, NEUTRAL_GRAY)
        target = OrgNode("Secretaría", "Titular", 0, 1, PRIMARY_BLUE)
        controller = SimpleNamespace(
            _node_flow_label=CanvasConnectionController._node_flow_label,
            winfo_toplevel=lambda: None,
        )

        with patch(
            "App_Organigrama.ui.canvas_connection_controller.messagebox.askyesno",
            return_value=False,
        ) as ask:
            result = CanvasConnectionController._confirm_hierarchy_direction(
                controller,
                source,
                target,
            )

        self.assertFalse(result)
        self.assertIn("inferior hacia uno superior", ask.call_args.args[1])
        self.assertIn("Personal Administrativo", ask.call_args.args[1])
        self.assertIn("Secretarios", ask.call_args.args[1])

    def test_normal_connection_does_not_show_confirmation(self):
        source = OrgNode("Secretaría", "Titular", 0, 0, PRIMARY_BLUE)
        target = OrgNode("Dirección", "Titular", 0, 1, SECONDARY_BLUE)
        controller = SimpleNamespace()

        with patch(
            "App_Organigrama.ui.canvas_connection_controller.messagebox.askyesno",
        ) as ask:
            result = CanvasConnectionController._confirm_hierarchy_direction(
                controller,
                source,
                target,
            )

        self.assertTrue(result)
        ask.assert_not_called()

    def test_connection_autoscroll_moves_toward_each_edge(self):
        self.assertEqual(connection_autoscroll_delta(400, 300, 800, 600), (0, 0))
        self.assertGreater(connection_autoscroll_delta(0, 300, 800, 600)[0], 0)
        self.assertLess(connection_autoscroll_delta(800, 300, 800, 600)[0], 0)
        self.assertGreater(connection_autoscroll_delta(400, 0, 800, 600)[1], 0)
        self.assertLess(connection_autoscroll_delta(400, 600, 800, 600)[1], 0)
        self.assertEqual(connection_autoscroll_delta(-500, 300, 800, 600), (0, 0))

    def test_connection_autoscroll_updates_pan_and_schedules_next_tick(self):
        canvas = SimpleNamespace(
            winfo_pointerx=lambda: 800,
            winfo_pointery=lambda: 300,
            winfo_rootx=lambda: 0,
            winfo_rooty=lambda: 0,
            winfo_width=lambda: 800,
            winfo_height=lambda: 600,
        )
        controller = SimpleNamespace(
            connection_autoscroll_after_id="current",
            interaction=SimpleNamespace(mode=InteractionMode.IDLE),
            pending_connection_source_id="source",
            canvas=canvas,
            pan_x=0,
            pan_y=0,
            connection_drag_source_id=None,
            request_redraw=Mock(),
            _emit_context_change=Mock(),
        )

        def schedule():
            controller.connection_autoscroll_after_id = "next"

        controller._schedule_connection_autoscroll = schedule

        CanvasInteractionController._run_connection_autoscroll(controller)

        self.assertLess(controller.pan_x, 0)
        self.assertEqual(controller.pan_y, 0)
        self.assertEqual(controller.connection_autoscroll_after_id, "next")
        controller.request_redraw.assert_called_once()


if __name__ == "__main__":
    unittest.main()
