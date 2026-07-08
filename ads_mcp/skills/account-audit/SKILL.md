---
name: account-audit
description: Run a full proactive audit of a Google Ads account and return a prioritized action plan — spend efficiency, wasted spend, Quality Score, impression share (lost opportunities), and structural gaps. Use when the user asks for an audit, a health check, an account review, or "how can I improve my account?".
---

# Account Audit — Revisión Completa

Analiza la cuenta de forma proactiva y entrega un **plan de acción priorizado**
por impacto. El objetivo NO es volcar datos: es decir *qué está mal, cuánto
cuesta, y qué hacer*. Todo en modo lectura; no cambies nada sin confirmación.

## Alcance
Trabaja sobre `LAST_30_DAYS` (o el rango que pida el usuario). Confirma la cuenta
con `list_accessible_accounts` si falta el `customer_id`.

## Áreas a auditar (recolecta primero, analiza después)

### A. Eficiencia de gasto
- `get_campaign_performance`: cost, conversiones, CPA/ROAS por campaña.
- Marca campañas con **gasto alto y 0/pocas conversiones** o CPA muy sobre el promedio.

### B. Gasto desperdiciado
- `get_search_terms_report` (min_impressions alto): términos con **cost > 0 y
  conversions = 0**.
- `get_keyword_performance`: keywords que gastan sin convertir.
- Señal de gap: si hay términos irrelevantes gastando, faltan negativos.

### C. Quality Score
- `get_quality_score_report`: cuenta keywords con **QS < 5** y su componente débil
  (ad relevance / expected CTR / landing page).

### D. Oportunidades perdidas (Impression Share)
- De `get_campaign_performance`: `search_budget_lost_impression_share` (pierdes por
  presupuesto) vs `search_rank_lost_impression_share` (pierdes por rank/calidad).

### E. Gaps estructurales
- ¿Campañas sin negativos? ¿Sin extensiones? (`list_assets`)
- ¿Anuncios de baja fuerza? (`get_ad_performance`, ad strength)
- Revisa recomendaciones de Google: `list_recommendations`.

## Entregable: plan priorizado
Presenta una **tabla ordenada por impacto** (no por área), así:

| Prioridad | Hallazgo | Impacto (S/ o métrica) | Acción recomendada | Skill/tool |
|---|---|---|---|---|
| 🔴 Alta | Términos sin conversión gastando | S/ X/mes | Agregar negativos | `wasted-spend-audit` |
| 🔴 Alta | Presupuesto perdido en campaña que convierte | IS budget-lost 40% | Subir/mover presupuesto | `update_campaign_budget` |
| 🟡 Media | 12 keywords con QS < 5 | encarece CPC | Reescribir RSAs | `quality-score-optimization` |
| … | … | … | … | … |

Cierra con: **los 3 movimientos de mayor impacto** y pregunta al usuario con
cuál quiere empezar. Recién ahí, y con confirmación, ejecuta cambios de escritura.

## Reglas
- Todo el diagnóstico es lectura. **Nunca** modifiques la cuenta durante la auditoría.
- Cuantifica en dinero cuando puedas (convierte micros: 1.000.000 = 1 unidad).
- Enlaza cada hallazgo con la skill que lo resuelve para que el usuario continúe.
