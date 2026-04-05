import type React from 'react';

type LayoutBox = {
	x?: number;
	y?: number;
	w?: number;
	h?: number;
};

type EditorialLayout = {
	family?: string;
	safe_margin_px?: number;
	hero_zone?: LayoutBox;
	support_zone?: LayoutBox;
	empty_zone?: LayoutBox;
	focal_zone?: LayoutBox;
	eyebrow_box?: LayoutBox;
	title_box?: LayoutBox;
	curve_box?: LayoutBox;
	accent_anchor?: {x?: number; y?: number};
	asset_crop?: {
		object_position?: string;
		veil_opacity?: number;
		grayscale?: number;
		contrast?: number;
	};
};

type StillFamilyContract = {
	id: string;
	composition_grid: string;
	grammar?: string;
	negative_space_min: number;
};

type StylePackContract = {
	negative_space_target: number;
};

export type ResolvedStillLayout = {
	safeZonePx: number;
	heroZone: Required<LayoutBox>;
	supportZone: Required<LayoutBox>;
	emptyZone: Required<LayoutBox>;
	focalZone: Required<LayoutBox>;
	titleBox: Required<LayoutBox>;
	eyebrowBox: Required<LayoutBox>;
	curveBox: Required<LayoutBox>;
	accentAnchor: {x: number; y: number};
	assetCrop: {
		object_position: string;
		veil_opacity: number;
		grayscale: number;
		contrast: number;
	};
};

const box = (fallback: Required<LayoutBox>, value?: LayoutBox): Required<LayoutBox> => ({
	x: value?.x ?? fallback.x,
	y: value?.y ?? fallback.y,
	w: value?.w ?? fallback.w,
	h: value?.h ?? fallback.h,
});

export const boxStyle = (value: Required<LayoutBox>): React.CSSProperties => ({
	position: 'absolute',
	left: `${(value.x * 100).toFixed(3)}%`,
	top: `${(value.y * 100).toFixed(3)}%`,
	width: `${(value.w * 100).toFixed(3)}%`,
	height: `${(value.h * 100).toFixed(3)}%`,
});

/**
 * Scale factor derived from negative_space_target.
 * At ns=0.50 (baseline), returns 0. At ns=0.35 (dense), returns ~-0.15.
 * At ns=0.72 (airy), returns ~+0.22.  Clamped to avoid collapse.
 */
const spaceScale = (ns: number): number => Math.max(-0.18, Math.min(0.26, ns - 0.50));

/**
 * Shrinks a zone's width to create more negative space, keeping it
 * anchored to the same left edge.
 */
const shrinkW = (base: number, delta: number): number =>
	Math.max(0.14, Math.min(0.60, base - delta));

