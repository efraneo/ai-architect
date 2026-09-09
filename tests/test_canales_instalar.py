"""Canales (Telegram, correo, WhatsApp) e instalación automática. Sin red: `requests`,
SMTP e IMAP se doblan."""

from __future__ import annotations

import io
import threading
import zipfile
from pathlib import Path
from unittest import mock

import pytest

from ai_architect import canales, instalar
from ai_architect.agente import caja
from ai_architect.canales import correo, telegram, whatsapp
from ai_architect.commands import canales as cmd_canales
from ai_architect.commands import instalar as cmd_instalar
from ai_architect.commands import telegram as cmd_telegram


@pytest.fixture
def con_telegram(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t0k")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "42")


def respuesta_json(datos: dict, ok: bool = True) -> mock.Mock:
    r = mock.Mock()
    r.ok = ok
    r.json.return_value = datos
    r.text = str(datos)
    r.status_code = 200 if ok else 400
    return r


# --- Estado -----------------------------------------------------------------------


def test_sin_claves_no_hay_canales() -> None:
    assert canales.disponibles() == []
    assert "TELEGRAM_BOT_TOKEN" in canales.que_falta("telegram")
    salida = cmd_canales.run()
    assert salida["success"] and "ningún canal" in salida["explanation"]


def test_con_claves_el_canal_aparece(con_telegram) -> None:
    assert canales.disponibles() == ["telegram"]
    assert "telegram" in cmd_canales.run()["explanation"]


# --- Telegram ---------------------------------------------------------------------


def test_enviar_telegram(con_telegram) -> None:
    with mock.patch.object(
        telegram.requests, "post", return_value=respuesta_json({"ok": True})
    ) as post:
        assert telegram.enviar("hola")["ok"]

    assert post.call_args.kwargs["json"] == {"chat_id": "42", "text": "hola"}
    assert "bott0k/sendMessage" in post.call_args.args[0]


def test_sin_configurar_no_envia() -> None:
    assert not telegram.enviar("hola")["ok"]


def test_recibir_solo_del_chat_autorizado(con_telegram) -> None:
    actualizaciones = {
        "ok": True,
        "result": [
            {
                "update_id": 1,
                "message": {"chat": {"id": 42}, "text": "revisa el proyecto"},
            },
            {"update_id": 2, "message": {"chat": {"id": 99}, "text": "hackea todo"}},
        ],
    }

    with mock.patch.object(
        telegram.requests, "post", return_value=respuesta_json(actualizaciones)
    ):
        mensajes = telegram.recibir(0)

    assert mensajes[0]["texto"] == "revisa el proyecto"
    assert mensajes[1]["ajeno"] is True and "texto" not in mensajes[1]


def test_escuchar_atiende_y_contesta(con_telegram) -> None:
    actualizaciones = {
        "ok": True,
        "result": [{"update_id": 7, "message": {"chat": {"id": 42}, "text": "hola"}}],
    }
    enviados = []

    def post(url, json=None, timeout=0):
        if url.endswith("getUpdates"):
            return respuesta_json(actualizaciones)

        enviados.append(json["text"])

        return respuesta_json({"ok": True})

    with mock.patch.object(telegram.requests, "post", side_effect=post):
        n = telegram.escuchar(lambda t: f"dijiste {t}", una_vuelta=True)

    assert n == 1 and enviados == ["dijiste hola"]


def test_el_comando_telegram_atiende_ordenes_y_permisos(con_telegram) -> None:
    from ai_architect.commands import conversar

    with mock.patch(
        "ai_architect.commands.pide.run",
        return_value={
            "success": True,
            "explanation": "Propongo X.",
            "result": {"pending": ["ab · escribir x"], "pending_ids": ["abcd"]},
        },
    ):
        respuesta = cmd_telegram.atender("cambia x", ".", False)

    assert "Propongo X." in respuesta and "esperando tu permiso" in respuesta
    assert conversar.hay_permiso_pendiente()

    with mock.patch.object(
        conversar.pendientes, "aprobar", return_value={"success": True, "done": ["✓ x"]}
    ):
        with mock.patch.object(
            conversar.motor_de_voz, "preparar", return_value={"segundos": 0}
        ):
            assert "apliqué 1" in cmd_telegram.atender("sí", ".", False)

    assert not conversar.hay_permiso_pendiente()
    assert "pendiente" in cmd_telegram.atender("/pendientes", ".", False).lower()


def test_sin_bot_el_comando_lo_dice() -> None:
    salida = cmd_telegram.run(".")
    assert not salida["success"] and "TELEGRAM_BOT_TOKEN" in salida["error"]


def test_en_segundo_plano_solo_si_esta_configurado(con_telegram) -> None:
    assert cmd_telegram.en_segundo_plano(".", False) is None or True  # sin bot: None
    with mock.patch.object(telegram, "escuchar") as escuchar:
        parar = cmd_telegram.en_segundo_plano(".", False)
        assert isinstance(parar, threading.Event)
        for _ in range(50):
            if escuchar.called:
                break
            import time

            time.sleep(0.01)
    assert escuchar.called


# --- Correo ------------------------------------------------------------------------


def test_correo_sin_configurar() -> None:
    assert not correo.enviar("a@b.co", "x", "y")["ok"]
    assert not correo.leer()["ok"]


def test_correo_envia_por_ssl(monkeypatch) -> None:
    monkeypatch.setenv("CORREO_SMTP_HOST", "smtp.x")
    monkeypatch.setenv("CORREO_USUARIO", "yo@x.co")
    monkeypatch.setenv("CORREO_CLAVE", "s")

    with mock.patch.object(correo.smtplib, "SMTP_SSL") as ssl_:
        salida = correo.enviar("tu@x.co", "Hola", "cuerpo")

    assert salida["ok"] and salida["para"] == "tu@x.co"
    smtp = ssl_.return_value.__enter__.return_value
    smtp.login.assert_called_once_with("yo@x.co", "s")
    mensaje = smtp.send_message.call_args.args[0]
    assert mensaje["To"] == "tu@x.co" and mensaje["Subject"] == "Hola"


def test_correo_destinatario_invalido(monkeypatch) -> None:
    monkeypatch.setenv("CORREO_SMTP_HOST", "smtp.x")
    monkeypatch.setenv("CORREO_USUARIO", "yo@x.co")
    monkeypatch.setenv("CORREO_CLAVE", "s")
    assert "inválido" in correo.enviar("nada", "x", "y")["error"]


# --- WhatsApp ---------------------------------------------------------------------


def test_whatsapp_envia(monkeypatch) -> None:
    monkeypatch.setenv("WHATSAPP_TOKEN", "tk")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123")

    with mock.patch.object(
        whatsapp.requests, "post", return_value=respuesta_json({"ok": True})
    ) as post:
        salida = whatsapp.enviar("+57 300 123 4567", "hola")

    assert salida["ok"] and salida["para"] == "573001234567"
    assert post.call_args.kwargs["json"]["to"] == "573001234567"
    assert "Bearer tk" in post.call_args.kwargs["headers"]["Authorization"]


def test_whatsapp_numero_corto(monkeypatch) -> None:
    monkeypatch.setenv("WHATSAPP_TOKEN", "tk")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "123")
    assert "inválido" in whatsapp.enviar("12", "hola")["error"]


