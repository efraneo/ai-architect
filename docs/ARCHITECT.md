# Cómo está hecho Architect (septiembre de 2026)

Una vuelta por el código tal como funciona hoy, de la orden a la voz. Los
detalles de cada módulo están en sus docstrings; esto es el mapa.

## Las capas

```
 voz / rostro          ai_architect/avatar/rostro.html · voz/{escuchar,hablar,nombre}.py
        │              commands/conversar.py (+ _servidor, _muletillas)
        ▼
 despachador           commands/pide.py (+ pide_guion, pide_modelo, pide_orden, pide_respuesta)
        │              commands/respuestas.py (lo que no necesita modelo)
        ▼
 comandos              cli.py: tabla COMANDOS → commands/{analyze,review,agents,improve,
        │              auto,changelog,execute,doctor,crear,tareas,hacer,memoria,skills,
        │              mcp,pendientes,…}.py
        ▼
 el agente             agente/: orquestador (bucle de turnos con herramientas), caja
        │              (herramientas acotadas al repositorio), guion (prompt), motor
        │              (adapta el proveedor), progreso (lo que va haciendo), memoria/,
        │              skills/, mcp/, aprobaciones.py
        ▼
 motores de análisis   analyzer/, reviewer/, agents/, improver/, patch_generator/,
                       planner/, decision_engine/, execution/, memory/ (experiencias)
        ▼
 proveedores           providers/ (OpenAI, Claude, Gemini, Ollama, OpenRouter)
```

## Una orden, de punta a punta

1. **Se oye.** La página graba PCM a 16 kHz con medio segundo de «antes»
   (`escucharConWhisper` en `rostro.html`) y lo manda a `POST /oir`; sin clave
   de OpenAI usa el reconocedor de Chrome y manda texto a `POST /orden`. Las dos
   vías llegan a `conversar.atender_lo_oido`.
2. **Se decide si iba para él.** `voz/nombre.py`: modo «nombre» (hay que decir
   «Architect», con tolerancia a recortes y ventana de 90 s) o «libre». El eco de
   su propia voz lo descarta `conversar.es_eco`. Si llegó mientras hablaba,
   se corta el audio (`hablar.callar`) y se atiende lo nuevo, o se calla.
3. **Se contesta al momento con un resguardo** y el trabajo sigue aparte
   (`_trabajar`); la página recoge la respuesta por `GET /respuesta?r=` y,
   mientras, pide `GET /progreso` cada medio segundo para enseñar en tarjetas
   lo que `hacer` va haciendo.
4. **`pide` elige.** Lo instantáneo (hora, memoria, ventana) lo resuelve
   `respuestas.py` sin modelo. El resto va al modelo rápido con el catálogo de
   comandos (`pide_guion.INSTRUCCIONES`, con la memoria del usuario dentro);
   si no es una orden, contesta como conversación o lo pasa a un especialista
   (`experto.py`).
5. **El comando corre.** Con `hacer`, el `OrchestratorAgent` trabaja con la
   caja de herramientas (`caja.herramientas_para`: leer, escribir, parche,
   consola, git, skills, MCP). Sin `--si`, cada escritura se niega y queda en la
   cola de aprobaciones (`aprobaciones.ApprovalStore`, SQLite) con sus
   argumentos exactos; `progreso.avisar("permiso", …)` lo cuenta en vivo.
6. **Se dice.** `hablar.preparar` sintetiza (Piper local → OpenAI → voz de
   Windows, con cuarentena de 5 min para el motor que falle). El WAV no suena
   en el servidor: `conversar.entregar` lo deja en memoria y la página lo
   reproduce desde `GET /audio?t=`, de modo que Chrome cancela su propio audio
   del micrófono y sabe cuándo terminó. Si quedaron cambios en cola, la cara se
   pone en ámbar y pregunta; «sí»/«no» (o los botones, `POST /permiso`) los
   aplica o descarta desde `commands/pendientes.py`.

## Dónde guarda lo suyo

`~/.ai_architect` (o `ARCHITECT_HOME`): `perfil.json`, `.env`, `memoria.json`
(hechos), `approvals.db` (cola), `skills/`, `mcp.json`, `conversacion.log`,
`gasto.json`, `voces/` (Piper).

## Lo que viene de fuera

- El núcleo del agente (orquestador, herramientas, skills, MCP, memoria,
  aprobaciones) es de **OpenJarvis** (Stanford, Apache-2.0), portado a
  `ai_architect/agente/` con los imports reescritos y sin sus dependencias
  externas. Licencia en `agente/LICENCIA-OpenJarvis.txt`.
- Las animaciones del HUD del rostro se inspiran en el `index.css` de OpenJarvis.

## Cómo se comprueba

`black --check`, `ruff check`, `mypy ai_architect` y `pytest` (unas 1 240
pruebas, sin red ni micrófono: los proveedores y la voz se doblan). Los archivos
portados llevan `# mypy: ignore-errors`. La CI corre eso en Ubuntu y Windows.

## El equipo de agentes: Architect manda, ellos obedecen

Architect no analiza ni arregla nada «a mano» cuando hay un agente para eso. Trece
agentes revisan el repositorio con herramientas reales (ruff, mypy, black, git, gh,
pip, pytest, osv.dev) y uno más, Voz y Canales, revisa la máquina. Como herramientas:

- `equipo` corre a todos y da el veredicto; `agente_<tema>` corre uno.
- `ordenar` (agente, tarea, argumentos) hace cumplir una tarea que cambia algo y
  **pasa por tu permiso** (cola de aprobaciones, recuadro ámbar en el rostro, «sí» por voz).
- `consultar` pide una tarea que no cambia nada, sin permiso.

| Agente | Órdenes que obedece |
|---|---|
| calidad | formatear (black), corregir (ruff --fix), verificar |
| errores | corregir (ruff --fix, solo errores reales) |
| dependencias | instalar `paquete`, actualizar (`paquete` o todos) |
| git | commit `mensaje`, subir, traer, rama `nombre` |
| publicacion | anotar_changelog, subir_version `x.y.z` |
| empaquetado | reconstruir (instalador), etiquetar |
| pruebas | correr (`ruta`, `filtro`) |
| devops | ver_ci, relanzar_ci |
| seguridad | auditar (escáneres reales), ultima_auditoria, proteger_secretos (.gitignore) |
| voz | instalar_ventana, probar_voz, configurar_canal `canal`, instalar_huella, instalar_oido_local |
| agenda | recordar `frase`, que_toca, cancelar |
| hogar | encender `dispositivo`, apagar `dispositivo`, estado |
| investigacion | clima, noticias `tema`, correo_urgente |
| sistema | abrir `que` |
| biblioteca | instalar `origen`, buscar `tema` |

Por voz: «formatea el código», «sube los cambios», «corre las pruebas», «actualiza las
dependencias», «anota el changelog», «etiqueta la versión», «reconstruye el instalador».
