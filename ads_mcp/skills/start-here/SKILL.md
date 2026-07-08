---
name: start-here
description: Orient a user who isn't sure what they need from Google Ads. Interview them briefly about their goal and route them to the right workflow or tools. Use when the user asks an open-ended question like "what can you do?", "help me with my account", "where do I start?", or gives no clear task.
---

# Start Here — Google Ads Concierge

Esta skill orienta a un usuario que no sabe exactamente qué pedir. En vez de
listar 78 herramientas, **entrevístalo** y **rutéalo** al flujo correcto.

## Cómo actuar

### 1. Confirma la cuenta
Si no tienes el `customer_id`, usa `list_accessible_accounts` y pide al usuario
que elija la cuenta con la que quiere trabajar.

### 2. Pregunta el objetivo (una sola pregunta, clara)
Ofrece opciones concretas en lenguaje de negocio, no técnico. Por ejemplo:

> ¿Qué te gustaría lograr hoy?
> 1. **Gastar mejor** — encontrar y recortar gasto que no convierte
> 2. **Vender/generar más leads** — mejorar rendimiento o lanzar algo nuevo
> 3. **Entender un problema** — cayeron mis conversiones / mis clics son caros
> 4. **Probar un cambio** con seguridad antes de aplicarlo
> 5. **Revisar todo** — una auditoría completa de la cuenta
> 6. **Otra cosa** — cuéntame en tus palabras

### 3. Rutea según la respuesta

| El usuario quiere… | Rutea a la skill / tools |
|---|---|
| Recortar gasto inútil | **`wasted-spend-audit`** |
| Lanzar una campaña nueva | **`campaign-launch`** |
| Entender por qué cayó algo | **`account-performance-diagnostics`** |
| Clics caros / relevancia baja | **`quality-score-optimization`** |
| Probar un cambio (A/B) | **`experiment-workflow`** |
| Subir ventas del CRM | **`offline-conversions`** |
| Auditoría completa | **`account-audit`** |
| Solo ver datos puntuales | tools de reporting (`get_campaign_performance`, `get_search_terms_report`, `execute_gaql`) |

### 4. Da el primer paso, no solo el nombre
No te limites a decir "usa X". **Arranca** el flujo: por ejemplo, si eligió
"gastar mejor", corre el primer paso de `wasted-spend-audit` (traer search terms
sin conversión) y muéstrale un hallazgo concreto para enganchar.

## Reglas
- Habla en lenguaje de negocio; traduce los términos técnicos.
- **Confirma antes de cualquier cambio de escritura.** En modo exploración, solo lee.
- Si el usuario ya sabe lo que quiere, sáltate la entrevista y ve directo al flujo.
