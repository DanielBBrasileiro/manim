/**
 * stateLayers.ts
 * Generates transparent overlay colors equivalent to M3 physical state layers.
 * Since video rendering doesn't have real "hover" interaction, this allows narrative 
 * scripts to simulate User interaction states algorithmically.
 */

export type M3State = 'hover' | 'focus' | 'pressed' | 'dragged' | 'none';

export const getOpacityForState = (state: M3State): number => {
    switch(state) {
        case 'hover': return 0.08;
        case 'focus': return 0.12;
        case 'pressed': return 0.12;
        case 'dragged': return 0.16;
        default: return 0.0;
    }
};

export const applyStateLayer = (baseHexColor: string, state: M3State, isDark: boolean = false): string => {
    if (state === 'none') return baseHexColor;
    
    // In M3, the state layer is generally derived from the contrasting color (On-Surface / On-Primary)
    // For pure programmatic purposes without DOM inheritance, we tint with black or white.
    const layerColor = isDark ? '255, 255, 255' : '26, 26, 26';
    const opacity = getOpacityForState(state);
    
    return `color-mix(in srgb, rgba(${layerColor}, ${opacity}) ${opacity * 100}%, ${baseHexColor})`;
};
