# Guía de usuario

## Antes de comenzar

La suite trabaja con archivos locales. Guarda proyectos con frecuencia y conserva por separado documentos originales y resultados. Los formatos y riesgos de datos sensibles se explican en [DATA_FORMATS.md](DATA_FORMATS.md) y [SECURITY_AND_PRIVACY.md](SECURITY_AND_PRIVACY.md).

## Instalación

1. Ejecuta `SuiteDigitalFresnillo-Setup-1.1.3.exe`.
2. Acepta la solicitud de permisos de administrador.
3. Conserva la ruta de instalación sugerida o elige otra.
4. Abre **Suite Digital Fresnillo** desde el menú Inicio o el acceso directo.

Python y LibreOffice ya están incluidos. Windows SmartScreen puede mostrar una advertencia si el instalador no cuenta con firma digital.

La ventana inicial permite abrir cada módulo. Al cerrar un módulo iniciado desde el launcher, este vuelve a mostrarse. Los atajos comunes son `Ctrl+N`, `Ctrl+O`, `Ctrl+S`, `Ctrl+Z` y `Ctrl+Y` cuando la operación está disponible.

## Test Data y versiones públicas

1. Abre un PDF o un proyecto `.td`.
2. Dibuja un rectángulo sobre el contenido que será testado.
3. Selecciona el concepto aplicable:
   - Datos generales.
   - Clasificación.
   - Otro fundamento.
   - Personalizado.
4. En **Personalizado**, escribe el texto exactamente como debe aparecer. El resumen lo enumera como `P.1`, `P.2`, etc.
5. Exporta el documento y elige la calidad:
   - **Estándar**: mantiene mayor resolución.
   - **Compacta**: reduce imágenes y optimiza el tamaño final.
6. Guarda el proyecto si deseas continuar después.

### Revisión de una versión pública

1. Recorre todas las páginas y confirma cada rectángulo.
2. Verifica la numeración final y el fundamento.
3. Comprueba páginas rotadas.
4. Abre el PDF exportado en un lector independiente.
5. Revisa visualmente y, cuando corresponda, intenta buscar/copiar texto testado.

Un `.td` contiene el PDF original y no debe entregarse como si fuera la versión pública.

## Organigrama

- Crea, edita, mueve y conecta nodos en el lienzo.
- Guarda el proyecto en formato `.og`.
- Exporta el resultado como PDF o imagen.
- Usa deshacer y rehacer para revertir cambios recientes.

Las conexiones automáticas usan rutas ortogonales. Si se mueven segmentos o dobleces se guardan puntos manuales; usa **Restablecer ruta** para volver al cálculo automático.

## Directorio

- Captura título, periodo, áreas y personal.
- Reordena áreas o personas desde sus menús de acciones.
- Las fechas deben usar el formato `dd/mm/aaaa`.
- Guarda proyectos `.dir` o exporta directamente a PDF.

Solo un área se mantiene expandida. Las filas visibles se reutilizan para conservar rendimiento; desplazarse no elimina información.

## Conversor a PDF

- Admite imágenes, documentos, hojas de cálculo, presentaciones y PDFs.
- Para páginas u hojas usa selecciones como `1`, `2-4` o deja el campo vacío para procesar todo.
- Puede separar resultados individuales o combinar varios PDFs.
- Si un nombre ya existe, crea una variante para evitar sobrescribirlo.

Para hojas de cálculo, los números representan pestañas; para documentos/PDF/presentaciones representan páginas. **Separar** crea una salida por elemento seleccionado. **Combinar PDFs** respeta el orden visible, que puede modificarse arrastrando.

## Recuperación y archivos recientes

Los módulos con proyectos registran hasta ocho rutas recientes. Si hay cambios sin guardar, el autosave puede ofrecer recuperación al siguiente inicio con el mismo usuario de Windows. La recuperación no sustituye un respaldo.

## Ayuda adicional

- Errores comunes: [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
- Plataformas y formatos: [COMPATIBILITY.md](COMPATIBILITY.md).
- Pruebas operativas: [QA.md](QA.md).
