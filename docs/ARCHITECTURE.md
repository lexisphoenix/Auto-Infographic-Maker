# Arquitectura del Sistema — Auto-Infographic-Maker

## Visión General

El sistema es un pipeline de 5 capas que transforma fuentes de información científica y tecnológica en infografías publicadas automáticamente en Instagram. Está diseñado para funcionar con mínima intervención humana excepto en la capa de revisión, que actúa como control de calidad editorial.

```
                    ┌─────────────────────────────────────────┐
                    │              n8n Orchestrator            │
                    │         (scheduler + state machine)      │
                    └────────────────┬────────────────────────┘
                                     │
          ┌──────────────────────────▼──────────────────────────────┐
          │                                                          │
    ┌─────▼──────┐  ┌────────────┐  ┌──────────┐  ┌──────────────┐ │
    │  CAPA 1    │  │  CAPA 2   │  │  CAPA 3  │  │   CAPA 4     │ │
    │ Research   │→ │   Queue   │→ │  Design  │→ │   Review     │ │
    │            │  │  Manager  │  │ (render) │  │ (human gate) │ │
    └────────────┘  └────────────┘  └──────────┘  └──────┬───────┘ │
                                                          │         │
                                                   ┌──────▼───────┐ │
                                                   │   CAPA 5     │ │
                                                   │  Publisher   │ │
                                                   │  (Instagram) │ │
                                                   └──────────────┘ │
          │                                                          │
          └──────────────────────────────────────────────────────────┘
```

---

## Capa 1: Research

**Objetivo:** Descubrir, filtrar y preparar temas relevantes de manera continua.

### Fuentes de datos

| Fuente | Tipo | Frecuencia | Prioridad |
|---|---|---|---|
| arXiv (cs.AI, cs.LG, q-bio, physics) | Papers académicos | Diaria | Alta |
| Semantic Scholar API | Trending papers + citas | Diaria | Alta |
| RSS: Nature, Science, MIT Tech Review | Noticias científicas | 4h | Media |
| Hacker News API (top stories) | Tech buzz | 2h | Media |
| News Crawler (proyecto hermano) | Noticias curadas | Pull on demand | Media |
| Twitter/X API (listas de científicos) | Breaking news | 1h | Baja |

### Procesamiento

```
Paper/Noticia raw
    │
    ▼
[Filtro relevancia] ← LLM scoring (0-10 por: novedad, impacto, visualizabilidad)
    │ score ≥ 7
    ▼
[Extracción de datos] ← Claude: extrae hechos, cifras, timeline, comparativas
    │
    ▼
[Enrichment] ← búsqueda de contexto adicional, datos históricos
    │
    ▼
[Story angles] ← LLM genera 2-3 ángulos narrativos candidatos
    │
    ▼
[Push to Queue] → Supabase
```

### Scoring de visualizabilidad

Un tema es "visualizable" si contiene al menos dos de:
- Cifras concretas (porcentajes, magnitudes, fechas)
- Comparativas (A vs B, entonces vs ahora)
- Proceso o secuencia de pasos
- Jerarquía o ranking
- Cambio temporal (tendencia)

---

## Capa 2: Queue Manager

**Objetivo:** Mantener una cola priorizada de temas listos para diseñar.

### Esquema de datos (Supabase)

