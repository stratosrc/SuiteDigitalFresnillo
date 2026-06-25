import unittest

from App_TestData.services.summary_pages import SummaryPagesWriter


class SummaryPagesWriterTests(unittest.TestCase):
    def setUp(self):
        self.writer = SummaryPagesWriter({})

    def test_reserved_summary_removes_leading_los(self):
        line = self.writer.build_summary_line(
            "Reservada.1",
            {
                "classification": "reserved",
                "reason": "Los documentos contienen datos protegidos",
                "paragraphs": 1,
                "rows": 2,
                "legal_basis": "artículo aplicable",
            },
        )

        self.assertTrue(line.startswith("Reservada.1: documentos contienen"))
        self.assertNotIn(": Los ", line)

    def test_all_summary_classifications_use_uniform_paragraph_spacing(self):
        self.assertEqual(
            self.writer._paragraph_spacing({"classification": "reserved"}, 13),
            0,
        )
        self.assertEqual(
            self.writer._paragraph_spacing({"classification": "confidential"}, 13),
            0,
        )
        self.assertEqual(
            self.writer._paragraph_spacing({"classification": "general"}, 13),
            0,
        )

    def test_reserved_summary_introduces_legal_basis_cohesively(self):
        line = self.writer.build_summary_line(
            "Reservada.1",
            {
                "classification": "reserved",
                "reason": "Documentos protegidos",
                "paragraphs": 1,
                "rows": 1,
                "legal_basis": "Artículo aplicable.",
            },
        )

        self.assertIn(
            "elaboracion de versiones publicas; lo anterior, con fundamento en: Artículo aplicable.",
            line,
        )
        self.assertNotIn("aplicable..", line)

    def test_confidential_summary_introduces_legal_basis_cohesively(self):
        line = self.writer.build_summary_line(
            "Confidencial.1",
            {
                "classification": "confidential",
                "reason": "Datos personales",
                "paragraphs": 1,
                "rows": 1,
                "legal_basis": "Artículo aplicable",
            },
        )

        self.assertIn(
            "Estado de Zacatecas; lo anterior, con fundamento en: Artículo aplicable.",
            line,
        )


if __name__ == "__main__":
    unittest.main()
