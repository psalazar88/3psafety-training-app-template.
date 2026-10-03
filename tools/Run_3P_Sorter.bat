@echo off
title 3P Safety - Takeout Contact Sorter
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo.
  echo Python is not installed.
  echo 1. Go to https://www.python.org/downloads/ and click "Download Python"
  echo 2. Run the installer and CHECK the box "Add python.exe to PATH"
  echo 3. Then double-click this file again.
  echo.
  pause
  exit /b
)

set "TAKEOUT=%USERPROFILE%\Downloads\Takeout"
if not exist "%TAKEOUT%" (
  echo Could not find "%TAKEOUT%".
  set /p "TAKEOUT=Drag the unzipped Takeout folder into this window and press Enter: "
)
set "TAKEOUT=%TAKEOUT:"=%"

python sort_takeout.py "%TAKEOUT%"
echo.
echo Finished. Your files are in: %~dp0
explorer "%~dp0"
pause
