// SSoT: all brand values come from the token bridge (brand.py → aiox_tokens.ts).
// Do NOT import assets/brand/theme.json here — that path is a competing bypass.
import { AIOX_TOKENS } from '../generated/aiox_tokens';

const dark = AIOX_TOKENS.brand.color_states.dark;
const accent = AIOX_TOKENS.brand.color_states.accent as { color: string };

export const Theme = {
    colors: {
        background: dark.background,
        textPrimary: (dark as { text_primary?: string }).text_primary ?? dark.foreground,
        textSecondary: (dark as { text_secondary?: string }).text_secondary ?? dark.foreground,
        accent: accent.color,
    },
    materials: AIOX_TOKENS.brand.materials,
    identity: AIOX_TOKENS.brand.identity,
} as const;
