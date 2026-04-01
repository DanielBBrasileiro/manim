#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { createRequire } = require("node:module");
const express = require("express");
const cors = require("cors");
const bodyParser = require("body-parser");

const ROOT = path.resolve(__dirname, "..");
const REMOTION_ROOT = path.join(ROOT, "engines", "remotion");
const ENTRY_POINT = path.join(REMOTION_ROOT, "src", "index.tsx");
const PUBLIC_DIR = path.join(REMOTION_ROOT, "public");
const BUNDLE_CACHE_DIR = path.join(REMOTION_ROOT, ".bundle-cache");
const BUNDLE_CACHE_MANIFEST = path.join(BUNDLE_CACHE_DIR, "bundle-manifest.json");
const DEFAULT_COMPOSITION = "short-cinematic-vertical";
const DEFAULT_TIMEOUT_MS = Number(process.env.REMOTION_RENDER_TIMEOUT_MS || "60000");
const SYSTEM_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const DEFAULT_STILL_EXTENSION = ".png";

const TARGET_ALIASES = {
  cinematicnarrative: "short-cinematic-vertical",
  cinematic_narrative: "short-cinematic-vertical",
  cinematicnarrative_v4: "short-cinematic-vertical",
  cinematic_narrative_v4: "short-cinematic-vertical",
  shortcinematic: "short-cinematic-vertical",
  short_cinematic: "short-cinematic-vertical",
  short_cinematic_vertical: "short-cinematic-vertical",
  "short-cinematic": "short-cinematic-vertical",
  "short-cinematic-vertical": "short-cinematic-vertical",
  linkedinstill: "linkedin-feed-4-5",
  linkedin_still: "linkedin-feed-4-5",
  linkedinstill_v4: "linkedin-feed-4-5",
  linkedin_feed_4_5: "linkedin-feed-4-5",
  "linkedin-still": "linkedin-feed-4-5",
  "linkedin-feed-4-5": "linkedin-feed-4-5",
  carouselslide: "linkedin-carousel-square",
  carousel_slide: "linkedin-carousel-square",
  carouselslide_v4: "linkedin-carousel-square",
  linkedin_carousel_square: "linkedin-carousel-square",
  "carousel-slide": "linkedin-carousel-square",
  "linkedin-carousel-square": "linkedin-carousel-square",
  youtubessay: "youtube-essay-16-9",
  youtube_essay: "youtube-essay-16-9",
  youtubessay_v4: "youtube-essay-16-9",
  youtube_essay_16_9: "youtube-essay-16-9",
  "youtube-essay": "youtube-essay-16-9",
  "youtube-essay-16-9": "youtube-essay-16-9",
  thumbnail: "youtube-thumbnail-16-9",
  youtube_thumbnail: "youtube-thumbnail-16-9",
  thumbnail_v4: "youtube-thumbnail-16-9",
  youtube_thumbnail_16_9: "youtube-thumbnail-16-9",
  "youtube-thumbnail-16-9": "youtube-thumbnail-16-9",
};

const BUNDLER_DIST = path.join(REMOTION_ROOT, "node_modules", "@remotion", "bundler", "dist");
const RENDERER_DIST = path.join(REMOTION_ROOT, "node_modules", "@remotion", "renderer", "dist");

const normalizeCompositionId = (value) => {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  return TARGET_ALIASES[normalized] || normalized || DEFAULT_COMPOSITION;
};

const resolveBrowserExecutable = () => {
  const fromEnv = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (fromEnv && fs.existsSync(fromEnv)) return fromEnv;
  if (fs.existsSync(SYSTEM_CHROME)) return SYSTEM_CHROME;
  return null;
};

const browserExecutable = resolveBrowserExecutable();
let bundlerApi = null;
let rendererApi = null;

const statMtime = (filePath) => (!fs.existsSync(filePath) ? 0 : fs.statSync(filePath).mtimeMs);
const latestMtimeInTree = (rootPath) => {
  if (!fs.existsSync(rootPath)) return 0;
  const stat = fs.statSync(rootPath);
  if (!stat.isDirectory()) return stat.mtimeMs;
  let latest = stat.mtimeMs;
  for (const entry of fs.readdirSync(rootPath, { withFileTypes: true })) {
    latest = Math.max(latest, latestMtimeInTree(path.join(rootPath, entry.name)));
  }
  return latest;
};

