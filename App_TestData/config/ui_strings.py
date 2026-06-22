"""Centralized Spanish strings used by the user-facing interface."""

APP_WINDOW_TITLE = "Test Data"

FILE_MENU_LABELS = {
    "button": "Archivo",
    "new_job": "Nuevo Proyecto",
    "open_project": "Abrir Proyecto",
    "save_project": "Guardar proyecto",
    "export_pdf": "Exportar PDF",
}

TOPBAR_LABELS = {
    "catalogue": "Catálogo",
    "help": "Ayuda",
    "exit": "Salir",
}

HEADER_TITLE = "Módulo de Test Data y Versiones Públicas"

ACTION_LABELS = {
    "undo": "Deshacer",
    "redo": "Rehacer",
    "delete": "Eliminar",
}

CONTENT_LABELS = {
    "empty_state": "Sin PDF cargado. Usa Nuevo (Ctrl+N) para elegir un documento o abre un proyecto con Ctrl+O.",
}

NAVIGATION_LABELS = {
    "page": "Página",
    "total_pages": "de {total_pages}",
    "go": "Ir",
    "zoom": "Zoom",
}

HELP_DIALOG = {
    "title": "Ayuda",
    "heading": "Guía de uso",
    "close": "Cerrar",
    "sections": [
        (
            "1. ACCIONES PRINCIPALES",
            [
                "Deshacer: Permite revertir la última acción realizada.",
                "Rehacer: Se utiliza para rehacer una acción antes deshecha.",
                "Eliminar recuadro: Elimina el cuadro de testado seleccionado actual.",
                "Salir: Cierra de forma segura la aplicación.",
            ],
        ),
        (
            "2. NAVEGACIÓN Y ZOOM DEL PDF",
            [
                "Botón [<]: Retrocede una página en el documento.",
                "Botón [>]: Adelanta una página en el documento.",
                "Entrada de Página (Input): Permite escribir y elegir una página exacta para ir directamente a ella sin buscarla manualmente.",
                "Botones [+] y [-]: Controlan el nivel de zoom para acercar o alejar la observación del PDF.",
            ],
        ),
        (
            "3. HERRAMIENTAS DE TESTADO",
            [
                "Testar un dato: Simplemente haz clic izquierdo y arrastra el cursor sobre el texto que deseas testar.",
                "Barra de buscar: Sirve para encontrar un elemento predeterminado dentro del catálogo.",
                "Información Reservada: Clasifica y testa un dato bajo el fundamento de información reservada.",
                "Confidencial: Clasifica y testa un dato por contener información confidencial.",
                "Otra Ley: Permite enlistar y capturar una ley extra de justificación legal que no venga contemplada por defecto en la Ley de Transparencia y Acceso a la Información Pública del Estado de Zacatecas.",
                "Campos de Renglones y Párrafos: Espacios numéricos para determinar con precisión la cantidad de renglones y párrafos testados en el bloque actual.",
            ],
        ),
        (
            "4. MANIPULACIÓN DE RECUADROS (EDICIÓN EN VIVO)",
            [
                "Mover y Reposicionar: Puedes arrastrar cualquier recuadro con el clic izquierdo para cambiar su ubicación.",
                "Cambiar Tamaño: Haz clic y arrastra desde las esquinas de un recuadro para ajustar sus dimensiones de forma dinámica.",
                "Atajos de Teclado: También puedes eliminar un recuadro seleccionado presionando la tecla [Supr] (Delete) o [Backspace] en tu teclado.",
            ],
        ),
    ],
}

CATALOGUE_DIALOG = {
    "title": "Catálogo de Conceptos",
    "close": "Cerrar",
}

EXPORT_DIALOG = {
    "title": "Exportar PDF",
    "tabs": {
        "area": "Versión pública de área generadora",
        "committee": "Versión pública del Comité de Transparencia",
    },
    "buttons": {
        "standard": "Generar PDF estándar",
        "committee": "Generar PDF para Comité",
    },
    "committee_fields": [
        ("Fecha", "date"),
        ("Área", "department"),
        ("Documento", "document"),
        ("Período de reserva", "reservation_period"),
        ("Fundamento legal confidencial", "confidential_legal_basis"),
        ("Fundamento legal reservada", "reserved_legal_basis"),
        ("Nombre del titular de área", "area_owner_name"),
    ],
}

