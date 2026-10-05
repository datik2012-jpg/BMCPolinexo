#if VER != EncodeVer(6, 5, 4)
  #error Build with Inno Setup 6.5.4
#endif
#ifndef AppVersion
  #define AppVersion "1.2.1"
#endif
#ifndef BundleDir
  #error BundleDir is required
#endif
#ifndef OutputDirPath
  #error OutputDirPath is required
#endif

[Setup]
AppId={{CB22149E-7991-4D17-BA3B-A28AD790BA03}
AppName=BMCPolinexo
AppVersion={#AppVersion}
AppPublisher=BMC
DefaultDirName={localappdata}\Programs\BMCPolinexo
DefaultGroupName=BMCPolinexo
PrivilegesRequired=lowest
ArchitecturesAllowed=x64os
ArchitecturesInstallIn64BitMode=x64os
MinVersion=10.0
OutputDir={#OutputDirPath}
OutputBaseFilename=BMCPolinexo-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
AppMutex={code:SetupMutex}
CloseApplications=no
RestartApplications=no
UninstallDisplayIcon={app}\BMCPolinexo.exe
SetupLogging=no
DisableProgramGroupPage=yes

[Languages]
Name: "hebrew"; MessagesFile: "compiler:Languages\Hebrew.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{#BundleDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; This directory contains bundled runtime files only, never customer data.
Type: filesandordirs; Name: "{app}\_internal"

[Icons]
Name: "{group}\BMCPolinexo"; Filename: "{app}\BMCPolinexo.exe"
Name: "{userdesktop}\BMCPolinexo"; Filename: "{app}\BMCPolinexo.exe"

[Run]
Filename: "{app}\BMCPolinexo.exe"; Description: "{cm:LaunchProgram,BMCPolinexo}"; Flags: nowait postinstall skipifsilent

[Code]
function SetupMutex(Param: String): String;
begin
  Result := 'Global\BMCPolinexo-Setup-' + GetEnv('USERDOMAIN') + '-' + GetEnv('USERNAME');
end;
