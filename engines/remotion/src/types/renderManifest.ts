/**
 * Canonical type for the render manifest passed from Python → Remotion.
 * Use `parseRenderManifest` at component boundaries to surface bad JSON early
 * rather than discovering shape mismatches at render time.
 */

export type TargetKind = 'still' | 'video' | 'carousel';

export interface RenderManifest {
  target: string;
  targetId: string;
  targetKind: TargetKind;
  /** Canonical frame count (camelCase from TS side) */
  durationInFrames?: number;
  /** Snake_case variant forwarded from Python side */
  duration_in_frames?: number;
  width?: number;
  height?: number;
  fps?: number;
  frameOverride?: number;
  stillFrame?: number;
  style_pack?: string;
  story_atoms?: unknown[];
  [key: string]: unknown;
}

/**
 * Validates the minimal required contract for a render manifest.
 * Throws a descriptive error when the Python side sends an incomplete payload.
 */
export function parseRenderManifest(value: unknown): RenderManifest {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new TypeError(
      `renderManifest must be a plain object, got: ${JSON.stringify(value)}`
    );
  }
  const m = value as Record<string, unknown>;

  if (typeof m['target'] !== 'string' || m['target'] === '') {
    throw new TypeError(
      `renderManifest.target must be a non-empty string, got: ${JSON.stringify(m['target'])}`
    );
  }
  if (typeof m['targetId'] !== 'string' || m['targetId'] === '') {
    throw new TypeError(
      `renderManifest.targetId must be a non-empty string, got: ${JSON.stringify(m['targetId'])}`
    );
  }
  const validKinds: TargetKind[] = ['still', 'video', 'carousel'];
  if (!validKinds.includes(m['targetKind'] as TargetKind)) {
    throw new TypeError(
      `renderManifest.targetKind must be one of ${validKinds.join(' | ')}, got: ${JSON.stringify(m['targetKind'])}`
    );
  }

  return m as RenderManifest;
}
