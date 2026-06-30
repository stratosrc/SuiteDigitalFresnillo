from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from App_Organigrama.exporters.pdf import PdfOrgChartExporter
from App_Organigrama.rendering.engine import RenderingEngine
from App_Organigrama.rendering.palette import NODE_COLOR_CHOICES
from App_Organigrama.routing.manhattan_router import ManhattanRouter
from App_Organigrama.routing.manual_routes import GridBox, move_bend_point, move_intermediate_segment, route_box_collisions
from App_Organigrama.services.persistence import PersistenceManager
from App_Organigrama.ui.modals.help import HELP_SECTIONS

from Main_View.backend.runtime import cleanup_tree, make_work_dir

from .schemas import OrgConnectionPayload, OrgManualRoutePayload, OrgNodePayload, OrgNodeUpdatePayload, OrgPayload

router = APIRouter(prefix="/api/organigrama")


def _document_response(document):
    engine = RenderingEngine()
    routes = ManhattanRouter(engine).route_document(document)
    return {
        "document": document.to_dict(),
        "routes": [
            {
                "connection_id": route.connection.id,
                "source_id": route.connection.source_id,
                "target_id": route.connection.target_id,
                "points": list(route.points),
            }
            for route in routes
        ],
    }


def _route_collision_node_ids(document, route_points: list[tuple[float, float]], engine: RenderingEngine) -> tuple[str, ...]:
    node_ids: list[str] = []
    boxes: list[GridBox] = []
    for node in document.nodes.values():
        node_ids.append(node.id)
        box = engine.get_node_box(node, include_logo=False)
        boxes.append(
            GridBox(
                left=box.left / engine.base_cell_width,
                top=box.top / engine.base_cell_height,
                right=box.right / engine.base_cell_width,
                bottom=box.bottom / engine.base_cell_height,
            )
        )
    collisions = route_box_collisions(route_points, boxes)
    return tuple(node_ids[index] for index in sorted(collisions))


@router.get("/help")
def get_help() -> dict:
    return {
        "title": "Ayuda de Organigramas",
        "sections": [
            {
                "title": title,
                "items": [item.strip() for item in items],
            }
            for title, items in HELP_SECTIONS
        ],
    }


@router.get("/palette")
def get_palette() -> dict:
    return {"colors": [{"label": label, "value": value} for label, value in NODE_COLOR_CHOICES]}


@router.post("/normalize")
def normalize_document(payload: OrgPayload) -> dict:
    try:
        return _document_response(PersistenceManager().from_dict(payload.document))
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/nodes")
def add_node(payload: OrgNodePayload) -> dict:
    try:
        document = PersistenceManager().from_dict(payload.document)
        document.add_node(payload.name, payload.role, payload.grid_x, payload.grid_y, payload.color)
        return _document_response(document)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/nodes/update")
def update_node(payload: OrgNodeUpdatePayload) -> dict:
    try:
        document = PersistenceManager().from_dict(payload.document)
        document.update_node(payload.node_id, payload.name, payload.role, payload.color)
        return _document_response(document)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/connections")
def add_connection(payload: OrgConnectionPayload) -> dict:
    try:
        document = PersistenceManager().from_dict(payload.document)
        connection = document.add_connection(
            payload.source_id,
            payload.target_id,
            kind=payload.kind,
            source_port=payload.source_port,
            target_port=payload.target_port,
        )
        if connection is None:
            raise ValueError("No se pudo crear la conexion.")
        return _document_response(document)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/connections/manual-route")
def update_manual_route(payload: OrgManualRoutePayload) -> dict:
    try:
        document = PersistenceManager().from_dict(payload.document)
        connection = document.get_connection(payload.connection_id)
        if connection is None:
            raise ValueError("No se encontro la conexion.")
        engine = RenderingEngine()
        routes = ManhattanRouter(engine).route_document(document)
        selected_route = next((route for route in routes if route.connection.id == payload.connection_id), None)
        if selected_route is None:
            raise ValueError("No se pudo calcular la ruta seleccionada.")
        if payload.kind == "bend":
            candidate = move_bend_point(selected_route.points, payload.index, payload.pointer)
        elif payload.kind == "segment":
            candidate = move_intermediate_segment(selected_route.points, payload.index, payload.pointer)
        else:
            raise ValueError("Tipo de edicion de ruta no valido.")
        collision_node_ids = _route_collision_node_ids(document, candidate, engine)
        if payload.commit and not collision_node_ids:
            document.set_connection_manual_points(payload.connection_id, candidate[1:-1])
            response = _document_response(document)
        else:
            response = {"document": document.to_dict(), "routes": _document_response(document)["routes"]}
        response["candidate_points"] = candidate
        response["collision_node_ids"] = collision_node_ids
        return response
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/routes")
def route_document(payload: OrgPayload) -> dict:
    try:
        document = PersistenceManager().from_dict(payload.document)
        return _document_response(document)
    except Exception as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("/pdf")
def create_pdf(payload: OrgPayload) -> FileResponse:
    work_dir = make_work_dir("suite-organigrama-")
    output_path = work_dir / "organigrama.pdf"
    try:
        document = PersistenceManager().from_dict(payload.document)
        engine = RenderingEngine()
        PdfOrgChartExporter(engine, ManhattanRouter(engine)).export(document, output_path)
    except Exception as error:
        cleanup_tree(work_dir)
        raise HTTPException(status_code=400, detail=str(error)) from error
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="organigrama.pdf",
        background=BackgroundTask(cleanup_tree, work_dir),
    )
