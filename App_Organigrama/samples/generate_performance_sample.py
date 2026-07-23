from __future__ import annotations

import argparse
from pathlib import Path
import random

from App_Organigrama.models.document import Connection, OrgGridDocument, OrgNode
from App_Organigrama.rendering.palette import (
    LIGHT_BLUE,
    NEUTRAL_GRAY,
    PRIMARY_BLUE,
    SECONDARY_BLUE,
)
from App_Organigrama.services.persistence import PersistenceManager


DEFAULT_SEED = 20260723
DEFAULT_OUTPUT = Path(__file__).with_name("organigrama_rendimiento_300.og")

FIRST_NAMES = (
    "Alejandra",
    "Andrea",
    "Arturo",
    "Beatriz",
    "Carlos",
    "Claudia",
    "Daniel",
    "Diana",
    "Eduardo",
    "Elena",
    "Fernando",
    "Gabriela",
    "Héctor",
    "Isabel",
    "Javier",
    "Laura",
    "Luis",
    "Mariana",
    "Miguel",
    "Natalia",
    "Óscar",
    "Patricia",
    "Raúl",
    "Sofía",
    "Valeria",
)

LAST_NAMES = (
    "Aguilar",
    "Álvarez",
    "Castillo",
    "Chávez",
    "Cortés",
    "Delgado",
    "Domínguez",
    "Flores",
    "García",
    "Gómez",
    "González",
    "Hernández",
    "Jiménez",
    "López",
    "Martínez",
    "Mendoza",
    "Morales",
    "Navarro",
    "Ortega",
    "Ramírez",
    "Reyes",
    "Rivera",
    "Rodríguez",
    "Sánchez",
    "Torres",
    "Vargas",
)

DIRECTORATES = (
    "Administración y Finanzas",
    "Asuntos Jurídicos",
    "Capital Humano",
    "Comunicación",
    "Desarrollo Social",
    "Operaciones",
    "Planeación",
    "Servicios Públicos",
    "Tecnologías de Información",
)

COORDINATION_AREAS = (
    "Administración",
    "Atención Ciudadana",
    "Calidad",
    "Compras",
    "Control de Gestión",
    "Desarrollo Institucional",
    "Enlace Operativo",
    "Evaluación",
    "Normatividad",
    "Proyectos",
)

ADMIN_ROLES = (
    "Analista Administrativo",
    "Asistente de Área",
    "Auxiliar Administrativo",
    "Capturista",
    "Enlace Administrativo",
    "Especialista Técnico",
    "Gestor de Servicios",
    "Secretaria Ejecutiva",
    "Técnico Administrativo",
)


def _person_names(rng: random.Random, count: int) -> list[str]:
    combinations = [
        f"{first} {last}"
        for first in FIRST_NAMES
        for last in LAST_NAMES
    ]
    rng.shuffle(combinations)
    return combinations[:count]


def build_performance_document(seed: int = DEFAULT_SEED) -> OrgGridDocument:
    """Build the same connected 300-node hierarchy for every given seed."""
    rng = random.Random(seed)
    names = iter(_person_names(rng, 300))
    nodes: dict[str, OrgNode] = {}
    connections: list[Connection] = []
    connection_number = 0

    def add_node(
        node_id: str,
        role: str,
        grid_x: int,
        grid_y: int,
        color: str,
    ) -> str:
        nodes[node_id] = OrgNode(
            id=node_id,
            name=next(names),
            role=role,
            grid_x=grid_x,
            grid_y=grid_y,
            color=color,
        )
        return node_id

    def connect(source_id: str, target_id: str) -> None:
        nonlocal connection_number
        connection_number += 1
        connections.append(
            Connection(
                id=f"connection-{connection_number:04d}",
                source_id=source_id,
                target_id=target_id,
                source_port="bottom",
                target_port="top",
            )
        )

    coordinator_spacing = 12
    coordinator_count = 45
    secretary_x = ((coordinator_count - 1) * coordinator_spacing) // 2
    secretary_id = add_node(
        "secretary-001",
        "Secretario General",
        secretary_x,
        0,
        PRIMARY_BLUE,
    )

    coordinator_number = 0
    administrator_number = 0
    for director_number, directorate in enumerate(DIRECTORATES, start=1):
        first_coordinator = coordinator_number
        director_x = (first_coordinator + 2) * coordinator_spacing
        director_id = add_node(
            f"director-{director_number:03d}",
            f"Director de {directorate}",
            director_x,
            4,
            SECONDARY_BLUE,
        )
        connect(secretary_id, director_id)

        for area_offset in range(5):
            coordinator_number += 1
            coordinator_x = (coordinator_number - 1) * coordinator_spacing
            area = COORDINATION_AREAS[
                (director_number * 3 + area_offset) % len(COORDINATION_AREAS)
            ]
            coordinator_id = add_node(
                f"coordinator-{coordinator_number:03d}",
                f"Coordinador de {area}",
                coordinator_x,
                8,
                LIGHT_BLUE,
            )
            connect(director_id, coordinator_id)

            child_count = 6 if coordinator_number <= 20 else 5
            child_offsets = (-5, -3, -1, 1, 3, 5)[:child_count]
            for child_offset in child_offsets:
                administrator_number += 1
                role = ADMIN_ROLES[rng.randrange(len(ADMIN_ROLES))]
                administrator_id = add_node(
                    f"administrator-{administrator_number:03d}",
                    role,
                    coordinator_x + child_offset,
                    12,
                    NEUTRAL_GRAY,
                )
                connect(coordinator_id, administrator_id)

    document = OrgGridDocument(
        title="Organigrama de prueba de rendimiento (300 personas)",
        period="Datos sintéticos deterministas",
        page_orientation="horizontal",
        show_logos=False,
        nodes=nodes,
        connections=connections,
    )
    assert len(document.nodes) == 300
    assert len(document.connections) == 299
    return document


def generate(output: Path = DEFAULT_OUTPUT, seed: int = DEFAULT_SEED) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    return PersistenceManager().save(build_performance_document(seed), output)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera un proyecto .og conectado con 300 personas sintéticas."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    args = parser.parse_args()
    output = generate(args.output, args.seed)
    print(f"Proyecto generado: {output.resolve()}")


if __name__ == "__main__":
    main()
