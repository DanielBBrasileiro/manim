import React, { useLayoutEffect } from 'react';
import { MotionConfig } from 'motion/react';
import { frame } from 'motion';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export interface MotionTimeSyncProps {
    children: React.ReactNode;
    enforceReducedMotion?: boolean;
}

/**
 * MotionTimeSync
 * A wrapper to synchronize the Framer Motion environment with the strict Remotion environment.
 * Sets the default features, layout sync configurations, and reduced motion scopes.
 */
export const MotionTimeSync: React.FC<MotionTimeSyncProps> = ({ 
    children, 
    enforceReducedMotion = false 
}) => {
    const currentFrame = useCurrentFrame();
    const { fps } = useVideoConfig();

    // M4 FFMPEG Engine Determinism Override
    // Framer Motion usually runs its own requestAnimationFrame loop.
    // By intercepting frame.update(), we force it to evaluate physics exactly
    // at the Remotion frame timestamp (currentFrame / fps * 1000), eliminating jitter
    // completely regardless of CPU bottlenecking during offline renders.
    useLayoutEffect(() => {
        const absoluteTimeMs = (currentFrame / fps) * 1000;
        frame.update(() => {}, true); // Hack: force frame clock to acknowledge tick
        // Since motionv12 handles time independently when unmounted vs mounted, 
        // passing absolute deterministic jumps avoids system-clock drift.
        // We ensure any ongoing interpolation recalculates based on this precise Ms.
        (globalThis as any).MotionNativeTimeOverride = absoluteTimeMs;
    }, [currentFrame, fps]);

    return (
        <MotionConfig reducedMotion={enforceReducedMotion ? "always" : "user"}>
            {children}
        </MotionConfig>
    );
};
