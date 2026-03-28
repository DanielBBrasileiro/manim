# AIOX v4.0 — PLANO MESTRE DE IMPLEMENTAÇÃO
## "The Invisible Architecture"

> **Objetivo:** Elevar em 200%+ a qualidade, escalabilidade e camada premium da produção audiovisual, transformando o pipeline de "catálogo de tech stack" em "cinema de dados narrativo" — no nível da referência "Masterize o Meio do Caminho".

---

## PARTE 1: DIAGNÓSTICO — O QUE ESTÁ ERRADO HOJE

Depois de ler cada arquivo do projeto, identifiquei 7 problemas estruturais que, juntos, explicam por que o output atual parece um infográfico animado e não um motion piece premium.

### 1.1 O Briefing manda mostrar ícones, não contar histórias

Todos os 6 briefings YAML seguem o mesmo padrão: "FadeIn logo A → FadeIn logo B → mover dot de A para B → texto PIPELINE SUCCESS". Isso é uma lista de instruções de animação, não uma narrativa. O briefing `elite_pipeline_test.yaml` exemplifica: cada ato é definido como "Cloud icon + Data nodes merging" — são instruções de motion design sem arco emocional.

**Na referência**, não existe nenhum ícone. Existe uma LINHA que é metáfora da jornada humana. A linha cresce, fica caótica, ultrapassa limites, e resolve. A história é emocional, os dados são a forma.

**Fix:** Reescrever o schema de briefings para ser narrative-first. O briefing deve definir EMOÇÃO por ato, não "qual SVG aparece".

### 1.2 O Manim está sendo usado como slideshow

As cenas (`elite_pipeline_scene.py`, `python_db_elite.py`, `spotify_scenes.py`) seguem o mesmo template: carregar SVGs → DrawBorderThenFill em sequência → MoveAlongPath com dots → FadeOut. Isso é o equivalente a um PowerPoint com animação de entrada.

O Manim é um engine de FÍSICA MATEMÁTICA. Ele deveria estar desenhando curvas que evoluem, campos vetoriais, transformações geométricas, partículas com comportamento emergente — não fazendo FadeIn de logos.

**Fix:** Criar uma biblioteca de "primitivos narrativos" no Manim: curvas vivas, containers dinâmicos, campos de partículas, inversão de cor. Eliminar SVGs de logos das cenas.

### 1.3 O Remotion é usado apenas como label machine

A `Composition.tsx` atual faz basicamente: renderizar o vídeo do Manim como fundo + colocar `GlassLabel` com "V3: DATA LAKE", "V3: RUST ENGINE" etc. em posições fixas. É uma camada de legendas, não uma camada de design.

**Na referência**, a tipografia é sincronizada com narração, aparece em posições que mudam com a narrativa, e usa weight/size como ferramenta expressiva (light 300 para reflexão, medium 500 para afirmação).

**Fix:** O Remotion precisa se tornar um motor de tipografia narrativa com composição dinâmica, não um overlay estático.

### 1.4 A paleta visual é fragmentada

O brand contract define "Cyber Red #FF3366" como primary, mas o resultado é: ícones coloridos (branco, vermelho, gradiente rosa do Python, outline do Postgres) sobre fundo preto, com labels serif bold em caixas translúcidas. Não existe unidade cromática.

**Na referência**, a paleta é: preto + branco + uma inversão total. 2 cores. Sem exceção.

**Fix:** Criar dois modos cromáticos (dark mode / inverted mode) e usar a transição entre eles como recurso dramático.

### 1.5 O formato é errado para o objetivo

Todos os briefings usam 16:9 horizontal (1920x1080). Se o objetivo é Instagram Reels, TikTok, ou YouTube Shorts, o formato precisa ser 9:16 vertical (1080x1920). Mesmo para LinkedIn/Twitter, vídeos verticais ou quadrados performam melhor.

**Fix:** Suportar múltiplos aspect ratios no pipeline, com vertical como default para social.

### 1.6 As personas são descritivas, não executáveis

Aria, Dara e Uma têm descrições ricas, mas o `orchestrator.py` não as usa de verdade. O método `generate_strategy()` retorna um dicionário hardcoded. As personas são decoração, não inteligência.

