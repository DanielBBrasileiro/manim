import React, {useMemo} from 'react';
import {
	AbsoluteFill,
	Audio,
	Img,
	OffthreadVideo,
	Sequence,
	staticFile,
	useCurrentFrame,
	useVideoConfig,
} from 'remotion';
import {NarrativeText, type NarrativeRole, type NarrativeZone} from '../components/NarrativeText';
import {tokens} from '../theme';
import {Theme} from '../utils/theme';

type RawCue = {
	at?: string | number;
	at_sec?: number;
	content?: string;
	text?: string;
	position?: string;
	zone?: string;
	role?: string;
	weight?: number;
	size?: string | number;
	color?: string;
	color_state?: string;
	align?: 'left' | 'center' | 'right';
	durationInFrames?: number;
	duration_in_frames?: number;
	startFrame?: number;
	start_frame?: number;
};

type RawAct = {
	name?: string;
	id?: string;
	time?: string;
	start_sec?: number;
	end_sec?: number;
	text?: RawCue[] | null;
	text_cues?: RawCue[] | null;
};

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

export type CinematicNarrativeProps = {
	videoSrc?: string;
	resolveWord?: string;
	textCues?: RawCue[];
	frameOverride?: number;
	target?: string;
	targetId?: string;
	targetKind?: string;
	narrative?: {
		acts?: RawAct[];
		resolveWord?: string;
	};
	renderManifest?: {
		target?: string;
		targetId?: string;
		targetKind?: string;
		videoSrc?: string;
		video_src?: string;
		resolveWord?: string;
		resolve_word?: string;
		frameOverride?: number;
		stillFrame?: number;
		textCues?: RawCue[];
		text_cues?: RawCue[];
		acts?: RawAct[];
		audio?: {
			enabled?: boolean;
			bed?: string;
			gain?: number;
		};
		story_atoms?: StoryAtoms;
		bgSrc?: string;
		bg_src?: string;
		editorialLayout?: EditorialLayout;
		editorial_layout?: EditorialLayout;
		active_variant?: {
			id?: string;
			label?: string;
			style_pack_id?: string;
			composition_mode?: string;
		};
		narrative?: {
			acts?: RawAct[];
			resolveWord?: string;
		};
	};
};

type ResolvedCue = {
	id: string;
	text: string;
	from: number;
	durationInFrames: number;
	zone: NarrativeZone;
	role: NarrativeRole;
	weight?: number;
	size?: string | number;
	color?: string;
	align?: 'left' | 'center' | 'right';
};

type TargetVisualProfile = {
	panelInset: string;
	panelRadius: number;
	railTop: string;
	accentColor: string;
	curveStroke: string;
	curveOpacity: number;
	curveWidth: number;
	driftStrength: number;
	textMaxWidth: string;
	resolveMaxWidth: string;
	heroTitleSize: string;
	heroSubtitleSize: string;
	heroLockupOffset: string;
};

