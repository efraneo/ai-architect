# QUANT AI Architect — Providers Architecture

> Estado: Diseño Institucional
> Versión: 1.0

---

# Objetivo

El subsistema Providers abstrae la comunicación con modelos de lenguaje (LLM), permitiendo cambiar de proveedor sin modificar la lógica del framework.

La arquitectura sigue el principio de inversión de dependencias y desacopla la infraestructura del dominio.

---

# Filosofía

El resto del sistema nunca debe conocer la implementación específica de un proveedor.

Los componentes superiores interactúan únicamente con una interfaz común.

Esto permite:

- cambiar de proveedor sin modificar el código del negocio;
- incorporar nuevos modelos fácilmente;
- ejecutar distintos proveedores según la configuración;
- facilitar pruebas y simulaciones.

---

# Arquitectura General

```
                 LLM Engine
                      │
                      ▼
               ProviderManager
                      │
                      ▼
               ProviderFactory
                      │
      ┌───────────────┼────────────────┐
      ▼               ▼                ▼
 OpenAIProvider ClaudeProvider GeminiProvider
      │               │                │
      └───────────────┼────────────────┘
                      ▼
                BaseProvider
```

---

# Componentes

## BaseProvider

Responsabilidad:

Definir el contrato común para todos los proveedores.

Métodos esperados:

- available()
- generate()
- configuration()
- health()

Todo proveedor debe implementar esta interfaz.

---

## ProviderManager

Responsabilidad:

Punto único de acceso para el resto del framework.

Funciones principales:

- seleccionar proveedor activo;
- generar respuestas;
- consultar estado;
- cambiar proveedor dinámicamente.

El resto del sistema nunca interactúa directamente con un proveedor concreto.

---

## ProviderFactory

Responsabilidad:

Crear la implementación adecuada según la configuración.

Actualmente soporta:

- OpenAI
- Claude
- Gemini
- Ollama
- OpenRouter

En futuras versiones evolucionará hacia un registro dinámico de plugins.

---

# Proveedores Soportados

## OpenAIProvider

Uso recomendado:

- GPT-5.x
- GPT-4.x

Fortalezas:

- alta calidad de generación;
- gran capacidad de razonamiento;
- amplio ecosistema.

---

## ClaudeProvider

Uso recomendado:

- análisis extensos;
- revisión arquitectónica;
- documentación.

Fortalezas:

- ventanas de contexto amplias;
- buena comprensión de proyectos grandes.

---

## GeminiProvider

Uso recomendado:

- tareas multimodales;
- análisis rápidos;
- integración con ecosistema Google.

---

## OllamaProvider

Uso recomendado:

- ejecución local;
- privacidad;
- desarrollo sin conexión.

Ventajas:

- sin dependencia de servicios externos;
- control total sobre los modelos.

---

## OpenRouterProvider

Uso recomendado:

- acceso unificado a múltiples modelos;
- comparación entre proveedores;
- balanceo de costos.

---

# Flujo de Ejecución

```
Instruction

↓

ProviderManager

↓

ProviderFactory

↓

Selected Provider

↓

LLM Response
```

---

# Selección del Proveedor

La selección se realiza mediante la configuración del entorno.

Ejemplo:

```
AI_PROVIDER=openai
```

Valores admitidos:

- openai
- claude
- gemini
- ollama
- openrouter

---

# Cambio Dinámico

El sistema permite cambiar de proveedor durante la ejecución mediante:

```
ProviderManager.switch(provider)
```

Esto evita reiniciar la aplicación cuando se requiere utilizar otro modelo.

---

# Estado del Proveedor

Cada implementación debe proporcionar información sobre:

- disponibilidad;
- configuración;
- modelo activo;
- estado de salud.

---

# Principios de Diseño

El subsistema Providers debe cumplir:

- desacoplamiento;
- extensibilidad;
- intercambiabilidad;
- simplicidad;
- independencia del dominio.

---

# Evolución Prevista

## Fase 1

Selección mediante variables de entorno.

---

## Fase 2

Registro dinámico de proveedores.

---

## Fase 3

Fallback automático entre proveedores.

Ejemplo:

```
OpenAI

↓

Claude

↓

Gemini

↓

Ollama
```

---

## Fase 4

Balanceo inteligente.

Selección según:

- costo;
- latencia;
- disponibilidad;
- calidad esperada.

---

## Fase 5

Consenso Multi-LLM

Un mismo prompt será evaluado por varios modelos y un motor de consenso decidirá la mejor respuesta.

---

# Beneficios

Esta arquitectura permite:

- evitar dependencia de un único proveedor;
- incorporar nuevos modelos sin modificar la lógica del framework;
- facilitar pruebas y simulaciones;
- aumentar la resiliencia ante caídas de servicios externos.

---

# Estado

En evolución continua.