CONCEPT_DIALOG = {
    "title": "Configurar datos del rectángulo",
    "heading": "Configurar",
    "tabs": {
        "general": "General",
        "reserved": "Información Reservada",
        "confidential": "Información Confidencial",
        "other_law": "Otra Ley",
    },
    "buttons": {
        "cancel": "Cancelar",
        "accept": "Aceptar",
    },
    "general_fields": {
        "search": "Buscar Concepto:",
        "rows": "Renglones:",
        "paragraphs": "Párrafos:",
    },
    "classification_fields": {
        "legal_basis": "Fundamento legal",
        "reason": "En virtud tratarse de",
        "paragraphs": "Cantidad de párrafos",
        "rows": "Cantidad de renglones",
        "history": "Historial",
    },
    "other_law_fields": {
        "object": "Objeto",
        "articles": "Artículos",
        "law": "Ley",
        "paragraphs": "Cantidad de párrafos",
        "rows": "Cantidad de renglones",
        "history": "Historial",
    },
    "placeholders": {
        "object": "Ej: Sueldo Neto, Fotografía, Convenio...",
        "articles": "Ej: Artículo 45 Fracción II, Art. 12...",
        "law": "Ej: Ley de Disciplina Financiera...",
    },
    "warnings": {
        "selection_required_title": "Selección requerida",
        "selection_required_message": "Por favor selecciona un concepto de la lista.",
        "invalid_value_title": "Valor inválido",
        "general_integer_message": "Renglones y párrafos deben ser números enteros.",
        "general_range_message": "Renglones y párrafos están fuera del rango permitido.",
        "classification_integer_message": "Las cantidades deben ser números enteros.",
        "classification_range_message": "Las cantidades están fuera del rango permitido.",
    },
}

NAVIGATION_MESSAGES = {
    "pdf_required_title": "PDF requerido",
    "pdf_required_message": "Carga un PDF antes de navegar.",
    "invalid_page_title": "Página inválida",
    "invalid_page_message": "Introduce un número de página válido.",
    "page_out_of_range_title": "Página fuera de rango",
    "page_out_of_range_message": "La página debe estar entre 1 y {total_pages}.",
}

EXPORT_MESSAGES = {
    "pdf_required_title": "PDF requerido",
    "pdf_required_message": "Carga un PDF antes de generar el archivo.",
    "export_running_title": "Exportación en curso",
    "export_running_message": "Espera a que termine la generación actual antes de iniciar otra.",
    "no_changes_title": "Sin cambios",
    "no_changes_message": "Dibuja al menos un rectángulo antes de generar el PDF.",
    "save_dialog_title": "Exportar PDF",
    "save_dialog_filetypes_label": "Archivos PDF",
    "invalid_path_title": "Ruta inválida",
    "invalid_path_message": "Guarda el PDF generado con un nombre distinto al archivo original.",
    "generating_status": "Generando PDF...",
    "generated_status": "PDF generado: {output_path}",
    "generated_title": "PDF generado",
    "generated_message": "El PDF se generó correctamente.",
    "error_status": "Error al generar el PDF.",
    "error_title": "Error",
    "error_message": "No se pudo generar el PDF:\n{error}",
}

EXIT_MESSAGES = {
    "export_running_title": "Exportación en curso",
    "export_running_message": "Espera a que termine la generación de PDF antes de salir.",
    "confirm_title": "Confirmar salida",
    "confirm_message": "¿Estás seguro de que quieres salir?",
}

PDF_MANAGER_MESSAGES = {
    "load_dialog_title": "Seleccionar archivo PDF",
    "load_dialog_filetypes_label": "Archivos PDF",
    "missing_file_title": "Error",
    "missing_file_message": "El archivo no existe: {file_path}",
    "new_job_cancelled_status": "Nuevo trabajo cancelado.",
    "loaded_status": "PDF cargado correctamente.",
    "invalid_pdf_status": "Error: Archivo PDF inválido.",
    "invalid_pdf_title": "Error",
    "invalid_pdf_message": "El archivo no es un PDF válido.",
    "load_error_status": "Error al cargar el PDF.",
    "load_error_title": "Error",
    "load_error_message": "No se pudo cargar el PDF:\n{error}",
    "render_error_status": "Error al renderizar la página.",
    "render_error_title": "Error",
    "render_error_message": "No se pudo renderizar la página:\n{error}",
    "file_status": "Archivo: {file_name}",
}