const getTargetVisualProfile = (targetId?: string): TargetVisualProfile => {
	switch (targetId) {
		case 'linkedin_feed_4_5':
			return {
				panelInset: '8% 7% 10% 7%',
				panelRadius: 40,
				railTop: '19%',
				accentColor: 'rgba(255,255,255,0.18)',
				curveStroke: 'rgba(255,255,255,0.72)',
				curveOpacity: 0.9,
				curveWidth: 2.4,
				driftStrength: 0,
				textMaxWidth: '74%',
				resolveMaxWidth: '84%',
				heroTitleSize: 'clamp(3rem, 7.8vw, 5.4rem)',
				heroSubtitleSize: 'clamp(1rem, 2vw, 1.25rem)',
				heroLockupOffset: '12%',
			};
		case 'linkedin_carousel_square':
			return {
				panelInset: '9% 8% 11% 8%',
				panelRadius: 34,
				railTop: '24%',
				accentColor: 'rgba(255,255,255,0.16)',
				curveStroke: 'rgba(245,245,245,0.5)',
				curveOpacity: 0.74,
				curveWidth: 1.9,
				driftStrength: 7,
				textMaxWidth: '74%',
				resolveMaxWidth: '84%',
				heroTitleSize: 'clamp(2.6rem, 6vw, 4rem)',
				heroSubtitleSize: 'clamp(0.95rem, 1.8vw, 1.1rem)',
				heroLockupOffset: '12%',
			};
		case 'youtube_essay_16_9':
			return {
				panelInset: '11% 8% 14% 8%',
				panelRadius: 28,
				railTop: '25%',
				accentColor: 'rgba(255,255,255,0.14)',
				curveStroke: 'rgba(255,255,255,0.42)',
				curveOpacity: 0.62,
				curveWidth: 1.8,
				driftStrength: 6,
				textMaxWidth: '62%',
				resolveMaxWidth: '76%',
				heroTitleSize: 'clamp(2.4rem, 4vw, 3.6rem)',
				heroSubtitleSize: 'clamp(0.9rem, 1.6vw, 1rem)',
				heroLockupOffset: '10%',
			};
		case 'youtube_thumbnail_16_9':
			return {
				panelInset: '8% 7% 12% 7%',
				panelRadius: 24,
				railTop: '21%',
				accentColor: 'rgba(255,255,255,0.18)',
				curveStroke: 'rgba(255,255,255,0.5)',
				curveOpacity: 0.8,
				curveWidth: 2.1,
				driftStrength: 7,
				textMaxWidth: '72%',
				resolveMaxWidth: '80%',
				heroTitleSize: 'clamp(2.4rem, 5vw, 3.6rem)',
				heroSubtitleSize: 'clamp(0.95rem, 1.7vw, 1.1rem)',
				heroLockupOffset: '10%',
			};
		default:
			return {
				panelInset: '9% 13% 21% 13%',
				panelRadius: 36,
				railTop: '22%',
				accentColor: 'rgba(255,106,106,0.18)',
				curveStroke: 'rgba(255,106,106,0.54)',
				curveOpacity: 0.78,
				curveWidth: 2.3,
				driftStrength: 11,
				textMaxWidth: '72%',
				resolveMaxWidth: '88%',
				heroTitleSize: 'clamp(3rem, 7.8vw, 5.4rem)',
				heroSubtitleSize: 'clamp(1rem, 2vw, 1.25rem)',
				heroLockupOffset: '12%',
			};
	}
};

const splitLockupTitle = (title?: string): string[] => {
	const words = String(title || '').trim().split(/\s+/).filter(Boolean);
	if (!words.length) {
		return ['Invisible', 'Architecture'];
	}
	if (words.length === 1) {
		return [words[0], ''];
	}
	const midpoint = Math.ceil(words.length / 2);
	return [words.slice(0, midpoint).join(' '), words.slice(midpoint).join(' ')];
};

const wordCap = (text?: string, maxWords = 2): string => {
	return String(text || '')
		.trim()
		.split(/\s+/)
		.filter(Boolean)
		.slice(0, maxWords)
		.join(' ');
};

const StaticBackdrop: React.FC<{frame: number; targetKind?: string; profile: TargetVisualProfile; bgSrc?: string | null; editorialLayout?: EditorialLayout}> = ({
	frame,
	targetKind,
	profile,
	bgSrc,
	editorialLayout,
}) => {
	const drift = Math.sin(frame / 24) * profile.driftStrength;
	const glow = Math.cos(frame / 38) * 0.06 + 0.18;
	const assetCrop = editorialLayout?.asset_crop ?? {};
	const objectPosition = assetCrop.object_position ?? '55% 42%';
	const veilOpacity = Number(assetCrop.veil_opacity ?? 0.2);
	const grayscale = Number(assetCrop.grayscale ?? 1.0);
	const contrast = Number(assetCrop.contrast ?? 1.12);

	return (
		<AbsoluteFill
			style={{
				background:
					targetKind === 'still'
						? 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.01) 24%, rgba(0,0,0,0) 52%), linear-gradient(180deg, #040404 0%, #0b0b0d 55%, #050505 100%)'
						: 'linear-gradient(180deg, #020202 0%, #090909 55%, #040404 100%)',
			}}
		>
			{bgSrc ? (
				<>
					<Img
						src={staticFile(bgSrc)}
						style={{
							position: 'absolute',
							inset: 0,
							width: '100%',
							height: '100%',
							objectFit: 'cover',
							objectPosition,
							filter: `grayscale(${grayscale}) contrast(${contrast}) brightness(0.7)`,
							opacity: 0.62,
						}}
					/>
					<div style={{position: 'absolute', inset: 0, background: '#000000', opacity: veilOpacity}} />
				</>
			) : null}
				<AbsoluteFill
					style={{
						transform: `translate(${drift}px, ${drift * 0.35}px)`,
						opacity: glow,
					}}
				>
					<div
						style={{
							position: 'absolute',
							inset: profile.panelInset,
							border: `1px solid ${profile.accentColor}`,
							borderRadius: profile.panelRadius,
						}}
					/>
					<div
						style={{
							position: 'absolute',
							left: '12%',
							right: '12%',
							top: profile.railTop,
							height: 1,
							background: profile.accentColor,
							opacity: 0.7,
						}}
					/>
					<svg
						viewBox="0 0 100 100"
						preserveAspectRatio="none"
						style={{
							position: 'absolute',
							inset: profile.panelInset,
							overflow: 'visible',
						}}
					>
						<path
							d="M 6 70 C 20 48, 32 36, 46 42 C 62 49, 72 60, 94 22"
							fill="none"
							stroke={profile.curveStroke}
							strokeWidth={profile.curveWidth}
							strokeLinecap="round"
							style={{opacity: profile.curveOpacity}}
						/>
					</svg>
				</AbsoluteFill>
			</AbsoluteFill>
	);
};

