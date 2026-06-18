import json
from pathlib import Path
import tempfile
import unittest

from App_Organigrama.models.document import OrgGridDocument
from App_Organigrama.services.persistence import PersistenceManager
from App_Directorio.models import AreaReportData, DirectoryReportData, PersonReportRow
from App_Directorio.services.persistence import DirectoryPersistenceManager


class ProjectFileTypeTests(unittest.TestCase):
    def test_organigrama_project_has_app_marker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "organigrama.og"

            PersistenceManager().save(OrgGridDocument(), target)

            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(payload["app"], "organigrama")
            self.assertIn("document", payload)

    def test_organigrama_rejects_testdata_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "testado.td"
            source.write_text(
                json.dumps({"app": "testdata", "version": 1}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                PersistenceManager().load(source)

    def test_organigrama_loads_legacy_spanish_node_fields(self):
        payload = {
            "app": "organigrama",
            "schema_version": 1,
            "document": {
                "nodes": {
                    "legacy-node": {
                        "id": "legacy-node",
                        "nombre": "Persona",
                        "cargo": "Cargo",
                        "grid_x": 1,
                        "grid_y": 2,
                        "color": "#123456",
                    }
                },
                "connections": [],
                "blocked_points": [],
            },
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "legacy.og"
            source.write_text(json.dumps(payload), encoding="utf-8")

            document = PersistenceManager().load(source)

        node = document.nodes["legacy-node"]
        self.assertEqual(node.name, "Persona")
        self.assertEqual(node.role, "Cargo")

    def test_organigrama_roundtrip_preserves_manual_route_points(self):
        document = OrgGridDocument()
        source = document.add_node("Origen", "Cargo", 0, 0, "#123456")
        target = document.add_node("Destino", "Cargo", 2, 0, "#123456")
        connection = document.add_connection(
            source.id,
            target.id,
            source_port="right",
            target_port="left",
        )
        self.assertIsNotNone(connection)
        document.set_connection_manual_points(
            connection.id,
            [(0.5, 0.0), (0.5, 1.0), (1.5, 1.0), (1.5, 0.0)],
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            target_path = Path(temp_dir) / "manual.og"
            manager = PersistenceManager()
            manager.save(document, target_path)
            restored = manager.load(target_path)

        self.assertEqual(
            restored.connections[0].manual_points,
            ((0.5, 0.0), (0.5, 1.0), (1.5, 1.0), (1.5, 0.0)),
        )

    def test_directorio_project_roundtrip_uses_dir_marker(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "directorio.dir"
            data = DirectoryReportData(
                title="Unidad",
                period="2026",
                areas=[
                    AreaReportData(
                        name="Area",
                        personnel=[
                            PersonReportRow(
                                rank="1",
                                name="Persona",
                                position="Cargo",
                                email="persona@example.com",
                                start_date="01/01/2026",
                            )
                        ],
                    )
                ],
            )

            manager = DirectoryPersistenceManager()
            manager.save(data, target)
            payload = json.loads(target.read_text(encoding="utf-8"))
            restored = manager.load(target)

            self.assertEqual(payload["app"], "directorio")
            self.assertEqual(restored, data)


if __name__ == "__main__":
    unittest.main()
