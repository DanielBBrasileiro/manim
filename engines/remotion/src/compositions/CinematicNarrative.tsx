import React, {useMemo} from 'react';
import {
	AbsoluteFill,
	Audio,
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

const StaticBackdrop: React.FC<{frame: number; targetKind?: string; profile: TargetVisualProfile}> = ({
	frame,
	targetKind,
	profile,
}) => {
	const drift = Math.sin(frame / 24) * profile.driftStrength;
	const glow = Math.cos(frame / 38) * 0.06 + 0.18;

	return (
		<AbsoluteFill
			style={{
				background:
					targetKind === 'still'
						? 'radial-gradient(circle at 30% 30%, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.01) 24%, rgba(0,0,0,0) 52%), linear-gradient(180deg, #040404 0%, #0b0b0d 55%, #050505 100%)'
						: 'linear-gradient(180deg, #020202 0%, #090909 55%, #040404 100%)',
			}}
		>
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

const LinkedInFeedHeroBackdrop: React.FC<{
	frame: number;
	profile: TargetVisualProfile;
	storyAtoms?: StoryAtoms;
	activeVariant?: {label?: string; composition_mode?: string};
}> = ({frame, profile, storyAtoms, activeVariant}) => {
	const drift = Math.sin(frame / 42) * 2.2;
	const pulse = Math.sin(frame / 28) * 0.02 + 0.08;
	const lockupLines = splitLockupTitle(storyAtoms?.title ?? storyAtoms?.resolve_word ?? storyAtoms?.resolveWord);
	const eyebrow = String(storyAtoms?.tagline || activeVariant?.composition_mode || 'Poster first').trim();
	const resolveWord = String(storyAtoms?.resolve_word || storyAtoms?.resolveWord || 'AIOX').trim();

	return (
		<AbsoluteFill
			style={{
				background:
					'radial-gradient(circle at 18% 18%, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 24%, rgba(0,0,0,0) 50%), linear-gradient(180deg, #030303 0%, #090909 56%, #050505 100%)',
			}}
		>
			<AbsoluteFill
				style={{
					transform: `translate(${drift}px, ${drift * 0.25}px)`,
					opacity: 0.9,
				}}
			>
				<div
					style={{
						position: 'absolute',
						inset: profile.panelInset,
						border: `1px solid ${profile.accentColor}`,
						borderRadius: profile.panelRadius,
						background: 'linear-gradient(180deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%)',
						boxShadow: 'inset 0 0 0 1px rgba(255,255,255,0.02)',
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
						opacity: 0.76,
					}}
				/>
				<div
					style={{
						position: 'absolute',
						right: '8.5%',
						top: '12.5%',
						width: '28%',
						height: '42%',
						borderRadius: 999,
						border: '1px solid rgba(255,255,255,0.08)',
						transform: `scale(${1 + pulse})`,
						opacity: 0.55,
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
						d="M 8 72 C 20 60, 30 38, 45 44 C 61 49, 74 62, 92 24"
						fill="none"
						stroke={profile.curveStroke}
						strokeWidth={profile.curveWidth}
						strokeLinecap="round"
						style={{opacity: profile.curveOpacity}}
					/>
					<path
						d="M 14 78 C 31 67, 43 53, 54 54 C 69 56, 81 67, 92 41"
						fill="none"
						stroke="rgba(255,255,255,0.18)"
						strokeWidth={1.1}
						strokeLinecap="round"
					/>
				</svg>
				<div
					style={{
						position: 'absolute',
						left: profile.heroLockupOffset,
						top: '14%',
						maxWidth: '38%',
						color: Theme.colors.textPrimary,
						fontFamily: tokens.typography.fonts.narrative.family,
						letterSpacing: '-0.04em',
					}}
				>
					<div
						style={{
							fontSize: profile.heroSubtitleSize,
							fontWeight: 300,
							textTransform: 'uppercase',
							letterSpacing: '0.32em',
							opacity: 0.56,
							marginBottom: '0.7rem',
						}}
					>
						{eyebrow}
					</div>
					<div
						style={{
							fontSize: profile.heroTitleSize,
							fontWeight: 500,
							lineHeight: 0.95,
							maxWidth: '8ch',
						}}
					>
						{lockupLines[0]}
						<br />
						{lockupLines[1] || resolveWord}
					</div>
					<div
						style={{
							fontSize: '0.92rem',
							fontWeight: 400,
							letterSpacing: '0.28em',
							textTransform: 'uppercase',
							opacity: 0.42,
							marginTop: '1.1rem',
						}}
					>
						{resolveWord}
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
				) : targetId === 'linkedin_feed_4_5' ? (
					<LinkedInFeedHeroBackdrop frame={frame} profile={profile} storyAtoms={storyAtoms} activeVariant={activeVariant} />
				) : (
					<StaticBackdrop
						frame={frame}
						targetKind={targetKind}
						profile={profile}
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