**Fix:** Conectar as personas ao Claude Code / Antigravity como agents reais com system prompts que governam a decisão criativa.

### 1.7 Os contracts são rígidos demais e não cobrem narrativa

Existem 3 contracts (brand, motion, layout) mas nenhum cobre: narrativa, tipografia dinâmica, estados cromáticos, ou regras de composição de câmera. Os contracts atuais definem "stiffness: 120" mas não definem "quando usar silêncio visual" ou "como construir tensão com espaço negativo".

**Fix:** Expandir para 6 contracts que cobrem todas as camadas da produção.

---

## PARTE 2: A NOVA ARQUITETURA (v4.0)

### 2.1 Estrutura de Diretórios Proposta

```
manim/
├── .agents/
│   ├── personas/
│   │   ├── aria.md          # REESCRITA: Director com system prompt executável
│   │   ├── dara.md          # REESCRITA: Engineer com regras de física
│   │   └── uma.md           # REESCRITA: Designer com regras de percepção
│   ├── briefs/              # Briefings por projeto
│   └── skills/              # Skills instaladas (já feito)
│
├── contracts/               # EXPANDIDO: 6 contracts
│   ├── brand.yaml           # Identidade visual + estados cromáticos
│   ├── motion.yaml          # Física + easing + spring configs
│   ├── layout.yaml          # Grid + safe zones + aspect ratios
│   ├── narrative.yaml       # NOVO: Arcos emocionais + regras de storytelling
│   ├── typography.yaml      # NOVO: Regras de tipo dinâmico + sincronização
│   └── camera.yaml          # NOVO: Enquadramentos + transições + zoom
│
├── core/
│   ├── orchestrator.py      # REESCRITO: Lê narrative contract, gera timeline
│   ├── cache_manager.py     # Mantém
│   └── primitives/          # NOVO: Biblioteca de formas narrativas
│       ├── curves.py        # Curvas vivas, sigmoids, noise
│       ├── containers.py    # Rects que dividem, rotacionam, expandem
│       ├── particles.py     # Campos de partículas, fluxo
│       ├── color_states.py  # Inversão, transições cromáticas
│       └── __init__.py
│
├── engines/
│   ├── manim/
│   │   ├── scenes/          # REORGANIZADO: uma cena por arquivo
│   │   │   ├── genesis.py       # Ato 1 template
│   │   │   ├── turbulence.py    # Ato 2 template
│   │   │   └── resolution.py    # Ato 3 template
│   │   ├── manim_theme.py   # Auto-gerado pelo sync
│   │   └── timing_logger.py
│   │
│   └── remotion/
│       └── src/
│           ├── index.tsx
│           ├── compositions/     # NOVO: uma composition por tipo
│           │   ├── CinematicNarrative.tsx  # Template principal
│           │   └── TechShowcase.tsx        # Para catálogos (caso precise)
│           ├── components/       # NOVO: componentes reutilizáveis
│           │   ├── NarrativeText.tsx    # Tipografia sincronizada
│           │   ├── ColorInversion.tsx   # Transição de inversão
│           │   ├── DiagonalAccent.tsx   # Linhas decorativas
│           │   └── GrainOverlay.tsx     # Texturas sutis
│           ├── theme.ts          # Auto-gerado
│           └── hooks/
│               └── useNarrativeSync.ts  # Sync timing Manim→Remotion
│
├── templates/               # NOVO: Templates de briefing reutilizáveis
│   ├── cinematic_narrative.yaml   # 3-act emotional arc
│   ├── tech_explainer.yaml        # Educational breakdown
│   ├── product_reveal.yaml        # Brand/product launch
│   └── social_hook.yaml           # 15s attention grab
│
├── scripts/
│   ├── sync_brand.py        # EXPANDIDO: compila 6 contracts
│   ├── run_pipeline.py      # REESCRITO: suporta nova estrutura
│   ├── new-video.sh         # ATUALIZADO: usa templates
│   └── sync.sh
│
├── assets/
│   └── brand/
│       ├── tokens.json      # EXPANDIDO: inclui narrative + typography
│       └── ...
│
├── briefings/               # Briefings ativos
└── output/
```

