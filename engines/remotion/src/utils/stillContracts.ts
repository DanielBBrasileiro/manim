export type StillFamilyContract = {
	id: string;
	description?: string;
	base: string | null;
	background: string;
	typography_system: string;
	composition_grid: string;
	accent: string;
	negative_space_min: number;
	max_text_elements: number;
	max_visual_elements: number;
	grain: number;
};

export type StylePackContract = {
	id: string;
	typography_system: string;
	still_family: string;
	color_mode: string;
	grain: number;
	accent_intensity: number;
	negative_space_target: number;
};

const STILL_FAMILIES: Record<string, StillFamilyContract> = {
	poster_minimal: {
		id: 'poster_minimal',
		description: 'Maximum restraint. One word. One line. Black field.',
		base: null,
		background: 'solid_dark',
		typography_system: 'editorial_minimal',
		composition_grid: 'golden_section',
		accent: 'single_rule_line',
		negative_space_min: 0.6,
		max_text_elements: 2,
		max_visual_elements: 1,
		grain: 0.06,
	},
	editorial_portrait: {
		id: 'editorial_portrait',
		description: 'Magazine cover energy. Photo base. Bold type.',
		base: 'editorial_photo',
		background: 'photo_with_veil',
		typography_system: 'editorial_dense',
		composition_grid: 'rule_of_thirds',
		accent: 'frame_crop + subtle_counter',
		negative_space_min: 0.35,
		max_text_elements: 4,
		max_visual_elements: 2,
		grain: 0.04,
	},
};

const STYLE_PACKS: Record<string, StylePackContract> = {
	silent_luxury: {
		id: 'silent_luxury',
		typography_system: 'editorial_minimal',
		still_family: 'poster_minimal',
		color_mode: 'monochrome_pure',
		grain: 0.04,
		accent_intensity: 0.1,
		negative_space_target: 0.65,
	},
	kinetic_editorial: {
		id: 'kinetic_editorial',
		typography_system: 'editorial_dense',
		still_family: 'editorial_portrait',
		color_mode: 'monochrome_warm',
		grain: 0.08,
		accent_intensity: 0.5,
		negative_space_target: 0.4,
	},
};

export const getStillFamily = (id?: string | null): StillFamilyContract | null => {
	if (!id) {
		return null;
	}
	return STILL_FAMILIES[id] ?? null;
};

export const getStylePack = (id?: string | null): StylePackContract | null => {
	if (!id) {
		return null;
	}
	return STYLE_PACKS[id] ?? null;
};
