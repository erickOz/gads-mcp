# AGENTS.md — Instrucciones para todo agente de IA

> Aplica a Claude Code, Codex, OpenCode, Antigravity, Gemini CLI o cualquier otro agente.
> Si eres Claude Code y llegaste por `CLAUDE.md`: este es el archivo real de instrucciones.

## Protocolo obligatorio de inicio de sesión

Antes de escribir una sola línea de código:

1. Lee `handoff/PLAN.md` — estado de las tareas del proyecto.
2. Lee `handoff/PROGRESS.md` — últimas 2-3 entradas para heredar contexto.
2b. Lee la sección "Aprendizajes acumulados" de este archivo, y los documentos
    del índice de referencia que apliquen a tu tarea.
3. Ejecuta `git log --oneline -10` y `git status` — estado real del código.
4. Identifica tu tarea: la marcada `[~]` (en progreso) o la primera `[ ]` de la fase actual.
5. Si tomas una tarea nueva, márcala `[~]` en `handoff/PLAN.md` ANTES de empezar (actúa como lock).

## Protocolo obligatorio de fin de sesión (o pausa)

**Cierre preventivo por cuota:** si el usuario avisa de que la ventana de tokens
o la cuota se agota ("me quedan pocos tokens", "guarda el estado"), o notas que
la tarea no cerrará en esta sesión, ejecuta este protocolo ANTES de seguir
escribiendo código.

1. Commit del trabajo, aunque esté incompleto: `wip: T-XX descripción de lo que falta`.
2. Agrega una entrada al inicio de `handoff/PROGRESS.md` con el formato definido ahí.
3. Actualiza `handoff/PLAN.md`: `[x]` solo si la verificación quedó registrada; si no, `[~]`.
4. Si `handoff/PROGRESS.md` supera ~50 entradas, mueve las antiguas a
   `handoff/PROGRESS.archive.md` y deja solo las últimas ~10.

## Reglas de trabajo

- Una tarea a la vez. No avances a la siguiente sin cerrar la actual.
- Tareas atómicas: si una tarea te tomará más de una sesión, divídela en subtareas primero.
- Nunca marques `[x]` sin registrar la verificación (ver Escalera de verificación).
- No refactorices fuera del alcance de tu tarea sin registrarlo en `handoff/PROGRESS.md`.
- Ante ambigüedad de diseño: elige lo más simple y documéntalo en "Decisiones".
- Bug ajeno encontrado de paso: NO lo arregles; agrégalo al Backlog de `handoff/PLAN.md`.
- Al iniciar, detecta concurrencia por locks `[~]` ajenos, últimas entradas de
  `PROGRESS.md`, commits recientes y `git status`. Si hay paralelismo, crea rama y
  `git worktree` propios antes de editar. Nunca compartas worktree.

## Verificación (definición de "terminado")

Verificar = **demostrar, de forma que el siguiente agente pueda reproducir, que la
tarea quedó hecha y no rompió lo que ya funcionaba.**

### Escalera de verificación

