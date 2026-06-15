from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Image as PdfImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from App_Directorio.config import DIRECTORY_ICON_PATH
from App_Directorio.models import DirectoryReportData
from App_Directorio.utils import crop_transparent_padding


HEADER_BACKGROUND = colors.HexColor("#131C46")
AREA_BACKGROUND = colors.HexColor("#E1E1E1")
PDF_PAGE_SIZE = landscape(letter)
HEADER_ROW_HEIGHT = 1.24 * inch
HEADER_VERTICAL_PADDING = 2
HEADER_HORIZONTAL_PADDING = 12
HEADER_LOGO_COLUMN_RATIO = 0.30
HEADER_CENTER_COLUMN_RATIO = 0.40
HEADER_LOGO_SCALE = 0.64
HEADER_LOGO_HEIGHT = (HEADER_ROW_HEIGHT - (HEADER_VERTICAL_PADDING * 2)) * HEADER_LOGO_SCALE
HEADER_TITLE_MAX_SIZE = 16
HEADER_TITLE_MIN_SIZE = 9
HEADER_PERIOD_MAX_SIZE = 14
HEADER_PERIOD_MIN_SIZE = 8


class DirectoryPdfExporter:
    def export(self, data: DirectoryReportData, target_path: str | Path) -> Path:
        path = Path(target_path)
        document = SimpleDocTemplate(
            str(path),
            pagesize=PDF_PAGE_SIZE,
            leftMargin=0.35 * inch,
            rightMargin=0.35 * inch,
            topMargin=0.35 * inch,
            bottomMargin=0.35 * inch,
            title=data.title or "Directorio",
        )
        available_width = document.width
        elements = [
            self._build_main_header(data, available_width),
            Spacer(1, 6),
            self._build_directory_table(data, available_width),
        ]
        document.build(elements)
        return path

    def _build_main_header(self, data: DirectoryReportData, available_width: float) -> Table:
        title = data.title or "Directorio"
        period = data.period or ""
        center_width = (available_width * HEADER_CENTER_COLUMN_RATIO) - (HEADER_HORIZONTAL_PADDING * 2)
        center_content, center_height = self._fit_header_center_content(title, period, center_width)
        row_height = max(HEADER_ROW_HEIGHT, center_height + (HEADER_VERTICAL_PADDING * 2))
        table = Table(
            [[self._logo_flowable(), center_content, self._logo_flowable()]],
            colWidths=[
                available_width * HEADER_LOGO_COLUMN_RATIO,
                available_width * HEADER_CENTER_COLUMN_RATIO,
                available_width * HEADER_LOGO_COLUMN_RATIO,
            ],
            rowHeights=[row_height],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HEADER_BACKGROUND),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), HEADER_HORIZONTAL_PADDING),
                    ("RIGHTPADDING", (0, 0), (-1, -1), HEADER_HORIZONTAL_PADDING),
                    ("TOPPADDING", (0, 0), (-1, -1), HEADER_VERTICAL_PADDING),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), HEADER_VERTICAL_PADDING),
                ]
            )
        )
        return table

    def _fit_header_center_content(self, title: str, period: str, max_width: float) -> tuple[Paragraph, float]:
        available_height = HEADER_ROW_HEIGHT - (HEADER_VERTICAL_PADDING * 2)
        title_size = HEADER_TITLE_MAX_SIZE
        best_paragraph = self._build_header_center_content(title, period, title_size)
        _, best_height = best_paragraph.wrap(max_width, 1000)

        while title_size > HEADER_TITLE_MIN_SIZE and best_height > available_height:
            title_size -= 0.5
            candidate = self._build_header_center_content(title, period, title_size)
            _, candidate_height = candidate.wrap(max_width, 1000)
            best_paragraph = candidate
            best_height = candidate_height

        return best_paragraph, best_height

    def _build_header_center_content(self, title: str, period: str, title_size: float) -> Paragraph:
        period_size = max(HEADER_PERIOD_MIN_SIZE, min(HEADER_PERIOD_MAX_SIZE, title_size - 2))
        leading = max(title_size + 4, period_size + 4)
        period_markup = ""
        if period:
            period_markup = f"<br/><font size='{period_size:g}'>{self._pdf_text(period)}</font>"
        return Paragraph(
            f"<b><font size='{title_size:g}'>{self._pdf_text(title)}</font></b>{period_markup}",
            ParagraphStyle(
                "MainHeaderCenter",
                fontName="Helvetica",
                fontSize=title_size,
                leading=leading,
                alignment=1,
                textColor=colors.white,
                splitLongWords=1,
                wordWrap="LTR",
            ),
        )

    def _build_directory_table(self, data: DirectoryReportData, available_width: float) -> Table:
        header_style = self._cell_style("ColumnHeader", colors.white, bold=True)
        body_style = self._cell_style("BodyCell", colors.black)
        area_style = self._cell_style("ÁreaCell", colors.black, bold=True)
        rows: list[list[Paragraph]] = [
            [
                Paragraph("Rango/Clave/Nivel", header_style),
                Paragraph("Nombre", header_style),
                Paragraph("Cargo", header_style),
                Paragraph("Fecha de Alta", header_style),
            ]
        ]
        styles = [
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BACKGROUND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.45, colors.HexColor("#A8A8A8")),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]

        for area in data.areas:
            area_row_index = len(rows)
            rows.append([Paragraph(self._pdf_text(area.name or "Área sin nombre"), area_style), "", "", ""])
            styles.extend(
                [
                    ("SPAN", (0, area_row_index), (-1, area_row_index)),
                    ("BACKGROUND", (0, area_row_index), (-1, area_row_index), AREA_BACKGROUND),
                ]
            )

            for person in area.personnel:
                rows.append(
                    [
                        Paragraph(self._pdf_text(person.rank), body_style),
                        Paragraph(self._pdf_text(person.name), body_style),
                        Paragraph(self._pdf_text(person.position), body_style),
                        Paragraph(self._pdf_text(person.start_date), body_style),
                    ]
                )

        table = Table(
            rows,
            colWidths=[
                available_width * 0.22,
                available_width * 0.30,
                available_width * 0.32,
                available_width * 0.16,
            ],
            repeatRows=1,
        )
        table.setStyle(TableStyle(styles))
        return table

    def _cell_style(self, name: str, text_color: colors.Color, bold: bool = False) -> ParagraphStyle:
        return ParagraphStyle(
            name,
            fontName="Helvetica-Bold" if bold else "Helvetica",
            fontSize=9.5,
            leading=11.5,
            textColor=text_color,
            splitLongWords=1,
            wordWrap="LTR",
        )

    def _logo_flowable(self) -> PdfImage | str:
        if not DIRECTORY_ICON_PATH.exists():
            return ""
        try:
            image = crop_transparent_padding(Image.open(DIRECTORY_ICON_PATH))
            image_buffer = BytesIO()
            image.save(image_buffer, format="PNG")
            image_buffer.seek(0)
            aspect_ratio = image.width / image.height
            return PdfImage(
                image_buffer,
                width=HEADER_LOGO_HEIGHT * aspect_ratio,
                height=HEADER_LOGO_HEIGHT,
                kind="proportional",
            )
        except OSError:
            return ""

    def _pdf_text(self, value: str) -> str:
        return escape(value).replace("\n", "<br/>")


__all__ = [
    "DirectoryPdfExporter",
]
