"""Memoria de hechos a largo plazo de Architect.

Portado de OpenJarvis (Apache-2.0): ``almacen`` (JSON en ``~/.ai_architect/memoria.json``),
``extractor`` (saca hechos durables de cada conversación con el modelo) y ``servicio``.

Este módulo expone la capa que usa el resto de Architect:

- ``recordar(texto)``            → «recuerda que…»: hecho de confianza.
- ``hechos()`` / ``olvidar()``    → listar y borrar.
- ``para_prompt()``              → bloque de texto listo para meter en un prompt.
- ``aprender_de(usuario, asistente)`` → aprendizaje automático tras cada respuesta.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any

from ai_architect.agente.memoria.almacen import Fact, LocalFactStore
from ai_architect.agente.rutas_agente import get_memory_dir

__all__ = [
    "Fact",
    "almacen",
    "aprender_de",
    "auto_activa",
    "hechos",
    "olvidar",
    "para_prompt",
    "recordar",
    "ruta",
]

_MAX_HECHOS = 1000
_ARCHIVO = "memoria.json"

# Lo que se le pide al modelo al aprender solo. El de OpenJarvis estaba en inglés
# y, en la primera prueba real, lo único que sacó fue «el usuario habla español»
# —dos veces, en dos idiomas—. Aquí se dice qué vale y qué no.
PROMPT_EXTRACTOR = (
    "Extraes hechos DURABLES sobre el usuario a partir de un intercambio: nombre, "
    "empresa, rol, proyectos en los que trabaja, herramientas y preferencias "
    "explícitas, decisiones que pidió recordar. Responde SOLO con una lista JSON "
    'de frases cortas en español, en tercera persona ("Trabaja en Xentris Tech"). '
    "NO incluyas: el idioma en que habla, saludos, lo que pidió en esta orden "
    "concreta, opiniones tuyas, ni nada que ya esté implícito en ser un "
    "programador que usa este asistente. Si no hay nada durable, responde []."
)

# Aunque el modelo se despiste, esto no entra: no aporta nada.
_TRIVIAL = ("español", "espanol", "spanish", "idioma", "language", "saluda", "greets")


def ruta() -> Path:
    return get_memory_dir() / _ARCHIVO


def almacen() -> LocalFactStore:
    return LocalFactStore(ruta(), max_facts=_MAX_HECHOS)


def recordar(texto: str, fuente: str = "usuario") -> bool:
    """Guarda un hecho dicho explícitamente por el usuario (confianza plena)."""
    limpio = " ".join((texto or "").split()).strip(" .")
    if not limpio:
        return False
    almacen().add_with_trust(limpio, source=fuente, trust="trusted")
    return True


def hechos() -> list[Fact]:
    return list(almacen().list())


def olvidar() -> int:
    tienda = almacen()
    n = len(tienda.list())
    tienda.clear()
    return n


def para_prompt(maximo: int = 25) -> str:
    """Los hechos como bloque de prompt, o cadena vacía si no hay nada."""
    lista = [f for f in hechos() if f.trusted_for_recall][-maximo:]
    if not lista:
        return ""
    lineas = "\n".join(f"- {f.text}" for f in lista)
    return f"Lo que sabes del usuario (memoria a largo plazo):\n{lineas}"


def auto_activa(engine_inyectado: Any = None) -> bool:
    """El aprendizaje automático se salta en pruebas (motor inyectado) o si se apaga por entorno."""
    if engine_inyectado is not None:
        return False
    return os.environ.get("ARCHITECT_MEMORIA_AUTO", "1") != "0"


def aprender_de(
    usuario: str, asistente: str, motor: Any = None, en_hilo: bool = True
) -> None:
    """Extrae hechos durables de un intercambio y los guarda como «auto».

    Con ``en_hilo`` corre en segundo plano para no retrasar la respuesta. Cualquier
    fallo del modelo se ignora: la memoria es un extra, nunca puede romper un comando.
    """
    if not (usuario or "").strip():
        return

    def _trabajo() -> None:
        try:
            _extraer_y_guardar(usuario, asistente, motor)
        except Exception:  # noqa: BLE001 - la memoria nunca rompe la respuesta
            return

    if en_hilo:
        threading.Thread(target=_trabajo, name="architect-memoria", daemon=True).start()
    else:
        _trabajo()


def _extraer_y_guardar(usuario: str, asistente: str, motor: Any) -> None:
    from ai_architect.agente.memoria.extractor import FactExtractor

    if motor is None:
        from ai_architect.agente.motor import MotorArquitecto

        motor = MotorArquitecto()
    modelo = getattr(motor, "modelo", "") or ""
    nuevos = FactExtractor(motor, modelo, system_prompt=PROMPT_EXTRACTOR).extract(
        usuario, asistente or ""
    )
    if not nuevos:
        return
    tienda = almacen()
    conocidos = {f.text.strip().lower() for f in tienda.list()}
    frescos = [
        n
        for n in nuevos
        if n.strip()
        and n.strip().lower() not in conocidos
        and not any(t in n.lower() for t in _TRIVIAL)
    ]
    if frescos:
        tienda.add_many_with_trust(frescos, source="auto", trust="auto")
