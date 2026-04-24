# Informe de Rendimiento y Estrategia Google Ads
## Uniflex Perú — Campaña [Search] CA - Flex ERP | BOF
### Período analizado: últimos 30 días · Fecha: Abril 2026

---

## Lo Que Hemos Logrado

### Antes vs. Ahora

| | Antes | Ahora |
|---|---|---|
| Presupuesto diario | **$8/día** | **$15/día** |
| Impresiones mensuales | ~0 (presupuesto insuficiente) | **1,485** |
| Clics mensuales | ~0 | **125** |
| Conversiones | 0 | 0 (en análisis) |
| Estructura de grupos | 1 grupo genérico (ERP) | **6 grupos específicos** |
| Seguimiento UTM | Plantillas de seguimiento en conflicto | URLs con parámetros limpios y consistentes |

Con $8 diarios la campaña no tenía masa crítica para generar impresiones constantes. El incremento a $15 desbloqueó visibilidad real. Aún no hay conversiones registradas — el siguiente paso es diagnosticar la experiencia en la landing page, que los datos señalan como el factor limitante.

---

### De lo Genérico a lo Específico

**Antes:** Un solo grupo de anuncios (GA - ERP Genérico) competía por búsquedas como "qué es un ERP", "sistema ERP", "ERP empresas" — términos informativos donde el usuario no está listo para comprar y donde Uniflex compite con SAP, Oracle y Odoo.

**Ahora:** 6 grupos de anuncios segmentados por intención y vertical:

| Grupo de Anuncios | Intención | Nivel de Competencia |
|---|---|---|
| GA - Distribución | Distribuidoras mayoristas buscando ERP | Localizada |
| GA - ERP Ferreterías | Ferreterías y distribuidoras de construcción | Localizada |
| GA - ERP Farmacéuticas | Distribuidoras de medicamentos | Especializada |
| GA - ERP Consumo Masivo | Distribuidoras de alimentos y bebidas | Nueva |
| GA - Brand Uniflex | Usuarios que ya conocen la marca | Propia |
| GA - Competidores | Usuarios evaluando software similar | Localizada |

Cada grupo tiene keywords específicas, copy de anuncio alineado al sector, y URL de destino diferenciada con parámetros UTM propios.

---

## Por Qué el Anuncio Aparece (o No) — El Ad Rank

Cada vez que un usuario hace una búsqueda, Google calcula en tiempo real un valor llamado **Ad Rank** para cada anunciante. Este valor determina si el anuncio se muestra y en qué posición. No es simplemente "quién paga más" — es una combinación de 6 factores.

---

## Factor 1 — La Puja (Bid)

**¿Qué es?**
El CPC máximo que estamos dispuestos a pagar por un clic. Es el "techo financiero" del Ad Rank. Sin una puja mínimamente competitiva, ninguna mejora de calidad puede ganar la subasta.

**Lo que hemos hecho:**
- Pujas diferenciadas por grupo según el valor del clic en cada vertical
- Brand: $0.35/clic (términos de marca propios, sin competencia real)
- Distribución / Ferreterías: $2.30–$2.44/clic (competencia media-alta)
- Competidores: $0.75/clic

**Lo que podemos mejorar:**
- Aumentar presupuesto diario (argumento en la sección de Cuota de Impresiones)
- Evaluar Smart Bidding (Target CPA) una vez que tengamos conversiones registradas — Google optimiza la puja en tiempo real por dispositivo, hora y perfil del usuario

---

## Factor 2a — CTR Esperado

**¿Qué es?**
Google predice la probabilidad de que alguien haga clic en el anuncio comparado con los competidores en la misma subasta. Un CTR alto sube el Ad Rank sin pagar más.

**Lo que hemos hecho:**
- Anuncios RSA (Responsive Search Ads) con 15 titulares y 4 descripciones cada uno — Google prueba combinaciones automáticamente y prioriza las que generan más clics
- Múltiples variantes por grupo para A/B testing continuo

**Resultados reales de CTR por grupo:**

| Grupo | CTR Desktop | CTR Mobile |
|---|---|---|
| GA - Brand Uniflex | 52.2% | 52.6% |
| GA - ERP Ferreterías | 29.4% | 30.8% |
| GA - ERP Farmacéuticas | 50.0% | 10.0% |
| GA - Distribución | 4.9% | 10.0% |
| GA - Competidores | 3.8% | 0% |

