@echo off
SETLOCAL EnableDelayedExpansion

:: Check if Python is installed by trying to call it
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed. Downloading and installing Python...

    :: Download Python installer using curl
    curl -L -o python-installer.exe https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to download Python installer.
        GOTO :EOF
    )

    :: Run the Python installer
    START /WAIT python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Python installation failed.
        GOTO :EOF
    )

    :: Add Python to PATH for the current script
    SET "PATH=%PATH%;C:\Python312\Scripts\;C:\Python312\"
)

:: Check if VRCX is already installed
IF EXIST "C:\Program Files\VRCX\VRCX.exe" (
    ECHO VRCX is already installed.
    GOTO InstallDependencies
)

:: Check if VRCX Setup file exists
IF NOT EXIST "VRCX_20240323_Setup.exe" (
    ECHO VRCX setup file not found. Downloading...
    curl -L -o VRCX_20240323_Setup.exe https://github.com/vrcx-team/VRCX/releases/download/v2024.03.23/VRCX_20240323_Setup.exe
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to download VRCX setup.
        GOTO :EOF
    )
) ELSE (
    ECHO VRCX setup file already exists. Verifying file integrity...
)

:: Download SHA256SUMS.txt
curl -L -o SHA256SUMS.txt https://github.com/vrcx-team/VRCX/releases/download/v2024.03.23/SHA256SUMS.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO Failed to download SHA256 checksums.
    GOTO :EOF
)

:: Extract the checksum from the file
FOR /F "tokens=1,2" %%G IN ('findstr VRCX_20240323_Setup.exe SHA256SUMS.txt') DO SET "downloadedChecksum=%%G"

:: Compute the checksum of the downloaded file
FOR /F "tokens=1" %%I IN ('CertUtil -hashfile VRCX_20240323_Setup.exe SHA256 ^| findstr /v "hash of file CertUtil"') DO (
    SET "computedChecksum=%%I"
    IF /I "!downloadedChecksum!"=="!computedChecksum!" (
        ECHO Checksum verified successfully.
        START /WAIT VRCX_20240323_Setup.exe /S
    ) ELSE (
        ECHO Checksum mismatch. The file may be corrupted or altered.
        GOTO CleanupAndExit
    )
)

:InstallDependencies
:: Ensure the current directory contains install_dependencies.py or adjust the path below
ECHO Installing Python dependencies...
python install_dependencies.py
IF %ERRORLEVEL% NEQ 0 (
    ECHO Failed to run install_dependencies.py.
    GOTO CleanupAndExit
)

ECHO Installation complete.
GOTO CleanupAndExit

:CleanupAndExit
:: Remove the checksum file and VRCX installer regardless of the installation outcome
DEL SHA256SUMS.txt
DEL VRCX_20240323_Setup.exe
PAUSE

:EOF
ENDLOCAL