const resolveGrammarDefaults = (
	familyId: string,
	grammar: string,
	ns: number,
	width: number,
	height: number,
) => {
	switch (familyId) {
		case 'centered_resolve':
			return {
				heroZone: {x: 0.24, y: 0.40, w: 0.52, h: 0.24},
				supportZone: {x: 0.28, y: 0.14, w: 0.44, h: 0.08},
				emptyZone: {x: 0.14, y: 0.18, w: 0.72, h: 0.56},
				focalZone: {x: 0.12, y: 0.12, w: 0.76, h: 0.72},
				curveBox: {x: 0.18, y: 0.22, w: 0.64, h: 0.44},
				titleBox: {x: 0.20, y: 0.46, w: 0.60, h: 0.16},
				eyebrowBox: {x: 0.28, y: 0.16, w: 0.44, h: 0.05},
				accentAnchor: {x: 0.50, y: 0.10},
				assetCrop: {
					object_position: '50% 46%',
					veil_opacity: 0.42,
					grayscale: 1,
					contrast: 1.12,
				},
			};
		case 'asymmetric_corner':
			return {
				heroZone: {x: 0.10, y: 0.62, w: 0.42, h: 0.22},
				supportZone: {x: 0.60, y: 0.10, w: 0.28, h: 0.10},
				emptyZone: {x: 0.10, y: 0.12, w: 0.34, h: 0.34},
				focalZone: {x: 0.08, y: 0.08, w: 0.84, h: 0.82},
				curveBox: {x: 0.20, y: 0.16, w: 0.64, h: 0.60},
				titleBox: {x: 0.10, y: 0.64, w: 0.40, h: 0.20},
				eyebrowBox: {x: 0.60, y: 0.10, w: 0.26, h: 0.08},
				accentAnchor: {x: 0.90, y: 0.18},
				assetCrop: {
					object_position: '66% 34%',
					veil_opacity: 0.30,
					grayscale: 1,
					contrast: 1.18,
				},
			};
		case 'architectural_grid':
			return {
				heroZone: {x: 0.10, y: 0.56, w: shrinkW(0.32, ns * 0.3), h: 0.18},
				supportZone: {x: 0.10, y: 0.12, w: shrinkW(0.18, ns * 0.18), h: 0.06},
				emptyZone: {x: 0.58, y: 0.10, w: 0.24, h: 0.72},
				focalZone: {x: 0.08, y: 0.08, w: 0.84, h: 0.84},
				curveBox: {x: 0.12, y: 0.18, w: 0.70, h: 0.48},
				titleBox: {x: 0.10, y: 0.58, w: shrinkW(0.30, ns * 0.3), h: 0.16},
				eyebrowBox: {x: 0.10, y: 0.12, w: shrinkW(0.18, ns * 0.18), h: 0.05},
				accentAnchor: {x: 0.84, y: 0.22},
				assetCrop: {
					object_position: width > height ? '58% 44%' : '54% 38%',
					veil_opacity: 0.28,
					grayscale: 1,
					contrast: 1.16,
				},
			};
		default:
			break;
	}

	switch (grammar) {
		case 'monumental':
			return {
				heroZone: {x: 0.1, y: 0.70, w: shrinkW(0.35, ns * 0.4), h: 0.15},
				supportZone: {x: 0.1, y: 0.14, w: shrinkW(0.22, ns * 0.3), h: 0.06},
				emptyZone: {x: 0.1, y: 0.20, w: 0.8, h: 0.45},
				focalZone: {x: 0.08, y: 0.08, w: 0.84, h: 0.84},
				curveBox: {x: 0.08, y: 0.08, w: 0.84, h: 0.84},
				titleBox: {x: 0.10, y: 0.72, w: shrinkW(0.35, ns * 0.4), h: 0.15},
				eyebrowBox: {x: 0.10, y: 0.14, w: shrinkW(0.22, ns * 0.3), h: 0.05},
				accentAnchor: {x: 0.90, y: 0.14},
				assetCrop: {
					object_position: '50% 40%',
					veil_opacity: 0.55,
					grayscale: 1,
					contrast: 1.1,
				},
			};
		case 'centered':
			return {
				heroZone: {x: 0.25, y: 0.45, w: 0.5, h: 0.2},
				supportZone: {x: 0.25, y: 0.15, w: 0.5, h: 0.08},
				emptyZone: {x: 0.1, y: 0.1, w: 0.15, h: 0.8},
				focalZone: {x: 0.1, y: 0.1, w: 0.8, h: 0.8},
				curveBox: {x: 0.1, y: 0.1, w: 0.8, h: 0.8},
				titleBox: {x: 0.2, y: 0.47, w: 0.6, h: 0.18},
				eyebrowBox: {x: 0.3, y: 0.15, w: 0.4, h: 0.05},
				accentAnchor: {x: 0.5, y: 0.08},
				assetCrop: {
					object_position: '50% 50%',
					veil_opacity: 0.4,
					grayscale: 1,
					contrast: 1.2,
				},
			};
		case 'asymmetric':
			return {
				heroZone: {x: 0.08, y: 0.65, w: 0.45, h: 0.25},
				supportZone: {x: 0.60, y: 0.10, w: 0.32, h: 0.12},
				emptyZone: {x: 0.10, y: 0.10, w: 0.40, h: 0.45},
				focalZone: {x: 0.06, y: 0.06, w: 0.88, h: 0.88},
				curveBox: {x: 0.06, y: 0.06, w: 0.88, h: 0.88},
				titleBox: {x: 0.08, y: 0.67, w: 0.42, h: 0.20},
				eyebrowBox: {x: 0.62, y: 0.10, w: 0.30, h: 0.08},
				accentAnchor: {x: 0.92, y: 0.18},
				assetCrop: {
					object_position: '65% 35%',
					veil_opacity: 0.32,
					grayscale: 1,
					contrast: 1.18,
				},
			};
		case 'editorial_grid':
		default:
			return {
				heroZone: {x: 0.08, y: 0.50, w: shrinkW(0.42, ns * 0.6), h: 0.26},
				supportZone: {x: 0.08, y: 0.12, w: shrinkW(0.30, ns * 0.4), h: 0.12},
				emptyZone: {x: Math.min(0.68, 0.56 - ns * 0.4), y: 0.10, w: Math.max(0.20, 0.28 + ns * 0.5), h: 0.46},
				focalZone: {x: 0.06, y: 0.08, w: Math.max(0.60, 0.88 - ns * 0.3), h: 0.82},
				curveBox: {x: 0.06, y: 0.08, w: Math.max(0.60, 0.88 - ns * 0.3), h: 0.78},
				titleBox: {x: 0.08, y: 0.52, w: shrinkW(0.40, ns * 0.6), h: 0.22},
				eyebrowBox: {x: 0.08, y: 0.12, w: shrinkW(0.30, ns * 0.4), h: 0.06},
				accentAnchor: {x: 0.90, y: 0.16},
				assetCrop: {
					object_position: width > height ? '62% 44%' : '56% 42%',
					veil_opacity: 0.36,
					grayscale: 1,
					contrast: 1.16,
				},
			};
	}
};

