# Formatos de datos y migraciones

Especificación de los formatos persistentes de Suite Digital Fresnillo 1.1.3. Los proyectos deben escribirse mediante sus servicios; antes de editarlos manualmente debe conservarse una copia.

## Test Data (`.td`)

El formato actual es un ZIP con versión `2`:

```text
proyecto.td
|-- project.json
`-- source.pdf
```

`project.json`:

```json
{
  "app": "testdata",
  "version": 2,
  "pdf_name": "original.pdf",
  "pdf_sha256": "SHA256_HEXADECIMAL",
  "current_page": 0,
  "current_zoom": 1.0,
  "rectangles": [],
  "reserved_history": [],
  "confidential_history": [],
  "other_law_history": [],
  "committee_data": {}
}
```

Cada rectángulo puede contener `id`, `order`, `page`, `x1`, `y1`, `x2`, `y2`, `classification`, `concept_id`, `category`, `concept_name`, `rows`, `paragraphs`, `legal_basis`, `reason`, `object`, `articles`, `law`, `custom_text`, `description`, `label`, `display_text`, `rect_tag` y `final_number`. `page` es un índice basado en cero y las coordenadas pertenecen al espacio PDF. Los IDs de Tk y el objeto `fitz.Rect` son transitorios.

El texto libre se guarda en `custom_text`. La exportación asigna `P.1`, `P.2`, etc.; el usuario no debe escribir el prefijo.

Al abrir se comprueba la presencia de ambos miembros, `app`, `version` y SHA-256 del PDF. La versión legado `1` era JSON y dependía de `pdf_path`; solo abre si el PDF original sigue disponible.

## Organigrama (`.og`)

El escritor actual usa `schema_version: 4`:

```json
{
  "app": "organigrama",
  "schema_version": 4,
  "document": {
    "title": "ORGANIGRAMA",
    "period": "2024-2027",
    "page_orientation": "horizontal",
    "show_logos": true,
    "nodes": {
      "id-nodo": {
        "name": "NOMBRE",
        "role": "CARGO",
        "grid_x": 4,
        "grid_y": 2,
        "color": "#005A9C",
        "id": "id-nodo"
      }
    },
    "connections": [{
      "source_id": "id-origen",
      "target_id": "id-destino",
      "source_port": "bottom",
      "target_port": "top",
      "kind": "direct",
      "manual_points": [],
      "id": "id-conexion"
    }]
  }
}
```

Una celda no puede contener dos nodos. Una conexión referencia nodos existentes. `manual_points` vacío activa enrutamiento automático; sus valores usan coordenadas de cuadrícula. El lector acepta documentos antiguos sin envoltura `document` y migra `nombre`/`cargo` a `name`/`role`.

## Directorio (`.dir`)

La versión `1` se valida estrictamente:

```json
{
  "app": "directorio",
  "version": 1,
  "directory": {
    "title": "UNIDAD",
    "period": "ENERO - MARZO 2026",
    "areas": [{
      "name": "ÁREA",
      "personnel": [{
        "rank": "1",
        "name": "NOMBRE",
        "position": "CARGO",
        "email": "correo@fresnillo.gob.mx",
        "start_date": "01/01/2026"
      }]
    }]
  }
}
```

Los campos son cadenas; las fechas válidas usan `dd/mm/aaaa`. Las filas completamente vacías no forman parte del reporte final.

## Datos auxiliares

```text
%LOCALAPPDATA%\SuiteDigitalFresnillo\
|-- recent_files.json
`-- recovery\<app>\recovery.bin
```

Se conservan hasta ocho rutas recientes por módulo. El autosave se evalúa cada 20 segundos y cifra el snapshot mediante Windows DPAPI para el usuario actual.

## Regla de migración

Al cambiar un formato: incrementar versión/esquema, conservar lector anterior cuando sea viable, aplicar defaults en persistencia, agregar pruebas de round-trip/migración, actualizar este documento y registrar el cambio en `CHANGELOG.md`.
