# QUANT AI Architect — Knowledge System

> Estado: Diseño Institucional
> Versión: 1.0

> **Dónde vive esto hoy:** el paquete `knowledge/` se podó. Sus
> constructores de grafos recorrían el árbol con `rglob` pelado —
> mirando dentro del `.venv` — y `DependencyGraph` reventaba con un
> solo archivo que no compilara; la "búsqueda semántica" era un
> `in` de subcadenas y los "embeddings", hashes.
> Lo cubren `analyzer/` (dependencias, estructura, complejidad) y
> `memory/knowledge_graph.py` (nodos y relaciones), ambos conectados.
> `dependency_index.py`, que era el único módulo vivo de allí, se
> mudó a `analyzer/`, junto a su consumidor.

---

# Objetivo

El Knowledge System mantiene una representación estructurada y persistente del conocimiento del proyecto.

Su propósito es transformar un conjunto de archivos fuente en un modelo semántico que permita razonar sobre la arquitectura, las dependencias y la evolución del software.

---

# Filosofía

El código fuente es únicamente la representación física del sistema.

El Knowledge System construye una representación lógica.

Esta representación permite responder preguntas como:

- ¿Cómo está organizada la arquitectura?
- ¿Qué módulos dependen entre sí?
- ¿Qué archivos cambian juntos?
- ¿Qué componentes son críticos?
- ¿Qué impacto tendrá una modificación?

---

# Arquitectura General

```
Repository

↓

Project Scanner

↓

File Graph

↓

Dependency Graph

↓

Architecture Graph

↓

Knowledge Base

↓

Semantic Search

↓

Vector Memory

↓

Agents
```

---

# Componentes

## Repository Scanner

Responsabilidad

Recorrer completamente el proyecto.

Obtiene:

- archivos;
- directorios;
- extensiones;
- metadatos.

---

## File Graph

Representa todos los archivos del proyecto.

Cada nodo contiene información como:

- ruta;
- lenguaje;
- tamaño;
- hash;
- fecha de modificación.

---

## Dependency Graph

Representa las relaciones entre módulos.

Ejemplos:

```
planner

↓

execution

↓

repository
```

Permite detectar:

- ciclos;
- acoplamiento;
- dependencias críticas.

---

## Architecture Graph

Describe la organización lógica del proyecto.

Ejemplo:

```
Presentation

↓

Application

↓

Domain

↓

Infrastructure
```

No depende del lenguaje de programación.

---

## Project Graph

Integra toda la información del repositorio en un único grafo.

Contiene:

- módulos;
- clases;
- funciones;
- dependencias;
- relaciones arquitectónicas.

---

## Knowledge Base

Repositorio central del conocimiento estructurado.

Incluye:

- reglas;
- métricas;
- decisiones;
- historial;
- relaciones.

---

## Semantic Search

Permite buscar por significado y no únicamente por texto.

Ejemplos:

```
"gestión de ramas"

↓

RepositoryManager

BranchManager

GitManager
```

---

## Embeddings

Transforman el contenido del proyecto en vectores semánticos.

Permiten:

- búsqueda contextual;
- similitud;
- recuperación inteligente.

---

## Vector Memory

Almacena representaciones vectoriales del conocimiento.

Facilita:

- recuperación rápida;
- comparación semántica;
- reutilización de contexto.

---

## Project Snapshot

Captura el estado completo del proyecto en un instante determinado.

Incluye:

- estructura;
- métricas;
- dependencias;
- arquitectura.

Permite comparar versiones.

---

# Flujo General

```
Repository

↓

Scanner

↓

Graphs

↓

Knowledge Base

↓

Embeddings

↓

Semantic Search

↓

Agents
```

---

# Casos de Uso

## Impact Analysis

Antes de modificar un archivo, el sistema identifica los componentes afectados.

---

## Context Building

Los agentes reciben únicamente el contexto relevante.

---

## Navegación Inteligente

El sistema puede localizar automáticamente:

- clases relacionadas;
- módulos equivalentes;
- implementaciones similares.

---

## Arquitectura

Permite validar que el proyecto siga las reglas arquitectónicas definidas.

---

# Integración

```
Knowledge System

↓

Memory Engine

↓

Decision Engine

↓

Swarm

↓

LLM Context Builder
```

El conocimiento generado puede ser utilizado por cualquier componente del framework.

---

# Beneficios

- comprensión estructural del proyecto;
- reducción del contexto enviado al LLM;
- análisis de impacto;
- navegación inteligente;
- mayor precisión en las decisiones.

---

# Evolución Prevista

## Fase 1

Escaneo del repositorio.

---

## Fase 2

Grafos de dependencias.

---

## Fase 3

Embeddings semánticos.

---

## Fase 4

Knowledge Graph unificado.

---

## Fase 5

Razonamiento sobre arquitectura.

El sistema será capaz de responder preguntas complejas sobre el proyecto utilizando su representación interna del conocimiento.

---

# Principios

El Knowledge System debe ser:

- incremental;
- persistente;
- extensible;
- independiente del proveedor LLM;
- reutilizable.

---

# Estado

En evolución continua.
