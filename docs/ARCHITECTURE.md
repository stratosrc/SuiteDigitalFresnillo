# Arquitectura

Suite Digital Fresnillo es una aplicación de escritorio modular construida con Python, Tkinter y CustomTkinter. `main.py` resuelve el módulo solicitado o abre el launcher.

## Capas

- **Configuración**: textos, rutas de recursos y constantes visuales.
- **Dominio/modelos**: estado serializable y reglas independientes de la interfaz.
- **Servicios**: persistencia, exportación, conversión y procesamiento de PDFs.
- **UI**: ventanas, diálogos, composición visual y controladores de interacción.
- **Componentes compartidos**: ciclo de vida de proyectos, escritura atómica, accesibilidad, imágenes, atajos y barras superiores.

## Módulos

### App_TestData

El dominio de rectángulos y textos legales está separado de la persistencia y la exportación PDF. La interfaz delega navegación, edición de rectángulos y exportación en controladores especializados.

### App_Organigrama

El lienzo compone controladores independientes para nodos, conexiones, viewport e interacción. `workspace_controller.py` construye y coordina la ventana; `workspace_project.py` administra apertura, guardado, exportación, historial, recuperación y tareas de fondo.

### App_Directorio

El formulario está dividido en:

- `field_helpers.py`: validación y normalización de campos.
- `personnel_row.py`: fila reutilizable de una persona.
- `area_section.py`: área expandible con filas virtualizadas.
- `directory_editor.py`: composición del formulario completo.
- `directory_form.py`: entrada pública compatible.

### App_ConversorPDF

Los servicios interpretan rangos, convierten archivos y administran LibreOffice. La UI está dividida en:

- `conversion_workspace.py`: estado y coordinación principal.
- `workspace_layout.py`: construcción visual.
- `conversion_workflow.py`: selección y conversión de archivos.
- `merge_workflow.py`: combinación y ordenamiento de PDFs.
- `background_tasks.py`: ejecución y cancelación en segundo plano.
- `workspace_models.py`: estado de los archivos cargados.

## Datos y seguridad

Los proyectos se escriben de forma atómica para reducir el riesgo de corrupción. Test Data empaqueta el PDF original dentro de `.td`; Organigrama y Directorio usan `.og` y `.dir`. Los formatos anteriores compatibles se migran al abrirse.

LibreOffice se distribuye en `App_ConversorPDF/vendor/LibreOffice` y se incluye en el instalador. Su contenido es código de terceros y no debe mezclarse con módulos propios.
