# Seguridad: Architect ataca su propio proyecto

«Hackea el proyecto», «audita la seguridad», «busca agujeros». Architect hace de
atacante antes de que lo haga otro, y luego corrige con tu permiso.

## Qué corre de verdad (sin modelo)

| Escáner | Qué mira | Necesita |
|---|---|---|
| secretos | claves, contraseñas y tokens en el código y en el historial de git | nada |
| patrones | lo que un atacante busca con grep: `eval`, `pickle`, `shell=True`, `verify=False`, SQL concatenado, contraseñas escritas, `curl \| sh`, CORS abierto, JWT `none`… | nada |
| dependencias | paquetes con vulnerabilidades conocidas (osv.dev) y desactualizados | red |
| errores | errores latentes (ruff F, B, PLE) | ruff |
| bandit | inyección, cripto débil, temporales inseguros en Python | `bandit` (Architect lo instala si falta) |
| pip-audit | vulnerabilidades en `requirements.txt` / `pyproject.toml` | `pip-audit` (lo instala si falta) |
| npm audit | vulnerabilidades en `package.json` | npm |
| agentshield | la configuración de agentes (`.claude/`): permisos comodín, secretos, ganchos con inyección, servidores MCP sin fijar | Node (`npx`) |

Todo se guarda en `~/.ai_architect/auditorias/<fecha>.md` (y `.json`), ordenado
por severidad (crítica, alta, media, baja), con archivo y línea.

Con `ARCHITECT_SIN_INSTALAR=1` no instala nada por su cuenta.

## Lo que hacen los especialistas (con modelo)

Después de los escáneres, Architect delega en `security-reviewer` y sigue la
habilidad `security-bounty-hunter` de la biblioteca: leen el código de verdad
buscando lo que un escáner no ve (inyección, SSRF, autenticación rota,
deserialización, rutas alcanzables desde fuera) y devuelven un informe con
cómo se explotaría y cómo se corrige. No cambian nada en ese paso.

## Corregir

«Corrige los agujeros» / «parcha la seguridad»: para cada hallazgo, de mayor a
menor severidad, Architect reproduce el problema con una prueba que falle,
aplica el parche mínimo, corre esa prueba y luego toda la batería. Cada cambio
pasa por tu permiso (recuadro ámbar, «sí» por voz).

## Órdenes al equipo

- `consultar seguridad auditar` (opcional `escaneres: [...]`)
- `consultar seguridad ultima_auditoria`
- `ordenar seguridad proteger_secretos`
