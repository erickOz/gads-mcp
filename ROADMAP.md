# Roadmap — Google Ads MCP

Estado, mejoras pendientes y próximos pasos del proyecto. Incluye los dos
objetivos estratégicos: **desplegar el servidor para consumo remoto** y
**publicar una versión pública compacta**.

_Última actualización: 2026-07-11._

---

## 1. Estado actual (qué ya resolvimos) ✅

Base sólida y verificada end-to-end (unit tests → estructura → **API real en vivo**).

| Dimensión | Estado |
|---|---|
| **Herramientas** | **78 tools** en 18 módulos (reporting, campañas, keywords, bidding, budgets, conversiones, audiencias, targeting, experimentos, keyword planner) |
| **Skills** | **8 playbooks** cableados como **prompts MCP** vía `skill_registry.py` |
| **Capa de guía** | Server `instructions` (mapa de capacidades + ruteo a `start-here` + reglas de seguridad) |
| **Librería** | `google-ads>=31.0.0`, API **v24** — **verificado contra la API real** (MCC Hype Digital, 15 cuentas) |
| **Config** | `tools_config.yaml`: habilitar/deshabilitar namespaces (perfil read-only, etc.) |
| **Seguridad** | `validation.py` — ~21 puntos de inyección GAQL cerrados (numeric_id, id_list, enum, resource_name) |
| **Tests** | **103 passing**, cobertura **48%**, ratchet CI `--cov-fail-under=45`, pylint **9.14/10** |
| **Deploy** | Dockerfile + docker-compose + Cloud Run script (Secret Manager + OAuth `GoogleProvider`) |

---

## 2. Qué podemos mejorar aún 🔧

### Calidad / robustez
- **Cobertura 48% → 65%+**: faltan ramas de lectura y errores. Sin tests aún:
  `upload_customer_match_members`, `get_keyword_forecast`, varias tools de `assets`,
  edge cases de PMax.
- **Deuda menor**: `reporting._validate_date_range` duplica lo que hace
  `validation.validate_enum` — unificar. Extraer un helper para leer filas planas
  de `execute_gaql` (hoy el comentario "flat keys" se repite en cada módulo).
- **Test de integración**: un smoke test que levante el server MCP en memoria y
  liste tools/prompts (hoy se valida a mano).
- **Manejo de errores**: estandarizar el wrap de `GoogleAdsException` en todas las
  operaciones `mutate` (algunas ya lo hacen).

### Documentación
- `CHANGELOG.md` (no existe).
- Sección de **skills** en el README (hoy no las menciona).
- Nota en `CONTRIBUTING.md`: contrato de claves planas + cómo agregar tool/namespace/skill.

---

## 3. Próximos pasos (priorizados) 🎯

1. **Endurecer el deploy para consumo remoto** (§4) — es el bloqueante para "consumir desde cualquier parte".
2. **Preparar la versión pública compacta** (§5).
3. **Subir cobertura** a 65% (empezar por `customer_match`, `assets`, `keyword_planner`).
4. **Backlog de herramientas** (§6) — empezar por las 🔴 (conversion value rules, adjustments).

---

## 4. Desplegar como servidor remoto 🌐

**Objetivo:** consumir el MCP desde Claude.ai / móvil / cualquier cliente, desde cualquier lugar.

### Ya está listo ✅
- Transporte `streamable-http` + endpoint `/mcp`.
- Cloud Run script con **Secret Manager** (secretos fuera del código).
- **OAuth a nivel MCP** (`GoogleProvider`): el cliente inicia sesión con Google antes de usar tools.
- Docker / docker-compose para local.

### Falta para producción ⚠️
| Prioridad | Gap | Acción |
|---|---|---|
| 🔴 **Crítico** | `GoogleProvider` acepta **cualquier** cuenta Google → quien tenga la URL usa **tu** MCC | Restringir a emails/dominio permitidos (allowlist) antes de exponer público |
| 🟡 Alto | **Single-tenant**: un solo refresh token = todos pegan al mismo MCC | OK para uso interno de la agencia (un MCC, `login_customer_id` por cliente). Multi-tenant (otras agencias con su propia cuenta) requiere OAuth de Google Ads por usuario |
| 🟡 Alto | Sin observabilidad | Logging estructurado + alertas (errores, latencia, cuota API) |
| 🟢 Medio | Cuotas de la Google Ads API | Manejo de rate limits / backoff; cache de reporting |
| 🟢 Medio | Costos | Revisar `min-instances`, timeouts, `max-instances=5` |

> **Recomendación:** para el uso de Hype Digital (una agencia, un MCC con 15 cuentas),
> el modelo single-tenant + `login_customer_id` **ya sirve**. El único bloqueante real
> antes de exponerlo es el 🔴 **allowlist de OAuth**. Con eso, desplegable hoy.

---

## 5. Versión pública compacta 📦

**Objetivo:** publicar en un repo público una versión más limitada y compacta — como
showcase / portfolio, sin exponer el arsenal completo de escritura.

