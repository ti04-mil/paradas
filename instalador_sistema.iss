[Setup]
AppName=Sistema de Paradas dos Teares
AppVersion=1.0.0
AppPublisher=Malharia Indaial
DefaultDirName={autopf}\SistemaParadas
DefaultGroupName=Sistema de Paradas
DisableProgramGroupPage=yes
OutputDir=.
OutputBaseFilename=Instalador_Sistema_Paradas
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Languages]
Name: "portuguesebrazil"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na Area de Trabalho"; GroupDescription: "Atalhos:"
Name: "runsetup"; Description: "Executar instalacao do ambiente (.venv e dependencias)"; Flags: checkedonce

[Files]
Source: "app.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "requirements.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "monitorar_app.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "instalar_servidor.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "Imagens\*"; DestDir: "{app}\Imagens"; Flags: ignoreversion recursesubdirs createallsubdirs
; Nao incluir bancos locais no instalador:
; Paradas.db e database.db ficam fora do pacote.

[Icons]
Name: "{autoprograms}\Sistema de Paradas"; Filename: "{app}\monitorar_app.bat"; WorkingDir: "{app}"
Name: "{autodesktop}\Sistema de Paradas"; Filename: "{app}\monitorar_app.bat"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
Filename: "{app}\instalar_servidor.bat"; Description: "Preparar ambiente no servidor"; Flags: shellexec postinstall skipifsilent; Tasks: runsetup
Filename: "{app}\monitorar_app.bat"; Description: "Iniciar Sistema de Paradas"; Flags: shellexec postinstall skipifsilent

