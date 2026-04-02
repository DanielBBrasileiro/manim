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
	const isPosterMinimal =
		stillFamily?.id === 'poster_minimal' ||
		stillFamily?.composition_grid === 'golden_section' ||
		negativeSpaceTarget >= 0.58;

	const ns = spaceScale(negativeSpaceTarget);

	const defaults = isPosterMinimal
		? {
				heroZone: {x: 0.1, y: 0.60, w: shrinkW(0.28, ns * 0.5), h: 0.18},
				supportZone: {x: 0.1, y: 0.14, w: shrinkW(0.22, ns * 0.3), h: 0.06},
				emptyZone: {x: Math.min(0.60, 0.48 - ns * 0.4), y: 0.08, w: Math.max(0.30, 0.42 + ns * 0.5), h: 0.52},
				focalZone: {x: 0.08 + ns * 0.04, y: 0.08, w: Math.max(0.60, 0.84 - ns * 0.3), h: 0.80},
				curveBox: {x: 0.08 + ns * 0.04, y: 0.08, w: Math.max(0.60, 0.84 - ns * 0.3), h: 0.80},
				titleBox: {x: 0.10, y: 0.62, w: shrinkW(0.28, ns * 0.5), h: 0.18},
				eyebrowBox: {x: 0.10, y: 0.14, w: shrinkW(0.22, ns * 0.3), h: 0.05},
				accentAnchor: {x: 0.90, y: 0.14},
				assetCrop: {
					object_position: '58% 46%',
					veil_opacity: 0.52,
					grayscale: 1,
					contrast: 1.12,
				},
			}
		: {
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