const boxStyle = (box: EditorialBox | undefined): React.CSSProperties => ({
	position: 'absolute',
	left: `${(((box?.x ?? 0) as number) * 100).toFixed(3)}%`,
	top: `${(((box?.y ?? 0) as number) * 100).toFixed(3)}%`,
	width: `${(((box?.w ?? 0) as number) * 100).toFixed(3)}%`,
	height: `${(((box?.h ?? 0) as number) * 100).toFixed(3)}%`,
});

const PosterHeroBackdrop: React.FC<{
	frame: number;
	profile: TargetVisualProfile;
	storyAtoms?: StoryAtoms;
	activeVariant?: {label?: string; composition_mode?: string};
	targetId?: string;
	bgSrc?: string | null;
	editorialLayout?: EditorialLayout;
}> = ({frame, profile, storyAtoms, activeVariant, targetId, bgSrc, editorialLayout}) => {
	const drift = Math.sin(frame / 52) * 1.1;
	const titleWord = wordCap(storyAtoms?.resolve_word ?? storyAtoms?.resolveWord ?? 'AIOX', 1) || 'AIOX';
	const accentLabel = wordCap(storyAtoms?.tagline ?? activeVariant?.label ?? 'Signal', 2);
	const isWide = targetId === 'youtube_thumbnail_16_9';
	const titleSize = isWide ? 'clamp(2rem, 5vw, 3.3rem)' : 'clamp(2.2rem, 6.2vw, 3.7rem)';
	const layout = editorialLayout ?? {};
	const eyebrowBox = layout.eyebrow_box ?? {x: isWide ? 0.08 : 0.11, y: 0.14, w: 0.26, h: 0.05};
	const titleBox = layout.title_box ?? {x: isWide ? 0.08 : 0.11, y: isWide ? 0.66 : 0.70, w: isWide ? 0.30 : 0.34, h: 0.16};
	const curveBox = layout.curve_box ?? {x: 0.08, y: 0.08, w: 0.84, h: 0.80};
	const accentAnchor = layout.accent_anchor ?? {x: isWide ? 0.92 : 0.90, y: isWide ? 0.16 : 0.14};
	const assetCrop = layout.asset_crop ?? {};
	const objectPosition = assetCrop.object_position ?? (isWide ? '64% 44%' : '58% 46%');
	const veilOpacity = Number(assetCrop.veil_opacity ?? 0.54);
	const grayscale = Number(assetCrop.grayscale ?? 1.0);
	const contrast = Number(assetCrop.contrast ?? 1.1);
	const titleOpacity = isWide ? 0.92 : 0.88;
	const eyebrowOpacity = 0.78;
	const curveOpacity = isWide ? 0.82 : 0.74;
	const dotRadius = isWide ? 1.35 : 1.18;

	return (
		<AbsoluteFill
			style={{
				background: '#000000',
			}}
		>
			{bgSrc && (
				<Img
					src={staticFile(bgSrc)}
					style={{
						position: 'absolute',
						inset: 0,
						width: '100%',
						height: '100%',
						objectFit: 'cover',
						objectPosition,
						filter: `grayscale(${grayscale}) contrast(${contrast}) brightness(0.58)`,
						opacity: 0.72,
					}}
				/>
			)}
			<div style={{position: 'absolute', inset: 0, background: '#000000', opacity: veilOpacity}} />
			<AbsoluteFill
				style={{
					transform: `translate(${drift}px, ${drift * 0.25}px)`,
				}}
			>
				<svg
					viewBox="0 0 100 100"
					preserveAspectRatio="none"
					style={{
						...boxStyle(curveBox),
						overflow: 'visible',
					}}
				>
					<path
						d={isWide ? 'M 8 74 C 22 66, 42 52, 58 44 C 74 36, 83 28, 92 16' : 'M 10 78 C 21 70, 38 57, 52 46 C 66 35, 79 24, 90 14'}
						fill="none"
						stroke="#FFFFFF"
						strokeWidth={isWide ? 1.45 : 1.55}
						strokeLinecap="round"
						vectorEffect="non-scaling-stroke"
						opacity={curveOpacity}
					/>
					<circle
						cx={Number(((accentAnchor.x ?? (isWide ? 0.92 : 0.90)) as number) * 100).toFixed(2)}
						cy={Number(((accentAnchor.y ?? (isWide ? 0.16 : 0.14)) as number) * 100).toFixed(2)}
						r={dotRadius}
						fill="#FF3366"
					/>
				</svg>
				<div
					style={{
						...boxStyle(eyebrowBox),
						color: '#FF3366',
						fontFamily: tokens.typography.fonts.narrative.family,
						opacity: eyebrowOpacity,
					}}
				>
					<div
						style={{
							fontSize: '0.58rem',
							fontWeight: 300,
							textTransform: 'uppercase',
							letterSpacing: '0.34em',
							lineHeight: 1.2,
						}}
					>
						{accentLabel || 'Signal'}
					</div>
				</div>
				<div
					style={{
						...boxStyle(titleBox),
						color: '#FFFFFF',
						fontFamily: tokens.typography.fonts.narrative.family,
						opacity: titleOpacity,
					}}
				>
					<div
						style={{
							fontSize: titleSize,
							fontWeight: 300,
							lineHeight: 0.92,
							letterSpacing: '-0.065em',
						}}
					>
						{titleWord}
					</div>
				</div>
			</AbsoluteFill>
		</AbsoluteFill>
	);
};

