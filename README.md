# Suite Digital Fresnillo

Suite de escritorio en Python para apoyar flujos administrativos de la Presidencia Municipal de Fresnillo. La aplicacion principal abre un launcher con modulos independientes para testado de documentos, organigramas, directorios institucionales y conversion de archivos a PDF.

## Modulos

### Test Data

Modulo para trabajar con versiones publicas de documentos PDF.

- Carga archivos PDF.
- Permite dibujar recuadros de testado sobre paginas.
- Registra conceptos y metadatos por recuadro.
- Incluye deshacer, rehacer y eliminacion de recuadros.
- Guarda y abre proyectos de trabajo en progreso con extension `.td`.
- Exporta PDF testado y PDF para Comite con portada/resumen.

### Organigrama

Modulo para disenar organigramas institucionales en un canvas.

- Crea nodos con clic en el lienzo.
- Edita datos de cada nodo con doble clic.
- Mueve nodos con clic derecho y arrastre.
- Desplaza la camara con clic derecho y arrastre sobre espacio vacio.
- Crea conexiones con clic izquierdo o arrastrando desde indicadores de conexion.
- Permite agregar obstaculos de ruta para modificar el recorrido de conexiones.
- Guarda y abre proyectos editables con extension `.og`.
- Exporta PDF e imagen.

### Directorio

Modulo para generar directorios de area en PDF.

- Captura titulo, periodo, areas y colaboradores.
- Guarda y abre proyectos editables con extension `.dir`.
- Cada colaborador incluye rango/clave/nivel, nombre, cargo, correo electronico y fecha de alta.
- Permite reordenar areas y filas de colaboradores.
- Mantiene una fila minima por area.
- Valida que las fechas mantengan formato `dd/mm/aaaa`.
- Muestra vista previa/resumen antes de guardar el PDF.
- Genera PDF final con la informacion capturada.

### Conversor a PDF

Modulo para convertir varios tipos de archivo a PDF.

- Convierte imagenes: `jpg`, `jpeg`, `png`, `webp`, `bmp`, `gif`, `tif`, `tiff`.
- Convierte documentos: `doc`, `docx`, `rtf`, `odt`, `xls`, `xlsx`, `ods`, `csv`, `ppt`, `pptx`, `odp`.
- Permite cargar PDFs existentes para extraer paginas.
- Permite seleccionar paginas u hojas con formato como `1` o `2-4`; si se deja vacio convierte todo.
- Descarga todos los archivos listados o un archivo individual.
- Usa LibreOffice incluido dentro del proyecto cuando existe en `App_ConversorPDF/vendor/libreoffice` o `App_ConversorPDF/vendor/LibreOffice`.

## Estructura

```text
SuiteDigitalFresnillo/
|-- main.py
|-- convertidor.spec
|-- QA.md
|-- App_TestData/
|-- App_Organigrama/
|-- App_Directorio/
|-- App_ConversorPDF/
|-- components/
`-- tests/
```

### Arquitectura interna

- `components/shared/` contiene infraestructura reutilizable de ventanas, imágenes, tooltips, barras superiores y diálogos de ayuda.
- Cada aplicación separa configuración, modelos o dominio, servicios y componentes de interfaz.
- `App_Organigrama/ui/canvas.py` compone el lienzo. Los controladores `canvas_node_controller.py`, `canvas_connection_controller.py`, `canvas_viewport_controller.py` y `canvas_interaction_controller.py` separan nodos, conexiones, viewport e interacción.
- `components/shared/project_lifecycle.py` centraliza cambios sin guardar, escritura atómica y archivos recientes.
- `App_ConversorPDF/services/output_planner.py` interpreta hojas o páginas y construye el plan de archivos de salida sin depender de la interfaz.
- Los proyectos nuevos de Organigrama guardan campos internos en inglés con esquema 3; el cargador mantiene compatibilidad con proyectos anteriores.

## Requisitos de Desarrollo

- Windows recomendado.
- Python 3.12 o superior.
- Dependencias Python usadas por la suite:
  - `customtkinter`
  - `Pillow`
  - `PyMuPDF` (`fitz`)
  - `reportlab`
  - `tkinterdnd2`
  - `pyinstaller` para compilar

Instalacion sugerida:

```powershell
python -m pip install customtkinter pillow pymupdf reportlab tkinterdnd2 pyinstaller
```

Tkinter viene incluido normalmente con Python en Windows.

## Ejecutar en Desarrollo

Desde la raiz del proyecto:

```powershell
python main.py
```

Tambien se puede abrir un modulo especifico:

```powershell
python main.py --app testdata
python main.py --app organigrama
python main.py --app directorio
python main.py --app conversor_pdf
```

## LibreOffice Interno

El Conversor a PDF busca LibreOffice en este orden:

1. Copia incluida en desarrollo: `App_ConversorPDF/vendor/libreoffice/program/soffice.exe`
2. Variante con mayusculas: `App_ConversorPDF/vendor/LibreOffice/program/soffice.exe`
3. Copia incluida junto al ejecutable compilado.
4. Copia dentro de `_internal/vendor/libreoffice/program/soffice.exe`.
5. Instalaciones del sistema en `C:/Program Files/LibreOffice` y `C:/Program Files (x86)/LibreOffice`.

Para distribuir la app sin pedir instalacion manual de LibreOffice, conserva la carpeta completa de LibreOffice dentro de `App_ConversorPDF/vendor/LibreOffice` o `App_ConversorPDF/vendor/libreoffice`. No copies solamente `soffice.exe`; LibreOffice necesita su estructura interna.

## Pruebas

Ejecutar todas las pruebas:

```powershell
python -m unittest discover -s tests -v
```

Ejecutar análisis estático:

```powershell
python -m ruff check .
```

Compilar bytecode de los modulos principales:

```powershell
python -m compileall -q App_TestData App_Organigrama App_Directorio App_ConversorPDF components
```

Checklist manual:

```text
QA.md
```

## Compilar a EXE

El proyecto incluye `convertidor.spec`, configurado para generar una distribucion `onedir` con nombre `SuiteFresnillo`.

Comando recomendado:

```powershell
python -m PyInstaller --clean --noconfirm convertidor.spec
```

Salida esperada:

```text
dist/
`-- SuiteFresnillo/
    `-- SuiteFresnillo.exe