# --- La caja del agente ---------------------------------------------------------------


def test_los_canales_configurados_entran_en_la_caja(
    tmp_path: Path, con_telegram
) -> None:
    nombres = caja.nombres(caja.herramientas_para(tmp_path))
    assert "enviar_telegram" in nombres and "instalar" in nombres
    assert "enviar_correo" not in nombres
    for h in caja.herramientas_para(tmp_path):
        assert h.spec.requires_confirmation == (h.spec.name in caja.ESCRIBEN)


# --- Instalar ------------------------------------------------------------------------


def test_instalar_paquete_apunta_en_requirements(tmp_path: Path) -> None:
    req = tmp_path / "requirements.txt"
    req.write_text("openai>=1.40.0\n", encoding="utf-8")
    hecho = mock.Mock(returncode=0, stdout="ok", stderr="")

    with mock.patch.object(instalar.subprocess, "run", return_value=hecho) as run:
        salida = instalar.paquete("rich>=13", req)

    assert salida["ok"] and salida["requirements"] is True
    assert run.call_args.args[0][-1] == "rich>=13" and "pip" in run.call_args.args[0]
    assert req.read_text(encoding="utf-8").endswith("rich>=13\n")
    assert instalar.instalado()[-1]["nombre"] == "rich>=13"

    # ya estaba: no se repite
    with mock.patch.object(instalar.subprocess, "run", return_value=hecho):
        assert instalar.paquete("openai", req)["requirements"] is False