```sql
-- Tabla principal de la cola
CREATE TABLE infographic_queue (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Contenido
  topic TEXT NOT NULL,
  source_url TEXT,
  source_type TEXT, -- arxiv | news | hacker_news | manual
  
  -- Narrativa generada
  headline TEXT,
  story_angle TEXT,           -- ángulo narrativo elegido
  key_facts JSONB,            -- array de hechos/cifras clave
  visual_metaphor TEXT,       -- metáfora visual sugerida
  
  -- Diseño
  canvas_format TEXT,         -- square | story | wide | a4
  design_language TEXT,       -- dark-glass | blueprint | naturalist-plate...
  should_animate BOOLEAN DEFAULT false,  -- ~20% true
  
  -- Estado del pipeline
  status TEXT DEFAULT 'pending',
  -- pending → designing → review_pending → approved → posting → posted | rejected
  
  -- Metadatos
  priority_score FLOAT DEFAULT 5.0,
  created_at TIMESTAMPTZ DEFAULT now(),
  scheduled_for TIMESTAMPTZ,  -- hora programada de publicación
  posted_at TIMESTAMPTZ,
  
  -- Output
  html_path TEXT,
  image_url TEXT,             -- Cloudinary URL
  video_url TEXT,             -- Cloudinary URL (si animado)
  caption TEXT,
  hashtags TEXT[],
  instagram_post_id TEXT
);

-- Tabla de historial de temas (deduplicación)
CREATE TABLE topic_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_fingerprint TEXT UNIQUE,  -- hash semántico del tema
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### Lógica de priorización

```
priority_score = (
  novelty_score * 0.35        -- qué tan nuevo/trending
  + viz_score * 0.30          -- qué tan visualizable
  + engagement_proxy * 0.20   -- temas similares que funcionaron antes
  + diversity_bonus * 0.15    -- penaliza si ya hay 2+ temas del mismo campo esta semana
)
```

### Scheduling de publicaciones

- **Frecuencia:** 3-5 posts por día
- **Ventanas óptimas:** 08:00, 13:00, 18:00, 21:00 (hora local)
- **Cooldown:** mínimo 2.5h entre posts
- **Cola mínima:** mantener siempre ≥ 10 items aprobados listos para publicar

---

## Capa 3: Design (Render Engine)

**Objetivo:** Convertir el brief de un item de la cola en un PNG (o MP4) de calidad profesional.

### Motor de diseño: Hybrid approach (Fal.ai + Claude + Puppeteer)

El sistema usa un enfoque híbrido que combina lo mejor de cada herramienta:

1. **Fal.ai genera ilustraciones hero** — Usando modelos como `fal-ai/flux-2` o `fal-ai/flux-2-pro`, genera las imágenes visualmente impactantes que anclan la infografía (backgrounds, objetos hero, escenas)
2. **Claude genera el HTML layout** — Con las ilustraciones de Fal.ai embebidas, Claude produce un HTML autocontenido con datos precisos, tipografía perfecta y composición profesional
3. **Puppeteer renderiza a PNG** — Captura el viewport exacto del HTML compuesto
4. **Claude Vision self-review** — El agente hace screenshot, lo "lee" con vision, y corrige si hay problemas
5. **Animación (20%)** — CSS animations + Playwright → ffmpeg → MP4

### Fal.ai como motor visual

Se reutiliza la misma API key y patrón de CinemaStudio (CINENODE):

```python
# Patrón de llamada a Fal.ai
response = await httpx.post(
    f"https://fal.run/fal-ai/flux-2",
    headers={"Authorization": f"Key {FAL_API_KEY}"},
    json={
        "prompt": "...",
        "image_size": "portrait_16_9",  # o square_hd, landscape_16_9
        "num_images": 1,
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
        "enable_safety_checker": True
    }
)
image_url = response.json()["images"][0]["url"]
```

**Modelos disponibles:**
| Modelo | Uso | Calidad |
|---|---|---|
| `fal-ai/flux-2` | Default, buen balance velocidad/calidad | ⭐⭐⭐⭐ |
| `fal-ai/flux-2-pro` | Cuando se necesita máxima calidad | ⭐⭐⭐⭐⭐ |
| `fal-ai/flux-pro` | Fallback rápido | ⭐⭐⭐ |

### Design Languages disponibles

| Estilo | Uso en @infographycs | Cuándo |
|---|---|---|
| `dark-glass` | Principal | Tech, IA, startups, datos numéricos |
| `blueprint` | Técnico | Cómo funciona X, arquitecturas, física |
| `naturalist-plate` | Ciencia | Biología, biotech, química, anatomía |
| `editorial` | Divulgativo | Historia de X, contexto social |
| `isometric-world` | Sistemas | Ecosistemas, redes, infraestructura |
| `park-poster` | Inspiracional | Hitos, logros, "visita Marte" |
| `cutaway` | Explicativo | Dentro de X: chip, cohete, célula |
| `retro-print` | Nostálgico | Evolución histórica, décadas |

### Formatos de canvas

| Formato | Dimensiones | % uso |
|---|---|---|
| `story` | 1080×1920 | 60% — Instagram Stories/Reels |
| `square` | 1080×1080 | 30% — Feed principal |
| `wide` | 1920×1080 | 10% — Carruseles o YouTube |

### Proceso de generación

```
Queue item (brief)
    │
    ▼
[1. Build prompt] 
    Contexto: topic, facts, angle, canvas, design language, visual metaphor
    │
    ▼
[2. LLM generates HTML]
    Claude Sonnet con EpicInfographics skill prompt
    Output: HTML autocontenido (CSS inline, SVG inline, fuentes via @import)
    │
    ▼
[3. Render to PNG]
    Puppeteer: set viewport → screenshot → save to /tmp/
    │
    ▼
[4. Vision self-review]
    Claude vision analiza el PNG:
    - ¿Se lee el texto? (anti-slop: no-text squint test)
    - ¿El diseño es coherente con el style?
    - ¿Los datos son correctos?
    - ¿Hay errores tipográficos?
    Pass → continúa | Fail → re-genera con feedback (max 3 intentos)
    │
    ▼
