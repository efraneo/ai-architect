# QUANT AI Architect — Memory Architecture

> Estado: Diseño Institucional
> Versión: 1.0

---

# Objetivo

El subsistema de memoria permite que QUANT AI Architect conserve experiencias, detecte patrones y mejore continuamente su comportamiento.

La memoria constituye uno de los pilares de la arquitectura institucional.

---

# Filosofía

Cada ejecución debe producir conocimiento.

El sistema no solo genera código; también aprende de:

- éxitos;
- errores;
- decisiones;
- revisiones;
- resultados de pruebas;
- cambios realizados.

---

# Arquitectura General

```
                Execution
                    │
                    ▼
             MemoryEngine
                    │
    ┌───────────────┼───────────────┐
    ▼               ▼               ▼
ExperienceStore LearningEngine PatternMiner
    │               │               │
    └───────────────┼───────────────┘
                    ▼
             KnowledgeGraph
                    │
                    ▼
              VectorMemory
```

---

# Componentes

## MemoryEngine

Responsabilidad:

Coordinar todos los servicios de memoria.

Funciones principales:

- remember()
- snapshot()
- refresh()
- recommendations()
- similar()
- statistics()
- clear()

Es la única fachada utilizada por el resto del sistema.

---

## ExperienceStore

Responsabilidad:

Persistencia de experiencias.

Actualmente utiliza almacenamiento JSON.

Responsabilidades:

- guardar;
- cargar;
- limpiar;
- consultar;
- recuperar historial.

Backends previstos:

- SQLite
- PostgreSQL
- ChromaDB
- LanceDB
- Milvus
- Weaviate

---

## JsonMemoryBackend

Responsabilidad:

Implementación actual del almacenamiento.

Ventajas:

- simple;
- legible;
- sin dependencias;
- ideal para desarrollo.

Limitaciones:

- poca escalabilidad;
- acceso secuencial;
- sin concurrencia.

---

## LearningEngine

Responsabilidad:

Extraer conocimiento a partir de las experiencias almacenadas.

Genera:

- patrones;
- recomendaciones;
- indicadores de aprendizaje.

---

## PatternMiner

Responsabilidad:

Detectar patrones repetitivos.

Ejemplos:

- errores frecuentes;
- módulos problemáticos;
- instrucciones exitosas;
- tipos de refactorización comunes.

---

## KnowledgeGraph

Responsabilidad:

Representar relaciones entre entidades.

Ejemplos:

- archivos;
- módulos;
- componentes;
- dependencias;
- decisiones.

Objetivo futuro:

Permitir razonamiento sobre el proyecto.

---

## VectorMemory

Responsabilidad:

Búsqueda semántica.

Permite localizar experiencias similares mediante embeddings.

Casos de uso:

- reutilizar soluciones;
- comparar problemas;
- sugerir mejoras.

---

# Modelo de Datos

Cada experiencia contiene información como:

```
Experience

• id
• repository
• filename
• instruction
• provider
• experience_type
• outcome
• confidence
• score
• risk
• metadata
• created_at
```

---

# Flujo de Aprendizaje

```
Execution

↓

Experience

↓

ExperienceStore

↓

LearningEngine

↓

PatternMiner

↓

KnowledgeGraph

↓

Recommendations
```

---

# Flujo de Búsqueda

```
Embedding

↓

VectorMemory

↓

Similarity Search

↓

Previous Experiences

↓

Recommendation
```

---

# Ciclo de Actualización

```
remember()

↓

append()

↓

refresh()

↓

learn()

↓

save()

↓

ready
```

---

# Objetivos

La memoria debe responder preguntas como:

- ¿Qué cambios fueron exitosos?
- ¿Qué instrucciones fallan con frecuencia?
- ¿Qué módulos presentan mayor riesgo?
- ¿Qué soluciones ya existen?
- ¿Qué decisiones produjeron mejores resultados?

---

# Estadísticas

El sistema puede informar:

- número de experiencias;
- patrones detectados;
- nodos del grafo;
- relaciones;
- vectores almacenados.

---

# Evolución Prevista

Fases futuras:

## Fase 1

Persistencia JSON.

## Fase 2

SQLite.

## Fase 3

Base vectorial.

## Fase 4

Memoria distribuida.

## Fase 5

Aprendizaje entre proyectos.

---

# Principios

La memoria debe ser:

- persistente;
- auditable;
- desacoplada;
- extensible;
- independiente del proveedor LLM.

---

# Estado

En evolución continua.
