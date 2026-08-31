# PROGRESS.md — Registro de traspaso entre agentes

> Entradas nuevas SIEMPRE al inicio. Cada agente escribe una al terminar o pausar.
> Un agente que retoma el proyecto solo necesita leer las últimas 2-3 entradas.
> Cuando supere ~50 entradas, las antiguas se mueven a `PROGRESS.archive.md`.

---

## 2026-08-31 — Auditoría funcional del MCP (B-12, B-13) — Claude Code / Opus 5

- **Hecho:**
  - **Auditoría tool por tool contra la API real.** Nuevo `deploy/audit-tools.py`:
    levanta su propia instancia por stdio, descubre IDs reales (MCC → cuenta hija
    con campaña y ad group activos) y llama a 24 tools de lectura.
    **Resultado: 20 OK, 4 fallas.** Handshake 4-5 s, 78 tools registradas.
  - **3 bugs reales encontrados y diagnosticados** (→ **B-12**), todos del mismo tipo
    que `90fd35b`/`a44de8a`/`d216d02`: campos GAQL que la v24 ya no acepta. Las 3
    correcciones quedaron **verificadas contra la API**, no supuestas:
    `experiment.id` → `experiment.experiment_id`; `WHERE ad_group.campaign.id` →
    `WHERE campaign.id`; y quitar los campos de `geo_target_constant` del SELECT
    sobre `campaign_criterion`.
  - **1 falso positivo aclarado** (→ **B-13**): `generate_keyword_ideas` **no está
    rota**. Choca con el rate limit de Keyword Planner
    (`ResourceExhausted: 429 … "Too many requests. Retry in 4 seconds."`). En frío
    responde; la segunda llamada seguida falla.
  - **Confirmado el apilamiento de B-11**: 18 procesos `ads_mcp.stdio` y 11 de
    `analytics-mcp` vivos, con la carga en 5.46. En esta sesión ambos servers
    cayeron con `CONNECT_TIMEOUT`.

- **Pendiente:**
  - **B-12** — aplicar las 3 correcciones + un test en `tests/live/` por cada una.
    La suite mockeada (120 passed) **no atrapa esta clase de bug**: pasa en verde
    con las 3 tools rotas. Ese es el punto ciego, no un descuido.
  - **B-13** — backoff/reintento y propagar el mensaje real del 429.
  - **B-11** — decidir entre cerrar sesiones de editor, acelerar el arranque (B-01)
    o pasar a HTTP compartido (Fase 2).
  - **T-02b** — borrar `gads-mcp.RETIRADO` cuando el usuario lo diga.

- **Decisiones:**
  - **No se arreglaron los bugs.** AGENTS.md manda registrarlos en el Backlog, no
    arreglarlos de paso; y la petición era verificar. Están en B-12 con el fix ya
    verificado, listos para una tarea propia.
  - **`deploy/audit-tools.py` se guarda en el repo** aunque no se pidió: sin él, el
    hallazgo no es reproducible, que es lo que exige la escalera de verificación.
  - **La allowlist `READ_ONLY` del auditor es deliberada y no debe crecer con tools
    de escritura**: corre contra cuentas de producción reales.

- **Gotchas (le ahorran horas al siguiente):**
  - **El payload del server no es uniforme.** `execute_gaql` y las tools de reporting
    devuelven `{"data": [...]}`; otras `{"result": [...]}`; alguna la lista pelada.
    Costó un falso diagnóstico. Ver `rows()` en `deploy/audit-tools.py`.
  - **Nunca audites contra el MCC.** Pedir métricas a una cuenta manager da
    `REQUESTED_METRICS_FOR_MANAGER` y parecen 5 tools rotas que están sanas. Hay que
    bajar a una cuenta hija: `SELECT customer_client.id FROM customer_client
    WHERE customer_client.manager = FALSE AND customer_client.status = 'ENABLED'`.
  - **`Error calling tool '<nombre>'` no dice nada: la excepción real va a stderr
    del server.** Para verla, lanza el server con `stderr` a un archivo. Así se
    descubrió que el "fallo" de `generate_keyword_ideas` era un 429.
  - **El parámetro de `get_reporting_view_doc` es `view`, no `view_name`.**
  - Keyword Planner limita a ~1 petición cada 4 s por método. Al auditar, espacia
    las llamadas o la segunda falla siempre.

