#define AppName "Suite Digital Fresnillo"
#define AppVersion "1.1.0"
#define AppPublisher "Municipio de Fresnillo"
#define AppExeName "SuiteFresnillo.exe"
#define UCRTUpdateName "Windows8-RT-KB2999226-x64.msu"

[Setup]
AppId={{C9AB84CA-BC2A-4551-9222-7D99C5106787}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Suite Digital Fresnillo
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir=..\installer_output
OutputBaseFilename=SuiteDigitalFresnillo-Windows8-Setup-{#AppVersion}
SetupIconFile=..\components\assets\SuiteIcon.ico
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
MinVersion=6.2

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "..\dist\SuiteFresnillo\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "vendor\{#UCRTUpdateName}"; Flags: dontcopy

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Abrir {#AppName}"; Flags: nowait postinstall skipifsilent; Check: CanLaunchApplication

[Code]
var
  UCRTNeedsRestart: Boolean;
  UCRTWasInstalledBySetup: Boolean;

function IsWindows80: Boolean;
var
  Version: TWindowsVersion;
begin
  GetWindowsVersionEx(Version);
  Result := (Version.Major = 6) and (Version.Minor = 2);
end;

function UCRTIsInstalled: Boolean;
begin
  Result :=
    FileExists(ExpandConstant('{sys}\ucrtbase.dll')) and
    FileExists(ExpandConstant('{sys}\api-ms-win-crt-stdio-l1-1-0.dll'));
end;

procedure InstallWindows8UCRT;
var
  ResultCode: Integer;
begin
  if (not IsWindows80) or UCRTIsInstalled then
    Exit;

  UCRTWasInstalledBySetup := True;
  WizardForm.StatusLabel.Caption :=
    'Instalando Universal C Runtime para Windows 8...';
  ExtractTemporaryFile('{#UCRTUpdateName}');

  if not Exec(
    ExpandConstant('{sys}\wusa.exe'),
    '"' + ExpandConstant('{tmp}\{#UCRTUpdateName}') + '" /quiet /norestart',
    '',
    SW_HIDE,
    ewWaitUntilTerminated,
    ResultCode
  ) then
    RaiseException('No fue posible iniciar la actualizacion KB2999226.');

  if (ResultCode <> 0) and (ResultCode <> 3010) and
     (ResultCode <> 2359302) then
    RaiseException(
      'No se pudo instalar Universal C Runtime KB2999226. Codigo: ' +
      IntToStr(ResultCode) + '.'
    );

  UCRTNeedsRestart := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssInstall then
    InstallWindows8UCRT;
end;

function CanLaunchApplication: Boolean;
begin
  Result := not UCRTNeedsRestart;
end;

function NeedRestart(): Boolean;
begin
  Result := UCRTNeedsRestart;
end;

procedure InitializeWizard;
begin
  UCRTNeedsRestart := False;
  UCRTWasInstalledBySetup := False;
end;

procedure CurPageChanged(CurPageID: Integer);
begin
  if (CurPageID = wpFinished) and UCRTWasInstalledBySetup then
    WizardForm.FinishedLabel.Caption :=
      'La instalacion termino correctamente.' + #13#10 + #13#10 +
      'Debes reiniciar Windows antes de abrir Suite Digital Fresnillo.';
end;