### 2.2 O Novo Schema de Briefing

O briefing atual é "o que animar". O novo é "que história contar".

```yaml
# briefings/exemplo_cinematic.yaml

meta:
  title: "The Invisible Architecture"
  format: vertical_9_16        # vertical_9_16 | wide_16_9 | square_1_1
  duration: 15s
  fps: 60
  template: cinematic_narrative

# A NARRATIVA (não as instruções de animação)
narrative:
  theme: "A beleza invisível de uma arquitetura que escala"
  
  acts:
    - name: genesis
      time: "0s → 4s"
      emotion: curiosidade
      description: >
        Um ponto nasce. Vira uma curva ascendente suave.
        Sensação de potencial e simplicidade.
      visual_primitives:
        - curve: sigmoid_growth
        - container: single_frame_fade
      text: null  # Silêncio intencional
      
    - name: turbulence  
      time: "4s → 10s"
      emotion: tensão
      description: >
        A curva se torna caótica. Containers se dividem.
        A linha ultrapassa bordas. Inversão de cor no clímax.
      visual_primitives:
        - curve: noise_oscillation
        - container: split_multiply_rotate
        - event: color_inversion_at_9s
      text:
        - at: 5s
          content: "quando a complexidade"
          position: top_center
          weight: 300
        - at: 7s
          content: "parece incontrolável"
          position: bottom_center
          weight: 300
        - at: 9s
          content: "é aqui que a maioria desiste."
          position: center
          weight: 500
          color: inverted  # Preto sobre branco
      
    - name: resolution
      time: "10s → 15s"
      emotion: maestria
      description: >
        Cor reverte. Linha se reorganiza, mais alta e estável.
        Container elegante enquadra o resultado.
      visual_primitives:
        - curve: chaotic_to_resolved
        - container: elegant_settle
        - accent: diagonal_line
      text:
        - at: 12s
          content: "arquitetura."
          position: top_center
          weight: 500
          size: 2.5rem
          tracking: 0.15em

# PARAMETROS VISUAIS (overrides dos contracts)
overrides:
  palette_mode: monochrome       # monochrome | brand | custom
  color_inversion: true
  grain_intensity: 0.08
```

### 2.3 A Diferença Fundamental

| Aspecto | v3 (atual) | v4 (proposto) |
|---------|-----------|--------------|
| Briefing define | "FadeIn Cloud SVG na posição LEFT" | "Curiosidade nasce de um ponto de luz" |
| Protagonista | Ícones de tecnologia | Formas geométricas abstratas |
| Manim renderiza | SVGs + dots movendo em arco | Curvas vivas + containers dinâmicos |
| Remotion adiciona | Labels "V3: DATA LAKE" | Tipografia narrativa sincronizada |
| Paleta | Vermelho + azul + branco + cores dos logos | Preto + branco + inversão dramática |
| Formato | 16:9 horizontal | 9:16 vertical (social-first) |
| Duração | 12s de ícones aparecendo | 15s de arco emocional com clímax |
| Personas | Decoração no output log | System prompts que governam decisões |

---

## PARTE 3: OS 6 NOVOS CONTRACTS

### 3.1 narrative.yaml (NOVO)

```yaml
# contracts/narrative.yaml
# Regras de storytelling que governam TODOS os briefings

structure:
  default_arc: three_act
  acts:
    genesis:
      duration_ratio: 0.25          # 25% do tempo total
      energy: [0.0, 0.3]
      emotion: curiosidade
      rules:
        - "Um único elemento visual nasce"
        - "Silêncio textual nos primeiros 2 segundos"
        - "Movimento lento e orgânico (spring damping > 20)"
        
    turbulence:
      duration_ratio: 0.45          # 45% do tempo total
      energy: [0.3, 1.0]
      emotion: tensão
      rules:
        - "Multiplicação visual: containers dividem, linhas se cruzam"
        - "Noise e caos crescente na curva principal"
        - "Clímax com inversão de cor ou escala"
        - "Texto aparece como narração, não como label"
        
    resolution:
      duration_ratio: 0.30          # 30% do tempo total
      energy: [1.0, 0.6]
      emotion: maestria
      rules:
        - "Caos se reorganiza em ordem mais elevada"
        - "Curva final mais alta que a original"
        - "Uma palavra. Só uma. Como assinatura"
        - "Branding sutil no último segundo"

pacing:
  text_minimum_gap: 1.5s           # Mínimo entre aparições de texto
  max_text_words_per_screen: 5     # Anti-poluição visual
  silence_ratio: 0.3               # 30% do vídeo sem texto nenhum

emotional_palette:
  curiosidade: { motion: slow_organic, space: generous_negative }
  tensão: { motion: fast_chaotic, space: compressed_dense }
  maestria: { motion: settled_confident, space: balanced_elegant }
```