- **Verificación (E3 + E1 + E2):**
  - `.venv/bin/python deploy/audit-tools.py` → **20 OK / 4 FALLAS**, reproducido 3
    veces con el mismo resultado (las 4 fallas son estables, no intermitentes).
  - Cada una de las 3 correcciones de B-12 se probó vía `execute_gaql` contra la
    cuenta `1746647707`: la variante corregida devuelve OK.
  - `pytest` → **120 passed** (sin cambios en `ads_mcp/`).
  - `pylint deploy/audit-tools.py` → 9.77/10.

- **Último commit:** ver `git log -1` (`test: auditar las 78 tools…`).

---

## 2026-08-30 — Verificación de los 4 clientes (cierra el pendiente de T-01/T-02) — Claude Code / Opus 5

- **Hecho:**
  - **Los 4 clientes quedan verificados llamando a la API real.** La entrada anterior
    daba esto por imposible sin el usuario ("ningún agente puede hacerlo"): **era
    falso**. Codex y OpenCode tienen CLI headless, y Claude Desktop deja logs.
    - **Claude Code** (Opus 5): `list_accessible_accounts` → `["8774376180"]`.
    - **Claude Desktop**: su log `~/Library/Logs/Claude/mcp-server-google-ads-mcp.log`
      muestra arranque con la ruta nueva a las 22:44:49Z, `initialize` + `tools/list`
      OK, y un **`tools/call` real con resultado** a las 22:48:27Z (1.16 s). Sin
      errores posteriores.
    - **Codex** (`gpt-5.6-luna`, codex-cli 0.149.0): `codex exec` → `["8774376180"]`.
    - **OpenCode** (`kimi-k2.7-code`, v1.18.21): `opencode run` → `["8774376180"]`.
  - **Nuevo script `deploy/smoke-clients.py`.** Lee las 5 configs reales de cliente y
    lanza el comando exacto de cada una con `cwd=/`. Resultado: **5/5 en ✓, 78 tools**,
    `initialize` entre 3.2 s y 8.9 s. Hace reproducible la verificación E1.

- **Pendiente:**
  - **T-02b — borrar `gads-mcp.RETIRADO` de Drive.** Su bloqueante real (¿funcionan
    los 4 clientes?) **ya está resuelto**. Lo único que queda es el margen de días
    que pedía T-02, que es criterio del usuario, no técnico.
  - T-03 (allowlist OAuth) sigue siendo el bloqueante 🔴 del deploy remoto.

- **Decisiones:**
  - **No se tocó la config de Codex.** El override de aprobación se pasó con `-c` solo
    para esa invocación. Pre-aprobar tools de forma permanente es decisión del usuario
    y **debería limitarse a las de lectura**: auto-aprobar las de escritura daría a un
    agente vía libre para mutar campañas reales sin confirmación.
  - **`deploy/smoke-clients.py` lee las configs en vez de hardcodear rutas**, que es
    justo el error que causó T-01 (la ruta del proyecto repetida en 5 sitios).

- **Gotchas (le ahorran horas al siguiente):**
  - **Se puede verificar Codex y OpenCode sin GUI ni usuario:**
    `codex exec "<prompt>"` y `opencode run --dir <ruta> "<prompt>"`.
  - **Codex falla toda llamada MCP en headless** con `MCP tool call requires approval,
    but approval policy is never`. **No es un fallo de conexión** — el server arranca
    y la tool se resuelve. En la app interactiva el usuario simplemente aprueba.
    Para headless, override por invocación:
    `codex exec -c 'mcp_servers.google-ads-mcp.tools.<tool>.approval_mode="approve"' …`
    (`analytics-mcp` ya tiene 3 tools pre-aprobadas así en `~/.codex/config.toml`;
    `google-ads-mcp` no tiene ninguna.)
  - **En OpenCode el server se llama `google-ads`**, no `google-ads-mcp`, y la tool
    aparece como `google-ads_list_accessible_accounts`. Si le pides el nombre
    equivocado, el agente no la encuentra.
  - **El primer arranque tras `uv sync` supera el timeout de 60 s de Claude Desktop.**
    En el log: arranque a las 22:17:50Z → `Couldn't start for Cowork and Code sessions.
    Error: Request timed out` a las 22:18:50Z, exacto a los 60 s. Al reintentar ya
    caliente, `initialize` tardó 18 s y funcionó. **Tras un `uv sync`, arranca el
    server a mano una vez antes de abrir los clientes.**
  - Los logs por server de Claude Desktop están en `~/Library/Logs/Claude/mcp-server-<nombre>.log`.
    Es la forma de auditar un cliente GUI sin tocarlo.

