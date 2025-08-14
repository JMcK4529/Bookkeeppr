[Setup]
AppName=Bookkeeppr
AppVersion=alpha-0.0.0
DefaultDirName={pf}\Bookkeeppr
DefaultGroupName=Bookkeeppr
OutputDir=..\dist
OutputBaseFilename=BookkeepprInstaller
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
SetupIconFile=..\assets\bookkeeppr.ico
WizardStyle=modern

[Files]
Source: "..\dist\Bookkeeppr.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Bookkeeppr"; Filename: "{app}\Bookkeeppr.exe"
Name: "{commondesktop}\Bookkeeppr"; Filename: "{app}\Bookkeeppr.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Run]
Filename: "{app}\Bookkeeppr.exe"; Description: "Launch Bookkeeppr"; Flags: nowait postinstall skipifsilent