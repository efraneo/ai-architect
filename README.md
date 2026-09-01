# AI Architect

**Un arquitecto de software autónomo.** Analiza un repositorio, planifica mejoras,
genera el código, lo revisa, ejecuta las pruebas y decide por sí mismo si el
cambio merece un commit.

[![CI](https://github.com/efraneo/ai-architect/actions/workflows/ci.yml/badge.svg)](https://github.com/efraneo/ai-architect/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![Checked with mypy](https://img.shields.io/badge/mypy-checked-blue)](https://mypy-lang.org/)

---

## Qué hace

Le das un repositorio —local o clonado de GitHub— y una instrucción. A partir de
ahí trabaja solo:

1. **Analiza** el código: archivos, clases, funciones, dependencias, duplicados
   y complejidad.
2. **Planifica** qué cambiar, con el contexto que extrajo del análisis.
3. **Genera** el parche con un LLM.
4. **Valida** el parche antes de tocar nada.
5. **Ejecuta** las pruebas del proyecto de verdad (`RUN_TESTS`).
6. **Decide** con una puntuación de confianza y riesgo si el cambio se acepta.
7. **Recuerda** lo aprendido para la siguiente ejecución.
8. **Commitea**, solo si se lo permites (ver *Commit automático*).

---

## Instalación

Requiere **Python 3.12 o superior**.

```bash
git clone https://github.com/efraneo/ai-architect.git
cd ai-architect

python -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate

pip install -e .
```

Para desarrollar (tests, linters y comprobación de tipos):

```bash
pip install -e ".[dev]"
```

### Configuración

Copia la plantilla y rellena la clave del proveedor que vayas a usar:

```bash
cp .env.example ai_architect.env
```

```ini
AI_PROVIDER=claude            # claude | openai | gemini | ollama | openrouter

ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
OPENROUTER_API_KEY=
OLLAMA_HOST=http://localhost:11434
```

> **Nunca subas ese archivo.** `.gitignore` ya cubre `*.env`; la única plantilla
> que se versiona es `.env.example`, sin valores.

---

## Uso

```
architect {analyze,review,improve,execute,agents,doctor} [proyecto] [opciones]
```

### Comprobar la instalación

No usa IA ni gasta tokens. Es lo primero que conviene ejecutar:

```console
$ architect doctor .
success: True
python: 3.12.0
platform: Windows-11
status: healthy
```

### Analizar un repositorio

Tampoco usa IA: solo lee el código.

```console
$ architect analyze .
success: True
repository: /ruta/al/proyecto
summary: {'total_files': 355, 'python_files': 322, 'total_classes': 304,
          'total_functions': 1325, 'duplicate_groups': 2,
          'average_complexity': 3.57}
recommendations: ['Remove or consolidate duplicated code.']
```

### Revisar el código

```bash
architect review .
```

### Pasar los agentes

Siete agentes estáticos —métricas, arquitectura, pruebas, seguridad,
dependencias, licencias y git— revisan el repositorio. **No usan IA ni gastan
tokens**, y no miran lo que no es tuyo: `.venv`, `node_modules` y las cachés
quedan fuera.

```console
$ architect agents .
success: True
ai: False
agents: ['architecture', 'dependencies', 'git', 'licenses', 'metrics',
         'security', 'testing']
total_findings: 0
```

Con `--ai` se suman los cinco agentes de IA (arquitecto, refactor, revisor,
pruebas y documentación). Son **cinco llamadas al proveedor**, así que hay que
pedirlo a propósito:

```bash
architect agents . --ai
```

Lo que encuentran los agentes estáticos también entra en la decisión de
`improve`: un secreto filtrado pesa en si el parche se aprueba.

### Mejorar el código *(requiere clave de proveedor)*

```bash
architect improve . --instruction "Extrae la lógica de validación a su propio módulo"
architect improve . --file ai_architect/planner/planner.py
```

### Aplicar un parche

`--dry-run` valida el parche **sin tocar** ningún archivo. Úsalo siempre antes
de aplicarlo de verdad:

```bash
architect execute . --patch cambios.patch --dry-run
architect execute . --patch cambios.patch
```

### Salida en JSON

Cualquier comando acepta `--json`, para encadenarlo con otras herramientas:

```bash
architect analyze . --json | jq '.summary.average_complexity'
```

---

## Arquitectura

Motores independientes que se coordinan entre sí:

| Motor | Paquete | Responsabilidad |
|---|---|---|
| Analizador | `analyzer/` | Estructura, dependencias, duplicados y complejidad |
| Planificador | `planner/` | Convierte el análisis en un plan de cambios |
| Proveedores | `providers/` | Claude, OpenAI, Gemini, Ollama y OpenRouter tras una interfaz común |
| Pruebas | `test_runner/` | Ejecuta la suite del proyecto y alimenta la decisión |
| Agentes | `agents/` | Revisión estática (gratis) y análisis con IA (opcional) |
| Generador de parches | `patch_generator/` | Construye y valida el diff |
| Ejecución | `execution/` | Aplica el parche de forma atómica y lanza las pruebas |
| Revisor | `reviewer/` | Puntúa el resultado y decide la aprobación |
| Motor de decisión | `decision_engine/` | Confianza, riesgo y decisión final |
| Memoria | `memory/` | Aprende de las ejecuciones anteriores |
| Git | `git/` | Ramas, commits y diffs |
| Autónomo | `autonomous/`, `scheduler/` | Ejecuciones desatendidas y programadas |
| Enjambre | `swarm/`, `agents/` | Agentes especializados que trabajan en paralelo |

---

## Desarrollo

```bash
pytest                      # 269 tests
ruff check .                # linter
black .                     # formato
mypy ai_architect           # tipos
```

Las cuatro comprobaciones se ejecutan en CI, en **Linux y Windows** con
**Python 3.12**. Cualquier fallo bloquea el merge.

Si vas a contribuir, instala los hooks para no pelearte con el CI:

```bash
pre-commit install
```

### Estado de las pruebas

| | |
|---|---|
| Tests | 269 |
| Cobertura | 50 % |
| Errores de tipo | 0 |

> La cobertura sigue siendo baja para un proyecto de este tamaño y es el
> principal frente de mejora. Subirla no es cosmético: un método roto en
> `Reviewer.statistics()` pasó desapercibido justo porque ninguna prueba
> recorría ese camino.
>
> Ya están cubiertos al 94-100 % el proveedor de Claude, `ExecutionResult` y
> la memoria de experiencias. Los siguientes candidatos, todos en 0 %:
> `memory/knowledge_base.py`, `execution/task_executor.py`, los proveedores
> de Ollama y OpenRouter, y `test_runner/`.

---

## Commit automático

El arquitecto puede aplicar el parche y commitearlo por su cuenta, pero
**viene apagado**. Para encenderlo:

```ini
AUTO_COMMIT=true
```

Aun encendido, commitea solo si se cumplen **las tres** condiciones:

1. `AUTO_COMMIT=true`
2. El motor de decisión **aprobó** el parche
3. El destino **es** un repositorio git

Si alguna falla, el parche queda guardado en disco y el resultado explica por
qué no se commiteó (`commit_reason`). Un fallo de git nunca tumba la mejora:
el parche ya está hecho y se puede aplicar a mano.

---

## Proveedores

| Proveedor | Variable | Notas |
|---|---|---|
| Claude | `ANTHROPIC_API_KEY` | Por defecto `claude-opus-5`. La API ya no acepta `temperature`: se traduce a `output_config.effort` |
| OpenAI | `OPENAI_API_KEY` | |
| Gemini | `GOOGLE_API_KEY` | |
| OpenRouter | `OPENROUTER_API_KEY` | |
| Ollama | `OLLAMA_HOST` | Local, sin clave |

Se elige con `AI_PROVIDER` y el modelo se puede fijar por variable de entorno
(por ejemplo `CLAUDE_MODEL`).

---

## Licencia

[MIT](LICENSE) · © 2026 Efrain Sarmiento
