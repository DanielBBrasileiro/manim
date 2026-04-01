import type {MotionGrammarContract, MotionRhythm, MotionTransitionType} from './motionGrammar';

type RawCue = {
	from: number;
	durationInFrames: number;
};

type RawAct = {
	name?: string;
	id?: string;
	time?: string;
	start_sec?: number;
	end_sec?: number;
};

type MotionAtom = {
	property: 'position' | 'scale' | 'opacity' | 'rotation' | 'skew' | 'blur' | 'clip';
	from: number;
	to: number;
	easing: string;
	duration_ms: number;
	delay_ms: number;
	spring: {stiffness: number; damping: number; mass: number} | null;
};

export type MotionPhrase = {
	id: string;
	emphasis: 'low' | 'medium' | 'high';
	anticipation: MotionAtom;
	action: MotionAtom;
	followThrough: MotionAtom;
	recovery_ms: number;
};

export type MotionSequence = {
	actId: string;
	startFrame: number;
	endFrame: number;
	phrases: MotionPhrase[];
	rhythm: MotionRhythm;
	staggerProfile: number[];
	breathPoints: number[];
	transitionTo: MotionTransitionType;
	withinActTransition: MotionTransitionType;
	minimumHoldFrames: number;
	maximumSimultaneous: number;
	cameraMode: string;
};

export type CueMotionSpec = {
	anticipationFrames: number;
	actionFrames: number;
	followThroughFrames: number;
	recoveryFrames: number;
	staggerDelayFrames: number;
	emphasis: 'low' | 'medium' | 'high';
	spring: {stiffness: number; damping: number; mass: number};
	transitionHint: MotionTransitionType;
};

