export type RemotionTargetId =
  | 'short_cinematic_vertical'
  | 'linkedin_feed_4_5'
  | 'linkedin_carousel_square'
  | 'youtube_essay_16_9'
  | 'youtube_thumbnail_16_9';

export type RemotionTargetKind = 'composition' | 'still';

export type RemotionTargetConfig = {
  id: RemotionTargetId;
  label: string;
  kind: RemotionTargetKind;
  compositionId: string;
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
  defaultStillFrame: number;
  safeZone: number;
};

export type RemotionTargetCatalog = Record<RemotionTargetId, RemotionTargetConfig>;

export const REMOTION_TARGETS: RemotionTargetCatalog = {
  short_cinematic_vertical: {
    id: 'short_cinematic_vertical',
    label: 'Short cinematic vertical',
    kind: 'composition',
    compositionId: 'short-cinematic-vertical',
    width: 1080,
    height: 1920,
    fps: 60,
    durationInFrames: 900,
    defaultStillFrame: 540,
    safeZone: 0.08,
  },
  linkedin_feed_4_5: {
    id: 'linkedin_feed_4_5',
    label: 'LinkedIn feed 4:5',
    kind: 'still',
    compositionId: 'linkedin-feed-4-5',
    width: 1080,
    height: 1350,
    fps: 30,
    durationInFrames: 900,
    defaultStillFrame: 540,
    safeZone: 0.1,
  },
  linkedin_carousel_square: {
    id: 'linkedin_carousel_square',
    label: 'LinkedIn carousel square',
    kind: 'still',
    compositionId: 'linkedin-carousel-square',
    width: 1080,
    height: 1080,
    fps: 30,
    durationInFrames: 900,
    defaultStillFrame: 600,
    safeZone: 0.1,
  },
  youtube_essay_16_9: {
    id: 'youtube_essay_16_9',
    label: 'YouTube essay 16:9',
    kind: 'composition',
    compositionId: 'youtube-essay-16-9',
    width: 1920,
    height: 1080,
    fps: 30,
    durationInFrames: 1800,
    defaultStillFrame: 900,
    safeZone: 0.06,
  },
  youtube_thumbnail_16_9: {
    id: 'youtube_thumbnail_16_9',
    label: 'YouTube thumbnail 16:9',
    kind: 'still',
    compositionId: 'youtube-thumbnail-16-9',
    width: 1280,
    height: 720,
    fps: 30,
    durationInFrames: 900,
    defaultStillFrame: 780,
    safeZone: 0.08,
  },
};

const TARGET_ALIASES: Record<string, RemotionTargetId> = {
  cinematicnarrative: 'short_cinematic_vertical',
  cinematic_narrative: 'short_cinematic_vertical',
  cinematicnarrative_v4: 'short_cinematic_vertical',
  cinematic_narrative_v4: 'short_cinematic_vertical',
  cinematicnarrativev4: 'short_cinematic_vertical',
  shortcinematic: 'short_cinematic_vertical',
  short_cinematic: 'short_cinematic_vertical',
  'short-cinematic': 'short_cinematic_vertical',
  short_cinematic_vertical: 'short_cinematic_vertical',
  linkedinstill: 'linkedin_feed_4_5',
  linkedin_still: 'linkedin_feed_4_5',
  'linkedin-still': 'linkedin_feed_4_5',
  linkedinstill_v4: 'linkedin_feed_4_5',
  linkedinstillv4: 'linkedin_feed_4_5',
  linkedin_feed_4_5: 'linkedin_feed_4_5',
  carouselslide: 'linkedin_carousel_square',
  carousel_slide: 'linkedin_carousel_square',
  'carousel-slide': 'linkedin_carousel_square',
  carouselslide_v4: 'linkedin_carousel_square',
  carouselslidev4: 'linkedin_carousel_square',
  linkedin_carousel_square: 'linkedin_carousel_square',
  youtubessay: 'youtube_essay_16_9',
  youtube_essay: 'youtube_essay_16_9',
  'youtube-essay': 'youtube_essay_16_9',
  youtubessay_v4: 'youtube_essay_16_9',
  youtubeessay_v4: 'youtube_essay_16_9',
  youtubeessayv4: 'youtube_essay_16_9',
  youtube_essay_16_9: 'youtube_essay_16_9',
  thumbnail: 'youtube_thumbnail_16_9',
  youtube_thumbnail: 'youtube_thumbnail_16_9',
  thumbnail_v4: 'youtube_thumbnail_16_9',
  thumbnailv4: 'youtube_thumbnail_16_9',
  youtube_thumbnail_16_9: 'youtube_thumbnail_16_9',
};

const TARGET_IDS = new Set<RemotionTargetId>(Object.keys(REMOTION_TARGETS) as RemotionTargetId[]);

export const REMOTION_TARGET_ORDER: RemotionTargetConfig[] = [
  REMOTION_TARGETS.short_cinematic_vertical,
  REMOTION_TARGETS.linkedin_feed_4_5,
  REMOTION_TARGETS.linkedin_carousel_square,
  REMOTION_TARGETS.youtube_essay_16_9,
  REMOTION_TARGETS.youtube_thumbnail_16_9,
];

export const normalizeTargetId = (value?: string | null): RemotionTargetId => {
  if (!value) {
    return 'short_cinematic_vertical';
  }

  const normalized = value.trim().toLowerCase().replace(/[\s-]+/g, '_').replace(/[^a-z0-9_]/g, '');
  const versionless = normalized.replace(/_?v\d+$/, '');
  const alias = TARGET_ALIASES[normalized] ?? TARGET_ALIASES[versionless];
  if (alias) {
    return alias;
  }

  if (TARGET_IDS.has(normalized as RemotionTargetId)) {
    return normalized as RemotionTargetId;
  }

  if (TARGET_IDS.has(versionless as RemotionTargetId)) {
    return versionless as RemotionTargetId;
  }

  return 'short_cinematic_vertical';
};

export const getTargetConfig = (value?: string | null): RemotionTargetConfig => {
  return REMOTION_TARGETS[normalizeTargetId(value)];
};

export const getTargetConfigByCompositionId = (compositionId: string): RemotionTargetConfig => {
  return REMOTION_TARGETS[normalizeTargetId(compositionId)];
};

export const getTargetFrameOverride = (
  target: RemotionTargetConfig,
  requestedFrame?: number | null,
): number | undefined => {
  if (Number.isFinite(requestedFrame ?? NaN)) {
    return requestedFrame as number;
  }

  return target.kind === 'still' ? target.defaultStillFrame : undefined;
};

export const getTargetDurationInFrames = (
  target: RemotionTargetConfig,
  requestedDuration?: number | null,
): number => {
  if (Number.isFinite(requestedDuration ?? NaN) && (requestedDuration ?? 0) > 0) {
    return requestedDuration as number;
  }

  return target.durationInFrames;
};
