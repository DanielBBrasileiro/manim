import React from 'react';
import { AbsoluteFill, OffthreadVideo, Sequence, staticFile } from 'remotion';
import { NarrativeText } from '../components/NarrativeText';
import { PHYSICS_STATE } from '../generated/physics_state';
import { Theme } from '../utils/theme';

export const CinematicNarrative: React.FC = () => {
    // dominantVelocity is written by physics_mixin.py after EntropyDemo runs.
    // Falls back to 0.5 (neutral) when the generated file has not been overwritten.
    const externalVelocity = PHYSICS_STATE.dominantVelocity;

    return (
        <AbsoluteFill style={{ backgroundColor: Theme.colors.background }}>

            {/* CAMADA 1: Geometria (O motor do Manim) */}
            <AbsoluteFill>
                <OffthreadVideo
                    src={staticFile("manim_base.mp4")}
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
            </AbsoluteFill>

            {/* CAMADA 2: Narrativa — Y-offset scaled by real pymunk velocity */}
            <Sequence from={60} durationInFrames={120}>
                <NarrativeText text="AIOX v4.0" externalVelocity={externalVelocity} />
            </Sequence>

            <Sequence from={210} durationInFrames={150}>
                <NarrativeText text="Invisible Architecture" externalVelocity={externalVelocity} />
            </Sequence>

        </AbsoluteFill>
    );
};
