# QUANT AI Architect — Core Architecture

> Versión: 1.0
> Estado: En construcción
> Última actualización: Agosto 2026

---

# Objetivo

Este documento describe la arquitectura central de QUANT AI Architect.

Su propósito es servir como referencia para comprender cómo interactúan los componentes principales del sistema antes de realizar cualquier refactorización o ampliación funcional.

La arquitectura aquí documentada representa el estado actual del framework y será actualizada durante el proceso de consolidación arquitectónica.

---

# Arquitectura General

Actualmente el framework está organizado alrededor de varios motores especializados (Engines), componentes de orquestación (Orchestrators), módulos de infraestructura y servicios auxiliares.

A grandes rasgos, el flujo de ejecución puede resumirse como:

```
CLI
    │
    ▼
ArchitectEngine / LLMEngine
    │
    ▼
AIArchitect
    │
    ├──────── Analyzer
    ├──────── Planner
    ├──────── Reviewer
    ├──────── Test Runner
    ├──────── Repository
    ├──────── Memory
    └──────── Notifier
```

Este diagrama será refinado durante la auditoría arquitectónica.

---

# Componentes Principales

## Entry Points

Actualmente existen múltiples puntos de entrada:

- architect.py
- cli.py
- main.py

Durante la Fase 6 se consolidarán en un único punto de entrada oficial.

---

## Engines

Motores principales detectados:

- ArchitectEngine
- LLMEngine
- MemoryEngine
- KnowledgeEngine
- AutonomousEngine
- DevelopmentEngine

La relación entre ellos será documentada individualmente.

---

## Orquestadores

Componentes responsables de coordinar procesos:

- AIArchitect
- LLMWorkflow
- SmartEditor
- Pipeline
- Orchestrator

---

## Infraestructura

Los servicios de infraestructura incluyen:

- Repository
- Memory
- Providers
- Decision Engine
- Notifier
- Workspace
- Scheduler

---

# Dominios

El proyecto está dividido en los siguientes dominios funcionales:

- agents
- analyzer
- autonomous
- changelog
- config
- core
- decision_engine
- execution
- filesystem
- git
- logger
- memory
- notifier
- patch_generator
- planner
- providers
- repository
- reviewer
- rules
- scheduler
- swarm
- testing
- test_runner
- workflows
- workspace

---

# Estado actual

Fortalezas

- Separación clara por dominios.
- Alto nivel de modularización.
- Arquitectura preparada para múltiples proveedores LLM.
- Sistema de memoria desacoplado.

Aspectos a consolidar

- Multiplicidad de puntos de entrada.
- Duplicidad de motores.
- Duplicidad de pipelines.
- Contextos independientes.
- Responsabilidades parcialmente superpuestas.

---

# Objetivos de Consolidación

Las siguientes fases buscarán:

- unificar la arquitectura;
- reducir duplicidad;
- simplificar el flujo de ejecución;
- mejorar mantenibilidad;
- facilitar la incorporación de nuevos módulos.

---

# Referencias

Ver también:

- ENTRY_POINTS.md
- ENGINES.md
- MODULES.md
- EXECUTION_FLOW.md
- TECHNICAL_DEBT.md
