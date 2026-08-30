# PROGRESS.md — Registro de traspaso entre agentes

> Entradas nuevas SIEMPRE al inicio. Cada agente escribe una al terminar o pausar.
> Un agente que retoma el proyecto solo necesita leer las últimas 2-3 entradas.
> Cuando supere ~50 entradas, las antiguas se mueven a `PROGRESS.archive.md`.

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
