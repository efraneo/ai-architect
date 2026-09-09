"""La autorreparación: se apunta, se ofrece y SOLO «adelante» la arranca."""

from __future__ import annotations

from pathlib import Path
from unittest import mock

import pytest

from ai_architect import autoreparacion
from ai_architect.canales import asistente
from ai_architect.commands import reparar, respuestas


@pytest.fixture(autouse=True)
def limpio(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ARCHITECT_FUENTE", "")
    # Las pruebas del ciclo usan el agente propio; la vía de Claude Code tiene la suya.
    monkeypatch.setenv("ARCHITECT_REPARADOR", "hacer")
    autoreparacion._en_curso.clear()
    autoreparacion._ultimo_informe = ""
    asistente.cancelar()

    from ai_architect.core import perfil

    archivo = tmp_path / "perfil.json"
    monkeypatch.setattr(perfil, "ARCHIVO", archivo)
    perfil.configurar("Efraín", archivo=archivo)

    yield

    autoreparacion._en_curso.clear()
    asistente.cancelar()


def fuente_falsa(tmp_path: Path) -> Path:
    f = tmp_path / "fuente"
    f.mkdir()
    (f / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (f / "empaquetar.cmd").write_text("@echo off\n", encoding="utf-8")
    return f


# --- Apuntar y ofrecer -----------------------------------------------------------


def test_se_apunta_y_queda_pendiente() -> None:
    a = autoreparacion.registrar("review", "revisa", "KeyError: x", "Traceback…")

    assert autoreparacion.pendiente()["id"] == a["id"]
    assert "adelante" in autoreparacion.aviso_de_averia(a)
    assert autoreparacion.averias()[-1]["estado"] == "pendiente"


def test_pide_apunta_la_averia_y_la_ofrece() -> None:
    from ai_architect.commands import pide

    def revienta(*_a, **_k):
        raise KeyError("x")

    with mock.patch(
        "ai_architect.cli.POR_NOMBRE",
        {"analyze": mock.Mock(ejecutar=revienta, requiere=())},
    ):
        salida = pide._ejecutar("analyze", {}, ".", "analiza", False, False, False)

    assert not salida["success"] and "adelante" in salida["explanation"]
    assert autoreparacion.pendiente()["comando"] == "analyze"


@pytest.mark.parametrize(
    "texto", ["adelante", "Adelante", "adelante, Architect", "Architect adelante"]
)
def test_la_palabra_maestra(texto: str) -> None:
    assert autoreparacion.es_palabra_maestra(texto)


@pytest.mark.parametrize("texto", ["sí", "dale", "hazlo", "adelante con el proyecto"])
def test_lo_que_no_es_la_palabra_maestra(texto: str) -> None:
    assert not autoreparacion.es_palabra_maestra(texto)


def test_sin_averia_adelante_no_hace_nada() -> None:
    with mock.patch.object(autoreparacion, "reparar") as rep:
        assert "nada pendiente" in autoreparacion.adelante(en_hilo=False)

    rep.assert_not_called()


def test_sin_adelante_nunca_se_repara() -> None:
    """La regla de Efraín: se apunta y se ofrece; no se arranca sola."""
    autoreparacion.registrar("review", "revisa", "boom")

    with mock.patch.object(autoreparacion, "reparar") as rep:
        assert respuestas.responder("sí") is None or "reparación" not in str(
            respuestas.responder("sí")
        )
        respuestas.responder("hazlo")

    rep.assert_not_called()
    assert autoreparacion.pendiente()["estado"] == "pendiente"


# --- Reparar ----------------------------------------------------------------------


def test_reparar_usa_hacer_con_permiso_y_prueba_aparte(
    tmp_path: Path, monkeypatch
) -> None:
    f = fuente_falsa(tmp_path)
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    a = autoreparacion.registrar("review", "revisa", "boom", "Traceback")

    with mock.patch(
        "ai_architect.commands.hacer.run", return_value={"explanation": "Cambié x.py."}
    ) as hacer:
        with mock.patch.object(
            autoreparacion,
            "correr_pruebas",
            return_value={"ok": True, "resumen": "9 passed"},
        ):
            salida = autoreparacion.reparar(a)

    assert (
        salida["ok"]
        and "pruebas pasan" in salida["informe"]
        and "adelante" in salida["informe"]
    )
    assert hacer.call_args.args[0] == str(f) and hacer.call_args.kwargs["si"] is True
    assert (
        "TU PROPIO CÓDIGO" in hacer.call_args.args[1]
        and "boom" in hacer.call_args.args[1]
    )
    assert autoreparacion.pendiente()["estado"] == "reparada"


def test_si_las_pruebas_fallan_queda_pendiente(tmp_path: Path, monkeypatch) -> None:
    f = fuente_falsa(tmp_path)
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    a = autoreparacion.registrar("review", "revisa", "boom")

    with mock.patch(
        "ai_architect.commands.hacer.run", return_value={"explanation": "Intenté."}
    ):
        with mock.patch.object(
            autoreparacion,
            "correr_pruebas",
            return_value={"ok": False, "resumen": "1 failed"},
        ):
            salida = autoreparacion.reparar(a)

    assert not salida["ok"] and "no pasan" in salida["informe"]
    assert autoreparacion.pendiente()["estado"] == "pendiente"


def test_sin_fuente_no_se_toca(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(autoreparacion.sys, "frozen", True, raising=False)
    a = autoreparacion.registrar("review", "revisa", "boom")

    with mock.patch("ai_architect.commands.hacer.run") as hacer:
        salida = autoreparacion.reparar(a)

    hacer.assert_not_called()
    assert not salida["ok"] and "ARCHITECT_FUENTE" in salida["informe"]


def test_adelante_repara_y_luego_reconstruye(tmp_path: Path, monkeypatch) -> None:
    f = fuente_falsa(tmp_path)
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    autoreparacion.registrar("review", "revisa", "boom")
    avisos: list[str] = []

    with mock.patch(
        "ai_architect.commands.hacer.run", return_value={"explanation": "Arreglado."}
    ):
        with mock.patch.object(
            autoreparacion, "correr_pruebas", return_value={"ok": True, "resumen": "ok"}
        ):
            dicho = autoreparacion.adelante(avisar=avisos.append, en_hilo=False)

    assert "reviso" in dicho and avisos and "adelante" in avisos[-1]

    with mock.patch.object(
        autoreparacion,
        "reiniciar",
        return_value={"ok": True, "informe": "Me reinicio."},
    ) as reiniciar:
        dicho = autoreparacion.adelante(avisar=avisos.append, en_hilo=False)

    assert "reinicio" in dicho and avisos[-1] == "Me reinicio."
    reiniciar.assert_called_once()
    assert autoreparacion.pendiente() is None


def test_por_voz_adelante_arranca_y_avisa_por_la_cara() -> None:
    autoreparacion.registrar("review", "revisa", "boom")

    with mock.patch.object(
        autoreparacion, "adelante", return_value="Adelante: reviso."
    ) as ad:
        salida = respuestas.responder("adelante")

    assert salida is not None and salida["respuesta"] == "Adelante: reviso."
    from ai_architect.commands import conversar

    assert ad.call_args.kwargs["avisar"] is conversar.decir_proactivo


def test_el_comando_reparar_lista_y_acepta_la_palabra() -> None:
    assert "No tengo averías" in reparar.run()["explanation"]
    autoreparacion.registrar("review", "revisa", "boom")
    assert "espera tu" in reparar.run()["explanation"]

    with mock.patch.object(autoreparacion, "adelante", return_value="Voy.") as ad:
        assert reparar.run("adelante")["executed"]

    assert ad.call_args.kwargs["en_hilo"] is False


def test_decir_proactivo_avisa_por_la_cara_y_el_celular(monkeypatch) -> None:
    from ai_architect.agente import progreso
    from ai_architect.commands import conversar

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    recibidos: list[dict] = []
    progreso.suscribir(recibidos.append)

    try:
        with mock.patch.object(
            conversar.motor_de_voz,
            "preparar",
            return_value={"segundos": 1.0, "texto": "Listo."},
        ):
            with mock.patch("ai_architect.canales.telegram.enviar") as enviar:
                conversar.decir_proactivo("Listo.")

                for _ in range(50):
                    if enviar.called:
                        break
                    import time

                    time.sleep(0.01)

    finally:
        progreso.desuscribir(recibidos.append)

    assert recibidos[-1]["tipo"] == "decir" and recibidos[-1]["ms"] == 1000
    assert enviar.call_args.args[0] == "Listo."


# --- La configuración guiada ---------------------------------------------------------


def test_sin_bot_llamar_pide_el_token(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(asistente, "CARPETA_USUARIO", tmp_path)

    salida = respuestas.responder("llama a Juan")

    assert salida is not None and salida["pedir"]["clave"] == "TELEGRAM_BOT_TOKEN"
    assert salida["pedir"]["secreto"] is True and "BotFather" in salida["respuesta"]
    assert asistente.hay_configuracion_en_curso()


def test_recibir_el_token_guarda_y_descubre_el_chat(
    monkeypatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(asistente, "CARPETA_USUARIO", tmp_path)
    respuestas.responder("llama a Juan")

    salida = asistente.recibir("TELEGRAM_BOT_TOKEN", "123:abc")

    assert salida["descubrir"] == "telegram" and "escríbele" in salida["respuesta"]
    assert "TELEGRAM_BOT_TOKEN=123:abc" in (tmp_path / ".env").read_text(
        encoding="utf-8"
    )

    actualizaciones = {
        "ok": True,
        "result": [{"update_id": 1, "message": {"chat": {"id": 777}, "text": "hola"}}],
    }

    with mock.patch(
        "ai_architect.canales.telegram._llamar", return_value=actualizaciones
    ):
        with mock.patch("ai_architect.canales.telegram.enviar") as enviar:
            hecho = asistente.descubrir_chat_id(en_hilo=False, espera=5)

    assert (
        hecho["ok"]
        and hecho["chat_id"] == "777"
        and hecho["orden_pendiente"] == "llama a Juan"
    )
    assert "TELEGRAM_CHAT_ID=777" in (tmp_path / ".env").read_text(encoding="utf-8")
    enviar.assert_called_once()
    assert not asistente.hay_configuracion_en_curso()


def test_configurar_el_correo_pide_paso_a_paso(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(asistente, "CARPETA_USUARIO", tmp_path)

    salida = respuestas.responder("configura el correo")

    assert salida is not None and salida["pedir"]["clave"] == "CORREO_SMTP_HOST"
    assert (
        asistente.recibir("CORREO_SMTP_HOST", "smtp.x")["pedir"]["clave"]
        == "CORREO_SMTP_PUERTO"
    )
    assert (
        asistente.recibir("CORREO_SMTP_PUERTO", "465")["pedir"]["clave"]
        == "CORREO_USUARIO"
    )
    assert (
        asistente.recibir("CORREO_USUARIO", "yo@x.co")["pedir"]["clave"]
        == "CORREO_CLAVE"
    )
    assert "vacío" in asistente.recibir("CORREO_CLAVE", "")["respuesta"]
    assert (
        asistente.recibir("CORREO_CLAVE", "s")["pedir"]["clave"] == "CORREO_IMAP_HOST"
    )
    fin = asistente.recibir("CORREO_IMAP_HOST", "")
    assert (
        "configurado" in fin["respuesta"] and not asistente.hay_configuracion_en_curso()
    )
    env = (tmp_path / ".env").read_text(encoding="utf-8")
    assert "CORREO_CLAVE=s" in env and "CORREO_IMAP_HOST" not in env


def test_conversar_recibe_el_dato_y_lo_dice(monkeypatch, tmp_path: Path) -> None:
    from ai_architect.commands import conversar

    monkeypatch.setattr(asistente, "CARPETA_USUARIO", tmp_path)
    respuestas.responder("configura el correo")

    with mock.patch.object(
        conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
    ):
        salida = conversar.recibir_dato("CORREO_SMTP_HOST", "smtp.x")

    assert (
        salida["pedir"]["clave"] == "CORREO_SMTP_PUERTO"
        and "Puerto" in salida["respuesta"]
    )


def test_reparate_sin_averia_explica_la_regla() -> None:
    salida = respuestas.responder("Repárate.")

    assert salida is not None and "adelante" in salida["respuesta"]
    assert "ninguna avería" in salida["respuesta"]


def test_reparate_con_averia_la_nombra() -> None:
    autoreparacion.registrar("review", "revisa", "boom")

    salida = respuestas.responder("arréglate")

    assert salida is not None and "review" in salida["respuesta"]


# --- Aprender lo que no sabe -----------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        "No puedo abrir programas.",
        "Lo siento, no tengo la capacidad de leer PDF.",
        "No sé cómo hacer eso todavía.",
    ],
)
def test_reconoce_un_no_puedo(texto: str) -> None:
    assert autoreparacion.es_incapacidad(texto)


def test_una_respuesta_normal_no_es_incapacidad() -> None:
    assert not autoreparacion.es_incapacidad(
        "Son las nueve. Revisé el proyecto y está bien."
    )


def test_pide_apunta_lo_que_no_supo_hacer_y_ofrece_aprender() -> None:
    from ai_architect.commands import pide

    with mock.patch.object(
        pide,
        "_preguntar",
        return_value='{"comando": "", "respuesta": "No puedo leer archivos PDF."}',
    ):
        salida = pide.run(".", frase="lee este PDF", engine=object())

    assert "adelante" in salida["explanation"] and "aprendo" in salida["explanation"]
    averia = autoreparacion.pendiente()
    assert averia["comando"] == "mejora" and averia["frase"] == "lee este PDF"


def test_lo_que_no_entiende_tambien_se_apunta() -> None:
    from ai_architect.commands import pide

    with mock.patch.object(
        pide, "_preguntar", return_value='{"comando": "", "respuesta": ""}'
    ):
        salida = pide.run(".", frase="haz algo rarísimo", engine=object())

    assert "adelante" in salida["explanation"]
    assert autoreparacion.pendiente()["frase"] == "haz algo rarísimo"


def test_reiniciar_relanza_y_cierra(monkeypatch) -> None:
    from ai_architect.commands import conversar

    monkeypatch.setattr(
        autoreparacion.sys, "argv", ["architect", "conversar", "--flotante"]
    )

    with mock.patch.object(autoreparacion.subprocess, "Popen") as popen:
        with mock.patch.object(conversar, "cerrar_sesion") as cerrar:
            salida = autoreparacion.reiniciar()

    assert salida["ok"] and "reinicio" in salida["informe"]
    orden = popen.call_args.args[0]
    assert orden[-2:] == ["conversar", "--flotante"] and "ai_architect.cli" in orden
    cerrar.assert_called_once()


def test_la_mejora_hecha_queda_en_la_memoria(tmp_path: Path, monkeypatch) -> None:
    from ai_architect.agente import memoria

    f = fuente_falsa(tmp_path)
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    a = autoreparacion.registrar("mejora", "leer archivos PDF", "capacidad")

    with mock.patch(
        "ai_architect.commands.hacer.run", return_value={"explanation": "Añadí pdf.py."}
    ):
        with mock.patch.object(
            autoreparacion, "correr_pruebas", return_value={"ok": True, "resumen": "ok"}
        ):
            autoreparacion.reparar(a)

    assert any("leer archivos PDF" in h.text for h in memoria.hechos())


def test_reconstruir_el_instalador_por_voz() -> None:
    with mock.patch.object(
        autoreparacion, "reconstruir", return_value={"ok": True, "informe": "Listo."}
    ) as rec:
        with mock.patch("ai_architect.commands.conversar.decir_proactivo") as decir:
            salida = respuestas.responder("reconstruye el instalador")

            import time

            for _ in range(50):
                if decir.called:
                    break

                time.sleep(0.02)

    assert salida is not None and "Reconstruyo" in salida["respuesta"]
    rec.assert_called_once()
    assert decir.call_args.args[0] == "Listo."


def test_instalar_ya_no_pide_permiso(tmp_path: Path) -> None:
    from ai_architect.agente import caja

    herramientas = {h.spec.name: h for h in caja.herramientas_para(tmp_path)}

    assert herramientas["instalar"].spec.requires_confirmation is False
    assert "instalar" not in caja.ESCRIBEN


# --- Con Claude Code ------------------------------------------------------------------------


def test_si_esta_claude_code_repara_con_el(tmp_path: Path, monkeypatch) -> None:
    f = fuente_falsa(tmp_path)
    monkeypatch.setenv("ARCHITECT_FUENTE", str(f))
    monkeypatch.delenv("ARCHITECT_REPARADOR", raising=False)
    a = autoreparacion.registrar("mejora", "leer PDF", "capacidad")
    hecho = mock.Mock(
        returncode=0,
        stdout="Añadí ai_architect/commands/pdf.py y sus pruebas.",
        stderr="",
    )

    with mock.patch.object(
        autoreparacion.shutil, "which", return_value="C:/claude.cmd"
    ):
        with mock.patch.object(
            autoreparacion.subprocess, "run", return_value=hecho
        ) as run:
            with mock.patch.object(
                autoreparacion,
                "correr_pruebas",
                return_value={"ok": True, "resumen": "ok"},
            ):
                with mock.patch("ai_architect.commands.hacer.run") as hacer:
                    salida = autoreparacion.reparar(a)

    hacer.assert_not_called()
    orden = run.call_args.args[0]
    assert (
        orden[0] == "C:/claude.cmd"
        and orden[1] == "-p"
        and "TU PROPIO CÓDIGO" in orden[2]
    )
    assert "--dangerously-skip-permissions" in orden
    assert run.call_args.kwargs["cwd"] == str(f)
    assert salida["ok"] and "pdf.py" in salida["informe"]


def test_sin_claude_code_repara_el_agente(monkeypatch) -> None:
    monkeypatch.delenv("ARCHITECT_REPARADOR", raising=False)

    with mock.patch.object(autoreparacion.shutil, "which", return_value=None):
        assert autoreparacion.reparador() == "hacer"

    monkeypatch.setenv("ARCHITECT_REPARADOR", "hacer")

    with mock.patch.object(autoreparacion.shutil, "which", return_value="claude"):
        assert autoreparacion.reparador() == "hacer"
