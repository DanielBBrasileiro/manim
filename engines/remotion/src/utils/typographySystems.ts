export type TypographyAlignment = 'optical_left' | 'mathematical_center' | 'flush_right' | 'justified';
export type TypographyBreakStrategy = 'semantic' | 'balanced' | 'none';
export type TypographyDensity = 'light' | 'medium' | 'dense';

export type TypographyScaleConfig = {
	base_px: number;
	ratio: number;
	display_step: number;
	title_step: number;
	body_step: number;
	caption_step: number;
};

export type TypographySystemContract = {
	id: string;
	description?: string;
	scale: TypographyScaleConfig;
	density: TypographyDensity;
	max_words_per_block: number;
	measure_chars: number;
	tracking_at_display: string;
	tracking_at_body: string;
	leading_display: number;
	leading_body: number;
	break_strategy: TypographyBreakStrategy;
	alignment_default: TypographyAlignment;
	baseline_unit?: number;
};

const TYPOGRAPHY_SYSTEMS: Record<string, TypographySystemContract> = {
	editorial_minimal: {
		id: 'editorial_minimal',
		description: 'Apple Keynote inspired. Maximum restraint.',
		scale: {
			base_px: 18,
			ratio: 1.618,
			display_step: 5,
			title_step: 3,
			body_step: 1,
			caption_step: 0,
		},
		density: 'light',
		max_words_per_block: 3,
		measure_chars: 20,
		tracking_at_display: '-0.06em',
		tracking_at_body: '-0.02em',
		leading_display: 0.88,
		leading_body: 1.35,
		break_strategy: 'semantic',
		alignment_default: 'optical_left',
		baseline_unit: 8,
	},
	editorial_dense: {
		id: 'editorial_dense',
		description: 'Stripe Sessions inspired. Information-rich but ordered.',
		scale: {
			base_px: 16,
			ratio: 1.25,
			display_step: 4,
			title_step: 3,
			body_step: 1,
			caption_step: 0,
		},
		density: 'medium',
		max_words_per_block: 8,
		measure_chars: 45,
		tracking_at_display: '-0.04em',
		tracking_at_body: '-0.01em',
		leading_display: 1.05,
		leading_body: 1.5,
		break_strategy: 'balanced',
		alignment_default: 'mathematical_center',
		baseline_unit: 8,
	},
};

export const getTypographySystem = (
	input?: string | Partial<TypographySystemContract> | null,
): TypographySystemContract | null => {
	if (!input) {
		return null;
	}

	if (typeof input === 'string') {
		return TYPOGRAPHY_SYSTEMS[input] ?? null;
	}

	const base = input.id ? TYPOGRAPHY_SYSTEMS[input.id] : null;
	if (!base) {
		return null;
	}

	return {
		...base,
		...input,
		scale: {
			...base.scale,
			...(input.scale ?? {}),
		},
	};
};

export const listTypographySystems = (): string[] => Object.keys(TYPOGRAPHY_SYSTEMS);