- **E3 · Tests automatizados** — `.venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
- **E2 · Chequeos estáticos** — `.venv/bin/python -m pylint ads_mcp` · `.venv/bin/pyink --check .`
- **E1 · Smoke manual** — arrancar el server y hacer el handshake MCP (ver más abajo).
- **E0 · Revisión** — solo contenido/config sin lógica; justificar en `PROGRESS.md`.

**Escalón actual del proyecto: E3.** La suite corre y pasa; úsala siempre.

**Comandos disponibles hoy:**
- tests: `.venv/bin/python -m pytest tests/ -q -p no:cacheprovider`
- tests en vivo contra la API real (requieren credenciales, no corren en CI):
  `GOOGLE_ADS_CREDENTIALS=~/.config/google-ads.yaml GOOGLE_ADS_MCP_TEST_CUSTOMER_ID=... \
   GOOGLE_ADS_MCP_TEST_LOGIN_CUSTOMER_ID=... .venv/bin/python -m pytest tests/live -q`
- lint: `.venv/bin/python -m pylint ads_mcp`
- deps: `uv sync` (recrea `.venv`; NUNCA edites `.venv` a mano)

**Smoke E1 — el flujo crítico que SIEMPRE se prueba tras tocar arranque, deps o config:**
que el servidor complete el handshake MCP. Levanta el server y comprueba que
responde `initialize` y `tools/list` en segundos, no minutos:

```bash
cd /Users/erickoz/Developer/gads-mcp
GOOGLE_ADS_CREDENTIALS=~/.config/google-ads.yaml .venv/bin/python -m ads_mcp.stdio
```

Debe quedarse esperando en stdin sin errores. Si tarda más de ~10 s en estar listo,
algo está mal con el entorno (ver Aprendizajes).

## Stack y comandos del proyecto

- Stack: Python 3.12, [FastMCP](https://github.com/jlowin/fastmcp) >= 3.4.2,
  `google-ads` >= 31.0.0 (**Google Ads API v24**), httpx, uv como gestor.
- Entrada stdio: `ads_mcp/stdio.py` · entrada HTTP: `ads_mcp/server.py`.
- Registro de tools: `ads_mcp/config.py` + `ads_mcp/tools_config.yaml` (namespaces).
- Skills como prompts MCP: `ads_mcp/skill_registry.py` + `ads_mcp/skills/`.
- Convención de commits: `tipo: T-XX descripción` (feat, fix, wip, chore, docs, test).
- Rama de trabajo: `main` (repo personal); `origin` = `github.com/erickOz/gads-mcp`,
  `upstream` = `github.com/googleads/google-ads-mcp`.

## Convenciones de código

- Estilo Google (pyink): indentación de **2 espacios**, línea de **79** caracteres.
- Un archivo por dominio en `ads_mcp/tools/`, tools con `@mcp.tool()`.
- Helpers compartidos: `get_ads_client()` y `execute_gaql()` desde `ads_mcp.tools.api`.
- **Toda entrada interpolada en GAQL pasa por `ads_mcp.tools.validation`**
  (`numeric_id`, `id_list`, `enum`, `resource_name`). No concatenes strings a mano.
- Al agregar un dominio: registrarlo como namespace en `tools_config.yaml` y
  `ads_mcp/config.py`, y agregar sus tests (mockeando `get_ads_client`/`execute_gaql`).

## Documentación de referencia del proyecto

| Documento | Cuándo leerlo | Confianza |
|---|---|---|
| `ROADMAP.md` | Antes de elegir qué construir; gaps de deploy y versión pública | [vigente] |
| `docs/setup-clients.md` | Conectar el MCP a Claude Desktop / Code / Codex / OpenCode | [vigente] |
| `README.md` | Qué es el proyecto y setup del entorno | [parcial] — no menciona las skills |
| `CONTRIBUTING.md` | Antes de agregar tool/namespace/skill | [parcial] |
| `CHANGELOG.md` | Historia de versiones | [vigente] |

**Regla:** si un documento contradice al código, gana el código. Reporta la
contradicción en `handoff/PROGRESS.md` y baja la confianza aquí.

## Aprendizajes acumulados

- **El repo NO puede vivir en Google Drive / iCloud / OneDrive.** Estuvo en
  `~/Library/CloudStorage/GoogleDrive-…` y el MCP era inusable: leer 20 YAML de
  `ads_mcp/context/views/` tardaba 27 s, `import ads_mcp.config` 32 s, y el arranque
  no terminaba en 15 min (0% CPU, todo I/O de red porque los archivos son
  *online-only*). Todo cliente MCP corta el handshake por timeout → "Connection
  closed". Además Drive rompe los symlinks de `.venv` y borra el bit de ejecución
  de los `.sh`. Vive en `/Users/erickoz/Developer/gads-mcp`. (T-01)
- **Nunca hardcodees la ruta del proyecto en más de un lugar sin listarla.** El
  montaje de Drive cambió de nombre y rompió 5 configs a la vez + el editable
  install del `.venv`. Las rutas del MCP viven en `docs/setup-clients.md`. (T-01)
- **Si mueves o renombras la carpeta, recrea el `.venv` con `uv sync`.** El editable
  install guarda rutas absolutas en `__editable___*_finder.py`; copiarlo da
  `ModuleNotFoundError: No module named 'ads_mcp'`. (T-01)
- **`origin` (`github.com/erickOz/gads-mcp`) es PÚBLICO.** Todo lo que escribas en
  `handoff/`, `AGENTS.md` o `docs/` se publica al pushear: hoy están ahí el correo
  de trabajo del usuario, el nombre del cliente (Hype Digital, MCC de ~15 cuentas)
  y las rutas locales. Decisión consciente del usuario (T-02), no un descuido: no
  lo "arregles" por tu cuenta. Pero al redactar, no agregues credenciales, IDs de
  cuenta ni datos de clientes nuevos. Ojo con `handoff/PLAN.md` T-03: describe un
  agujero de OAuth sin parchear, ya público. (T-02)
