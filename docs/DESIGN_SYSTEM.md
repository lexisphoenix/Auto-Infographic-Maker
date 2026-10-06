# Sistema de Diseño — infographycs

## Filosofía de diseño

Inspirado en [EpicInfographics](https://github.com/OrRon/EpicInfographics):

> El canvas es un **lugar**, no una página. Cada pieza construye una escena y los datos viven *dentro* de esa escena. El minimalismo gráfico plano cuenta como un fallo, incluso cuando está ordenado.

**Las tres reglas de oro:**
1. El objeto dibujado *porta* el dato (una copa llena a 2/3 porque 2 de cada 3 adultos beben café)
2. Los charts se calculan, no se adivinan (ratios de barras, arcos de donut son aritmética)
3. El agente revisa su propio render antes de entregarlo (loop check-render-review)

---

## Design Languages para @infographycs

### 1. `dark-glass` — El principal (60% de posts)
**Cuándo:** Tecnología, IA, datos numéricos, startups, hitos computacionales

Características:
- Fondo casi negro (#0A0A0F), elementos con glassmorphism sutil
- Tipografía: Inter o Space Grotesk, jerarquía muy marcada
- Acentos en cian (#00D4FF), verde neón (#39FF14), o violeta (#A855F7)
- Datos representados con elementos geométricos precisos
- Sensación: "esto es el futuro"

**Ejemplo:** "GPT-5 consume la electricidad de 10,000 hogares al día"

---

### 2. `blueprint` — Técnico (15% de posts)
**Cuándo:** "Cómo funciona X", arquitecturas, esquemas, física, ingeniería

Características:
- Fondo azul oscuro (#0D1B2A), líneas blancas finas
- Grid técnico visible en el fondo
- Tipografía monoespaciada para datos, serif para títulos
- Dimensiones, cotas y anotaciones técnicas
- Sensación: "plano de arquitectura, diagrama de ingeniería"

**Ejemplo:** "Anatomía de un procesador cuántico de 1000 qubits"

---

### 3. `naturalist-plate` — Ciencia (10% de posts)
**Cuándo:** Biología, biotech, química, anatomía molecular, naturaleza

Características:
- Fondo crema/pergamino (#F4EDD3), ilustración al estilo atlas científico
- Tipografía: serif clásica para títulos, sans-serif para datos
- Líneas de detalle finas, anotaciones con flechas dibujadas
- Paleta natural: verdes, azules, ocres
- Sensación: "lámina de atlas de historia natural del s.XIX pero con datos actuales"

**Ejemplo:** "CRISPR-Cas9: cómo edita el ADN"

---

### 4. `editorial` — Divulgativo (8% de posts)
**Cuándo:** Historia de X, contexto social, análisis de impacto

Características:
- Layout tipo revista científica/The Economist
- Tipografía mixta (serif titular + sans-serif cuerpo)
- Uso de espacio en blanco, columnas
- Sensación: "artículo de divulgación bien diseñado"

---

### 5. Otros estilos (uso ocasional)
- `isometric-world`: ecosistemas, redes, infraestructura digital
- `park-poster`: logros históricos, hitos espaciales
- `cutaway`: dentro de X (chip, reactor, célula)
- `retro-print`: evolución histórica, décadas

---

## Reglas de narrativa visual

### El test de 5 segundos
Al cubrir todo el texto, ¿sigue siendo reconocible el tema? Si no, el diseño visual es genérico.

### Jerarquía de información
```
[Hero Fact] → El dato más impactante, en grande, imposible de no ver
[Contexto]  → 3-5 datos de soporte que explican el hero
[Fuente]    → Crédito al paper/organización, pequeño pero presente
[Branding]  → @infographycs, discreto pero consistente
```

### Representaciones de datos (variadas, no solo barras)

| Tipo | Cuándo usarlo |
|---|---|
| Número hero gigante | Un solo dato es la historia |
| Barra comparativa | A vs B o ranking de 3-6 items |
| Donut/Pie | Partes de un todo (max 4 segmentos) |
| Timeline horizontal | Evolución temporal, hitos |
| Pictograma/Icon army | "1 de cada X..." |
| Treemap/Mapa de calor | Muchos valores relativos |
| Objeto-como-barra | Líquido en copa, altura de edificio |
| Flow/Diagrama | Proceso de pasos |

**Regla:** nunca más de 2 charts del mismo tipo en una infografía.

---

## Animaciones (20% de posts)

Para contenido destinado a Stories o Reels:

### Tipos de animación
- **Reveal progresivo:** los elementos aparecen en orden narrativo (300-500ms cada uno)
- **Counter animation:** números que "cuentan" hasta el valor final
- **Flow animation:** flechas o partículas que fluyen mostrando el proceso
- **Zoom dramático:** la cámara hace zoom al hero fact

### Técnica
- CSS animations puras en el HTML (no JavaScript para las animations principales)
- Duración total: 15-30 segundos (perfecto para Stories/Reels)
- Render: Playwright graba la pestaña → ffmpeg codifica MP4 a 30fps
- Formatos de entrega: MP4 (Instagram Reels), GIF (previews)

---

## Branding @infographycs

### Paleta base (varía según design language)
- Siempre hay coherencia: fondo oscuro para `dark-glass`, claro para `naturalist-plate`

### Logo/Marca
- `@infographycs` aparece en esquina inferior derecha
- Fuente: la misma que el estilo de la infografía
- Tamaño: pequeño pero legible

### Hashtags estratégicos (incluir en caption)
```
Siempre: #infographycs #infographic #datavisualization
Por tema:
  IA: #artificialintelligence #machinelearning #deeplearning #AI
  Biotech: #biotech #CRISPR #genomics #synthetic biology  
  Física: #physics #quantum #astrophysics
  Computing: #programming #tech #computing #hardware
```

---

## Quality checklist (pre-publicación)

Antes de enviar a revisión humana, el sistema valida automáticamente:

- [ ] **No-text squint test**: cubrir texto → tema reconocible
- [ ] **Template test**: ¿parece un template genérico de Canva? → rechazar
- [ ] **Flat-ground test**: ¿todo en el mismo plano sin profundidad? → rechazar
- [ ] **Legibilidad**: texto mínimo 24px en formato story, 18px en square
- [ ] **Contraste**: ratio ≥ 4.5:1 para texto principal
- [ ] **Datos correctos**: LLM verifica que las cifras en el HTML coinciden con los hechos extraídos
- [ ] **Branding presente**: @infographycs visible
- [ ] **Fuente citada**: paper/organización mencionada
- [ ] **Caption lista**: longitud, CTA, hashtags
