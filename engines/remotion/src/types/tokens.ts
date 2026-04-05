/**
 * Canonical shape contract for AIOX_TOKENS.
 * brand.py enforces this via `satisfies AioxTokensShape` — any deviation
 * in the generated artifact breaks the TypeScript build immediately.
 */

export interface AioxMotionPhysics {
  default_engine: string;
  physics_enabled: boolean;
  simulation_restitution: number;
  convergence_gravity_G: number;
}

export interface AioxMotionSpringPreset {
  type?: string;
  stiffness: number;
  damping: number;
  mass: number;
  initial_velocity?: number;
  duration?: number;
}

export interface AioxTimingPresets {
  premium_editorial: AioxMotionSpringPreset;
  silent_luxury_fluid: AioxMotionSpringPreset;
  [key: string]: AioxMotionSpringPreset | unknown;
}

export interface AioxTimingStandards {
  durations: { short: number; medium: number; long: number };
  easings: Record<string, string>;
  presets: AioxTimingPresets;
  curve_behaviors?: Record<string, unknown>;
}

export interface AioxMotion {
  physics: AioxMotionPhysics;
  timing_standards: AioxTimingStandards;
  easing?: Record<string, string>;
  interpolation?: Record<string, unknown>;
}

export interface AioxColorState {
  background: string;
  foreground: string;
  text_primary?: string;
  text_secondary?: string;
  stroke?: string;
  [key: string]: unknown;
}

/** M3 tonal palette: keys are "tone_0" through "tone_100" (13 standard steps). */
export type AioxTonalPalette = Record<string, string>;

export interface AioxBrandColors {
  primary: string;
  on_primary: string;
  surface: string;
  on_surface: string;
  surface_variant: string;
  outline: string;
  /** Primary tonal palette — genuine OKLCH-generated M3 tones. */
  tones: AioxTonalPalette;
  /** Neutral palette for surface/background roles. */
  tones_neutral: AioxTonalPalette;
  /** Neutral variant palette for outlines and surface variants. */
  tones_neutral_variant: AioxTonalPalette;
}

export interface AioxBrand {
  color_states: {
    dark: AioxColorState;
    accent: { color: string; [key: string]: unknown };
    [key: string]: AioxColorState | { color: string; [key: string]: unknown } | unknown;
  };
  materials: Record<string, unknown>;
  identity: Record<string, unknown>;
  colors?: AioxBrandColors;
  [key: string]: unknown;
}

export interface AioxTokensShape {
  layout: Record<string, unknown>;
  motion: AioxMotion;
  brand: AioxBrand;
  laws?: Record<string, unknown>;
}
