# Build para macOS 10.11 El Capitan

La meta legacy de la suite es macOS 10.11 El Capitan o superior, solo Intel `x86_64`.

## Requisitos recomendados

- Compilar con Python 3.10.11. Fue la ultima version 3.10 con instalador de macOS.
- Usar arquitectura `x86_64`.
- Exportar `MACOSX_DEPLOYMENT_TARGET=10.11`.
- Usar PyMuPDF 1.18.19; versiones modernas pueden incluir binarios que El Capitan no puede cargar o procesar.
- Probar el resultado en una Mac o VM con macOS 10.11.

## Comando base

```bash
MACOSX_DEPLOYMENT_TARGET=10.11 python -m PyInstaller --clean --noconfirm suite_fresnillo.spec
```

Evita Python 3.10.0 en El Capitan. Esa version puede fallar durante el analisis de PyInstaller con `IndexError: tuple index out of range`.

## Nota importante sobre PyInstaller

PyInstaller moderno puede ejecutarse en macOS 10.15 o superior, pero sus bootloaders precompilados normalmente apuntan a macOS 10.13 o superior. Para que el `.app` sea realmente compatible con El Capitan, compila o instala PyInstaller con bootloader propio usando `MACOSX_DEPLOYMENT_TARGET=10.11` antes de generar la app.

Si se usa el wheel normal de PyInstaller sin reconstruir el bootloader, el `Info.plist` dira 10.11, pero el ejecutable puede fallar en El Capitan.

## Validacion minima

1. Abrir `dist/SuiteFresnillo.app` en macOS 10.11.
2. Confirmar que el launcher muestra Test Data, Organigrama y Directorio.
3. Abrir y cerrar cada modulo.
4. Exportar un PDF desde Test Data, Organigrama y Directorio.
5. Guardar y abrir proyectos `.td`, `.og` y `.dir`.