```

Ejecutar el compilado:

```powershell
.\dist\SuiteFresnillo\SuiteFresnillo.exe
```

## Probar en una Computadora sin LibreOffice

1. Compila con `python -m PyInstaller --clean --noconfirm convertidor.spec`.
2. Copia la carpeta completa `dist/SuiteFresnillo` a una computadora sin LibreOffice instalado.
3. Ejecuta `SuiteFresnillo.exe`.
4. Abre `Conversor a PDF`.
5. Convierte un archivo `docx`, `xlsx` o `pptx`.
6. Confirma que el PDF se genera sin instalar LibreOffice manualmente.

## Crear y validar el instalador

Después de compilar con PyInstaller, instala Inno Setup 6 y ejecuta:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\SuiteFresnillo.iss
```

El instalador se genera en `installer_output`. La prueba final debe hacerse en una
máquina virtual limpia de Windows 10/11 que no tenga Python ni LibreOffice:

1. Crear un punto de control de la VM limpia.
2. Copiar únicamente el instalador generado.
3. Instalar, abrir desde el menú Inicio y comprobar los cuatro módulos.
4. Convertir DOCX, XLSX y PPTX para verificar el LibreOffice incluido.
5. Guardar/recuperar proyectos `.td`, `.og` y `.dir`.
6. Desinstalar y confirmar que no queden procesos ni accesos directos.
7. Restaurar el punto de control antes de repetir la prueba.

## Notas de Uso

- En Directorio, la fecha se considera valida si respeta el formato `dd/mm/aaaa`.
- TestData guarda proyectos portátiles como `.td`, incluyendo el PDF original dentro del archivo. Organigrama usa `.og` y Directorio `.dir`; los proyectos JSON anteriores de TestData y Organigrama se conservan como compatibilidad de apertura.
- En Conversor a PDF, las selecciones aceptan valores como `1`, `2-4` o vacío. Para Excel, Calc, ODS y CSV los números representan pestañas completas del libro; para PDF, documentos y presentaciones representan páginas.
- Si un PDF de salida ya existe, el conversor crea un nombre unico para evitar sobrescritura accidental.
- El proyecto usa rutas relativas y `pathlib.Path` para funcionar en desarrollo y en compilado.

## Mantenimiento

- Mantener assets dentro de la carpeta de cada modulo o en `components/assets`.
- Evitar mover LibreOffice fuera de `App_ConversorPDF/vendor` sin actualizar `convertidor.spec` y el resolvedor de rutas.
- Al modificar interacciones visuales, actualizar tambien los cuadros de ayuda.
- Al agregar campos al Directorio, actualizar modelo, formulario, exportador PDF y pruebas si aplica.
- GitHub Actions ejecuta pruebas, compilación y Ruff mediante `.github/workflows/quality.yml`.
