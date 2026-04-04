import React, { useLayoutEffect } from 'react';
import { AIOX_TOKENS } from '../generated/aiox_tokens';

/**
 * TokenInjector
 * 
 * Ensures the generated 13-step HCT color array and primary governance tokens
 * are pushed into the Document Object Model CSS Variables (`--md-sys-color-*`).
 * Because Remotion's React runtime executes inside a headless Chromium, we use 
 * native DOM Style insertions for zero-overhead blending over thousands of frames.
 */
export const TokenInjector: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    // useLayoutEffect guarantees these execute before browser paint
    useLayoutEffect(() => {
        const root = document.documentElement;
        const { brand } = AIOX_TOKENS;
        if (!brand || !brand.colors) return;

        // The python AIOX CLI ensures standard MD3 tokens are generated in the brand file
        const colors = brand.colors;
        if (colors.primary) root.style.setProperty('--md-sys-color-primary', colors.primary);
        if (colors.on_primary) root.style.setProperty('--md-sys-color-on-primary', colors.on_primary);
        if (colors.surface) root.style.setProperty('--md-sys-color-surface', colors.surface);
        if (colors.on_surface) root.style.setProperty('--md-sys-color-on-surface', colors.on_surface);
        if (colors.surface_variant) root.style.setProperty('--md-sys-color-surface-variant', colors.surface_variant);
        if (colors.outline) root.style.setProperty('--md-sys-color-outline', colors.outline);

        // Inject the full 13-step M3 HCT Palette
        if (colors.tones) {
            Object.entries(colors.tones).forEach(([key, hexValue]) => {
                // key looks like "tone_40", map to "--md-sys-color-primary-40"
                const step = key.split('_')[1];
                root.style.setProperty(`--md-sys-color-primary-${step}`, hexValue as string);
            });
        }
    }, []);

    return <>{children}</>;
};
