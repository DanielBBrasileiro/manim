import type {TypographyScaleConfig} from './typographySystems';

export type ScaleRole = 'display' | 'title' | 'body' | 'caption';

export type ScaleSystem = {
	steps: Record<number, number>;
	family: Record<ScaleRole, number>;
};

export const createScaleSystem = (config: TypographyScaleConfig): ScaleSystem => {
	const maxStep = Math.max(
		config.display_step,
		config.title_step,
		config.body_step,
		config.caption_step,
	);
	const steps: Record<number, number> = {};

	for (let step = 0; step <= maxStep; step += 1) {
		steps[step] = Number((config.base_px * Math.pow(config.ratio, step)).toFixed(3));
	}

	return {
		steps,
		family: {
			display: steps[config.display_step],
			title: steps[config.title_step],
			body: steps[config.body_step],
			caption: steps[config.caption_step],
		},
	};
};
