# QUANT AI Architect — Engines

> Estado: En construcción
> Última actualización: Agosto 2026

---

# Objetivo

Este documento describe todos los motores (Engines) del framework.

Cada Engine representa un componente de alto nivel encargado de coordinar un dominio específico del sistema.

Su documentación permite:

- comprender responsabilidades;
- detectar duplicidades;
- definir futuras consolidaciones;
- facilitar la incorporación de nuevos motores.

---

# Arquitectura General

Actualmente se identifican los siguientes motores:

```
                +----------------+
                | ArchitectEngine|
                +--------+-------+
                         |
                         |
                 +-------v------+
                 | AIArchitect  |
                 +-------+------+
                         |
        -----------------------------------------
        |         |         |         |          |
   Analyzer   Planner   Reviewer   Tests   Repository
```

De forma paralela existe un segundo flujo basado en LLM:

```
LLMEngine
      │
      ▼
LLMWorkflow
      │
      ▼
SmartEditor
      │
ExecutionPipeline
```

Durante la consolidación arquitectónica ambos flujos serán evaluados para determinar si deben coexistir o integrarse.

---

# ArchitectEngine

## Archivo

```
engine.py
```

## Estado

Activo

## Responsabilidad

Motor principal del framework clásico.

Coordina la ejecución de:

- análisis;
- planificación;
- pruebas;
- notificaciones.

## Dependencias

- AIArchitect
- NotificationLevel

## Flujo

```
ArchitectEngine

        │

        ▼

AIArchitect

        │

 ├── analyze()

 ├── plan()

 ├── run_tests()

 └── notifier
```

## Observaciones

Actualmente no utiliza directamente el sistema basado en LLM.

---

# LLMEngine

## Archivo

```
llm/llm_engine.py
```

## Estado

Activo

## Responsabilidad

Motor especializado para operaciones asistidas por modelos de lenguaje.

## Coordina

- LLMWorkflow

## Funciones públicas

- improve()
- review()
- refactor()

## Flujo

```
LLMEngine

      │

      ▼

LLMWorkflow

      │

      ▼

SmartEditor
```

## Observaciones

Representa una arquitectura paralela al flujo clásico.

Será evaluada para una posible integración con ArchitectEngine.

---

# MemoryEngine

## Archivo

```
memory/memory_engine.py
```

## Estado

Activo

## Responsabilidad

Coordinador central del subsistema de memoria.

## Coordina

- ExperienceStore
- LearningEngine
- PatternMiner
- VectorMemory
- KnowledgeGraph

## Capacidades

- almacenamiento persistente;
- aprendizaje;
- minería de patrones;
- memoria vectorial;
- estadísticas.

---

# KnowledgeEngine

## Archivo

```
knowledge/knowledge_engine.py
```

## Estado

Pendiente de auditoría

## Responsabilidad

Gestionar el conocimiento estructural del proyecto.

## Observaciones

Será documentado durante la auditoría del módulo Knowledge.

---

# AutonomousEngine

## Archivo

```
autonomous/autonomous_engine.py
```

## Estado

Pendiente de auditoría

## Objetivo

Automatizar ciclos completos de ejecución.

---

# DevelopmentEngine

## Archivo

```
development_loop/development_engine.py
```

## Estado

Pendiente de auditoría

## Objetivo

Gestionar ciclos continuos de mejora del proyecto.

---

# Comparativa

| Engine | Dominio | Estado |
|---------|----------|--------|
| ArchitectEngine | Framework clásico | Activo |
| LLMEngine | IA / LLM | Activo |
| MemoryEngine | Memoria | Activo |
| KnowledgeEngine | Conocimiento | Auditoría |
| AutonomousEngine | Automatización | Auditoría |
| DevelopmentEngine | Mejora continua | Auditoría |

---

# Posibles Consolidaciones

Durante la Fase 6 se evaluará:

- mantener múltiples motores especializados;
- introducir un SuperEngine;
- unificar el flujo de ejecución.

No se tomarán decisiones hasta finalizar la auditoría completa.

---

# Referencias

- CORE_ARCHITECTURE.md
- ENTRY_POINTS.md
- EXECUTION_FLOW.md