### 3.2 typography.yaml (NOVO)

```yaml
# contracts/typography.yaml

fonts:
  narrative:
    family: "PP Neue Montreal"     # Clean, editorial, não é Inter
    weights:
      whisper: 300                 # Para reflexão
      statement: 500               # Para afirmação
    fallback: "Helvetica Neue, sans-serif"
    
  brand:
    family: "Cal Sans"
    weight: 600
    use: "Apenas no logo resolve final"

rules:
  sizing:
    vertical_9_16:
      narrative_text: "clamp(1.5rem, 4vw, 2.5rem)"
      brand_text: "0.875rem"
    wide_16_9:
      narrative_text: "clamp(1.2rem, 3vw, 2rem)"
      brand_text: "0.75rem"
      
  behavior:
    entrance: "fade_up_8px"        # Nunca snap. Sempre ease.
    exit: "fade_down_4px"
    sync_mode: "beat_aligned"       # Texto entra no beat da narrativa
    
  anti_patterns:
    - "NUNCA usar text-transform: uppercase em textos narrativos"
    - "NUNCA usar font-weight > 500 para corpo de texto"
    - "NUNCA colocar texto dentro de containers (caixas/badges)"
    - "NUNCA usar mais de 2 tamanhos de fonte por frame"
    
  positioning:
    vertical_rule: >
      Texto narrativo fica em 2 zonas: 
      top_zone (15% a 30% do topo) ou 
      bottom_zone (70% a 85% do fundo).
      NUNCA no centro vertical (isso é para clímax apenas).
```

### 3.3 camera.yaml (NOVO)

```yaml
# contracts/camera.yaml

default_behavior: "observational"    # Câmera como observador discreto

movements:
  static_breathe:
    description: "Câmera parada, mas com micro-movimento respiratório"
    scale_oscillation: 0.002          # ±0.2% de zoom sutil
    period: 4s
    use_for: [genesis, resolution]
    
  track_subject:
    description: "Câmera segue o elemento principal suavemente"
    spring: { stiffness: 40, damping: 25 }
    use_for: [turbulence]
    
  dramatic_zoom:
    description: "Zoom rápido para clímax"
    spring: { stiffness: 200, damping: 8 }
    use_for: [inversão de cor, resolução final]

container_choreography:
  split_horizontal:
    description: "Container se divide em 2 painéis lado a lado"
    animation: "center_expands_to_two"
    spring: { stiffness: 100, damping: 16 }
    
  split_triple:
    description: "Container se divide em 3 painéis"
    animation: "sequential_division"
    
  rotate:
    max_angle: 15                     # Graus máximos de rotação
    spring: { stiffness: 80, damping: 20 }
    
  boundary_break:
    description: "Elemento visual ultrapassa as bordas do container"
    overflow: visible
    effect: "tensão narrativa máxima"
```

### 3.4 brand.yaml (REESCRITO)

