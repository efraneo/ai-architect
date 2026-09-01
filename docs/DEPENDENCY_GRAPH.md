# QUANT AI Architect — Dependency Graph

> Estado: Auditoría Arquitectónica
> Versión: 1.0

---

# Objetivo

Este documento describe las dependencias entre los principales módulos del framework.

Permite identificar:

- acoplamientos fuertes;
- dependencias circulares;
- módulos centrales;
- candidatos a refactorización;
- puntos de expansión.

---

# Arquitectura General

```
                           CLI
                            │
                            ▼
                    ArchitectEngine
                            │
                            ▼
                      AIArchitect
                            │
     ┌──────────────────────┼──────────────────────┐
     ▼                      ▼                      ▼
 Analyzer               Planner              TestRunner
     │                      │                      │
     └──────────────┬───────┴──────────────┬───────┘
                    ▼                      ▼
              Repository             Reviewer
                    │
                    ▼
              Notification
```

---

# Arquitectura LLM

```
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
ProviderManager
      │
      ▼
ProviderFactory
      │
      ▼
OpenAI / Claude / Gemini / Ollama / OpenRouter
```

---

# Dependencias Principales

## ArchitectEngine

Depende de:

- AIArchitect
- NotificationLevel

No debería depender de:

- Providers
- LLM
- Memory

---

## AIArchitect

Depende de:

- analyzer
- planner
- reviewer
- repository
- notifier
- test_runner

No debería depender de:

- cli
- app
- engine

---

## LLMEngine

Depende de:

- LLMWorkflow

---

## LLMWorkflow

Depende de:

- SmartEditor

---

## SmartEditor

Depende de:

- ExecutionPipeline
- CodeEditor
- DecisionEngine
- MemoryEngine
- CommitManager
- DiffManager
- NotifierManager

Es uno de los módulos con mayor nivel de acoplamiento.

---

## ExecutionPipeline

Depende de:

- RepositoryScanner
- PromptBuilder
- ProviderManager
- PatchValidator

---

## ProviderManager

Depende de:

- ProviderFactory
- BaseProvider

---

## ProviderFactory

Depende de:

- OpenAIProvider
- ClaudeProvider
- GeminiProvider
- OllamaProvider
- OpenRouterProvider

---

## MemoryEngine

Depende de:

- ExperienceStore
- LearningEngine
- PatternMiner
- VectorMemory
- KnowledgeGraph

---

## Decision Engine

Depende de:

- QualityScore
- RiskEngine
- ConfidenceEngine
- ScoringEngine
- ExecutionPolicy

---

## Repository

Depende de:

- GitManager
- CommitManager
- BranchManager
- DiffManager
- TagManager

---

# Dependencias entre módulos

| Módulo | Depende de |
|---------|------------|
| agents | analyzer, planner, repository |
| analyzer | core |
| planner | analyzer |
| execution | planner, repository |
| llm | providers, repository, memory |
| providers | configuración |
| memory | core |
| repository | git |
| reviewer | analyzer |
| notifier | config |

---

# Módulos Críticos

Los siguientes módulos son utilizados por múltiples componentes y deben mantenerse estables:

- core
- repository
- providers
- memory
- decision_engine

---

# Posibles Dependencias Circulares

Durante la auditoría deberán verificarse:

- llm ↔ decision_engine
- llm ↔ repository
- planner ↔ analyzer
- execution ↔ planner

Actualmente no se han confirmado ciclos, pero requieren revisión.

---

# Riesgos de Acoplamiento

## SmartEditor

Alto nivel de acoplamiento.

Responsabilidades actuales:

- edición;
- validación;
- memoria;
- commits;
- notificaciones;
- decisiones.

Se recomienda dividir responsabilidades en futuras fases.

---

## AIArchitect

Coordina numerosos subsistemas.

Debe mantenerse como fachada, evitando incorporar lógica de negocio adicional.

---

## ProviderFactory

Actualmente importa todos los proveedores directamente.

En el futuro podría evolucionar hacia un sistema de registro dinámico (plugin registry) para evitar dependencias innecesarias.

---

# Objetivos de Refactorización

Durante las siguientes fases se buscará:

- reducir acoplamiento;
- eliminar dependencias innecesarias;
- introducir inversión de dependencias;
- desacoplar infraestructura del dominio;
- facilitar pruebas unitarias mediante interfaces.

---

# Estado

Documento vivo.

Se actualizará conforme evolucione la arquitectura.
