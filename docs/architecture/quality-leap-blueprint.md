# AIOX Quality Leap — Architecture Blueprint
**Date:** 2026-04-01
**Status:** Draft for backlog conversion
**Author:** Architecture pass over real repo state

---

## 1. Executive Diagnosis

AIOX has something rare: a *working* end-to-end pipeline from narrative intent through hybrid Manim+Remotion rendering to judged output. The contracts system, agent personas, and quality loop are real code, not aspirations. The v4 plan correctly identified that the old system was "a slideshow with labels" and redesigned it around emotional arcs, semantic motion, and narrative typography.

But the system has reached a **structural plateau**. The architecture can produce *one aesthetic* reliably — dark, minimal, geometric, monochromatic — and struggles to produce anything else. The contracts are deep in philosophy but shallow in parameterization. The judge scores vibes, not craft. The typography system has one voice. The motion system has physics tokens but no grammar. The still pipeline borrows from the motion pipeline instead of having its own architecture.

The gap is not code quality. The gap is that **the system describes a premium visual language but does not yet model the structure of visual decisions** at a resolution fine enough to produce consistently excellent output across varied creative intents.

---

## 2. What the System Already Gets Right

- **Narrative-first briefings.** Emotion-per-act structure is the correct paradigm. The three-act model (genesis/turbulence/resolution) is a real creative framework, not a fake one.
- **Contract-driven rendering.** YAML contracts as the single source of truth for brand, motion, typography, layout, and narrative is architecturally sound. The `contract_loader.py` caching pattern is clean.
- **Hybrid engine split.** Manim for physics/geometry and Remotion for typography/composition is the right separation of concerns. Neither engine is asked to do what it's bad at.
- **Agent personas with real logic.** `kael.py` (pacing), `aria.py` (archetype), `zara.py` (entropy) are not decorative — they produce structured outputs consumed by the compiler. The `PacingProfile` and `EntropyProfile` concepts are solid.
- **Self-correcting render loop.** `auto_iterate.py` with `frame_scorer.py` is the right architecture: render → judge → extract corrections → re-plan → re-render. Few systems have this loop at all.
- **Multi-target composition routing.** `TargetedCinematicNarrative.tsx` with `getTargetVisualProfile()` correctly separates target-specific tuning from shared narrative logic.
- **Render manifest as intermediate representation.** `render_manifest.py` as the bridge between creative plan and render engine is the correct compilation pattern.

---

## 3. Why Current Quality Likely Plateaus

### 3.1 Typography is a single voice, not a system
`NarrativeText.tsx` has five roles (whisper/statement/climax/resolve/brand) with hardcoded spring configs, letter-spacing, and scale values. This is one typographic personality. There is no concept of typographic *architecture* — how multiple text elements relate to each other spatially, how type creates hierarchy through scale ratios (not just weight), how line length and line breaking create rhythm, or how type can be the *primary visual element* rather than annotation on geometry.

The contract (`typography.yaml`) lists anti-patterns but doesn't define positive *typographic systems*. There's no concept of: display vs body, baseline grid, optical alignment, cap-height relationships, measure control, rag quality, or typographic color (density of strokes on page).

### 3.2 Motion is physics without grammar
`motion.yaml` defines spring presets and curve behaviors. The signature YAMLs define physics parameters. But there is no *motion grammar* — no system for how motions compose, how transitions between acts work, what constitutes a "beat", how silence (stillness) is metered, how motion creates anticipation vs release, or how the tempo of motion varies within an act (not just between acts).

`plan_generator.py` hardcodes timeline phases per archetype. This means every `chaos_to_order` video has the same motion structure. There's no variation within an archetype's motion vocabulary.

### 3.3 Stills are demoted video frames, not authored compositions
The linkedin_feed_4_5 target gets a `frameOverride` to extract a single frame from the video composition. But a great still has different compositional needs than a video frame: it needs stronger spatial hierarchy, more deliberate typography placement, considered negative space distribution, and visual tension that works without temporal context. The current still pipeline renders frame 0 of a video composition — it doesn't compose a poster.

### 3.4 The judge cannot distinguish good from great
`frame_scorer.py` has 5 dimensions (composition, typography, color, motion_signature, brand_compliance) scored 0-100 by a vision LLM against a checklist. The criteria are binary compliance checks ("Max 2 font weights", "No gradients") rather than aesthetic quality assessments. A frame that passes all rules can still be mediocre. The judge cannot evaluate: visual tension, hierarchy strength, typographic craft, poster impact, emotional resonance, or whether the composition feels *authored* vs *generated*.

The correction recipes in `auto_iterate.py` are also compliance-focused ("Reduce to MAX 3 words") rather than craft-focused ("The visual hierarchy is flat — increase the scale ratio between primary and secondary text from 1.2x to 2.5x").

