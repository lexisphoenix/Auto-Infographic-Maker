# Auto-Infographic-Maker — Decisiones de arquitectura

## ADR-001: n8n como orquestador principal

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Contexto
Necesitamos un orquestador para el pipeline de 5 capas. Opciones evaluadas:
- n8n (self-hosted, visual, low-code)
- Prefect / Airflow (Python, más potente, más complejo)
- GitHub Actions (simple, pero no ideal para workflows event-driven continuos)
- Make.com / Zapier (SaaS, limitado, caro en volumen)

### Decisión
**n8n self-hosted** en VPS.

### Razonamiento
- Visual y fácil de debuggear (ver el estado de cada step en el UI)
- Tiene nodos nativos para: Supabase, Telegram, HTTP, Cloudinary, OpenAI
- Permite Code nodes (JS/Python) para lógica custom
- Webhooks y schedulers incluidos
- Self-hosted = sin límite de workflows ni runs
- La complejidad de Prefect/Airflow no se justifica para este volumen

### Consecuencias
- Necesita VPS mínimo 2GB RAM (~6€/mes)
- Los workflows se exportan como JSON (versionables en Git)
- Debugging más visual pero menos poderoso que código puro

---

## ADR-002: HTML+CSS+SVG → Puppeteer para render

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Contexto
Opciones para generar las imágenes de infografías:
- A) DALL-E 3 / Flux: texto → imagen directamente
- B) Python (matplotlib, plotly, PIL): programático
- C) HTML+CSS+SVG → Puppeteer: el LLM genera HTML, Puppeteer lo renderiza
- D) Figma/Canva API: templates

### Decisión
**Opción C: HTML+CSS+SVG → Puppeteer**, siguiendo el approach de EpicInfographics.

### Razonamiento
- Los LLMs (especialmente Claude) son extremadamente buenos generando HTML/CSS
- El resultado es pixel-perfect y reproducible
- El texto siempre es legible (no el caso con imagen AI)
- Los datos son exactos (no "eyeballed")
- El LLM puede ver su propio output via screenshot y corregirlo
- Ofrece flexibilidad total de diseño sin depender de templates
- Las animaciones CSS son triviales de añadir al mismo HTML

**Contra:** Requiere un servicio Puppeteer/Playwright en el servidor.

---

## ADR-003: Supabase como base de datos principal

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Decisión
Supabase (PostgreSQL managed) para toda la persistencia del sistema.

### Razonamiento
- Free tier generoso (500MB, suficiente para meses)
- API REST y SDK ya disponibles como n8n node
- Compartible con `news-crawler` y `Auto-video-documentary` via schemas separados
- Realtime subscriptions útiles para el Telegram bot
- Postgres = SQL real, no NoSQL limitado

---

## ADR-004: Revisión humana obligatoria vía Telegram

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Contexto
¿Publicar automáticamente sin revisión o incluir human-in-the-loop?

### Decisión
**Revisión humana obligatoria**, implementada como bot de Telegram con botones de acción.

### Razonamiento
- Riesgo reputacional: un error factual en una infografía científica daña la credibilidad
- La fricción es mínima (2 clics: ver imagen + aprobar)
- Telegram es inmediato y accesible desde móvil
- Se puede configurar auto-aprobación tras timeout (4h) para días sin conexión
- Permite aprendizaje: los rechazos con feedback mejoran el scoring

### Consecuencias
- Latencia adicional de 0-4h en el pipeline
- Requiere que el reviewer tenga Telegram y esté medianamente disponible
- La cola debe tener siempre items aprobados suficientes para no quedarse sin posts

---

## ADR-005: Auto-Infographic-Maker como proyecto independiente

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Contexto
¿Integrar dentro de `Auto-video-documentary` o mantener separado?

### Decisión
**Proyecto independiente**, con infraestructura compartida (Supabase, Cloudinary).

### Razonamiento
Ver [`INTEGRATION.md`](INTEGRATION.md) para análisis completo.

Resumen: los outputs (imagen vs. vídeo largo), ritmos de producción (diario vs. semanal), dependencias técnicas (Puppeteer vs. ffmpeg+TTS) y audiencias objetivo son suficientemente distintos como para que la separación sea la decisión correcta.

---

## ADR-006: Meta Graph API oficial para publicación

**Fecha:** 2026-10-06  
**Estado:** Aceptado

### Decisión
Usar exclusivamente la **Facebook Graph API oficial** para publicar en Instagram Business.

### Razonamiento
- Las librerías no oficiales (`instabot`, `aiograpi`) violan los ToS de Meta
- Una cuenta baneada anula todo el trabajo del proyecto
- La API oficial soporta: imágenes, vídeos, carruseles, stories (Business/Creator accounts)
- n8n tiene nodo HTTP genérico suficiente para llamar la API

### Requisitos
- Cuenta Instagram Business (no Personal)
- Facebook Developer App aprobada
- Long-lived Access Token (renovar cada ~60 días o usar token de sistema)
