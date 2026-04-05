import React, {useMemo} from 'react';
import {AbsoluteFill, Img, staticFile, useVideoConfig} from 'remotion';
import {StillTextBlock} from '../components/StillTextBlock';
import {CompositionPrimitive} from '../components/CompositionPrimitive';
import {tokens} from '../theme';
import {Theme} from '../utils/theme';
import {getStillFamily, getStylePack} from '../utils/stillContracts';
import {boxStyle, resolveStillLayout} from '../utils/stillLayout';
import {resolveStylePackFields, resolveStylePackPalette} from '../utils/stylePack';

type StoryAtoms = {
	title?: string;
	tagline?: string;
	thesis?: string;
	resolve_word?: string;
	resolveWord?: string;
};

type EditorialBox = {
	x?: number;
	y?: number;
	w?: number;
	h?: number;
};

type EditorialLayout = {
	family?: string;
	safe_margin_px?: number;
	hero_zone?: EditorialBox;
	support_zone?: EditorialBox;
	empty_zone?: EditorialBox;
	focal_zone?: EditorialBox;
	curve_box?: EditorialBox;
	eyebrow_box?: EditorialBox;
	title_box?: EditorialBox;
	accent_anchor?: {x?: number; y?: number};
	asset_crop?: {
		object_position?: string;
		veil_opacity?: number;
		grayscale?: number;
		contrast?: number;
	};
};

type StillBaseStrategy = {
	base?: string | null;
	background?: string;
	requires_manim?: boolean;
	allow_manim_bypass?: boolean;
	use_asset_if_available?: boolean;
};

export type StillComposerProps = {
	target?: string;
	targetId?: string;
	renderManifest?: {
		target?: string;
		targetId?: string;
		targetKind?: string;
		story_atoms?: StoryAtoms;
		bgSrc?: string;
		bg_src?: string;
		editorialLayout?: EditorialLayout;
		editorial_layout?: EditorialLayout;
		active_variant?: {label?: string; composition_mode?: string};
		style_pack?: string;
		typography_system?: string;
		still_family?: string;
		motion_grammar?: string;
		color_mode?: string;
		negative_space_target?: number;
		accent_intensity?: number;
		grain?: number;
		still_base_strategy?: StillBaseStrategy;
		summary?: string;
		seed?: string;
	};
};

const wordCap = (text?: string, maxWords = 3): string =>
	String(text || '')
		.trim()
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, maxWords)
		.join(' ');

const lineCap = (text?: string, maxWords = 10): string =>
	String(text || '')
		.trim()
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, maxWords)
		.join(' ');

const withAlpha = (color: string, alpha: number): string => {
	if (!color) {
		return `rgba(255,255,255,${alpha})`;
	}
	if (color.startsWith('rgba(')) {
		return color.replace(/rgba\(([^)]+),\s*[\d.]+\)/, `rgba($1,${alpha})`);
	}
	if (color.startsWith('rgb(')) {
		return color.replace('rgb(', 'rgba(').replace(')', `,${alpha})`);
	}
	if (color.startsWith('#')) {
		const value = color.slice(1);
		const normalized =
			value.length === 3
				? value
						.split('')
						.map((part) => part + part)
						.join('')
				: value.padEnd(6, '0').slice(0, 6);
		const r = parseInt(normalized.slice(0, 2), 16);
		const g = parseInt(normalized.slice(2, 4), 16);
		const b = parseInt(normalized.slice(4, 6), 16);
		return `rgba(${r},${g},${b},${alpha})`;
	}
	return color;
};

const GrainOverlay: React.FC<{opacity: number; inkColor?: string}> = ({opacity, inkColor}) => {
	const dot = inkColor
		? inkColor.replace(/,\s*[\d.]+\)$/, ',0.10)')
		: 'rgba(255,255,255,0.08)';
	return (
		<div
			style={{
				position: 'absolute',
				inset: 0,
				opacity,
				mixBlendMode: 'screen',
				backgroundImage: `radial-gradient(${dot} 0.6px, transparent 0.7px)`,
				backgroundSize: '10px 10px',
				pointerEvents: 'none',
			}}
		/>
	);
};