[5. Si should_animate]
    CSS animations → Playwright recording → ffmpeg encode → MP4 30s max
    │
    ▼
[6. Upload to Cloudinary]
    Returns public URL → update queue record
    │
    ▼
[7. Generate caption + hashtags]
    LLM: caption ≤ 2200 chars, CTA, hashtags relevantes (20-30)
    │
    ▼
Status → review_pending
```

---

## Capa 4: Revisión Humana

**Objetivo:** Control de calidad editorial con fricción mínima.

### Interfaz de revisión: Telegram Bot

El bot envía al reviewero (tú):

```
📊 Nueva infografía lista para revisión

Tema: "DeepMind's AlphaFold 3 puede predecir moléculas pequeñas"
Estilo: naturalist-plate • Formato: story
Animada: No

[imagen adjunta]

Caption:
"La proteína ya no tiene secretos. AlphaFold 3..."

━━━━━━━━━━━━━━━━━━━━━━━━━
✅ Aprobar y publicar ahora
📅 Aprobar y programar
✏️ Editar caption
🎨 Regenerar diseño
❌ Rechazar
```

### Flujo de decisión

```
Notificación Telegram
    │
    ├── ✅ Aprobar → status = approved → n8n publica según schedule
    │
    ├── 📅 Programar → picker de hora → status = approved (con scheduled_for)
    │
    ├── ✏️ Editar caption → responder con nuevo texto → actualizar BD → aprobado
    │
    ├── 🎨 Regenerar → feedback opcional → vuelve a Capa 3 con nuevo intento
    │
    └── ❌ Rechazar → status = rejected → feedback para mejorar scoring
```

### SLA de revisión

- **Timeout:** si no hay respuesta en 4h → auto-aprobación (configurable)
- **Queue mínima:** si la cola aprobada cae por debajo de 3 items → alerta urgente

---

## Capa 5: Publisher

**Objetivo:** Publicar en Instagram usando la API oficial de Meta.

### API de Meta (Facebook Graph API)

> ⚠️ **IMPORTANTE:** Nunca usar librerías no oficiales (`instabot`, `aiograpi`). Solo Meta Graph API oficial para cuentas de negocio.

### Flujo de publicación

```
Item aprobado (scheduled_for llegó)
    │
    ▼
[1. Verificar image URL] ← Cloudinary URL pública accesible
    │
    ▼
[2. Crear media container]
    POST /me/media
    {
      image_url: "https://res.cloudinary.com/...",
      caption: "...",
      media_type: "IMAGE"  // o VIDEO para Reels
    }
    → creation_id
    │
    ▼
[3. Esperar procesamiento] ← polling status cada 5s, max 60s
    │
    ▼
[4. Publicar]
    POST /me/media_publish
    { creation_id: "..." }
    → post_id
    │
    ▼
[5. Actualizar registro]
    status = posted
    posted_at = now()
    instagram_post_id = post_id
    │
    ▼
[6. Analytics tracking] ← guardar para feedback loop
```

### Rate limits y scheduling

- **Límite Meta:** 50 publicaciones por 24h (más que suficiente)
- **Rate limit interno:** máximo 5 posts/día, mínimo 2h entre posts
- **Ventanas de publicación:** configurables por timezone

---

## Infraestructura

### Stack local / self-hosted

```yaml
# docker-compose.yml
services:
  n8n:
    image: n8nio/n8n
    ports: ["5678:5678"]
    
  puppeteer-render:
    build: ./services/designer
    # Node.js + Puppeteer headless
    
  postgres:
    image: postgres:15
    # n8n database
```

### Servicios cloud

| Servicio | Plan | Costo estimado |
|---|---|---|
| Supabase | Free/Pro | \$0-25/mes |
| Cloudinary | Free | \$0 (25GB suficiente) |
| Claude API | Pay-per-use | ~\$5-15/mes |
| OpenAI API | Pay-per-use | ~\$2-8/mes (backup) |
| Servidor VPS (n8n) | 2GB RAM | ~\$6/mes |

**Total estimado: \$13-54/mes** para 4-5 posts/día

---

## Variables de entorno

```env
# LLMs
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_KEY=

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Meta / Instagram
META_ACCESS_TOKEN=         # Long-lived token
META_INSTAGRAM_USER_ID=    # Business account ID
META_APP_ID=
META_APP_SECRET=

# Telegram (revisión humana)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Fuentes de datos
SEMANTIC_SCHOLAR_API_KEY=  # Free tier disponible

# Configuración
POSTS_PER_DAY=4
MIN_QUEUE_SIZE=10
REVIEW_TIMEOUT_HOURS=4
AUTO_APPROVE_AFTER_TIMEOUT=false
```
