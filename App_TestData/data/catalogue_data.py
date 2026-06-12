CATALOGUE_SECTIONS = [
    (
        "Artículo 3, Sección X \nDatos Personales",
        [
            "Nombre", "Domicilio", "Correo electrónico", "Teléfono particular", "Teléfono celular", "Firma", "RFC",
            "CURP", "Clave de elector", "Matrícula de servicio militar nacional", "Número de pasaporte", "Lugar de nacimiento",
            "Nacionalidad", "Edad", "Fotografía", "Estado civil", "Número de seguro social", "Tránsito y datos migratorios",
            "Referencias personales", "Estatura", "Complexión", "Solicitud de empleo", "Documento de selección", "Documentos de reclutamiento",
            "Nombramiento", "Hoja de servicio", "Incidencias", "Capacitación", "Actividades extracurriculares", "Referencias", "Trayectoria educativa",
            "Calificaciones", "Títulos de particulares", "Certificados", "Reconocimientos", "Solicitud como aspirante", "Evaluaciones",
            "Bienes muebles", "Bienes inmuebles", "Régimen fiscal", "Obligaciones fiscales", "Firma electrónica", "Contraseña fiscal", "Historial crediticio",
            "Ingresos", "Egresos", "Cuenta bancaria", "Seguros", "Fianzas", "Servicios contratados", "la correspondiente a una persona relacionada con un procedimiento administrativo",
            "la correspondiente a una persona relacionada con un procedimiento laboral", "la correspondiente a una persona relacionada con un procedimiento civil", "la correspondiente a una persona relacionada con un procedimiento penal",
            "la correspondiente a una persona relacionada con un procedimiento fiscal", "la correspondiente a una persona relacionada con un procedimiento familiar", "la correspondiente a una persona relacionada con un procedimiento agrario",
            "la correspondiente a una persona relacionada con un procedimiento mercantil", "la correspondiente a una persona relacionada con un procedimiento administrativo con cualquier otra rama del derecho",
        ],
    ),
    (
        "Artículo 3, Sección X, Inciso a) \nDatos Personales Sensibles",
        [
            "Origen", "Etnia", "Raza", "Color de piel", "Color de ojos", "Color y tipo de cabello", "Ideología", "Creencias",
            "Opinión política", "Afiliación política", "Afiliación sindical", "Religión", "Convicción filosófica", "Información de la vida sexual", "Expediente clínico",
            "Referencias o descripción de sintomatologías", "Enfermedades", "Incapacidad médica", "Discapacidad", "Intervención quirúrgica",
            "Vacunas", "Consumo de estupefacientes", "Uso de aparatos oftalmológicos", "Uso de aparatos auditivos", "Uso de prótesis",
            "Estado físico", "Estado mental",
        ],
    ),
    (
        "Artículo 3, Sección X, Inciso b) \nDatos Personales Biométricos",
        [
            "Huella dactilar", "Reconocimiento facial", "Iris", "Retina", "Patrón vascular", "Código QR", "ADN", "Patrón de voz",
            "Geometría de la mano", "Firma biométrica", "Reconocimiento de escritura",
            "Forma de caminar", "Reconocimiento de oreja", "Biometría ocular",
        ],
    ),
]


def build_catalogue_items(catalogue_sections=CATALOGUE_SECTIONS):
    items = []
    current_id = 1
    for _, section_items in catalogue_sections:
        for item_name in section_items:
            items.append((current_id, item_name))
            current_id += 1
    return items


def build_catalogue_categories(catalogue_sections=CATALOGUE_SECTIONS):
    categories = {}
    current_id = 1
    for section_title, section_items in catalogue_sections:
        normalized_title = section_title.lower()
        if "biometric" in normalized_title or "inciso b" in normalized_title:
            category = "biometric"
        elif "sensible" in normalized_title or "inciso a" in normalized_title:
            category = "sensitive"
        else:
            category = "normal"

        for _ in section_items:
            categories[current_id] = category
            current_id += 1
    return categories
