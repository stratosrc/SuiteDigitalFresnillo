"""Generate the deterministic large directory project used for performance QA."""

from __future__ import annotations

import json
from pathlib import Path
import random
import unicodedata


SEED = 20260723
PEOPLE_PER_AREA = 300
AREA_NAMES = (
    "COORDINACIÓN DE SERVICIOS DIGITALES",
    "DIRECCIÓN DE OPERACIÓN TERRITORIAL",
    "UNIDAD DE ATENCIÓN CIUDADANA",
)
FIRST_NAMES = (
    "Alejandra",
    "Ana",
    "Carlos",
    "Daniel",
    "Elena",
    "Fernanda",
    "Gabriel",
    "Héctor",
    "Isabel",
    "Jorge",
    "Laura",
    "Luis",
    "Mariana",
    "Miguel",
    "Natalia",
    "Óscar",
    "Patricia",
    "Raúl",
    "Sofía",
    "Víctor",
)
LAST_NAMES = (
    "Álvarez",
    "Cabrera",
    "Castillo",
    "Chávez",
    "Delgado",
    "Flores",
    "García",
    "González",
    "Hernández",
    "Jiménez",
    "López",
    "Martínez",
    "Medina",
    "Mendoza",
    "Morales",
    "Navarro",
    "Ortega",
    "Ramírez",
    "Reyes",
    "Sánchez",
)
POSITIONS = (
    "Analista Administrativo",
    "Auxiliar de Área",
    "Coordinación de Proyecto",
    "Enlace Institucional",
    "Especialista Técnico",
    "Jefatura de Departamento",
    "Responsable de Seguimiento",
    "Supervisión Operativa",
    "Técnico de Soporte",
)


def email_fragment(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(character for character in normalized if character.isascii() and character.isalnum()).lower()


def build_person(rng: random.Random, area_number: int, person_number: int) -> dict[str, str]:
    first_name = rng.choice(FIRST_NAMES)
    first_last_name = rng.choice(LAST_NAMES)
    second_last_name = rng.choice(LAST_NAMES)
    name = f"{first_name} {first_last_name} {second_last_name}"
    email = (
        f"{email_fragment(first_name)}.{email_fragment(first_last_name)}."
        f"a{area_number:02d}{person_number:03d}@fresnillo.gob.mx"
    )
    day = 1 + ((person_number * 7 + area_number) % 28)
    month = 1 + ((person_number + area_number * 3) % 12)
    year = 2018 + ((person_number + area_number) % 9)
    return {
        "rank": f"NIVEL {1 + ((person_number + area_number) % 12):02d}",
        "name": name,
        "position": rng.choice(POSITIONS),
        "email": email,
        "start_date": f"{day:02d}/{month:02d}/{year}",
    }


def build_payload() -> dict[str, object]:
    rng = random.Random(SEED)
    areas = []
    for area_number, area_name in enumerate(AREA_NAMES, start=1):
        areas.append(
            {
                "name": area_name,
                "personnel": [
                    build_person(rng, area_number, person_number)
                    for person_number in range(1, PEOPLE_PER_AREA + 1)
                ],
            }
        )
    return {
        "app": "directorio",
        "version": 1,
        "directory": {
            "title": "DIRECTORIO DE PRUEBA DE ALTO VOLUMEN",
            "period": "ENERO - DICIEMBRE 2026",
            "areas": areas,
        },
    }


def main() -> None:
    target = Path(__file__).with_name("directorio_3_areas_900_registros.dir")
    target.write_text(
        json.dumps(build_payload(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
