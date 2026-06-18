from dataclasses import dataclass
from pathlib import Path
import unittest

from App_ConversorPDF.services.output_planner import (
    build_output_plan,
    expand_selection,
    normalize_selection,
)


class Value:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value


@dataclass
class Item:
    path: Path
    sheet_var: Value | None
    split_var: Value | None


class OutputPlannerTests(unittest.TestCase):
    def test_normalizes_and_expands_numeric_ranges(self):
        self.assertEqual(normalize_selection("1; 3 - 5"), "1,3-5")
        self.assertEqual(expand_selection("1,3-5"), ["1", "3", "4", "5"])

    def test_split_plan_creates_one_pdf_per_selected_page(self):
        item = Item(Path("report.pdf"), Value("2-4"), Value(True))

        outputs = build_output_plan([item])

        self.assertEqual(
            [output.filename for output in outputs],
            ["report_2.pdf", "report_3.pdf", "report_4.pdf"],
        )
        self.assertEqual([output.selection for output in outputs], ["2", "3", "4"])

    def test_combined_plan_keeps_selection_in_one_pdf(self):
        item = Item(Path("book.xlsx"), Value("2-4"), Value(False))

        outputs = build_output_plan([item])

        self.assertEqual(len(outputs), 1)
        self.assertEqual(outputs[0].filename, "book_2-4.pdf")
        self.assertEqual(outputs[0].selection, "2-4")


if __name__ == "__main__":
    unittest.main()
