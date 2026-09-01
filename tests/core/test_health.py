"""``Health``: el informe que ``architect doctor`` no daba.

Estaba huérfano mientras `doctor` —el comando que el README manda ejecutar
primero— devolvía ``"status": "healthy"`` **fijo**. Respondía que todo iba
bien sin una sola clave de proveedor y sin git instalado. Un chequeo que no
puede dar mal no diagnostica nada.
"""

from __future__ import annotations

import pytest

from ai_architect.core.health import Health


class ComponenteFalso:
    def __init__(self, nombre: str, informe: dict | None = None, revienta=None):
        self.name = nombre
        self._informe = informe if informe is not None else {"status": "OK"}
        self._revienta = revienta

    def health(self) -> dict:
        if self._revienta:
            raise RuntimeError(self._revienta)

        return self._informe


@pytest.fixture
def salud() -> Health:
    return Health()


# --- Registrar --------------------------------------------------------------


def test_empieza_sano_y_vacio(salud: Health) -> None:
    informe = salud.report()

    assert informe["healthy"] is True
    assert informe["components"] == {}


def test_registra_por_el_nombre_del_componente(salud: Health) -> None:
    salud.register(ComponenteFalso("proveedor"))

    assert "proveedor" in salud.report()["components"]


def test_el_nombre_se_puede_dar_aparte(salud: Health) -> None:
    """La regresión: ``AgentManager`` no tiene atributo ``name``, y el
    registro reventaba con ``AttributeError`` antes de llegar al informe."""

    class SinNombre:
        def health(self) -> dict:
            return {"status": "OK"}

    salud.register(SinNombre(), name="agentes")

    assert "agentes" in salud.report()["components"]


def test_sin_nombre_ni_atributo_usa_la_clase(salud: Health) -> None:
    class Anonimo:
        def health(self) -> dict:
            return {"status": "OK"}

    salud.register(Anonimo())

    assert "Anonimo" in salud.report()["components"]


# --- Qué cuenta como "no está bien" -----------------------------------------


def test_todo_en_ok_esta_sano(salud: Health) -> None:
    salud.register(ComponenteFalso("uno"))
    salud.register(ComponenteFalso("dos"))

    assert salud.report()["healthy"] is True


@pytest.mark.parametrize(
    "estado",
    ["not_configured", "ERROR", "failed", "unavailable", "DOWN"],
)
def test_un_estado_malo_tumba_el_informe(salud: Health, estado: str) -> None:
    """La regresión: solo contaba como fallo que ``health()`` lanzara. Un
    proveedor sin clave respondía educadamente ``not_configured`` y el
    informe seguía diciendo que todo iba bien."""
    salud.register(ComponenteFalso("proveedor", {"status": estado}))

    assert salud.report()["healthy"] is False


def test_el_estado_no_distingue_mayusculas(salud: Health) -> None:
    salud.register(ComponenteFalso("uno", {"status": "Not_Configured"}))

    assert salud.report()["healthy"] is False


def test_sin_campo_status_se_da_por_bueno(salud: Health) -> None:
    """No todo componente reporta estado; contarlo como fallo sería mentir
    en la otra dirección."""
    salud.register(ComponenteFalso("uno", {"agents": 16}))

    assert salud.report()["healthy"] is True


# --- Un componente roto no tumba el informe ---------------------------------


def test_si_un_componente_revienta_se_anota(salud: Health) -> None:
    salud.register(ComponenteFalso("malo", revienta="se rompió"))

    informe = salud.report()

    assert informe["components"]["malo"]["status"] == "ERROR"
    assert informe["components"]["malo"]["error"] == "se rompió"
    assert informe["healthy"] is False


def test_los_demas_siguen_reportando(salud: Health) -> None:
    salud.register(ComponenteFalso("bueno"))
    salud.register(ComponenteFalso("malo", revienta="x"))

    informe = salud.report()

    assert informe["components"]["bueno"]["status"] == "OK"


def test_lo_que_no_devuelve_un_diccionario_se_envuelve(salud: Health) -> None:
    class Raro:
        name = "raro"

        def health(self):
            return "todo bien"

    salud.register(Raro())

    assert salud.report()["components"]["raro"]["value"] == "todo bien"


# --- Comprobaciones sueltas -------------------------------------------------


def test_una_comprobacion_que_pasa(salud: Health) -> None:
    salud.check("git", True, "git version 2.51")

    informe = salud.report()

    assert informe["components"]["git"]["status"] == "OK"
    assert informe["components"]["git"]["detail"] == "git version 2.51"
    assert informe["healthy"] is True


def test_una_comprobacion_que_falla_tumba_el_informe(salud: Health) -> None:
    salud.check("git", False, "git no está en el PATH")

    informe = salud.report()

    assert informe["components"]["git"]["status"] == "unavailable"
    assert informe["healthy"] is False


def test_una_comprobacion_sin_detalle(salud: Health) -> None:
    salud.check("algo", True)

    assert "detail" not in salud.report()["components"]["algo"]


# --- El informe -------------------------------------------------------------


def test_el_informe_dice_desde_cuando(salud: Health) -> None:
    assert salud.report()["started"] == salud.started.isoformat()


def test_el_informe_es_serializable(salud: Health) -> None:
    import json

    salud.register(ComponenteFalso("uno"))
    salud.check("git", True)

    assert json.dumps(salud.report())
