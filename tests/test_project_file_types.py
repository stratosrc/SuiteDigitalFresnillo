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
