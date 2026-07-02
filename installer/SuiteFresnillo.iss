#define AppName "Suite Digital Fresnillo"
#define AppVersion "1.1.0"
#define AppPublisher "Municipio de Fresnillo"
#define AppExeName "SuiteFresnillo.exe"

[Setup]
AppId={{C9AB84CA-BC2A-4551-9222-7D99C5106787}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Suite Digital Fresnillo
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=SuiteDigitalFresnillo-Setup-{#AppVersion}
SetupIconFile=..\components\assets\SuiteIcon.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\SuiteFresnillo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent

[Code]
var
  RequirementsPage: TOutputMsgMemoWizardPage;

procedure InitializeWizard;
var
  RequirementsText: String;
begin
  RequirementsText :=
    'Sistema operativo:' + #13#10 +
    '  - Windows 10 o Windows 11 de 64 bits' + #13#10 +
    '  - En Windows XP, Vista, 7, 8 y 8.1 la aplicacion no esta soportada y podria no funcionar correctamente' + #13#10 + #13#10 +
    'Hardware minimo:' + #13#10 +
    '  - Procesador compatible con x64' + #13#10 +
    '  - 4 GB de memoria RAM' + #13#10 +
    '  - 500 MB de espacio libre durante la instalacion' + #13#10 +
    '  - Pantalla con resolucion de 1280 x 720 o superior' + #13#10 + #13#10 +
    'Dependencias:' + #13#10 +
    '  - No es necesario instalar Python' + #13#10 +
    '  - Todos los componentes requeridos vienen incluidos' + #13#10 + #13#10 +
    'Se requieren permisos de administrador para instalar la aplicacion.';

  RequirementsPage := CreateOutputMsgMemoPage(
    wpWelcome,
    'Requerimientos minimos',
    'Antes de instalar {#AppName}',
    'Comprueba que este equipo cumpla con los siguientes requisitos:',
    RequirementsText
  );
end;
