import React from 'react';
import {
	AbsoluteFill,
	interpolate,
	spring,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {tokens} from '../theme';
import {Theme} from '../utils/theme';
import type {TypographySystemContract} from '../utils/typographySystems';
import {resolveNarrativeTypography} from '../utils/typographyEngine';
import type {CueMotionSpec} from '../utils/motionSequence';

export type NarrativeZone = 'top' | 'bottom' | 'center';
export type NarrativeRole = 'whisper' | 'statement' | 'climax' | 'resolve' | 'brand';

type NarrativeTextProps = {
	text: string;
	delay?: number;
	zone?: NarrativeZone;
	role?: NarrativeRole;
	color?: string;
	weight?: number;
	size?: string | number;
	align?: 'left' | 'center' | 'right';
	maxWidth?: string | number;
	accent?: boolean;
	typographySystem?: string | Partial<TypographySystemContract> | null;
	motionSpec?: CueMotionSpec | null;
};

const layout = tokens.layout.formats.vertical_9_16;
const textZones = layout.text_zones;
const safeInset = `${layout.safe_zone * 100}%`;
const narrativeFont = tokens.typography.fonts.narrative.family;
const brandFont = tokens.typography.fonts.brand.family;
const narrativeSize = tokens.typography.rules.sizing.vertical_9_16.narrative_text;

const zoneStyles: Record<NarrativeZone, React.CSSProperties> = {
	top: {
		top: textZones.top.y,
		height: textZones.top.height,
		justifyContent: 'flex-start',
	},
	center: {
		top: textZones.center.y,
		height: textZones.center.height,
		justifyContent: 'center',
	},
	bottom: {
		top: textZones.bottom.y,
		height: textZones.bottom.height,
		justifyContent: 'flex-end',
	},
};

const roleAlign: Record<NarrativeRole, 'left' | 'center' | 'right'> = {
	whisper: 'left',
	statement: 'left',
	climax: 'center',
	resolve: 'center',
	brand: 'right',
};

const roleWeight: Record<NarrativeRole, number> = {
	whisper: 300,
	statement: 400,
	climax: 500,
	resolve: tokens.typography.fonts.brand.weight,
	brand: 500,
};

const roleLetterSpacing: Record<NarrativeRole, string> = {
	whisper: '-0.02em',
	statement: '-0.035em',
	climax: '-0.045em',
	resolve: '-0.06em',
	brand: '-0.03em',
};

const roleScaleIn: Record<NarrativeRole, [number, number]> = {
	whisper: [0.992, 1],
	statement: [0.986, 1],
	climax: [0.972, 1],
	resolve: [0.945, 1],
	brand: [0.982, 1],
};

const roleOffsetY: Record<NarrativeRole, [number, number]> = {
	whisper: [10, 0],
	statement: [16, 0],
	climax: [22, 0],
	resolve: [28, 0],
	brand: [8, 0],
};

const roleBlur: Record<NarrativeRole, [number, number]> = {
	whisper: [4, 0],
	statement: [3, 0],
	climax: [2, 0],
	resolve: [4, 0],
	brand: [1, 0],
};

const containerAlign = (align: 'left' | 'center' | 'right'): React.CSSProperties => {
	if (align === 'center') {
		return {alignItems: 'center'};
	}

	return align === 'right' ? {alignItems: 'flex-end'} : {alignItems: 'flex-start'};
};

export const NarrativeText: React.FC<NarrativeTextProps> = ({
	text,
	delay = 0,
	zone = 'center',
	role = 'statement',
	color,
	weight,
	size,
	align,
	maxWidth = '78%',
	accent = false,
	typographySystem,
	motionSpec,
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const zoneStyle = zoneStyles[zone];
	const typography = resolveNarrativeTypography({
		text,
		role,
		align,
		typographySystem,
	});
	const resolvedAlign = typography?.containerAlign ?? align ?? roleAlign[role];
	const motionDelay = delay + (motionSpec?.staggerDelayFrames ?? 0);
	const motionFrame = Math.max(0, frame - motionDelay);
	const fallbackSpring =
		role === 'resolve'
			? {damping: 16, mass: 0.95, stiffness: 110}
			: role === 'climax'
				? {damping: 14, mass: 0.85, stiffness: 120}
				: {damping: 20, mass: 1.0, stiffness: 70};
	const activeFrame = motionSpec
		? Math.max(0, motionFrame - motionSpec.anticipationFrames)
		: motionFrame;

	const entrance = spring({
		fps,
		frame: activeFrame,
		config: motionSpec?.spring ?? fallbackSpring,
	});

	const actionEnd = motionSpec?.actionFrames ?? 12;
	const opacity = interpolate(activeFrame, [0, Math.max(2, Math.round(actionEnd * 0.35)), Math.max(4, actionEnd)], [0, 0.82, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const emphasisFactor = motionSpec?.emphasis === 'high' ? 1.14 : motionSpec?.emphasis === 'low' ? 0.9 : 1;
	const scaleFrom = motionSpec ? roleScaleIn[role][0] - ((emphasisFactor - 1) * 0.02) : roleScaleIn[role][0];
	const scale = interpolate(entrance, [0, 1], [scaleFrom, roleScaleIn[role][1]]);
	const translateYBase = interpolate(entrance, [0, 1], [roleOffsetY[role][0] * emphasisFactor, roleOffsetY[role][1]]);
	const blurBase = motionSpec?.emphasis === 'low' ? roleBlur[role][0] * 0.82 : motionSpec?.emphasis === 'high' ? roleBlur[role][0] * 1.15 : roleBlur[role][0];
	const blur = interpolate(entrance, [0, 1], [blurBase, roleBlur[role][1]]);
	const translateY = typography
		? Math.round((translateYBase + typography.opticalShiftPx) / typography.baselineUnit) * typography.baselineUnit
		: translateYBase;
	const textContent = typography?.text ?? text;
	const fontSize = typography ? `${typography.fontSizePx}px` : size ?? (role === 'resolve' ? 'clamp(3.8rem, 12vw, 7.2rem)' : narrativeSize);
	const fontWeight = weight ?? roleWeight[role];
	const letterSpacing = typography?.letterSpacing ?? roleLetterSpacing[role];
	const lineHeight = typography?.lineHeight ?? (role === 'resolve' ? 0.88 : 1);
	const blockWidth = typography?.maxWidth ?? maxWidth;
	const textAlign = typography?.textAlign ?? resolvedAlign;

	return (
		<AbsoluteFill
			style={{
				...zoneStyle,
				...containerAlign(resolvedAlign),
				paddingLeft: safeInset,
				paddingRight: safeInset,
				pointerEvents: 'none',
				position: 'absolute',
			}}
		>
			<div
				style={{
					maxWidth: blockWidth,
					textAlign,
					width: typography ? 'fit-content' : undefined,
				}}
			>
				<div
					style={{
						fontFamily: role === 'resolve' ? brandFont : narrativeFont,
						fontSize,
						fontWeight,
						letterSpacing,
						color:
							color ??
							(accent ? Theme.colors.accent : role === 'brand' ? Theme.colors.textSecondary : Theme.colors.textPrimary),
						opacity,
						transform: `translateY(${translateY}px) scale(${scale})`,
						filter: `blur(${blur}px)`,
						margin: 0,
						lineHeight,
						textTransform: role === 'resolve' ? 'uppercase' : 'none',
						whiteSpace: typography ? 'pre-line' : 'pre-wrap',
					}}
				>
					{textContent}
				</div>
			</div>
		</AbsoluteFill>
	);
};
