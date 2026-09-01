# QUANT AI Architect — Consensus Engine

> Estado: Diseño Institucional
> Versión: 1.0

---

# Objetivo

El Consensus Engine es responsable de consolidar las recomendaciones generadas por múltiples agentes especializados y producir una única decisión coherente.

Su función es reducir conflictos, aumentar la confiabilidad y garantizar decisiones explicables.

---

# Filosofía

Ningún agente posee la verdad absoluta.

Cada agente aporta una perspectiva especializada.

La decisión final surge del consenso entre múltiples evaluaciones.

---

# Arquitectura General

```
              Agent Results
                    │
                    ▼
          Consensus Engine
                    │
     ┌──────────────┼──────────────┐
     ▼              ▼              ▼
Aggregation      Scoring      Conflict Solver
     │              │              │
     └──────────────┼──────────────┘
                    ▼
             Final Decision
```

---

# Componentes

## Aggregation

Responsabilidad:

Reunir todas las respuestas producidas por los agentes participantes.

Cada resultado incluye:

- agente;
- recomendación;
- confianza;
- evidencias;
- observaciones.

---

## Scoring

Responsabilidad:

Asignar un peso a cada propuesta.

Factores posibles:

- experiencia del agente;
- historial de aciertos;
- confianza declarada;
- criticidad del dominio.

---

## Conflict Solver

Responsabilidad:

Resolver discrepancias entre recomendaciones.

Puede:

- aceptar una propuesta;
- combinar varias;
- solicitar una nueva evaluación;
- escalar la decisión.

---

# Flujo de Ejecución

```
Task

↓

Agents

↓

Recommendations

↓

Aggregation

↓

Weighted Scoring

↓

Conflict Resolution

↓

Consensus

↓

Decision Report
```

---

# Ejemplo

Tarea:

```
Optimizar RepositoryManager
```

Resultados:

```
PerformanceAgent

↓

Reducir asignaciones

------------------------

SecurityAgent

↓

Validar rutas

------------------------

CodeReviewerAgent

↓

Eliminar duplicación

------------------------

DocumentationAgent

↓

Actualizar documentación
```

El Consensus Engine integra todas las recomendaciones compatibles en un único plan de acción.

---

# Estrategias de Consenso

## Unanimidad

Todos los agentes coinciden.

Resultado:

Aprobación inmediata.

---

## Mayoría

La propuesta con mayor apoyo es seleccionada.

---

## Consenso Ponderado

Cada agente posee un peso distinto.

Ejemplo:

```
SecurityAgent        0.95

ArchitectureAgent    0.90

PerformanceAgent     0.80

DocumentationAgent   0.60
```

Las recomendaciones de mayor peso tienen más influencia en la decisión final.

---

## Escalamiento

Si el desacuerdo supera un umbral definido, la decisión se marca para revisión adicional o intervención humana.

---

# Conflictos

Ejemplo:

```
PerformanceAgent

↓

Eliminar validaciones

-------------------------

SecurityAgent

↓

Mantener validaciones
```

El motor detecta la incompatibilidad y evita ejecutar ambas propuestas simultáneamente.

---

# Reporte de Consenso

Cada decisión genera un informe con:

```
participating_agents

recommendations

conflicts

confidence

decision

reason
```

---

# Integración con Decision Engine

```
Consensus Engine

↓

Decision Engine

↓

Execution Policy

↓

Repository
```

El consenso produce una recomendación.

El Decision Engine decide si esa recomendación puede ejecutarse.

---

# Beneficios

- decisiones más robustas;
- menor dependencia de un único agente;
- reducción de errores;
- mayor trazabilidad;
- explicabilidad.

---

# Evolución Prevista

## Fase 1

Consenso por mayoría simple.

---

## Fase 2

Pesos configurables por agente.

---

## Fase 3

Aprendizaje de pesos a partir del historial de ejecuciones.

---

## Fase 4

Consenso jerárquico.

Los agentes líderes podrán revisar decisiones antes de su aprobación.

---

## Fase 5

Consenso Multi-LLM.

Un mismo problema podrá ser evaluado por modelos distintos (OpenAI, Claude, Gemini, Ollama, etc.), y el Consensus Engine combinará sus resultados con los de los agentes especializados.

---

# Principios

El Consensus Engine debe ser:

- determinista;
- transparente;
- auditable;
- extensible;
- independiente de los proveedores LLM.

---

# Estado

En evolución continua.
