import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Theme } from '../utils/theme';

interface NarrativeTextProps {
    text: string;
    delay?: number;
    /**
     * Normalised velocity scalar from real pymunk physics [0, 1].
     * Scales the entrance Y-offset so high-energy renders have a more
     * dramatic text entrance; low-energy renders enter more subtly.
     * Defaults to 0.5 (neutral mid-energy entrance).
     */
    externalVelocity?: number;
}

export const NarrativeText: React.FC<NarrativeTextProps> = ({
    text,
    delay = 0,
    externalVelocity = 0.5,
}) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    const entrance = spring({
        fps,
        frame: frame - delay,
        config: { damping: 14, mass: 0.8 },
    });

    const opacity = interpolate(frame - delay, [0, 15], [0, 1], {
        extrapolateRight: 'clamp',
        extrapolateLeft: 'clamp',
    });

    // Physics-driven entrance: higher velocity → more dramatic Y drop (20–60 px)
    const yOffset = 20 + externalVelocity * 40;
    const translateY = interpolate(entrance, [0, 1], [yOffset, 0]);

    return (
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
            <h1 style={{
                fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", sans-serif',
                fontSize: '80px',
                fontWeight: 600,
                letterSpacing: '-0.04em',
                color: Theme.colors.textPrimary,
                opacity,
                transform: `translateY(${translateY}px)`,
                margin: 0,
            }}>
                {text}
            </h1>
        </AbsoluteFill>
    );
};
