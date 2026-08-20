import unittest
import json
from pathlib import Path

from App_Directorio.samples.generate_large_directory_sample import build_payload
from App_Directorio.services.persistence import DirectoryPersistenceManager
from App_Directorio.ui.forms.virtualization import start_from_fraction, virtual_window
from App_Directorio.utils import is_valid_date


class DirectoryVirtualizationTests(unittest.TestCase):
    def test_window_clamps_to_first_and_last_records(self):
        self.assertEqual(virtual_window(300, 12, -50), virtual_window(300, 12, 0))

        last = virtual_window(300, 12, 999)

        self.assertEqual(last.start, 288)
        self.assertEqual(last.stop, 300)
        self.assertEqual(last.first_fraction, 0.96)
        self.assertEqual(last.last_fraction, 1.0)

    def test_fraction_maps_to_valid_window_start(self):
        self.assertEqual(start_from_fraction(300, 12, 0.0), 0)
        self.assertEqual(start_from_fraction(300, 12, 0.5), 150)
        self.assertEqual(start_from_fraction(300, 12, 1.0), 288)

    def test_large_sample_has_three_areas_with_300_people_each(self):
        sample_path = (
            Path(__file__).parents[1]
            / "App_Directorio"
            / "samples"
            / "directorio_3_areas_900_registros.dir"
        )

        directory = DirectoryPersistenceManager().load(sample_path)

        self.assertEqual(len(directory.areas), 3)
        self.assertEqual([len(area.personnel) for area in directory.areas], [300, 300, 300])
        self.assertEqual(sum(len(area.personnel) for area in directory.areas), 900)
        self.assertEqual(len({person.email for area in directory.areas for person in area.personnel}), 900)
        self.assertTrue(all(is_valid_date(person.start_date) for area in directory.areas for person in area.personnel))
        self.assertEqual(json.loads(sample_path.read_text(encoding="utf-8")), build_payload())


if __name__ == "__main__":
    unittest.main()
