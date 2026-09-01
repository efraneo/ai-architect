"""``VectorMemory``: encontrar ejecuciones parecidas a la de ahora.

Está **conectado** —``MemoryEngine.similar()`` pasa por aquí— y estaba al
50 % de cobertura.

Al lado vivía ``vector_store.py``, huérfano, que llamaba "embedding" a un
``sha256`` del texto y medía el parecido comparando los caracteres de dos
digestos hexadecimales. Eso no mide nada: dos textos sin relación comparten
casi todos los dígitos hex. Este sí hace coseno de verdad, así que aquel se
podó.
"""

from __future__ import annotations

import uuid

import pytest

from ai_architect.memory.models import (
    Experience,
    ExperienceOutcome,
    ExperienceType,
)
from ai_architect.memory.vector_memory import VectorMemory


def experiencia(instruccion: str = "algo") -> Experience:
    return Experience(
        id=str(uuid.uuid4()),
        repository="/proyecto",
        filename="modulo.py",
        instruction=instruccion,
        provider="openai",
        experience_type=ExperienceType.EXECUTION,
        outcome=ExperienceOutcome.SUCCESS,
        confidence=0.9,
        score=1.0,
        risk=0.1,
    )


@pytest.fixture
def memoria() -> VectorMemory:
    return VectorMemory()


# --- Guardar y quitar -------------------------------------------------------


def test_empieza_vacia(memoria: VectorMemory) -> None:
    assert memoria.count() == 0


def test_guarda_una_experiencia(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [1.0, 0.0, 0.0])

    assert memoria.count() == 1


def test_quitar_una_que_existe(memoria: VectorMemory) -> None:
    e = experiencia()
    memoria.add(e, [1.0, 0.0])

    memoria.remove(e.id)

    assert memoria.count() == 0


def test_quitar_una_que_no_existe_no_revienta(memoria: VectorMemory) -> None:
    memoria.remove("inventado")

    assert memoria.count() == 0


def test_vaciarla(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [1.0])
    memoria.add(experiencia(), [0.0])

    memoria.clear()

    assert memoria.count() == 0


# --- El parecido ------------------------------------------------------------


def test_un_vector_identico_da_parecido_uno(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [1.0, 2.0, 3.0])

    assert memoria.search([1.0, 2.0, 3.0])[0].similarity == 1.0


def test_dos_vectores_perpendiculares_no_se_parecen(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [1.0, 0.0])

    assert memoria.search([0.0, 1.0])[0].similarity == 0.0


def test_la_magnitud_no_importa_solo_la_direccion(memoria: VectorMemory) -> None:
    """Es lo que distingue al coseno de una distancia: [1,2] y [2,4] apuntan
    al mismo sitio."""
    memoria.add(experiencia(), [1.0, 2.0])

    assert memoria.search([2.0, 4.0])[0].similarity == 1.0


def test_vectores_de_distinta_longitud_no_se_comparan(memoria: VectorMemory) -> None:
    """Comparar un vector de 3 con uno de 2 no significa nada."""
    memoria.add(experiencia(), [1.0, 2.0, 3.0])

    assert memoria.search([1.0, 2.0])[0].similarity == 0.0


def test_un_vector_de_ceros_no_divide_entre_cero(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [0.0, 0.0])

    assert memoria.search([1.0, 1.0])[0].similarity == 0.0


# --- La búsqueda ------------------------------------------------------------


def test_las_mas_parecidas_van_primero(memoria: VectorMemory) -> None:
    lejana = experiencia("lejana")
    cercana = experiencia("cercana")

    memoria.add(lejana, [0.0, 1.0])
    memoria.add(cercana, [1.0, 0.1])

    resultados = memoria.search([1.0, 0.0])

    assert resultados[0].experience.instruction == "cercana"


def test_se_puede_limitar_cuántas_devuelve(memoria: VectorMemory) -> None:
    for i in range(10):
        memoria.add(experiencia(f"la {i}"), [float(i), 1.0])

    assert len(memoria.search([1.0, 1.0], limit=3)) == 3


def test_buscar_en_una_memoria_vacia(memoria: VectorMemory) -> None:
    assert memoria.search([1.0, 0.0]) == []


def test_el_resultado_trae_la_experiencia_entera(memoria: VectorMemory) -> None:
    e = experiencia("extraer el validador")
    memoria.add(e, [1.0])

    resultado = memoria.search([1.0])[0]

    assert resultado.experience.id == e.id
    assert resultado.experience.instruction == "extraer el validador"


# --- Solo las que se parecen de verdad --------------------------------------


def test_solo_devuelve_las_que_pasan_el_umbral(memoria: VectorMemory) -> None:
    memoria.add(experiencia("gemela"), [1.0, 0.0])
    memoria.add(experiencia("distinta"), [0.0, 1.0])

    parecidas = memoria.similar_experiences([1.0, 0.0])

    assert [e.instruction for e in parecidas] == ["gemela"]


def test_el_umbral_se_puede_bajar(memoria: VectorMemory) -> None:
    memoria.add(experiencia("gemela"), [1.0, 0.0])
    memoria.add(experiencia("distinta"), [0.0, 1.0])

    assert len(memoria.similar_experiences([1.0, 0.0], threshold=0.0)) == 2


def test_si_nada_se_parece_no_devuelve_nada(memoria: VectorMemory) -> None:
    memoria.add(experiencia(), [0.0, 1.0])

    assert memoria.similar_experiences([1.0, 0.0]) == []
