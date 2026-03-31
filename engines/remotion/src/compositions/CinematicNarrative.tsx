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
	content?: string;
	text?: string;
	position?: string;
	zone?: string;
	role?: string;
	weight?: number;
	size?: string | number;
	color?: string;
	align?: 'left' | 'center' | 'right';
	durationInFrames?: number;
	startFrame?: number;
};

type RawAct = {
	name?: string;
	time?: string;
	text?: RawCue[] | null;
};

type CinematicNarrativeProps = {
	videoSrc?: string;
	resolveWord?: string;
	textCues?: RawCue[];
	narrative?: {
		acts?: RawAct[];
		resolveWord?: string;
	};
	renderManifest?: {
		videoSrc?: string;
		resolveWord?: string;
		textCues?: RawCue[];
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
		const rawCues = act.text ?? [];

		rawCues.forEach((cue, cueIndex) => {
			const cueStart =
				cue.startFrame ??
				(parseSeconds(cue.at) !== null ? Math.round((parseSeconds(cue.at) ?? 0) * fps) : actStartFrame);
			const nextCue = rawCues[cueIndex + 1];
			const nextStart =
				nextCue?.startFrame ??
				(parseSeconds(nextCue?.at) !== null ? Math.round((parseSeconds(nextCue?.at) ?? 0) * fps) : null);
			const defaultEnd = nextStart ?? actEndFrame;
			const duration = cue.durationInFrames ?? Math.max(Math.round(1.5 * fps), defaultEnd - cueStart - Math.round(0.2 * fps));
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
				role: inferRole(cue, act.name),
				weight: cue.weight,
				size: cue.size,
				color:
					cue.color === 'inverted'
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
	const directCues = props.textCues ?? manifest.textCues;

	if (directCues?.length) {
		return addResolveCueIfNeeded(
			flattenActs([{name: 'custom', text: directCues}], fps, durationInFrames),
			props.resolveWord ?? manifest.resolveWord,
			fps,
			durationInFrames,
		);
	}

	const acts = props.narrative?.acts ?? manifest.narrative?.acts ?? tokens.narrative.acts;
	const built = flattenActs(acts, fps, durationInFrames);
	const withResolve = addResolveCueIfNeeded(
		built,
		props.resolveWord ?? props.narrative?.resolveWord ?? manifest.resolveWord ?? manifest.narrative?.resolveWord,
		fps,
		durationInFrames,
	);

	return withResolve.length ? withResolve : cinematicDefaults(fps, durationInFrames);
};

export const CinematicNarrative: React.FC<CinematicNarrativeProps> = (props) => {
	const frame = useCurrentFrame();
	const {durationInFrames, fps} = useVideoConfig();
	const cues = useMemo(() => buildCues(props, fps, durationInFrames), [props, fps, durationInFrames]);
	const videoSrc = props.videoSrc ?? props.renderManifest?.videoSrc ?? staticFile('manim_base.mp4');
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
				<OffthreadVideo
					src={videoSrc}
					style={{width: '100%', height: '100%', objectFit: 'cover'}}
				/>
			</AbsoluteFill>

			{audioCfg?.enabled && audioCfg.bed ? (
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
