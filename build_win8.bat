@echo off
setlocal
cd /d "%~dp0"

python -c "import sys; raise SystemExit(0 if sys.version_info[:2] == (3, 8) and sys.maxsize > 2**32 else 1)"
if errorlevel 1 (
    echo ERROR: Debes ejecutar este archivo con Python 3.8.10 de 64 bits.
    exit /b 1
)

if not exist ".venv-win8\Scripts\python.exe" (
    python -m venv .venv-win8
    if errorlevel 1 exit /b 1
)

call ".venv-win8\Scripts\activate.bat"

for /f "usebackq delims=" %%P in (`python -c "import sys; print(sys.base_prefix)"`) do set "PYTHON_BASE=%%P"
set "TCL_LIBRARY=%PYTHON_BASE%\tcl\tcl8.6"
set "TK_LIBRARY=%PYTHON_BASE%\tcl\tk8.6"

python -m pip install --upgrade pip==24.0 setuptools==68.2.2 wheel==0.42.0
if errorlevel 1 exit /b 1

python -m pip install ".[dev]"
if errorlevel 1 exit /b 1

python -m pytest
if errorlevel 1 exit /b 1

powershell -NoProfile -ExecutionPolicy Bypass -Command "$s = Get-AuthenticodeSignature 'installer\vendor\Windows8-RT-KB2999226-x64.msu'; if ($s.Status -ne 'Valid' -or $s.SignerCertificate.Subject -notmatch 'Microsoft') { exit 1 }"
if errorlevel 1 (
    echo ERROR: El paquete KB2999226 no tiene una firma valida de Microsoft.
    exit /b 1
)

python -m PyInstaller --clean --noconfirm convertidor.spec
if errorlevel 1 exit /b 1

set "ISCC=%ProgramFiles%\Inno Setup 7\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" (
    echo ERROR: Instala Inno Setup 6 o 7.
    exit /b 1
)

"%ISCC%" installer\SuiteFresnillo.iss
if errorlevel 1 exit /b 1

echo.
echo Instalador generado:
echo %CD%\installer_output\SuiteDigitalFresnillo-Windows8-Setup-1.1.0.exe
endlocal
