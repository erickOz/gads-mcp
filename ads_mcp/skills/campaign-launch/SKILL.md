---
name: campaign-launch
description: Build a new Google Ads Search campaign end to end — budget, campaign, ad group, responsive search ad, keywords, negative keywords, and sitelink extensions. Use this skill when the user wants to launch, create, or set up a new Search campaign from scratch.
---

# Campaign Launch Skill

Playbook para lanzar una campaña de Search completa y segura usando las
herramientas de este MCP. El orden importa: cada paso depende de los IDs del
anterior.

## Principios
- **Crea todo en PAUSED** (es el default de `create_campaign`). Solo activar con
  confirmación explícita del usuario al final.
- Confirma con el usuario los datos clave (presupuesto, oferta de puja, URLs)
  antes de escribir.
- Trabaja con micros: $1.00 = 1.000.000 micros.

## Workflow

### 1. Reúne los datos mínimos
Pregunta al usuario si falta algo:
- `customer_id` (o usa `list_accessible_accounts`)
- nombre de campaña, presupuesto diario, estrategia de puja
- tema/keywords semilla, URL final, textos de anuncio

### 2. Crea la campaña (incluye su presupuesto)
- `create_campaign` con `daily_budget_micros`, `status="PAUSED"` y la
  `bidding_strategy` elegida (para TARGET_CPA/ROAS pasa el target). Guarda el
  `campaign_id` devuelto.

### 3. Crea el grupo de anuncios
- `create_ad_group` con el `campaign_id` y un `cpc_bid_micros`. Guarda el
  `ad_group_id`.

### 4. Agrega keywords
- `add_keywords` al `ad_group_id`. Recomienda EXACT/PHRASE para control; evita
  BROAD salvo que el usuario lo pida. Agrupa keywords temáticamente afines.

### 5. Agrega negativos de arranque
- `add_negative_keywords` (o `add_campaign_negative_keywords`) con términos
  obvios a excluir (p. ej. "gratis", "empleo", "pdf") para no desperdiciar desde
  el día 1.

### 6. Crea el anuncio responsive (RSA)
- `create_responsive_search_ad` con 8–15 headlines y 3–4 descriptions. Incluye
  la keyword principal en al menos 2 headlines para mejorar Quality Score.

### 7. Agrega extensiones de sitelink
- `add_sitelink_assets` con 4+ sitelinks relevantes (mejoran CTR y Ad Rank).

### 8. Revisa y activa
- Resume todo lo creado (IDs y nombres). **Pide confirmación.**
- Solo entonces: `update_campaign_status` a `ENABLED`.

## Entregable
Una tabla con cada entidad creada (campaña, grupo, anuncio, keywords, negativos,
sitelinks) y sus IDs, terminando con el recordatorio de que la campaña está en
PAUSED hasta que el usuario confirme activarla.
