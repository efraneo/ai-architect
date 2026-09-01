# QUANT AI Architect — Entry Points

---

# Objetivo

Documentar todos los puntos de entrada del framework y definir cuál será el punto de acceso oficial en futuras versiones.

---

# Entry Points Detectados

## architect.py

Estado

Activo

Responsabilidad

CLI moderna basada en LLMEngine.

Observaciones

Actualmente implementa los comandos:

- analyze
- review
- improve

Solo improve posee implementación funcional.

---

## cli.py

Estado

Activo (legado)

Responsabilidad

Inicializa la clase Application utilizando argumentos de línea de comandos.

Depende de:

- Application
- ArchitectEngine

---

## main.py

Estado

Experimental

Responsabilidad

Ejecuta ArchitectEngine utilizando rutas fijas.

Observaciones

No debe utilizarse como punto de entrada en producción.

---

## app.py

Estado

Activo

Responsabilidad

Fachada ligera que encapsula ArchitectEngine.

---

# Problemas Detectados

Actualmente existen varios mecanismos diferentes para iniciar el framework.

Esto incrementa:

- complejidad;
- mantenimiento;
- duplicidad de código;
- riesgo de comportamientos inconsistentes.

---

# Objetivo Arquitectónico

El framework dispondrá de un único punto de entrada oficial.

Ejemplo:

```bash
python -m ai_architect
```

o

```bash
ai-architect
```

Todos los demás archivos permanecerán únicamente como adaptadores o serán eliminados durante la Fase 6.

---

# Estado

En auditoría.
