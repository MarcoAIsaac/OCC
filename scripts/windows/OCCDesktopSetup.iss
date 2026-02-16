#define AppName "OCC Desktop"
#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#ifndef ExeFile
  #error ExeFile define is required
#endif
#ifndef OutputDir
  #error OutputDir define is required
#endif
#ifndef SetupIconFile
  #error SetupIconFile define is required
#endif

[Setup]
AppId={{9F402AB0-A2D2-462A-9460-24ECFE62A36E}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher=OCC Project
AppPublisherURL=https://github.com/MarcoAIsaac/OCC
DefaultDirName={autopf}\OCC Desktop
DefaultGroupName=OCC Desktop
DisableProgramGroupPage=yes
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir={#OutputDir}
OutputBaseFilename=OCCDesktop-Setup-windows-x64
SetupIconFile={#SetupIconFile}
UninstallDisplayIcon={app}\OCCDesktop.exe
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "{#ExeFile}"; DestDir: "{app}"; DestName: "OCCDesktop.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\OCC Desktop"; Filename: "{app}\OCCDesktop.exe"
Name: "{autodesktop}\OCC Desktop"; Filename: "{app}\OCCDesktop.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\OCCDesktop.exe"; Description: "Launch OCC Desktop"; Flags: nowait postinstall skipifsilent
