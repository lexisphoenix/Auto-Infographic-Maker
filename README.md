# 🎨 Auto-Infographic-Maker
### Sistema automático de creación de infografías para `@infographycs`

> **Misión:** Convertir papers, noticias y avances de tecnología, IA, computación, biotecnología y física en infografías visuales de calidad de estudio — sin tocar el resultado manualmente.

---

## ¿Qué hace este sistema?

Un pipeline de 5 capas completamente automatizado que va de "noticia/paper" a "publicado en Instagram":

```
[Research] → [Cola/Queue] → [Diseño] → [Revisión Humana] → [Publicación]
```

- **~4–5 infografías/día** en imagen fija (formato story 1080×1920 o square 1080×1080)
- **~1 de cada 5** se animan como video corto (Reels / TikTok)
- Temas: IA, computing, biotech, física, matemáticas aplicadas
- Calidad visual de estudio: inspirado en [EpicInfographics](https://github.com/OrRon/EpicInfographics), no en templates genéricos

---

## Arquitectura del sistema

Ver [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) para el diseño completo.

### Stack tecnológico

| Capa | Herramienta | Rol |
|---|---|---|
| **Orquestación** | n8n (self-hosted) | Motor de workflows visuales |
| **Research** | arXiv API + RSS + Perplexity | Fuentes de contenido |
| **Queue** | Supabase (PostgreSQL) | Cola de temas priorizada |
| **LLM** | Claude Sonnet / GPT-4o | Análisis, narrativa, HTML |
| **Diseño** | HTML+CSS+SVG → Puppeteer | Render de infografías |
| **Animación** | Playwright + ffmpeg | Render de MP4/GIF (~20%) |
| **Revisión** | Telegram Bot + webhook | Human-in-the-loop |
| **Storage** | Cloudinary | Hosting de imágenes públicas |
| **Publicación** | Meta Graph API | Instagram oficial |

---

## Estructura del proyecto

```
Auto-Infographic-Maker/
├── README.md                    # Este archivo
├── docs/
│   ├── ARCHITECTURE.md          # Diseño detallado del sistema
│   ├── PIPELINE.md              # Flujo paso a paso
│   ├── DESIGN_SYSTEM.md         # Sistema de diseño de infografías
│   └── INTEGRATION.md           # Relación con otros proyectos
├── services/
│   ├── researcher/              # Capa 1: Research y descubrimiento
│   ├── queue-manager/           # Capa 2: Gestión de cola
│   ├── designer/                # Capa 3: Generación de infografías
│   ├── reviewer/                # Capa 4: Revisión humana
│   └── publisher/               # Capa 5: Publicación
├── skills/
│   └── epic-infographics/       # Skill de diseño (fork de EpicInfographics)
├── templates/                   # Templates HTML base
├── n8n/
│   └── workflows/               # Exports JSON de workflows n8n
├── scripts/
│   ├── render.js                # Puppeteer: HTML → PNG
│   ├── animate.js               # Playwright + ffmpeg: HTML → MP4
│   └── post.py                  # Meta Graph API publisher
└── docker-compose.yml           # Stack local completo
```

---

## Quick Start

```bash
# 1. Clonar y configurar entorno
cp .env.example .env
# Rellenar claves: OPENAI_KEY, ANTHROPIC_KEY, CLOUDINARY_*, META_ACCESS_TOKEN, etc.

# 2. Arrancar stack
docker-compose up -d

# 3. Acceder a n8n
open http://localhost:5678

# 4. Importar workflows
# n8n > Settings > Import workflow > seleccionar archivos en n8n/workflows/
```

---

## Relación con otros proyectos

| Proyecto | Relación |
|---|---|
| `news-crawler` | **Integrado como fuente** — sus feeds alimentan la capa Research |
| `Auto-video-documentary` | **Proyecto hermano independiente** — comparten infra (Supabase, Cloudinary) pero pipelines separados |

Ver [`docs/INTEGRATION.md`](docs/INTEGRATION.md) para el razonamiento completo.

---

## Roadmap

- [ ] v0.1 — Pipeline básico: arXiv → Claude → HTML → PNG → Telegram → Instagram
- [ ] v0.2 — Sistema de diseño completo (8 design languages)
- [ ] v0.3 — Animaciones (~20% de posts)
- [ ] v0.4 — Multi-plataforma (TikTok, LinkedIn)
- [ ] v0.5 — Analytics y feedback loop automático

---

*Cuenta de Instagram objetivo: [@infographycs](https://instagram.com/infographycs)*
