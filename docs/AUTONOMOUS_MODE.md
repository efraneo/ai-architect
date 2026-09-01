# QUANT AI Architect — Autonomous Mode

> Estado: Diseño Institucional
> Versión: 1.0

> **Lo que existe hoy:** `architect auto --instructions A B C` ejecuta
> varias mejoras en orden de prioridad y pasa cada resultado por
> `ApprovalEngine`, que antes se construía y no se llamaba nunca.
> Los gestores de rama, fusión y rollback que había aquí llamaban a
> git **sin `cwd`** -- sobre el directorio del proceso, no sobre el
> repositorio analizado. Las ramas se movieron a
> `git/branch_manager.py`; el rollback se podó porque
> `git/commit_manager.py` ya lo hace apuntando bien.

---

# Objetivo

El modo autónomo permite que QUANT AI Architect ejecute ciclos completos de ingeniería de software sin intervención humana.

El sistema es capaz de:

- analizar un proyecto;
- detectar oportunidades de mejora;
- planificar cambios;
- generar código;
- validar resultados;
- aprender de la experiencia.

Todo ello respetando las políticas definidas por el Decision Engine.

---

# Filosofía

El objetivo no es reemplazar al desarrollador.

El objetivo es automatizar el trabajo repetitivo, reducir errores y acelerar la evolución del software.

Toda acción debe ser:

- explicable;
- auditable;
- reversible.

---

# Arquitectura General

```
                 Scheduler
                     │
                     ▼
          Development Loop
                     │
                     ▼
          Task Generator
                     │
                     ▼
             Swarm Manager
                     │
                     ▼
              Specialized Agents
                     │
                     ▼
             Consensus Engine
                     │
                     ▼
            Decision Engine
                     │
                     ▼
          Execution Pipeline
                     │
                     ▼
              Repository
                     │
                     ▼
              Memory Engine
                     │
                     └──────────────┐
                                    ▼
                          Improvement Cycle
```

---

# Componentes

## Scheduler

Responsabilidad

Determinar cuándo iniciar un nuevo ciclo autónomo.

Puede ejecutarse:

- por tiempo;
- por evento;
- por cambios en Git;
- manualmente.

---

## Development Loop

Es el núcleo del modo autónomo.

Coordina toda la ejecución.

---

## Task Generator

Analiza el estado actual del proyecto y genera nuevas tareas automáticamente.

Ejemplos:

- eliminar duplicación;
- mejorar arquitectura;
- actualizar documentación;
- optimizar rendimiento;
- aumentar cobertura de pruebas.

---

## Swarm

Distribuye las tareas entre los agentes especializados.

---

## Consensus Engine

Consolida las recomendaciones producidas por los agentes.

---

## Decision Engine

Determina si las propuestas cumplen las políticas institucionales.

---

## Execution Pipeline

Aplica los cambios aprobados.

Incluye:

- edición;
- validación;
- pruebas;
- commits;
- notificaciones.

---

## Memory Engine

Registra:

- decisiones;
- resultados;
- errores;
- patrones;
- métricas.

---

# Flujo Completo

```
Repository

↓

Analysis

↓

Task Generation

↓

Planning

↓

Swarm

↓

Consensus

↓

Decision

↓

Execution

↓

Testing

↓

Commit

↓

Learning

↓

Next Cycle
```

---

# Ciclo Autónomo

Cada iteración sigue las mismas etapas.

## 1. Observación

El sistema analiza el proyecto.

---

## 2. Diagnóstico

Detecta:

- deuda técnica;
- código duplicado;
- problemas arquitectónicos;
- riesgos;
- oportunidades.

---

## 3. Planificación

Se genera un conjunto priorizado de tareas.

---

## 4. Ejecución

Los agentes implementan las mejoras.

---

## 5. Validación

Se ejecutan:

- pruebas;
- revisión;
- evaluación de riesgo.

---

## 6. Decisión

El Decision Engine decide:

- aprobar;
- repetir;
- rechazar.

---

## 7. Aprendizaje

Toda la experiencia queda registrada.

---

# Principios

El modo autónomo debe ser:

- incremental;
- reversible;
- seguro;
- explicable;
- controlado.

---

# Modos de Operación

## Manual

El usuario inicia cada acción.

---

## Asistido

El sistema propone cambios y espera aprobación.

---

## Supervisado

El sistema ejecuta automáticamente tareas de bajo riesgo.

Las tareas críticas requieren aprobación humana.

---

## Autónomo

El sistema ejecuta el ciclo completo respetando las políticas configuradas.

---

# Límites de Seguridad

El modo autónomo nunca debe:

- eliminar repositorios;
- sobrescribir ramas protegidas;
- publicar código sin autorización;
- ignorar políticas del Decision Engine.

---

# Registro de Actividad

Cada ciclo produce un informe con:

- tareas ejecutadas;
- agentes participantes;
- decisiones tomadas;
- cambios aplicados;
- pruebas ejecutadas;
- métricas.

---

# Evolución Prevista

## Fase 1

Automatización básica.

---

## Fase 2

Priorización inteligente de tareas.

---

## Fase 3

Aprendizaje continuo.

---

## Fase 4

Optimización basada en experiencia histórica.

---

## Fase 5

Evolución adaptativa.

El sistema ajustará automáticamente:

- prioridades;
- estrategias;
- selección de agentes;
- políticas de ejecución.

---

# Objetivo Final

Construir un sistema capaz de mejorar continuamente un proyecto de software con mínima intervención humana, manteniendo siempre la trazabilidad y el control.

---

# Estado

En evolución continua.
