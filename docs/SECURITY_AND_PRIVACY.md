# Seguridad y privacidad

La suite procesa documentos potencialmente sensibles. La lógica propia funciona localmente y no incluye telemetría, sincronización ni envío de documentos a servicios web.

## Datos sensibles

- Un `.td` contiene el PDF original sin testar.
- `.og` y `.dir` pueden contener nombres, cargos y correos.
- `recent_files.json` revela rutas locales.
- Los snapshots de recuperación contienen estado del proyecto.

## Controles implementados

- Escritura atómica para reducir archivos parciales.
- SHA-256 del PDF incrustado en `.td`.
- Recuperaciones cifradas con DPAPI y ligadas al usuario Windows.
- Cancelación y terminación del árbol de procesos LibreOffice.
- Nombres alternativos en el Conversor para evitar sobrescritura.

## Límites

- `.td`, `.og`, `.dir` y PDFs finales no están cifrados por la aplicación.
- La suite no protege PDFs con contraseña.
- Un instalador sin Authenticode puede activar SmartScreen.
- La automatización no sustituye la revisión humana de una versión pública.
- El borrado de temporales no equivale a borrado forense seguro.

## Operación recomendada

1. Usar carpetas institucionales con permisos adecuados.
2. No enviar `.td` a quien solo necesita el PDF testado.
3. Revisar visualmente todas las páginas exportadas.
4. Verificar búsqueda, selección y copia en zonas testadas cuando el riesgo lo amerite.
5. Publicar el SHA-256 del instalador y firmarlo digitalmente.
6. Probar releases en una VM limpia.
7. Mantener dependencias y LibreOffice actualizados mediante una publicación controlada.

Un reporte de seguridad debe indicar versión, Windows, módulo, pasos mínimos e impacto. Las muestras deben anonimizarse.