### 3.5 Creative range is locked to one aesthetic
The system can only produce: black background, white text, geometric lines, minimal accent. Every archetype shares this visual language. There's no mechanism for:
- warm vs cold palettes
- photographic vs geometric backgrounds
- dense editorial layouts vs airy minimal ones
- brutalist vs refined typography
- different visual "families" that still feel premium

---

## 4. Typography System Architecture

### 4.1 What is missing

| Missing concept | Why it matters |
|---|---|
| **Scale system** | Type sizes currently use `clamp()` without relational hierarchy. A headline at 5.4rem with body at 1.25rem = 4.32x ratio — but this ratio isn't intentional, it's incidental. The system needs a modular type scale (e.g., 1.333 perfect fourth, 1.618 golden ratio) chosen per artifact family. |
| **Measure control** | `maxWidth: '74%'` doesn't create a typographic measure. The optimal reading measure is 45-75 characters. For display type, measure should be controlled by the number of words, not container width. |
| **Baseline grid** | No vertical rhythm. Text elements are positioned by zone (top/center/bottom) without relationship to each other. In premium typography, every element sits on a baseline grid that creates invisible vertical order. |
| **Line breaking intelligence** | The system has no concept of where text should break. "The Invisible Architecture" could break as "The Invisible / Architecture" or "The / Invisible Architecture" — these have very different visual and semantic weight. |
| **Typographic color** | No awareness of how dense the strokes are on the page. Light weight at large size creates very different density than medium weight at small size. The system should model this. |
| **Text-as-structure** | Type is always overlaid on geometry. It should sometimes *be* the geometry — a large resolve word as architectural form, not annotation. |
| **Cadence** | Multiple text cues are staggered by time gap but without rhythmic intent. The gaps between text entries should vary to create musical cadence — not just "minimum 1.5s between entries". |

### 4.2 First-class typography primitives

```
TypographicAtom
├── role: whisper | statement | display | title | caption | resolve | brand
├── content: string
├── measure: number (characters or words, not pixels)
├── breakStrategy: semantic | balanced | none
├── scale: derived from ScaleSystem + role
├── weight: derived from role + emphasis
├── tracking: derived from size (larger = tighter)
├── leading: derived from role (display = tight, body = open)
├── opticalAlign: true | false (visual vs mathematical center)
└── density: light | medium | dense (controls typographic color)

TypographicBlock
├── atoms: TypographicAtom[]
├── layout: stack | inline | scattered | architectural
├── alignment: optical_left | mathematical_center | flush_right | justified
├── baselineGrid: number (vertical rhythm unit in px)
├── groupRelationship: hierarchy | sequence | contrast | echo
└── spatialAnchor: compositional_zone | geometric_element | free

ScaleSystem
├── base: number (px)
├── ratio: 1.125 | 1.2 | 1.25 | 1.333 | 1.414 | 1.5 | 1.618 | 2.0
├── steps: derived (base * ratio^n for n in range)
└── family: {display: step[5], title: step[4], body: step[1], caption: step[0]}
```

### 4.3 Typography contracts to introduce

**`contracts/typography_systems/`** — a library of named typographic systems:

```yaml
# contracts/typography_systems/editorial_minimal.yaml
id: editorial_minimal
description: "Apple Keynote inspired. Maximum restraint."
scale:
  base_px: 18
  ratio: 1.618  # golden ratio
  display_step: 5   # 18 * 1.618^5 ≈ 198px
  title_step: 3     # 18 * 1.618^3 ≈ 76px
  body_step: 1      # 18 * 1.618^1 ≈ 29px
  caption_step: 0   # 18px
density: light
max_words_per_block: 3
measure_chars: 20  # very short lines
tracking_at_display: -0.06em
tracking_at_body: -0.02em
leading_display: 0.88
leading_body: 1.35
break_strategy: semantic
alignment_default: optical_left
```

```yaml
# contracts/typography_systems/editorial_dense.yaml
id: editorial_dense
description: "Stripe Sessions inspired. Information-rich but ordered."
scale:
  base_px: 16
  ratio: 1.25  # major third
  display_step: 4   # 16 * 1.25^4 ≈ 39px
  title_step: 3     # 31px
  body_step: 1      # 20px
  caption_step: 0   # 16px
density: medium
max_words_per_block: 8
measure_chars: 45
tracking_at_display: -0.04em
tracking_at_body: -0.01em
leading_display: 1.05
leading_body: 1.5
break_strategy: balanced
alignment_default: mathematical_center
```

### 4.4 Typography per artifact family

| Artifact | Scale ratio | Max words | Display tracking | Alignment | Break |
|---|---|---|---|---|---|
| Premium still (linkedin_feed_4_5) | 1.618 (golden) | 5 | -0.06em | optical left | semantic |
| Short vertical motion | 1.414 (augmented fourth) | 4 | -0.05em | left/center by zone | semantic |
| Essay / cinematic (16:9) | 1.25 (major third) | 8 | -0.03em | center or flush left | balanced |
| Thumbnail | 2.0 (octave) | 3 | -0.08em | center | none |
| Carousel | 1.333 (perfect fourth) | 6 | -0.04em | left | balanced |

