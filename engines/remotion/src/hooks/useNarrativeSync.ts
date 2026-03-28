import { useVideoConfig, interpolate, spring } from 'remotion';
import { v4 } from '../theme';
import events from '../../../../assets/brand/timing_events.json';

export const useNarrativeSync = (frame: number) => {
    const { fps } = useVideoConfig();
    const acts = v4.narrative.acts || [];

    // Helper to parse time strings like "5s" to numbers
    const parseTime = (time: string | number) => {
        if (typeof time === 'number') return time;
        return parseFloat(time.replace('s', ''));
    };

    // Find active text elements for the current frame
    const activeTexts = acts.flatMap((act: any) => {
        if (!act.text) return [];
        return act.text.filter((t: any) => {
            const timeInSeconds = parseTime(t.at);
            const startFrame = timeInSeconds * fps;
            const endFrame = (timeInSeconds + 2.5) * fps; // 2.5s duration
            return frame >= startFrame && frame < endFrame;
        }).map((t: any) => ({
            ...t,
            progress: spring({
                frame: frame - (parseTime(t.at) * fps),
                fps,
                config: v4.motion.physics.presets.gentle_birth
            })
        }));
    });

    const inversionEvent = events.find(e => e.type === 'inversion');
    const isInverted = inversionEvent ? (frame >= (inversionEvent.timestamp * fps)) : false;

    return {
        activeTexts,
        isInverted,
        v4
    };
};
