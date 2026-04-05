#!/usr/bin/env node

const fs = require("node:fs");
const path = require("node:path");
const {createRequire} = require("node:module");

const ROOT = path.resolve(__dirname, "..");
const REMOTION_ROOT = path.join(ROOT, "engines", "remotion");
const ENTRY_POINT = path.join(REMOTION_ROOT, "src", "index.tsx");
const PUBLIC_DIR = path.join(REMOTION_ROOT, "public");
const DEFAULT_COMPOSITION = "CinematicNarrative-v4";
const STILL_EXTENSION = ".png";
const DEFAULT_TIMEOUT_MS = Number(process.env.REMOTION_RENDER_TIMEOUT_MS || "60000");
const requireRemotion = createRequire(path.join(REMOTION_ROOT, "package.json"));

const {bundle} = requireRemotion("@remotion/bundler");
const {getCompositions, renderMedia, renderStill} = requireRemotion("@remotion/renderer");

const TARGET_ALIASES = {
  cinematicnarrative: DEFAULT_COMPOSITION,
  cinematic_narrative: DEFAULT_COMPOSITION,
  cinematicnarrative_v4: DEFAULT_COMPOSITION,
  cinematic_narrative_v4: DEFAULT_COMPOSITION,
  shortcinematic: DEFAULT_COMPOSITION,
  short_cinematic: DEFAULT_COMPOSITION,
  short_cinematic_vertical: DEFAULT_COMPOSITION,
  "short-cinematic": DEFAULT_COMPOSITION,
  "short-cinematic-vertical": DEFAULT_COMPOSITION,
  linkedinstill: DEFAULT_COMPOSITION,
  linkedin_still: DEFAULT_COMPOSITION,
  linkedinstill_v4: DEFAULT_COMPOSITION,
  linkedin_feed_4_5: DEFAULT_COMPOSITION,
  "linkedin-still": DEFAULT_COMPOSITION,
  "linkedin-feed-4-5": DEFAULT_COMPOSITION,
  carouselslide: DEFAULT_COMPOSITION,
  carousel_slide: DEFAULT_COMPOSITION,
  carouselslide_v4: DEFAULT_COMPOSITION,
  linkedin_carousel_square: DEFAULT_COMPOSITION,
  "carousel-slide": DEFAULT_COMPOSITION,
  "linkedin-carousel-square": DEFAULT_COMPOSITION,
  youtubessay: DEFAULT_COMPOSITION,
  youtube_essay: DEFAULT_COMPOSITION,
  youtubessay_v4: DEFAULT_COMPOSITION,
  youtube_essay_16_9: DEFAULT_COMPOSITION,
  "youtube-essay": DEFAULT_COMPOSITION,
  "youtube-essay-16-9": DEFAULT_COMPOSITION,
  thumbnail: DEFAULT_COMPOSITION,
  youtube_thumbnail: DEFAULT_COMPOSITION,
  thumbnail_v4: DEFAULT_COMPOSITION,
  youtube_thumbnail_16_9: DEFAULT_COMPOSITION,
  "youtube-thumbnail-16-9": DEFAULT_COMPOSITION,
};

let cachedServeUrl = null;

const normalizeKey = (value) =>
  String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "");

const normalizeCompositionId = (value) => {
  const raw = String(value || "").trim();
  if (!raw) return DEFAULT_COMPOSITION;
  if (raw === DEFAULT_COMPOSITION) return DEFAULT_COMPOSITION;
  return TARGET_ALIASES[normalizeKey(raw)] || raw;
};

const parseInputProps = () => {
  const propsPath = process.env.REMOTION_INPUT_PROPS_PATH;
  if (propsPath && fs.existsSync(propsPath)) {
    return JSON.parse(fs.readFileSync(propsPath, "utf-8"));
  }

  const propsJson = process.env.REMOTION_INPUT_PROPS_JSON;
  if (propsJson) {
    return JSON.parse(propsJson);
  }

  return {};
};

const rendererOptions = (inputProps) => ({
  inputProps,
  logLevel: "warn",
  timeoutInMilliseconds: DEFAULT_TIMEOUT_MS,
});

const ensureBundle = async () => {
  if (cachedServeUrl) {
    return cachedServeUrl;
  }

  console.log("[Direct] Bundling Remotion project...");
  cachedServeUrl = await bundle({
    askAIEnabled: false,
    entryPoint: ENTRY_POINT,
    enableCaching: true,
    ignoreRegisterRootWarning: true,
    publicDir: PUBLIC_DIR,
    rootDir: REMOTION_ROOT,
  });
  console.log(`[Direct] Bundle ready at: ${cachedServeUrl}`);
  return cachedServeUrl;
};

const resolveComposition = async (requestedCompositionId, inputProps) => {
  const serveUrl = await ensureBundle();
  const compositions = await getCompositions(serveUrl, rendererOptions(inputProps));
  const normalized = normalizeCompositionId(requestedCompositionId);
  const composition =
    compositions.find((entry) => entry.id === requestedCompositionId) ||
    compositions.find((entry) => entry.id === normalized) ||
    compositions.find((entry) => entry.id === DEFAULT_COMPOSITION);

  if (!composition) {
    throw new Error(`Composition not found: ${requestedCompositionId}`);
  }

  return {composition, serveUrl};
};

const render = async (command, requestedCompositionId, outputLocation) => {
  const inputProps = parseInputProps();
  const {composition, serveUrl} = await resolveComposition(requestedCompositionId, inputProps);
  fs.mkdirSync(path.dirname(outputLocation), {recursive: true});

  if (command === "still") {
    const pngOutput = outputLocation.endsWith(STILL_EXTENSION)
      ? outputLocation
      : `${outputLocation}${STILL_EXTENSION}`;
    const frame = Number(inputProps?.frameOverride || inputProps?.renderManifest?.stillFrame || 0);
    console.log(`[Direct] Rendering still for ${composition.id} -> ${pngOutput}`);
    await renderStill({
      composition,
      frame,
      inputProps,
      output: pngOutput,
      overwrite: true,
      serveUrl,
      ...rendererOptions(inputProps),
    });
    return pngOutput;
  }

  console.log(`[Direct] Rendering video for ${composition.id} -> ${outputLocation}`);
  await renderMedia({
    codec: "h264",
    composition,
    concurrency: 2,
    inputProps,
    outputLocation,
    overwrite: true,
    serveUrl,
    ...rendererOptions(inputProps),
  });
  return outputLocation;
};

const main = async () => {
  const [, , command, compositionArg, outputArg] = process.argv;

  if (command === "warm") {
    await ensureBundle();
    console.log("[Direct] Warm bundle ready.");
    return;
  }

  if (!["render", "still"].includes(command || "")) {
    throw new Error("Usage: remotion_direct.js <warm|render|still> [composition] [output]");
  }

  if (!outputArg) {
    throw new Error("Output path is required for render/still commands.");
  }

  const finalOutput = await render(command, compositionArg || DEFAULT_COMPOSITION, outputArg);
  if (!fs.existsSync(finalOutput) || fs.statSync(finalOutput).size === 0) {
    throw new Error(`Render output missing or empty: ${finalOutput}`);
  }
  console.log(`[Direct] Done: ${finalOutput}`);
};

main().catch((error) => {
  console.error("[Direct] Error:", error);
  process.exit(1);
});
