@echo off
SETLOCAL EnableDelayedExpansion

:: Check if Python is installed by trying to call it
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO Python is not installed. Attempting to download and install Python...

    :: Download Python installer using curl with detailed error output
    curl -L -o python-installer.exe https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe
    SET CURL_ERRORLEVEL=%ERRORLEVEL%
    IF !CURL_ERRORLEVEL! NEQ 0 (
        ECHO Failed to download Python installer. Error Level: !CURL_ERRORLEVEL!
        GOTO :EOF
    )

    :: Confirm the download visually
    IF NOT EXIST python-installer.exe (
        ECHO Python installer file not found after download.
        GOTO :EOF
    )

    ECHO Python installer downloaded successfully.

    :: Run the Python installer
    START /WAIT python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Python installation failed.
        GOTO :EOF
    )

    ECHO Python installed successfully.
    :: Add Python to PATH for the current script
    SET "PATH=%PATH%;C:\Python312\Scripts\;C:\Python312\"
)

ECHO Checking for VRCX installation...
:: Check if VRCX is already installed
IF EXIST "C:\Program Files\VRCX\VRCX.exe" (
    ECHO VRCX is already installed.
    GOTO InstallDependencies
)

:: Check if VRCX Setup file exists and download if not
IF NOT EXIST "VRCX_20240323_Setup.exe" (
    ECHO VRCX setup file not found. Downloading...
    curl -L -o VRCX_20240323_Setup.exe https://github.com/vrcx-team/VRCX/releases/download/v2024.03.23/VRCX_20240323_Setup.exe
    IF %ERRORLEVEL% NEQ 0 (
        ECHO Failed to download VRCX setup. Error Level: %ERRORLEVEL%
        GOTO :EOF
    )
)

ECHO Proceeding to VRCX installation...
:: Additional steps for VRCX installation here...

:InstallDependencies
:: Ensure the current directory contains install_dependencies.py or adjust the path below
ECHO Installing Python dependencies...
python install_dependencies.py
IF %ERRORLEVEL% NEQ 0 (
    ECHO Failed to run install_dependencies.py.
    GOTO CleanupAndExit
)

ECHO Installation complete.

:CleanupAndExit
:: Remove the checksum file and VRCX installer regardless of the installation outcome
DEL SHA256SUMS.txt
DEL VRCX_20240323_Setup.exe
PAUSE

:EOF
ENDLOCAL