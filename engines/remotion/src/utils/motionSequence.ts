import type {MotionGrammarContract, MotionRhythm, MotionTransitionType} from './motionGrammar';

type RawCueTiming = {
	id: string;
	from: number;
	durationInFrames: number;
	actId?: string;
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

/**
 * Resolve silence duration (ms) in a rhythm-aware way.
 * Instead of always using the midpoint of the grammar range, vary by
 * position and rhythm so restrained/kinetic grammars feel different
 * across the sequence — not just in magnitude but in shape.
 */
const resolveSilenceMs = (
	range: [number, number],
	rhythm: MotionRhythm,
	indexInAct: number,
	totalInAct: number,
): number => {
	const [min, max] = range;
	const progress = totalInAct > 1 ? indexInAct / (totalInAct - 1) : 0.5;

	if (rhythm === 'decelerating') {
		// Silence grows as sequence progresses — each pause is earned
		return Math.round(min + (max - min) * progress);
	}
	if (rhythm === 'accelerating') {
		// Silence shrinks — momentum builds
		return Math.round(max - (max - min) * progress);
	}
	if (rhythm === 'syncopated') {
		// Short–long alternation; odd indices get 35% of the gap added
		return Math.round(indexInAct % 2 === 0 ? min : min + (max - min) * 0.35);
	}
	// uniform: use midpoint (safe default, unchanged behaviour)
	return Math.round(min + (max - min) * 0.5);
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
	cue: {from: number};
	cueIndex: number;
	sequences: MotionSequence[];
	fps: number;
}): CueMotionSpec | null => {
	const sequence = sequences.find((item) => cue.from >= item.startFrame && cue.from < item.endFrame);
	if (!sequence) {
		return null;
	}
	// Rotate through available phrases so each cue in an act gets distinct
	// motion character when multiple phrases were defined.
	const phraseIndex = cueIndex % Math.max(sequence.phrases.length, 1);
	const phrase = sequence.phrases[phraseIndex];
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

export const scheduleCuesWithGrammar = <T extends RawCueTiming>({
	cues,
	grammar,
	fps,
	seed = 'default-seed',
}: {
	cues: T[];
	grammar: MotionGrammarContract | null;
	fps: number;
	seed?: string;
}): T[] => {
	if (!grammar) {
		return cues;
	}

	const minHoldFrames = Math.round((grammar.timing.minimum_hold_ms / 1000) * fps);
	const maxSimultaneous = grammar.timing.maximum_simultaneous;
	const [minSilenceMs, maxSilenceMs] = grammar.timing.silence_between_phrases_ms;
	const staggerProfile = grammar.stagger;

	// Group cues by act
	const cuesByAct: Record<string, T[]> = {};
	cues.forEach((cue) => {
		const actId = cue.actId ?? 'default';
		if (!cuesByAct[actId]) {
			cuesByAct[actId] = [];
		}
		cuesByAct[actId].push(cue);
	});

	const scheduledCues: T[] = [];

	Object.keys(cuesByAct).forEach((actId) => {
		const actCues = cuesByAct[actId].sort((a, b) => a.from - b.from);
		if (actCues.length === 0) {
			return;
		}

		const actStart = actCues[0].from;
		let currentSequenceTime = actStart;
		const activeCues: {endFrame: number}[] = [];

		actCues.forEach((cue, index) => {
			// Clear finished cues from active list
			while (activeCues.length > 0 && activeCues[0].endFrame <= currentSequenceTime) {
				activeCues.shift();
			}

			// Apply stagger if grammar allows simultaneity, otherwise force sequential
			const staggerIdx = index % Math.max(staggerProfile.length, 1);
			const staggerFrames = Math.round(staggerProfile[staggerIdx] * 2);

			let startTime = currentSequenceTime;

			if (activeCues.length >= maxSimultaneous) {
				// If we hit limits, we MUST wait for at least one to finish
				const earliestFinish = activeCues.shift();
				if (earliestFinish) {
					const silenceMs = resolveSilenceMs(
						[minSilenceMs, maxSilenceMs],
						grammar.rhythm,
						index,
						actCues.length,
					);
					const silenceFrames = Math.round((silenceMs / 1000) * fps);
					startTime = Math.max(startTime, earliestFinish.endFrame + silenceFrames);
				}
			} else if (index > 0 && maxSimultaneous > 1) {
				// We can have some overlap/stagger
				startTime = Math.max(actCues[index - 1].from + staggerFrames, currentSequenceTime);
			} else if (index > 0 && maxSimultaneous === 1) {
				// Force sequential with rhythm-aware silence
				const silenceMs = resolveSilenceMs(
					[minSilenceMs, maxSilenceMs],
					grammar.rhythm,
					index,
					actCues.length,
				);
				const silenceFrames = Math.round((silenceMs / 1000) * fps);
				startTime = Math.max(startTime, actCues[index - 1].from + actCues[index - 1].durationInFrames + silenceFrames);
			}

			// Ensure we don't start before the original intent if it was explicitly timed
			// (Though for this patch we want the grammar to take over mostly)
			// But we'll respect the act boundaries.

			const duration = Math.max(minHoldFrames, cue.durationInFrames);

			cue.from = startTime;
			cue.durationInFrames = duration;

			scheduledCues.push(cue);
			activeCues.push({endFrame: startTime + duration});
			activeCues.sort((a, b) => a.endFrame - b.endFrame);

			// Update sequence time only if we are moving forward in a way that affects the next cue
			currentSequenceTime = startTime;
		});
	});

	return scheduledCues.sort((a, b) => a.from - b.from);
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
	// Select phrase based on temporal position within the sequence window so
	// scene motion character evolves across a multi-phrase act.
	const sequenceDuration = Math.max(1, sequence.endFrame - sequence.startFrame);
	const frameInSequence = Math.max(0, frame - sequence.startFrame);
	const phraseIndex = Math.min(
		sequence.phrases.length - 1,
		Math.floor((frameInSequence / sequenceDuration) * sequence.phrases.length),
	);
	const phrase = sequence.phrases[phraseIndex];
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