const parseSeconds = (value?: string | number | null): number | null => {
	if (typeof value === 'number' && Number.isFinite(value)) {
		return value;
	}

	if (typeof value !== 'string') {
		return null;
	}

	const match = value.match(/(\d+(?:\.\d+)?)/);
	return match ? Number(match[1]) : null;
};

const parseActWindow = (value?: string): {start: number | null; end: number | null} => {
	if (!value) {
		return {start: null, end: null};
	}

	const numbers = value.match(/\d+(?:\.\d+)?/g)?.map(Number) ?? [];
	return {
		start: numbers[0] ?? null,
		end: numbers[1] ?? null,
	};
};

const normalizeZone = (value?: string): NarrativeZone => {
	if (value === 'top' || value === 'top_zone') {
		return 'top';
	}
	if (value === 'bottom' || value === 'bottom_zone') {
		return 'bottom';
	}
	return 'center';
};

const inferRole = (cue: RawCue, actName?: string): NarrativeRole => {
	const explicitRole = cue.role?.toLowerCase();
	if (explicitRole === 'whisper' || explicitRole === 'statement' || explicitRole === 'climax' || explicitRole === 'resolve' || explicitRole === 'brand') {
		return explicitRole;
	}

	if (actName === 'resolution') {
		return normalizeZone(cue.position ?? cue.zone) === 'center' ? 'resolve' : 'brand';
	}

	if (normalizeZone(cue.position ?? cue.zone) === 'center') {
		return 'climax';
	}

	return cue.weight && cue.weight <= 300 ? 'whisper' : 'statement';
};

const cinematicDefaults = (fps: number, durationInFrames: number): ResolvedCue[] => {
	const resolutionStart = Math.round(durationInFrames * 0.8);
	return [
		{
			id: 'fallback-top',
			text: 'when systems',
			from: Math.round(5 * fps),
			durationInFrames: Math.round(1.7 * fps),
			zone: 'top',
			role: 'whisper',
			weight: 300,
		},
		{
			id: 'fallback-bottom',
			text: 'reach the limit',
			from: Math.round(7 * fps),
			durationInFrames: Math.round(1.8 * fps),
			zone: 'bottom',
			role: 'statement',
			weight: 300,
			align: 'right',
		},
		{
			id: 'fallback-center',
			text: 'we invent silence.',
			from: Math.round(9 * fps),
			durationInFrames: Math.round(1.6 * fps),
			zone: 'center',
			role: 'climax',
			weight: 500,
			color: Theme.colors.textPrimary,
		},
		{
			id: 'fallback-resolve',
			text: tokens.brand.identity.name,
			from: resolutionStart,
			durationInFrames: Math.round(2.2 * fps),
			zone: 'center',
			role: 'resolve',
		},
	];
};

