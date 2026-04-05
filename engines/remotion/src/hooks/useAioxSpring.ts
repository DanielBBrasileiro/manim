import { useMemo } from 'react';
import type { Transition } from 'motion/react';
import { useVideoConfig } from 'remotion';
import { AIOX_TOKENS } from '../generated/aiox_tokens';

export interface SpringConfig {
    stiffness: number;
    damping: number;
    mass?: number;
    initial_velocity?: number; // v0 translated from Pymunk
}

/**
 * useAioxSpring
 * Translates offline Manim physical metrics into React determinist springs.
 *
 * @param presetName    - key in motion.yaml spring_presets
 * @param overrideConfig - partial overrides applied on top of the preset
 * @param externalVelocity - scalar velocity injected from physics_state.initial_velocity.magnitude
 *   in the render_manifest (written by PhysicsOrchestratorMixin.inject_velocity_into_manifest).
 *   Unit: Pymunk abstract coordinates/s. Scaled to px/s (×100) before passing to Framer Motion.
 *   When present this takes precedence over the preset's initial_velocity.
 */
export const useAioxSpring = (
    presetName: string = "silent_luxury_fluid",
    overrideConfig?: Partial<SpringConfig>,
    externalVelocity?: number,
): Transition => {
    const { fps } = useVideoConfig();

    return useMemo(() => {
        // Read strictly from the Governance pipeline (Single Source of Truth)
        const motionContracts = AIOX_TOKENS.motion as any;
        const presets: Record<string, SpringConfig> = motionContracts?.timing_standards?.presets || {};

        const baseConfig: SpringConfig = presets[presetName] || {
            stiffness: 100, damping: 20, mass: 1, initial_velocity: 0
        };

        const merged = { ...baseConfig, ...overrideConfig };

        // Velocity resolution priority:
        // 1. externalVelocity from Pymunk physics_state (wired handshake)
        // 2. preset/override initial_velocity (static contract default)
        // Framer Motion velocity unit = px/sec.
        // Pymunk operates on [-7, 7] abstract coords — multiply by 100 for screen mapping.
        const resolvedVelocity = externalVelocity !== undefined
            ? externalVelocity * 100
            : (merged.initial_velocity ? merged.initial_velocity * 100 : 0);

        return {
            type: "spring",
            stiffness: merged.stiffness,
            damping: merged.damping,
            mass: merged.mass,
            velocity: resolvedVelocity,
            // Critical for deterministic layout morphing over FFMPEG context
            bounce: 0,
            restDelta: 0.001,
        };
    }, [presetName, overrideConfig, externalVelocity, fps]);
};
