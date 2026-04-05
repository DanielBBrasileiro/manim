// ⚠️ GERADO AUTOMATICAMENTE VIA core/cli/brand.py - NÃO EDITE
// Pipeline de Governança de Design Física AIOX
import type { AioxTokensShape } from '../types/tokens';

export const AIOX_TOKENS = {
  layout: {
  "window_size_classes": {
    "COMPACT": {
      "max_width": 599,
      "base_gap": "16px",
      "base_padding": "24px",
      "edge_breathing": "24px",
      "grid_columns": 4,
      "grid_margin": "16px"
    },
    "MEDIUM": {
      "max_width": 839,
      "base_gap": "24px",
      "base_padding": "32px",
      "edge_breathing": "48px",
      "grid_columns": 8,
      "grid_margin": "24px"
    },
    "EXPANDED": {
      "max_width": 10000,
      "base_gap": "32px",
      "base_padding": "48px",
      "edge_breathing": "64px",
      "grid_columns": 12,
      "grid_margin": "24px"
    }
  },
  "formats": {
    "vertical_9_16": {
      "width": 1080,
      "height": 1920,
      "safe_zone": 0.08,
      "text_zones": {
        "top": {
          "y": "15%",
          "height": "15%"
        },
        "bottom": {
          "y": "70%",
          "height": "15%"
        },
        "center": {
          "y": "42%",
          "height": "16%"
        }
      }
    },
    "wide_16_9": {
      "width": 1920,
      "height": 1080,
      "safe_zone": 0.06
    },
    "square_1_1": {
      "width": 1080,
      "height": 1080,
      "safe_zone": 0.1
    },
    "instagram_reel": {
      "width": 1080,
      "height": 1920,
      "fps": 30,
      "max_duration": 90,
      "safe_zone": 0.1,
      "alias": "vertical_9_16"
    },
    "instagram_post": {
      "width": 1080,
      "height": 1080,
      "fps": null,
      "safe_zone": 0.1,
      "alias": "square_1_1"
    },
    "instagram_story": {
      "width": 1080,
      "height": 1920,
      "fps": 30,
      "max_duration": 15,
      "safe_zone": 0.12,
      "alias": "vertical_9_16"
    },
    "instagram_carousel": {
      "width": 1080,
      "height": 1080,
      "fps": null,
      "max_frames": 10,
      "safe_zone": 0.1,
      "alias": "square_1_1"
    },
    "tiktok": {
      "width": 1080,
      "height": 1920,
      "fps": 30,
      "max_duration": 600,
      "safe_zone": 0.14,
      "alias": "vertical_9_16"
    },
    "linkedin_video": {
      "width": 1920,
      "height": 1080,
      "fps": 30,
      "max_duration": 600,
      "safe_zone": 0.06,
      "alias": "wide_16_9"
    },
    "linkedin_post": {
      "width": 1200,
      "height": 627,
      "fps": null,
      "safe_zone": 0.08
    },
    "linkedin_square": {
      "width": 1080,
      "height": 1350,
      "fps": null,
      "safe_zone": 0.1
    },
    "twitter_video": {
      "width": 1280,
      "height": 720,
      "fps": 30,
      "max_duration": 140,
      "safe_zone": 0.06
    },
    "twitter_thumbnail": {
      "width": 1200,
      "height": 675,
      "fps": null,
      "safe_zone": 0.06
    },
    "youtube_shorts": {
      "width": 1080,
      "height": 1920,
      "fps": 60,
      "max_duration": 60,
      "safe_zone": 0.08,
      "alias": "vertical_9_16"
    },
    "youtube_thumbnail": {
      "width": 1280,
      "height": 720,
      "fps": null,
      "safe_zone": 0.06
    }
  },
  "default_output_target": "short_cinematic_vertical",
  "output_targets": {
    "short_cinematic_vertical": {
      "format": "vertical_9_16",
      "alias": "instagram_reel",
      "channel": "instagram_reel",
      "purpose": "short_form_social",
      "priority": 100,
      "default": true,
      "render_mode": "video",
      "composition": "short-cinematic-vertical",
      "legacy_composition": "CinematicNarrative-v4",
      "legacy_aliases": [
        "vertical_social",
        "short_cinematic"
      ],
      "label": "Short Cinematic Vertical",
      "fps": 60,
      "safe_zone": 0.1,
      "preferred_channels": [
        "instagram_reel",
        "tiktok",
        "youtube_shorts",
        "instagram_story"
      ]
    },
    "linkedin_feed_4_5": {
      "format": "linkedin_square",
      "alias": "linkedin_square",
      "channel": "linkedin_feed",
      "purpose": "premium_still",
      "priority": 80,
      "render_mode": "still",
      "composition": "linkedin-feed-4-5",
      "legacy_composition": "LinkedInStill-v4",
      "legacy_aliases": [
        "square_social",
        "linkedin_still",
        "linkedin_post"
      ],
      "label": "LinkedIn Feed 4:5",
      "fps": 30,
      "safe_zone": 0.1,
      "preferred_channels": [
        "linkedin_feed",
        "linkedin_square"
      ]
    },
    "linkedin_carousel_square": {
      "format": "square_1_1",
      "alias": "instagram_carousel",
      "channel": "linkedin_carousel",
      "purpose": "narrative_carousel",
      "priority": 75,
      "render_mode": "carousel",
      "composition": "linkedin-carousel-square",
      "legacy_composition": "CarouselSlide-v4",
      "legacy_aliases": [
        "instagram_carousel",
        "carousel_slide"
      ],
      "label": "LinkedIn Carousel Square",
      "fps": 30,
      "safe_zone": 0.1,
      "min_slides": 5,
      "max_slides": 9,
      "preferred_channels": [
        "linkedin_carousel",
        "instagram_carousel"
      ]
    },
    "youtube_essay_16_9": {
      "format": "wide_16_9",
      "alias": "linkedin_video",
      "channel": "youtube_video",
      "purpose": "visual_essay",
      "priority": 70,
      "render_mode": "video",
      "composition": "youtube-essay-16-9",
      "legacy_composition": "YouTubeEssay-v4",
      "legacy_aliases": [
        "wide_showcase",
        "youtube_essay"
      ],
      "label": "YouTube Essay 16:9",
      "fps": 30,
      "safe_zone": 0.06,
      "preferred_channels": [
        "youtube_video",
        "linkedin_video",
        "twitter_video"
      ]
    },
    "youtube_thumbnail_16_9": {
      "format": "youtube_thumbnail",
      "alias": "youtube_thumbnail",
      "channel": "youtube_thumbnail",
      "purpose": "thumbnail",
      "priority": 65,
      "render_mode": "still",
      "composition": "youtube-thumbnail-16-9",
      "legacy_composition": "Thumbnail-v4",
      "legacy_aliases": [
        "thumbnail"
      ],
      "label": "YouTube Thumbnail 16:9",
      "fps": 30,
      "safe_zone": 0.08,
      "preferred_channels": [
        "youtube_thumbnail"
      ]
    },
    "loop_gif_square": {
      "format": "square_1_1",
      "alias": "instagram_post",
      "channel": "loop_gif",
      "purpose": "loop_gif",
      "priority": 60,
      "render_mode": "video",
      "native_support": false,
      "output_ext": ".gif",
      "composition": "linkedin-carousel-square",
      "legacy_aliases": [
        "gif_square",
        "motion_loop_square"
      ],
      "label": "Loop GIF Square",
      "fps": 24,
      "safe_zone": 0.1,
      "preferred_channels": [
        "linkedin_feed",
        "instagram_post"
      ]
    },
    "loop_gif_vertical": {
      "format": "vertical_9_16",
      "alias": "instagram_reel",
      "channel": "loop_gif",
      "purpose": "loop_gif",
      "priority": 58,
      "render_mode": "video",
      "native_support": false,
      "output_ext": ".gif",
      "composition": "short-cinematic-vertical",
      "legacy_aliases": [
        "gif_vertical",
        "motion_loop_vertical"
      ],
      "label": "Loop GIF Vertical",
      "fps": 24,
      "safe_zone": 0.1,
      "preferred_channels": [
        "instagram_story",
        "instagram_reel"
      ]
    },
    "motion_preview_webm": {
      "format": "wide_16_9",
      "alias": "twitter_video",
      "channel": "motion_preview",
      "purpose": "motion_preview",
      "priority": 55,
      "render_mode": "video",
      "native_support": false,
      "output_ext": ".webm",
      "composition": "youtube-essay-16-9",
      "legacy_aliases": [
        "preview_webm",
        "motion_preview"
      ],
      "label": "Motion Preview WebM",
      "fps": 24,
      "safe_zone": 0.06,
      "preferred_channels": [
        "twitter_video",
        "linkedin_video"
      ]
    }
  },
  "composition": {
    "rule_of_thirds": true,
    "center_bias": 0.6,
    "edge_breathing": "64px"
  }
},
  motion: {
  "physics": {
    "default_engine": "spring",
    "physics_enabled": false,
    "simulation_restitution": 0.2,
    "convergence_gravity_G": 1000.0
  },
  "timing_standards": {
    "durations": {
      "short": 200,
      "medium": 400,
      "long": 700
    },
    "easings": {
      "emphasized": "cubic-bezier(0.2, 0.0, 0, 1.0)",
      "standard": "cubic-bezier(0.2, 0.0, 0, 1.0)"
    },
    "presets": {
      "gentle_birth": {
        "stiffness": 40,
        "damping": 26,
        "mass": 1.2
      },
      "tension_build": {
        "stiffness": 160,
        "damping": 10,
        "mass": 0.8
      },
      "elegant_settle": {
        "stiffness": 80,
        "damping": 22,
        "mass": 1.0
      },
      "hard_cut": {
        "duration": 0
      },
      "premium_editorial": {
        "type": "fluid_spring",
        "stiffness": 300,
        "damping": 28,
        "mass": 1.0,
        "initial_velocity": 0.0
      },
      "silent_luxury_fluid": {
        "type": "fluid_spring",
        "stiffness": 80,
        "damping": 20,
        "mass": 1.0,
        "initial_velocity": 0.0
      }
    },
    "curve_behaviors": {
      "sigmoid_growth": {
        "function": "1 / (1 + exp(-k*(x-x0)))",
        "params": {
          "k": 5,
          "x0": 0.5
        }
      },
      "noise_oscillation": {
        "base": "sigmoid_growth",
        "noise_type": "perlin",
        "amplitude_curve": "linear_ramp 0\u21920.4"
      },
      "chaotic_to_resolved": {
        "behavior": "noise decays exponentially until smooth",
        "resolve_spring": "elegant_settle"
      }
    }
  },
  "easing": {
    "default": "cubic_bezier(0.16, 1, 0.3, 1)",
    "dramatic": "cubic_bezier(0.87, 0, 0.13, 1)"
  },
  "interpolation": {
    "standard": "smooth",
    "never_use": [
      "linear",
      "there_and_back"
    ]
  }
},
  brand: {
  "identity": {
    "name": "AIOX",
    "tagline": "The Invisible Architecture"
  },
  "color_states": {
    "dark": {
      "background": "#000000",
      "foreground": "#FFFFFF",
      "stroke": "rgba(255, 255, 255, 0.85)",
      "text_primary": "#FFFFFF",
      "text_secondary": "rgba(255, 255, 255, 0.55)"
    },
    "inverted": {
      "background": "#FFFFFF",
      "foreground": "#000000",
      "stroke": "rgba(0, 0, 0, 0.85)",
      "text_primary": "#000000",
      "text_secondary": "rgba(0, 0, 0, 0.55)"
    },
    "accent": {
      "color": "#FF3366",
      "use": "Only for pulsing dot or momentary highlight",
      "max_screen_coverage": "2%"
    }
  },
  "materials": {
    "grain": 0.06,
    "stroke_width": {
      "primary": 1.5,
      "secondary": 0.5,
      "container": 0.8
    }
  },
  "anti_patterns": [
    "NEVER use gradients",
    "NEVER use shadows or glow",
    "NEVER use glassmorphism",
    "NEVER show tech logos (Python, Postgres, etc.)",
    "NEVER use serif fonts",
    "NEVER use text-transform: uppercase (except brand name)"
  ],
  "colors": {
    "primary": "#ffffff",
    "on_primary": "#1a1a1a",
    "surface": "#ffffff",
    "on_surface": "#1a1a1a",
    "surface_variant": "#e5e5e5",
    "outline": "#cccccc",
    "tones": {
      "tone_0": "#000000",
      "tone_10": "#484848",
      "tone_20": "#636363",
      "tone_25": "#707070",
      "tone_30": "#7e7e7e",
      "tone_40": "#999999",
      "tone_50": "#aaaaaa",
      "tone_60": "#bbbbbb",
      "tone_70": "#cccccc",
      "tone_80": "#dddddd",
      "tone_90": "#eeeeee",
      "tone_95": "#f6f6f6",
      "tone_100": "#ffffff"
    }
  }
},
  laws: {
  "min_negative_space": 0.4,
  "max_colors": 2,
  "typography": {
    "max_weights": 2,
    "forbidden": [
      "serif",
      "uppercase_prose"
    ]
  },
  "anti_patterns": [
    "no_gradients",
    "no_logos",
    "no_shadows"
  ]
}
} satisfies AioxTokensShape as const;
