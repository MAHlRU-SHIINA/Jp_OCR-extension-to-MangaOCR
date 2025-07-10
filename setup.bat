@echo off
ECHO.
ECHO =======================================================
ECHO  Welcome to the All-in-One Setup for Manga OCR!
ECHO =======================================================
ECHO.
ECHO This script will perform all necessary steps:
ECHO  1. Create a Python virtual environment.
ECHO  2. Install required libraries (this may take a while).
ECHO  3. Create the necessary launcher files.
ECHO  4. Place a shortcut on your Desktop.
ECHO.
ECHO Please make sure you have Python installed first.
ECHO.
PAUSE

REM --- [1/4] Create Virtual Environment ---
ECHO.
ECHO [1/4] Creating Python virtual environment...
python -m venv venv
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Could not create the virtual environment.
    ECHO Please make sure Python is installed and added to your PATH.
    PAUSE
    EXIT /B
)
ECHO Done.

REM --- [2/4] Install Requirements ---
ECHO.
ECHO [2/4] Installing required libraries... This is the longest step.
call "venv\Scripts\activate.bat"
pip install -r requirements.txt
IF %ERRORLEVEL% NEQ 0 (
    ECHO.
    ECHO ERROR: Failed to install libraries. Please check your internet connection.
    PAUSE
    EXIT /B
)
ECHO Done.

REM --- [3/4] Create Launcher Files ---
ECHO.
ECHO [3/4] Creating local launcher files...

ECHO Writing run.bat...
:: Overwrite or create run.bat with the first line
echo @echo off > run.bat
:: Append the rest of the lines
echo cd /d "%%~dp0" >> run.bat
echo call "venv\Scripts\activate.bat" >> run.bat
echo pythonw JP_OCR.py >> run.bat

ECHO Writing launcher.vbs...
:: Overwrite or create launcher.vbs with the first line
echo ' This script runs a .bat file silently in the background. > launcher.vbs
:: Append the rest of the lines
echo Set objShell = CreateObject("WScript.Shell") >> launcher.vbs
echo strScriptPath = WScript.ScriptFullName >> launcher.vbs
echo Set objFSO = CreateObject("Scripting.FileSystemObject") >> launcher.vbs
echo strFolderPath = objFSO.GetParentFolderName(strScriptPath) >> launcher.vbs
echo strRunBatPath = strFolderPath ^& "\run.bat" >> launcher.vbs
echo objShell.Run chr(34) ^& strRunBatPath ^& Chr(34), 0, false >> launcher.vbs

ECHO Done.

REM --- [4/4] Create Desktop Shortcut ---
ECHO.
ECHO [4/4] Creating Desktop shortcut...

SET SHORTCUT_NAME=Manga OCR.lnk
SET DESKTOP_PATH=%USERPROFILE%\Desktop
SET LAUNCHER_FILE_PATH=%~dp0launcher.vbs
SET ICON_FILE_PATH=%~dp0icon.ico
SET WORKING_DIR=%~dp0

:: Create the temporary VBScript file line by line for maximum reliability
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\create_shortcut.vbs"
echo sLinkFile = "%DESKTOP_PATH%\%SHORTCUT_NAME%" >> "%TEMP%\create_shortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\create_shortcut.vbs"
echo oLink.TargetPath = "%LAUNCHER_FILE_PATH%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.IconLocation = "%ICON_FILE_PATH%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.WorkingDirectory = "%WORKING_DIR%" >> "%TEMP%\create_shortcut.vbs"
echo oLink.Save >> "%TEMP%\create_shortcut.vbs"

:: Now run the script, which is guaranteed to exist
cscript //nologo "%TEMP%\create_shortcut.vbs"

:: Clean up
del "%TEMP%\create_shortcut.vbs"

ECHO Done.

REM --- [SUCCESS] ---
ECHO.
ECHO =======================================================
ECHO  All-in-One Setup Complete!
ECHO =======================================================
ECHO.
ECHO A shortcut named 'Manga OCR' has been placed on your Desktop.
ECHO You can use it to start the application from now on.
ECHO You can now safely close this window.
ECHO.
PAUSE