**Lo que podemos mejorar:**
- Incorporar titulares con comparativa directa en el grupo Competidores: "¿Evaluando Paqari? Conoce Uniflex"
- Probar titulares con urgencia o beneficio tangible: "Demo en 24 Horas" o "Implementación en 45 Días"

---

## Factor 2b — Relevancia del Anuncio

**¿Qué es?**
Qué tan alineado está el texto del anuncio con la intención exacta de la búsqueda. Es el factor donde más control directo tenemos como agencia.

**Lo que hemos hecho:**
- Segmentación por vertical: el usuario que busca "erp para ferretería" ve un anuncio que menciona ferreterías, no un mensaje genérico de ERP
- Display paths personalizados: `/erp/ferreteria`, `/erp/distribucion`, `/erp/uniflex` — refuerzan visualmente la relevancia
- Todos los grupos con **Creative Quality: ABOVE AVERAGE** según Google — el copy es relevante en el 100% de los casos medidos

**Lo que podemos mejorar:**
- Grupo Farmacéuticas: aún sin suficientes datos de QS — monitorear en 2–3 semanas
- Grupo Consumo Masivo: recién creado, necesita período de aprendizaje

---

## Factor 2c — Experiencia en la Landing Page

**¿Qué es?**
Google evalúa si la página de destino responde exactamente a lo que el usuario buscó, si carga rápido, y si tiene un llamado a la acción claro. Un landing page débil arrastra todo el Quality Score hacia abajo, sube el CPC real y baja la posición.

**Diagnóstico actual por keyword:**

| Keyword | Quality Score | Landing Page | Interpretación |
|---|---|---|---|
| "uniflex del peru" | 10/10 | ABOVE AVERAGE | Perfecta — usuario busca la marca y llega a la web de la marca |
| "uniflex peru" | 8/10 | AVERAGE | Buena |
| "sistema uniflex" | 5/10 | AVERAGE | La página podría reflejar más el nombre de marca |
| "nextbyn peru" | 5/10 | **BELOW AVERAGE** | Usuario busca "alternativa a Nextbyn", llega a página genérica de ERP |
| "paqari" | 3/10 | **BELOW AVERAGE** | Mismo problema — la landing no menciona la comparativa |
| "erp farmacia" | 3/10 | **BELOW AVERAGE** | No existe página específica de farmacias |

**Impacto de un QS bajo:**
Un Quality Score de 3/10 puede significar pagar hasta **2–3 veces más por clic** que un competidor con QS 7/10 para obtener la misma posición.

**Lo que hemos hecho:**
- Iniciamos prueba A/B cambiando la URL de destino de `/erp-para-distribuidoras/` a `/erp/` en los anuncios de mayor CTR — resultado en evaluación

**Lo que podemos mejorar:**
- Crear landing pages específicas para los grupos de mayor inversión:
  - `/erp-ferreteria/` — mencionar control de inventario ferretero, créditos, despacho
  - `/alternativa-paqari/` — comparativa directa con Paqari
  - `/erp-farmacias/` — control de lotes, vencimientos, regulación DIGEMID
- Este cambio puede subir el QS de 3 a 7, **reduciendo el CPC real hasta 30–40%**

---

## Factor 3 — Umbrales Mínimos de Ad Rank

**¿Qué es?**
Google establece un umbral de calidad mínima para aparecer en las posiciones premium (Top 3 de la página). Aunque la puja sea alta, si la calidad no supera el umbral, el anuncio aparece más abajo o no aparece.

**Estado actual:**
- Top Impression Share: **14.7%** — Uniflex aparece en los 3 primeros resultados en menos de 2 de cada 10 subastas donde participa
- Absolute Top IS: **~10%** — aparece en posición #1 en 1 de cada 10 subastas

**Acción:** Este factor no se controla directamente. Se eleva indirectamente mejorando el Quality Score (Factor 2) y aumentando las pujas (Factor 1).

---

## Factor 4 — Competitividad de la Subasta

**¿Qué es?**
Si los competidores pujan agresivamente o tienen QS alto, el umbral de la subasta sube para todos. No podemos controlar lo que hace la competencia, pero sí podemos elegir estratégicamente en qué subastas participamos.

### Con quiénes compite Uniflex en realidad

