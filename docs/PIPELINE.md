# Pipeline — Flujo detallado paso a paso

## Diagrama de estados

```
                      RESEARCH
                   ┌────────────┐
    Fuentes ──────►│  Scoring   │
    (arXiv,        │  & Filter  │
     RSS, HN,      │  LLM 0-10  │
     crawler)      └─────┬──────┘
                         │ score ≥ 7
                         ▼
                   ┌────────────┐
                   │  Extract   │
                   │  facts &   │
                   │  angles    │
                   └─────┬──────┘
                         │
                         ▼
                      QUEUE
                   ┌────────────┐
                   │  Supabase  │
                   │  status:   │◄── Manual input también posible
                   │  "pending" │
                   └─────┬──────┘
                         │ n8n scheduler picks next
                         ▼
                      DESIGN
                   ┌────────────┐
                   │  Claude    │
                   │  generates │
                   │  HTML      │
                   └─────┬──────┘
                         │
                         ▼
                   ┌────────────┐
                   │ Puppeteer  │
                   │  → PNG     │
                   └─────┬──────┘
                         │
                         ▼
                   ┌────────────┐
                   │  Vision    │◄── fail: regenerar (max 3x)
                   │  self-     │
                   │  review    │
                   └─────┬──────┘
                         │ pass
                         ▼
                   ┌────────────┐
                   │ Cloudinary │
                   │  upload    │
                   └─────┬──────┘
                         │
                         ▼
                      REVIEW
                   ┌────────────┐
                   │  Telegram  │
                   │  bot       │
                   │  notifica  │
                   └─────┬──────┘
                         │
           ┌─────────────┼──────────────┐
           │             │              │
           ▼             ▼              ▼
       Aprobar       Regenerar      Rechazar
           │             │              │
           │        Vuelve a        status =
           │        Design          rejected
           ▼
    status = approved
           │
           ▼ (scheduled_for llegó)
                      PUBLISH
                   ┌────────────┐
                   │ Meta Graph │
                   │    API     │
                   │  Instagram │
                   └─────┬──────┘
                         │
                         ▼
                   status = posted
                   analytics tracking
```

---

## Workflows n8n

### Workflow 1: Research Crawler
**Trigger:** Schedule — cada 2 horas

```
[Schedule] 
  → [HTTP: arXiv API] → [Code: parse papers] → [AI: score relevance]
  → [HTTP: Semantic Scholar] → [Code: merge & deduplicate]
  → [HTTP: HN API top stories] → [Code: filter tech/science]
  → [HTTP: news-crawler webhook/Supabase] → [Code: pull new articles]
  → [AI: extract facts + story angles + visual metaphor]
  → [Supabase: insert into infographic_queue WHERE score ≥ 7]
```

### Workflow 2: Design Pipeline
**Trigger:** Schedule — cada 30 minutos, SI hay items `pending` en cola

```
[Schedule]
  → [Supabase: SELECT next pending item by priority]
  → [IF queue empty] → [Stop]
  → [Code: build design prompt (brief + facts + angle + canvas + style)]
  → [AI: Claude Sonnet → generate HTML infographic]
  → [HTTP: Puppeteer service → render PNG]
  → [AI: Claude Vision → self-review checklist]
  → [IF fail AND attempts < 3] → [AI: regenerate with feedback] → loop
  → [IF fail AND attempts = 3] → [Supabase: mark as design_failed]
  → [Cloudinary: upload PNG]
  → [AI: generate Instagram caption + hashtags]
  → [Supabase: update status = review_pending]
  → [Telegram: send notification to reviewer]
```

### Workflow 3: Telegram Review Bot
**Trigger:** Webhook (Telegram webhook endpoint)

```
[Telegram Webhook]
  → [Switch: callback_data]
    ├── "approve" → [Supabase: status = approved] → [Notify: aprobado ✅]
    ├── "schedule" → [Show: time picker] → [Supabase: scheduled_for = selected_time]
    ├── "edit_caption" → [Set: waiting for text] → [On next message: update caption]
    ├── "regenerate" → [Supabase: status = pending, attempts++] → trigger Design workflow
    └── "reject" → [Supabase: status = rejected] → [Notify: rechazado ❌]
```

### Workflow 4: Publisher
**Trigger:** Schedule — cada 15 minutos

```
[Schedule]
  → [Supabase: SELECT item WHERE status=approved AND scheduled_for <= now()]
  → [IF none] → [Stop]
  → [Cloudinary: verify image URL accessible]
  → [HTTP: POST /me/media (Meta Graph API)]
  → [Wait: 10s]
  → [HTTP: GET media status (polling)]
  → [HTTP: POST /me/media_publish]
  → [Supabase: status = posted, instagram_post_id = ...]
  → [Analytics: log post metrics]
```

### Workflow 5: Queue Health Monitor
**Trigger:** Schedule — cada hora

```
[Schedule]
  → [Supabase: COUNT items WHERE status=approved]
  → [IF count < 3] → [Telegram: ⚠️ ALERTA: cola baja, quedan {count} posts aprobados]
  → [Supabase: COUNT items WHERE status=pending]
  → [IF count < 5] → [Trigger Research Crawler immediately]
  → [Log: queue health metrics]
```

---

## Gestión de errores

| Error | Respuesta del sistema |
|---|---|
| LLM genera HTML inválido | Retry con prompt simplificado, max 3x |
| Puppeteer falla el render | Retry con Chrome diferente flag, alert si persiste |
| Vision review falla 3x | Marca como `needs_human_design`, notifica Telegram |
| Cloudinary upload falla | Retry exponencial, 3 intentos |
| Meta API rechaza imagen | Verificar ratio, tamaño, formato → fix automático |
| Meta API rate limit | Esperar cooldown, reencolar para siguiente ventana |
| Telegram bot offline | Email fallback para notificaciones críticas |

---

## Métricas a trackear

```sql
-- En Supabase: tabla infographic_analytics
CREATE TABLE infographic_analytics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  queue_item_id UUID REFERENCES infographic_queue(id),
  instagram_post_id TEXT,
  
  -- Engagement (fetch desde Meta API cada 24h)
  likes INTEGER,
  comments INTEGER,
  saves INTEGER,
  shares INTEGER,
  reach INTEGER,
  impressions INTEGER,
  
  -- Pipeline metrics
  design_attempts INTEGER,         -- cuántas regeneraciones
  time_to_approve INTERVAL,        -- cuánto tardó la revisión humana
  design_language TEXT,
  canvas_format TEXT,
  
  -- Feedback loop
  engagement_rate FLOAT,           -- (likes+comments+saves)/reach
  fetched_at TIMESTAMPTZ DEFAULT now()
);
```

### Dashboard mínimo viable
- Posts por día (meta: 4-5)
- Engagement rate por design language
- Tasa de rechazo/regeneración
- Tiempo promedio pipeline completo (research → posted)
- Temas más populares (para ajustar scoring)
