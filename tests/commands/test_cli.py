"""El CLI: los comandos en una tabla, no en una cadena de ``elif``.

Antes cada comando nuevo obligaba a tocar **tres sitios**: la lista de
``choices``, la cadena de ``elif`` y sus banderas. Olvidarse de uno no daba
error — el comando existía y no hacía nada, o hacía lo del anterior. Durante
el trabajo de conexión pasó de cinco comandos a ocho, y la complejidad del
módulo llegó a 15.

Lo que fijan estas pruebas es que la tabla es la única fuente: si un comando
está en ``COMANDOS``, `argparse` lo acepta y `main()` lo ejecuta.
"""

from __future__ import annotations

from unittest import mock

import pytest

from ai_architect import cli

# --- La tabla es la única fuente --------------------------------------------


def test_las_choices_salen_de_la_tabla() -> None:
    """`pide` va aparte: es quien usa la tabla, no uno de sus miembros.
    Meterlo dentro le dejaría elegirse a sí mismo."""
    accion = next(a for a in cli.build_parser()._actions if a.dest == "command")

    assert set(accion.choices) == {c.nombre for c in cli.COMANDOS} | {"pide"}


def test_pide_no_esta_en_la_tabla_que_elige() -> None:
    assert "pide" not in {c.nombre for c in cli.COMANDOS}
    assert "pide" not in cli.POR_NOMBRE


def test_estan_los_comandos() -> None:
    assert {c.nombre for c in cli.COMANDOS} == {
        "analyze",
        "review",
        "improve",
        "execute",
        "doctor",
        "agents",
        "auto",
        "changelog",
        "voz",
    }


def test_cada_comando_tiene_su_ayuda() -> None:
    """La ayuda del CLI se arma desde la tabla: sin texto, sale vacía."""
    assert all(c.ayuda for c in cli.COMANDOS)


def test_no_hay_nombres_repetidos() -> None:
    nombres = [c.nombre for c in cli.COMANDOS]

    assert len(nombres) == len(set(nombres))


# --- Se ejecuta el que toca -------------------------------------------------


@pytest.mark.parametrize(
    ("comando", "modulo"),
    [
        ("doctor", "doctor"),
        ("analyze", "analyze"),
        ("review", "review"),
        ("agents", "agents"),
    ],
)
def test_cada_comando_llama_a_su_modulo(comando: str, modulo: str) -> None:
    with mock.patch.object(cli, modulo) as destino:
        destino.run.return_value = {"success": True}

        with mock.patch("sys.argv", ["ai-architect", comando, "."]):
            cli.main()

    destino.run.assert_called_once()


def test_el_proyecto_llega_al_comando() -> None:
    with mock.patch.object(cli, "analyze") as destino:
        destino.run.return_value = {}

        with mock.patch("sys.argv", ["ai-architect", "analyze", "/otro/sitio"]):
            cli.main()

    assert destino.run.call_args.args[0] == "/otro/sitio"


def test_por_defecto_el_proyecto_es_el_actual() -> None:
    with mock.patch.object(cli, "analyze") as destino:
        destino.run.return_value = {}

        with mock.patch("sys.argv", ["ai-architect", "analyze"]):
            cli.main()

    assert destino.run.call_args.args[0] == "."


# --- Las banderas obligatorias ----------------------------------------------


def test_auto_sin_instrucciones_falla_con_su_mensaje() -> None:
    with mock.patch("sys.argv", ["ai-architect", "auto", "."]):
        with pytest.raises(SystemExit):
            cli.main()


def test_execute_sin_parche_falla_con_su_mensaje() -> None:
    with mock.patch("sys.argv", ["ai-architect", "execute", "."]):
        with pytest.raises(SystemExit):
            cli.main()


def test_la_guarda_salta_antes_de_ejecutar_nada() -> None:
    """Si el comando corriera igual, `execute` recibiría un parche vacío."""
    with mock.patch.object(cli, "execute") as destino:
        with mock.patch("sys.argv", ["ai-architect", "execute", "."]):
            with pytest.raises(SystemExit):
                cli.main()

    destino.run.assert_not_called()


def test_con_la_bandera_si_se_ejecuta() -> None:
    with mock.patch.object(cli, "auto") as destino:
        destino.run.return_value = {}

        with mock.patch(
            "sys.argv",
            ["ai-architect", "auto", ".", "--instructions", "una", "otra"],
        ):
            cli.main()

    assert destino.run.call_args.kwargs["instructions"] == ["una", "otra"]


def test_los_comandos_sin_exigencias_no_piden_nada() -> None:
    sin_requisitos = [c.nombre for c in cli.COMANDOS if not c.requiere]

    assert "doctor" in sin_requisitos
    assert "analyze" in sin_requisitos


# --- La salida --------------------------------------------------------------


def test_un_comando_desconocido_no_llega_a_main() -> None:
    with mock.patch("sys.argv", ["ai-architect", "inventado", "."]):
        with pytest.raises(SystemExit):
            cli.main()


def test_json_imprime_json(capsys) -> None:
    import json

    with mock.patch.object(cli, "doctor") as destino:
        destino.run.return_value = {"success": True, "status": "healthy"}

        with mock.patch("sys.argv", ["ai-architect", "doctor", "--json"]):
            cli.main()

    assert json.loads(capsys.readouterr().out)["status"] == "healthy"


def test_sin_json_imprime_una_linea_por_clave(capsys) -> None:
    with mock.patch.object(cli, "doctor") as destino:
        destino.run.return_value = {"success": True, "status": "healthy"}

        with mock.patch("sys.argv", ["ai-architect", "doctor"]):
            cli.main()

    assert "status: healthy" in capsys.readouterr().out
