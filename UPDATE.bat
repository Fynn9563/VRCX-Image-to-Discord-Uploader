@echo off
SETLOCAL

:: Mark db files to be skipped by Git during resets
ECHO Preserving local database files...
git update-index --skip-worktree *.db
IF %ERRORLEVEL% NEQ 0 (
    ECHO Failed to protect database files. Please ensure they exist and retry.
    GOTO :EOF
)

:: Fetch the latest changes from the remote repository
ECHO Fetching latest changes from the remote repository...
git fetch --all
IF %ERRORLEVEL% NEQ 0 (
    ECHO Failed to fetch changes. Please ensure Git is installed and you are in the correct directory.
    GOTO :EOF
)

:: Reset the current branch to match the remote branch (force overwrite local changes)
ECHO Overwriting local changes with remote repository version...
git reset --hard origin/HEAD
IF %ERRORLEVEL% NEQ 0 (
    ECHO Reset failed. Please check your repository settings.
    GOTO :EOF
)

ECHO Local repository successfully updated with remote changes.

:EOF
ENDLOCAL
