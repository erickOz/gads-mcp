---
name: wasted-spend-audit
description: Find and cut wasted ad spend in a Google Ads account — keywords and search terms that cost money but do not convert, low Quality Score keywords, and budget lost to irrelevant queries. Use this skill when the user asks to reduce wasted spend, audit performance, find non-converting keywords, or clean up search terms.
---

# Wasted Spend Audit Skill

Playbook para encontrar y recortar gasto desperdiciado usando las herramientas
de este MCP. El objetivo es identificar dónde se va el dinero sin retorno y
proponer acciones concretas (pausar, agregar negativos, ajustar bids).

## Antes de empezar
- Confirma la cuenta con `list_accessible_accounts` si no tienes el `customer_id`.
- Usa un rango de al menos `LAST_30_DAYS` para tener señal estadística.
- **No apliques cambios sin confirmar con el usuario.** Primero reporta, luego actúa.

## Workflow

### 1. Search terms que gastan y no convierten (mayor impacto)
1. `get_search_terms_report` con `date_range=LAST_30_DAYS` y `min_impressions` alto
   (p. ej. 10) para reducir ruido.
2. Marca como desperdicio los términos con: **cost > 0 y conversions = 0** (ordena
   por costo descendente).
3. Propón al usuario:
   - Términos claramente irrelevantes → `add_negative_keywords` (ad group) o
     `add_campaign_negative_keywords` (campaña).
   - Términos relevantes pero caros → revisar la landing/oferta, no negativizar.

### 2. Keywords con gasto sin conversión
1. `get_keyword_performance` con el mismo rango.
2. Identifica keywords con **cost alto y 0 conversiones** o **CPA muy por encima**
   del promedio de la cuenta.
3. Propón: pausar con `update_keyword_status` (status=PAUSED) o bajar el bid con
   `update_keyword_bid`. Para EXACT/PHRASE de bajo rendimiento, pausar suele ser
   mejor que negativizar.

### 3. Quality Score bajo (encarece cada clic)
1. `get_quality_score_report`.
2. Para keywords con **Quality Score < 5**, revisa los componentes (ad relevance,
   expected CTR, landing page experience).
3. Acción según el componente débil:
   - *Ad relevance* baja → reescribe el RSA con `replace_responsive_search_ad`
     incluyendo la keyword en los headlines.
   - *Landing page* baja → recomendación al usuario (no accionable vía API).

### 4. Presupuesto perdido por baja relevancia
1. `get_campaign_performance` y revisa `search_budget_lost_impression_share` vs
   `search_rank_lost_impression_share`.
2. Si se pierde por presupuesto en campañas que SÍ convierten bien, sugiere mover
   presupuesto desde las que desperdician (con `update_campaign_budget`).

## Entregable
Resume en una tabla: **dónde se desperdicia, cuánto cuesta, y la acción
recomendada** (con la tool exacta). Pide confirmación antes de ejecutar cualquier
cambio de escritura.