### 4.5 Planner vs engine for typography

| Decision | Owner |
|---|---|
| What text appears in what order | **Planner** (LLM + narrative contract) |
| Which typography system to use | **Planner** (selected from library based on artifact + intent) |
| Text role assignment (whisper/display/etc) | **Planner** |
| Line breaking | **Engine** (deterministic algorithm: semantic breaks + rag quality check) |
| Scale values | **Engine** (computed from ScaleSystem) |
| Tracking/leading | **Engine** (lookup table from role + size) |
| Baseline grid placement | **Engine** (snap to grid) |
| Optical alignment adjustment | **Engine** (cap-height calculation) |

### 4.6 How typography should be judged

Add these dimensions to the judge:

- **Scale hierarchy clarity**: ratio between largest and second-largest type > 2.5x. Binary check + degree measurement.
- **Typographic color uniformity**: variance in stroke density across the frame. Should be intentionally varied (hierarchy) not accidentally varied (sloppy).
- **Measure quality**: no line of display text exceeds 20 characters OR no body text exceeds 50 characters (per typography system).
- **Rag quality**: right-edge of flush-left text should not create a monotonous straight line or deeply jagged line. Target is "organic but controlled".
- **Baseline alignment**: when multiple text blocks exist, their baselines should relate to a common grid.
- **Text isolation**: minimum distance between any two text blocks. Type needs air.

---

## 5. Motion System Architecture

### 5.1 What is missing

| Missing concept | Why it matters |
|---|---|
| **Motion grammar** | Individual motions exist (spring, ease, snap) but there's no grammar for composing them. "Anticipation → action → follow-through" is a motion sentence. The system has words but no syntax. |
| **Temporal silence** | `silence_ratio >= 0.30` is a number. Silence should be *placed* — before reveals, after climaxes, at act boundaries. Silence is the most powerful motion tool. |
| **Transition vocabulary** | How does one act transition to the next? Cut? Cross-dissolve? Spatial wipe? Push? The system defaults to sequential playback. |
| **Inertia** | Elements have spring configs but no mass continuity. When something stops moving, it should feel like it carries the energy of its motion, not like it was paused. |
| **Rhythm variation** | Every stagger is uniform (equal time gaps). Real authored motion varies the stagger — quick-quick-slow, or accelerating, or decelerating. |
| **Camera as character** | `camera.yaml` defines movements but camera is not integrated into the motion runtime. Camera should breathe, react to content, and have its own pacing profile. |

### 5.2 Motion grammar primitives

```
MotionPhrase
├── anticipation: MotionAtom (subtle cue before the main action)
├── action: MotionAtom (the main motion event)
├── followThrough: MotionAtom (overshoot, settle, or echo)
├── recovery: Duration (silence/stillness after the phrase)
└── emphasis: low | medium | high (controls amplitude of all atoms)

MotionSequence
├── phrases: MotionPhrase[]
├── rhythm: uniform | accelerating | decelerating | syncopated | custom
├── staggerProfile: number[] (relative delays, e.g., [0, 1, 1, 2, 3])
├── breathPoints: Timestamp[] (enforced stillness moments)
└── transitionTo: TransitionType (how this sequence hands off to the next)

TransitionType
├── cut (instant, no interpolation)
├── crossfade (opacity blend)
├── spatial_wipe (geometry-driven reveal)
├── push (outgoing pushes in, incoming pushes out)
├── morph (elements transform into new state)
└── silence_bridge (hold stillness, then begin new sequence)

MotionAtom
├── property: position | scale | opacity | rotation | skew | blur | clip
├── from: value
├── to: value
├── easing: EasingProfile
├── duration: number (ms)
├── delay: number (ms)
└── spring: SpringConfig | null
```

### 5.3 Motion contracts to introduce

**`contracts/motion_grammars/`** — named motion languages:

```yaml
# contracts/motion_grammars/cinematic_restrained.yaml
id: cinematic_restrained
description: "Kurosawa-inspired. Long holds. Decisive movements."
principles:
  - "stillness is the default state"
  - "motion is earned — only move when meaning demands it"
  - "one element moves at a time"
timing:
  minimum_hold_ms: 800    # nothing moves for less than 800ms
  maximum_simultaneous: 1 # one motion phrase at a time
  silence_between_phrases_ms: [400, 1200]  # range
rhythm: decelerating  # start brisk, end in long holds
stagger: [0, 3, 5, 8]  # fibonacci-ish, increasing gaps
transitions:
  act_to_act: silence_bridge
  within_act: cut
camera:
  default: static_breathe
  climax_only: [dramatic_zoom, track_subject]
```

