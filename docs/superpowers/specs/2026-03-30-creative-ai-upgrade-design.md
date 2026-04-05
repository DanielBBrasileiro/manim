# Creative AI Upgrade — Design Spec
**Date:** 2026-03-30
**Status:** Approved
**Scope:** Replace keyword-based intent parsing with local LLM pipeline + continuous learning loop

---

## Problem

The current system has two compounding failures:

1. **Compreensão fraca** — `intent_parser.py` uses static keyword matching (lexicon dicts). It misses context, intent, and creative nuance.
2. **Execução inconsistente** — assets, effects, and composition don't compose correctly even when intent is partially understood.

---

## Solution Overview

A 4-layer architecture: local LLM understanding → validated asset planning → existing execution pipeline → continuous learning from approvals.

```
┌─────────────────────────────────────────┐
│  1. COMPREENSÃO                          │
│  Ollama → Qwen 2.5 14B (text)           │
│  Qwen2-VL 7B (vision, reference videos) │
└──────────────────┬──────────────────────┘
                   │ Scene Plan JSON
┌──────────────────▼──────────────────────┐
│  2. ASSET REGISTRY                       │
│  Validated inventory: primitives,        │
│  effects, brand tokens, archetypes       │
└──────────────────┬──────────────────────┘
                   │ Validated plan
┌──────────────────▼──────────────────────┐
│  3. EXECUÇÃO (unchanged)                 │
│  creative_compiler → graph_runtime       │
└──────────────────┬──────────────────────┘
                   │ Rendered video
┌──────────────────▼──────────────────────┐
│  4. FEEDBACK LOOP                        │
│  approve/reject → training pairs         │
│  mlx-lm LoRA fine-tune (periodic)        │
│  Qwen 7B fine-tuned replaces 14B         │
└─────────────────────────────────────────┘
```

---

## Component Designs

### 1. Scene Plan JSON (contract between LLM and compiler)

```json
{
  "archetype": "chaos_to_order",
  "duration": 12,
  "pacing": "cinematic",
  "scenes": [
    {
      "id": "intro",
      "duration": 3,
      "primitives": ["particle_system", "fbm_noise"],
      "params": { "density": "high", "entropy": 0.9 }
    },
    {
      "id": "transition",
      "duration": 5,
      "primitives": ["living_curve", "gravity_field"],
      "params": { "collapse_to": "center", "trail_length": 0.4 }
    }
  ],
  "assets": {
    "logo": "brand/logo_white.svg",
    "palette": "brand/tokens.json#dark_mode"
  },
  "effects": ["post_glitch_light", "grain_overlay"],
  "confidence": 0.87
}
```

**Confidence gate:** if `confidence < 0.7`, the system asks for confirmation before rendering. If `>= 0.7`, executes directly.

### 2. Asset Registry (`assets/registry.json`)

A live JSON inventory the LLM receives as context before planning. The LLM can only reference items in the registry — eliminates hallucinated effects/assets.

```json
{
  "primitives": ["particle_system", "living_curve", "physics_field", "fbm_noise", ...],
  "effects": ["post_glitch_light", "grain_overlay", "color_grade_cyber", ...],
  "brand": {
    "logos": ["brand/logo_white.svg", "brand/logo_dark.svg"],
    "palettes": ["dark_mode", "neon_accent", "minimal_light"],
    "fonts": ["brand/inter_bold.ttf"]
  },
  "archetypes": ["chaos_to_order", "emergence", "gravitational_collapse", "order_to_chaos"]
}
```

Adding a new effect to the project = updating the registry = LLM can immediately use it.

### 3. Vision Extractor (reference video pipeline)

User drops a reference video → system extracts keyframes via ffmpeg → Qwen2-VL analyzes the sequence and generates a Scene Plan JSON → user reviews/approves → saved as training data.

```
video.mp4 → ffmpeg keyframes → Qwen2-VL → Scene Plan JSON → user review → assets/training_data/
```

### 4. Feedback Store + Fine-tune

Every approved generation saves a training pair to `core/memory/training_pairs.jsonl`:

```json
{"prompt": "user prompt text", "completion": "{...scene plan json...}"}
```

When ~50 pairs are accumulated, run LoRA fine-tune via mlx-lm (Apple Silicon native, Metal GPU):

```bash
mlx_lm.lora \
  --model qwen2.5-7b-instruct \
  --data core/memory/training_pairs.jsonl \
  --iters 500 \
  --adapter-path core/memory/lora_adapter
```

The adapter (~50MB) loads on top of the base model. Over time, the fine-tuned 7B surpasses the generic 14B for this specific creative domain.

---

## File Changes

### Modified (surgical, interface-preserving)

| File | Change |
|---|---|
| `core/compiler/intent_parser.py` | Replace keyword matching with Ollama call; preserve `Intent` dataclass interface |
| `core/intelligence/ai_brain.py` | Add Ollama client; Anthropic API becomes optional fallback |
| `core/orchestrator.py` | Inject Asset Registry into compiler context before planning |

### New Files

| File | Purpose |
|---|---|
| `core/intelligence/ollama_client.py` | Ollama wrapper — structured output, timeout, graceful fallback to heuristics |
| `core/intelligence/scene_plan.py` | ScenePlan dataclass + JSON schema validation |
| `core/intelligence/vision_extractor.py` | Qwen2-VL pipeline for reference video analysis |
| `core/memory/feedback_store.py` | Persist approved (prompt → plan) pairs for fine-tuning |
| `assets/registry.json` | Live asset/effect/primitive inventory |

### Unchanged

- `core/compiler/creative_compiler.py`
- `core/runtime/graph_runtime.py`
- All agents (Aria, Kael, Zara, Dara, Uma)
- All rendering generators
- All primitives

---

## Setup

```bash
# One-time setup
brew install ollama
ollama pull qwen2.5:14b
ollama pull qwen2.5-vl:7b
pip install mlx-lm  # for future fine-tuning
```

---

## Error Handling

- If Ollama is not running → fall back to current keyword matching (no breakage)
- If LLM returns invalid JSON → retry once with stricter prompt → fall back to heuristics
- If `confidence < 0.7` → prompt user for confirmation before rendering
- If fine-tune adapter missing → use base model (adapter is additive, not required)

---

## Success Criteria

- Prompt `"quero algo que respire, logo emergindo da névoa, tom orgânico"` produces a correct Scene Plan without keyword matches for "breathe" or "fog"
- All effects in generated plans exist in `assets/registry.json` (zero hallucinations)
- After 50 approved pairs, fine-tuned 7B produces plans rated equal or better than 14B base by the user
- System runs entirely offline after initial model download