Los datos de búsqueda de la campaña revelan algo clave: **Uniflex no compite en las mismas subastas que SAP, Oracle o Odoo.** Los competidores reales son ERPs peruanos locales de escala comparable:

| Competidor | Origen | Presencia en nuestras subastas | Nivel de amenaza |
|---|---|---|---|
| **Saurie ERP** | Perú | Alta (4 clics en nuestra cuenta) | Real — mismo mercado |
| **KeyFacil ERP** | Perú | Media (2 clics) | Real |
| **GYO Manager** | Perú | Media (1 clic) | Real |
| **Imperium Sistema** | Perú | Media | Real |
| **Nisira** | Perú | Media | Real |
| **Kame / Kame One** | Regional | Baja | Monitorear |
| **Kontroller ERP** | Local | Baja | Monitorear |
| SAP / Oracle | Global enterprise | Excluidos activamente ✅ | No competimos con ellos |
| Odoo | Open source global | Excluidos activamente ✅ | No competimos con ellos |
| Defontana | Chile (mediano) | Excluido activamente ✅ | No competimos con ellos |

> Hemos configurado las campañas para **no gastar en subastas imposibles de ganar**. Odoo, SAP y Defontana son negativos a nivel de campaña. Uniflex compite donde puede ganar: ERPs locales peruanos sin el respaldo de marca global de SAP ni la inversión de un ERP enterprise.

**Lo que podemos mejorar:**
- Incorporar a Saurie, KeyFacil, GYO Manager, Nisira y Kame al grupo GA - Competidores — son competidores peruanos donde Uniflex tiene ventaja diferencial en soporte local, especialización en distribución y precio

---

## Factor 5 — Contexto de la Búsqueda

**¿Qué es?**
Google ajusta el Ad Rank en tiempo real según el dispositivo, la ubicación, la hora del día, y las señales del usuario. Podemos aprovechar esto con ajustes de puja inteligentes.

**Lo que hemos hecho:**
- RSAs adaptan automáticamente el formato al dispositivo
- Todos los anuncios tienen parámetros UTM diferenciados por campaña para análisis preciso en GA4

**Datos reales por dispositivo:**

| Grupo | CTR Desktop | CTR Mobile | Conclusión |
|---|---|---|---|
| GA - Brand Uniflex | 52.2% | 52.6% | Rendimiento uniforme |
| GA - ERP Ferreterías | 29.4% | 30.8% | Alta intención en ambos |
| GA - Distribución | 4.9% | 10.0% | Mobile duplica en gestores de distribución |
| GA - ERP Farmacéuticas | 50.0% | 10.0% | Decisión en desktop (entorno corporativo) |

**Lo que podemos mejorar:**
- Ajuste de puja por dispositivo: +20% mobile en Distribución y Consumo Masivo
- Programación de anuncios: concentrar presupuesto en horario laboral L–V 8am–7pm
- Segmentación geográfica: Lima Metropolitana como foco principal (mayor concentración de distribuidoras)

---

## Factor 6 — Impacto de Assets (Extensiones)

**¿Qué es?**
Google evalúa si los assets adicionales (sitelinks, callouts, imágenes, formularios) mejorarán el rendimiento del anuncio. Más assets relevantes = anuncio más grande visualmente = mayor CTR = mayor Ad Rank. **Es la palanca más subestimada porque mejora la posición sin aumentar la puja.**

**Assets activos actualmente:**

| Tipo | Cantidad | Ejemplos |
|---|---|---|
| Sitelinks | 15+ | Solicitar Demo, App Móvil para Ventas, ERP para Distribuidoras, Facturación Electrónica, Nuestros Clientes, Flex WMS, Módulo BI |
| Callouts | 18+ | Certificado ISO 27001, +25 Años de Trayectoria, Soporte Local en Perú, Implementación Rápida, Demostración SIN Costo |
| Structured Snippets | 6 | Módulos del sistema, Marcas (Flex Business ERP, Flex WMS, Intellia Flex, Flex Mobile), Tipos de Ferreterías |

**Assets faltantes que subirían el Ad Rank:**

| Asset | Beneficio | Prioridad |
|---|---|---|
| **Price Asset** | Muestra rangos de precio — pre-califica al prospecto y sube CTR de leads reales | Alta |
| **Image Asset** | Anuncios con imagen ocupan más espacio visual en mobile | Alta |
| **Call Asset** | Teléfono directo — en B2B muchos prospectos prefieren llamar antes de llenar un formulario | Alta |
| **Lead Form Asset** | El prospecto deja datos sin salir de Google — reduce fricción al máximo | Media |
| **Promotion Asset** | "Demo gratis disponible" — genera urgencia y diferencia del competidor | Media |

