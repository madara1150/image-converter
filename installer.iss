; Windows installer (Inno Setup 6)
; iscc /DAppVersion=1.1.0 installer.iss  ->  Output\ImageConverter-Setup-Windows.exe

#ifndef AppVersion
  #define AppVersion "1.1.0"
#endif

[Setup]
AppId={{7C1E7A52-3B4F-4D2B-9C1F-6A5E2F3B8D41}
AppName=Image Converter
AppVersion={#AppVersion}
AppVerName=Image Converter {#AppVersion}
AppPublisher=Image Converter
AppPublisherURL=https://github.com/madara1150/image-converter
AppSupportURL=https://github.com/madara1150/image-converter/issues
DefaultDirName={autopf}\Image Converter
DefaultGroupName=Image Converter
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=ImageConverter-Setup-Windows
SetupIconFile=assets\icon.ico
UninstallDisplayIcon={app}\ImageConverter.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion={#AppVersion}
VersionInfoDescription=Image Converter Setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\ImageConverter\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Image Converter"; Filename: "{app}\ImageConverter.exe"
Name: "{autodesktop}\Image Converter"; Filename: "{app}\ImageConverter.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\ImageConverter.exe"; Description: "{cm:LaunchProgram,Image Converter}"; Flags: nowait postinstall skipifsilent
