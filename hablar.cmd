@echo off
rem =========================================================
rem  Hablar con el arquitecto
rem
rem      hablar
rem
rem  Abre el rostro, enciende el microfono y se queda
rem  escuchando. Se le habla sin mas: no hay palabra clave.
rem  Ctrl+C para terminar.
rem
rem  Para que ademas pueda TOCAR archivos del repositorio:
rem
rem      hablar --si
rem
rem  Esa decision se toma aqui, al abrir, y no a mitad de la
rem  conversacion: hablando no hay forma de teclear una
rem  bandera, y adivinar que una frase autoriza a cambiar
rem  codigo es justo lo que no hay que hacer.
rem =========================================================

setlocal

set "RAIZ=%~dp0"
set "PY=%RAIZ%.venv\Scripts\python.exe"

if not exist "%PY%" (
  echo No encuentro el entorno en %RAIZ%.venv
  echo Crealo con:  python -m venv .venv ^&^& .venv\Scripts\pip install -e .
  exit /b 1
)

"%PY%" -m ai_architect.cli conversar "%RAIZ%." %*

endlocal
