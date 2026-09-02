@echo off
rem =========================================================
rem  Empaquetar el arquitecto
rem
rem      empaquetar
rem
rem  Hace las dos mitades: PyInstaller convierte el proyecto en un
rem  ejecutable que no necesita Python, e Inno Setup lo envuelve en un
rem  instalador que se le puede pasar a cualquiera.
rem
rem  Sale `salida\ArquitectoSetup.exe`, unos 36 MB.
rem
rem  Hace falta Inno Setup, que se instala con:
rem      winget install --id JRSoftware.InnoSetup --exact
rem =========================================================

setlocal

set "RAIZ=%~dp0"
set "PY=%RAIZ%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo No encuentro el entorno en %RAIZ%.venv
  exit /b 1
)

rem  Inno Setup se instala en un sitio u otro segun como se instale: con
rem  winget acaba en la carpeta del usuario, no en Archivos de programa.
rem  Se miran los dos en vez de dar por hecho uno.
set "ISCC="

for %%R in (
  "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
  "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
  "%ProgramFiles%\Inno Setup 6\ISCC.exe"
) do (
  if not defined ISCC if exist %%R set "ISCC=%%~R"
)

echo.
echo === 1 de 2: el ejecutable ===
echo.

"%PY%" -m PyInstaller "%RAIZ%arquitecto.spec" --noconfirm ^
  --distpath "%RAIZ%dist_tmp" --workpath "%RAIZ%build_tmp" --log-level WARN

if errorlevel 1 (
  echo.
  echo Fallo al construir el ejecutable.
  exit /b 1
)

if not defined ISCC (
  echo.
  echo Ejecutable listo en dist_tmp\arquitecto\arquitecto.exe
  echo.
  echo No encuentro Inno Setup, asi que no hay instalador. Para tenerlo:
  echo     winget install --id JRSoftware.InnoSetup --exact
  exit /b 0
)

echo.
echo === 2 de 2: el instalador ===
echo.

"%ISCC%" "%RAIZ%instalador.iss"

if errorlevel 1 (
  echo.
  echo Fallo al construir el instalador.
  exit /b 1
)

echo.
echo Listo: salida\ArquitectoSetup.exe
echo.
echo Windows avisara de "editor desconocido" la primera vez: falta la
echo firma de codigo, que es un certificado de pago. Es un tramite, no
echo un fallo del programa.

endlocal
