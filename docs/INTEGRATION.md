# Integración con proyectos existentes

## Decisión de arquitectura

### TL;DR

| Pregunta | Decisión |
|---|---|
| ¿Integrar `news-crawler`? | ✅ Sí, como fuente de datos en Capa 1 |
| ¿Integrar con `Auto-video-documentary`? | ❌ No directamente. Proyectos hermanos independientes con infraestructura compartida |
| ¿Mover todo a `Auto-video-documentary`? | ❌ No recomendable |

---

## Análisis: ¿Por qué no un monorepo con `Auto-video-documentary`?

### Similitudes

- Ambos consumen fuentes de noticias/papers científicos
- Ambos usan LLMs para generar contenido
- Ambos publican en redes sociales (Instagram/YouTube)
- Ambos tienen revisión humana como gate

### Diferencias críticas

| Dimensión | Auto-video-documentary | Auto-Infographic-Maker |
|---|---|---|
| **Output** | Vídeo 5-20min (MP4 narrado) | Imagen fija / GIF/Reel corto |
| **Pipeline** | Guión → Narración → B-roll → Edición | Brief → HTML → Render → Review |
| **Tiempo de producción** | Horas | Minutos |
| **Frecuencia** | 1-3 vídeos/semana | 4-5 posts/día |
| **Profundidad** | Profundidad documental | Visual snapshot / síntesis |
| **Audiencia** | YouTube, divulgación larga | Instagram, TikTok, consumo rápido |
| **Complejidad técnica** | ffmpeg, TTS, stock footage | Puppeteer, SVG, CSS animations |

### Riesgo de monorepo

Fusionar ambos crearía un monolito donde un bug en el render de imágenes puede parar la producción de vídeos y viceversa. Los ritmos de publicación son incompatibles (diario vs semanal) y las dependencias técnicas son completamente distintas.

**Conclusión:** Mantenerlos como proyectos independientes es la decisión correcta. Se puede compartir infraestructura (Supabase, Cloudinary) mediante namespacing de tablas/buckets.

---

## Integración con `news-crawler`

### Cómo encaja

`news-crawler` actúa como **proveedor de feeds curados** para la Capa 1 (Research) de Auto-Infographic-Maker.

```
news-crawler                     Auto-Infographic-Maker
     │                                    │
     │  Push/Pull de artículos           │
     │  filtrados y enriquecidos         │
     └──────────────────────────────────►│ Capa 1: Research
                                         │   └── news-crawler es UNA fuente
                                         │       entre varias (arXiv, RSS, HN...)
```

### Modo de integración: Pull via API/webhook

**Opción A (recomendada): Supabase compartida**
- `news-crawler` escribe en tabla `crawled_articles` en Supabase
- Auto-Infographic-Maker la consulta en su ciclo de research
- Namespacing: `infographic_queue`, `topic_history` (infographic) vs `crawled_articles`, `sources` (crawler)

**Opción B: Webhook**
- `news-crawler` hace POST a endpoint de n8n cuando hay artículo relevante
- n8n lo procesa directamente en el pipeline de research

**Opción C: Google Sheets compartida** (más simple, menos robusto)

### Configuración recomendada

```sql
-- En Supabase compartida, tabla proveída por news-crawler
-- Auto-Infographic-Maker la consume como fuente
SELECT * FROM crawled_articles
WHERE 
  processed_by_infographic IS NULL
  AND relevance_score >= 7
  AND topic_tags && ARRAY['ai', 'biotech', 'physics', 'computing']
ORDER BY published_at DESC
LIMIT 20;
```

---

## Infraestructura compartida

### Supabase

```
Proyecto Supabase "content-platform"
├── Schema: infographics/
│   ├── infographic_queue
│   ├── topic_history
│   └── design_sessions
├── Schema: crawler/
│   ├── crawled_articles
│   └── sources
└── Schema: videos/  (Auto-video-documentary)
    ├── video_queue
    └── script_versions
```

### Cloudinary

```
Cloud: infographycs-media
├── /infographics/
│   ├── /png/     ← imágenes fijas
│   └── /video/   ← reels animados
├── /thumbnails/  (Auto-video-documentary)
└── /crawler/     (assets del crawler)
```

---

## Hoja de ruta de integración

### Fase 1 (inmediata): Proyectos independientes, datos compartidos
- Auto-Infographic-Maker tiene su propia Supabase instance (o comparte con namespacing)
- `news-crawler` expone sus artículos vía tabla o webhook

### Fase 2 (futuro): Shared intelligence layer
- Un único "topic scorer" LLM decide si un tema va a infografía, a vídeo, o a ambos
- Los analytics de engagement de Instagram retroalimentan qué temas priorizar en `news-crawler`

### Fase 3 (avanzado): Content OS
- Plataforma unificada de gestión de contenido
- Un tema → N formatos (infografía, vídeo corto, hilo Twitter, newsletter)
- Repositorio compartido de "design assets" (paletas, ilustraciones, datos curados)
