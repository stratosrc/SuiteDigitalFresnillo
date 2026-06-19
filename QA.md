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
- Guardar proyecto `.td`, cerrar, volver a abrirlo y confirmar que PDF, pagina, zoom y recuadros se restauren.
- Exportar PDF estandar y confirmar que se genera el archivo.
- Exportar PDF para Comite con datos capturados y confirmar portada/resumen.

## Organigrama

- Crear nodos con clic en el canvas.
- Mover nodos arrastrando y comprobar que la barra contextual cambie de mensaje.
- Conectar dos nodos con clic izquierdo desde el indicador de conexión y verificar que la selección no tape nodos.
- Seleccionar una conexión, mover un segmento y un punto de doblez, y comprobar los ghosts válido e inválido.
- Probar deshacer y rehacer cambios del organigrama.
- Activar obstaculos de ruta y confirmar que las conexiones se enruten alrededor.
- Guardar proyecto `.og`, abrirlo de nuevo y confirmar nodos/conexiones.
- Exportar PDF horizontal y vertical.
- Exportar imagen PNG.

## Directorio

- Capturar titulo, periodo, areas y personas.
- Guardar proyecto `.dir`, cerrar, volver a abrirlo y confirmar que titulo, periodo, areas y personas se restauren.
- Reordenar areas y personas con los botones de flecha.
- Intentar exportar con una fecha vacia o invalida y confirmar que la vista previa lo advierta.
- Corregir fechas y exportar PDF.
- Crear un nuevo proyecto y confirmar que el formulario se limpia.

## Ciclo de proyecto

- Modificar un proyecto y confirmar que el título de la ventana muestre `*`.
- Intentar crear, abrir o cerrar con cambios pendientes y verificar Guardar/Descartar/Cancelar.
- Guardar un proyecto, abrirlo desde `Archivos recientes` y confirmar su contenido.
