/**
 * Canonical type for the render manifest passed from Python -> Remotion.
 * Use `parseRenderManifest` at component boundaries to fail fast on malformed JSON.
 */

export type TargetKind = 'still' | 'video' | 'carousel';

export interface PhysicsState {
  label?: string;
  seed?: number;
  motion_signature?: string;
  stability?: string;
  physical_entropy?: number;
  normalized_velocity?: number;
  position?: { x: number; y: number };
  velocity?: { x: number; y: number; magnitude: number };
}

export interface RenderManifest {
  target: string;
  targetId: string;
  targetKind: TargetKind;
  durationInFrames?: number;
  duration_in_frames?: number;
  width?: number;
  height?: number;
  fps?: number;
  frameOverride?: number;
  stillFrame?: number;
  style_pack?: string;
  story_atoms?: unknown[];
  physics_state?: PhysicsState;
  [key: string]: unknown;
}

export function parseRenderManifest(value: unknown): RenderManifest {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(
      `renderManifest must be a plain object, got: ${JSON.stringify(value)}`
    );
  }

  const manifest = value as Record<string, unknown>;

  if (typeof manifest['target'] !== 'string' || manifest['target'] === '') {
    throw new TypeError(
      `renderManifest.target must be a non-empty string, got: ${JSON.stringify(manifest['target'])}`
    );
  }

  if (typeof manifest['targetId'] !== 'string' || manifest['targetId'] === '') {
    throw new TypeError(
      `renderManifest.targetId must be a non-empty string, got: ${JSON.stringify(manifest['targetId'])}`
    );
  }

  const validKinds: TargetKind[] = ['still', 'video', 'carousel'];
  if (!validKinds.includes(manifest['targetKind'] as TargetKind)) {
    throw new TypeError(
      `renderManifest.targetKind must be one of ${validKinds.join(' | ')}, got: ${JSON.stringify(manifest['targetKind'])}`
    );
  }

  return manifest as RenderManifest;
}
