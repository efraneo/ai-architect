"""``PatternMiner``: lo que el arquitecto aprende de sus ejecuciones.

Está **conectado** —lo construye ``MemoryEngine`` y lo consulta
``patterns_summary()``— pero estaba al 26 % de cobertura. Antes había
pruebas en esta carpeta, pero para ``ExperienceMemory``, que resultó ser una
implementación paralela al conjunto ``ExperienceStore`` + ``LearningEngine``
+ ``MemoryEngine``. Se podó, y la cobertura se pone donde sí se ejecuta.
"""

from __future__ import annotations

import uuid

import pytest

from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
)
from ai_architect.memory.pattern_miner import PatternMiner


def experiencia(
    *,
    exito: bool = True,
    proveedor: str = "openai",
    repositorio: str = "/proyecto",
    instruccion: str = "extraer el validador",
) -> Experience:
    return Experience(
        id=str(uuid.uuid4()),
        repository=repositorio,
        filename="modulo.py",
        instruction=instruccion,
        provider=proveedor,
        experience_type=ExperienceType.EXECUTION,
        outcome=ExperienceOutcome.SUCCESS if exito else ExperienceOutcome.FAILURE,
        confidence=0.9 if exito else 0.2,
        score=1.0,
        risk=0.1,
    )


@pytest.fixture
def minero() -> PatternMiner:
    return PatternMiner()


# --- Éxitos y fracasos ------------------------------------------------------


def test_cuenta_las_ejecuciones_con_exito(minero: PatternMiner) -> None:
    patrones = minero.success_patterns(
        [experiencia(), experiencia(), experiencia(exito=False)]
    )

    assert patrones[0].name == "successful_executions"
    assert patrones[0].occurrences == 2


def test_cuenta_las_que_fallaron(minero: PatternMiner) -> None:
    patrones = minero.failure_patterns(
        [experiencia(), experiencia(exito=False), experiencia(exito=False)]
    )

    assert patrones[0].occurrences == 2


def test_sin_experiencias_los_contadores_van_a_cero(minero: PatternMiner) -> None:
    assert minero.success_patterns([])[0].occurrences == 0
    assert minero.failure_patterns([])[0].occurrences == 0


# --- Por proveedor ----------------------------------------------------------


def test_un_patron_por_proveedor(minero: PatternMiner) -> None:
    patrones = minero.provider_patterns(
        [experiencia(proveedor="openai"), experiencia(proveedor="anthropic")]
    )

    assert {p.name for p in patrones} == {"provider:openai", "provider:anthropic"}


def test_la_confianza_del_proveedor_es_su_tasa_de_acierto(
    minero: PatternMiner,
) -> None:
    """Tres ejecuciones, dos buenas: dos tercios."""
    patrones = minero.provider_patterns(
        [
            experiencia(proveedor="openai"),
            experiencia(proveedor="openai"),
            experiencia(proveedor="openai", exito=False),
        ]
    )

    assert patrones[0].confidence == 0.667
    assert patrones[0].occurrences == 3


def test_un_proveedor_que_siempre_falla(minero: PatternMiner) -> None:
    patrones = minero.provider_patterns([experiencia(exito=False)])

    assert patrones[0].confidence == 0.0


# --- Por repositorio --------------------------------------------------------


def test_cuenta_la_actividad_por_repositorio(minero: PatternMiner) -> None:
    patrones = minero.repository_patterns(
        [
            experiencia(repositorio="/uno"),
            experiencia(repositorio="/uno"),
            experiencia(repositorio="/otro"),
        ]
    )

    por_nombre = {p.name: p.occurrences for p in patrones}

    assert por_nombre["repository:/uno"] == 2
    assert por_nombre["repository:/otro"] == 1


# --- Por palabras de la instrucción -----------------------------------------


def test_saca_las_palabras_frecuentes(minero: PatternMiner) -> None:
    patrones = minero.keyword_patterns(
        [
            experiencia(instruccion="extraer el validador"),
            experiencia(instruccion="extraer el planificador"),
        ]
    )

    por_nombre = {p.name: p.occurrences for p in patrones}

    assert por_nombre["keyword:extraer"] == 2
    assert por_nombre["keyword:validador"] == 1


def test_las_palabras_no_distinguen_mayusculas(minero: PatternMiner) -> None:
    patrones = minero.keyword_patterns(
        [experiencia(instruccion="EXTRAER"), experiencia(instruccion="extraer")]
    )

    assert {p.name for p in patrones} == {"keyword:extraer"}


def test_solo_las_veinticinco_mas_frecuentes(minero: PatternMiner) -> None:
    """Un informe con mil palabras no es un informe."""
    largas = [experiencia(instruccion=f"palabra{i}") for i in range(40)]

    assert len(minero.keyword_patterns(largas)) == 25


# --- Todo junto -------------------------------------------------------------


def test_mine_junta_las_cinco_familias(minero: PatternMiner) -> None:
    patrones = minero.mine([experiencia()])

    nombres = {p.name for p in patrones}

    assert "successful_executions" in nombres
    assert "failed_executions" in nombres
    assert "provider:openai" in nombres
    assert "repository:/proyecto" in nombres
    assert any(n.startswith("keyword:") for n in nombres)


def test_sin_experiencias_no_revienta(minero: PatternMiner) -> None:
    patrones = minero.mine([])

    assert all(p.occurrences == 0 for p in patrones)