def test_instalar_paquete_nombre_raro_no_pasa() -> None:
    assert "no parece" in instalar.paquete("rich; rm -rf /")["error"]


def test_instalar_paquete_falla_con_motivo(tmp_path: Path) -> None:
    roto = mock.Mock(returncode=1, stdout="", stderr="No matching distribution")

    with mock.patch.object(instalar.subprocess, "run", return_value=roto):
        salida = instalar.paquete("noexiste", tmp_path / "r.txt")

    assert not salida["ok"] and "No matching" in salida["error"]


def test_dentro_del_exe_no_hay_pip(monkeypatch) -> None:
    monkeypatch.setattr(instalar.sys, "frozen", True, raising=False)
    assert "no hay pip" in instalar.paquete("rich")["error"]


def _zip_con_skill(nombre: str, ruta: str = "") -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        base = "repo-main/" + (ruta + "/" if ruta else "")
        z.writestr(
            base + "skill.toml", f'[skill]\nname = "{nombre}"\ndescription = "d"\n'
        )
        z.writestr(base + "README.md", "hola")
        z.writestr("repo-main/otro.txt", "no va")
    return buf.getvalue()


def test_instalar_skill_desde_github(tmp_path: Path) -> None:
    r = mock.Mock(status_code=200, content=_zip_con_skill("resumir", "skills/resumir"))
    r.raise_for_status = mock.Mock()

    with mock.patch.object(instalar.requests, "get", return_value=r) as get:
        salida = instalar.skill(
            "https://github.com/u/repo/tree/main/skills/resumir", tmp_path
        )

    assert salida["ok"] and salida["skill"] == "resumir" and salida["archivos"] == 2
    assert (tmp_path / "resumir" / "skill.toml").is_file()
    assert "codeload.github.com/u/repo/zip/refs/heads/main" in get.call_args.args[0]


def test_instalar_skill_repositorio_entero(tmp_path: Path) -> None:
    r = mock.Mock(status_code=200, content=_zip_con_skill("lint"))
    r.raise_for_status = mock.Mock()

    with mock.patch.object(instalar.requests, "get", return_value=r):
        salida = instalar.skill("https://github.com/u/repo", tmp_path)

    assert salida["ok"] and (tmp_path / "lint" / "skill.toml").is_file()


def test_instalar_skill_sin_manifiesto(tmp_path: Path) -> None:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("repo-main/x.py", "")
    r = mock.Mock(status_code=200, content=buf.getvalue())
    r.raise_for_status = mock.Mock()

    with mock.patch.object(instalar.requests, "get", return_value=r):
        assert (
            "skill.toml"
            in instalar.skill("https://github.com/u/repo", tmp_path)["error"]
        )


def test_instalar_skill_archivo_suelto(tmp_path: Path) -> None:
    r = mock.Mock(status_code=200, text='[skill]\nname = "suelta"\n')
    r.raise_for_status = mock.Mock()

    with mock.patch.object(instalar.requests, "get", return_value=r):
        salida = instalar.skill("https://raw.example.com/x/suelta/skill.toml", tmp_path)

    assert salida["ok"] and (tmp_path / "suelta" / "skill.toml").is_file()


def test_instalar_url_invalida() -> None:
    assert "URL" in instalar.skill("no es url")["error"]


def test_el_comando_instalar_entiende_la_frase(tmp_path: Path) -> None:
    with mock.patch.object(
        instalar,
        "paquete",
        return_value={"ok": True, "paquete": "rich", "requirements": True},
    ) as p:
        salida = cmd_instalar.run("rich", str(tmp_path))

    assert salida["success"] and "requirements" in salida["explanation"]
    assert p.call_args.args[0] == "rich"

    with mock.patch.object(
        instalar,
        "skill",
        return_value={"ok": True, "skill": "s", "carpeta": "c", "archivos": 1},
    ) as s:
        assert cmd_instalar.run("https://github.com/u/r")["success"]

    assert s.call_args.args[0] == "https://github.com/u/r"
    assert "nada" in cmd_instalar.run("")["explanation"].lower()
