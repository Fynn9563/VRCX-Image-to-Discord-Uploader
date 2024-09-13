[Setup]
AppName=VRChat Photo Uploader
AppVersion=1.0
DefaultDirName={pf}\VRChat Photo Uploader
DefaultGroupName=VRChat Photo Uploader
OutputDir=Output
OutputBaseFilename=VRChatPhotoUploaderSetup
Compression=lzma
SolidCompression=yes

[Files]
; These will be relative paths within the repository
Source: "dist\VRChat Photo Uploader.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "background_image.png"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; This creates a shortcut on the desktop and start menu
Name: "{group}\VRChat Photo Uploader"; Filename: "{app}\VRChat Photo Uploader.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\VRChat Photo Uploader"; Filename: "{app}\VRChat Photo Uploader.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon

[Run]
; This will run the application after installation
Filename: "{app}\VRChat Photo Uploader.exe"; Description: "Launch VRChat Photo Uploader"; Flags: nowait postinstall skipifsilent

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"