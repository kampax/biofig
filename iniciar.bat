@echo off
setlocal EnableExtensions
rem BioFig: doble clic para abrir. La primera vez instala todo lo necesario,
rem incluso Python y Git si faltan (con winget, el instalador oficial de Windows).
cd /d "%~dp0"
if exist ".instalado" goto iniciar

echo ================================================================
echo   BioFig - primera vez: preparando la instalacion
echo ================================================================

call :buscar_python
if not defined PYEXE call :instalar_python
if not defined PYEXE goto sin_python
echo   OK  Python: %PYEXE%

call :buscar_git
if not defined GITOK call :instalar_git
if not defined GITOK goto sin_git
echo   OK  Git

"%PYEXE%" instalar.py
if errorlevel 1 (
  echo.
  echo La instalacion no termino. Revisa el mensaje de arriba y volve a abrir iniciar.bat.
  pause
  exit /b 1
)

:iniciar
if not exist ".venv\Scripts\python.exe" (
  del ".instalado" 2>nul
  echo Falta el entorno de BioFig. Volve a abrir iniciar.bat para reinstalarlo.
  pause
  exit /b 1
)
echo Abriendo BioFig en http://127.0.0.1:8765 ... (cerra esta ventana para apagarlo)
start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8765"
".venv\Scripts\python.exe" server.py
if errorlevel 1 pause
exit /b 0

rem ===================================================================== subrutinas

:buscar_python
rem Busca un Python 3.11+ (lanzador py, PATH y carpetas de instalacion habituales).
set "PYEXE="
if defined BIOFIG_SIMULAR_SIN_PYTHON exit /b 0
for %%C in ("py -3.13" "py -3.12" "py -3.11" "py -3" "python" "python3") do call :probar_python %%~C
if defined PYEXE exit /b 0
for %%D in ("%LOCALAPPDATA%\Programs\Python\Python313" "%LOCALAPPDATA%\Programs\Python\Python312" "%LOCALAPPDATA%\Programs\Python\Python311" "%ProgramFiles%\Python313" "%ProgramFiles%\Python312" "%ProgramFiles%\Python311") do call :probar_carpeta "%%~D"
exit /b 0

:probar_python
if defined PYEXE exit /b 0
for /f "usebackq delims=" %%P in (`call %* "%~dp0verificar_python.py" 2^>nul`) do set "PYEXE=%%P"
exit /b 0

:probar_carpeta
if defined PYEXE exit /b 0
if exist "%~1\python.exe" call :probar_python "%~1\python.exe"
exit /b 0

:instalar_python
echo.
echo No se encontro Python 3.11 o mas nuevo (BioFig lo necesita).
where winget >nul 2>nul
if errorlevel 1 exit /b 0
choice /c SN /n /m "Instalo Python 3.12 automaticamente (paquete oficial, via winget)? [S/N] "
if errorlevel 2 exit /b 0
echo Instalando Python 3.12... (puede tardar un par de minutos)
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements
call :buscar_python
exit /b 0

:buscar_git
set "GITOK="
if defined BIOFIG_SIMULAR_SIN_GIT exit /b 0
where git >nul 2>nul
if not errorlevel 1 set "GITOK=1"
if not defined GITOK if exist "%ProgramFiles%\Git\cmd\git.exe" set "PATH=%ProgramFiles%\Git\cmd;%PATH%"
if not defined GITOK if exist "%ProgramFiles%\Git\cmd\git.exe" set "GITOK=1"
if not defined GITOK if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "PATH=%LOCALAPPDATA%\Programs\Git\cmd;%PATH%"
if not defined GITOK if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GITOK=1"
exit /b 0

:instalar_git
echo.
echo No se encontro Git (BioFig lo usa para descargar las bibliotecas de iconos).
where winget >nul 2>nul
if errorlevel 1 exit /b 0
choice /c SN /n /m "Instalo Git automaticamente (paquete oficial, via winget)? [S/N] "
if errorlevel 2 exit /b 0
echo Instalando Git... (Windows puede pedir permiso de administrador)
winget install -e --id Git.Git --silent --accept-package-agreements --accept-source-agreements
call :buscar_git
exit /b 0

:sin_python
echo.
echo Para continuar, instala Python 3.11 o mas nuevo desde https://www.python.org/downloads/
echo marcando la opcion "Add python.exe to PATH", y volve a abrir iniciar.bat.
start "" https://www.python.org/downloads/
pause
exit /b 1

:sin_git
echo.
echo Para continuar, instala Git desde https://git-scm.com/downloads y volve a abrir iniciar.bat.
start "" https://git-scm.com/downloads
pause
exit /b 1