const syncDirectoryContents = (sourceDir, destinationDir) => {
  fs.mkdirSync(destinationDir, { recursive: true });
  const seenEntries = new Set();
  for (const entry of fs.readdirSync(sourceDir, { withFileTypes: true })) {
    seenEntries.add(entry.name);
    const sourcePath = path.join(sourceDir, entry.name);
    const destinationPath = path.join(destinationDir, entry.name);
    if (entry.isDirectory()) {
      syncDirectoryContents(sourcePath, destinationPath);
      continue;
    }
    const sourceStat = fs.statSync(sourcePath);
    const destinationExists = fs.existsSync(destinationPath);
    const destinationStat = destinationExists ? fs.statSync(destinationPath) : null;
    const destinationIsStale =
      !destinationStat ||
      destinationStat.size !== sourceStat.size ||
      destinationStat.mtimeMs < sourceStat.mtimeMs;
    if (destinationIsStale) {
      fs.mkdirSync(path.dirname(destinationPath), { recursive: true });
      fs.copyFileSync(sourcePath, destinationPath);
      fs.utimesSync(destinationPath, sourceStat.atime, sourceStat.mtime);
    }
  }
  for (const entry of fs.readdirSync(destinationDir, { withFileTypes: true })) {
    if (seenEntries.has(entry.name)) continue;
    fs.rmSync(path.join(destinationDir, entry.name), { recursive: true, force: true });
  }
};

const syncPublicAssets = (bundlePath) => {
  const bundlePublicDir = path.join(bundlePath, "public");
  fs.mkdirSync(bundlePublicDir, { recursive: true });
  syncDirectoryContents(PUBLIC_DIR, bundlePublicDir);
};

const getSourceMtime = () =>
  Math.max(
    latestMtimeInTree(path.join(REMOTION_ROOT, "src")),
    statMtime(path.join(REMOTION_ROOT, "package.json"))
  );

const readBundleManifest = () => {
  try {
    if (!fs.existsSync(BUNDLE_CACHE_MANIFEST)) return null;
    return JSON.parse(fs.readFileSync(BUNDLE_CACHE_MANIFEST, "utf-8"));
  } catch (_) {
    return null;
  }
};

const writeBundleManifest = (bundlePath) => {
  try {
    fs.mkdirSync(BUNDLE_CACHE_DIR, { recursive: true });
    fs.writeFileSync(
      BUNDLE_CACHE_MANIFEST,
      JSON.stringify({ bundlePath, sourceMtime: getSourceMtime(), createdAt: Date.now() }, null, 2)
    );
  } catch (_) {}
};

const findReusableBundle = () => {
  const sourceMtime = getSourceMtime();
  const manifest = readBundleManifest();
  if (
    manifest &&
    manifest.sourceMtime >= sourceMtime &&
    manifest.bundlePath &&
    fs.existsSync(path.join(manifest.bundlePath, "bundle.js"))
  ) {
    return manifest.bundlePath;
  }
  return null;
};

const loadBundler = () => {
  if (bundlerApi) return bundlerApi;
  bundlerApi = require(path.join(BUNDLER_DIST, "bundle.js"));
  return bundlerApi;
};

const loadRenderer = () => {
  if (rendererApi) return rendererApi;
  const { getCompositions } = require(path.join(RENDERER_DIST, "get-compositions.js"));
  const { renderMedia } = require(path.join(RENDERER_DIST, "render-media.js"));
  let renderStill = null;
  try {
    ({ renderStill } = require(path.join(RENDERER_DIST, "render-still.js")));
  } catch (_) {}
  rendererApi = { getCompositions, renderMedia, renderStill };
  return rendererApi;
};

const makeRendererOptions = () => ({
  browserExecutable,
  chromiumOptions: { headless: true, ignoreCertificateErrors: true },
  logLevel: "warn",
  timeoutInMilliseconds: DEFAULT_TIMEOUT_MS,
});

let _cachedBundleUrl = null;

