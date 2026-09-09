# Architect como asistente personal: la estructura JARVIS y cómo la cumple

Un asistente personal no es un orquestador empresarial: necesita control del
entorno, proactividad y varios sentidos. Esta es la estructura pedida y, para
cada pieza, qué hace Architect hoy, con qué módulo y cómo se usa por voz.

## Agentes especializados

| Pieza | Estado | Dónde vive | Por voz |
|---|---|---|---|
| **Interfaz y voz** (escucha continua, nombre, voz natural) | ✅ | `voz/escuchar.py`, `voz/hablar.py`, `voz/nombre.py`, `avatar/rostro.html` | «Architect, …» (opcional `--nombre`), interrumpirlo hablándole encima |
| **Contexto y agenda** (horarios, hábitos, prioridad por hora) | ✅ | `agenda.py` (+ `commands/tareas.py` para lo repetido) | «recuérdame llamar a Juan a las tres», «en veinte minutos», «qué tengo hoy», «qué tengo mañana», «cancela los recordatorios». La hora, la parte del día y lo pendiente entran en el guion del modelo. |
| **Hogar e IoT** (luces, persianas, cámaras, electrodomésticos) | ✅ vía Home Assistant | `canales/hogar.py` (`HOGAR_URL`, `HOGAR_TOKEN`) | «enciende la luz de la sala», «abre la puerta del garaje», «cómo está la temperatura», «estado de la casa». Sin configurar, pide la URL y el token. |
| **Investigación y noticias** (clima, tráfico, correo urgente, noticias) | ✅ clima, noticias, correo · ⚠️ tráfico | `investigar.py` | «qué clima hace», «va a llover», «noticias de economía», «tengo correos nuevos». El tráfico necesita una clave de Google Maps y lo dice en vez de inventar. |
| **Código y sistema** (abrir apps, música, archivos) | ✅ | `commands/abrir.py`, `office/word.py`, `commands/dictado.py`, `canales/celular.py`, agente `hacer` | «abre Word», «escribe lo siguiente en Word», «pon una canción» (celular), «maximiza ventana», todo lo del repositorio |

Y el **equipo de agentes de ingeniería** (13 que revisan el repositorio con
ruff, mypy, black, git, gh, pip, pytest, osv.dev y **obedecen** órdenes con
`ordenar`/`consultar`) sigue en `docs/ARCHITECT.md`.

## Habilidades críticas

| Habilidad | Estado | Cómo |
|---|---|---|
| **Proactividad** (habla sin que le pregunten) | ✅ | `proactivo.py`: latido cada minuto en la conversación. Disparadores: recordatorio vencido, lluvia en las próximas horas donde vives, correo que parece urgente, CI de Architect rota. Cada uno espaciado y sin repetir el mismo aviso. Va a la cara y al celular por Telegram. |
| **Visión** (cámara) | ✅ describe escenas, objetos y texto · ✖ no identifica caras | `vision.py` + `/mirar`: la cara toma un fotograma y un modelo con visión (`gpt-4o-mini`, `ARCHITECT_MODELO_VISION`) lo describe. «qué ves», «lee esto», «cuántas personas hay». No reconoce a personas por su cara: es una decisión, no una carencia. |
| **Memoria semántica** (datos fijos) | ✅ | `agente/memoria`: «recuerda que mi café es expreso doble», «qué sabes de mí». Entra en cada prompt. |
| **Memoria episódica** (qué pasó y cuándo) | ✅ | `agente/memoria/episodios.py` sobre `conversacion.log`: «qué hablamos ayer», «qué te dije el lunes sobre las llaves», «dónde dejé las llaves». |
| **Tareas en segundo plano** | ✅ | La conversación lanza cada orden en un hilo y contesta al momento; reparación, reconstrucción, canales y el latido proactivo corren aparte. |

## Infraestructura

| Pieza | Estado | Cómo |
|---|---|---|
| **Conversación no lineal** (saltar de tema y volver) | ✅ sin LangGraph | El orquestador propio (`agente/orquestador.py`) lleva el hilo con herramientas, memoria de hechos, memoria episódica y contexto del día. Un framework de grafos añadiría una dependencia grande para lo que ya hace un bucle con estado; si algún día hace falta, el motor es intercambiable (`agente/motor.py`). |
| **Híbrido local + nube** | ✅ | Voz local: Piper (TTS) y `faster-whisper` (STT) con `ARCHITECT_OIDO=local` («ordenar voz instalar_oido_local»). Órdenes críticas sin modelo: agenda, casa, ventana, programas, cálculo, dictado, celular se resuelven con reglas en la máquina. Modelo local: proveedor Ollama (`OLLAMA_URL`, `OLLAMA_MODEL`). Lo complejo va a la nube (OpenAI/Claude). |
| **Seguridad biométrica** (huella de voz) | ✅ opcional | `voz/huella.py` con `resemblyzer` («ordenar voz instalar_huella»): «aprende mi voz» (varias frases), y desde entonces «adelante», desbloquear, abrir la puerta o la alarma solo se aceptan si la voz se parece (umbral `ARCHITECT_HUELLA_UMBRAL`, 0,75). Sin el paquete no se bloquea nada y el agente de voz lo cuenta como pendiente. «olvida mi voz» la borra. |

## Lo que sigue siendo del usuario

- Home Assistant instalado y con un token (para la casa).
- La ciudad («recuerda que vivo en Bogotá» o `ARCHITECT_CIUDAD`) para el clima.
- IMAP del correo (`CORREO_IMAP_HOST`) para leer correos urgentes.
- `resemblyzer` y `faster-whisper` si quiere huella de voz y oído sin red
  (Architect los instala con su orden).
- Una clave de Google Maps si quiere tráfico en vivo.