---

## La Cuota de Impresiones — El Argumento Definitivo

### Lo que dicen los números

En los últimos 30 días, de todas las búsquedas disponibles en el mercado peruano de ERP para distribuidoras:

```
Cuota ganada por Uniflex:          19.8%   ← Solo 1 de cada 5 búsquedas ve el anuncio
Perdida por PRESUPUESTO agotado:   39.3%   ← 4 de cada 10: el dinero diario ya se acabó
Perdida por AD RANK insuficiente:  40.9%   ← 4 de cada 10: la puja o calidad no alcanzó
─────────────────────────────────────────
Mercado que NUNCA ve a Uniflex:    80.2%
```

### La interpretación para el negocio

Por cada 10 empresas peruanas que buscan hoy un ERP para distribuidoras, **Uniflex aparece ante 2**. Las otras 8 ven a la competencia.

De esas 8 empresas que no ven a Uniflex:
- **4 se pierden puramente porque el presupuesto se agotó ese día** — hay demanda, hay usuarios buscando, simplemente el dinero ya no alcanzó para más impresiones
- **4 se pierden porque el Ad Rank no fue suficiente** para ganar esa subasta específica — se resuelve mejorando Quality Score y pujas

### Las dos palancas

| Palanca | Qué resuelve | Inversión | Velocidad |
|---|---|---|---|
| Aumentar presupuesto | 39.3% perdido por billetera | $+X/día | **Inmediata** |
| Mejorar landing pages y QS | Parte del 40.9% perdido por rango | Desarrollo web | 2–4 semanas |
| Subir pujas en grupos de alto CTR | Mejora posición Top 3 | Redistribución de presupuesto | Inmediata |

La estrategia óptima es actuar en las dos en paralelo: **más presupuesto captura el mercado ahora**, y **mejor Quality Score hace que cada sol invertido rinda más Ad Rank** — reduciendo el CPC real entre 20–40%.

---

## Resumen Ejecutivo

### Lo que ya hemos logrado

1. **Presupuesto operativo:** De $8 (sin impresiones) a $15 diarios — la campaña ahora es visible y genera 1,485 impresiones y 125 clics mensuales
2. **Estructura segmentada:** De 1 grupo genérico a 6 grupos específicos por vertical (Ferreterías, Distribución, Farmacéuticas, Consumo Masivo, Brand, Competidores)
3. **Tracking limpio:** Eliminamos el conflicto de plantillas de seguimiento — ahora GA4 recibe atribución precisa con UTMs manuales por cada campaña
4. **Exclusiones estratégicas:** SAP, Odoo, Defontana excluidos — no gastamos en subastas imposibles de ganar
5. **Assets robustos:** 15+ sitelinks, 18+ callouts, 6 structured snippets activos que amplían la visibilidad del anuncio
6. **Competencia local identificada:** Confirmamos que Uniflex compite contra ERPs peruanos de escala comparable, no contra gigantes enterprise

### Lo que sigue para subir de posición

| Prioridad | Acción | Factor que mejora |
|---|---|---|
| 1 | Aumentar presupuesto diario | IS perdida por presupuesto (39.3%) |
| 2 | Landing page específica para Ferreterías | QS / Landing Page Experience |
| 3 | Landing page para búsquedas de competidores (Paqari, Nextbyn) | QS / Landing Page Experience |
| 4 | Incorporar competidores locales al grupo Competidores (Saurie, KeyFacil, Nisira) | Cobertura de subasta |
| 5 | Agregar Price Asset, Call Asset e Image Asset | Ad Rank sin costo adicional |
| 6 | Ajustes de puja por dispositivo y programación horaria | Señales de contexto |
| 7 | Activar Smart Bidding (Target CPA) cuando haya conversiones | Optimización automática de puja |

### El número clave

> Con el presupuesto actual, Uniflex captura el **19.8% del mercado disponible**. Atacando presupuesto + landing pages en paralelo, el escenario conservador proyecta llegar al **35–45% de cuota de impresiones** — más del doble de visibilidad para el mismo segmento de compradores.
