# QUANT AI Architect — Arquitectura de agentes

> Estado: **lo que hay en el código**, no lo que se planeó.
> Actualizado al podar los agentes huérfanos.

---

## Cómo leer este documento

La versión anterior describía treinta y cuatro agentes organizados bajo un
`MasterAgent`. Esa arquitectura nunca llegó a funcionar: doce de esos agentes
**no se podían ni instanciar** —heredaban de `BaseAgent`, que declara `run`
abstracto, y ninguno lo implementaba—, y al `MasterAgent` no lo construía
nadie.

Aquí solo está lo que existe y se ejecuta hoy.

---

## El orquestador

`AgentManager` (`agents/agent_manager.py`) es el único orquestador. Tiene dos
mitades, y **la diferencia entre ellas es dinero**:

| | Qué corre | Coste |
|---|---|---|
| `inspect(repositorio)` | Los once agentes estáticos | Cero: no toca ningún proveedor |
| `execute(repositorio)` | Los once estáticos **más** los cinco de IA | Cinco llamadas al proveedor |

`ImprovementEngine.improve()` llama a `inspect()`, nunca a `execute()`:
colgar los cinco agentes de IA de cada mejora multiplicaría por cinco el
coste de cada ejecución. `execute()` se pide a propósito, con
`architect agents --ai`.

`findings_de(inspeccion)` aplana el informe a la lista de hallazgos que lee
el motor de decisión, con archivo y línea cuando el agente los da.

---

## Los once agentes estáticos

No usan IA. Leen el repositorio y devuelven un diccionario con `status` y,
los que encuentran algo, una lista `findings`.

| Agente | Qué mira |
|---|---|
| `ProjectMetricsAgent` | Archivos, líneas, lenguajes, tamaño, los mayores |
| `ArchitectureAgent` | Módulos sobredimensionados, anidamiento, archivos vacíos |
| `TestingAgent` | Archivos de prueba frente a archivos de producción |
| `SecurityAgent` | Secretos por expresión regular: claves AWS, tokens, claves privadas |
| `DependencyAgent` | `requirements.txt`, `pyproject.toml`, Poetry, Pipenv |
| `LicenseAgent` | Licencia declarada y de qué tipo |
| `GitAgent` | Estado del repositorio, ramas, historial |
| `BugHunterAgent` | `except:` pelado, `except` que solo hace `pass`, TODO/FIXME, argumentos mutables por defecto |
| `PerformanceAgent` | `iterrows`, `range(len(...))`, concatenar cadenas en bucle |
| `DevOpsAgent` | Dockerfile, flujos de CI, empaquetado |
| `ReleaseAgent` | CHANGELOG y versión declarada |

### Qué no miran

Todos comparten el filtro de `agents/scope.py`, construido sobre la lista de
exclusión del propio proyecto (`filesystem/constants.py`): fuera `.venv`,
`node_modules`, las cachés y los binarios.

No es un detalle. Sin ese filtro, sobre este mismo repositorio el
`SecurityAgent` reportaba quince secretos filtrados —los quince dentro de
`.venv`, incluido `ruff.exe`, donde la expresión regular casaba con bytes
crudos— y `ProjectMetricsAgent` contaba 18.309 archivos y 1,9 M de líneas
que no son del proyecto.

Un agente que reporta las dependencias de otro no ayuda: mete ruido en la
decisión.

---

## Los cinco agentes de IA

Reciben el contexto que dejaron los estáticos (`context.data`) y llaman al
proveedor. Solo corren con `execute()`.

| Agente | Qué produce |
|---|---|
| `ArchitectAgent` | Lectura arquitectónica del proyecto |
| `RefactorAgent` | Refactorizaciones propuestas |
| `CodeReviewerAgent` | Revisión de código |
| `TestAgent` | Pruebas que faltan |
| `DocumentationAgent` | Análisis documental |

---

## El contrato

`BaseAgent` (`agents/base_agent.py`):

- `run(context)` — **abstracto**. Todo agente lo implementa; los estáticos
  delegan en `review()`.
- `review(project)` — inspección estática. Los agentes de IA no la usan.
- `health()`, `capabilities()`, `metadata()` — introspección.

Un agente que no implementa `run` no se puede construir. Eso fue exactamente
lo que dejó doce agentes inservibles sin que nadie se enterara: como nadie
los construía, el `TypeError` nunca llegaba a saltar.

---

## Qué se podó y por qué

Quince agentes se borraron. En todos los casos el módulo conectado hacía lo
mismo mejor, o el huérfano no hacía nada:

| Podado | Por qué |
|---|---|
| `SecurityAuditorAgent` | Buscaba las subcadenas "secret", "token" y "password" en minúsculas sobre todo el archivo. `SecurityAgent` usa expresiones regulares de la forma real de un secreto |
| `PerformanceOptimizerAgent` | Gemelo de `PerformanceAgent` con `.append(` como regla: saltaba en casi todos los archivos |
| `RefactoringAgent`, `CodeQualityAgent` | Tercera y cuarta implementación de "archivos grandes"; `ArchitectureAgent` ya lo reporta |
| `BackendAgent` | Contaba archivos `.py`; `ProjectMetricsAgent` ya lo hace |
| `DocumentationWriterAgent` | Devolvía `documentation_ready: True` fijo y una lista estática |
| `DuplicateCodeAgent` | El analizador ya reporta `duplicate_groups` |
| `ProjectManagerAgent` | Analizador + contexto + planificador: es lo que hace `ImprovementEngine` |
| `MasterAgent` | Orquestador paralelo superado por `AgentManager` |
| `AgentRegistry` | Registro genérico que nadie usaba |
| `APIAgent`, `DatabaseAgent`, `MLAgent`, `TradingAgent`, `TradingArchitectAgent` | Restos de QUANT TITAN: casaban subcadenas de dominio sobre el código en minúsculas |

Con ellos se fueron dos cadenas que solo colgaban de ahí:
`development_loop/` (un ciclo autónomo paralelo, superado por
`improver/improvement_engine.py`) y `self_improvement/` (cuyo único usuario
era `CodeQualityAgent`; el aprendizaje real vive en `memory/` y
`decision_engine/`).

---

## Cómo se usa

```bash
architect agents .          # los once estáticos, gratis
architect agents . --ai     # + los cinco de IA, cinco llamadas al proveedor
architect agents . --json   # para encadenar con otras herramientas
```

Lo que encuentran los estáticos entra también en la decisión de
`architect improve`: un secreto filtrado pesa en si el parche se aprueba.