```yaml
# contracts/motion_grammars/kinetic_editorial.yaml
id: kinetic_editorial
description: "Stripe/Linear-inspired. Precise, rhythmic, information-rich."
principles:
  - "motion carries information"
  - "stagger creates reading order"
  - "spring physics everywhere — no linear interpolation"
timing:
  minimum_hold_ms: 200
  maximum_simultaneous: 3
  silence_between_phrases_ms: [100, 400]
rhythm: syncopated  # varying pace creates visual music
stagger: [0, 1, 1, 2, 1]  # quick-quick-long-quick
transitions:
  act_to_act: push
  within_act: crossfade
camera:
  default: track_subject
  all_acts: [static_breathe, track_subject]
```

### 5.4 Manim vs Remotion rebalancing

The current split is correct in principle but should be refined:

| Responsibility | Manim | Remotion |
|---|---|---|
| Particle systems, physics fields | **Yes** | No |
| Curve math (sigmoid, perlin, fbm) | **Yes** | No |
| Geometric primitives (containers, grids) | **Yes** | No |
| Typography (all) | No | **Yes** |
| Camera (virtual camera, zoom, pan) | Shared: Manim for math, Remotion for implementation | **Yes** |
| Transitions between acts | No | **Yes** |
| Color state transitions (inversion) | No | **Yes** |
| Grain/texture overlays | No | **Yes** |
| Still composition (entire) | No | **Yes** — stills should not go through Manim at all unless they need physics geometry |

**Key change for stills:** Premium stills should bypass Manim entirely when the composition doesn't require physics geometry. A linkedin_feed_4_5 hero poster is pure typography + composition + accent geometry — all natively Remotion. Manim involvement should be opt-in (e.g., if the still needs a particle field background), not default.

### 5.5 How motion should be judged (separate from stills)

- **Phrase completeness**: does every motion have anticipation + action + follow-through? Or do elements just "appear"?
- **Silence placement**: are there intentional holds before reveals and after climaxes?
- **Rhythm consistency**: does the stagger pattern feel intentional or random?
- **Spring character**: do spring physics feel tuned to the emotional context? (Gentle genesis vs tense turbulence)
- **Transition quality**: do act transitions feel authored or just "next scene"?
- **Camera integration**: does camera motion support or fight the content motion?

---

## 6. Premium Still Factory Architecture

### 6.1 Why stills need their own pipeline

A great still is not a "paused video". The considerations are fundamentally different:

| Video frame concern | Still/poster concern |
|---|---|
| Motion context gives meaning | **Must communicate without temporal context** |
| Typography moves in/out | **Typography is permanently visible — every letter placement matters** |
| Eye follows motion | **Eye navigates spatial composition — hierarchy must be instant** |
| Imperfections pass at speed | **Every pixel is scrutinized** |
| Duration creates narrative | **Single image must contain narrative tension** |

### 6.2 Canonical premium still pipeline

```
┌─────────────────────────────────────┐
│  1. CONCEPT SEED                     │
│  Intent + archetype + target format  │
│  → Output: StillBrief                │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  2. COMPOSITION PLANNING            │
│  Planner selects:                    │
│  - StillFamily (poster/editorial/    │
│    data-display/portrait/abstract)   │
│  - TypographySystem                  │
│  - CompositionGrid                   │
│  - AccentStrategy                    │
│  → Output: StillCompositionPlan      │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  3. GEOMETRIC BASE (optional)        │
│  If physics geometry needed:         │
│  Manim renders → crop → export PNG   │
│  If not: skip entirely               │
│  → Output: base_geometry.png | null  │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  4. COMPOSITION ENGINE (Remotion)    │
│  Builds the final still:             │
│  - Background layer (color/gradient/ │
│    geometry/editorial photo)          │
│  - Compositional zones               │
│  - Typography blocks (full system)   │
│  - Accent elements (lines, dots,     │
│    frames, counters)                  │
│  - Grain/texture finish              │
│  → Output: candidate.png             │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  5. POSTER TEST                      │
│  Judge evaluates as still:           │
│  - Hierarchy strength (instant read) │
│  - Negative space quality            │
│  - Type craft (rag, measure, scale)  │
│  - Visual tension (without motion)   │
│  - Poster "stop power"               │
│  → Output: PosterScore + corrections │
└──────────────────┬──────────────────┘
                   │
┌──────────────────▼──────────────────┐
│  6. ITERATION (if needed)            │
│  Apply corrections → re-compose      │
│  Max 3 cycles                        │
│  → Output: final.png                 │
└─────────────────────────────────────┘
```

### 6.3 Still families as reusable systems

```yaml
# contracts/still_families/poster_minimal.yaml
id: poster_minimal
description: "Maximum restraint. One word. One line. Black field."
base: null  # no Manim geometry
background: solid_dark
typography_system: editorial_minimal
composition_grid: golden_section
accent: single_rule_line  # one thin horizontal or diagonal
negative_space_min: 0.60
max_text_elements: 2
max_visual_elements: 1
grain: 0.06
```

```yaml
# contracts/still_families/editorial_portrait.yaml
id: editorial_portrait
description: "Magazine cover energy. Photo base. Bold type."
base: editorial_photo  # or Manim geometry
background: photo_with_veil
typography_system: editorial_dense
composition_grid: rule_of_thirds
accent: frame_crop + subtle_counter
negative_space_min: 0.35
max_text_elements: 4
max_visual_elements: 2
grain: 0.04
```