```yaml
# contracts/brand.yaml v4

identity:
  name: "AIOX"
  tagline: "The Invisible Architecture"

# DOIS ESTADOS CROMÁTICOS (a transição entre eles é um recurso narrativo)
color_states:
  dark:                              # 90% do tempo
    background: "#000000"
    foreground: "#FFFFFF"
    stroke: "rgba(255, 255, 255, 0.85)"
    text_primary: "#FFFFFF"
    text_secondary: "rgba(255, 255, 255, 0.55)"
    
  inverted:                          # Clímax dramático
    background: "#FFFFFF"
    foreground: "#000000"
    stroke: "rgba(0, 0, 0, 0.85)"
    text_primary: "#000000"
    text_secondary: "rgba(0, 0, 0, 0.55)"

  accent:                            # Uso cirúrgico (máximo 1 frame)
    color: "#FF3366"
    use: "Apenas para dot pulsante ou highlight momentâneo"
    max_screen_coverage: "2%"

materials:
  grain: 0.06                        # Mais sutil que v3
  stroke_width:
    primary: 1.5
    secondary: 0.5
    container: 0.8
    
anti_patterns:
  - "NUNCA usar gradientes"
  - "NUNCA usar sombras ou glow"
  - "NUNCA usar glassmorphism"
  - "NUNCA mostrar logos de tecnologia"
  - "NUNCA usar serif fonts"
  - "NUNCA usar text-transform: uppercase (exceto brand name)"
```

### 3.5 motion.yaml e layout.yaml (ATUALIZADOS)

```yaml
# contracts/motion.yaml v4
physics:
  default_engine: spring
  
  presets:
    gentle_birth: { stiffness: 40, damping: 26, mass: 1.2 }
    tension_build: { stiffness: 160, damping: 10, mass: 0.8 }
    elegant_settle: { stiffness: 80, damping: 22, mass: 1.0 }
    hard_cut: { duration: 0 }        # Sem transição. Impacto.

  curve_behaviors:
    sigmoid_growth:
      function: "1 / (1 + exp(-k*(x-x0)))"
      params: { k: 5, x0: 0.5 }
      
    noise_oscillation:
      base: sigmoid_growth
      noise_type: perlin
      amplitude_curve: "linear_ramp 0→0.4"
      
    chaotic_to_resolved:
      behavior: "noise decai exponencialmente até smooth"
      resolve_spring: elegant_settle

easing:
  default: "cubic_bezier(0.16, 1, 0.3, 1)"   # ease-out expo
  dramatic: "cubic_bezier(0.87, 0, 0.13, 1)"  # ease-in-out expo
  
interpolation:
  standard: smooth
  never_use: [linear, there_and_back]
```

```yaml
# contracts/layout.yaml v4
formats:
  vertical_9_16:
    width: 1080
    height: 1920
    safe_zone: 8%
    text_zones:
      top: { y: "15%", height: "15%" }
      bottom: { y: "70%", height: "15%" }
      center: { y: "42%", height: "16%" }  # Só para clímax
      
  wide_16_9:
    width: 1920
    height: 1080
    safe_zone: 6%
    
  square_1_1:
    width: 1080
    height: 1080
    safe_zone: 10%

composition:
  rule_of_thirds: true
  center_bias: 0.6                   # 60% do conteúdo na zona central
  edge_breathing: 64px               # Mínimo de respiro nas bordas
```

---

## PARTE 4: A BIBLIOTECA DE PRIMITIVOS NARRATIVOS (Manim)

O coração da mudança. Em vez de carregar SVGs, o Manim passa a usar primitivos abstratos reutilizáveis.

### 4.1 `core/primitives/curves.py`

```python
"""
Curvas narrativas: o protagonista visual dos vídeos.
Cada curva tem um 'comportamento' que evolui ao longo do tempo.
"""
from manim import *
import numpy as np

class LivingCurve(VMobject):
    """Curva que evolui de suave para caótica e volta."""
    
    def __init__(self, 
                 resolution=200,
                 noise_amplitude=0.0,
                 growth_progress=0.0,
                 **kwargs):
        super().__init__(**kwargs)
        self.resolution = resolution
        self.noise_amplitude = noise_amplitude
        self.growth_progress = growth_progress
        self._build_curve()
    
    def _build_curve(self):
        """Gera curva sigmoid com noise overlay."""
        points = []
        for i in range(int(self.resolution * self.growth_progress)):
            t = i / self.resolution
            # Base: sigmoid
            y = 1 / (1 + np.exp(-8 * (t - 0.5)))
            # Noise overlay
            if self.noise_amplitude > 0:
                noise = self.noise_amplitude * np.sin(30 * t) * np.cos(17 * t + 2.3)
                y += noise
            points.append(np.array([
                t * 6 - 3,    # x: -3 a 3
                y * 4 - 2,    # y: -2 a 2
                0
            ]))
        if len(points) > 1:
            self.set_points_smoothly(points)
    
    def grow_to(self, progress, noise=0.0):
        """Retorna updater para crescimento animado."""
        new = LivingCurve(
            resolution=self.resolution,
            noise_amplitude=noise,
            growth_progress=progress,
            stroke_color=self.get_stroke_color(),
            stroke_width=self.get_stroke_width()
        )
        return new
```

