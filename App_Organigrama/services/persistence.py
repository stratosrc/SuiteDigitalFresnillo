from __future__ import annotations

import json
from pathlib import Path

from App_Organigrama.models.document import Connection, OrgGridDocument, OrgNode
from components.shared.project_lifecycle import atomic_write_json

DEFAULT_DOCUMENT_TITLE = "Titulo del organigrama"
PROJECT_APP_ID = "organigrama"


class PersistenceManager:
    """Serialize and restore documents using the public data model."""

    def save(self, document: OrgGridDocument, target_path: str | Path) -> Path:
        path = Path(target_path)
        payload = {
            "app": PROJECT_APP_ID,
            "schema_version": 3,
            "document": document.to_dict(),
        }
        return atomic_write_json(path, payload)

    def load(self, source_path: str | Path) -> OrgGridDocument:
        path = Path(source_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("app", PROJECT_APP_ID) != PROJECT_APP_ID:
            raise ValueError("Este archivo no es un proyecto de Organigrama.")
        if "document" not in payload and not any(key in payload for key in ("nodes", "connections", "title")):
            raise ValueError("El archivo seleccionado no parece ser un proyecto de Organigrama.")
        return self.from_dict(payload.get("document", payload))

    def from_dict(self, raw_document: dict) -> OrgGridDocument:
        nodes = {}
        for node_id, raw_node in raw_document.get("nodes", {}).items():
            node_data = dict(raw_node)
            node_data["name"] = node_data.pop("nombre", node_data.get("name", ""))
            node_data["role"] = node_data.pop("cargo", node_data.get("role", ""))
            nodes[node_id] = OrgNode(**node_data)
        connections = []
        for raw_connection in raw_document.get("connections", []):
            connection_data = dict(raw_connection)
            connection_data["manual_points"] = tuple(
                (float(point[0]), float(point[1]))
                for point in connection_data.get("manual_points", [])
            )
            connections.append(Connection(**connection_data))
        blocked_points = [
            (float(point[0]), float(point[1]))
            for point in raw_document.get("blocked_points", [])
        ]
        raw_title = str(raw_document.get("title", "") or "")
        normalized_title = (
            ""
            if raw_title.strip() in {DEFAULT_DOCUMENT_TITLE, "Título del organigrama"}
            else raw_title
        )

        return OrgGridDocument(
            title=normalized_title,
            period=raw_document.get("period", ""),
            page_orientation=raw_document.get("page_orientation", "horizontal"),
            show_logos=bool(raw_document.get("show_logos", True)),
            nodes=nodes,
            connections=connections,
            blocked_points=blocked_points,
        )


__all__ = ["PersistenceManager"]