```yaml
# contracts/still_families/data_poster.yaml
id: data_poster
description: "Tufte-meets-cinema. Single data point as hero."
base: manim_geometry  # Manim renders the data visualization
background: dark_with_geometry_base
typography_system: editorial_minimal
composition_grid: swiss_grid
accent: data_callout + axis_lines
negative_space_min: 0.50
max_text_elements: 3
max_visual_elements: 1  # the data vis itself
grain: 0.08
```

### 6.4 How to support radically different visual languages

The key insight: **variety comes from combining different values of the same structural parameters, not from different code paths.** A brutalist poster and a minimal poster differ in:
- typography system (dense vs sparse)
- scale ratio (high contrast vs low contrast)
- negative space target (35% vs 65%)
- accent intensity (bold vs subtle)
- grain (high vs low)
- background complexity (textured vs pure)

All of these are parameterizable. The system needs a `StylePack` concept — a named bundle of parameter choices:

```yaml
# contracts/style_packs/silent_luxury.yaml
id: silent_luxury
typography_system: editorial_minimal
motion_grammar: cinematic_restrained  # for video variants
still_family: poster_minimal
color_mode: monochrome_pure
grain: 0.04
accent_intensity: 0.1  # barely there
negative_space_target: 0.65
```

```yaml
# contracts/style_packs/kinetic_editorial.yaml
id: kinetic_editorial
typography_system: editorial_dense
motion_grammar: kinetic_editorial
still_family: editorial_portrait
color_mode: monochrome_warm  # allows off-whites
grain: 0.08
accent_intensity: 0.5
negative_space_target: 0.40
```

The planner selects a StylePack based on intent + archetype. All downstream systems read their parameters from it. This is how the system produces varied output without different code paths.

---

## 7. Judge Redesign Architecture

### 7.1 Likely weaknesses in current architecture

1. **Compliance ≠ quality.** The current checklist asks "did you follow the rules?" not "did you make something excellent?" A perfectly compliant frame can be boring.
2. **Single-pass scoring.** The vision LLM gets one prompt and must evaluate everything. Human design critics work differently — they have an immediate gut reaction, then analyze specifics.
3. **No artifact-aware scoring.** The same checklist applies to stills and video frames. A still poster needs different evaluation than a mid-act video frame.
4. **No comparative evaluation.** The judge scores each frame in isolation. It cannot say "this is better than the last iteration" in a structured way.
5. **Correction recipes are compliance patches.** "Reduce to MAX 3 words" is a rule fix, not a design fix. The corrections should be about *craft* — "increase the scale hierarchy", "add visual tension through diagonal placement", "create asymmetry in the negative space distribution".
6. **No hard vetoes.** Everything is scored 0-100. But some things should be absolute failures: text overlapping text, completely empty frame, text bleeding off canvas, illegible text-on-background contrast.

### 7.2 New scoring architecture

#### 7.2.1 Two-pass evaluation

**Pass 1 — Structural check (programmatic, no LLM, <100ms)**
`brand_validator.py` already does this partially. Expand to include:
- Hard vetoes: text clipping, zero contrast, empty frame, more than N colors
- Structural metrics: negative space %, text density, color purity, grain level
- Geometric checks: safe zone compliance, element overlap detection

If Pass 1 fails hard vetoes → reject immediately, don't waste LLM call.

**Pass 2 — Craft evaluation (vision LLM, artifact-aware)**
Different prompts for different artifact types:

```
StillPosterPrompt → evaluates: poster impact, hierarchy strength, type craft, tension, stop-power
VideoFramePrompt → evaluates: motion coherence, temporal context fit, rhythm, anticipation
CarouselSlidePrompt → evaluates: series consistency, narrative progression, readability at speed
ThumbnailPrompt → evaluates: instant readability, click magnetism, scale at small sizes
```

#### 7.2.2 New score dimensions

Replace the current 5 with 8 artifact-aware dimensions:

**For stills/posters:**

| Dimension | Weight | What it measures |
|---|---|---|
| hierarchy_strength | 0.20 | Is the visual hierarchy instant? Can you identify the primary element in < 0.5s? |
| typographic_craft | 0.20 | Scale relationships, measure quality, tracking, leading, rag quality |
| spatial_intelligence | 0.15 | Negative space is intentional, not leftover. Composition has tension. |
| poster_impact | 0.15 | "Stop power" — would this halt a scrolling thumb? |
| brand_discipline | 0.10 | On-palette, no anti-patterns, accent used sparingly |
| material_finish | 0.10 | Grain quality, texture consistency, surface feel |
| emotional_coherence | 0.05 | Does the mood match the intent? |
| originality | 0.05 | Within contract bounds, does this feel authored or templated? |

**For motion:**

