import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, getInputProps, staticFile } from 'remotion';
import { NarrativeText } from '../components/NarrativeText';
import { Theme } from '../utils/theme';
import { parseRenderManifest, type PhysicsState, type RenderManifest } from '../types/renderManifest';

export const CinematicNarrative: React.FC = () => {
    const rawInput = getInputProps() as { renderManifest?: unknown } | undefined;
    const fallbackManifest: RenderManifest = {
        target: 'short_cinematic_vertical',
        targetId: 'short_cinematic_vertical',
        targetKind: 'video',
    };
    const renderManifest = rawInput?.renderManifest
        ? parseRenderManifest(rawInput.renderManifest)
        : fallbackManifest;
    const physicsState = (renderManifest.physics_state ?? {}) as PhysicsState;
    const externalVelocity = Number(physicsState.normalized_velocity ?? 0);

    return (
        // O fundo da composição puxa a cor exata do token bridge ativo.
        <AbsoluteFill style={{ backgroundColor: Theme.colors.background }}>
            
            {/* CAMADA 1: Geometria (O motor do Manim) */}
            <AbsoluteFill>
                <OffthreadVideo 
                    src={staticFile("manim_base.mp4")} 
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }} 
                />
            </AbsoluteFill>

            {/* CAMADA 2: Narrativa e Tipografia (O motor do React) */}
            {/* Aos 1 segundo (frame 60), o título entra com física de mola */}
            <Sequence from={60} durationInFrames={120}>
                <NarrativeText text="AIOX v4.0" externalVelocity={externalVelocity} />
            </Sequence>

            {/* Aos 3.5 segundos (frame 210), a tagline principal */}
            <Sequence from={210} durationInFrames={150}>
                <NarrativeText text="Invisible Architecture" externalVelocity={externalVelocity} />
            </Sequence>
            
        </AbsoluteFill>
    );
};
