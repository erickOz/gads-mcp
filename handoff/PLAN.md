# PLAN.md — Plan de trabajo del proyecto

> Estados: `[ ]` pendiente · `[~]` en progreso (lock: solo un agente) · `[x]` terminada y verificada · `[!]` bloqueada
> Regla: `[x]` solo si la verificación de AGENTS.md quedó registrada en `handoff/PROGRESS.md`.

## Objetivo del proyecto

Servidor MCP sobre la Google Ads API (v24) para operar las cuentas de Hype Digital
(un MCC, ~15 cuentas) desde cualquier cliente de IA: reporting, gestión de campañas,
keywords, presupuestos, conversiones, audiencias y experimentos. Dos objetivos
estratégicos abiertos: **exponerlo como servidor remoto seguro** y **publicar una
versión pública compacta** como showcase.

---

## Fase 0: Ya implementado ✅

> Reconstruido por arqueología del repo + `ROADMAP.md` (2026-07-11) + historial de commits.
> Verificado por la suite de tests y por smoke contra la API real.

- [x] F0-01 **78 tools en 18 módulos** de `ads_mcp/tools/` (reporting, campañas, ad groups,
      keywords, assets, audiencias, labels, recomendaciones, conversiones, customer match,
      geo, demografía, ad scheduling, keyword planner, shared budgets, portfolio bidding,
      experiments, change history).
- [x] F0-02 **8 skills** expuestas como prompts MCP vía `ads_mcp/skill_registry.py`.
- [x] F0-03 **Capa de guía**: `instructions` del server (mapa de capacidades, ruteo a
      `start-here`, reglas de seguridad).
- [x] F0-04 **Gating por namespaces**: `ads_mcp/tools_config.yaml` + `ads_mcp/config.py`
      (permite perfil read-only).
- [x] F0-05 **Validación anti-inyección GAQL**: `ads_mcp/tools/validation.py`, ~21 puntos
      cerrados (`numeric_id`, `id_list`, `enum`, `resource_name`).
- [x] F0-06 **Migración a google-ads 31 / API v24**, verificada contra la API real.
- [x] F0-07 **Suite de tests**: 103 passing, cobertura 48%, ratchet `--cov-fail-under=45`,
      pylint 9.14/10.
- [x] F0-08 **Smoke tests en vivo** (`tests/live/`, gated por credenciales). Atraparon 3 bugs
      de campos GAQL inválidos en v24 (commits `90fd35b`, `a44de8a`, `d216d02`).
- [x] F0-09 **Deploy**: `Dockerfile`, `docker-compose.yml`, `deploy/cloud-run.sh`
      (Secret Manager + OAuth `GoogleProvider`), transporte `streamable-http` en `/mcp`.

---

## Fase 1: Entorno y conectividad de clientes

- [x] T-01 **Sacar el repo de Google Drive y dejar el MCP conectando en los 4 clientes**
      (Claude Desktop, Claude Code, Codex, OpenCode). Mover a
      `/Users/erickoz/Developer/gads-mcp`, recrear `.venv` con `uv sync`, repuntar las
      5 configs y verificar el handshake MCP. Documentar en `docs/setup-clients.md`.
- [x] T-02 **Retirar la copia de Google Drive.** Renombrada a `gads-mcp.RETIRADO`
      (2026-08-30). El respaldo real es `origin` en GitHub, ya al día en `f1edf92`.
- [ ] T-02b **Borrar definitivamente `gads-mcp.RETIRADO`** de Drive. Los 4 clientes
      **ya están verificados** contra la API real (2026-08-30): Claude Code, Codex
      (`gpt-5.6-luna`) y OpenCode (`kimi-k2.7-code`) por llamada end-to-end, y Claude
      Desktop por su log de `tools/call`. Solo queda el margen de días que pedía T-02,
      que es criterio del usuario. Antes de borrar, releer los gotchas de T-02.
      Reverificar con `.venv/bin/python deploy/smoke-clients.py` (espera 5/5, 78 tools).

## Fase 2: Endurecer el deploy remoto 🌐

> Bloqueante para "consumir el MCP desde cualquier parte". Ver `ROADMAP.md` §4.

