---
name: experiment-workflow
description: Run a safe A/B test (campaign experiment) in Google Ads — create the experiment, schedule it, evaluate the results, then promote the winner or end it. Use this skill when the user wants to A/B test a change, run a campaign experiment, or test a new bid/budget/strategy before applying it.
---

# Experiment Workflow Skill

Los experimentos dividen el tráfico de una campaña entre un brazo de **control**
(la campaña original) y uno de **tratamiento** (una copia con tu cambio). Sirven
para validar un cambio con datos antes de aplicarlo a todo. Este playbook cubre
el ciclo completo de forma segura.

## Estados del experimento
`SETUP → INITIATED → ENABLED → (PROMOTED | GRADUATED | REMOVED)`

## Workflow

### 1. Define la hipótesis
Confirma con el usuario: qué campaña base, qué cambio se prueba (puja, presupuesto,
estrategia, anuncios), y el split de tráfico (50/50 es lo más común y estadísticamente
más rápido).

### 2. Crea el experimento
- `create_experiment` con `campaign_id` (la base = control) y
  `traffic_split_percent` para el tratamiento. Queda en estado **SETUP**.
- Guarda el `experiment_id`.

### 3. Aplica el cambio al brazo de tratamiento
- Realiza el cambio que quieres probar sobre la campaña de tratamiento (p. ej.
  `update_campaign_bidding_strategy`, `update_campaign_budget`, o nuevos anuncios).
- **No programes hasta que el cambio esté listo.**

### 4. Programa (ponlo en marcha)
- `schedule_experiment` → pasa a **INITIATED** y empieza a dividir tráfico.
- Informa al usuario que necesita tiempo y volumen para tener significancia
  (idealmente ≥2 semanas y conversiones suficientes en ambos brazos).

### 5. Evalúa resultados
- `list_experiments` para ver el estado.
- Compara control vs tratamiento con `get_campaign_performance` en ambas campañas:
  mira conversiones, CPA/ROAS y CTR. No decidas con pocos datos.

### 6. Decide
- **Gana el tratamiento** → `promote_experiment`: aplica los ajustes del
  tratamiento a la campaña original.
- **No concluyente o pierde** → `end_experiment`: devuelve el 100% del tráfico a
  la original sin cambios.

## Reglas de seguridad
- Nunca promuevas sin datos suficientes; explícalo si el usuario lo pide antes de
  tiempo.
- Antes de `promote_experiment` o `end_experiment`, resume el resultado y **pide
  confirmación** — son acciones que cambian la campaña en producción.
