from dataclasses import dataclass
from io import BytesIO
import logging
import math
from pathlib import Path

import fitz
from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas

from App_Organigrama.models.document import OrgGridDocument, OrgNode
from App_Organigrama.rendering.connection_arrows import build_arrow_triangle
from App_Organigrama.rendering.engine import Box, DocumentBounds, NodeLayout, PageLayout, RenderingEngine
from App_Organigrama.routing.manhattan_router import ConnectionRoute, ManhattanRouter
from App_Organigrama.config.assets import (
    BANNER_LOGO_PATH,
    NODE_LOGO_PATH,
    WATERMARK_LOGO_PATH,
)
from components.shared.images import crop_transparent, load_pil_rgba
from components.shared.atomic_output import write_atomic_output
from components.styles.styles import PDF_FONT_BOLD, PDF_FONT_REGULAR


LOGGER = logging.getLogger(__name__)
DIGITAL_CONTENT_SCALE = 0.75
MAX_PDF_MEDIA_BOX_POINTS = 14_000.0
MAX_PDF_USER_UNIT = 75
MIN_DIGITAL_PAGE_WIDTH = 792.0
MIN_DIGITAL_PAGE_HEIGHT = 612.0
DIGITAL_MARGIN_X = 24.0
DIGITAL_MARGIN_BOTTOM = 24.0
DIGITAL_MARGIN_TOP = 16.0
DIGITAL_HEADER_HEIGHT = 112.0
DIGITAL_CONTENT_TOP_MARGIN = 18.0
MAX_DIGITAL_DECORATION_SCALE = 4.0
WATERMARK_PAGE_RATIO = 0.80
WATERMARK_ASPECT_RATIO = 465 / 633


@dataclass(frozen=True, slots=True)
class PdfTransform:
    scale: float
    offset_x: float
    offset_y: float
    page_height: float
    bounds: DocumentBounds
    user_unit: float = 1.0

    def world_to_pdf_x(self, world_x: float) -> float:
        return self.offset_x + ((world_x - self.bounds.left) * self.scale)

    def world_to_pdf_top(self, world_y: float) -> float:
        return self.offset_y + ((world_y - self.bounds.top) * self.scale)

    def world_to_pdf_center_y(self, world_y: float) -> float:
        return self.page_height - self.world_to_pdf_top(world_y)

    def box_to_pdf(self, box: Box) -> tuple[float, float, float, float]:
        x = self.world_to_pdf_x(box.left)
        top = self.world_to_pdf_top(box.top)
        width = box.width * self.scale
        height = box.height * self.scale
        y = self.page_height - top - height
        return (x, y, width, height)