type RenderManifestLike = {
	style_pack?: string;
	motion_grammar?: string;
	act_quality_profile?: Record<string, {
		breath_points?: number[];
		silence_ratio?: number;
		motion_sequence?: {
			rhythm?: MotionRhythm;
			stagger_profile?: number[];
			transition_to?: MotionTransitionType;
			within_act_transition?: MotionTransitionType;
			minimum_hold_ms?: number;
			maximum_simultaneous?: number;
			camera?: {default?: string};
			phrases?: Array<{
				id?: string;
				emphasis?: 'low' | 'medium' | 'high';
				anticipation?: MotionAtom;
				action?: MotionAtom;
				follow_through?: MotionAtom;
				recovery_ms?: number;
			}>;
		};
		rhythm?: MotionRhythm;
		stagger_profile?: number[];
		transition_to?: MotionTransitionType;
		minimum_hold_ms?: number;
	}>;
	acts?: RawAct[];
	narrative?: {acts?: RawAct[]};
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

const rhythmMultiplier = (rhythm: MotionRhythm, actIndex: number, totalActs: number): number => {
	if (totalActs <= 1) {
		return 1;
	}
	const progress = actIndex / Math.max(totalActs - 1, 1);
	if (rhythm === 'decelerating') {
		return 1 + 0.45 * progress;
	}
	if (rhythm === 'accelerating') {
		return Math.max(0.7, 1 - 0.28 * progress);
	}
	if (rhythm === 'syncopated') {
		return [1, 0.82, 1.12][actIndex % 3];
	}
	return 1;
};

const defaultPhrase = (
	actId: string,
	grammar: MotionGrammarContract,
	actIndex: number,
	totalActs: number,
): MotionPhrase => {
	const emphasis = actId === 'genesis' ? 'low' : actId === 'turbulence' ? 'high' : 'medium';
	const multiplier = rhythmMultiplier(grammar.rhythm, actIndex, totalActs);
	const actionMs = Math.max(220, Math.round(grammar.timing.minimum_hold_ms * 0.95 * multiplier));
	const anticipationMs = Math.max(100, Math.round(grammar.timing.minimum_hold_ms * 0.35 * multiplier));
	const followMs = Math.max(140, Math.round(grammar.timing.minimum_hold_ms * 0.45 * multiplier));

	return {
		id: `${actId}_primary`,
		emphasis,
		anticipation: {
			property: 'opacity',
			from: 0,
			to: 0.2,
			easing: 'ease_out',
			duration_ms: anticipationMs,
			delay_ms: 0,
			spring: null,
		},
		action: {
			property: 'position',
			from: emphasis === 'high' ? 28 : 18,
			to: 0,
			easing: 'spring',
			duration_ms: actionMs,
			delay_ms: anticipationMs,
			spring: {
				stiffness: emphasis === 'high' ? 118 : emphasis === 'low' ? 82 : 96,
				damping: emphasis === 'high' ? 14 : emphasis === 'low' ? 20 : 17,
				mass: emphasis === 'high' ? 0.86 : emphasis === 'low' ? 1.05 : 0.95,
			},
		},
		followThrough: {
			property: 'scale',
			from: emphasis === 'high' ? 0.96 : 0.985,
			to: 1,
			easing: 'ease_out',
			duration_ms: followMs,
			delay_ms: anticipationMs + actionMs,
			spring: null,
		},
		recovery_ms: grammar.timing.silence_between_phrases_ms[1],
	};
};

export const buildMotionSequences = ({
	manifest,
	grammar,
	fps,
	durationInFrames,
}: {
	manifest: RenderManifestLike;
	grammar: MotionGrammarContract | null;
	fps: number;
	durationInFrames: number;
}): MotionSequence[] => {
	if (!grammar) {
		return [];
	}

	const acts = manifest.acts ?? manifest.narrative?.acts ?? [];
	if (!acts.length) {
		return [];
	}
	const actQuality = manifest.act_quality_profile ?? {};

	return acts.map((act, index) => {
		const actId = String(act.id ?? act.name ?? `act_${index}`);
		const window = parseActWindow(act.time);
		const startFrame =
			act.start_sec !== undefined
				? Math.round(act.start_sec * fps)
				: window.start !== null
					? Math.round(window.start * fps)
					: Math.round((durationInFrames / Math.max(acts.length, 1)) * index);
		const endFrame =
			act.end_sec !== undefined
				? Math.round(act.end_sec * fps)
				: window.end !== null
					? Math.round(window.end * fps)
					: index === acts.length - 1
						? durationInFrames
						: Math.round((durationInFrames / Math.max(acts.length, 1)) * (index + 1));
		const quality = actQuality[actId] ?? {};
		const motionSequence = quality.motion_sequence ?? {};
		const phrases = Array.isArray(motionSequence.phrases) && motionSequence.phrases.length
			? motionSequence.phrases.map((phrase, phraseIndex) => ({
					id: String(phrase.id ?? `${actId}_${phraseIndex}`),
					emphasis: phrase.emphasis ?? (actId === 'turbulence' ? 'high' : actId === 'genesis' ? 'low' : 'medium'),
					anticipation: phrase.anticipation ?? defaultPhrase(actId, grammar, index, acts.length).anticipation,
					action: phrase.action ?? defaultPhrase(actId, grammar, index, acts.length).action,
					followThrough: phrase.follow_through ?? defaultPhrase(actId, grammar, index, acts.length).followThrough,
					recovery_ms: phrase.recovery_ms ?? defaultPhrase(actId, grammar, index, acts.length).recovery_ms,
				}))
			: [defaultPhrase(actId, grammar, index, acts.length)];
		return {
			actId,
			startFrame,
			endFrame,
			phrases,
			rhythm: motionSequence.rhythm ?? quality.rhythm ?? grammar.rhythm,
			staggerProfile: motionSequence.stagger_profile ?? quality.stagger_profile ?? grammar.stagger,
			breathPoints: quality.breath_points ?? [],
			transitionTo: motionSequence.transition_to ?? quality.transition_to ?? grammar.transitions.act_to_act,
			withinActTransition: motionSequence.within_act_transition ?? grammar.transitions.within_act,
			minimumHoldFrames: Math.max(1, Math.round((motionSequence.minimum_hold_ms ?? quality.minimum_hold_ms ?? grammar.timing.minimum_hold_ms) / 1000 * fps)),
			maximumSimultaneous: motionSequence.maximum_simultaneous ?? grammar.timing.maximum_simultaneous,
			cameraMode: motionSequence.camera?.default ?? grammar.camera.default,
		};
	});
};

export const resolveCueMotionSpec = ({
	cue,
	cueIndex,
	sequences,
	fps,
}: {
	cue: RawCue;
	cueIndex: number;
	sequences: MotionSequence[];
	fps: number;
}): CueMotionSpec | null => {
	const sequence = sequences.find((item) => cue.from >= item.startFrame && cue.from < item.endFrame);
	if (!sequence) {
		return null;
	}
	const phrase = sequence.phrases[0];
	const staggerUnit = sequence.staggerProfile[cueIndex % Math.max(sequence.staggerProfile.length, 1)] ?? 0;
	return {
		anticipationFrames: Math.max(0, Math.round((phrase.anticipation.duration_ms / 1000) * fps)),
		actionFrames: Math.max(2, Math.round((phrase.action.duration_ms / 1000) * fps)),
		followThroughFrames: Math.max(2, Math.round((phrase.followThrough.duration_ms / 1000) * fps)),
		recoveryFrames: Math.max(0, Math.round((phrase.recovery_ms / 1000) * fps)),
		staggerDelayFrames: Math.max(0, Math.round(staggerUnit * 2)),
		emphasis: phrase.emphasis,
		spring: phrase.action.spring ?? {stiffness: 90, damping: 18, mass: 0.95},
		transitionHint: sequence.withinActTransition,
	};
};

const inBreathHold = (frame: number, sequence: MotionSequence): boolean =>
	sequence.breathPoints.some((point) => Math.abs(frame - point) <= sequence.minimumHoldFrames / 2);

export const resolveSceneMotionState = ({
	frame,
	sequences,
	grammar,
}: {
	frame: number;
	sequences: MotionSequence[];
	grammar: MotionGrammarContract | null;
}): {translateX: number; translateY: number; scale: number; opacity: number} | null => {
	if (!grammar || !sequences.length) {
		return null;
	}

	const sequence =
		sequences.find((item) => frame >= item.startFrame && frame < item.endFrame) ??
		sequences[sequences.length - 1];
	const phrase = sequence.phrases[0];
	const emphasisFactor = phrase.emphasis === 'high' ? 1.25 : phrase.emphasis === 'low' ? 0.72 : 1.0;
	const baseTranslateY = Math.sin(frame / (sequence.rhythm === 'syncopated' ? 14 : 22)) * 8 * emphasisFactor;
	const baseTranslateX =
		sequence.cameraMode === 'track_subject'
			? Math.sin(frame / 31) * 10 * emphasisFactor
			: 0;
	const baseScale =
		sequence.rhythm === 'decelerating'
			? 1 + Math.sin(frame / 42) * 0.004
			: sequence.rhythm === 'syncopated'
				? 1 + Math.sin(frame / 16) * 0.006
				: 1 + Math.sin(frame / 28) * 0.003;
	const nextBoundary = sequence.endFrame - frame;

	if (inBreathHold(frame, sequence)) {
		return {
			translateX: baseTranslateX * 0.15,
			translateY: baseTranslateY * 0.15,
			scale: 1,
			opacity: 1,
		};
	}

	if (nextBoundary >= 0 && nextBoundary <= Math.max(6, sequence.minimumHoldFrames)) {
		const progress = 1 - nextBoundary / Math.max(1, sequence.minimumHoldFrames);
		if (sequence.transitionTo === 'crossfade') {
			return {
				translateX: baseTranslateX,
				translateY: baseTranslateY,
				scale: baseScale,
				opacity: 1 - progress * 0.12,
			};
		}
		if (sequence.transitionTo === 'push') {
			return {
				translateX: baseTranslateX + progress * 42,
				translateY: baseTranslateY,
				scale: baseScale,
				opacity: 1,
			};
		}
		if (sequence.transitionTo === 'silence_bridge') {
			return {
				translateX: baseTranslateX * 0.08,
				translateY: baseTranslateY * 0.08,
				scale: 1,
				opacity: 1,
			};
		}
	}

	return {
		translateX: baseTranslateX,
		translateY: baseTranslateY,
		scale: baseScale,
		opacity: 1,
	};
};
