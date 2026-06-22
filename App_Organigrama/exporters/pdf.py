from dataclasses import dataclass
import logging
from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

from App_Organigrama.models.document import OrgGridDocument, OrgNode
from App_Organigrama.rendering.connection_arrows import build_arrow_triangle
from App_Organigrama.rendering.engine import Box, DocumentBounds, NodeLayout, PageLayout, RenderingEngine, VERTICAL_ORIENTATION
from App_Organigrama.routing.manhattan_router import ConnectionRoute, ManhattanRouter
from App_Organigrama.config.assets import (
    BANNER_LOGO_PATH,
    NODE_LOGO_PATH,
    SEGOE_UI_BOLD_FONT_PATH,
    SEGOE_UI_FONT_PATH,
    WATERMARK_LOGO_PATH,
)
from components.shared.images import crop_transparent, load_pil_rgba
from components.shared.atomic_output import write_atomic_output


LOGGER = logging.getLogger(__name__)
PDF_FONT_REGULAR = "SegoeUI"
PDF_FONT_BOLD = "SegoeUI-Bold"
_FONTS_REGISTERED = False


@dataclass(frozen=True, slots=True)
class PdfTransform:
    scale: float
    offset_x: float
    offset_y: float
    page_height: float
    bounds: DocumentBounds

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

    def export(self, document: OrgGridDocument, target_path: str | Path) -> Path:
        self._register_fonts()
        path = Path(target_path)
        return write_atomic_output(
            path,
            lambda temporary: self._write_pdf(document, temporary),
        )

    def _write_pdf(self, document: OrgGridDocument, path: Path) -> None:
        page_layout = self.rendering_engine.get_page_layout(document.page_orientation)
        canvas = Canvas(str(path), pagesize=(page_layout.width, page_layout.height))

        self._draw_background_assets(canvas, page_layout)
        self._draw_header(canvas, document, page_layout)

        routes = self.router.route_document(document)
        if document.nodes:
            transform = self._build_transform(document, page_layout, routes)
            self._draw_connections(canvas, transform, routes)
            self._draw_nodes(canvas, transform, document)

        canvas.save()

    def _register_fonts(self) -> None:
        global _FONTS_REGISTERED
        if _FONTS_REGISTERED:
            return

        if SEGOE_UI_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(PDF_FONT_REGULAR, str(SEGOE_UI_FONT_PATH)))
        if SEGOE_UI_BOLD_FONT_PATH.exists():
            pdfmetrics.registerFont(TTFont(PDF_FONT_BOLD, str(SEGOE_UI_BOLD_FONT_PATH)))
        _FONTS_REGISTERED = True

    def _build_transform(
        self,
        document: OrgGridDocument,
        page_layout: PageLayout,
        routes: list[ConnectionRoute],
    ) -> PdfTransform:
        route_points = [list(route.points) for route in routes]
        bounds = self.rendering_engine.compute_document_bounds(document, route_points, include_blocked_points=False)
        available_width = page_layout.width - page_layout.margin_left - page_layout.margin_right
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
        scale = min(1.0, available_width / content_width, usable_height / content_height)
        offset_x = page_layout.margin_left + ((available_width - (content_width * scale)) / 2)
        offset_y = content_origin_y + content_top_margin
        return PdfTransform(
            scale=scale,
            offset_x=offset_x,
            offset_y=offset_y,
            page_height=page_layout.height,
            bounds=bounds,
        )

    def _draw_background_assets(self, pdf: Canvas, page_layout: PageLayout) -> None:
        if WATERMARK_LOGO_PATH.exists():
            pdf.saveState()
            pdf.setFillColor(Color(1, 1, 1, alpha=1))
            pdf.drawImage(
                str(WATERMARK_LOGO_PATH),
                (page_layout.width / 2) - 232,
                (page_layout.height / 2) - 310,
                width=465,
                height=633,
                mask="auto",
            )
            pdf.restoreState()

        if BANNER_LOGO_PATH.exists():
            banner_width = 250
            banner_height = 125
            pdf.drawImage(
                str(BANNER_LOGO_PATH),
                1,
                page_layout.height - banner_height + 15,
                width=banner_width,
                height=banner_height,
                mask="auto",
            )

    def _draw_header(self, pdf: Canvas, document: OrgGridDocument, page_layout: PageLayout) -> None:
        title = document.title.strip() or "Título del organigrama"
        period = document.period.strip()
        title_y = page_layout.height - 84
        period_y = title_y - 26
        if document.page_orientation == VERTICAL_ORIENTATION:
            title_y = page_layout.height - 98
            period_y = title_y - 28

        title_font_size = self._fit_text_size(pdf, title, PDF_FONT_BOLD, 20.0, page_layout.width - 210)
        pdf.setFillColor(HexColor("#263238"))
        pdf.setFont(PDF_FONT_BOLD, title_font_size)
        pdf.drawCentredString(page_layout.width / 2, title_y, title)

        if period:
            period_font_size = self._fit_text_size(pdf, period, PDF_FONT_REGULAR, 18.0, page_layout.width - 220)
            pdf.setFont(PDF_FONT_REGULAR, period_font_size)
            pdf.drawCentredString(page_layout.width / 2, period_y, period)

    def _fit_text_size(
        self,
        pdf: Canvas,
        text: str,
        font_name: str,
        start_size: float,
        max_width: float,
    ) -> float:
        size = start_size
        while size > 8 and pdf.stringWidth(text, font_name, size) > max_width:
            size -= 0.5
        return size

    def _draw_connections(self, pdf: Canvas, transform: PdfTransform, routes: list[ConnectionRoute]) -> None:
        pdf.setStrokeColor(HexColor("#09519F"))
        pdf.setFillColor(HexColor("#09519F"))
        for route in routes:
            if len(route.points) < 2:
                continue
            line_width = self.rendering_engine.base_line_width * transform.scale
            pdf.setLineWidth(max(0.75, line_width))
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
                length=max(4.5, 8.0 * transform.scale),
                width=max(4.5, 7.0 * transform.scale),
                target_gap=max(3.5, 6.0 * transform.scale),
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
        pdf.roundRect(x, y, width, height, 5, fill=True, stroke=True)

        if show_logo:
            self._draw_node_logo(pdf, transform, layout, node.color)

        pdf.setFillColor(HexColor("#FFFFFF"))
        for line in layout.lines:
            font_name = PDF_FONT_BOLD if line.is_bold else PDF_FONT_REGULAR
            pdf.setFont(font_name, line.font_size * transform.scale)
            baseline_world_y = layout.box.top + line.top + line.font_size 
            pdf.drawCentredString(
                transform.world_to_pdf_x(layout.center_x),
                transform.world_to_pdf_center_y(baseline_world_y),
                line.text,
            )

    def _draw_node_logo(self, pdf: Canvas, transform: PdfTransform, layout: NodeLayout, color: str) -> None:
        center_x = transform.world_to_pdf_x(layout.logo_center_x)
        center_y = transform.world_to_pdf_center_y(layout.logo_center_y)
        radius = layout.style.logo_radius * transform.scale
        pdf.setFillColor(HexColor(color))
        pdf.setStrokeColor(HexColor("#FFFFFF"))
        pdf.setLineWidth(max(0.8, transform.scale))
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


__all__ = ["PdfOrgChartExporter"]