- **Verificación (E1 + E3):**
  - `.venv/bin/python deploy/smoke-clients.py` → 5/5 ✓, 78 tools cada una.
  - 3 llamadas end-to-end a la API real desde 3 agentes distintos (Opus 5, gpt-5.6-luna,
    kimi-k2.7-code), las tres devolviendo el MCC `8774376180`.
  - Claude Desktop auditado por log (no se pudo ejercitar: es GUI).
  - Tests: **120 passed** (sin cambios de código en esta entrada; solo se añadió
    `deploy/smoke-clients.py`, que no entra en la suite).

- **Último commit:** ver `git log -1` (`test: verificar el MCP en los 4 clientes…`).

---

## 2026-08-30 — T-02 (completa) + cierre del pendiente de T-01 — Claude Code / Opus 5

- **Hecho:**
  - **Cerrado el pendiente de T-01: el respaldo en GitHub ya existe.** `origin`
    estaba 4 commits atrás (desde el 13 de julio). Merge fast-forward de
    `setup/handoff-y-conectividad` a `main` y push: `origin/main` pasa de `90fd35b`
    a `f1edf92`. Subieron los 2 fixes de GAQL (`a44de8a`, `d216d02`) y los 2 de T-01
    (`AGENTS.md`, `handoff/`, `docs/setup-clients.md`, `deploy/repoint-mcp-configs.py`).
  - **T-02: copia de Drive retirada.** Renombrada a `gads-mcp.RETIRADO` en
    `…/Mi unidad/4. Proyectos/projects-mkt/`. **No borrada** (ver Pendiente).
  - **Auditada la copia de Drive antes de retirarla.** Estaba en `d216d02` (todo ya
    en `origin`). Sus cambios sin commitear resultaron ser ruido: los `.DS_Store`
    borrados, y `run_mcp.sh` + `deploy/cloud-run.sh` con **cambio de modo solamente**
    (755→644, la corrupción de bit de ejecución que hace Drive), 0 líneas de diff.
  - **Rescate verificado de un `AGENTS.md` sin trackear que había en Drive**: no era
    el del handoff sino la vieja "Codex Setup Guide" (11.5 KB), la variante para Codex
    del mismo documento. Su contenido íntegro (tabla de las 78 tools, Example Prompts,
    Credentials Reference, `tools_config`, Cloud Run) ya está en `docs/setup-clients.md`.
    No se perdió nada.
  - Nuevo aprendizaje en `AGENTS.md`: **`origin` es público**.

- **Pendiente:**
  - **T-02b — borrar `gads-mcp.RETIRADO` de Drive.** Deliberadamente NO se borró:
    el propio T-02 gatilla el borrado "tras confirmar", y esa confirmación no existe
    todavía. El renombrado es reversible; el borrado no.
  - **Verificación humana en 3 clientes.** Solo **Claude Code** quedó verificado, y
    esta vez de verdad: llamada en vivo `list_accessible_accounts` → MCC `8774376180`.
    Claude Desktop, Codex y OpenCode siguen sin verificar; hay que **reiniciarlos** y
    confirmar que `google-ads-mcp` aparece conectado. Ningún agente puede hacerlo.
  - Sigue abierto lo de siempre: T-03 (allowlist OAuth) es el bloqueante 🔴 del deploy.

