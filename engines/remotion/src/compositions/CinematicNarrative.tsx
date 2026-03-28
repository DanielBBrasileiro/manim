import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from 'remotion';
import { NarrativeText } from '../components/NarrativeText';
import { Theme } from '../utils/theme';

export const CinematicNarrative: React.FC = () => {
    return (
        // O fundo da composição puxa a cor exata do theme.json
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
                <NarrativeText text="AIOX v4.0" />
            </Sequence>

            {/* Aos 3.5 segundos (frame 210), a tagline principal */}
            <Sequence from={210} durationInFrames={150}>
                <NarrativeText text="Invisible Architecture" />
            </Sequence>
            
        </AbsoluteFill>
    );
};