### Consideraciones de licencia (importante)
- El proyecto deriva de `googleads/google-ads-mcp` (**Apache-2.0**). Publicar un
  derivado está permitido, pero hay que: mantener `LICENSE`, conservar los headers
  de copyright, **atribuir** al proyecto original (NOTICE) y declarar los cambios.

### Qué recortar / mantener
| Incluir | Excluir |
|---|---|
| Core: `execute_gaql`, `list_accessible_accounts`, docs | Escritura sensible: `mutate`, `campaigns`, `pmax`, `customer_match`, `conversions` |
| **Reporting** completo (read-only, sin riesgo) | Targeting avanzado, bidding portfolios, experiments |
| 1–2 skills (`account-audit`, `wasted-spend-audit`) | Skills que orquestan escritura (`campaign-launch`) |
| `tools_config.yaml`, `validation.py`, tests del subset | Contexto de negocio / cuentas reales |

### Dos caminos (elegir)
- **A — Perfil "lite" en el mismo código (bajo mantenimiento):** publicar el repo
  completo pero con `tools_config.yaml` default en **read-only** y README enfocado.
  Un solo codebase; "compacto" por config, no por borrado.
- **B — Fork curado y genuinamente compacto (más vistoso):** repo nuevo
  (`google-ads-mcp-lite`) con ~15–20 tools (reporting + gestión básica), 1–2 skills,
  README propio. Más trabajo de mantenimiento pero es el mejor showcase.

> **Recomendación:** empezar con **A** (rápido, aprovecha el gating que ya construimos).
> Si gana tracción, invertir en **B**.

### Checklist de publicación
- [ ] Repo nuevo público + `LICENSE` (Apache-2.0) + `NOTICE` con atribución al upstream
- [ ] `tools_config.yaml` read-only por default
- [ ] README limpio (sin contexto de agencia/cuentas)
- [ ] Barrido de secretos e historial (`.env`, `google-ads.yaml`, IDs de cuentas)
- [ ] CI verde (tests del subset) + badge

---

## 6. Backlog de herramientas de la API

Capacidades de la Google Ads API aún **no** cubiertas por las 78 tools. Prioridad:
🔴 alto impacto (encaja con flujos actuales), 🟡 escenarios específicos, 🟢 nicho / cubrible con `execute_gaql`.

### 🔴 Alta prioridad
- **Conversion Value Rules** — `create/list/remove_conversion_value_rule`. Ajusta el
  *valor* de conversión por ubicación/dispositivo/audiencia; alimenta Smart Bidding.
  (`ConversionValueRule`, `ConversionValueRuleSet`)
- **Conversion Adjustments** — `upload_conversion_adjustments`. Corregir/anular
  conversiones ya subidas (devoluciones, leads descalificados). Complementa los
  uploads existentes. (`ConversionAdjustmentUploadService`)
- **Seasonality Adjustments / Data Exclusions** — señales para Smart Bidding
  (Black Friday, Cyber Wow) o excluir periodos anómalos. (`BiddingSeasonalityAdjustment`,
  `BiddingDataExclusion`)
- **Ad Customizers** — texto dinámico en RSAs (precios, stock, countdown) sin duplicar
  anuncios. (`CustomizerAttribute`, `CustomerCustomizer`, `AdGroupCustomizer`)

### 🟡 Media prioridad
- **Shopping / PMax — Listing Groups & Merchant Center** — segmentar el feed en PMax.
  (`MerchantCenterLink`, `AssetGroupListingGroupFilter`)
- **Audiencias avanzadas** — custom / combined / in-market / affinity (hoy solo
  rule-based). (`CustomAudience`, `CombinedAudience`, `UserInterest`)
- **Campaign Drafts** — borradores antes de experimento/producción. (`CampaignDraft`)
- **Batch Jobs** — mutaciones masivas asíncronas. (`BatchJobService`)
- **Brand Safety** — exclusiones de placement / topic / content en Display/Video/PMax.
  (`CampaignCriterion`, `AdGroupCriterion`)

### 🟢 Baja prioridad / cubrible con `execute_gaql`
- **Bid / Budget Simulations** — estimar impacto de subir/bajar bids/presupuesto.
  (`CampaignSimulation`, `AdGroupSimulation`)
- **Account Budgets / Billing** — visibilidad de presupuestos de cuenta (MCC).
  (`AccountBudget`, `BillingSetup`)
- **Smart Campaigns / Keyword Themes** — campañas Smart para PYMEs (nicho).
  (`SmartCampaignSetting`)

### Patrón de implementación
- Un archivo por dominio en `ads_mcp/tools/`, decorador `@mcp.tool()`, helpers
  `get_ads_client()` / `execute_gaql()` desde `ads_mcp.tools.api`.
- Validar toda entrada interpolada con `ads_mcp.tools.validation`.
- Registrar el dominio como *namespace* en `tools_config.yaml` y `ads_mcp/config.py`.
- Agregar tests del módulo (mockear `get_ads_client` / `execute_gaql`) y subir el ratchet.