export const resolveStillLayout = ({
	editorialLayout,
	stillFamily,
	stylePack,
	width,
	height,
}: {
	editorialLayout?: EditorialLayout;
	stillFamily?: StillFamilyContract | null;
	stylePack?: StylePackContract | null;
	width: number;
	height: number;
}): ResolvedStillLayout => {
	const negativeSpaceTarget = Math.max(
		stylePack?.negative_space_target ?? 0,
		stillFamily?.negative_space_min ?? 0.4,
	);
	
	const ns = spaceScale(negativeSpaceTarget);
	const familyId = stillFamily?.id ?? 'poster_minimal';
	const grammar = stillFamily?.grammar ?? (familyId === 'poster_minimal' ? 'monumental' : 'editorial_grid');

	const defaults = resolveGrammarDefaults(familyId, grammar, ns, width, height);

	return {
		safeZonePx:
			editorialLayout?.safe_margin_px ??
			Math.max(64, Math.round(Math.min(width, height) * (0.06 + ns * 0.02))),
		heroZone: box(defaults.heroZone, editorialLayout?.hero_zone ?? editorialLayout?.title_box),
		supportZone: box(defaults.supportZone, editorialLayout?.support_zone ?? editorialLayout?.eyebrow_box),
		emptyZone: box(defaults.emptyZone, editorialLayout?.empty_zone),
		focalZone: box(defaults.focalZone, editorialLayout?.focal_zone),
		titleBox: box(defaults.titleBox, editorialLayout?.title_box ?? editorialLayout?.hero_zone),
		eyebrowBox: box(defaults.eyebrowBox, editorialLayout?.eyebrow_box ?? editorialLayout?.support_zone),
		curveBox: box(defaults.curveBox, editorialLayout?.curve_box ?? editorialLayout?.focal_zone),
		accentAnchor: {
			x: editorialLayout?.accent_anchor?.x ?? defaults.accentAnchor.x,
			y: editorialLayout?.accent_anchor?.y ?? defaults.accentAnchor.y,
		},
		assetCrop: {
			object_position:
				editorialLayout?.asset_crop?.object_position ?? defaults.assetCrop.object_position,
			veil_opacity:
				Number(editorialLayout?.asset_crop?.veil_opacity ?? defaults.assetCrop.veil_opacity),
			grayscale: Number(editorialLayout?.asset_crop?.grayscale ?? defaults.assetCrop.grayscale),
			contrast: Number(editorialLayout?.asset_crop?.contrast ?? defaults.assetCrop.contrast),
		},
	};
};
