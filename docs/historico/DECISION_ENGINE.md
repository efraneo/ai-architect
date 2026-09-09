# QUANT AI Architect — Decision Engine

> Estado: Diseño Institucional
> Versión: 1.0

> **Lo que quedó en pie:** `DecisionEngine` -> `AutoDecision` encadena
> calidad, riesgo, confianza, puntuación y política, sobre un
> `AIContext` de `core/`. Se podó `decision_context.py`, que duplicaba
> ese `AIContext` sin que nadie lo usara.

---

# Objetivo

El Decision Engine es el responsable de evaluar la calidad de una modificación antes de permitir su integración en el proyecto.

Su propósito es evitar que cambios generados automáticamente degraden el código.

---

# Filosofía

El modelo de lenguaje nunca toma la decisión final.

Siempre existe una capa independiente que analiza:

- calidad;
- riesgo;
- confianza;
- políticas;
- pruebas.

Solo entonces se decide si un cambio será aceptado.

---

# Arquitectura

```
AI Context

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

# Componentes

## AutoDecision

Responsabilidad:

Coordinar el proceso completo de evaluación.

Pipeline:

```
Context

↓

Quality

↓

Risk

↓

Confidence

↓

Score

↓

Policy

↓

Decision
```

Es la fachada pública del subsistema.

---

## QualityScore

Responsabilidad:

Evaluar la calidad del cambio.

Indicadores posibles:

- complejidad;
- duplicación;
- tamaño;
- mantenibilidad;
- estilo;
- deuda técnica.

Resultado:

QualityAssessment

---

## RiskEngine

Responsabilidad:

Estimar el riesgo del cambio.

Factores considerados:

- archivos críticos;
- impacto arquitectónico;
- cambios masivos;
- módulos sensibles;
- dependencias.

Resultado:

RiskAssessment

---

## ConfidenceEngine

Responsabilidad:

Calcular la confianza de la modificación.

Entradas:

- calidad;
- riesgo;
- contexto.

Resultado:

ConfidenceAssessment

---

## ScoringEngine

Responsabilidad:

Generar una puntuación global.

Entradas:

- calidad;
- confianza;
- riesgo.

Resultado:

ScoreAssessment

---

## ExecutionPolicy

Responsabilidad:

Aplicar las políticas institucionales.

Decide:

- aprobar;
- rechazar;
- solicitar revisión;
- reintentar.

---

# Flujo Completo

```
AIContext

↓

Quality Assessment

↓

Risk Assessment

↓

Confidence Assessment

↓

Score Assessment

↓

Execution Policy

↓

Decision Report
```

---

# Modelo de Evaluación

Cada modificación recibe una evaluación basada en cuatro dimensiones.

## Calidad

Pregunta:

> ¿El cambio mejora el código?

---

## Riesgo

Pregunta:

> ¿Puede romper el sistema?

---

## Confianza

Pregunta:

> ¿Qué tan confiable es esta propuesta?

---

## Score

Pregunta:

> ¿Cuál es la valoración global?

---

# Posibles Decisiones

```
APPROVED

REVIEW

RETRY

REJECTED
```

---

## APPROVED

El cambio puede aplicarse automáticamente.

---

## REVIEW

Requiere intervención humana.

---

## RETRY

Se solicita una nueva generación del cambio.

---

## REJECTED

El cambio no debe continuar.

---

# Reporte Final

El Decision Report incluye:

```
decision

approved

reason

quality

risk

confidence

score
```

---

# Criterios de Evaluación

## Calidad

- complejidad
- duplicación
- cobertura
- estilo
- arquitectura

---

## Riesgo

- archivos críticos
- dependencias
- impacto
- tamaño del cambio

---

## Confianza

- historial previo
- proveedor utilizado
- experiencia similar
- estabilidad

---

## Score

Combinación ponderada de:

```
Quality

+

Confidence

-

Risk
```

---

# Uso dentro del Pipeline

```
LLM

↓

Generated Code

↓

Patch Validation

↓

Decision Engine

↓

Repository
```

Sin aprobación del Decision Engine ningún cambio llega al repositorio.

---

# Objetivos

Garantizar que:

- las mejoras realmente mejoren;
- los cambios peligrosos sean bloqueados;
- exista trazabilidad;
- todas las decisiones sean auditables.

---

# Evolución Prevista

Fase 1

Evaluación basada en reglas.

---

Fase 2

Aprendizaje a partir de experiencias previas.

---

Fase 3

Ajuste dinámico de umbrales.

---

Fase 4

Consenso entre múltiples motores de decisión.

---

Fase 5

Autoajuste mediante aprendizaje continuo.

---

# Principios

El Decision Engine debe ser:

- independiente del LLM;
- determinista;
- explicable;
- auditable;
- extensible.

---

# Estado

En evolución continua.
