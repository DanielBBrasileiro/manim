import React, { useMemo, useEffect } from 'react';
import { motion, type HTMLMotionProps } from 'motion/react';
import { useAioxSpring, type SpringConfig } from '../hooks/useAioxSpring';

export interface StoryAtomProps extends HTMLMotionProps<"div"> {
    /** Override internal children */
    children?: React.ReactNode;

    /** Override style */
    style?: React.CSSProperties;

    /** 
     * Extremely important: if this layoutId matches another component generated in the future
     * (e.g. going from "Turbulence" to "Resolution" scene), Framer Motion will magically morph 
     * its position, width, height, and color across the Remotion canvas automatically.
     */
    layoutId?: string;
    
    /** Specific preset matching the motion.yaml spec */
    preset?: string;
    
    /** Toggle the deterministic presence exit drop. */
    withGravityExit?: boolean;

    /** External trigger for releasing manually simulated rigid bodies */
    onTeardownPhysics?: () => void;
}

/**
 * StoryAtom
 * The fundamental React Component wrapper powered by the Framer Motion Elite Interpolation engine.
 * Ensures the Remotion FFMPEG rendering happens entirely via CSS sub-pixel translations instead 
 * of layout reflows.
 */
export const StoryAtom: React.FC<StoryAtomProps> = ({
    children,
    layoutId,
    preset = "silent_luxury_fluid",
    withGravityExit = true,
    onTeardownPhysics,
    style,
    ...restProps
}) => {
    // Generate deterministic Spring configurations for the morph translation
    const springTransition = useAioxSpring(preset);

    // M4 optimization: Explicit GC and Engine teardown of physics memory chunks if bound
    useEffect(() => {
        return () => {
            if (onTeardownPhysics) onTeardownPhysics();
        };
    }, [onTeardownPhysics]);

    // Initial Mount animation pattern: Blur and Scale up 
    const initialAnim = useMemo(() => ({
        opacity: 0,
        scale: 0.9,
        filter: 'blur(10px)',
    }), []);

    // Idle layout standard
    const animateAnim = useMemo(() => ({
        opacity: 1,
        scale: 1,
        filter: 'blur(0px)',
    }), []);

    // Exit Unmount pattern: Drop downwards representing Mass gravity
    const exitAnim = useMemo(() => {
        if (!withGravityExit) return { opacity: 0 };
        return {
            opacity: 0,
            y: 30, // Drop
            filter: 'blur(5px)',
            transition: { ...springTransition, stiffness: springTransition.stiffness ? (springTransition.stiffness as number) * 0.8 : undefined } // Slight relax
        };
    }, [withGravityExit, springTransition]);

    return (
        <motion.div
            layoutId={layoutId}
            layout="position" // Optimize by only rendering transforms under the hood, not width/height reflows
            initial={initialAnim}
            animate={animateAnim}
            exit={exitAnim}
            transition={springTransition}
            style={{
                // GPU promotion: willChange elevates the layer, backfaceVisibility
                // prevents Safari/Chrome from flushing the composite layer on repaint.
                // translate3d is managed by Framer Motion internally via layout="position" —
                // do NOT add a raw transform here as it would override Framer's interpolation.
                willChange: "transform, opacity, filter",
                backfaceVisibility: "hidden",
                WebkitBackfaceVisibility: "hidden",
                ...style
            }}
            {...restProps}
        >
            {children}
        </motion.div>
    );
};