### 4.2 `core/primitives/containers.py`

```python
"""
Containers narrativos: frames que enquadram, dividem, rotacionam.
Inspirados na referência "Masterize".
"""
from manim import *

class NarrativeContainer(VGroup):
    """Container que pode se dividir, rotacionar e expandir."""
    
    def __init__(self, width=4, height=5, **kwargs):
        super().__init__(**kwargs)
        self.rect = Rectangle(
            width=width, height=height,
            stroke_color=WHITE, stroke_width=0.8,
            fill_opacity=0
        )
        self.add(self.rect)
    
    def split_horizontal(self, gap=0.3):
        """Retorna animação de divisão em dois painéis."""
        w = self.rect.width
        h = self.rect.height
        left = Rectangle(width=w/2 - gap/2, height=h,
                        stroke_color=WHITE, stroke_width=0.8, fill_opacity=0)
        right = Rectangle(width=w/2 - gap/2, height=h,
                         stroke_color=WHITE, stroke_width=0.8, fill_opacity=0)
        left.shift(LEFT * (w/4 + gap/4))
        right.shift(RIGHT * (w/4 + gap/4))
        return [left, right]
    
    def rotate_dramatic(self, angle=15):
        """Rotação com spring physics."""
        return self.rect.animate.rotate(
            angle * DEGREES,
            rate_func=smooth
        )
```

### 4.3 `core/primitives/color_states.py`

```python
"""
Gerenciamento de estados cromáticos: dark ↔ inverted.
A transição entre eles é o recurso narrativo mais poderoso.
"""
from manim import *

class ColorInversion:
    """Hard cut de preto→branco (ou vice-versa)."""
    
    @staticmethod
    def invert(scene, duration=0.0):
        """Inversão instantânea (hard cut)."""
        bg = FullScreenRectangle(
            fill_color=WHITE, fill_opacity=1
        )
        if duration == 0:
            scene.add(bg)
        else:
            scene.play(FadeIn(bg, run_time=duration))
        return bg
    
    @staticmethod  
    def revert(scene, bg_rect, duration=0.8):
        """Reverter suavemente."""
        scene.play(FadeOut(bg_rect, run_time=duration, rate_func=smooth))
```

---

## PARTE 5: PERSONAS COMO AGENTS REAIS

### 5.1 Como Funciona no Antigravity + Claude Code

As personas deixam de ser `.md` descritivos e viram system prompts executáveis que governam sessões do Claude Code / Antigravity.

**Fluxo de produção com agents:**

```
1. Você escreve o briefing YAML (narrativa + emoção)
2. Abre o Antigravity no projeto
3. Invoca: /aria → Aria analisa o briefing e gera um PLANO DE DIREÇÃO
4. Invoca: /dara → Dara pega o plano e gera o CÓDIGO MANIM
5. Invoca: /uma  → Uma revisa frames renderizados e dá FEEDBACK DE DESIGN
6. Repete até o frame passar no critério: "funciona como pôster se pausar?"
```

### 5.2 Aria (Director) — Nova Versão

```markdown
# .agents/personas/aria.md
---
name: aria-director
description: >
  Creative Director. Analisa briefings e gera planos de direção
  cinematográfica. Invoque quando precisar definir a narrativa,
  ritmo e arco emocional de um vídeo.
context: conversation
---

# Aria — Creative Director

Você é Aria, diretora criativa da AIOX.

## Sua função
Quando recebe um briefing YAML, você:
1. Lê o theme e os acts definidos
2. Valida se cada ato tem emoção clara
3. Gera um PLANO DE DIREÇÃO detalhado com:
   - Timing frame-by-frame para cada primitivo visual
   - Notas de "câmera" (zoom, pan, estática)
   - Onde o texto deve aparecer (e onde deve haver silêncio)
   - Onde o clímax visual acontece
   
## Regras absolutas
- Se um ato não tem emoção definida, REJEITE o briefing
- Se existem mais de 5 palavras de texto por tela, REDUZA
- 30% do vídeo deve ser silêncio visual (sem texto)
- Cada ato precisa de um "momento pôster" (frame que funciona parado)
- NUNCA sugira mostrar logos ou ícones de tecnologia

## Formato de output
Gere um JSON com a timeline completa que Dara (engineer) vai implementar.
```

