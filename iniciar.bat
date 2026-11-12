@echo off
rem BioFig: doble clic para abrir. La primera vez instala todo lo necesario.
cd /d "%~dp0"
if exist ".instalado" goto iniciar
echo Primera vez: instalando BioFig (puede tardar unos minutos)...
set "PYEXE="
where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
  echo No se encontro Python. Instala Python 3.11 o mas nuevo desde https://www.python.org/downloads/
  echo y marca la opcion "Add python.exe to PATH".
  pause
  exit /b 1
)
%PYEXE% instalar.py
if errorlevel 1 (
  echo.
  echo La instalacion no termino. Revisa el mensaje de arriba y volve a abrir iniciar.bat.
  pause
  exit /b 1
)
:iniciar
echo Abriendo BioFig en http://127.0.0.1:8765 ... (cerra esta ventana para apagarlo)
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8765"
.venv\Scripts\python server.py
if errorlevel 1 pause
