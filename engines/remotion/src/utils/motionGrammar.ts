export type MotionTransitionType = 'cut' | 'crossfade' | 'push' | 'silence_bridge';
export type MotionRhythm = 'uniform' | 'accelerating' | 'decelerating' | 'syncopated' | 'custom';

export type MotionGrammarContract = {
	id: string;
	description?: string;
	principles: string[];
	timing: {
		minimum_hold_ms: number;
		maximum_simultaneous: number;
		silence_between_phrases_ms: [number, number];
	};
	rhythm: MotionRhythm;
	stagger: number[];
	transitions: {
		act_to_act: MotionTransitionType;
		within_act: MotionTransitionType;
	};
	camera: {
		default: string;
		climax_only?: string[];
		all_acts?: string[];
	};
};

const MOTION_GRAMMARS: Record<string, MotionGrammarContract> = {
	cinematic_restrained: {
		id: 'cinematic_restrained',
		description: 'Kurosawa-inspired. Long holds. Decisive movements.',
		principles: [
			'stillness is the default state',
			'motion is earned — only move when meaning demands it',
			'one element moves at a time',
		],
		timing: {
			minimum_hold_ms: 800,
			maximum_simultaneous: 1,
			silence_between_phrases_ms: [400, 1200],
		},
		rhythm: 'decelerating',
		stagger: [0, 3, 5, 8],
		transitions: {
			act_to_act: 'silence_bridge',
			within_act: 'cut',
		},
		camera: {
			default: 'static_breathe',
			climax_only: ['dramatic_zoom', 'track_subject'],
		},
	},
	kinetic_editorial: {
		id: 'kinetic_editorial',
		description: 'Stripe/Linear-inspired. Precise, rhythmic, information-rich.',
		principles: [
			'motion carries information',
			'stagger creates reading order',
			'spring physics everywhere — no linear interpolation',
		],
		timing: {
			minimum_hold_ms: 200,
			maximum_simultaneous: 3,
			silence_between_phrases_ms: [100, 400],
		},
		rhythm: 'syncopated',
		stagger: [0, 1, 1, 2, 1],
		transitions: {
			act_to_act: 'push',
			within_act: 'crossfade',
		},
		camera: {
			default: 'track_subject',
			all_acts: ['static_breathe', 'track_subject'],
		},
	},
};

const STYLE_PACK_TO_GRAMMAR: Record<string, string> = {
	silent_luxury: 'cinematic_restrained',
	kinetic_editorial: 'kinetic_editorial',
};

export const getMotionGrammar = (id?: string | null): MotionGrammarContract | null => {
	if (!id) {
		return null;
	}
	return MOTION_GRAMMARS[id] ?? null;
};

export const resolveMotionGrammar = ({
	explicitId,
	stylePackId,
}: {
	explicitId?: string | null;
	stylePackId?: string | null;
}): MotionGrammarContract | null => {
	if (explicitId) {
		return getMotionGrammar(explicitId);
	}
	if (stylePackId) {
		return getMotionGrammar(STYLE_PACK_TO_GRAMMAR[stylePackId] ?? null);
	}
	return null;
};
