import {getStylePack} from './stillContracts';

export type ResolvedStylePackFields = {
	stylePackId: string;
	typographySystem: string;
	stillFamily: string;
	motionGrammar: string;
	colorMode: string;
	negativeSpaceTarget: number;
	accentIntensity: number;
	grain: number;
};

export type StylePackPalette = {
	background: string;
	field: string;
	accent: string;
	curve: string;
	rail: string;
};

const STYLE_PACK_TO_MOTION_GRAMMAR: Record<string, string> = {
	silent_luxury: 'cinematic_restrained',
	kinetic_editorial: 'kinetic_editorial',
};

const DEFAULT_FIELDS: ResolvedStylePackFields = {
	stylePackId: 'silent_luxury',
	typographySystem: 'editorial_minimal',
	stillFamily: 'poster_minimal',
	motionGrammar: 'cinematic_restrained',
	colorMode: 'monochrome_pure',
	negativeSpaceTarget: 0.65,
	accentIntensity: 0.1,
	grain: 0.04,
};

export const resolveStylePackFields = ({
	stylePackId,
	explicit,
}: {
	stylePackId?: string | null;
	explicit?: {
		typography_system?: string | null;
		still_family?: string | null;
		motion_grammar?: string | null;
		color_mode?: string | null;
		negative_space_target?: number | null;
		accent_intensity?: number | null;
		grain?: number | null;
	};
}): ResolvedStylePackFields => {
	const contract = getStylePack(stylePackId ?? DEFAULT_FIELDS.stylePackId);
	return {
		stylePackId: stylePackId ?? contract?.id ?? DEFAULT_FIELDS.stylePackId,
		typographySystem:
			explicit?.typography_system ?? contract?.typography_system ?? DEFAULT_FIELDS.typographySystem,
		stillFamily:
			explicit?.still_family ?? contract?.still_family ?? DEFAULT_FIELDS.stillFamily,
		motionGrammar:
			explicit?.motion_grammar ??
			(contract?.id ? STYLE_PACK_TO_MOTION_GRAMMAR[contract.id] : null) ??
			(stylePackId ? STYLE_PACK_TO_MOTION_GRAMMAR[stylePackId] : null) ??
			DEFAULT_FIELDS.motionGrammar,
		colorMode: explicit?.color_mode ?? contract?.color_mode ?? DEFAULT_FIELDS.colorMode,
		negativeSpaceTarget:
			explicit?.negative_space_target ?? contract?.negative_space_target ?? DEFAULT_FIELDS.negativeSpaceTarget,
		accentIntensity:
			explicit?.accent_intensity ?? contract?.accent_intensity ?? DEFAULT_FIELDS.accentIntensity,
		grain: explicit?.grain ?? contract?.grain ?? DEFAULT_FIELDS.grain,
	};
};

export const resolveStylePackPalette = (fields: ResolvedStylePackFields): StylePackPalette => {
	if (fields.colorMode === 'monochrome_warm') {
		return {
			background: '#050403',
			field: 'linear-gradient(180deg, #070605 0%, #120f0d 56%, #050403 100%)',
			accent: '#FF6A6A',
			curve: 'rgba(255,233,228,0.62)',
			rail: 'rgba(255,210,198,0.18)',
		};
	}

	return {
		background: '#000000',
		field: 'linear-gradient(180deg, #020202 0%, #090909 55%, #040404 100%)',
		accent: '#FF3366',
		curve: 'rgba(255,255,255,0.72)',
		rail: 'rgba(255,255,255,0.18)',
	};
};

export const applyStylePackToProfile = <
	T extends {
		accentColor: string;
		curveStroke: string;
		curveOpacity: number;
		textMaxWidth: string;
		resolveMaxWidth: string;
	}
>(
	profile: T,
	fields: ResolvedStylePackFields,
): T => {
	const palette = resolveStylePackPalette(fields);
	const negativeSpaceBias = Math.max(0, Math.min(1, fields.negativeSpaceTarget));
	const textWidth = `${Math.round(58 + (1 - negativeSpaceBias) * 24)}%`;
	const resolveWidth = `${Math.round(70 + (1 - negativeSpaceBias) * 20)}%`;
	const accentOpacity = 0.1 + fields.accentIntensity * 0.22;
	const curveOpacity = Math.max(0.56, Math.min(0.92, 0.58 + fields.accentIntensity * 0.34));

	return {
		...profile,
		accentColor: palette.rail.replace(/0\.\d+\)/, `${accentOpacity.toFixed(2)})`),
		curveStroke: palette.curve,
		curveOpacity,
		textMaxWidth: textWidth,
		resolveMaxWidth: resolveWidth,
	};
};
