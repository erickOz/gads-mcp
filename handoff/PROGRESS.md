# PROGRESS.md — Registro de traspaso entre agentes

> Entradas nuevas SIEMPRE al inicio. Cada agente escribe una al terminar o pausar.
> Un agente que retoma el proyecto solo necesita leer las últimas 2-3 entradas.
> Cuando supere ~50 entradas, las antiguas se mueven a `PROGRESS.archive.md`.

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
