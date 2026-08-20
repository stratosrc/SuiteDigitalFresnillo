import unittest

from App_TestData.services.redaction_exporter import RedactionPdfExporter


class CustomRedactionNumberingTests(unittest.TestCase):
    def test_custom_numbers_have_an_independent_sequence(self):
        rectangles = [
            {"classification": "custom"},
            {"classification": "general", "concept_id": 7},
            {"classification": "custom"},
            {"classification": "general", "concept_id": 7},
        ]

        RedactionPdfExporter({})._assign_final_numbers(rectangles)

        self.assertEqual(
            [item["final_number"] for item in rectangles],
            ["P.1", "#7.1", "P.2", "#7.2"],
        )


if __name__ == "__main__":
    unittest.main()
