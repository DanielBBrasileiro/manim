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

const StaticBackdrop: React.FC<{frame: number; targetKind?: string; targetId?: string}> = ({
	frame,
	targetKind,
	targetId,
}) => {
	const drift = Math.sin(frame / 24) * 18;
	const glow = Math.cos(frame / 38) * 0.06 + 0.18;
	const wide = targetId === 'youtube_thumbnail_16_9' || targetId === 'youtube_essay_16_9';
	const accent = wide ? 'rgba(255,255,255,0.14)' : 'rgba(255,106,106,0.18)';

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
						inset: wide ? '14% 9% 20% 9%' : '10% 14% 22% 14%',
						border: `1px solid ${accent}`,
						borderRadius: wide ? 28 : 36,
					}}
				/>
				<div
					style={{
						position: 'absolute',
						left: wide ? '12%' : '18%',
						right: wide ? '12%' : '18%',
						top: wide ? '28%' : '22%',
						height: 1,
						background: accent,
						opacity: 0.7,
					}}
				/>
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
	const cues = useMemo(() => buildCues(props, fps, durationInFrames), [props, fps, durationInFrames]);
	const explicitVideoSrc = props.videoSrc ?? props.renderManifest?.videoSrc ?? props.renderManifest?.video_src;
	const useBaseVideo = explicitVideoSrc !== null && explicitVideoSrc !== '';
	const videoSrc = useBaseVideo ? explicitVideoSrc ?? staticFile('manim_base.mp4') : null;
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
				) : (
					<StaticBackdrop
						frame={frame}
						targetKind={props.targetKind ?? props.renderManifest?.targetKind}
						targetId={props.target ?? props.targetId ?? props.renderManifest?.targetId}
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
						maxWidth={cue.role === 'resolve' ? '88%' : '72%'}
					/>
				</Sequence>
			))}
		</AbsoluteFill>
	);
};
