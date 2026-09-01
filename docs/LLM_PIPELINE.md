# QUANT AI Architect — LLM Pipeline

> Estado: Diseño Institucional
> Versión: 1.0

---

# Objetivo

Este documento describe el funcionamiento interno del pipeline basado en modelos de lenguaje (LLM).

El pipeline transforma una instrucción del usuario en modificaciones reales del código mediante un flujo controlado, validado y auditable.

---

# Visión General

```
Usuario
    │
    ▼
CLI / API
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
Context Builder
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
Patch Validator
    │
    ▼
Decision Engine
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

# Componentes

## 1. LLMEngine

Responsabilidad:

Punto de entrada para todas las operaciones basadas en IA.

Funciones:

- improve()
- review()
- refactor()

No contiene lógica de edición.

Actúa únicamente como fachada.

---

## 2. LLMWorkflow

Responsabilidad:

Coordinar el flujo completo.

Delega la ejecución hacia SmartEditor.

En el futuro permitirá múltiples workflows especializados:

- review
- migrate
- generate
- document
- refactor

---

## 3. SmartEditor

Responsabilidad:

Motor principal de edición inteligente.

Coordina:

- ExecutionPipeline
- CodeEditor
- DecisionEngine
- MemoryEngine
- DiffManager
- CommitManager
- NotifierManager

Es actualmente el componente más importante del pipeline.

---

## 4. ExecutionPipeline

Responsabilidad:

Transformar una instrucción en código generado.

Subprocesos:

```
Instruction

↓

Repository Context

↓

Prompt

↓

LLM

↓

Generated Source
```

---

## 5. Repository Scanner

Responsabilidad:

Analizar el proyecto.

Extrae:

- archivos relevantes;
- dependencias;
- estructura;
- contexto.

---

## 6. Context Builder

Responsabilidad:

Construir el contexto enviado al modelo.

Incluye:

- imports;
- dependencias;
- clases;
- funciones;
- historial.

---

## 7. Prompt Builder

Responsabilidad:

Construir prompts institucionales.

Debe garantizar:

- consistencia;
- contexto suficiente;
- instrucciones claras;
- formato controlado.

---

## 8. Provider Manager

Responsabilidad:

Seleccionar el proveedor activo.

Actualmente soporta:

- OpenAI
- Claude
- Gemini
- Ollama
- OpenRouter

---

## 9. Provider Factory

Responsabilidad:

Crear dinámicamente el proveedor configurado.

Idealmente deberá evolucionar hacia un sistema basado en plugins.

---

## 10. LLM Provider

Responsabilidad:

Comunicación directa con el modelo.

Entrada:

Prompt

Salida:

Código generado

---

## 11. Patch Validator

Responsabilidad:

Validar que la respuesta del modelo sea aplicable.

Debe detectar:

- errores de sintaxis;
- archivos inexistentes;
- respuestas incompletas;
- modificaciones peligrosas.

---

## 12. Decision Engine

Responsabilidad:

Determinar si el cambio puede aceptarse.

Evalúa:

- riesgo;
- calidad;
- confianza;
- políticas;
- pruebas.

---

## 13. Repository Layer

Responsabilidad:

Aplicar cambios al repositorio.

Incluye:

- diff;
- commit;
- branch;
- tags.

---

## 14. Memory Engine

Responsabilidad:

Registrar la experiencia obtenida.

Almacena:

- éxito;
- fracaso;
- confianza;
- métricas;
- patrones.

---

## 15. Notifier

Responsabilidad:

Informar el resultado.

Actualmente:

- Telegram

Futuro:

- Slack
- Discord
- Email

---

# Flujo Completo

```
Instruction

↓

Analyze Repository

↓

Build Context

↓

Build Prompt

↓

Generate Code

↓

Validate

↓

Evaluate Risk

↓

Decision

↓

Write File

↓

Commit

↓

Learn

↓

Notify
```

---

# Estados del Pipeline

```
Idle

↓

Preparing

↓

Scanning

↓

Context

↓

Generating

↓

Validating

↓

Decision

↓

Writing

↓

Commit

↓

Completed
```

---

# Manejo de Errores

Errores posibles:

- proveedor no disponible;
- prompt inválido;
- respuesta vacía;
- código inválido;
- fallo de validación;
- fallo de commit;
- fallo de notificación.

Cada error debe producir un reporte estructurado.

---

# Evolución Futura

Se prevé incorporar:

- múltiples modelos simultáneos;
- consenso entre modelos;
- generación incremental;
- planificación jerárquica;
- revisión automática;
- aprendizaje continuo.

---

# Objetivo Final

Convertir el pipeline en un sistema desacoplado, extensible y preparado para ejecutar tareas complejas de desarrollo de software de forma autónoma.

---

# Estado

En evolución continua.
