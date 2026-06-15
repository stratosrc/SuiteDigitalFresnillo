# QA Manual

Checklist minimo antes de entregar una version:

## Launcher

- Abrir el launcher desde `main.py`.
- Verificar que se muestren las apps disponibles con iconos.
- Abrir TestData, Organigrama y Directorio desde sus tarjetas.
- Cerrar cada app y confirmar que el launcher sigue respondiendo.

## TestData

- Crear un nuevo trabajo y cargar un PDF valido.
- Navegar entre paginas y verificar que los botones anterior/siguiente se deshabiliten en limites.
- Dibujar un recuadro, editarlo con doble clic y probar deshacer/rehacer.
- Guardar proyecto JSON, cerrar, volver a abrirlo y confirmar que PDF, pagina, zoom y recuadros se restauren.
- Exportar PDF estandar y confirmar que se genera el archivo.
- Exportar PDF para Comite con datos capturados y confirmar portada/resumen.

## Organigrama

- Crear nodos con clic en el canvas.
- Mover nodos arrastrando y comprobar que la barra contextual cambie de mensaje.
- Conectar dos nodos con clic derecho y verificar que la seleccion de conexion no tape nodos.
- Activar obstaculos de ruta y confirmar que las conexiones se enruten alrededor.
- Guardar proyecto, abrirlo de nuevo y confirmar nodos/conexiones.
- Exportar PDF horizontal y vertical.
- Exportar imagen PNG.

## Directorio

- Capturar titulo, periodo, areas y personas.
- Reordenar areas y personas con los botones de flecha.
- Intentar exportar con una fecha vacia o invalida y confirmar que la vista previa lo advierta.
- Corregir fechas y exportar PDF.
- Crear un nuevo proyecto y confirmar que el formulario se limpia.
