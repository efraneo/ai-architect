"""Los sentidos: visión por la cámara, oído local y huella de voz. Nada sale
de la máquina: el modelo de visión, faster-whisper y resemblyzer se doblan."""

from __future__ import annotations

import io
import math
import struct
import sys
import types
import wave

import pytest

from ai_architect import vision
from ai_architect.agents import ordenes
from ai_architect.commands import conversar, respuestas
from ai_architect.voz import escuchar, huella

# --- visión ---------------------------------------------------------------------------


def test_que_ves_pide_la_foto_a_la_cara(monkeypatch) -> None:
    monkeypatch.setattr(vision, "disponible", lambda: True)

    salida = vision.por_voz("Architect, ¿qué ves?")

    assert salida is not None and salida["mirar"] and "mirar" in salida["respuesta"]
    assert vision.por_voz("abre Word") is None


def test_sin_clave_no_promete_ver(monkeypatch) -> None:
    monkeypatch.setattr(vision, "disponible", lambda: False)

    salida = vision.por_voz("qué ves")

    assert (
        salida is not None
        and "OPENAI_API_KEY" in salida["respuesta"]
        and "mirar" not in salida
    )


def test_describir_manda_la_imagen_al_modelo(monkeypatch) -> None:
    llamadas = []

    class Cliente:
        class chat:  # noqa: N801 - imita al SDK
            class completions:  # noqa: N801
                @staticmethod
                def create(**kw):
                    llamadas.append(kw)
                    return types.SimpleNamespace(
                        choices=[
                            types.SimpleNamespace(
                                message=types.SimpleNamespace(
                                    content="Una taza de café sobre un escritorio."
                                )
                            )
                        ]
                    )

    monkeypatch.setattr(vision, "disponible", lambda: True)
    monkeypatch.setattr(vision, "_cliente", lambda: Cliente())

    salida = vision.describir("data:image/jpeg;base64,AAAA", "¿qué hay?")

    assert salida["ok"] and "taza" in salida["texto"]
    contenido = llamadas[0]["messages"][1]["content"]
    assert contenido[0]["text"] == "¿qué hay?"
    assert contenido[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert "No identifiques" in llamadas[0]["messages"][0]["content"]


def test_describir_sin_imagen_o_sin_clave(monkeypatch) -> None:
    assert vision.describir("")["ok"] is False
    monkeypatch.setattr(vision, "disponible", lambda: False)
    assert "OPENAI_API_KEY" in vision.describir("AAAA")["error"]


def test_mirar_imagen_contesta_hablado(monkeypatch) -> None:
    monkeypatch.setattr(
        vision,
        "describir",
        lambda imagen, pregunta="": {"ok": True, "texto": "Veo un perro."},
    )

    salida = conversar.mirar_imagen("AAAA", "qué ves")

    assert salida["respuesta"] == "Veo un perro." and "_audio" in salida
    assert "cámara" in conversar.mirar_imagen("", "qué ves")["respuesta"]


def test_la_respuesta_rapida_lleva_mirar_a_la_cara(monkeypatch) -> None:
    monkeypatch.setattr(vision, "disponible", lambda: True)

    assert respuestas.responder("qué ves")["mirar"]


# --- oído local ------------------------------------------------------------------------


def test_sin_faster_whisper_no_hay_oido_local(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "faster_whisper", None)

    assert escuchar.oido_local_disponible() is False
    monkeypatch.setenv("ARCHITECT_OIDO", "local")
    assert escuchar._usar_local() is False


def test_con_faster_whisper_y_sin_clave_se_oye_en_local(monkeypatch) -> None:
    class Segmento:
        def __init__(self, text):
            self.text = text

    class Modelo:
        def __init__(self, *a, **kw):
            pass

        def transcribe(self, ruta, **kw):
            return [Segmento(" Abre Word "), Segmento("y escribe")], None

    falso = types.ModuleType("faster_whisper")
    falso.WhisperModel = Modelo
    monkeypatch.setitem(sys.modules, "faster_whisper", falso)
    # La clave puede venir del .env de la máquina: se pide local explícitamente.
    monkeypatch.setenv("ARCHITECT_OIDO", "local")
    monkeypatch.setattr(escuchar, "_modelo_local", None)

    assert escuchar._usar_local() is True
    assert escuchar.disponible() is True

    salida = escuchar.transcribir(b"RIFF....", ".wav")

    assert salida == {"texto": "Abre Word y escribe", "modelo": "local", "error": ""}
    assert escuchar.ultimo_audio == b"RIFF...."


def test_la_nube_manda_si_hay_clave_salvo_que_se_pida_local(monkeypatch) -> None:
    falso = types.ModuleType("faster_whisper")
    falso.WhisperModel = object
    monkeypatch.setitem(sys.modules, "faster_whisper", falso)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-x")

    monkeypatch.delenv("ARCHITECT_OIDO", raising=False)
    assert escuchar._usar_local() is False

    monkeypatch.setenv("ARCHITECT_OIDO", "local")
    assert escuchar._usar_local() is True


# --- huella de voz ------------------------------------------------------------------------


def _wav(segundos: float = 2.0, frecuencia: int = 16000, tono: float = 220.0) -> bytes:
    cuadros = int(segundos * frecuencia)
    salida = io.BytesIO()

    with wave.open(salida, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(frecuencia)
        w.writeframes(
            b"".join(
                struct.pack(
                    "<h", int(12000 * math.sin(2 * math.pi * tono * i / frecuencia))
                )
                for i in range(cuadros)
            )
        )

    return salida.getvalue()


@pytest.fixture
def resemblyzer_falso(monkeypatch):
    """Un codificador que devuelve un vector distinto por tono: 220 Hz es
    Efraín, 440 Hz es otra persona."""

    class Codificador:
        def __init__(self, verbose=False):
            pass

        def embed_utterance(self, onda):
            cruces = sum(
                1 for a, b in zip(onda[:400], onda[1:401], strict=False) if a * b < 0
            )
            return [1.0, 0.0, 0.0] if cruces < 16 else [0.0, 1.0, 0.0]

    falso = types.ModuleType("resemblyzer")
    falso.VoiceEncoder = Codificador
    falso.preprocess_wav = lambda onda, source_sr=16000: onda
    monkeypatch.setitem(sys.modules, "resemblyzer", falso)
    monkeypatch.setattr(huella, "_codificador", None)
    huella._ultimo_parecido = None
    return falso


def test_sin_resemblyzer_no_se_bloquea_nada(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "resemblyzer", None)

    assert huella.disponible() is False
    assert huella.comparar(_wav()) is None
    assert huella.autoriza("adelante") == (True, "")
    salida = huella.por_voz("aprende mi voz", _wav())
    assert salida is not None and "resemblyzer" in salida["respuesta"]


def test_aprende_la_voz_y_reconoce_al_duenio(resemblyzer_falso) -> None:
    aprendido = huella.por_voz("aprende mi voz", _wav(tono=220))

    assert aprendido is not None and "Aprendida" in aprendido["respuesta"]
    assert huella.aprendida()

    assert huella.comparar(_wav(tono=220)) == pytest.approx(1.0)
    assert huella.autoriza("adelante") == (True, "")

    parecido = huella.comparar(_wav(tono=440))
    assert parecido is not None and parecido < huella.umbral()
    permitido, motivo = huella.autoriza("adelante")
    assert permitido is False and "voz" in motivo
    assert huella.autoriza("abre Word") == (True, "")  # no es sensible


def test_el_audio_corto_no_vale(resemblyzer_falso) -> None:
    salida = huella.aprender(_wav(segundos=0.3))

    assert salida["ok"] is False and "corto" in salida["error"]


def test_olvidar_la_voz(resemblyzer_falso) -> None:
    huella.aprender(_wav())

    assert "olvidé" in huella.por_voz("olvida mi voz")["respuesta"]
    assert huella.aprendida() is False


def test_la_conversacion_rechaza_la_voz_ajena(resemblyzer_falso, monkeypatch) -> None:
    dichos = []
    monkeypatch.setattr(
        conversar, "decir_proactivo", lambda texto: dichos.append(texto)
    )
    huella.aprender(_wav(tono=220))
    huella.comparar(_wav(tono=440))

    salida = conversar.atender_lo_oido("adelante", ".", False)

    assert salida.get("ajeno") and salida["error"] == "voz" and dichos


def test_las_ordenes_saben_instalar_los_sentidos() -> None:
    assert {"instalar_huella", "instalar_oido_local"} <= set(ordenes.tareas_de("voz"))