const ensureBundle = async () => {
  const reusableBundle = findReusableBundle();
  if (reusableBundle) {
    syncPublicAssets(reusableBundle);
    _cachedBundleUrl = reusableBundle;
    return reusableBundle;
  }
  console.log("[Daemon] Bundling Remotion project on startup...");
  const { bundle } = loadBundler();
  const serveUrl = await bundle({
    askAIEnabled: false,
    entryPoint: ENTRY_POINT,
    enableCaching: true,
    experimentalClientSideRenderingEnabled: false,
    experimentalVisualModeEnabled: false,
    ignoreRegisterRootWarning: true,
    keyboardShortcutsEnabled: false,
    publicDir: PUBLIC_DIR,
    rootDir: REMOTION_ROOT,
    rspack: true,
    webpackOverride: (config) => {
      config.resolve = config.resolve || {};
      config.resolve.fallback = { ...(config.resolve.fallback || {}), fs: false, path: false };
      return config;
    },
  });
  writeBundleManifest(serveUrl);
  syncPublicAssets(serveUrl);
  _cachedBundleUrl = serveUrl;
  console.log(`[Daemon] Bundle ready at: ${serveUrl}`);
  return serveUrl;
};

const loadCompositions = async (serveUrl, inputProps) => {
  const { getCompositions } = loadRenderer();
  return await getCompositions(serveUrl, { ...makeRendererOptions(), inputProps });
};

// EXPRESS SERVER
const app = express();
app.use(cors());
app.use(bodyParser.json({ limit: "50mb" }));

app.post("/render", async (req, res) => {
  try {
    const { command, requestedCompositionId, outputLocation, inputProps } = req.body;
    if (!["render", "still"].includes(command)) {
      return res.status(400).json({ ok: false, error: "Invalid command" });
    }
    
    const compositionId = normalizeCompositionId(requestedCompositionId);
    let finalOutputLocation = outputLocation || path.join(ROOT, "output", "renders", `${compositionId}.mp4`);
    
    // Assegura que o bundle ta limpo mas NUNCA re-builda no meio de uma requisicao se nao precisar
    let serveUrl = _cachedBundleUrl;
    if (!serveUrl) {
      serveUrl = await ensureBundle();
    } else {
      syncPublicAssets(serveUrl); // Fast sync in case data changed
    }

    const compositions = await loadCompositions(serveUrl, inputProps || {});
    const composition = compositions.find((c) => c.id === compositionId);
    if (!composition) {
      return res.status(404).json({ ok: false, error: `Composition not found: ${compositionId}` });
    }

    fs.mkdirSync(path.dirname(finalOutputLocation), { recursive: true });
    
    if (command === "render") {
      const { renderMedia } = loadRenderer();
      await renderMedia({
        ...makeRendererOptions(),
        codec: "h264",
        composition,
        concurrency: 2,
        inputProps: inputProps || {},
        outputLocation: finalOutputLocation,
        overwrite: true,
        serveUrl,
      });
    } else if (command === "still") {
      finalOutputLocation = finalOutputLocation.endsWith(".png") ? finalOutputLocation : `${finalOutputLocation}${DEFAULT_STILL_EXTENSION}`;
      const { renderStill } = loadRenderer();
      const stillFrame = Number(inputProps?.frameOverride || inputProps?.renderManifest?.stillFrame || 0);
      
      await renderStill({
        ...makeRendererOptions(),
        composition,
        frame: stillFrame,
        inputProps: inputProps || {},
        output: finalOutputLocation,
        overwrite: true,
        serveUrl,
      });
    }

    if (!fs.existsSync(finalOutputLocation) || fs.statSync(finalOutputLocation).size === 0) {
      return res.status(500).json({ ok: false, error: "Render resulted in missing or empty file" });
    }

    res.json({ ok: true, outputLocation: finalOutputLocation });

  } catch (error) {
    console.error("[Daemon] Error:", error);
    res.status(500).json({ ok: false, error: error.message || String(error) });
  }
});

const PORT = 3333;
app.listen(PORT, async () => {
  console.log(`🚀 AIOX Remotion Daemon v5.0 started on port ${PORT}`);
  await ensureBundle();
  console.log(`✅ Daemon is hot and ready for 500ms zero-bundle renders!`);
});