| Dimension | Weight |
|---|---|
| motion_coherence | 0.20 |
| temporal_rhythm | 0.15 |
| typographic_craft | 0.15 |
| spatial_intelligence | 0.15 |
| transition_quality | 0.10 |
| emotional_arc | 0.10 |
| brand_discipline | 0.10 |
| silence_quality | 0.05 |

#### 7.2.3 Hard vetoes (instant reject, no score)

```python
HARD_VETOES = [
    "text_off_canvas",        # any text bleeding past safe zone
    "text_overlap_text",      # two text blocks occupying same space
    "zero_hierarchy",         # everything same size/weight
    "illegible_contrast",     # text/background contrast ratio < 3:1
    "empty_frame",            # > 98% single color with no content
    "gradient_detected",      # any gradient present
    "logo_detected",          # forbidden element present
]
```

#### 7.2.4 Craft-oriented correction recipes

Replace compliance fixes with structural design fixes:

```python
CRAFT_CORRECTIONS = {
    "hierarchy_strength": {
        "critical": "STRUCTURAL: The composition has no clear focal point. Increase the scale ratio "
                    "between the primary element and everything else to at least 3:1. "
                    "Remove or shrink secondary elements until one thing dominates.",
        "poor": "The hierarchy reads but weakly. Increase display type size by 1.5x while "
                "keeping secondary elements stable. Create more dramatic scale contrast.",
        "weak": "Hierarchy is present but could be sharper. Try pulling the primary element "
                "slightly off-center for more dynamic tension.",
    },
    "typographic_craft": {
        "critical": "TYPE EMERGENCY: Text is either too dense, poorly scaled, or badly ragged. "
                    "Apply the typography system's scale ratio strictly. "
                    "Check: measure ≤ 20 chars for display, rag quality on right edge, "
                    "tracking tightens as size increases.",
        "poor": "Type needs tuning. Check letter-spacing at display sizes (should be negative). "
                "Verify line breaks are semantic, not arbitrary. "
                "Ensure cap-height alignment between adjacent blocks.",
        "weak": "Minor type issues. Fine-tune leading, check for widows/orphans, "
                "verify optical alignment vs mathematical alignment.",
    },
    "spatial_intelligence": {
        "critical": "SPACE FAILURE: Negative space feels accidental, not designed. "
                    "Increase minimum negative space to 55%. "
                    "Group content into one clear zone and leave the rest empty. "
                    "Empty space must feel intentional — asymmetric, generous, breathing.",
        "poor": "Composition feels cramped or unbalanced. "
                "Redistribute elements toward rule-of-thirds intersections. "
                "Ensure at least one large continuous empty area.",
        "weak": "Space is adequate but could be more intentional. "
                "Consider pushing content further off-center for dynamic tension.",
    },
    "poster_impact": {
        "critical": "NO STOP POWER: This would not halt a scrolling thumb. "
                    "Needs dramatic scale, high contrast, or visual surprise. "
                    "Try: massive display type, extreme negative space, or bold accent placement.",
        "poor": "Impact is mild. Increase visual contrast. "
                "Try bigger type, more decisive placement, or a single bold accent element.",
        "weak": "Good foundation but needs the final 10% of polish for true poster impact.",
    },
}
```

---

## 8. New Contract Layers to Introduce

### Current state
```
contracts/
├── brand.yaml, motion.yaml, layout.yaml, typography.yaml
├── narrative.yaml, camera.yaml, global_laws.yaml
├── design_canon.yaml, post_processing.yaml
├── narrative/archetypes/    (12 archetypes)
├── motion/signatures/       (8 signatures)
└── references/              (3 reference systems)
```

### Proposed additions
```
contracts/
├── (existing, preserved)
├── typography_systems/      # NEW: named typography parameter sets
│   ├── editorial_minimal.yaml
│   ├── editorial_dense.yaml
│   └── display_heroic.yaml
├── motion_grammars/         # NEW: named motion composition rules
│   ├── cinematic_restrained.yaml
│   ├── kinetic_editorial.yaml
│   └── ambient_drift.yaml
├── still_families/          # NEW: named still composition archetypes
│   ├── poster_minimal.yaml
│   ├── editorial_portrait.yaml
│   ├── data_poster.yaml
│   └── abstract_field.yaml
├── style_packs/             # NEW: bundles that select one from each system
│   ├── silent_luxury.yaml
│   ├── kinetic_editorial.yaml
│   ├── brutalist_signal.yaml
│   └── organic_warm.yaml
└── judge_profiles/          # NEW: artifact-specific scoring configs
    ├── premium_still.yaml
    ├── motion_frame.yaml
    ├── thumbnail.yaml
    └── carousel_slide.yaml
```

### Hierarchy
```
StylePack
  → selects: TypographySystem + MotionGrammar + StillFamily + ColorMode
  → consumed by: Planner (artifact_plan), RenderManifest, Judge

TypographySystem → consumed by: NarrativeText.tsx, type layout engine
MotionGrammar → consumed by: plan_generator.py, kael.py, Remotion motion runtime
StillFamily → consumed by: still composition pipeline (new)
JudgeProfile → consumed by: frame_scorer.py, auto_iterate.py
```

