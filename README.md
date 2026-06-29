# Suite Digital Fresnillo Web

Aplicacion web con frontend React y backend Python/FastAPI para apoyar flujos administrativos de la Presidencia Municipal de Fresnillo. La suite se ejecuta desde un servidor local por ahora y queda preparada para publicarse despues detras de un dominio, HTTPS y un proxy o plataforma cloud.

## Modulos Web

### Test Data

- Carga archivos PDF desde el navegador.
- Renderiza paginas del PDF como imagen.
- Permite dibujar recuadros de testado sobre la pagina.
- Captura clasificacion, concepto, fundamento y motivo.
- Exporta PDF testado reutilizando el motor existente de resumen y etiquetas.

### Organigrama

- Editor visual en canvas web.
- Crea nodos desde formulario o doble clic.
- Edita nombre, cargo y color del nodo seleccionado.
- Conecta dos nodos seleccionados.
- Exporta PDF usando el motor de renderizado institucional existente.

### Directorio

- Captura titulo, periodo, areas y colaboradores.
- Permite agregar multiples areas y personas.
- Genera PDF final del directorio.

### Conversor a PDF

- Sube archivos desde el navegador.
- Convierte imagenes, PDFs y documentos soportados por LibreOffice.
- Permite seleccionar paginas u hojas con formato como `1` o `2-4`.
- Descarga el PDF generado.

## Requisitos

- Python 3.12 o superior.
- Dependencias declaradas en `pyproject.toml`.
- Para convertir DOCX, XLSX, PPTX y otros documentos de oficina, conserva LibreOffice en `App_ConversorPDF/vendor/LibreOffice` o instala LibreOffice en el servidor.

Instalacion local:

```powershell
python -m pip install -e .
```

## Ejecutar en Servidor Local

Desde la raiz del proyecto:

```powershell
python main.py
```

La aplicacion escucha por defecto en:

```text
http://localhost:8000
```

Para que otros equipos de la misma red entren, usa la IP del equipo servidor:

```text
http://IP-DEL-SERVIDOR:8000
```

## Index Para Hosting

El proyecto incluye dos archivos de entrada:

- `web_app/static/index.html`: index React servido por FastAPI en `/`.
- `index.html`: index React en la raiz para hosts que piden un archivo de entrada.

Importante: la suite no puede funcionar completa en hosting estatico puro. El `index.html`
puede abrir, pero los modulos necesitan el backend Python/FastAPI para subir archivos,
renderizar PDFs, convertir documentos y generar descargas.

El frontend usa React desde import maps y carga la aplicacion modular en:

```text
web_app/static/js/app.js
```

Para publicarlo en nube, usa un host que ejecute Python/ASGI y apunte a:

```text
web_app.main:app
```

Variables de entorno disponibles:

```powershell
$env:SUITE_HOST="0.0.0.0"
$env:SUITE_PORT="8000"
$env:SUITE_RELOAD="true"
python main.py
```

## Preparacion Para Nube

La app ya expone un objeto ASGI en:

```text
web_app.main:app
```

Comando compatible con servidores o contenedores:

```powershell
uvicorn web_app.main:app --host 0.0.0.0 --port 8000
```

Para acceso externo se recomienda:

- Ejecutar Uvicorn/Gunicorn detras de Nginx, Caddy, IIS ARR o el proxy del proveedor cloud.
- Activar HTTPS en el proxy o balanceador.
- Montar almacenamiento persistente si se quieren conservar proyectos o historiales.
- Limitar tamano de subida de archivos desde el proxy.
- Ejecutar conversiones de documentos en un servidor con LibreOffice disponible.

## Apache

Se incluyen plantillas para publicar con Apache sin cambiar el codigo de la app:

- `deploy/apache/suite-digital-fresnillo.conf`: VirtualHost con Apache como proxy inverso hacia Uvicorn.
- `deploy/systemd/suite-digital-fresnillo.service`: servicio Linux para mantener Uvicorn encendido.
- `passenger_wsgi.py`: entrada para hosts Apache/Passenger o cPanel Python App que pidan WSGI.

La opcion mas estable es Apache como proxy inverso. Si el host es compartido y solo ofrece
Passenger/Python App, usa `passenger_wsgi.py`. Si el host solo acepta archivos estaticos,
el backend no podra procesar PDFs ni conversiones.

Guia completa:

```text
deploy/apache/README.md
```

## Estructura

```text
SuiteDigitalFresnilloWeb/
|-- main.py
|-- passenger_wsgi.py
|-- index.html
|-- web_app/
|   |-- main.py
|   |-- backend/
|   |   |-- app.py
|   |   |-- config.py
|   |   |-- runtime.py
|   |   |-- schemas.py
|   |   `-- routers/
|   `-- static/
|       |-- index.html
|       |-- styles.css
|       `-- js/
|           |-- app.js
|           |-- shared/
|           `-- modules/
|-- deploy/
|-- docs/
|-- App_TestData/
|-- App_Organigrama/
|-- App_Directorio/
|-- App_ConversorPDF/
|-- components/
`-- tests/
```

Las carpetas `App_*` y `components` permanecen porque el backend web reutiliza sus servicios,
exportadores, catalogos y assets. No son flujo ejecutable de escritorio en la app web; son
dependencias Python vivas hasta que esos servicios se migren por completo a `web_app/backend`.

## Pruebas

Compilar bytecode de la aplicacion web:

```powershell
python -m compileall -q main.py web_app
```

Ejecutar pruebas existentes:

```powershell
python -m pytest
```

Ejecutar analisis estatico:

```powershell
python -m ruff check .
```

## Notas

- La aplicacion ya no mantiene un flujo principal de escritorio ni configuracion de instalador EXE.
- Los paquetes antiguos de interfaz Tkinter permanecen en el repositorio solo como referencia y para seguir reutilizando servicios/dominio durante la migracion.
- Los archivos temporales de trabajo se guardan en la carpeta temporal del sistema bajo `suite-digital-fresnillo-web`.
