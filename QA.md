# QA Manual

Checklist minimo antes de entregar una version.

## Launcher

- Abrir el launcher desde `main.py`.
- Verificar que se muestren Test Data, Organigrama y Directorio con iconos.
- Abrir Test Data, Organigrama y Directorio desde sus tarjetas.
- Cerrar cada app y confirmar que el launcher sigue respondiendo.

## Test Data

- Crear un nuevo trabajo y cargar un PDF valido.
- Navegar entre paginas y verificar que los botones anterior/siguiente se deshabiliten en limites.
- Dibujar un recuadro, editarlo con doble clic y probar deshacer/rehacer.
- Guardar proyecto `.td`, cerrar, volver a abrirlo y confirmar que PDF, pagina, zoom y recuadros se restauren.
- Exportar PDF estandar y confirmar que se genera el archivo.
- Exportar PDF para Comite con datos capturados y confirmar portada/resumen.

## Organigrama

- Crear nodos con clic en el canvas.
- Mover nodos arrastrando y comprobar que la barra contextual cambie de mensaje.
- Conectar dos nodos con clic izquierdo desde el indicador de conexion y verificar que la seleccion no tape nodos.
- Seleccionar una conexion, mover un segmento y un punto de doblez, y comprobar los estados valido e invalido.
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

## Ciclo de Proyecto

- Modificar un proyecto y confirmar que el titulo de la ventana muestre `*`.
- Intentar crear, abrir o cerrar con cambios pendientes y verificar Guardar/Descartar/Cancelar.
- Guardar un proyecto, abrirlo desde `Archivos recientes` y confirmar su contenido.

## Instalador en Windows Limpio

- Ejecutar el instalador en una VM de Windows 10/11 sin Python.
- Confirmar que el ejecutable muestra icono y version `1.1.0`.
- Abrir los tres modulos desde el launcher.
- Guardar y recuperar proyectos `.td`, `.og` y `.dir`.
- Desinstalar y comprobar que se eliminen accesos directos y archivos instalados.

## Build en macOS

- Compilar con `python -m PyInstaller --clean --noconfirm suite_fresnillo.spec`.
- Confirmar que se genera `dist/SuiteFresnillo.app`.
- Abrir el `.app` en macOS 10.11 El Capitan y validar los tres modulos desde el launcher.
