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
 */
export const useAioxSpring = (presetName: string = "silent_luxury_fluid", overrideConfig?: Partial<SpringConfig>): Transition => {
    const { fps } = useVideoConfig();

    return useMemo(() => {
        // Read strictly from the Governance pipeline (Single Source of Truth)
        const motionContracts = AIOX_TOKENS.motion as any;
        const presets: Record<string, SpringConfig> = motionContracts?.timing_standards?.presets || {};
        
        let baseConfig: SpringConfig = presets[presetName] || {
            stiffness: 100, damping: 20, mass: 1, initial_velocity: 0
        };

        const merged = { ...baseConfig, ...overrideConfig };
        
        // Translating the raw metrics to motion/react Transition spec.
        return {
            type: "spring",
            stiffness: merged.stiffness,
            damping: merged.damping,
            mass: merged.mass,
            // Framer motion uses velocity unit format of px/sec. 
            // We scale the Manim (which operates on [-7, 7] abstract coordinates)
            // assuming a rough multiplier based on standard screen mapping.
            velocity: merged.initial_velocity ? merged.initial_velocity * 100 : 0,
            
            // Critical for deterministic layout morphing over FFMPEG context
            bounce: 0, // Enforce strict no-bounce defaults if not mapped differently 
            restDelta: 0.001 // High precision stopping point for strict convergence
        };
    }, [presetName, overrideConfig, fps]);
};
