// Bridge: brand, motion e layout vêm do pipeline SSoT (brand.py → aiox_tokens.ts).
// Typography, narrative e camera são defaults estruturais estáticos — não gerenciados por brand.py.
import { AIOX_TOKENS } from './generated/aiox_tokens';

export const tokens = {
  v4_meta: {
    engine_version: "4.0",
    philosophy: "The Invisible Architecture",
    briefing_active: true
  },
  brand: AIOX_TOKENS.brand,
  motion: AIOX_TOKENS.motion,
  layout: AIOX_TOKENS.layout,
  narrative_rules: {
    structure: {
      default_arc: "three_act",
      acts: {
        genesis: {
          duration_ratio: 0.25,
          energy: [0.0, 0.3],
          emotion: "curiosity",
          rules: [
            "A single visual element is born",
            "Textual silence in the first 2 seconds",
            "Slow and organic movement (damping > 20)"
          ]
        },
        turbulence: {
          duration_ratio: 0.45,
          energy: [0.3, 1.0],
          emotion: "tension",
          rules: [
            "Visual multiplication: containers split, lines cross",
            "Increasing noise and chaos on the main curve",
            "Climax with color inversion or scale drop",
            "Text appears as narration, not as a label"
          ]
        },
        resolution: {
          duration_ratio: 0.3,
          energy: [1.0, 0.6],
          emotion: "mastery",
          rules: [
            "Chaos reorganizes into higher order",
            "Final curve higher than the original",
            "One word. Just one. As a signature",
            "Subtle branding in the last second"
          ]
        }
      }
    },
    pacing: {
      text_minimum_gap: "1.5s",
      max_text_words_per_screen: 5,
      silence_ratio: 0.3
    },
    emotional_palette: {
      curiosity: { motion: "slow_organic", space: "generous_negative" },
      tension: { motion: "fast_chaotic", space: "compressed_dense" },
      mastery: { motion: "settled_confident", space: "balanced_elegant" }
    }
  },
  narrative: {
    theme: "Elegance in Scalability",
    acts: [
      {
        name: "genesis",
        time: "0s → 4s",
        emotion: "curiosity",
        description: "A single point of origin.",
        visual_primitives: ["curve:sigmoid"],
        text: null
      },
      {
        name: "turbulence",
        time: "4s → 10s",
        emotion: "tension",
        description: "Complexity emerges.",
        visual_primitives: ["noise", "split"],
        text: [
          { at: "5s", content: "when systems", position: "top_zone", weight: 300 },
          { at: "7s", content: "reach the limit", position: "bottom_zone", weight: 300 },
          { at: "9s", content: "we invent silence.", position: "center", weight: 500, color: "inverted" }
        ]
      },
      {
        name: "resolution",
        time: "10s → 15s",
        emotion: "mastery",
        description: "Clarity attained.",
        visual_primitives: ["resolve"],
        text: [
          { at: "12s", content: "AIOX v4.0", position: "top_zone", weight: 500, size: "2.5rem" }
        ]
      }
    ]
  },
  typography: {
    fonts: {
      narrative: {
        family: "PP Neue Montreal, Inter, Helvetica Neue, sans-serif",
        weights: { whisper: 300, statement: 500 }
      },
      brand: {
        family: "Cal Sans",
        weight: 600,
        use: "Only for final resolve logo"
      }
    },
    rules: {
      sizing: {
        vertical_9_16: {
          narrative_text: "clamp(1.5rem, 4vw, 2.5rem)",
          brand_text: "0.875rem"
        },
        wide_16_9: {
          narrative_text: "clamp(1.2rem, 3vw, 2rem)",
          brand_text: "0.75rem"
        }
      },
      behavior: {
        entrance: "fade_up_8px",
        exit: "fade_down_4px",
        sync_mode: "beat_aligned"
      },
      anti_patterns: [
        "NEVER use text-transform: uppercase in narrative texts",
        "NEVER use font-weight > 500 for body text",
        "NEVER put text inside containers (boxes/badges)",
        "NEVER use more than 2 font sizes per frame"
      ],
      positioning: {
        vertical_rule: "Narrative text stays in 2 zones: top_zone (15% to 30% from top) or bottom_zone (70% to 85% from bottom). NEVER in the vertical center (reserved for climax).\n"
      }
    }
  },
  camera: {
    default_behavior: "observational",
    movements: {
      static_breathe: {
        description: "Camera static, but with subtle breathing micro-movement",
        scale_oscillation: 0.002,
        period: "4s",
        use_for: ["genesis", "resolution"]
      },
      track_subject: {
        description: "Camera follows the main element smoothly",
        spring: { stiffness: 40, damping: 25 },
        use_for: ["turbulence"]
      },
      dramatic_zoom: {
        description: "Fast zoom for climax",
        spring: { stiffness: 200, damping: 8 },
        use_for: ["color_inversion", "final_resolve"]
      }
    },
    container_choreography: {
      split_horizontal: {
        description: "Container splits into 2 panels side by side",
        animation: "center_expands_to_two",
        spring: { stiffness: 100, damping: 16 }
      },
      split_triple: {
        description: "Container splits into 3 panels",
        animation: "sequential_division"
      },
      rotate: {
        max_angle: 15,
        spring: { stiffness: 80, damping: 20 }
      },
      boundary_break: {
        description: "Visual element exceeds container borders",
        overflow: "visible",
        effect: "maximum narrative tension"
      }
    }
  },
  meta: {
    title: "The Invisible Architecture",
    format: "vertical_9_16",
    duration: "15s",
    fps: 60,
    template: "cinematic_narrative"
  }
};

export const v4 = tokens;
export const theme = v4;
