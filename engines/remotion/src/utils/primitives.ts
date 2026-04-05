/**
 * Simple deterministic PRNG based on a string seed.
 * Uses a basic LCG (Linear Congruential Generator) algorithm.
 */
export class DeterministicPRNG {
	private state: number;

	constructor(seed: string) {
		this.state = this.hash(seed);
	}

	private hash(s: string): number {
		let h = 0x811c9dc5;
		for (let i = 0; i < s.length; i++) {
			h ^= s.charCodeAt(i);
			h = Math.imul(h, 0x01000193);
		}
		return h >>> 0;
	}

	next(): number {
		this.state = (Math.imul(this.state, 1664525) + 1013904223) >>> 0;
		return this.state / 0xffffffff;
	}

	nextRange(min: number, max: number): number {
		return min + this.next() * (max - min);
	}

	pick<T>(array: T[]): T {
		return array[Math.floor(this.next() * array.length)];
	}
}

export type PrimitiveType = 'arc' | 'ribbon' | 'spline' | 'orbit';

export interface PrimitiveParams {
	type: PrimitiveType;
	seed: string;
	amplitude: number;
	tension: number;
	thickness: number;
	opacity: number;
	color?: string;
}

export interface RenderedPrimitive {
	path: string;
	path2?: string; // For ribbons
	style: React.CSSProperties;
}

export const resolvePrimitive = (
	params: Partial<PrimitiveParams>,
	baseSeed: string
): RenderedPrimitive => {
	const seed = `${baseSeed}-${params.seed || 'default'}`;
	const rng = new DeterministicPRNG(seed);

	const type = params.type || rng.pick(['arc', 'ribbon', 'spline', 'orbit']);
	const amplitude = params.amplitude ?? rng.nextRange(0.4, 0.9);
	const tension = params.tension ?? rng.nextRange(0.3, 0.8);
	const thickness = params.thickness ?? rng.nextRange(1.2, 3.0);
	const opacity = params.opacity ?? rng.nextRange(0.6, 0.9);

	switch (type) {
		case 'arc':
			return generateArc(rng, amplitude, tension);
		case 'ribbon':
			return generateRibbon(rng, amplitude, tension, thickness);
		case 'spline':
			return generateSpline(rng, amplitude, tension);
		case 'orbit':
			return generateOrbit(rng, amplitude, tension);
		default:
			return generateArc(rng, amplitude, tension);
	}
};

const generateArc = (rng: DeterministicPRNG, _amp: number, _ten: number): RenderedPrimitive => {
	// Simple arc from left-ish to right-ish
	const x1 = rng.nextRange(5, 15);
	const y1 = rng.nextRange(20, 80);
	const x2 = rng.nextRange(85, 95);
	const y2 = rng.nextRange(20, 80);
	const cx = rng.nextRange(30, 70);
	const cy = rng.nextRange(0, 100);

	return {
		path: `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`,
		style: {},
	};
};

const generateRibbon = (rng: DeterministicPRNG, _amp: number, _ten: number, thickness: number): RenderedPrimitive => {
	const x1 = rng.nextRange(5, 20);
	const y1 = rng.nextRange(30, 70);
	const x2 = rng.nextRange(80, 95);
	const y2 = rng.nextRange(30, 70);
	const cx = rng.nextRange(35, 65);
	const cy = rng.nextRange(10, 90);

	const offset = thickness * 2.5;

	return {
		path: `M ${x1} ${y1} Q ${cx} ${cy} ${x2} ${y2}`,
		path2: `M ${x1} ${y1 + offset} Q ${cx} ${cy + offset} ${x2} ${y2 + offset}`,
		style: {},
	};
};

const generateSpline = (rng: DeterministicPRNG, _amp: number, _ten: number): RenderedPrimitive => {
	const x1 = rng.nextRange(5, 15);
	const y1 = rng.nextRange(60, 90);
	const x2 = rng.nextRange(85, 95);
	const y2 = rng.nextRange(10, 40);

	const c1x = rng.nextRange(20, 40);
	const c1y = rng.nextRange(0, 100);
	const c2x = rng.nextRange(60, 80);
	const c2y = rng.nextRange(0, 100);

	return {
		path: `M ${x1} ${y1} C ${c1x} ${c1y}, ${c2x} ${c2y}, ${x2} ${y2}`,
		style: {},
	};
};

const generateOrbit = (rng: DeterministicPRNG, _amp: number, _ten: number): RenderedPrimitive => {
	const cx = rng.nextRange(40, 60);
	const cy = rng.nextRange(40, 60);
	const rx = rng.nextRange(30, 45);
	const ry = rng.nextRange(20, 35);
	const startAngle = rng.nextRange(0, Math.PI);
	const endAngle = startAngle + rng.nextRange(Math.PI * 0.5, Math.PI * 1.5);

	const x1 = cx + rx * Math.cos(startAngle);
	const y1 = cy + ry * Math.sin(startAngle);
	const x2 = cx + rx * Math.cos(endAngle);
	const y2 = cy + ry * Math.sin(endAngle);

	const largeArcFlag = endAngle - startAngle <= Math.PI ? 0 : 1;

	return {
		path: `M ${x1} ${y1} A ${rx} ${ry} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
		style: {},
	};
};
