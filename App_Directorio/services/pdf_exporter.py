from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class PersonReportRow:
    rank: str
    name: str
    position: str
    start_date: str


@dataclass(frozen=True, slots=True)
class AreaReportData:
    name: str
    personnel: list[PersonReportRow]


@dataclass(frozen=True, slots=True)
class DirectoryReportData:
    title: str
    period: str
    areas: list[AreaReportData]


HEADER_BACKGROUND = colors.HexColor("#131C46")
AREA_BACKGROUND = colors.HexColor("#E1E1E1")
PDF_PAGE_SIZE = landscape(letter)
HEADER_ROW_HEIGHT = 1.24 * inch
HEADER_VERTICAL_PADDING = 2
HEADER_LOGO_SCALE = 0.64
HEADER_LOGO_HEIGHT = (HEADER_ROW_HEIGHT - (HEADER_VERTICAL_PADDING * 2)) * HEADER_LOGO_SCALE


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
        center_content = Paragraph(
            f"<b>{self._pdf_text(title)}</b><br/><font size='14'>{self._pdf_text(period)}</font>",
            ParagraphStyle(
                "MainHeaderCenter",
                fontName="Helvetica",
                fontSize=16,
                leading=20,
                alignment=1,
                textColor=colors.white,
                splitLongWords=1,
            ),
        )
        table = Table(
            [[self._logo_flowable(), center_content, self._logo_flowable()]],
            colWidths=[available_width * 0.30, available_width * 0.40, available_width * 0.30],
            rowHeights=[HEADER_ROW_HEIGHT],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), HEADER_BACKGROUND),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "CENTER"),
                    ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 12),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                    ("TOPPADDING", (0, 0), (-1, -1), HEADER_VERTICAL_PADDING),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), HEADER_VERTICAL_PADDING),
                ]
            )
        )
        return table

    def _build_directory_table(self, data: DirectoryReportData, available_width: float) -> Table:
        header_style = self._cell_style("ColumnHeader", colors.white, bold=True)
        body_style = self._cell_style("BodyCell", colors.black)
        area_style = self._cell_style("AreaCell", colors.black, bold=True)
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
            image = Image.open(DIRECTORY_ICON_PATH).convert("RGBA")
            visible_box = image.getchannel("A").getbbox()
            if visible_box:
                image = image.crop(visible_box)
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
    "AreaReportData",
    "DirectoryPdfExporter",
    "DirectoryReportData",
    "PersonReportRow",
]
