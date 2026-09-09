"""
=========================================================
Calcular

«¿Cuánto es 25 por 4?», «suma 3 y 5», «el 15 por ciento de 200», «raíz de 81».
=========================================================

Sin modelo: la frase se traduce a una expresión aritmética y se evalúa con un
evaluador propio sobre el árbol de sintaxis (solo números, + − × ÷, potencias,
paréntesis, raíz y porcentaje). Nada de ``eval``.
"""

from __future__ import annotations

import ast
import math
import operator
import re
from typing import Any

from ai_architect.core.texto import sin_adornos

NUMEROS = {
    "cero": 0,
    "un": 1,
    "uno": 1,
    "una": 1,
    "dos": 2,
    "tres": 3,
    "cuatro": 4,
    "cinco": 5,
    "seis": 6,
    "siete": 7,
    "ocho": 8,
    "nueve": 9,
    "diez": 10,
    "once": 11,
    "doce": 12,
    "trece": 13,
    "catorce": 14,
    "quince": 15,
    "dieciseis": 16,
    "diecisiete": 17,
    "dieciocho": 18,
    "diecinueve": 19,
    "veinte": 20,
    "treinta": 30,
    "cuarenta": 40,
    "cincuenta": 50,
    "sesenta": 60,
    "setenta": 70,
    "ochenta": 80,
    "noventa": 90,
    "cien": 100,
    "mil": 1000,
    "millon": 1_000_000,
    "un millon": 1_000_000,
}

PALABRAS = (
    (r"\bmas\b", "+"),
    (r"\bsumado a\b", "+"),
    (r"\bmenos\b", "-"),
    (r"\bpor ciento de\b", "% de"),
    (r"\bpor\b", "*"),
    (r"\bmultiplicado por\b", "*"),
    (r"\bveces\b", "*"),
    (r"\bentre\b", "/"),
    (r"\bdividido (?:por|entre)\b", "/"),
    (r"\bsobre\b", "/"),
    (r"\belevado a\b", "**"),
    (r"\ba la\b", "**"),
    (r"\bal cuadrado\b", "**2"),
    (r"\bal cubo\b", "**3"),
    (r"\braiz cuadrada de\b", "sqrt"),
    (r"\braiz de\b", "sqrt"),
)

ARRANQUES = (
    "cuanto es",
    "cuanto da",
    "cuanto vale",
    "calcula",
    "calculame",
    "dime cuanto es",
    "suma",
    "resta",
    "multiplica",
    "divide",
    "cual es el resultado de",
    "resultado de",
)

OPERADORES: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _evaluar(nodo: ast.AST) -> float:
    if isinstance(nodo, ast.Expression):
        return _evaluar(nodo.body)

    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return float(nodo.value)

    if isinstance(nodo, ast.BinOp) and type(nodo.op) in OPERADORES:
        izquierda, derecha = _evaluar(nodo.left), _evaluar(nodo.right)

        if isinstance(nodo.op, ast.Pow) and abs(derecha) > 64:
            raise ValueError("potencia demasiado grande")

        return float(OPERADORES[type(nodo.op)](izquierda, derecha))

    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in OPERADORES:
        return float(OPERADORES[type(nodo.op)](_evaluar(nodo.operand)))

    if (
        isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Name)
        and nodo.func.id == "sqrt"
        and len(nodo.args) == 1
    ):
        return math.sqrt(_evaluar(nodo.args[0]))

    raise ValueError("expresión no permitida")


def _a_expresion(frase: str) -> str | None:
    """La frase en aritmética, o ``None`` si no parece una cuenta."""
    plano = sin_adornos(frase)

    for arranque in sorted(ARRANQUES, key=len, reverse=True):
        if plano.startswith(arranque + " "):
            plano = plano[len(arranque) + 1 :]

            break

    plano = re.sub(r"^(el |la |los |las )", "", plano).strip()

    # «suma 3 y 5», «multiplica 4 y 6»: la conjunción es el operador del verbo.
    verbo = sin_adornos(frase).split()[0] if sin_adornos(frase) else ""
    conjuncion = {"suma": "+", "resta": "-", "multiplica": "*", "divide": "/"}.get(
        verbo
    )

    if conjuncion:
        plano = re.sub(r"\by\b", conjuncion, plano)

    # Primero los operadores dichos con palabras («por ciento de» antes de que
    # «ciento» se vuelva un número), luego los números con letras.
    for patron, simbolo in PALABRAS:
        plano = re.sub(patron, simbolo, plano)

    for palabra, numero in sorted(NUMEROS.items(), key=lambda p: -len(p[0])):
        plano = re.sub(rf"\b{palabra}\b", str(numero), plano)

    # «15 % de 200» → 200*15/100
    plano = re.sub(
        r"(\d+(?:[.,]\d+)?)\s*%\s*de\s*(\d+(?:[.,]\d+)?)", r"(\2)*(\1)/100", plano
    )
    plano = (
        plano.replace(",", ".").replace("x", "*").replace("×", "*").replace("÷", "/")
    )
    plano = re.sub(r"sqrt\s*(\d+(?:\.\d+)?)", r"sqrt(\1)", plano)
    plano = plano.replace("=", "").replace("?", "").strip(" .")

    if not re.fullmatch(r"[\d\s.+\-*/%()sqrt]+", plano) or not re.search(r"\d", plano):
        return None

    if not re.search(r"[+\-*/%]|sqrt", plano):
        return None

    return plano


def calcular(frase: str) -> dict[str, Any] | None:
    """El resultado dicho, o ``None`` si la frase no es una cuenta."""
    expresion = _a_expresion(frase)

    if expresion is None:
        return None

    try:
        arbol = ast.parse(expresion, mode="eval")
        resultado = _evaluar(arbol)

    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError):
        return None

    bonito = _bonito(resultado)
    legible = _como_se_dijo(frase)

    return {"respuesta": f"{legible} es {bonito}.", "resultado": resultado}


def _como_se_dijo(frase: str) -> str:
    """La cuenta como la dijo el usuario, sin el «cuánto es» ni los signos."""
    texto = " ".join((frase or "").split()).strip(" ?¿.!")
    plano = sin_adornos(texto)

    for arranque in sorted(ARRANQUES, key=len, reverse=True):
        if plano.startswith(arranque + " "):
            texto = texto[len(texto) - len(plano) + len(arranque) + 1 :].strip()

            break

    return texto[0].upper() + texto[1:] if texto else "Eso"


def _bonito(valor: float) -> str:
    if valor == int(valor) and abs(valor) < 1e15:
        return f"{int(valor):,}".replace(",", ".")

    return f"{valor:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