const flattenActs = (acts: RawAct[] | undefined, fps: number, totalFrames: number): ResolvedCue[] => {
	const cues: ResolvedCue[] = [];
	const allActs = acts ?? [];

	allActs.forEach((act, actIndex) => {
		const actWindow = parseActWindow(act.time);
		const actStartFrame = actWindow.start !== null ? Math.round(actWindow.start * fps) : 0;
		const actEndFrame =
			actWindow.end !== null ? Math.round(actWindow.end * fps) : totalFrames;
		const fallbackStartFrame = act.start_sec !== undefined ? Math.round(act.start_sec * fps) : actStartFrame;
		const fallbackEndFrame = act.end_sec !== undefined ? Math.round(act.end_sec * fps) : actEndFrame;
		const rawCues = act.text ?? act.text_cues ?? [];

		rawCues.forEach((cue, cueIndex) => {
			const cueStart =
				cue.startFrame ??
				cue.start_frame ??
				(cue.at_sec !== undefined
					? Math.round(cue.at_sec * fps)
					: parseSeconds(cue.at) !== null
						? Math.round((parseSeconds(cue.at) ?? 0) * fps)
						: fallbackStartFrame);
			const nextCue = rawCues[cueIndex + 1];
			const nextStart =
				nextCue?.startFrame ??
				nextCue?.start_frame ??
				(nextCue?.at_sec !== undefined
					? Math.round(nextCue.at_sec * fps)
					: parseSeconds(nextCue?.at) !== null
						? Math.round((parseSeconds(nextCue?.at) ?? 0) * fps)
						: null);
			const defaultEnd = nextStart ?? fallbackEndFrame;
			const duration =
				cue.durationInFrames ??
				cue.duration_in_frames ??
				Math.max(Math.round(1.5 * fps), defaultEnd - cueStart - Math.round(0.2 * fps));
			const text = cue.content ?? cue.text;

			if (!text) {
				return;
			}

			cues.push({
				id: `${act.name ?? 'act'}-${actIndex}-${cueIndex}`,
				text,
				from: cueStart,
				durationInFrames: Math.max(Math.round(0.8 * fps), duration),
				zone: normalizeZone(cue.position ?? cue.zone),
				role: inferRole(cue, act.name ?? act.id),
				weight: cue.weight,
				size: cue.size,
				color:
					cue.color === 'inverted' || cue.color_state === 'inverted'
						? Theme.colors.textPrimary
						: cue.color,
				align: cue.align,
			});
		});
	});

	return cues.sort((a, b) => a.from - b.from);
};

const addResolveCueIfNeeded = (
	cues: ResolvedCue[],
	resolveWord: string | undefined,
	fps: number,
	durationInFrames: number,
): ResolvedCue[] => {
	if (cues.some((cue) => cue.role === 'resolve')) {
		return cues;
	}

	const resolveFrom = Math.round(durationInFrames * 0.82);
	return [
		...cues,
		{
			id: 'auto-resolve',
			text: resolveWord || tokens.brand.identity.name,
			from: resolveFrom,
			durationInFrames: Math.round(2.1 * fps),
			zone: 'center',
			role: 'resolve',
		},
	];
};

const buildCues = (
	props: CinematicNarrativeProps,
	fps: number,
	durationInFrames: number,
): ResolvedCue[] => {
	const manifest = props.renderManifest ?? {};
	const targetId = props.target ?? props.targetId ?? manifest.targetId ?? manifest.target;
	if (targetId === 'linkedin_feed_4_5' || targetId === 'youtube_thumbnail_16_9') {
		return [];
	}
	const directCues = props.textCues ?? manifest.textCues ?? manifest.text_cues;
	const resolveWord = props.resolveWord ?? manifest.resolveWord ?? manifest.resolve_word;

	if (directCues?.length) {
		return addResolveCueIfNeeded(
			flattenActs([{name: 'custom', text: directCues}], fps, durationInFrames),
			resolveWord,
			fps,
			durationInFrames,
		);
	}

	const acts =
		props.narrative?.acts ??
		manifest.acts ??
		manifest.narrative?.acts ??
		tokens.narrative.acts;
	const built = flattenActs(acts, fps, durationInFrames);
	const withResolve = addResolveCueIfNeeded(
		built,
		resolveWord ?? props.narrative?.resolveWord ?? manifest.narrative?.resolveWord,
		fps,
		durationInFrames,
	);

	return withResolve.length ? withResolve : cinematicDefaults(fps, durationInFrames);
};