const AnchorMarker: React.FC<{
	x: number;
	y: number;
	size: number;
	color: string;
	shape?: 'dot' | 'square';
}> = ({x, y, size, color, shape = 'dot'}) => (
	<div
		style={{
			position: 'absolute',
			left: `calc(${(x * 100).toFixed(3)}% - ${size / 2}px)`,
			top: `calc(${(y * 100).toFixed(3)}% - ${size / 2}px)`,
			width: size,
			height: size,
			borderRadius: shape === 'dot' ? 999 : 4,
			background: color,
			boxShadow: `0 0 0 1px ${withAlpha(color, 0.14)}`,
			opacity: 0.92,
		}}
	/>
);

export const StillComposer: React.FC<StillComposerProps> = ({target, targetId, renderManifest}) => {
	const manifest = renderManifest ?? {};
	const {width, height} = useVideoConfig();
	const resolvedTargetId = target ?? targetId ?? manifest.targetId ?? manifest.target;
	const resolvedStylePack = resolveStylePackFields({
		stylePackId: manifest.style_pack ?? 'silent_luxury',
		explicit: {
			typography_system: manifest.typography_system,
			still_family: manifest.still_family,
			motion_grammar: manifest.motion_grammar,
			color_mode: manifest.color_mode,
			negative_space_target: manifest.negative_space_target,
			accent_intensity: manifest.accent_intensity,
			grain: manifest.grain,
		},
	});
	const stylePack = {
		...(getStylePack(resolvedStylePack.stylePackId) ?? {}),
		id: resolvedStylePack.stylePackId,
		typography_system: resolvedStylePack.typographySystem,
		still_family: resolvedStylePack.stillFamily,
		color_mode: resolvedStylePack.colorMode,
		negative_space_target: resolvedStylePack.negativeSpaceTarget,
		accent_intensity: resolvedStylePack.accentIntensity,
		grain: resolvedStylePack.grain,
	};
	const palette = resolveStylePackPalette(resolvedStylePack);
	const stillFamily =
		getStillFamily(resolvedStylePack.stillFamily ?? stylePack?.still_family ?? 'poster_minimal') ??
		getStillFamily('poster_minimal');
	const typographySystem =
		resolvedStylePack.typographySystem ?? stillFamily?.typography_system ?? stylePack?.typography_system;
	const editorialLayout = manifest.editorialLayout ?? manifest.editorial_layout;
	const layout = useMemo(
		() =>
			resolveStillLayout({
				editorialLayout,
				stillFamily,
				stylePack,
				width,
				height,
			}),
		[editorialLayout, stillFamily, stylePack, width, height],
	);
	const storyAtoms = manifest.story_atoms ?? {};
	const baseStrategy = manifest.still_base_strategy ?? {};
	const bgSrc = manifest.bgSrc ?? manifest.bg_src;
	const allowBypass = baseStrategy.allow_manim_bypass ?? !baseStrategy.requires_manim;
	const shouldUseBaseAsset =
		Boolean(bgSrc) && (baseStrategy.use_asset_if_available ?? stillFamily?.base !== null);
	
	const grammar = stillFamily?.grammar ?? 'editorial_grid';
	
	const titleText = wordCap(
		storyAtoms.resolve_word ??
			storyAtoms.resolveWord ??
			storyAtoms.title ??
			storyAtoms.thesis ??
			tokens.brand.identity.name,
		grammar === 'monumental' ? 2 : 6,
	);
	const supportText = lineCap(
		storyAtoms.tagline ??
			manifest.active_variant?.label ??
			manifest.summary ??
			storyAtoms.thesis,
		grammar === 'monumental' ? 4 : 12,
	);
	const brandText = tokens.brand.identity.name;
	const accentOpacity = Math.max(0.08, resolvedStylePack.accentIntensity);
	const grainOpacity = Math.max(palette.grainLift, resolvedStylePack.grain ?? stillFamily?.grain ?? 0.04);
	const familyId = stillFamily?.id ?? 'poster_minimal';
	const isCentered = grammar === 'centered';
	const isAsymmetric = grammar === 'asymmetric';
	const isEditorialGrid = grammar === 'editorial_grid';
	const isArchitectural = familyId === 'architectural_grid';
	const isCenteredResolve = familyId === 'centered_resolve';
	const isPosterMinimal = familyId === 'poster_minimal';
	const titleRole = isEditorialGrid || isAsymmetric ? 'climax' : 'resolve';
	const titleAlign = isCentered ? 'center' : 'left';
	const supportAlign = isCentered ? 'center' : isAsymmetric ? 'right' : 'left';
	const titleWeight = isCenteredResolve ? 360 : isArchitectural ? 340 : isPosterMinimal ? 300 : 320;
	const supportRole = isEditorialGrid || isAsymmetric ? 'statement' : 'brand';
	const primitiveType =
		resolvedStylePack.primitiveFamily ?? stillFamily?.primitive_family ?? 'arc';
	const primitiveWeight = stillFamily?.primitive_weight ?? (isArchitectural ? 1.2 : 1.6);
	const primitiveOpacity = isCenteredResolve ? 0.26 : isAsymmetric ? 0.52 : isArchitectural ? 0.30 : 0.22;
	const primitiveTension = isAsymmetric ? 0.72 : isArchitectural ? 0.46 : 0.34;
	const anchorColor = isArchitectural ? palette.rail : palette.accent;
	const backgroundColor = palette.background;
	const inkColor = palette.ink;
	const seed = manifest.seed ?? resolvedTargetId ?? 'still-default-seed';
	const titleBox = layout.titleBox;
	const supportBox = layout.eyebrowBox;
	const brandBox = isCenteredResolve
		? {x: 0.43, y: 0.78, w: 0.16, h: 0.04}
		: isAsymmetric
			? {x: 0.10, y: 0.84, w: 0.20, h: 0.04}
			: {
					x: layout.supportZone.x,
					y: Math.min(0.88, layout.supportZone.y + layout.supportZone.h + 0.56),
					w: 0.18,
					h: 0.04,
			  };

	return (
		<AbsoluteFill style={{backgroundColor}}>
			{shouldUseBaseAsset ? (
				<Img
					src={staticFile(bgSrc as string)}
					style={{
						position: 'absolute',
						inset: 0,
						width: '100%',
						height: '100%',
						objectFit: 'cover',
						objectPosition: layout.assetCrop.object_position,
						filter: `grayscale(${layout.assetCrop.grayscale}) contrast(${layout.assetCrop.contrast}) brightness(0.68)`,
						opacity: 0.76,
					}}
				/>
			) : null}

			<div
				style={{
					position: 'absolute',
					inset: 0,
					background: palette.field,
					opacity: shouldUseBaseAsset ? 0.82 : 1,
				}}
			/>

			<div
				style={{
					...boxStyle(layout.emptyZone),
					background: isCenteredResolve
						? `radial-gradient(circle at center, ${withAlpha(palette.paper, 0.08)} 0%, transparent 74%)`
						: isArchitectural
							? `linear-gradient(180deg, ${withAlpha(palette.rail, 0.10)} 0%, ${withAlpha(palette.rail, 0.02)} 100%)`
							: `linear-gradient(180deg, ${withAlpha(palette.paper, 0.05)} 0%, transparent 100%)`,
					border: isArchitectural ? `1px solid ${withAlpha(palette.rail, 0.12)}` : undefined,
					borderRadius: isCenteredResolve ? 999 : isAsymmetric ? '28px 4px 28px 4px' : 20,
					mixBlendMode: isCenteredResolve ? 'screen' : 'normal',
					opacity: isAsymmetric ? 0.7 : 1,
					pointerEvents: 'none',
				}}
			/>

			{isCenteredResolve || isArchitectural || isAsymmetric ? (
				<div
					style={{
						...boxStyle(layout.heroZone),
						background: isCenteredResolve
							? `radial-gradient(circle at center, ${withAlpha(palette.paper, 0.10)} 0%, transparent 76%)`
							: isArchitectural
								? `linear-gradient(180deg, ${withAlpha(palette.paper, 0.06)} 0%, ${withAlpha(palette.paper, 0.02)} 100%)`
								: `linear-gradient(135deg, ${withAlpha(palette.paper, 0.09)} 0%, transparent 100%)`,
						border: isArchitectural ? `1px solid ${withAlpha(palette.rail, 0.10)}` : undefined,
						borderRadius: isCenteredResolve ? 999 : isAsymmetric ? '36px 8px 24px 8px' : 16,
						pointerEvents: 'none',
					}}
				/>
			) : null}

			{isArchitectural ? (
				<div
					style={{
						...boxStyle(layout.focalZone),
						border: `1px solid ${withAlpha(palette.rail, 0.18)}`,
						boxShadow: `inset 0 0 0 1px ${withAlpha(palette.paper, 0.03)}`,
						pointerEvents: 'none',
					}}
				>
					<div
						style={{
							position: 'absolute',
							left: '33.333%',
							top: 0,
							bottom: 0,
							width: 1,
							background: withAlpha(palette.rail, 0.16),
						}}
					/>
					<div
						style={{
							position: 'absolute',
							left: '66.666%',
							top: 0,
							bottom: 0,
							width: 1,
							background: withAlpha(palette.rail, 0.12),
						}}
					/>
				</div>
			) : isAsymmetric ? (
				<div
					style={{
						...boxStyle(layout.focalZone),
						pointerEvents: 'none',
					}}
				>
					<div
						style={{
							position: 'absolute',
							top: 0,
							right: 0,
							width: '26%',
							height: 1,
							background: withAlpha(palette.rail, 0.22),
						}}
					/>
					<div
						style={{
							position: 'absolute',
							top: 0,
							right: 0,
							width: 1,
							height: '18%',
							background: withAlpha(palette.rail, 0.22),
						}}
					/>
					<div
						style={{
							position: 'absolute',
							left: 0,
							bottom: 0,
							width: '22%',
							height: 1,
							background: withAlpha(palette.rail, 0.18),
						}}
					/>
				</div>
			) : isEditorialGrid ? (
				<div
					style={{
						...boxStyle(layout.focalZone),
						borderTop: `1px solid ${withAlpha(palette.rail, 0.16)}`,
						borderLeft: `1px solid ${withAlpha(palette.rail, 0.12)}`,
						pointerEvents: 'none',
					}}
				/>
			) : null}

			<CompositionPrimitive
				seed={seed}
				type={primitiveType}
				weight={primitiveWeight}
				opacity={primitiveOpacity}
				tension={primitiveTension}
				color={isArchitectural ? palette.rail : palette.curve}
				style={boxStyle(layout.curveBox)}
			/>

			<AnchorMarker
				x={layout.accentAnchor.x}
				y={layout.accentAnchor.y}
				size={isCenteredResolve ? 8 : isArchitectural ? 9 : 10}
				color={anchorColor}
				shape={isArchitectural ? 'square' : 'dot'}
			/>

			<StillTextBlock
				text={titleText}
				role={titleRole}
				box={titleBox}
				typographySystem={typographySystem}
				color={inkColor}
				align={titleAlign}
				weight={titleWeight}
			/>

			{supportText && (stillFamily?.max_text_elements ?? 2) > 1 ? (
				<StillTextBlock
					text={supportText}
					role={supportRole}
					box={supportBox}
					typographySystem={typographySystem}
					color={isEditorialGrid || isAsymmetric ? inkColor : palette.accent}
					align={supportAlign}
					weight={300}
					uppercase={!isEditorialGrid && !isAsymmetric}
					opacity={isEditorialGrid || isAsymmetric ? 0.82 : 0.76}
				/>
			) : null}

			{(stillFamily?.max_text_elements ?? 0) > 2 || isCenteredResolve ? (
				<StillTextBlock
					text={brandText}
					role="brand"
					box={brandBox}
					typographySystem={typographySystem}
					color={isCenteredResolve ? inkColor : Theme.colors.textSecondary}
					align={isCenteredResolve ? 'center' : 'left'}
					opacity={0.72}
				/>
			) : null}

			<GrainOverlay opacity={grainOpacity} inkColor={palette.curve} />
		</AbsoluteFill>
	);
};
