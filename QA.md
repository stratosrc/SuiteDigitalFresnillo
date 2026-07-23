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
- Iniciar el dibujo, movimiento o redimensionado de un recuadro y cancelarlo con `Esc` y clic secundario.
- Exportar paginas con rotaciones 0, 90, 180 y 270 grados y confirmar que recuadros y etiquetas queden orientados correctamente.
- Guardar proyecto `.td`, cerrar, volver a abrirlo y confirmar que PDF, pagina, zoom y recuadros se restauren.
- Exportar PDF estandar y confirmar que se genera el archivo.
- Exportar PDF para Comite con datos capturados y confirmar portada/resumen.

## Organigrama

- Crear nodos con clic en el canvas.
- Confirmar que el selector de color muestre cuatro niveles jerarquicos en vertical y marque la opcion elegida con borde verde.
- Intentar conectar Personal Administrativo hacia Secretarios y verificar la advertencia de jerarquia inversa.
- Crear una conexion normal de Secretarios hacia un nivel inferior y confirmar que no aparezca la advertencia.
- Durante una conexion, llevar el cursor a cada borde del canvas y confirmar que la vista se desplace en esa direccion.
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
- Abrir `App_Directorio/samples/directorio_3_areas_900_registros.dir` y confirmar que contiene 3 areas de 300 personas.
- Confirmar que solo un area permanece abierta, el indicador muestra 12 filas visibles y la barra interna llega hasta la persona 300.
- Editar una persona, desplazarla fuera de la ventana visible, regresar y confirmar que el cambio se conserva.
- Cambiar entre las tres areas y confirmar que la interfaz sigue respondiendo sin crear controles para las 900 personas.
- Guardar proyecto `.dir`, cerrar, volver a abrirlo y confirmar que titulo, periodo, areas y personas se restauren.
- Reordenar areas y personas con los botones de flecha.
- Intentar exportar con una fecha vacia o invalida y confirmar que la vista previa lo advierta.
- Corregir fechas y exportar PDF.
- Crear un nuevo proyecto y confirmar que el formulario se limpia.

## Ciclo de proyecto

- Modificar un proyecto y confirmar que el título de la ventana muestre `*`.
- Intentar crear, abrir o cerrar con cambios pendientes y verificar Guardar/Descartar/Cancelar.
- Guardar un proyecto, abrirlo desde `Archivos recientes` y confirmar su contenido.

## Instalador en Windows limpio

- Ejecutar el instalador en una VM de Windows 10/11 sin Python ni LibreOffice.
- Confirmar que el ejecutable muestra icono y versión `1.0.0`.
- Abrir los cuatro módulos desde el launcher.
- Convertir DOCX, XLSX y PPTX usando únicamente LibreOffice incluido.
- Cancelar una conversión y comprobar que no queden procesos `soffice.exe`.
- Desinstalar y comprobar que se eliminen accesos directos y archivos instalados.
