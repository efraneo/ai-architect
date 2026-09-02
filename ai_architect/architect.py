"""Punto de entrada del programa instalado.

Existe por dos motivos distintos, y hasta ahora solo cubría uno.

Como `console_scripts` —``architect = "ai_architect.architect:main"``—
basta con exportar `main`: setuptools genera el lanzador y lo llama él.

Como **script suelto** no: PyInstaller ejecuta este archivo de arriba
abajo, y sin la guarda de abajo importaba `main`, no la llamaba, y salía
con código 0. El `.exe` arrancaba, no hacía nada y no se quejaba — que es
la peor forma de fallar, porque parece que funciona.
"""

from __future__ import annotations

from ai_architect.cli import main

__all__ = ["main"]


if __name__ == "__main__":
    main()
