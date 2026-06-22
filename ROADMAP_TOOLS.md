# Roadmap de Herramientas — Google Ads MCP

Herramientas de la Google Ads API que **aún no** están cubiertas por nuestras 78 tools
actuales y que aportarían valor. Pensado como backlog para trabajar a futuro.

Estado actual: **78 tools** (ver `CLAUDE.md` para el listado completo).

Leyenda de prioridad:
- 🔴 **Alta** — alto impacto, encaja con flujos que ya usamos (conversiones offline, PPC).
- 🟡 **Media** — útil en escenarios específicos (e-commerce, Display/Video, brand safety).
- 🟢 **Baja** — nicho o cubrible hoy con `execute_gaql`.

---

## 🔴 Alta prioridad

### Conversion Value Rules
- **Tools propuestas:** `create_conversion_value_rule`, `list_conversion_value_rules`, `remove_conversion_value_rule`
- **Qué resuelve:** ajustar el *valor* de las conversiones según ubicación, dispositivo o
  audiencia (p. ej. un lead de Lima vale más que uno de provincia). Alimenta Smart Bidding.
- **Recursos API:** `ConversionValueRule`, `ConversionValueRuleSet`

### Conversion Adjustments (retractions / restatements)
- **Tools propuestas:** `upload_conversion_adjustments`
- **Qué resuelve:** corregir o anular conversiones ya subidas (devoluciones, leads
  descalificados por el CRM). Hoy solo tenemos *upload* de conversiones, no su ajuste.
- **Recursos API:** `ConversionAdjustmentUploadService`
- **Nota:** complementa directamente `upload_click_conversions` / `upload_call_conversions`.

### Seasonality Adjustments / Data Exclusions
- **Tools propuestas:** `create_seasonality_adjustment`, `create_data_exclusion`, `list_bidding_signals`
- **Qué resuelve:** avisar a Smart Bidding de picos esperados (Black Friday, Cyber Wow,
  lanzamientos) o excluir periodos anómalos (caída de tracking) para que no distorsione el modelo.
- **Recursos API:** `BiddingSeasonalityAdjustment`, `BiddingDataExclusion`

### Ad Customizers
- **Tools propuestas:** `create_customizer_attribute`, `set_customizer_value`, `list_customizers`
- **Qué resuelve:** texto dinámico en RSAs (precios, stock, cuenta regresiva) sin duplicar anuncios.
- **Recursos API:** `CustomizerAttribute`, `CustomerCustomizer`, `AdGroupCustomizer`

---

## 🟡 Media prioridad

### Shopping / Performance Max — Listing Groups & Merchant Center
- **Tools propuestas:** `link_merchant_center`, `set_listing_group_filters`, `list_product_groups`
- **Qué resuelve:** segmentar el feed de productos dentro de PMax/Shopping (por marca,
  categoría, ID). Clave para e-commerce.
- **Recursos API:** `MerchantCenterLink`, `AssetGroupListingGroupFilter`, `ListingGroup`

### Audiencias avanzadas (Custom / Combined / In-Market / Affinity)
- **Tools propuestas:** `create_custom_audience`, `create_combined_audience`, `apply_inmarket_audience`
- **Qué resuelve:** hoy `create_audience` solo hace listas rule-based de visitantes web.
  Faltan audiencias por intención/interés (in-market, affinity) y combinadas.
- **Recursos API:** `CustomAudience`, `CombinedAudience`, `UserInterest`

### Campaign Drafts
- **Tools propuestas:** `create_campaign_draft`, `promote_campaign_draft`, `list_campaign_drafts`
- **Qué resuelve:** preparar cambios en un borrador antes de pasarlos a experimento o a producción.
- **Recursos API:** `CampaignDraft`

### Batch Jobs (mutaciones masivas)
- **Tools propuestas:** `create_batch_job`, `add_batch_job_operations`, `run_batch_job`, `get_batch_job_results`
- **Qué resuelve:** ejecutar miles de mutaciones de forma asíncrona sin topar límites de la API.
  Útil para reestructuraciones grandes de cuenta.
- **Recursos API:** `BatchJobService`

### Brand Safety — Exclusiones de Placement / Topic / Content
- **Tools propuestas:** `add_negative_placements`, `exclude_topics`, `set_content_exclusions`
- **Qué resuelve:** evitar que anuncios de Display/Video/PMax aparezcan en sitios, apps o temas
  no deseados (brand safety).
- **Recursos API:** `CampaignCriterion` (placement/topic/content_label), `AdGroupCriterion`

---

## 🟢 Baja prioridad / cubrible con `execute_gaql`

### Bid Simulations / Landscapes
- **Tools propuestas:** `get_bid_simulation`, `get_budget_simulation`
- **Qué resuelve:** estimar el impacto en clics/conversiones de subir o bajar bids/presupuesto.
- **Recursos API:** `KeywordPlanBidSimulation`, `CampaignSimulation`, `AdGroupSimulation`
- **Nota:** parcialmente consultable hoy vía GAQL sobre las vistas `*_simulation`.

### Account Budgets / Billing
- **Tools propuestas:** `list_account_budgets`, `get_billing_setup`
- **Qué resuelve:** visibilidad de presupuestos de cuenta y configuración de facturación (MCC).
- **Recursos API:** `AccountBudget`, `BillingSetup`

### Smart Campaigns / Keyword Themes
- **Tools propuestas:** `create_smart_campaign`, `suggest_keyword_themes`
- **Qué resuelve:** campañas Smart para PYMEs. Nicho; rara vez lo gestiona un equipo PPC avanzado.
- **Recursos API:** `SmartCampaignSetting`, `SmartCampaignSuggestService`

---

## Notas de implementación
- Reutilizar el patrón existente: un archivo por dominio en `ads_mcp/tools/`, decorador
  `@mcp.tool()`, y helpers `get_ads_client()` / `execute_gaql()` desde `ads_mcp.tools.api`.
- Cada nuevo dominio se registra como un *namespace* en `tools_config.yaml` (ver infra de config).
- Priorizar las 🔴: son las que más se alinean con el uso actual (conversiones offline + PPC).
