import React, {useMemo} from 'react';
import {AbsoluteFill, Img, staticFile, useVideoConfig} from 'remotion';
import {StillTextBlock} from '../components/StillTextBlock';
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

const GrainOverlay: React.FC<{opacity: number}> = ({opacity}) => (
	<div
		style={{
			position: 'absolute',
			inset: 0,
			opacity,
			mixBlendMode: 'screen',
			backgroundImage:
				'radial-gradient(rgba(255,255,255,0.08) 0.6px, transparent 0.7px)',
			backgroundSize: '10px 10px',
			pointerEvents: 'none',
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
	const titleText = wordCap(
		storyAtoms.resolve_word ??
			storyAtoms.resolveWord ??
			storyAtoms.title ??
			storyAtoms.thesis ??
			tokens.brand.identity.name,
		stillFamily?.id === 'poster_minimal' ? 2 : 5,
	);
	const supportText = lineCap(
		storyAtoms.tagline ??
			manifest.active_variant?.label ??
			manifest.summary ??
			storyAtoms.thesis,
		stillFamily?.max_text_elements === 2 ? 2 : 8,
	);
	const brandText = tokens.brand.identity.name;
	const accentOpacity = Math.max(0.08, resolvedStylePack.accentIntensity);
	const grainOpacity = Math.min(0.08, resolvedStylePack.grain ?? stillFamily?.grain ?? 0.04);
	const isEditorialPortrait = stillFamily?.id === 'editorial_portrait';
	const titleRole = isEditorialPortrait ? 'climax' : 'resolve';
	const backgroundColor = palette.background;

	return (
		<AbsoluteFill style={{backgroundColor}}>
			{shouldUseBaseAsset ? (
				<>
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
					<div
						style={{
							position: 'absolute',
							inset: 0,
							background: palette.background,
							opacity: layout.assetCrop.veil_opacity,
						}}
					/>
				</>
			) : allowBypass ? (
				<div
					style={{
						position: 'absolute',
						inset: 0,
						background:
							stillFamily?.background === 'photo_with_veil'
								? palette.field
								: palette.background,
					}}
				/>
			) : null}

			<div
				style={{
					...boxStyle(layout.emptyZone),
					background: 'transparent',
				}}
			/>

			{stillFamily?.accent === 'single_rule_line' ? (
				<>
					<div
						style={{
							position: 'absolute',
							left: `${(layout.curveBox.x * 100).toFixed(3)}%`,
							top: `${((layout.accentAnchor.y ?? 0.14) * 100).toFixed(3)}%`,
							width: `${(layout.curveBox.w * 42).toFixed(3)}%`,
							height: 1,
							background: '#FFFFFF',
							opacity: accentOpacity,
						}}
					/>
					<div
						style={{
							position: 'absolute',
							left: `${((layout.accentAnchor.x ?? 0.9) * 100).toFixed(3)}%`,
							top: `${((layout.accentAnchor.y ?? 0.14) * 100).toFixed(3)}%`,
							width: 10,
							height: 10,
							borderRadius: 999,
							background: palette.accent,
						}}
					/>
				</>
			) : (
				<div
					style={{
						position: 'absolute',
						inset: `${Math.round(layout.safeZonePx * 0.45)}px`,
						border: `1px solid ${palette.rail.replace(/0\.\d+\)/, `${(accentOpacity * 0.7).toFixed(3)})`)}`,
						borderRadius: 24,
					}}
				/>
			)}

			<StillTextBlock
				text={titleText}
				role={titleRole}
				box={layout.titleBox}
				typographySystem={typographySystem}
				color="#FFFFFF"
				align={isEditorialPortrait ? 'left' : 'left'}
				weight={isEditorialPortrait ? 400 : 300}
			/>

			{supportText && (stillFamily?.max_text_elements ?? 2) > 1 ? (
				<StillTextBlock
					text={supportText}
					role={isEditorialPortrait ? 'statement' : 'brand'}
					box={layout.eyebrowBox}
					typographySystem={typographySystem}
					color={isEditorialPortrait ? '#FFFFFF' : palette.accent}
					align="left"
					weight={isEditorialPortrait ? 300 : 300}
					uppercase={!isEditorialPortrait}
					opacity={isEditorialPortrait ? 0.82 : 0.76}
				/>
			) : null}

			{isEditorialPortrait && (stillFamily?.max_text_elements ?? 0) > 2 ? (
				<StillTextBlock
					text={brandText}
					role="brand"
					box={{
						x: layout.supportZone.x,
						y: Math.min(0.88, layout.supportZone.y + layout.supportZone.h + 0.56),
						w: 0.18,
						h: 0.04,
					}}
					typographySystem={typographySystem}
					color={Theme.colors.textSecondary}
					align="left"
					opacity={0.72}
				/>
			) : null}

			<GrainOverlay opacity={grainOpacity} />
		</AbsoluteFill>
	);
};
