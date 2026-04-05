import React from 'react';
import {StillComposer, type StillComposerProps} from './StillComposer';
import {
	getTargetConfig,
	normalizeTargetId,
	type RemotionTargetConfig,
	type RemotionTargetId,
} from '../targets';

type RenderManifestLike = NonNullable<StillComposerProps['renderManifest']> & {
	target?: string;
	targetId?: string;
	targetKind?: string;
	width?: number;
	height?: number;
	frameOverride?: number;
	stillFrame?: number;
	targets?: Record<string, Record<string, unknown>>;
	targetProps?: Record<string, Record<string, unknown>>;
	renderTargets?: Record<string, Record<string, unknown>>;
};

export type TargetedStillCompositionProps = StillComposerProps & {
	target?: RemotionTargetId | string;
	targetId?: RemotionTargetId | string;
};

const asObject = (value: unknown): Record<string, unknown> | undefined => {
	if (!value || typeof value !== 'object' || Array.isArray(value)) {
		return undefined;
	}
	return value as Record<string, unknown>;
};

const readTargetOverride = (
	props: TargetedStillCompositionProps,
	targetId: RemotionTargetId,
): Record<string, unknown> | undefined => {
	const hasMatchingKey = (key: string | undefined): boolean => {
		if (!key) {
			return false;
		}
		return normalizeTargetId(key) === targetId;
	};

	const fromTopLevel =
		asObject((props as Record<string, unknown>).targetProps)?.[targetId] ??
		asObject((props as Record<string, unknown>).targetOverrides)?.[targetId] ??
		Object.entries(asObject((props as Record<string, unknown>).targetProps) ?? {}).find(([key]) => hasMatchingKey(key))?.[1] ??
		Object.entries(asObject((props as Record<string, unknown>).targetOverrides) ?? {}).find(([key]) => hasMatchingKey(key))?.[1];

	const manifest = asObject(props.renderManifest) as RenderManifestLike | undefined;
	if (!manifest) {
		return asObject(fromTopLevel);
	}

	const fromManifest =
		manifest.targets?.[targetId] ??
		manifest.targetProps?.[targetId] ??
		manifest.renderTargets?.[targetId] ??
		Object.entries(manifest.targets ?? {}).find(([key]) => hasMatchingKey(key))?.[1] ??
		Object.entries(manifest.targetProps ?? {}).find(([key]) => hasMatchingKey(key))?.[1] ??
		Object.entries(manifest.renderTargets ?? {}).find(([key]) => hasMatchingKey(key))?.[1];

	return asObject(fromManifest) ?? asObject(fromTopLevel);
};

const mergeRenderManifest = (
	base: StillComposerProps['renderManifest'],
	override: Record<string, unknown> | undefined,
	target: RemotionTargetConfig,
): RenderManifestLike => {
	const baseManifest = asObject(base) ?? {};
	const overrideManifest = asObject((override as {renderManifest?: unknown} | undefined)?.renderManifest) ?? {};

	return {
		...baseManifest,
		...overrideManifest,
		target: target.id,
		targetId: target.id,
		targetKind: target.kind,
		width: target.width,
		height: target.height,
		frameOverride: target.defaultStillFrame,
		stillFrame: target.defaultStillFrame,
	};
};

export const TargetedStillComposition: React.FC<TargetedStillCompositionProps> = (props) => {
	const target = getTargetConfig(
		props.target ??
			props.targetId ??
			(props.renderManifest as RenderManifestLike | undefined)?.target ??
			(props.renderManifest as RenderManifestLike | undefined)?.targetId,
	);
	const override = readTargetOverride(props, target.id);
	const mergedRenderManifest = mergeRenderManifest(props.renderManifest, override, target);

	return (
		<StillComposer
			{...props}
			target={target.id}
			renderManifest={mergedRenderManifest}
		/>
	);
};
