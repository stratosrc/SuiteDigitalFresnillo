import unittest

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.ui.canvas import OrgGridCanvas


class CanvasContextStub:
    _node_flow_label = staticmethod(OrgGridCanvas._node_flow_label)
    _connection_flow_message = OrgGridCanvas._connection_flow_message

    def __init__(self, document):
        self.document = document


class OrgConnectionContextTests(unittest.TestCase):
    def test_flow_message_includes_names_and_roles(self):
        document = OrgGridDocument()
        source = document.add_node("Persona 1", "Presidente", 0, 0, "#09519F")
        target = document.add_node("Persona 2", "Asistente", 1, 1, "#09519F")
        canvas = CanvasContextStub(document)

        message = canvas._connection_flow_message(
            source.id,
            target.id,
            "Suelta para conectar",
        )

        self.assertEqual(
            message,
            "Suelta para conectar: Persona 1 — Presidente → Persona 2 — Asistente",
        )


if __name__ == "__main__":
    unittest.main()
