@echo off
rem =========================================================
rem  Arquitecto
rem
rem  Una frase, y responde: elige el comando, lo ejecuta, lo
rem  explica, lo dice en voz alta y lo acompana con la cara.
rem
rem      arquitecto revisa el proyecto y dime que tal esta
rem
rem  Sin comillas: se toma la linea entera. Asi se puede
rem  escribir como se habla, que es de lo que iba todo esto.
rem
rem  Lo que modifica archivos no se ejecuta solo: contesta
rem  con lo que haria y pide --si. Para autorizarlo:
rem
rem      arquitecto --si arregla los except vacios
rem =========================================================

setlocal

set "RAIZ=%~dp0"
set "PY=%RAIZ%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo No encuentro el entorno en %RAIZ%.venv
  echo Crealo con:  python -m venv .venv ^&^& .venv\Scripts\pip install -e .
  exit /b 1
)

set "PERMISO="
set "FRASE=%*"

rem  --si tiene que ir como bandera, no como parte de la frase:
rem  si se cuela dentro, el modelo lee "si arregla los except"
rem  y se pone a interpretar la palabra "si".
if /i "%~1"=="--si" (
  set "PERMISO=--si"
  set "FRASE=%*"
  call set "FRASE=%%FRASE:*--si=%%"
)

if "%FRASE%"=="" (
  echo Dime que quieres, en una frase:
  echo    arquitecto revisa el proyecto y dime que tal esta
  exit /b 1
)

"%PY%" -m ai_architect.cli pide "%RAIZ%." --decir --cara %PERMISO% --frase %FRASE%

endlocal
