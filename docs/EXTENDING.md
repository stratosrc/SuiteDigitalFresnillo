# Extender la suite

## Nueva aplicación

1. Crear `App_Nueva/` con `application.py`, `__init__.py`, `__main__.py`, `config`, modelos/dominio, servicios, UI y assets.
2. Exponer `main()` sin argumentos.
3. Añadir `ApplicationDefinition` a `components/shared/app_registry.py`.
4. Agregar el paquete a `hiddenimports` y assets a `datas` en `convertidor.spec` porque el registro importa dinámicamente.
5. Probar launcher, ejecución directa y compilada.
6. Actualizar README, arquitectura, guía, QA y changelog.

## Nuevo campo persistente

Actualizar modelo, serialización, defaults/migración, UI, exportador, pruebas de round-trip y [DATA_FORMATS.md](DATA_FORMATS.md). Incrementar versión si no hay compatibilidad.

## Nuevo concepto Test Data

Revisar catálogo, `RectangleData`, texto legal, edición, `ConceptDialog`, resúmenes, persistencia y pruebas de numeración/rotación.

## Nuevo formato del Conversor

Registrar extensión, elegir estrategia en `PdfConverter`, definir páginas/hojas, actualizar planificador, cancelación, pruebas, ayuda y dependencias PyInstaller.

## Cambios por módulo

- Organigrama: geometría en `rendering`/`routing`/helpers; eventos en controladores; dibujo en `canvas_drawing.py`.
- Directorio: campos en modelo/fila/persistencia/PDF; áreas en `area_section.py`; coordinación en `directory_editor.py`.
- Test Data: reglas puras en `domain`, PDF en `services`, eventos en `ui/interactions`.

Separar archivos cuando mezclen razones de cambio, capas o dependencias; no solo por líneas. Conservar fachadas pequeñas si estabilizan imports.

## Definition of Done

- [ ] Capa y responsabilidad correctas.
- [ ] Tipos, errores y cancelación adecuados.
- [ ] Escritura atómica cuando corresponda.
- [ ] Pruebas y QA visual.
- [ ] Ruff, compileall y pytest.
- [ ] Documentación/changelog.
- [ ] EXE e instalador si es publicación.
