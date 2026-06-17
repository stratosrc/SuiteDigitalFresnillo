import unittest

from App_Directorio.utils.validation import is_date_input_prefix, is_valid_date
from App_TestData.utils.navigation import get_adjacent_page_index, is_valid_page_index, parse_page_number, to_page_index
from App_TestData.utils.validation import parse_bounded_pair
from App_TestData.utils.zoom import format_zoom_percentage, get_auto_zoom, get_next_zoom


class NavigationZoomValidationTests(unittest.TestCase):
    def test_page_navigation_stays_in_bounds(self):
        self.assertEqual(get_adjacent_page_index(0, 3, "prev"), 0)
        self.assertEqual(get_adjacent_page_index(1, 3, "next"), 2)
        self.assertEqual(get_adjacent_page_index(2, 3, "next"), 2)
        self.assertEqual(to_page_index(parse_page_number("4")), 3)
        self.assertTrue(is_valid_page_index(2, 3))
        self.assertFalse(is_valid_page_index(3, 3))

    def test_zoom_helpers_bound_values(self):
        self.assertEqual(get_next_zoom(3.0, "in"), 3.0)
        self.assertEqual(get_next_zoom(0.3, "out"), 0.3)
        self.assertEqual(format_zoom_percentage(1.25), "125%")
        self.assertEqual(get_auto_zoom(200, 100), 0.5)

    def test_integer_and_date_validation(self):
        self.assertEqual(parse_bounded_pair("1", "5", 1, 10), (1, 5))
        with self.assertRaises(ValueError):
            parse_bounded_pair("0", "5", 1, 10)
        self.assertTrue(is_date_input_prefix("15/06/2026"))
        self.assertTrue(is_valid_date("15/06/2026"))
        self.assertTrue(is_valid_date("31/02/2026"))
        self.assertFalse(is_valid_date("31-02-2026"))


if __name__ == "__main__":
    unittest.main()