---

## 9. Planner vs Deterministic Engine Split

The system is currently too fuzzy in some places and too rigid in others.

### Must be PLANNER (LLM) decisions
- Which archetype fits the intent
- Which StylePack to select
- What text content appears
- What text roles to assign (whisper/statement/etc)
- Which acts get text and which are silent
- Whether to use Manim geometry for the base
- Emotional arc calibration
- When to break rules (e.g., "use 3 colors for this specific concept")

### Must be ENGINE (deterministic) decisions
- Type scale computation from ScaleSystem
- Letter-spacing at given size
- Leading at given role
- Line breaking algorithm
- Baseline grid snapping
- Safe zone enforcement
- Color palette enforcement
- Negative space calculation
- Grain application
- Spring physics computation
- Stagger timing from rhythm profile
- Hard veto checks

### Currently too fuzzy (move toward deterministic)
- **Typography sizing**: currently `clamp()` CSS — should be computed from ScaleSystem
- **Text placement**: currently zone-based — should be grid-based with optical alignment
- **Motion timing**: currently hardcoded per archetype in `plan_generator.py` — should be derived from MotionGrammar

### Currently too rigid (move toward planner)
- **Archetype-to-timeline mapping**: hardcoded if/elif in `plan_generator.py`. Should be LLM-planned using archetype contract + motion grammar as constraints.
- **Visual profile per target**: hardcoded switch in `getTargetVisualProfile()`. Should be derived from StylePack + target format.
- **Number of text cues**: derived from act structure. Should be planned based on intent density.

---

## 10. Iteration Loop Redesign

### Current loop
```
intent → compiler → plan → render_manifest → Manim → Remotion → judge → correction prompt → re-plan → re-render
```

### Problem
The loop is too coarse. If the judge fails on typography, the entire pipeline re-runs including Manim geometry, which is expensive and unlikely to change.

### Proposed loop with preview gate

```
intent
  → compiler
    → creative_plan (archetype, pacing, text)
      → artifact_plan (targets, style_pack, typography_system)
        ┌───────────────────────────────┐
        │ PREVIEW GATE (new)            │
        │ Remotion renders still preview│
        │ at 1/4 resolution             │
        │ Judge evaluates preview        │
        │ If fail: adjust plan, re-preview│
        │ Max 2 preview cycles          │
        └──────────────┬────────────────┘
                       │ approved plan
        → render_manifest
          → Manim (if needed for geometry)
            → Remotion (full render)
              ┌────────────────────────┐
              │ FINAL GATE             │
              │ Judge at full res      │
              │ If fail: targeted fix  │
              │ (typography only,      │
              │  color only, etc)      │
              │ Max 2 fix cycles       │
              └────────────────────────┘
                → approved output
```

The preview gate catches composition and typography problems *before* expensive full renders. Most quality issues are structural (wrong hierarchy, bad placement, too much text) and visible at low resolution.

---

## 11. Architecture Roadmap by Phase

### Phase 1: Foundation (Weeks 1-3)
**Goal:** Introduce the structural primitives without breaking existing flow.

1. Create `contracts/typography_systems/` with 2 systems (minimal, dense)
2. Create `contracts/still_families/` with 2 families (poster_minimal, editorial_portrait)
3. Create `contracts/style_packs/` with 2 packs (silent_luxury, kinetic_editorial)
4. Add `contracts/judge_profiles/` with premium_still and motion_frame profiles
5. Refactor `frame_scorer.py` to load judge profile based on render_mode
6. Add hard veto layer to `brand_validator.py`

### Phase 2: Typography Engine (Weeks 3-6)
**Goal:** Typography becomes a proper system.

1. Implement `ScaleSystem` computation in a new `engines/remotion/src/utils/typeScale.ts`
2. Refactor `NarrativeText.tsx` to consume ScaleSystem + TypographySystem contract
3. Add line-breaking intelligence (semantic breaks based on word boundaries)
4. Add baseline grid support
5. Implement optical alignment (cap-height based centering vs mathematical centering)
6. Add typography-specific judge dimensions

### Phase 3: Still Factory (Weeks 4-7)
**Goal:** Premium stills have their own composition pipeline.

1. Create `StillComposer` Remotion component separate from `CinematicNarrative`
2. Implement StillFamily loading in render_manifest.py
3. Support Manim-bypass for stills that don't need physics geometry
4. Add editorial layout system (compositional zones with named anchors)
5. Implement poster-specific judge profile
6. Add preview gate to still pipeline

### Phase 4: Motion Grammar (Weeks 6-9)
**Goal:** Motion becomes a language, not a bag of effects.

1. Create `contracts/motion_grammars/` with 2 grammars
2. Implement MotionPhrase/MotionSequence in Remotion runtime
3. Refactor `kael.py` to produce MotionSequence from grammar + archetype
4. Add transition system between acts
5. Integrate camera motion into motion grammar
6. Add motion-specific judge dimensions

