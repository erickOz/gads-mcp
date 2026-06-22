---
name: account-performance-diagnostics
description: Diagnose Google Ads account performance issues — conversion/value loss, low lead flow, and lost opportunities due to ad rank, bids, or budgets. Use this skill to guide which MCP tools and GAQL queries to run when troubleshooting a performance drop.
---

# Account Performance Diagnostics Skill

Guía para diagnosticar caídas de rendimiento usando las herramientas de este MCP.

> Adaptado del skill oficial de `googleads/google-ads-mcp` a nuestras herramientas
> específicas (que son más directas que el `search` genérico del repo oficial).

## Herramientas relevantes de este servidor

- Descubrir campos/vistas: `get_reporting_fields_doc`, `get_reporting_view_doc`, `get_gaql_doc`
- Rendimiento: `get_campaign_performance`, `get_keyword_performance`, `get_search_terms_report`,
  `get_auction_insights`, `get_ad_performance`, `get_quality_score_report`
- Consultas libres: `execute_gaql`
- Conversiones: `list_conversion_actions`
- Auditoría de cambios: `get_change_history`

---

## Workflows

### 1. Pérdida de conversiones o de valor de conversión

Cuando las conversiones o el valor de conversión caen de golpe:

1. **Confirmar campos** (opcional): `get_reporting_view_doc` / `get_reporting_fields_doc`
   para los nombres correctos de métricas/segmentos.
2. **Medir el rendimiento**: `get_campaign_performance` para el periodo de la caída vs. el
   periodo previo. Si necesitas segmentar más fino, usa `execute_gaql` con:
   - **Recurso**: `campaign` o `ad_group`
   - **Campos**: `campaign.name`, `metrics.conversions`, `metrics.conversions_value`, `metrics.cost_micros`
   - **Segmentos**: `segments.date`, `segments.device`, `segments.conversion_action`
   - **Condición**: comparar ventanas (`segments.date BETWEEN ...`)
3. **Analizar**: ¿la pérdida es de un dispositivo concreto (mobile vs desktop) o de una
   acción de conversión específica?
4. **Revisar uploads offline**: si subes conversiones desde CRM, revisa
   `list_conversion_actions` y consulta vía `execute_gaql` la vista
   `offline_conversion_upload_conversion_action_summary` para detectar fallos de carga.

### 2. Oportunidades perdidas (Impression Share)

Para detectar oportunidades perdidas por ad rank, bids o presupuesto:

1. **Consultar impression share**: `get_campaign_performance` (incluye IS) o `execute_gaql`
   sobre `campaign` con: `metrics.search_impression_share`,
   `metrics.search_rank_lost_impression_share`, `metrics.search_budget_lost_impression_share`.
2. **Interpretar**:
   - `search_budget_lost_impression_share` alto → se pierde por **presupuesto** limitado.
   - `search_rank_lost_impression_share` alto → se pierde por **ad rank** (bid o calidad).
3. **Profundizar en calidad**: si el problema es rank, cruza con `get_quality_score_report`
   y `get_auction_insights` (overlap y outranking vs. competidores).

### 3. Bajo flujo de leads ("¿por qué bajaron mis leads estos días?")

1. **Confirmar la caída**: `get_campaign_performance` segmentado por fecha, últimos días
   vs. periodo previo.
2. **Aislar la causa**:
   - ¿Cayó el **tráfico** (clics, impresiones)?
   - ¿Cayó la **tasa de conversión** (conversiones/clics)?
3. **Si cayó el tráfico** → Workflow 2 (impression share): ¿presupuesto, rank, o bajó el
   volumen de búsqueda en general?
4. **Si cayó la conversión** → desglosa por `segments.device` o `segments.conversion_action`
   (vía `execute_gaql`) para ver qué área falla. Revisa también `get_search_terms_report`
   por si entró tráfico irrelevante.
5. **Revisar cambios**: `get_change_history` para ver si se tocaron bids, presupuestos o
   targeting cerca del inicio de la caída.
   - *Nota*: las consultas a `change_event` requieren `LIMIT <= 10000`.
