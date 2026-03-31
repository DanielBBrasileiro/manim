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
	whisper: [0.985, 1],
	statement: [0.975, 1],
	climax: [0.96, 1],
	resolve: [0.92, 1],
	brand: [0.97, 1],
};

const roleOffsetY: Record<NarrativeRole, [number, number]> = {
	whisper: [18, 0],
	statement: [24, 0],
	climax: [34, 0],
	resolve: [46, 0],
	brand: [12, 0],
};

const roleBlur: Record<NarrativeRole, [number, number]> = {
	whisper: [10, 0],
	statement: [8, 0],
	climax: [6, 0],
	resolve: [12, 0],
	brand: [4, 0],
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
}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();
	const zoneStyle = zoneStyles[zone];
	const resolvedAlign = align ?? roleAlign[role];
	const motionFrame = Math.max(0, frame - delay);

	const entrance = spring({
		fps,
		frame: motionFrame,
		config:
			role === 'resolve'
				? {damping: 16, mass: 0.95, stiffness: 110}
				: role === 'climax'
					? {damping: 14, mass: 0.85, stiffness: 120}
					: {damping: 20, mass: 1.0, stiffness: 70},
	});

	const opacity = interpolate(motionFrame, [0, 8, 22], [0, 0.65, 1], {
		extrapolateLeft: 'clamp',
		extrapolateRight: 'clamp',
	});
	const scale = interpolate(entrance, [0, 1], roleScaleIn[role]);
	const translateY = interpolate(entrance, [0, 1], roleOffsetY[role]);
	const blur = interpolate(entrance, [0, 1], roleBlur[role]);

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
					maxWidth,
					textAlign: resolvedAlign,
				}}
			>
				<div
					style={{
						fontFamily: role === 'resolve' ? brandFont : narrativeFont,
						fontSize:
							size ?? (role === 'resolve' ? 'clamp(3.8rem, 12vw, 7.2rem)' : narrativeSize),
						fontWeight: weight ?? roleWeight[role],
						letterSpacing: roleLetterSpacing[role],
						color:
							color ??
							(accent ? Theme.colors.accent : role === 'brand' ? Theme.colors.textSecondary : Theme.colors.textPrimary),
						opacity,
						transform: `translateY(${translateY}px) scale(${scale})`,
						filter: `blur(${blur}px)`,
						margin: 0,
						lineHeight: role === 'resolve' ? 0.88 : 1,
						textTransform: role === 'resolve' ? 'uppercase' : 'none',
						whiteSpace: 'pre-wrap',
					}}
				>
					{text}
				</div>
			</div>
		</AbsoluteFill>
	);
};