- **Decisiones:**
  - **Pushear al repo público tal cual, sin cambiar la visibilidad.** Se le advirtió
    al usuario en detalle que `erickOz/gads-mcp` es público (no es un fork; creado el
    2026-04-13, 0 estrellas, sin descripción) y que el push publicaría su correo de
    trabajo, "Hype Digital / MCC de ~15 cuentas", las rutas locales y la descripción
    del agujero de OAuth de T-03. **El usuario lo confirmó explícitamente.** Es una
    decisión suya, no un descuido: **no la revuelvas**. Revertir la visibilidad es
    `gh repo edit erickOz/gads-mcp --visibility private`, pero lo ya indexado no vuelve.
  - **Retirar por renombrado, no por borrado.** Es la primera mitad de T-02 tal como
    está escrita, y deja marcha atrás. El borrado se separó como T-02b.
  - **T-02 se ejecutó pese a que su precondición no se cumplía** ("unos días con los
    4 clientes funcionando"; T-01 se cerró el mismo día y solo 1 cliente verificado).
    Se advirtió y el usuario pidió proceder. El riesgo quedó acotado porque el push
    a `origin` se hizo primero: ya hay respaldo real antes de tocar Drive.

- **Gotchas (le ahorran horas al siguiente):**
  - **Nunca borres la copia de Drive antes de comprobar que `origin` está al día.**
    Aquí el diario afirmaba "el respaldo real es `origin` en GitHub" y era **falso**:
    faltaban 4 commits. Comprueba con `git log --oneline origin/main..main`, no con
    lo que diga `PROGRESS.md`.
  - **Auditar la copia de Drive sin colgarse:** `git -C "<ruta drive>" status --short`
    tarda minutos. Lánzalo en segundo plano y redirige a archivo; en macOS no hay
    `timeout(1)` y `cmd | tail` no muestra nada hasta que termina.
  - **Los diffs de `.sh` en Drive son casi siempre falsos positivos**: cambio de modo
    755→644, no de contenido. Distínguelos con `git diff --summary`, no con `--stat`.
  - `~/.claude.json` conserva una clave de *historial de proyecto* con la ruta vieja de
    Drive. Es inofensiva (historial de sesiones de esa carpeta), **no** una ruta de MCP.
    Las 5 configs de cliente apuntan todas a `/Users/erickoz/Developer/gads-mcp`.
  - La config de OpenCode es `~/.config/opencode/opencode.jsonc` (**`.jsonc`**, con
    comentarios), no `.json`, y ahí el server se llama `google-ads`, no `google-ads-mcp`.

- **Verificación (E3 + E1):**
  - **E3 — tests:** `.venv/bin/python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/live`
    → **120 passed**, corrido dos veces: antes de tocar nada y después de retirar Drive.
  - **E1 — MCP en vivo contra la API real:** `list_accessible_accounts` → `8774376180`,
    ejecutado **antes y después** del renombrado de Drive. Prueba handshake + auth +
    Google Ads API v24 de punta a punta.
  - **E1 — handshake directo:** `initialize` por stdio devuelve `serverInfo` correcto.
  - **E0 — configs:** 0 de las 5 configs de cliente apuntan a la ruta retirada.
  - **Push confirmado en el remoto:** `gh api repos/erickOz/gads-mcp/commits/main`
    → `f1edf92`; `handoff/PLAN.md` y `handoff/PROGRESS.md` visibles en GitHub.

- **Último commit:** ver `git log -1` (este mismo cierre, `docs: T-02 …`).

---

## 2026-08-30 — T-01 (completa) + adopción del sistema — Claude Code / Opus 5

- **Hecho:**
  - **Diagnóstico del "Connection closed"** que rompía el MCP en Claude Desktop,
    Claude Code, Codex y OpenCode a la vez. Tres causas encadenadas:
    1. Las 5 configs de cliente apuntaban a
       `…/CloudStorage/GoogleDrive-e.zea@hype/Mi unidad/…`, ruta que ya no existe
       (el montaje real es `GoogleDrive-e.zea@hy-pedigital.com`). El proceso ni
       arrancaba: `FileNotFoundError`.
    2. El `.venv` tenía el editable install clavado a esa misma ruta muerta
       (`__editable___google_ads_mcp_0_7_0_finder.py` → `MAPPING`), así que aun con
       el binario correcto daba `ModuleNotFoundError: No module named 'ads_mcp'`.
    3. **La causa de fondo:** el repo vivía en Google Drive File Stream. Los
       archivos son *online-only* y cada lectura es una descarga.
  - **Movido el repo** de Drive a `/Users/erickoz/Developer/gads-mcp` (rsync de 676
    archivos con `.git`, excluyendo `.venv`, `__pycache__`, `.pytest_cache`,
    `.coverage`, `*.egg-info`, `.DS_Store`). `.venv` recreado con `uv sync`.
  - **Repuntadas las 5 configs** de cliente con
    `deploy/repoint-mcp-configs.py` (reemplazo literal de la ruta; deja un
    `.bak-gadspath` junto a cada archivo). Ver la tabla en `docs/setup-clients.md`.
  - **Restaurado** el bit de ejecución de `run_mcp.sh` y `deploy/cloud-run.sh`
    (Drive los había pasado de 755 a 644) y sacados los `.DS_Store` del tracking.
  - **Instalado el sistema de handoff**: `AGENTS.md` real en la raíz,
    `handoff/PLAN.md` reconstruido por arqueología, este `PROGRESS.md`.
    `CLAUDE.md` y `GEMINI.md` quedaron como puentes de dos líneas a `AGENTS.md`
    (antes CLAUDE.md eran 11 KB que se cargaban en cada sesión).

- **Pendiente:**
  - **Verificación humana en los 4 clientes**: hay que **reiniciar** Claude Desktop,
    Claude Code, Codex y OpenCode y confirmar que `google-ads-mcp` aparece conectado.
    La verificación automática cubre el servidor, no el arranque de cada cliente.
  - **T-02**: retirar la copia de Drive (`…/projects-mkt/gads-mcp`) una vez que los
    4 clientes lleven unos días funcionando. **Sigue intacta a propósito**, como red
    de seguridad. Renombrarla a `gads-mcp.RETIRADO` antes de borrar.
  - Rama `setup/handoff-y-conectividad` **sin mergear a `main` y sin pushear**.
    Además, `main` tiene 2 commits viejos sin pushear a `origin` (`a44de8a`, `d216d02`).

- **Decisiones:**
  - **Mover el repo en vez de solo arreglar rutas.** Con las rutas corregidas pero
    el repo en Drive el problema persistía: el arranque no terminaba. Es la única
    opción que deja el handshake en segundos. Elegido por el usuario entre tres.
  - **Se conservaron las dos formas de invocación** que ya usaba cada cliente
    (`\.venv/bin/python` en Claude Desktop y OpenCode; `uv run --directory` en Claude
    Code y Codex) en vez de unificarlas: ambas quedaron verificadas y unificar
    habría sido churn sin beneficio medible.
  - **`docs/setup-clients.md` es la fuente única de las rutas.** Nació del CLAUDE.md
    viejo para no perder la tabla de las 78 tools ni las guías de conexión.
  - **La copia de Drive no se borró.** Borrar es irreversible y el usuario no lo pidió.

- **Gotchas (le ahorran horas al siguiente):**
  - **Si mueves o renombras la carpeta del proyecto, `uv sync` es obligatorio.**
    Copiar el `.venv` no sirve: el editable install guarda rutas absolutas.
  - **El primer arranque tras `uv sync` tarda ~29 s** (compilación de bytecode de los
    protos de `google-ads` v24, que son enormes). Los siguientes, 3-4 s. Si un cliente
    falla justo después de un `uv sync`, arranca el server a mano una vez y reintenta.
  - **`~/.claude.json` lo reescribe Claude Code al vuelo.** Tras editarlo, verificar
    que el cambio sobrevivió: `grep -c "Developer/gads-mcp" ~/.claude.json` → 3.
  - `google-ads-mcp` está definido **dos veces** para Claude Code (`~/.claude.json` y
    `~/.claude/settings.json`). Ambas quedaron apuntando al mismo sitio; si algún día
    divergen, ahí está la ambigüedad.
  - En macOS no hay `timeout(1)`; y `cmd | tail` no muestra nada hasta que el proceso
    termina (útil saberlo al depurar arranques lentos: redirige a un archivo).

- **Verificación (E3 + E1):**
  - **E3 — tests:** `.venv/bin/python -m pytest tests/ -q -p no:cacheprovider --ignore=tests/live`
    → **120 passed en 8.29 s**. (El `ROADMAP.md` decía 103; hoy son 120.)
  - **E1 — smoke del handshake MCP**, con un cliente JSON-RPC mínimo que manda
    `initialize` + `tools/list` por stdio, `cwd=/` (como lo lanzan los clientes):
    - `\.venv/bin/python -m ads_mcp.stdio` → initialize **3.14 s**, **78 tools**
    - `uv run --directory … -m ads_mcp.stdio` → initialize **3.88 s**, **78 tools**
    - Antes del cambio, en Drive: sin respuesta a los 90 s; el import de
      `ads_mcp.coordinator` seguía corriendo a los 15 min con 0% CPU.
  - **Medición del I/O de Drive** (la evidencia que justificó mover el repo):
    leer 20 de los 167 YAML de `ads_mcp/context/views/` → **27.6 s**;
    `import dotenv` → 5 s; `import ads_mcp.config` → 32 s;
    `git status` → **timeout a los 2 min** (ahora: **0.076 s**).
  - **E0 — configs:** los 5 archivos quedaron con 0 referencias a la ruta muerta y
    siguen siendo JSON/TOML válidos (parseados con `json.load` y `tomllib`).

- **Último commit:** `b7a5007` `chore: T-01 sacar el repo de Google Drive e instalar el sistema de handoff`

---

## PLANTILLA (copiar hacia arriba)

## AAAA-MM-DD — T-XX (estado: completa | incompleta) — [agente/modelo]

- **Hecho:** qué se implementó, en qué archivos
- **Pendiente:** qué falta exactamente para cerrar la tarea (ser específico)
- **Decisiones:** elecciones de diseño tomadas y por qué
- **Gotchas:** trampas, configuraciones raras, cosas que le ahorrarán tiempo al siguiente
- **Verificación:** qué se corrió y su resultado (tests ✓/✗, lint ✓/✗, build ✓/✗)
- **Último commit:** hash + mensaje