export const CinematicNarrative: React.FC<CinematicNarrativeProps> = (props) => {
	const currentFrame = useCurrentFrame();
	const frame = props.frameOverride ?? currentFrame;
	const {durationInFrames, fps} = useVideoConfig();
	const targetId = props.target ?? props.targetId ?? props.renderManifest?.targetId;
	const targetKind = props.targetKind ?? props.renderManifest?.targetKind;
	const profile = useMemo(() => getTargetVisualProfile(targetId), [targetId]);
	const storyAtoms = props.renderManifest?.story_atoms;
	const bgSrc = props.renderManifest?.bgSrc ?? props.renderManifest?.bg_src;
	const editorialLayout = props.renderManifest?.editorialLayout ?? props.renderManifest?.editorial_layout;
	const activeVariant = props.renderManifest?.active_variant;
	const cues = useMemo(() => buildCues(props, fps, durationInFrames), [props, fps, durationInFrames]);
	const explicitVideoSrc = props.videoSrc ?? props.renderManifest?.videoSrc ?? props.renderManifest?.video_src;
	const shouldUseBaseVideo =
		targetId !== 'linkedin_feed_4_5' &&
		targetKind !== 'still' &&
		explicitVideoSrc !== null &&
		explicitVideoSrc !== '';
	const videoSrc = shouldUseBaseVideo ? explicitVideoSrc ?? staticFile('manim_base.mp4') : null;
	const audioCfg = props.renderManifest?.audio;

	const turbulenceStart = Math.round(durationInFrames * 0.25);
	const resolutionStart = Math.round(durationInFrames * 0.7);
	const breathe = Math.sin((frame / fps) * (Math.PI / 2)) * 0.002;
	const turbulenceDrift = frame >= turbulenceStart && frame < resolutionStart ? Math.sin(frame / 18) * 10 : 0;
	const turbulenceScale = frame >= turbulenceStart && frame < resolutionStart ? 1.012 : 1;
	const resolveSettle = frame >= resolutionStart ? 1 - Math.min(0.01, ((frame - resolutionStart) / (durationInFrames - resolutionStart || 1)) * 0.01) : 1;

	return (
		<AbsoluteFill style={{backgroundColor: Theme.colors.background}}>
			<AbsoluteFill
				style={{
					transform: `translateY(${turbulenceDrift}px) scale(${(1 + breathe) * turbulenceScale * resolveSettle})`,
				}}
			>
				{videoSrc ? (
					<OffthreadVideo
						src={videoSrc}
						style={{width: '100%', height: '100%', objectFit: 'cover'}}
					/>
				) : targetId === 'linkedin_feed_4_5' || targetId === 'youtube_thumbnail_16_9' ? (
					<PosterHeroBackdrop
						frame={frame}
						profile={profile}
						storyAtoms={storyAtoms}
						activeVariant={activeVariant}
						targetId={targetId}
						bgSrc={bgSrc}
						editorialLayout={editorialLayout}
					/>
				) : (
					<StaticBackdrop
						frame={frame}
						targetKind={targetKind}
						profile={profile}
						bgSrc={bgSrc}
						editorialLayout={editorialLayout}
					/>
				)}
			</AbsoluteFill>

			{videoSrc && audioCfg?.enabled && audioCfg.bed ? (
				<Audio src={staticFile(audioCfg.bed)} volume={audioCfg.gain ?? 0.18} />
			) : null}

			{cues.map((cue) => (
				<Sequence key={cue.id} from={cue.from} durationInFrames={cue.durationInFrames}>
					<NarrativeText
						text={cue.text}
						zone={cue.zone}
						role={cue.role}
						weight={cue.weight}
						size={cue.size}
						color={cue.color}
						align={cue.align}
						maxWidth={cue.role === 'resolve' ? profile.resolveMaxWidth : profile.textMaxWidth}
					/>
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
