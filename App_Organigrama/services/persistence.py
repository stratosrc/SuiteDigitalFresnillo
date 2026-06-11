import json
from pathlib import Path

from App_Organigrama.models.document import Connection, OrgGridDocument, OrgNode

DEFAULT_DOCUMENT_TITLE = "Titulo del organigrama"


class PersistenceManager:
    """Serialize and restore documents using the public data model."""

    def save(self, document: OrgGridDocument, target_path: str | Path) -> Path:
        path = Path(target_path)
        payload = {
            "schema_version": 1,
            "document": document.to_dict(),
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, source_path: str | Path) -> OrgGridDocument:
        path = Path(source_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        raw_document = payload.get("document", payload)

        nodes = {
            node_id: OrgNode(**node_data)
            for node_id, node_data in raw_document.get("nodes", {}).items()
        }
        connections = [Connection(**connection_data) for connection_data in raw_document.get("connections", [])]
        blocked_points = [
            (float(point[0]), float(point[1]))
            for point in raw_document.get("blocked_points", [])
        ]

        return OrgGridDocument(
            title=raw_document.get("title", DEFAULT_DOCUMENT_TITLE),
            period=raw_document.get("period", ""),
            page_orientation=raw_document.get("page_orientation", "horizontal"),
            show_logos=bool(raw_document.get("show_logos", True)),
            nodes=nodes,
            connections=connections,
            blocked_points=blocked_points,
        )


__all__ = ["PersistenceManager"]
