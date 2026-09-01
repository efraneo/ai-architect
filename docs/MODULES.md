# QUANT AI Architect — Modules

> Estado: Auditoría Arquitectónica
> Última actualización: Agosto 2026

---

# Objetivo

Este documento describe todos los módulos que conforman QUANT AI Architect.

Cada módulo representa un dominio funcional del framework.

La finalidad de este documento es:

- comprender responsabilidades;
- identificar dependencias;
- detectar duplicidad;
- facilitar futuras refactorizaciones.

---

# Visión General

Actualmente el framework contiene aproximadamente 30 módulos principales.

```
ai_architect/

├── agents
├── analyzer
├── autonomous
├── changelog
├── config
├── core
├── decision_engine
├── execution
├── filesystem
├── git
├── logger
├── memory
├── notifier
├── patch_generator
├── planner
├── providers
├── repository
├── reviewer
├── rules
├── scheduler
├── swarm
├── testing
├── test_runner
├── workflows
└── workspace
```

---

# agents

## Objetivo

Contiene los agentes especializados.

## Responsabilidades

- arquitectura
- backend
- seguridad
- documentación
- testing
- git
- performance
- machine learning
- project manager
- refactoring
- trading

## Estado

Muy grande.

Será dividido por dominios internos.

---

# analyzer

## Objetivo

Analizar el proyecto.

## Componentes

- ProjectAnalyzer
- DependencyAnalyzer
- ComplexityAnalyzer
- DuplicateDetector

## Estado

Muy sólido.

---

# autonomous

## Objetivo

Automatización completa del framework.

## Componentes

- AutonomousEngine
- ExecutionWorker
- RollbackManager
- MergeManager
- ApprovalEngine

## Estado

Pendiente de auditoría.

---

# changelog

## Objetivo

Gestión del historial del proyecto.

---

# config

## Objetivo

Configuración global.

Actualmente contiene:

- Settings

En el futuro contendrá:

- perfiles
- proveedores
- políticas
- configuración dinámica

---

# core

## Objetivo

Tipos fundamentales del framework.

Contiene:

- Result
- Context
- Metadata
- Exceptions
- Events
- Contracts
- Enums

Debe mantenerse extremadamente estable.

---

# decision_engine

## Objetivo

Sistema institucional de toma de decisiones.

Componentes principales:

- AutoDecision
- RiskEngine
- ConfidenceEngine
- QualityScore
- ExecutionPolicy
- ScoringEngine

---


## Objetivo

Ciclos continuos de mejora.

---

# execution

## Objetivo

Modelo general de ejecución.

---

# filesystem

## Objetivo

Acceso seguro al sistema de archivos.

---

# git

## Objetivo

Abstracción de Git.

---


## Objetivo

Base de conocimiento del framework.

Incluye:

- Graphs
- Embeddings
- Semantic Search

---


## Objetivo

Subsistema completo de IA.

Componentes:

- LLMEngine
- SmartEditor
- Workflow
- PromptBuilder
- CodeGenerator
- RepositoryScanner
- PlannerAgent

Actualmente representa uno de los módulos más importantes.

---

# logger

## Objetivo

Registro de eventos.

---

# memory

## Objetivo

Sistema de memoria institucional.

Incluye:

- Experience Store

- Learning Engine

- Pattern Miner

- Vector Memory

- Knowledge Graph

---

# notifier

## Objetivo

Notificaciones externas.

Actualmente:

- Telegram

Futuro:

- Slack

- Discord

- Email

---

# patch_generator

## Objetivo

Generación de parches.

---

# planner

## Objetivo

Planificación de tareas.

---

# providers

## Objetivo

Abstracción de proveedores LLM.

Actualmente soporta:

- OpenAI

- Claude

- Gemini

- Ollama

- OpenRouter

---

# repository

## Objetivo

Gestión del repositorio Git.

---

# reviewer

## Objetivo

Revisión de código.

---

# rules

## Objetivo

Políticas institucionales.

Incluye:

- arquitectura

- revisión

- estilo

---

# scheduler

## Objetivo

Planificación de trabajos.

---


## Objetivo

Auto-mejora del framework.

---

# swarm

## Objetivo

Coordinación multiagente.

---

# testing

## Objetivo

Control de calidad.

---

# test_runner

## Objetivo

Ejecución de pruebas.

---

# workflows

## Objetivo

Pipelines reutilizables.

---

# workspace

## Objetivo

Gestión del espacio de trabajo.

---

# Resumen

| Módulo | Estado |
|---------|---------|
| agents | Muy grande |
| analyzer | Estable |
| autonomous | Auditoría |
| changelog | Estable |
| config | Estable |
| core | Crítico |
| decision_engine | Muy sólido |
| execution | Auditoría |
| filesystem | Estable |
| git | Estable |
| logger | Estable |
| memory | Muy importante |
| notifier | Estable |
| patch_generator | Auditoría |
| planner | Muy sólido |
| providers | Muy sólido |
| repository | Estable |
| reviewer | Estable |
| rules | Estable |
| scheduler | Auditoría |
| swarm | Experimental |
| testing | Estable |
| test_runner | Estable |
| workflows | Auditoría |
| workspace | Estable |

---

# Próximas auditorías

Cada módulo contará posteriormente con su propia documentación técnica detallada.
