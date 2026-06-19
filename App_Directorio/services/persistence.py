import json
from pathlib import Path

from App_Directorio.models import AreaReportData, DirectoryReportData, PersonReportRow
from components.shared.project_lifecycle import atomic_write_json

PROJECT_APP_ID = "directorio"
PROJECT_VERSION = 1


class DirectoryPersistenceManager:
    def save(self, data: DirectoryReportData, target_path: str | Path) -> Path:
        path = Path(target_path)
        payload = {
            "app": PROJECT_APP_ID,
            "version": PROJECT_VERSION,
            "directory": {
                "title": data.title,
                "period": data.period,
                "areas": [
                    {
                        "name": area.name,
                        "personnel": [
                            {
                                "rank": person.rank,
                                "name": person.name,
                                "position": person.position,
                                "email": person.email,
                                "start_date": person.start_date,
                            }
                            for person in area.personnel
                        ],
                    }
                    for area in data.areas
                ],
            },
        }
        return atomic_write_json(path, payload)

    def load(self, source_path: str | Path) -> DirectoryReportData:
        path = Path(source_path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("app") != PROJECT_APP_ID:
            raise ValueError("Este archivo no es un proyecto de Directorio.")
        if payload.get("version") != PROJECT_VERSION:
            raise ValueError("Version de proyecto no compatible.")

        raw_directory = payload.get("directory")
        if not isinstance(raw_directory, dict):
            raise ValueError("El archivo seleccionado no parece ser un proyecto de Directorio.")

        areas = []
        for raw_area in raw_directory.get("areas", []):
            personnel = [
                PersonReportRow(
                    rank=str(raw_person.get("rank", "")),
                    name=str(raw_person.get("name", "")),
                    position=str(raw_person.get("position", "")),
                    email=str(raw_person.get("email", "")),
                    start_date=str(raw_person.get("start_date", "")),
                )
                for raw_person in raw_area.get("personnel", [])
                if isinstance(raw_person, dict)
            ]
            areas.append(
                AreaReportData(
                    name=str(raw_area.get("name", "")),
                    personnel=personnel,
                )
            )

        return DirectoryReportData(
            title=str(raw_directory.get("title", "")),
            period=str(raw_directory.get("period", "")),
            areas=areas,
        )


__all__ = ["DirectoryPersistenceManager"]
