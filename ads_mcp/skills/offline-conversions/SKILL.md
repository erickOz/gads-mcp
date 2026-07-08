---
name: offline-conversions
description: Upload offline conversions from a CRM into Google Ads — set up the conversion action, then import click (gclid) or call conversions so Smart Bidding learns from real sales, not just online form fills. Use this skill when the user wants to import CRM sales, track offline/closed deals, upload gclid conversions, or feed Smart Bidding with offline revenue.
---

# Offline Conversions Skill

Muchos negocios cierran ventas offline (llamadas, visitas, checkout diferido). Si
solo cuentas conversiones online, Smart Bidding optimiza para la señal equivocada.
Este playbook importa las ventas reales del CRM de vuelta a Google Ads.

## Cómo funciona
Google graba un **gclid** (Google Click ID) cuando alguien hace clic en tu anuncio.
Tu CRM debe capturar ese gclid en el lead. Cuando el lead se convierte en venta,
subes el gclid + valor + fecha a Google Ads, que lo atribuye al clic original.

## Pre-requisitos (confírmalos con el usuario)
- El CRM captura y almacena el **gclid** de cada lead.
- Existe (o se creará) una **conversion action** de tipo apropiado.
- Las fechas están en formato `yyyy-MM-dd HH:mm:ss+ZZ:ZZ`.

## Workflow

### 1. Asegura la conversion action
- `list_conversion_actions` para ver si ya existe una adecuada.
- Si no, `create_conversion_action` (category típica: `LEAD` o `PURCHASE`). Si las
  ventas tienen valor monetario, configúralo. Guarda el `conversion_id`.

### 2. Prepara los datos del CRM
Para conversiones por **clic** (lo más común), cada registro necesita:
- `gclid`, `conversion_action_id`, `conversion_date_time`, `conversion_value`,
  y opcionalmente `currency_code`.
Para conversiones por **llamada**, usa `caller_id` y `call_start_date_time`.

### 3. Sube las conversiones
- `upload_click_conversions` (o `upload_call_conversions`) con `partial_failure=True`
  para que las válidas entren aunque algunas fallen.
- Revisa el resultado: `successful_count`, `failed_count` y
  `partial_failure_errors`. Reporta los errores al usuario con su causa.

### 4. Diagnostica fallos comunes
- gclid inválido o expirado (la ventana de subida típica es ~90 días).
- `conversion_date_time` anterior al clic, o fuera de la ventana de lookback.
- conversion_action no habilitada para import.

### 5. Cierra el loop
- Recuerda al usuario que tras acumular suficientes conversiones offline, conviene
  que Smart Bidding (Target CPA/ROAS) optimice hacia ellas. Enlaza con el flujo de
  estrategia de puja si corresponde.

## Entregable
Resumen de la subida (cuántas entraron, cuántas fallaron y por qué) y el siguiente
paso recomendado. Nunca subas datos sin confirmar con el usuario que el mapeo de
campos del CRM es correcto.
