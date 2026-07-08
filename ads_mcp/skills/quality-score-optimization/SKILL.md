---
name: quality-score-optimization
description: Diagnose and improve low Quality Score keywords in Google Ads — identify which component (expected CTR, ad relevance, landing page experience) is weak and take action to raise it. Use this skill when the user asks about Quality Score, why clicks are expensive, or how to improve ad rank/relevance.
---

# Quality Score Optimization Skill

Quality Score (1–10) afecta directamente cuánto pagas por clic y tu Ad Rank.
Subirlo baja el CPC y mejora posición. Este playbook diagnostica el componente
débil y propone la acción correcta.

## Contexto rápido
QS tiene 3 componentes, cada uno calificado BELOW_AVERAGE / AVERAGE / ABOVE_AVERAGE:
- **Expected CTR** — qué tan probable es que hagan clic.
- **Ad relevance** — qué tan alineado está el anuncio con la keyword.
- **Landing page experience** — relevancia y calidad de la página destino.

## Workflow

### 1. Identifica las keywords problema
- `get_quality_score_report` (idealmente filtrado por campaña/grupo).
- Prioriza keywords con **QS < 5** y volumen de impresiones relevante (las de bajo
  QS y alto gasto primero).

### 2. Diagnostica el componente débil
Para cada keyword problemática, mira cuál componente está BELOW_AVERAGE:

| Componente débil | Causa típica | Acción |
|---|---|---|
| Ad relevance | El anuncio no menciona la keyword | Reescribir RSA (ver paso 3) |
| Expected CTR | Anuncio poco atractivo / keyword muy amplia | Mejorar copy + revisar match type |
| Landing page | Página lenta o poco relevante | Recomendación al usuario (no API) |

### 3. Acción: mejorar Ad relevance / CTR
- Revisa el anuncio actual con `get_ad_performance` (ad strength, textos).
- `replace_responsive_search_ad`: incluye la **keyword exacta en 2+ headlines**,
  alinea descriptions con la intención, agrega un CTA claro.
- Considera mover keywords muy distintas a su propio ad group (SKAG-like) para
  que el anuncio sea más específico.

### 4. Acción: estructura
- Si una keyword amplia arrastra el CTR, evalúa cambiar match type
  (`update_keyword_status` para pausar la amplia y `add_keywords` con EXACT/PHRASE).

### 5. Reduce desperdicio en paralelo
- Cruza con `get_search_terms_report`: agrega negativos
  (`add_negative_keywords`) para que el anuncio solo se muestre en queries
  relevantes — esto sube el CTR esperado con el tiempo.

## Entregable
Tabla por keyword: QS actual, componente débil, acción recomendada y la tool
exacta. Para landing page, una recomendación clara al usuario (fuera del alcance
de la API). Pide confirmación antes de reescribir anuncios o pausar keywords.