### 5.3 Dara (Engineer) — Nova Versão

```markdown
# .agents/personas/dara.md
---
name: dara-engineer
description: >
  Production Engineer. Converte planos de direção em código Manim
  e componentes Remotion. Invoque quando precisar implementar
  animações, física de spring, e renderizar cenas.
context: conversation
---

# Dara — Production Engineer

Você é Dara, engenheira de produção da AIOX.

## Sua função
Quando recebe um plano de direção (de Aria), você:
1. Importa os primitivos de `core/primitives/`
2. Implementa cada ato como uma cena Manim
3. Define os timing events para sincronização com Remotion
4. Gera o código Remotion para tipografia e overlays

## Regras absolutas
- NUNCA use SVGMobject para logos de tecnologia
- NUNCA use FadeIn como animação principal (use Create, DrawBorderThenFill, ou custom)
- SEMPRE use primitivos de `core/primitives/` como base
- SEMPRE respeite os spring presets do motion.yaml
- SEMPRE exporte timing events via TimingLogger
- O Manim renderiza APENAS geometria e física. ZERO texto.
- O Remotion renderiza APENAS tipografia e composição. ZERO geometria.

## Stack
- Manim: curvas, containers, partículas, inversão de cor
- Remotion: texto narrativo, grain, diagonal accents, brand resolve
```

### 5.4 Uma (Designer) — Nova Versão

```markdown
# .agents/personas/uma.md
---
name: uma-designer
description: >
  Design System Engineer. Revisa frames renderizados e valida
  se passam no critério de qualidade premium. Invoque após
  renderização para QA visual.
context: conversation
---

# Uma — Design System Engineer

Você é Uma, designer de sistemas da AIOX.

## Sua função
Quando recebe frames renderizados, você:
1. Avalia cada frame contra o checklist de qualidade
2. Dá feedback específico e acionável
3. Não aceita "bom o suficiente" — só aceita "funciona como pôster"

## Checklist de qualidade (cada frame deve passar em TODOS)
- [ ] Frame funciona como pôster se pausar?
- [ ] Máximo 2 tamanhos de fonte visíveis?
- [ ] Espaço negativo generoso (>40% da tela é "vazio")?
- [ ] Nenhum elemento encosta nas bordas (mín 64px)?
- [ ] Paleta monocromática respeitada (máx 2 cores + inversão)?
- [ ] Texto em posição narrativa (não centralizado, não em caixa)?
- [ ] Nenhum logo de tecnologia visível?
- [ ] Grain sutil mas presente?
- [ ] Cada forma tem propósito narrativo (não decoração)?

## Formato de output
Lista de issues por frame, com severidade (block / warn / note).
```

---

## PARTE 6: INTEGRAÇÃO COM ANTIGRAVITY

### 6.1 Setup

```bash
# No diretório do projeto
cd ~/Documents/Bordeless/manim

# Copiar personas como skills invocáveis
cp .agents/personas/aria.md .claude/skills/aria-director/SKILL.md
cp .agents/personas/dara.md .claude/skills/dara-engineer/SKILL.md
cp .agents/personas/uma.md .claude/skills/uma-designer/SKILL.md

# Para Antigravity
cp -r .claude/skills/* .agent/skills/
```

### 6.2 Workflow no Antigravity

