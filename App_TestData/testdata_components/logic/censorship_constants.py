# Censorship Constants and Utilities

CENSORSHIP_TEMPLATE = (
    "{label} {concept_name} censurado por ser un dato personal de conformidad con "
    "el artículo 3, sección X de la Ley de Transparencia y Acceso a la Información Pública "
    "del Estado de Zacatecas ({paragraphs} párrafo{'s' if paragraphs != 1 else ''} "
    "{rows} renglón{'es' if rows != 1 else ''})."
)


def build_censorship_text(label_text, concept_name, rows, paragraphs):
    return (
        f"{label_text} {concept_name} censurado por ser un dato personal de conformidad con el "
        f"artículo 3, sección X de la Ley de Transparencia y Acceso a la Información Pública del "
        f"Estado de Zacatecas ({paragraphs} párrafo{'s' if paragraphs != 1 else ''} "
        f"{rows} renglón{'es' if rows != 1 else ''})."
    )
