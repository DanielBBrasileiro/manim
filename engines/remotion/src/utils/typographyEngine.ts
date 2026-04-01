import type {NarrativeRole} from '../components/NarrativeText';
import {breakText} from './textBreak';
import {createScaleSystem, type ScaleRole} from './typeScale';
import {
	getTypographySystem,
	type TypographyAlignment,
	type TypographyBreakStrategy,
	type TypographySystemContract,
} from './typographySystems';

type HorizontalAlign = 'left' | 'center' | 'right';

type TypographySpec = {
	text: string;
	fontSizePx: number;
	letterSpacing: string;
	lineHeight: number;
	maxWidth: string;
	textAlign: HorizontalAlign;
	containerAlign: HorizontalAlign;
	baselineUnit: number;
	opticalShiftPx: number;
};

const roleToScaleRole = (role: NarrativeRole): ScaleRole => {
	switch (role) {
		case 'resolve':
		case 'climax':
			return 'display';
		case 'statement':
			return 'title';
		case 'brand':
			return 'caption';
		case 'whisper':
		default:
			return 'body';
	}
};

const alignmentToTextAlign = (
	alignment: TypographyAlignment,
): HorizontalAlign => {
	switch (alignment) {
		case 'flush_right':
			return 'right';
		case 'mathematical_center':
			return 'center';
		case 'optical_left':
		case 'justified':
		default:
			return 'left';
	}
};

const parseEm = (value: string): number => {
	const parsed = Number.parseFloat(value.replace('em', '').trim());
	return Number.isFinite(parsed) ? parsed : 0;
};

const toEm = (value: number): string => `${value.toFixed(3).replace(/\.?0+$/, '')}em`;

const interpolate = (from: number, to: number, amount: number): number => from + (to - from) * amount;

const computeTracking = (
	role: ScaleRole,
	system: TypographySystemContract,
): string => {
	const display = parseEm(system.tracking_at_display);
	const body = parseEm(system.tracking_at_body);

	switch (role) {
		case 'display':
			return toEm(display);
		case 'title':
			return toEm(interpolate(display, body, 0.55));
		case 'caption':
			return toEm(body + Math.abs(display - body) * 0.3);
		case 'body':
		default:
			return toEm(body);
	}
};

const snapToGrid = (value: number, baselineUnit: number): number =>
	Math.max(baselineUnit, Math.round(value / baselineUnit) * baselineUnit);

const computeLineHeight = (
	role: ScaleRole,
	fontSizePx: number,
	system: TypographySystemContract,
	baselineUnit: number,
): number => {
	const raw =
		role === 'display'
			? system.leading_display
			: role === 'title'
				? interpolate(system.leading_display, system.leading_body, 0.45)
				: role === 'caption'
					? system.leading_body + 0.08
					: system.leading_body;

	const snapped = snapToGrid(fontSizePx * raw, baselineUnit);
	return snapped / fontSizePx;
};

const measureByRole = (role: ScaleRole, system: TypographySystemContract): number => {
	switch (role) {
		case 'display':
			return Math.min(20, system.measure_chars);
		case 'title':
			return Math.min(28, Math.max(20, system.measure_chars));
		case 'caption':
			return Math.min(24, Math.max(14, system.measure_chars));
		case 'body':
		default:
			return Math.min(50, Math.max(45, system.measure_chars));
	}
};

const resolveBreakStrategy = (system: TypographySystemContract): TypographyBreakStrategy =>
	system.break_strategy ?? 'semantic';

const computeOpticalShift = (
	role: ScaleRole,
	align: HorizontalAlign,
	fontSizePx: number,
	baselineUnit: number,
): number => {
	if (align !== 'center') {
		return 0;
	}

	const factor = role === 'display' ? -0.08 : role === 'title' ? -0.06 : -0.04;
	return snapToGrid(fontSizePx * factor, baselineUnit);
};

export const resolveNarrativeTypography = ({
	text,
	role,
	align,
	typographySystem,
}: {
	text: string;
	role: NarrativeRole;
	align?: HorizontalAlign;
	typographySystem?: string | Partial<TypographySystemContract> | null;
}): TypographySpec | null => {
	const system = getTypographySystem(typographySystem);
	if (!system) {
		return null;
	}

	const roleScale = roleToScaleRole(role);
	const scale = createScaleSystem(system.scale);
	const baselineUnit = system.baseline_unit ?? 8;
	const fontSizePx = scale.family[roleScale];
	const lineHeight = computeLineHeight(roleScale, fontSizePx, system, baselineUnit);
	const measureChars = measureByRole(roleScale, system);
	const resolvedAlign = align ?? alignmentToTextAlign(system.alignment_default);
	const opticalShiftPx = computeOpticalShift(roleScale, resolvedAlign, fontSizePx, baselineUnit);

	return {
		text: breakText(text, resolveBreakStrategy(system), {
			maxChars: measureChars,
			role: roleScale,
			maxWordsPerBlock: system.max_words_per_block,
		}),
		fontSizePx,
		letterSpacing: computeTracking(roleScale, system),
		lineHeight,
		maxWidth: `${measureChars}ch`,
		textAlign: resolvedAlign,
		containerAlign: resolvedAlign,
		baselineUnit,
		opticalShiftPx,
	};
};