- [ ] T-03 🔴 **Allowlist de OAuth**: hoy `GoogleProvider` acepta cualquier cuenta Google,
      así que quien tenga la URL usa el MCC. Restringir por email/dominio ANTES de
      exponerlo. Es el único bloqueante real para desplegar.
- [ ] T-04 🟡 **Observabilidad**: logging estructurado + alertas (errores, latencia, cuota API).
- [ ] T-05 🟢 **Cuotas y rate limits** de la Google Ads API: backoff + cache de reporting.
- [ ] T-06 🟢 **Costos de Cloud Run**: revisar `min-instances`, timeouts, `max-instances`.

## Fase 3: Versión pública compacta 📦

> Camino elegido en `ROADMAP.md` §5: **A** (perfil "lite" por config, un solo codebase).

- [ ] T-07 `tools_config.yaml` con default **read-only** + README enfocado.
- [ ] T-08 `NOTICE` con atribución a `googleads/google-ads-mcp` (Apache-2.0) y declaración
      de cambios; conservar `LICENSE` y headers de copyright.
- [ ] T-09 Barrido de secretos e historial (`.env`, `google-ads.yaml`, IDs de cuentas)
      antes de publicar.
- [ ] T-10 CI verde sobre el subset + badge.

---

## Backlog (bugs y mejoras encontradas fuera de alcance)

- [ ] B-01 **Arranque en frío en un clon nuevo se cuelga.** `.api-version` y
      `.mcp-server-version` están en `.gitignore`, así que en una máquina nueva
      `update_views_yaml()` hace 167 requests HTTP + 167 escrituras **antes** de responder
      al handshake MCP → el cliente corta por timeout. Opciones: versionar los sentinels,
      o mover la actualización a segundo plano / hacerla perezosa.
      (`ads_mcp/stdio.py`, `ads_mcp/scripts/generate_views.py`)
- [ ] B-02 Subir cobertura 48% → 65%. Sin tests aún: `upload_customer_match_members`,
      `get_keyword_forecast`, varias tools de `assets`, edge cases de PMax.
- [ ] B-03 `reporting._validate_date_range` duplica `validation.validate_enum` — unificar.
- [ ] B-04 Extraer un helper para leer filas planas de `execute_gaql` (el comentario
      "flat keys" se repite en cada módulo).
- [ ] B-05 Estandarizar el wrap de `GoogleAdsException` en todas las operaciones `mutate`.
- [ ] B-06 Job de CI opcional que corra `tests/live/` cuando haya secretos configurados.
- [ ] B-07 Sección de **skills** en el README (hoy no las menciona).
- [ ] B-08 Nota en `CONTRIBUTING.md`: contrato de claves planas + cómo agregar
      tool/namespace/skill.
- [ ] B-09 Tools de la API pendientes, por prioridad (ver `ROADMAP.md` §6):
      🔴 Conversion Value Rules · Conversion Adjustments · Seasonality Adjustments /
      Data Exclusions · Ad Customizers.
      🟡 Shopping/PMax listing groups · audiencias avanzadas · campaign drafts ·
      batch jobs · brand safety.
- [ ] B-10 Los `.sh` del repo perdieron el bit de ejecución mientras vivió en Drive.
      Restaurado en T-01; si vuelve a pasar, revisar `core.fileMode` de git.
- [ ] B-11 **Los servidores MCP se acumulan: una copia por sesión de agente, sin
      liberarse.** Observado el 2026-08-30: 11 procesos `ads_mcp.stdio` y 6 de
      `analytics-mcp` vivos a la vez (hasta 48 min), de 3 sesiones de Claude Code
      (extensión VS Code) + 2 de Codex + 1 de OpenCode. Idle (0% CPU) pero con la
      carga en 5.56 el arranque en frío superó el timeout de 30 s de Claude Code y
      **ambos servers cayeron con `CONNECT_TIMEOUT` en plena sesión**. Cada cliente
      lanza su propio proceso por diseño (stdio), así que el arreglo no es del MCP:
      o se cierran las sesiones de editor que no se usan, o se acelera el arranque
      (ver B-01), o se pasa a transporte HTTP compartido (Fase 2). Diagnóstico:
      `ps -eo pid,ppid,etime,command | grep ads_mcp.stdio`.

## Bloqueos

<!-- T-XX bloqueada por: motivo, qué se necesita para desbloquear -->

_(ninguno)_
