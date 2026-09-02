# =========================================================
#  Empaquetar el arquitecto en un .exe
#
#      pyinstaller arquitecto.spec
#
#  Sale `dist/arquitecto/arquitecto.exe`, que funciona en un Windows sin
#  Python instalado.
#
#  **Una carpeta y no un solo archivo.** Con `--onefile` el ejecutable se
#  descomprime en el temporal en cada arranque: son varios segundos cada
#  vez, y aqui se arranca para decir una frase. Una carpeta arranca al
#  instante; el instalador la esconde igual.
#
#  **El rostro viaja dentro.** Es la misma leccion que con la rueda: sin
#  declararlo, PyInstaller empaqueta los .py y nada mas, y `conversar`
#  contestaria "no encuentro el rostro" en cualquier maquina.
#
#  Lo que NO se mete: las voces de Piper. Son cien megas y no todo el
#  mundo las quiere; se bajan en el primer arranque de quien las pida.
# =========================================================

from pathlib import Path

RAIZ = Path(SPECPATH)

a = Analysis(
    [str(RAIZ / "ai_architect" / "architect.py")],
    pathex=[str(RAIZ)],
    binaries=[],
    # (origen, destino dentro del paquete)
    datas=[
        (str(RAIZ / "ai_architect" / "avatar" / "rostro.html"), "ai_architect/avatar"),
    ],
    # PyInstaller sigue los imports que ve escritos, y aqui hay unos
    # cuantos que se hacen dentro de una funcion para no pagarlos al
    # arrancar. Sin declararlos, el .exe falla al usarlos y no antes.
    hiddenimports=[
        "ai_architect.commands.agents",
        "ai_architect.commands.analyze",
        "ai_architect.commands.auto",
        "ai_architect.commands.avatar",
        "ai_architect.commands.changelog",
        "ai_architect.commands.configurar",
        "ai_architect.commands.conversar",
        "ai_architect.commands.crear",
        "ai_architect.commands.doctor",
        "ai_architect.commands.encargo",
        "ai_architect.commands.execute",
        "ai_architect.commands.experto",
        "ai_architect.commands.improve",
        "ai_architect.commands.pide",
        "ai_architect.commands.respuestas",
        "ai_architect.commands.review",
        "ai_architect.commands.tareas",
        "ai_architect.commands.voz",
        "ai_architect.herramientas.cve",
        "ai_architect.herramientas.historial",
        "ai_architect.core.windows",
        "tkinter",
        "tkinter.filedialog",
    ],
    hookspath=[],
    runtime_hooks=[],
    # Lo que arrastraria el tamano sin usarse. `matplotlib` y compania no
    # estan instalados, pero si alguien los tiene en su entorno acabarian
    # dentro sin que nadie los pidiera.
    excludes=[
        "matplotlib",
        "numpy",
        "pandas",
        "scipy",
        "PyQt5",
        "PySide6",
        "IPython",
        "notebook",
        "pytest",
        "mypy",
        "black",
        "ruff",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="arquitecto",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Con consola: el arquitecto habla por la terminal tanto como por los
    # altavoces —lo que oye, lo que responde, lo que descarta por eco— y
    # esconderla dejaria al usuario sin la mitad de la informacion.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="arquitecto",
)