### Phase 5: Creative Range (Weeks 8-12)
**Goal:** The system can produce visually varied output.

1. Implement StylePack selection in planner
2. Add 3 more style packs (warm, brutalist, organic)
3. Add color mode system beyond monochrome
4. Extend StillFamily library to 5 families
5. Implement preview gate for all artifact types
6. End-to-end validation: same intent → different style packs → varied but premium output

---

## 12. Highest Leverage Changes in the Next 30 Days

1. **Create the typography systems contract layer** (`contracts/typography_systems/`) with ScaleSystem parameters. This immediately makes type quality parameterizable instead of hardcoded.

2. **Split the judge into still vs motion profiles.** Two different prompt templates + different weight distributions. Takes 2-3 hours. Immediately improves judge accuracy.

3. **Add hard vetoes to the judge.** Programmatic checks that instantly reject broken frames before the LLM call. Saves time and catches obvious failures.

4. **Create 2 StillFamily contracts** and wire `render_manifest.py` to include them in the render manifest. Even before the Remotion component reads them, having the contracts formalizes what a premium still *is*.

5. **Add `poster_impact` as a judge dimension.** Even without the full redesign, adding one prompt line about "stop power" and "scroll-stopping quality" will improve still evaluation significantly.

---

## 13. Highest Leverage Changes in the Next 90 Days

1. **Build the StillComposer component** in Remotion that composes stills from scratch instead of extracting video frames. This is the single biggest quality unlock for the premium still pipeline.

2. **Implement the full typography engine** with ScaleSystem, optical alignment, and semantic line-breaking. This elevates every artifact type simultaneously.

3. **Build the StylePack system** and train the planner to select packs based on intent. This unlocks creative range — the system can produce silent luxury *and* kinetic editorial *and* data cinema.

4. **Implement the preview gate.** Catch composition problems before expensive renders. This transforms iteration speed.

5. **Implement MotionPhrase/MotionSequence** in the Remotion runtime. This turns motion from "spring presets" into authored choreography.

---

## 14. Risks, Failure Modes, and Anti-Patterns

### Risk: Overparameterization
More contracts ≠ better output. If the planner has 200 parameters to choose, it will choose badly. **Mitigation:** StylePacks bundle parameters into curated, tested combinations. The planner selects a pack, not individual parameters.

### Risk: Judge inflation
Vision LLMs tend toward generous scoring. A system that always passes is useless. **Mitigation:** Hard vetoes that cannot be scored around. Regular calibration by human review of "borderline pass" frames.

### Risk: Divergence between plan and render
The richer the plan language, the more ways it can be misinterpreted by the render engine. **Mitigation:** The render manifest is a strict typed contract. Anything not in the manifest is not rendered. The planner cannot hallucinate capabilities.

### Risk: Premature optimization of the wrong aesthetic
Building deeply for "silent luxury" and then struggling to adapt for "data cinema". **Mitigation:** The contract/system architecture is *parameterized*, not *specialized*. Every system has knobs, not flavors.

### Risk: LLM dependency for core quality
If the judge requires an LLM call for every quality decision, the system is slow and fragile. **Mitigation:** The two-pass architecture. Pass 1 (programmatic) catches 60% of issues in <100ms. Pass 2 (LLM) handles nuance only when needed.

### Anti-pattern: "One more feature" syndrome
The temptation to add effects (glow, 3D, particles) before the fundamentals are rock-solid. **Rule:** No new visual effects until typography, composition, and judging are at the target quality level. Effects mask weak fundamentals.

### Anti-pattern: Generic design tokens
Tokens like `accent_intensity: 0.5` are meaningless without context. Every token must specify *what it controls visually* and *what range is valid*.

---

## 15. What Must Remain Stable While Scaling Quality

1. **The render manifest as the compilation target.** Every enhancement must flow through the render manifest. No side-channel data from planner to renderer.

2. **YAML contracts as the source of truth.** No design decisions hardcoded in Python or TypeScript. If it's a design choice, it's in a contract.

3. **The three-act narrative structure.** Genesis/turbulence/resolution is a proven creative framework. Enhance it (add sub-beats, breath points, transitions) but don't replace it.

4. **The Manim/Remotion engine split.** Manim for physics, Remotion for typography and composition. Don't blur this boundary.

5. **The `aiox.py` CLI entry point and the `create` command contract.** Users should not need to change their workflow to get better output.

6. **The agent persona architecture** (Aria, Kael, Zara, Dara, Uma). These are the right abstractions. Enhance what they produce (richer PacingProfiles, TypographySystems, etc.) but keep the persona model.

7. **The quality loop (render → judge → correct → re-render).** This is the system's core intelligence mechanism. Make it faster and smarter, but never remove it.

8. **Backward compatibility with existing briefings.** Old briefings should produce *better* output through new defaults, not *broken* output through missing fields.
