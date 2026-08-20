# Rendimiento y capacidad

No hay límites rígidos: dependen del equipo, resolución y complejidad. Deben medirse escenarios reproducibles.

## Estrategias

- Directorio: una sección expandida, modelos separados de widgets y ventana virtual de 12 filas.
- Organigrama: cachés, culling, overlays separados y rutas recalculadas desde elementos afectados.
- Test Data: una página renderizada, coordenadas vectoriales, marca de agua reutilizada y calidad Compacta.
- Conversor: hilos, cancelación, planificación previa y procesos observados.

## Escenarios de referencia

| Módulo | Escenario |
|---|---|
| Test Data | PDF de 100 páginas, 100 rectángulos y ambas calidades. |
| Organigrama | `organigrama_rendimiento_300.og`. |
| Directorio | `directorio_3_areas_900_registros.dir`. |
| Conversor | Lote DOCX/XLSX/PPTX/PDF representativo. |

Registrar CPU, RAM, disco, Windows, versión, entrada, tiempo, memoria pico y tamaño final. Medir antes/después en el mismo equipo.

Se considera regresión: UI bloqueada en tareas asíncronas, widgets proporcionales a las 900 personas, redraw continuo, cachés omitidas, procesos `soffice.exe` huérfanos o pérdida repetible de reducción Compacta.

Optimización segura: reproducir, medir, cambiar una estrategia, ejecutar pruebas, medir de nuevo y revisar calidad visual. No sacrificar integridad de testado ni precisión geométrica.