class PdfOrgChartExporter:
    def __init__(self, rendering_engine: RenderingEngine, router: ManhattanRouter) -> None:
        self.rendering_engine = rendering_engine
        self.router = router
        self._node_logo_reader = self._load_node_logo_reader()

    def export(
        self,
        document: OrgGridDocument,
        target_path: str | Path,
        *,
        digital: bool = True,
    ) -> Path:
        path = Path(target_path)
        return write_atomic_output(
            path,
            lambda temporary: self._write_pdf(
                document,
                temporary,
                digital=digital,
            ),
        )

    def _write_pdf(
        self,
        document: OrgGridDocument,
        path: Path,
        *,
        digital: bool,
    ) -> None:
        routes = self.router.route_document(document)
        if not digital:
            self._write_page_pdf(document, path, routes)
            return

        (
            page_layout,
            transform,
            user_unit,
            decoration_scale,
        ) = self._build_digital_layout(
            document,
            routes,
        )
        pdf_buffer = BytesIO()
        canvas = Canvas(
            pdf_buffer,
            pagesize=(page_layout.width, page_layout.height),
            pdfVersion=(1, 6),
            pageCompression=1,
        )

        drawing_unit = decoration_scale / user_unit
        self._draw_background_assets(canvas, page_layout, drawing_unit)
        self._draw_header(canvas, document, page_layout, drawing_unit)

        if document.nodes:
            self._draw_connections(canvas, transform, routes)
            self._draw_nodes(canvas, transform, document)

        canvas.save()
        pdf_buffer.seek(0)
        with fitz.open(stream=pdf_buffer.getvalue(), filetype="pdf") as pdf_document:
            if user_unit > 1:
                pdf_document.xref_set_key(
                    pdf_document[0].xref,
                    "UserUnit",
                    self._format_pdf_number(user_unit),
                )
            pdf_document.save(path)

    def _write_page_pdf(
        self,
        document: OrgGridDocument,
        path: Path,
        routes: list[ConnectionRoute],
    ) -> None:
        page_layout = self.rendering_engine.get_page_layout(
            document.page_orientation
        )
        canvas = Canvas(
            str(path),
            pagesize=(page_layout.width, page_layout.height),
            pageCompression=1,
        )
        self._draw_background_assets(canvas, page_layout, 1.0)
        self._draw_header(canvas, document, page_layout, 1.0)
        if document.nodes:
            transform = self._build_page_transform(
                document,
                page_layout,
                routes,
            )
            self._draw_connections(canvas, transform, routes)
            self._draw_nodes(canvas, transform, document)
        canvas.save()

    def _build_digital_layout(
        self,
        document: OrgGridDocument,
        routes: list[ConnectionRoute],
    ) -> tuple[PageLayout, PdfTransform, float, float]:
        route_points = [list(route.points) for route in routes]
        bounds = self.rendering_engine.compute_document_bounds(
            document,
            route_points,
        )
        content_width = max(bounds.width, 1.0)
        content_height = max(bounds.height, 1.0)
        decoration_scale = self._digital_decoration_scale(
            content_width,
            content_height,
        )
        margin_x = DIGITAL_MARGIN_X * decoration_scale
        margin_bottom = DIGITAL_MARGIN_BOTTOM * decoration_scale
        margin_top = DIGITAL_MARGIN_TOP * decoration_scale
        header_height = DIGITAL_HEADER_HEIGHT * decoration_scale
        content_top_margin = DIGITAL_CONTENT_TOP_MARGIN * decoration_scale

        max_digital_dimension = MAX_PDF_MEDIA_BOX_POINTS * MAX_PDF_USER_UNIT
        max_content_width = max_digital_dimension - (margin_x * 2)
        max_content_height = max_digital_dimension - (
            margin_top
            + header_height
            + content_top_margin
            + margin_bottom
        )
        content_scale = min(
            DIGITAL_CONTENT_SCALE,
            max_content_width / content_width,
            max_content_height / content_height,
        )

        desired_content_width = content_width * content_scale
        desired_content_height = content_height * content_scale
        desired_page_width = max(
            MIN_DIGITAL_PAGE_WIDTH,
            desired_content_width + (margin_x * 2),
        )
        desired_page_height = max(
            MIN_DIGITAL_PAGE_HEIGHT,
            margin_top
            + header_height
            + content_top_margin
            + desired_content_height
            + margin_bottom,
        )
        user_unit = float(
            max(
                1,
                min(
                    MAX_PDF_USER_UNIT,
                    math.ceil(
                        max(desired_page_width, desired_page_height)
                        / MAX_PDF_MEDIA_BOX_POINTS
                    ),
                ),
            )
        )
        coordinate_scale = 1.0 / user_unit
        page_layout = PageLayout(
            width=desired_page_width * coordinate_scale,
            height=desired_page_height * coordinate_scale,
            margin_left=margin_x * coordinate_scale,
            margin_top=margin_top * coordinate_scale,
            margin_right=margin_x * coordinate_scale,
            margin_bottom=margin_bottom * coordinate_scale,
            header_height=header_height * coordinate_scale,
        )
        available_width = desired_page_width - (margin_x * 2)
        offset_x = (
            margin_x
            + ((available_width - desired_content_width) / 2)
        ) * coordinate_scale
        offset_y = (
            margin_top
            + header_height
            + content_top_margin
        ) * coordinate_scale
        transform = PdfTransform(
            scale=content_scale * coordinate_scale,
            offset_x=offset_x,
            offset_y=offset_y,
            page_height=page_layout.height,
            bounds=bounds,
            user_unit=user_unit,
        )
        return page_layout, transform, user_unit, decoration_scale

    def _digital_decoration_scale(
        self,
        content_width: float,
        content_height: float,
    ) -> float:
        reference_width = (
            MIN_DIGITAL_PAGE_WIDTH - (DIGITAL_MARGIN_X * 2)
        )
        reference_height = (
            MIN_DIGITAL_PAGE_HEIGHT
            - DIGITAL_MARGIN_TOP
            - DIGITAL_HEADER_HEIGHT
            - DIGITAL_CONTENT_TOP_MARGIN
            - DIGITAL_MARGIN_BOTTOM
        )
        extent_ratio = max(
            (content_width * DIGITAL_CONTENT_SCALE) / reference_width,
            (content_height * DIGITAL_CONTENT_SCALE) / reference_height,
        )
        if extent_ratio <= 1.5:
            return 1.0
        return min(
            MAX_DIGITAL_DECORATION_SCALE,
            math.sqrt(extent_ratio),
        )

    def _build_page_transform(
        self,
        document: OrgGridDocument,
        page_layout: PageLayout,
        routes: list[ConnectionRoute],
    ) -> PdfTransform:
        route_points = [list(route.points) for route in routes]
        bounds = self.rendering_engine.compute_document_bounds(
            document,
            route_points,
        )
        available_width = (
            page_layout.width
            - page_layout.margin_left
            - page_layout.margin_right
        )
        available_height = (
            page_layout.height
            - page_layout.margin_top
            - page_layout.margin_bottom
            - page_layout.header_height
        )
        content_origin_y = page_layout.margin_top + page_layout.header_height
        content_top_margin = self.rendering_engine.content_top_margin
        content_width = max(bounds.width, 1.0)
        content_height = max(bounds.height, 1.0)
        usable_height = max(1.0, available_height - content_top_margin)
        scale = min(
            1.0,
            available_width / content_width,
            usable_height / content_height,
        )
        offset_x = page_layout.margin_left + (
            (available_width - (content_width * scale)) / 2
        )
        offset_y = content_origin_y + content_top_margin
        return PdfTransform(
            scale=scale,
            offset_x=offset_x,
            offset_y=offset_y,
            page_height=page_layout.height,
            bounds=bounds,
        )

    def _draw_background_assets(
        self,
        pdf: Canvas,
        page_layout: PageLayout,
        drawing_unit: float,
    ) -> None:
        if WATERMARK_LOGO_PATH.exists():
            watermark_width, watermark_height = self._watermark_dimensions(
                page_layout,
            )
            pdf.saveState()
            pdf.setFillColor(Color(1, 1, 1, alpha=1))
            pdf.drawImage(
                str(WATERMARK_LOGO_PATH),
                (page_layout.width - watermark_width) / 2,
                (page_layout.height - watermark_height) / 2,
                width=watermark_width,
                height=watermark_height,
                mask="auto",
            )
            pdf.restoreState()

        if BANNER_LOGO_PATH.exists():
            banner_width = 250 * drawing_unit
            banner_height = 125 * drawing_unit
            pdf.drawImage(
                str(BANNER_LOGO_PATH),
                1 * drawing_unit,
                page_layout.height - banner_height + (15 * drawing_unit),
                width=banner_width,
                height=banner_height,
                mask="auto",
            )

    def _watermark_dimensions(
        self,
        page_layout: PageLayout,
    ) -> tuple[float, float]:
        max_width = page_layout.width * WATERMARK_PAGE_RATIO
        max_height = page_layout.height * WATERMARK_PAGE_RATIO
        if max_width / max_height <= WATERMARK_ASPECT_RATIO:
            return max_width, max_width / WATERMARK_ASPECT_RATIO
        return max_height * WATERMARK_ASPECT_RATIO, max_height

    def _draw_header(
        self,
        pdf: Canvas,
        document: OrgGridDocument,
        page_layout: PageLayout,
        drawing_unit: float,
    ) -> None:
        title = document.title.strip() or "Título del organigrama"
        period = document.period.strip()
        title_y = page_layout.height - (84 * drawing_unit)
        period_y = title_y - (26 * drawing_unit)
        title_font_size = self._fit_text_size(
            pdf,
            title,
            PDF_FONT_BOLD,
            20.0 * drawing_unit,
            page_layout.width - (210 * drawing_unit),
            minimum_size=8.0 * drawing_unit,
        )
        pdf.setFillColor(HexColor("#263238"))
        pdf.setFont(PDF_FONT_BOLD, title_font_size)
        pdf.drawCentredString(page_layout.width / 2, title_y, title)

        if period:
            period_font_size = self._fit_text_size(
                pdf,
                period,
                PDF_FONT_REGULAR,
                18.0 * drawing_unit,
                page_layout.width - (220 * drawing_unit),
                minimum_size=8.0 * drawing_unit,
            )
            pdf.setFont(PDF_FONT_REGULAR, period_font_size)
            pdf.drawCentredString(page_layout.width / 2, period_y, period)

    def _fit_text_size(
        self,
        pdf: Canvas,
        text: str,
        font_name: str,
        start_size: float,
        max_width: float,
        *,
        minimum_size: float = 8.0,
    ) -> float:
        size = start_size
        step = max(0.05, 0.5 * (start_size / 20.0))
        while size > minimum_size and pdf.stringWidth(text, font_name, size) > max_width:
            size -= step
        return size

    def _draw_connections(self, pdf: Canvas, transform: PdfTransform, routes: list[ConnectionRoute]) -> None:
        pdf.setStrokeColor(HexColor("#09519F"))
        pdf.setFillColor(HexColor("#09519F"))
        for route in routes:
            if len(route.points) < 2:
                continue
            line_width = self.rendering_engine.base_line_width * transform.scale
            pdf.setLineWidth(max(0.75 / transform.user_unit, line_width))
            pdf_points: list[tuple[float, float]] = []
            for start, end in zip(route.points, route.points[1:]):
                start_x, start_y = self.rendering_engine.grid_to_world(start[0], start[1])
                end_x, end_y = self.rendering_engine.grid_to_world(end[0], end[1])
                if not pdf_points:
                    pdf_points.append(
                        (
                            transform.world_to_pdf_x(start_x),
                            transform.world_to_pdf_center_y(start_y),
                        )
                    )
                pdf_points.append(
                    (
                        transform.world_to_pdf_x(end_x),
                        transform.world_to_pdf_center_y(end_y),
                    )
                )
                pdf.line(
                    transform.world_to_pdf_x(start_x),
                    transform.world_to_pdf_center_y(start_y),
                    transform.world_to_pdf_x(end_x),
                    transform.world_to_pdf_center_y(end_y),
                )
            arrow = build_arrow_triangle(
                pdf_points,
                length=max(4.5 / transform.user_unit, 8.0 * transform.scale),
                width=max(4.5 / transform.user_unit, 7.0 * transform.scale),
                target_gap=max(3.5 / transform.user_unit, 6.0 * transform.scale),
            )
            if arrow is not None:
                path = pdf.beginPath()
                path.moveTo(*arrow[0])
                path.lineTo(*arrow[1])
                path.lineTo(*arrow[2])
                path.close()
                pdf.drawPath(path, fill=True, stroke=False)

    def _draw_nodes(self, pdf: Canvas, transform: PdfTransform, document: OrgGridDocument) -> None:
        for node in document.nodes.values():
            layout = self.rendering_engine.layout_node(node, include_logo=document.show_logos)
            self._draw_node(pdf, transform, node, layout, show_logo=document.show_logos)

    def _draw_node(
        self,
        pdf: Canvas,
        transform: PdfTransform,
        node: OrgNode,
        layout: NodeLayout,
        show_logo: bool,
    ) -> None:
        x, y, width, height = transform.box_to_pdf(layout.box)
        pdf.setFillColor(HexColor(node.color))
        pdf.setStrokeColor(HexColor(node.color))
        pdf.roundRect(
            x,
            y,
            width,
            height,
            5 / transform.user_unit,
            fill=True,
            stroke=True,
        )

        if show_logo:
            self._draw_node_logo(pdf, transform, layout, node.color)

        pdf.setFillColor(HexColor("#FFFFFF"))
        pdf.setStrokeColor(HexColor("#FFFFFF"))
        for line in layout.lines:
            font_name = PDF_FONT_BOLD if line.is_bold else PDF_FONT_REGULAR
            scaled_font_size = line.font_size * transform.scale
            pdf.setFont(font_name, scaled_font_size)
            baseline_world_y = layout.box.top + line.top + line.font_size 
            baseline_pdf_y = transform.world_to_pdf_center_y(baseline_world_y)
            text_width = pdf.stringWidth(line.text, font_name, scaled_font_size)
            if line.align == "left":
                text_x = transform.world_to_pdf_x(layout.box.left + layout.style.text_padding_x)
                pdf.drawString(text_x, baseline_pdf_y, line.text)
            else:
                text_x = transform.world_to_pdf_x(layout.center_x) - (text_width / 2)
                pdf.drawCentredString(transform.world_to_pdf_x(layout.center_x), baseline_pdf_y, line.text)
            if line.is_underlined:
                underline_y = baseline_pdf_y - max(
                    0.8 / transform.user_unit,
                    transform.scale * 1.2,
                )
                pdf.setLineWidth(
                    max(0.6 / transform.user_unit, transform.scale * 0.9)
                )
                pdf.line(text_x, underline_y, text_x + text_width, underline_y)

    def _draw_node_logo(self, pdf: Canvas, transform: PdfTransform, layout: NodeLayout, color: str) -> None:
        center_x = transform.world_to_pdf_x(layout.logo_center_x)
        center_y = transform.world_to_pdf_center_y(layout.logo_center_y)
        radius = layout.style.logo_radius * transform.scale
        pdf.setFillColor(HexColor(color))
        pdf.setStrokeColor(HexColor("#FFFFFF"))
        pdf.setLineWidth(max(0.8 / transform.user_unit, transform.scale))
        pdf.circle(center_x, center_y, radius, fill=True, stroke=True)

        if self._node_logo_reader is None:
            return

        image_size = layout.logo_image_size * transform.scale
        pdf.drawImage(
            self._node_logo_reader,
            center_x - (image_size / 2),
            center_y - (image_size / 2),
            width=image_size,
            height=image_size,
            mask="auto",
        )

    def _load_node_logo_reader(self) -> ImageReader | None:
        image = load_pil_rgba(NODE_LOGO_PATH)
        if image is None:
            return None

        try:
            return ImageReader(crop_transparent(image))
        except OSError as error:
            LOGGER.warning("Unable to load node logo: %s", error)
            return None

    def _format_pdf_number(self, value: float) -> str:
        if value.is_integer():
            return str(int(value))
        return f"{value:.6f}".rstrip("0").rstrip(".")


__all__ = ["PdfOrgChartExporter"]
