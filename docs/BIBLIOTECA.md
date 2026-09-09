# La biblioteca: habilidades, especialistas, reglas y recetas

Architect tiene a mano cientos de habilidades (listas de pasos y patrones por
tema y lenguaje), decenas de especialistas (revisores de seguridad, de Python,
de rendimiento, planificadores, cazadores de fallos silenciosos…), reglas por
lenguaje y recetas de trabajo. Viven en `~/.ai_architect/biblioteca` y no se
cargan todas a la vez: se buscan por tema y se usan cuando hacen falta.

## Instalar y actualizar

- Por voz: «instala la biblioteca», «actualiza la biblioteca».
- Como orden al equipo: `ordenar biblioteca instalar` (origen opcional: URL de
  GitHub o carpeta local; por defecto `ARCHITECT_BIBLIOTECA`).
- Solo se copia contenido (markdown, texto, json, yaml, toml): ningún script
  ni gancho de otros programas entra en Architect.

## Usar

| Por voz | Qué pasa |
|---|---|
| «¿qué habilidades tienes para seguridad en Django?» | busca por tema (con sinónimos español/inglés) y lo lista |
| «¿qué especialistas tienes?» / «cuántas habilidades tienes» | el estado de la biblioteca |
| «usa la habilidad tdd-workflow y añade pruebas al módulo de voz» | Architect carga la habilidad con `usar_habilidad` y la sigue |
| «que el especialista de seguridad revise el proyecto» | Architect delega con `especialista`: un agente aparte con el guion del especialista y herramientas de solo lectura, que devuelve su informe |

Herramientas de Architect: `buscar_habilidad`, `usar_habilidad`,
`anexo_habilidad`, `especialista`. El guion le dice cuántas hay y cuándo
delegar. Los especialistas no escriben: informan; quien cambia el código es
Architect, con tu permiso, como siempre.

## Los especialistas más útiles

security-reviewer, silent-failure-hunter, performance-optimizer, python-reviewer,
typescript-reviewer, react-reviewer, database-reviewer, tdd-guide, planner,
architect, code-simplifier, refactor-cleaner, doc-updater, build-error-resolver,
e2e-runner, a11y-architect, seo-specialist, network-architect.

La atribución del contenido está en `docs/LICENCIAS-TERCEROS.md`.
