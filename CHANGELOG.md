# Changelog

## 0.3.0 — 2026-09-09

- Agentes del entorno: agenda, hogar, investigación y sistema, orquestados y con órdenes
- Los sentidos: visión por la cámara, oído local y huella de voz
- Vida diaria: agenda, casa, mundo, memoria episódica y proactividad
- Los agentes obedecen: órdenes reales que Architect manda y ellos cumplen
- Equipo de agentes orquestado por Architect: herramientas reales y tres agentes nuevos
- reiniciar: banderas de Windows bajo sys.platform para que mypy pase en Linux
- Aprende lo que no sabe: «no puedo» → mejora pendiente; «adelante» la programa (con Claude Code), instala solo y se reinicia
- Dictado: guardar de cualquier forma (con sitio y nombre), «punto a parte», y terminar aunque llegue mal transcrito
- Aislamiento de pruebas: sin Chrome/Edge y sin lanzar programas, pero sin tapar la ventana flotante
- Dictado a Word con signos y tablas, y las pruebas ya no abren ventanas
- Por defecto atiende todo lo que oiga; «Architect» delante es opcional (--nombre lo exige)
- Cámara, micrófono y sonido permitidos desde el arranque, sin preguntar
- Que obedezca todo: cerrar y descansar de cualquier forma, abrir programas, cuentas por voz, mejoras con «adelante», ventana maximizada
- Tercera prueba real: el transcriptor alucinaba su contexto, «cierra Architect» no cerraba, y ahora separa órdenes encadenadas
- Tras la segunda prueba real: memoria por más caminos, «repárate», el eco solo mientras suena, y los 41 hallazgos revisados
- Se arregla a sí mismo solo con «adelante», y se configura hablando
- Las pruebas del celular llevan su propio perfil: sin él, pide contesta «es la primera vez»
- Canales (celular, correo, WhatsApp), el celular por voz, auto-instalación y la nebulosa como reposo
- La prueba HTTP de punta a punta usa un puerto libre: en Linux el 8731 quedaba en TIME_WAIT

## 0.1.0

Initial public architecture.

### Added

- Planner
- Execution Pipeline
- Decision Engine
- Memory Engine
- Knowledge Graph
- Repository Analyzer
- Git Integration
- Autonomous Workflow
- Multi-provider LLM Support
