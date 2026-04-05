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
	primitiveFamily?: string;
	primitiveWeight?: number;
	primitiveOpacity?: number;
	primitiveTension?: number;
};

export type StylePackPalette = {
	mode: string;
	background: string;
	field: string;
	accent: string;
	curve: string;
	rail: string;
	ink: string;
	paper: string;
	grainLift: number;
};

type PaletteMode =
	| 'monochrome_pure'
	| 'desaturated_warm'
	| 'indigo_night'
	| 'carbon_gold'
	| 'void_crimson'
	| 'editorial_white'
	| 'blueprint_cold';

const STYLE_PACK_TO_MOTION_GRAMMAR: Record<string, string> = {
	silent_luxury: 'cinematic_restrained',
	kinetic_editorial: 'kinetic_editorial',
	data_ink: 'kinetic_editorial',
	carbon_authority: 'cinematic_restrained',
	signal_burst: 'kinetic_editorial',
	blueprint_cold: 'cinematic_restrained',
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

const STYLE_PACK_TO_PALETTE_MODE: Record<string, PaletteMode> = {
	silent_luxury: 'monochrome_pure',
	kinetic_editorial: 'desaturated_warm',
	data_ink: 'editorial_white',
	carbon_authority: 'carbon_gold',
	signal_burst: 'void_crimson',
	blueprint_cold: 'blueprint_cold',
};

const LEGACY_COLOR_MODE_ALIAS: Record<string, PaletteMode> = {
	monochrome_pure: 'monochrome_pure',
	monochrome_warm: 'desaturated_warm',
	indigo_night: 'indigo_night',
	carbon_gold: 'carbon_gold',
	void_crimson: 'void_crimson',
	editorial_white: 'editorial_white',
	desaturated_warm: 'desaturated_warm',
	blueprint_cold: 'blueprint_cold',
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
		primitive_family?: string | null;
		primitive_weight?: number | null;
		primitive_opacity?: number | null;
		primitive_tension?: number | null;
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
		primitiveFamily: explicit?.primitive_family ?? contract?.primitive_family,
		primitiveWeight: explicit?.primitive_weight ?? undefined,
		primitiveOpacity: explicit?.primitive_opacity ?? undefined,
		primitiveTension: explicit?.primitive_tension ?? undefined,
	};
};

export const resolveStylePackPaletteMode = (fields: ResolvedStylePackFields): PaletteMode => {
	const requestedMode = String(fields.colorMode ?? '')
		.trim()
		.toLowerCase();
	const aliasedMode = LEGACY_COLOR_MODE_ALIAS[requestedMode];
	const preferredByPack = STYLE_PACK_TO_PALETTE_MODE[fields.stylePackId];

	if (requestedMode === 'monochrome_warm' && preferredByPack) {
		return preferredByPack;
	}

	if (requestedMode === 'monochrome_pure' && preferredByPack && preferredByPack !== 'monochrome_pure') {
		return preferredByPack;
	}

	if (aliasedMode) {
		return aliasedMode;
	}

	return preferredByPack ?? 'monochrome_pure';
};

export const resolveStylePackPalette = (fields: ResolvedStylePackFields): StylePackPalette => {
	const paletteMode = resolveStylePackPaletteMode(fields);
	const accentLift = Math.max(0, Math.min(1, fields.accentIntensity));
	const restrainedRail = (base: number) => Math.max(0.1, Math.min(0.32, base + accentLift * 0.06));

	switch (paletteMode) {
		case 'desaturated_warm':
			return {
				mode: paletteMode,
				background: '#070504',
				field: 'linear-gradient(180deg, #0b0807 0%, #171210 52%, #070504 100%)',
				accent: '#D76C52',
				curve: 'rgba(255,232,220,0.66)',
				rail: `rgba(226,156,132,${restrainedRail(0.15).toFixed(2)})`,
				ink: '#F7EEE9',
				paper: '#1B1512',
				grainLift: 0.08,
			};
		case 'indigo_night':
			return {
				mode: paletteMode,
				background: '#04060C',
				field: 'linear-gradient(180deg, #060914 0%, #0d1326 56%, #04060c 100%)',
				accent: '#6C8CFF',
				curve: 'rgba(208,222,255,0.68)',
				rail: `rgba(124,154,255,${restrainedRail(0.14).toFixed(2)})`,
				ink: '#F1F5FF',
				paper: '#12182B',
				grainLift: 0.04,
			};
		case 'carbon_gold':
			return {
				mode: paletteMode,
				background: '#080604',
				field: 'linear-gradient(180deg, #0d0906 0%, #17120b 50%, #080604 100%)',
				accent: '#C9A56A',
				curve: 'rgba(255,242,214,0.64)',
				rail: `rgba(201,165,106,${restrainedRail(0.14).toFixed(2)})`,
				ink: '#F5EBD7',
				paper: '#17120C',
				grainLift: 0.02,
			};
		case 'void_crimson':
			return {
				mode: paletteMode,
				background: '#010101',
				field: 'linear-gradient(180deg, #040202 0%, #130506 56%, #010101 100%)',
				accent: '#C7243A',
				curve: 'rgba(255,244,246,0.8)',
				rail: `rgba(235,90,112,${restrainedRail(0.18).toFixed(2)})`,
				ink: '#FFF2F4',
				paper: '#18080A',
				grainLift: 0.1,
			};
		case 'editorial_white':
			return {
				mode: paletteMode,
				background: '#F4F0E8',
				field: 'linear-gradient(180deg, #f7f3ec 0%, #ece6dc 58%, #f1ece3 100%)',
				accent: '#335CFF',
				curve: 'rgba(27,30,36,0.72)',
				rail: `rgba(51,92,255,${restrainedRail(0.12).toFixed(2)})`,
				ink: '#12151B',
				paper: '#FFFFFF',
				grainLift: 0.03,
			};
		case 'blueprint_cold':
			return {
				mode: paletteMode,
				background: '#07111A',
				field: 'linear-gradient(180deg, #0a1622 0%, #102131 52%, #07111a 100%)',
				accent: '#5FB7D8',
				curve: 'rgba(220,244,255,0.66)',
				rail: `rgba(95,183,216,${restrainedRail(0.13).toFixed(2)})`,
				ink: '#E7F6FF',
				paper: '#122635',
				grainLift: 0.05,
			};
		case 'monochrome_pure':
		default:
			return {
				mode: 'monochrome_pure',
				background: '#050505',
				field: 'linear-gradient(180deg, #090909 0%, #121212 55%, #050505 100%)',
				accent: '#B9C1D4',
				curve: 'rgba(250,250,252,0.76)',
				rail: `rgba(185,193,212,${restrainedRail(0.11).toFixed(2)})`,
				ink: '#FAFAFC',
				paper: '#161616',
				grainLift: 0.01,
			};
	}
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
