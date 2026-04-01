import React from 'react';
import {tokens} from '../theme';
import {Theme} from '../utils/theme';
import {resolveNarrativeTypography} from '../utils/typographyEngine';
import {boxStyle} from '../utils/stillLayout';
import type {TypographySystemContract} from '../utils/typographySystems';
import type {NarrativeRole} from './NarrativeText';

type LayoutBox = {
	x: number;
	y: number;
	w: number;
	h: number;
};

type StillTextBlockProps = {
	text: string;
	role: NarrativeRole;
	box: LayoutBox;
	typographySystem?: string | Partial<TypographySystemContract> | null;
	color?: string;
	align?: 'left' | 'center' | 'right';
	weight?: number;
	uppercase?: boolean;
	opacity?: number;
};

export const StillTextBlock: React.FC<StillTextBlockProps> = ({
	text,
	role,
	box,
	typographySystem,
	color,
	align,
	weight,
	uppercase = false,
	opacity = 1,
}) => {
	const typography = resolveNarrativeTypography({
		text,
		role,
		align,
		typographySystem,
	});
	const resolvedAlign = typography?.textAlign ?? align ?? 'left';

	return (
		<div
			style={{
				...boxStyle(box),
				display: 'flex',
				flexDirection: 'column',
				justifyContent: 'flex-start',
				alignItems:
					resolvedAlign === 'center'
						? 'center'
						: resolvedAlign === 'right'
							? 'flex-end'
							: 'flex-start',
				color:
					color ??
					(role === 'brand' ? Theme.colors.textSecondary : Theme.colors.textPrimary),
				opacity,
				pointerEvents: 'none',
			}}
		>
			<div
				style={{
					maxWidth: typography?.maxWidth ?? '78%',
					width: typography ? 'fit-content' : undefined,
					fontFamily:
						role === 'resolve' ? tokens.typography.fonts.brand.family : tokens.typography.fonts.narrative.family,
					fontSize: typography ? `${typography.fontSizePx}px` : 'clamp(2rem, 5vw, 3.6rem)',
					fontWeight: weight ?? (role === 'resolve' ? tokens.typography.fonts.brand.weight : 300),
					letterSpacing: typography?.letterSpacing ?? '-0.04em',
					lineHeight: typography?.lineHeight ?? 1,
					textAlign: resolvedAlign,
					textTransform: uppercase || role === 'resolve' ? 'uppercase' : 'none',
					whiteSpace: typography ? 'pre-line' : 'pre-wrap',
					margin: 0,
				}}
			>
				{typography?.text ?? text}
			</div>
		</div>
	);
};