```
Passo 1: Criar briefing
  → Editar briefings/novo_video.yaml usando o template

Passo 2: Rodar Aria
  → No Antigravity: "Use a skill aria-director para analisar 
     o briefing em briefings/novo_video.yaml e gerar um plano 
     de direção"
  → Aria gera: .agents/briefs/novo_video_direction.json

Passo 3: Rodar Dara
  → "Use a skill dara-engineer para implementar o plano de 
     direção em .agents/briefs/novo_video_direction.json"
  → Dara gera: engines/manim/scenes/novo_video.py
  →           engines/remotion/src/compositions/NovoVideo.tsx

Passo 4: Renderizar
  → "Renderize a cena Manim e depois a composição Remotion"
  → Output: output/novo_video.mp4

Passo 5: QA com Uma
  → "Use a skill uma-designer para revisar os frames de 
     output/novo_video.mp4"
  → Uma retorna: lista de issues

Passo 6: Iterar
  → Corrigir issues e re-renderizar até Uma aprovar
```

### 6.3 O Poder do Antigravity Multi-Agent

O Antigravity permite rodar múltiplos agents em paralelo. O setup ideal:

```
Agent A (Aria): Analisa briefing → gera plano
Agent B (Dara): Implementa plano → gera código → renderiza
Agent C (Uma): Revisa output → dá feedback
```

Os três trabalham no mesmo workspace, cada um com seu escopo. Aria não toca código. Dara não questiona narrativa. Uma não implementa — só valida.

---

## PARTE 7: SEQUÊNCIA DE IMPLEMENTAÇÃO

### Fase 1: Contracts + Primitivos (1 sessão)
1. Criar os 6 contracts YAML
2. Implementar `core/primitives/` (curves, containers, color_states)
3. Atualizar `sync_brand.py` para compilar os 6 contracts

### Fase 2: Personas + Templates (1 sessão)
4. Reescrever as 3 personas como skills executáveis
5. Criar template de briefing `cinematic_narrative.yaml`
6. Configurar skills no Claude Code e Antigravity

### Fase 3: Engine Manim (1-2 sessões)
7. Criar cena de teste usando primitivos (genesis → turbulence → resolution)
8. Implementar inversão de cor
9. Implementar containers dinâmicos (split, rotate, boundary break)
10. Renderizar e validar frames

### Fase 4: Engine Remotion (1 sessão)
11. Criar `NarrativeText.tsx` (tipografia sincronizada)
12. Criar `ColorInversion.tsx`
13. Criar `CinematicNarrative.tsx` (composition principal)
14. Conectar timing events do Manim

### Fase 5: Orquestração (1 sessão)
15. Reescrever `orchestrator.py` para nova estrutura
16. Atualizar `run_pipeline.py`
17. Testar pipeline completo: briefing → render → output

### Fase 6: QA + Polish (1-2 sessões)
18. Rodar Uma no output
19. Iterar até qualidade premium
20. Documentar o workflow final

---

## PARTE 8: O QUE MUDA NA SUA ROTINA

**Antes (v3):**
```
Você: escreve briefing com "FadeIn Cloud SVG"
Claude/Antigravity: gera código que faz FadeIn de Cloud SVG
Output: catálogo animado de ícones
```

**Depois (v4):**
```
Você: escreve briefing com "curiosidade nasce de um ponto de luz"
Aria: gera plano de direção com timing preciso
Dara: implementa com primitivos (curvas, containers, inversão)
Uma: valida que cada frame é um pôster
Output: cinema de dados narrativo
```

A mudança fundamental é: você passa a ser o **roteirista** do vídeo, não o **animador**. Você descreve emoções e metáforas. Os agents traduzem isso em código. Isso é o que permite escalar — qualquer história pode ser contada com o mesmo pipeline de primitivos.

---

## RESUMO EXECUTIVO

| Entregável | Status | Impacto |
|-----------|--------|---------|
| 6 contracts YAML | A criar | Governa toda a qualidade |
| Biblioteca de primitivos Manim | A criar | Elimina dependência de SVGs |
| 3 personas como agents executáveis | A reescrever | Workflow com Antigravity |
| Template de briefing narrativo | A criar | Briefings emocionais, não técnicos |
| Componentes Remotion (texto, inversão) | A criar | Tipografia premium sincronizada |
| Orchestrator v4 | A reescrever | Suporta nova arquitetura |
| Pipeline completo testado | A validar | 200%+ de qualidade |

