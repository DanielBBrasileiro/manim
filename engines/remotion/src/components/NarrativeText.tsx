import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { Theme } from '../utils/theme';

export const NarrativeText: React.FC<{ text: string, delay?: number }> = ({ text, delay = 0 }) => {
    const frame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // Física de mola (Spring) para uma entrada cinematográfica e suave
    const entrance = spring({
        fps,
        frame: frame - delay,
        config: { damping: 14, mass: 0.8 }, // Valores ideais para Motion Design premium
    });

    const opacity = interpolate(frame - delay, [0, 15], [0, 1], {
        extrapolateRight: 'clamp',
        extrapolateLeft: 'clamp',
    });

    // Calcula o movimento de baixo para cima
    const translateY = interpolate(entrance, [0, 1], [40, 0]);

    return (
        <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center' }}>
            <h1 style={{
                // Idealmente, a fonte viria do theme.json, usando system fonts para ser clean
                fontFamily: '-apple-system, BlinkMacSystemFont, "Inter", sans-serif',
                fontSize: '80px',
                fontWeight: 600,
                letterSpacing: '-0.04em',
                color: Theme.colors.textPrimary, // Lendo a cor DIRETAMENTE do contrato!
                opacity: opacity,
                transform: `translateY(${translateY}px)`,
                margin: 0,
            }}>
                {text}
            </h1>
        </AbsoluteFill>
    );
};
