"""Que las tareas corran con el programa cerrado.

Las tareas programadas se ejecutan mientras la conversación está abierta,
y eso deja fuera justo el caso que se pidió: "revisa el repositorio cada
noche". A las diez de la noche el arquitecto está cerrado.

Ninguna prueba crea una tarea de verdad en el sistema.
"""

from __future__ import annotations

from unittest import mock

import pytest

from ai_architect.core import windows


@pytest.fixture(autouse=True)
def como_si_fuera_windows(monkeypatch):
    monkeypatch.setattr(windows, "disponible", lambda: True)

    yield


def bien(salida: str = ""):
    return {"success": True, "detalle": salida}


def mal(detalle: str = "acceso denegado"):
    return {"success": False, "detalle": detalle}


def test_se_registra_una_sola_orden() -> None:
    """El Programador pone la hora; el arquitecto, qué hacer.

    Registrar cada tarea por separado obligaría a tocar Windows cada vez
    que se programa algo hablando.
    """
    with mock.patch.object(windows, "_schtasks", return_value=bien()) as llamada:
        salida = windows.registrar("C:/proyectos/x")

    argumentos = llamada.call_args[0][0]

    assert salida["success"] is True
    assert "/Create" in argumentos
    assert "tareas" in salida["command"]
    assert "--correr" in salida["command"]


def test_reemplaza_la_anterior() -> None:
    """Sin `/F`, registrarlo dos veces falla en vez de actualizar."""
    with mock.patch.object(windows, "_schtasks", return_value=bien()) as llamada:
        windows.registrar(".")

    assert "/F" in llamada.call_args[0][0]


def test_se_dice_como_quitarlo() -> None:
    """Registrar algo en el sistema sin decir cómo deshacerlo es una trampa."""
    with mock.patch.object(windows, "_schtasks", return_value=bien()):
        salida = windows.registrar(".")

    assert "--desregistrar" in salida["explanation"]


def test_si_falla_se_dice_por_que() -> None:
    with mock.patch.object(windows, "_schtasks", return_value=mal()):
        salida = windows.registrar(".")

    assert salida["success"] is False
    assert "acceso denegado" in salida["error"]
    assert "administrador" in salida["error"], "hay que decir qué intentar"


def test_se_puede_quitar() -> None:
    with mock.patch.object(windows, "_schtasks", return_value=bien()) as llamada:
        salida = windows.quitar()

    assert salida["success"] is True
    assert "/Delete" in llamada.call_args[0][0]


def test_quitarlo_no_borra_lo_programado() -> None:
    """Son dos cosas: quién despierta al arquitecto, y qué hace al despertar."""
    with mock.patch.object(windows, "_schtasks", return_value=bien()):
        salida = windows.quitar()

    assert "sigue guardado" in salida["explanation"]


def test_fuera_de_windows_se_dice_claro(monkeypatch) -> None:
    monkeypatch.setattr(windows, "disponible", lambda: False)

    salida = windows.registrar(".")

    assert salida["success"] is False
    assert "cron" in salida["error"], "hay que decir cuál sería el equivalente"


def test_desde_el_codigo_llama_al_interprete_del_entorno(monkeypatch) -> None:
    """El Programador arrancaría el Python del sistema, que no lo tiene."""
    monkeypatch.setattr(windows.sys, "frozen", False, raising=False)

    assert "-m ai_architect.cli" in windows.ejecutable()


def test_empaquetado_se_llama_a_si_mismo(monkeypatch) -> None:
    monkeypatch.setattr(windows.sys, "frozen", True, raising=False)

    assert "-m ai_architect.cli" not in windows.ejecutable()


def test_schtasks_que_no_esta_no_revienta() -> None:
    with mock.patch("subprocess.run", side_effect=OSError("no existe")):
        assert windows._schtasks(["/Query"])["success"] is False


# --- El empaquetado ---------------------------------------------------------


def test_el_punto_de_entrada_llama_a_main() -> None:
    """El `.exe` arrancaba, no hacía nada y salía con código 0.

    Como `console_scripts` basta con exportar `main`, porque lo llama
    setuptools. Como script suelto —que es como lo ejecuta PyInstaller—
    hace falta la guarda, y sin ella el ejecutable no se quejaba: la peor
    forma de fallar, porque parece que funciona.
    """
    from pathlib import Path

    import ai_architect.architect as entrada

    fuente = Path(entrada.__file__).read_text(encoding="utf-8")

    assert '__name__ == "__main__"' in fuente
    assert "main()" in fuente


def test_el_rostro_esta_declarado_en_el_spec() -> None:
    """Es la misma lección que con la rueda: sin declararlo, no viaja."""
    from pathlib import Path

    spec = Path(__file__).resolve().parents[2] / "arquitecto.spec"

    assert spec.is_file()

    texto = spec.read_text(encoding="utf-8")

    assert "rostro.html" in texto


def test_los_comandos_estan_declarados_como_ocultos() -> None:
    """Se importan dentro de funciones; PyInstaller no los ve solo."""
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[2] / "arquitecto.spec").read_text(
        encoding="utf-8"
    )

    for comando in ("conversar", "crear", "experto", "tareas", "encargo"):
        assert f"ai_architect.commands.{comando}" in texto


def test_el_instalador_esta_escrito() -> None:
    """Sin `.iss` no hay instalador, y sin instalador no hay icono."""
    from pathlib import Path

    iss = Path(__file__).resolve().parents[2] / "instalador.iss"

    assert iss.is_file()

    texto = iss.read_text(encoding="utf-8")

    assert "arquitecto.exe" in texto


def test_el_instalador_no_pide_administrador() -> None:
    """Es donde se cae la mitad de la gente, y no hace falta: el
    arquitecto solo escribe en la carpeta del usuario."""
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[2] / "instalador.iss").read_text(
        encoding="utf-8"
    )

    assert "PrivilegesRequired=lowest" in texto


def test_al_desinstalar_se_quita_del_programador() -> None:
    """Una tarea huérfana que arranca un programa borrado deja errores
    en el visor de sucesos para siempre."""
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[2] / "instalador.iss").read_text(
        encoding="utf-8"
    )

    assert "[UninstallRun]" in texto
    assert "--desregistrar" in texto


def test_el_registro_de_tareas_va_sin_marcar() -> None:
    """Crear una tarea del sistema sobrevive al programa: se pregunta."""
    from pathlib import Path

    texto = (Path(__file__).resolve().parents[2] / "instalador.iss").read_text(
        encoding="utf-8"
    )

    assert "Flags: unchecked" in texto
