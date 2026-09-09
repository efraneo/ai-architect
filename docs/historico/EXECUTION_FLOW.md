# QUANT AI Architect — Execution Flow

> Estado: Auditoría Arquitectónica
> Versión: 1.0

> **Lo que quedó en pie:** la cadena conectada es
> `ExecutionEngine` -> `ExecutionPipeline` -> `pipeline_state`, que es
> por donde pasa `architect execute`. Se podó la mitad huérfana
> (`ExecutionOrchestrator`, `TaskExecutor`, `ExecutionResult`,
> `ExecutionTask`, `ExecutionContext`, `RepositoryMetrics` y un
> `__main__` que duplicaba el comando): el orquestador esperaba tareas
> con `metadata["file"]` apuntando a un parche, y el `Planner` no
> produce eso — al correrlo con un plan real moría con
> `Permission denied: '.'` en la primera tarea.
> Para ejecutar varias mejoras en orden está `architect auto`.

---

# Objetivo

Describir el recorrido completo que realiza una solicitud desde su entrada al framework hasta la finalización del proceso.

Este documento constituye la referencia principal para comprender el comportamiento global del sistema.

---

# Visión General

Actualmente existen dos grandes flujos de ejecución.

```
                    Usuario
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      ArchitectEngine         LLMEngine
            │                     │
            ▼                     ▼
       AIArchitect          LLMWorkflow
            │                     │
            └──────────┬──────────┘
                       ▼
                Servicios internos
```

---

# Flujo Clásico

```
Usuario

    │

    ▼

ArchitectEngine

    │

    ▼

AIArchitect

    │

    ├──────── analyze()

    ├──────── plan()

    ├──────── run_tests()

    └──────── notifier()

    │

    ▼

Resultado
```

---

# Flujo basado en LLM

```
Usuario

      │

      ▼

LLMEngine

      │

      ▼

LLMWorkflow

      │

      ▼

SmartEditor

      │

      ▼

ExecutionPipeline

      │

      ▼

Repository Scanner

      │

      ▼

Prompt Builder

      │

      ▼

Provider Manager

      │

      ▼

LLM Provider

      │

      ▼

Generated Code

      │

      ▼

Patch Validation

      │

      ▼

Decision Engine

      │

      ▼

Commit

      │

      ▼

Memory

      │

      ▼

Notification
```

---

# Flujo de Mejora Automática

Cuando se ejecuta:

```
improve
```

el framework sigue el siguiente recorrido:

```
LLMEngine

↓

LLMWorkflow

↓

SmartEditor

↓

ExecutionPipeline

↓

Repository Context

↓

Prompt Builder

↓

Provider

↓

Generated Source

↓

Code Editor

↓

Diff

↓

Decision Engine

↓

Commit Manager

↓

Memory Engine

↓

Notifier
```

---

# Flujo de Memoria

```
Experience

      │

      ▼

ExperienceStore

      │

      ▼

Learning Engine

      │

      ▼

Pattern Miner

      │

      ▼

Knowledge Graph

      │

      ▼

Vector Memory
```

---

# Flujo de Decisión

```
AIContext

      │

      ▼

Quality Score

      │

      ▼

Risk Engine

      │

      ▼

Confidence Engine

      │

      ▼

Scoring Engine

      │

      ▼

Execution Policy

      │

      ▼

Decision Report
```

---

# Flujo de Providers

```
Prompt

    │

    ▼

ProviderManager

    │

    ▼

ProviderFactory

    │

    ├──────── OpenAI

    ├──────── Claude

    ├──────── Gemini

    ├──────── Ollama

    └──────── OpenRouter

            │

            ▼

      LLM Response
```

---

# Flujo de Repository

```
Repository

      │

      ▼

RepositoryManager

      │

      ├──── GitManager

      ├──── BranchManager

      ├──── DiffManager

      ├──── CommitManager

      └──── TagManager
```

---

# Flujo de Planner

```
Project Analysis

        │

        ▼

Planner

        │

        ▼

Dependency Builder

        │

        ▼

Architecture Builder

        │

        ▼

Testing Builder

        │

        ▼

Security Builder

        │

        ▼

Execution Plan
```

---

# Flujo Esperado (Objetivo Arquitectónico)

Después de la consolidación, el framework debería seguir un único recorrido principal:

```
CLI

 │

 ▼

ArchitectEngine

 │

 ▼

Execution Orchestrator

 │

 ▼

Analysis

 │

 ▼

Planning

 │

 ▼

Decision

 │

 ▼

LLM

 │

 ▼

Validation

 │

 ▼

Repository

 │

 ▼

Memory

 │

 ▼

Notification
```

---

# Observaciones

Durante la auditoría se detectaron varios recorridos parcialmente duplicados.

Las próximas fases buscarán:

- reducir bifurcaciones;
- eliminar caminos paralelos;
- centralizar la orquestación;
- unificar la lógica de ejecución.

---

# Estado

En revisión continua.
