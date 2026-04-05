#!/usr/bin/env node

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");
const REMOTION_ROOT = path.join(ROOT, "engines", "remotion");
const ENTRY_POINT = path.join(REMOTION_ROOT, "src", "index.tsx");
const PUBLIC_DIR = path.join(REMOTION_ROOT, "public");
const BUNDLE_CACHE_DIR = path.join(REMOTION_ROOT, ".bundle-cache");
const BUNDLE_CACHE_MANIFEST = path.join(BUNDLE_CACHE_DIR, "bundle-manifest.json");
const DEFAULT_COMPOSITION = "CinematicNarrative-v4";
const DEFAULT_TIMEOUT_MS = Number(process.env.REMOTION_RENDER_TIMEOUT_MS || "60000");
const USE_RSPACK = process.env.AIOX_REMOTION_USE_RSPACK === "1";
const SYSTEM_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const PLAYWRIGHT_CACHE_DIR = path.join(os.homedir(), "Library", "Caches", "ms-playwright");
const DEFAULT_STILL_EXTENSION = ".png";
const BUNDLER_DIST = path.join(REMOTION_ROOT, "node_modules", "@remotion", "bundler", "dist");
const RENDERER_DIST = path.join(REMOTION_ROOT, "node_modules", "@remotion", "renderer", "dist");

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

const normalizeCompositionId = (value) => {
  const normalized = String(value || "")
    .trim()
    .toLowerCase()
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "");
  return TARGET_ALIASES[normalized] || value || DEFAULT_COMPOSITION;
};

const resolveBrowserExecutable = () => {
  const fromEnv = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (fromEnv && fs.existsSync(fromEnv)) return fromEnv;
  try {
    if (fs.existsSync(PLAYWRIGHT_CACHE_DIR)) {
      const candidates = fs
        .readdirSync(PLAYWRIGHT_CACHE_DIR, {withFileTypes: true})
        .filter((entry) => entry.isDirectory() && entry.name.startsWith("chromium-"))
        .map((entry) =>
          path.join(
            PLAYWRIGHT_CACHE_DIR,
            entry.name,
            "chrome-mac-arm64",
            "Google Chrome for Testing.app",
            "Contents",
            "MacOS",
            "Google Chrome for Testing",
          ),
        )
        .filter((candidate) => fs.existsSync(candidate))
        .sort()
        .reverse();
      if (candidates.length > 0) {
        return candidates[0];
      }
    }
  } catch (_) {}
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
  chromiumOptions: {
    headless: true,
    ignoreCertificateErrors: true,
    gl: "angle",
    disableWebSecurity: true,
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-gpu",
      "--disable-software-rasterizer",
      "--disable-background-networking",
      "--disable-background-timer-throttling",
    ],
  },
  logLevel: "warn",
  timeoutInMilliseconds: DEFAULT_TIMEOUT_MS,
});

let _cachedBundleUrl = null;
let _bundlePromise = null;

const ensureBundle = async () => {
  if (_cachedBundleUrl) {
    return _cachedBundleUrl;
  }

  if (_bundlePromise) {
    return _bundlePromise;
  }

  const reusableBundle = findReusableBundle();
  if (reusableBundle) {
    syncPublicAssets(reusableBundle);
    _cachedBundleUrl = reusableBundle;
    return reusableBundle;
  }
  _bundlePromise = (async () => {
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
      rspack: USE_RSPACK,
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
  })();

  try {
    return await _bundlePromise;
  } finally {
    _bundlePromise = null;
  }
};

const loadCompositions = async (serveUrl, inputProps) => {
  const { getCompositions } = loadRenderer();
  return await getCompositions(serveUrl, { ...makeRendererOptions(), inputProps });
};

const sendJson = (res, statusCode, payload) => {
  res.writeHead(statusCode, {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
  });
  res.end(JSON.stringify(payload));
};

const readJsonBody = (req) =>
  new Promise((resolve, reject) => {
    let body = "";
    req.setEncoding("utf8");
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 50 * 1024 * 1024) {
        reject(new Error("Request body too large"));
        req.destroy();
      }
    });
    req.on("end", () => {
      if (!body) {
        resolve({});
        return;
      }
      try {
        resolve(JSON.parse(body));
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });

const handleRender = async (body, res) => {
  try {
    const { command, requestedCompositionId, outputLocation, inputProps } = body;
    if (!["render", "still"].includes(command)) {
      sendJson(res, 400, { ok: false, error: "Invalid command" });
      return;
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
      sendJson(res, 404, { ok: false, error: `Composition not found: ${compositionId}` });
      return;
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
      sendJson(res, 500, { ok: false, error: "Render resulted in missing or empty file" });
      return;
    }

    sendJson(res, 200, { ok: true, outputLocation: finalOutputLocation });
  } catch (error) {
    console.error("[Daemon] Error:", error);
    sendJson(res, 500, { ok: false, error: error.message || String(error) });
  }
};

const PORT = Number(process.env.REMOTION_DAEMON_PORT || "3333");
const server = http.createServer(async (req, res) => {
  if (!req.url) {
    sendJson(res, 400, { ok: false, error: "Missing URL" });
    return;
  }

  if (req.method === "OPTIONS") {
    sendJson(res, 204, {});
    return;
  }

  if (req.method === "GET" && req.url === "/health") {
    sendJson(res, 200, {
      ok: true,
      browserExecutable,
      bundleReady: Boolean(_cachedBundleUrl),
      bundleWarming: Boolean(_bundlePromise),
      serveUrl: _cachedBundleUrl,
    });
    return;
  }

  if (req.method === "POST" && req.url === "/warm") {
    const wasReady = Boolean(_cachedBundleUrl);
    const wasWarming = Boolean(_bundlePromise);
    sendJson(res, wasReady ? 200 : 202, {
      ok: true,
      bundleReady: wasReady,
      bundleWarming: wasWarming || !wasReady,
    });
    setTimeout(() => {
      ensureBundle().catch((error) => {
        console.error("[Daemon] Warmup failed:", error);
      });
    }, 0);
    return;
  }

  if (req.method === "POST" && req.url === "/render") {
    try {
      const body = await readJsonBody(req);
      await handleRender(body, res);
    } catch (error) {
      sendJson(res, 400, { ok: false, error: error.message || String(error) });
    }
    return;
  }

  sendJson(res, 404, { ok: false, error: "Not found" });
});

server.listen(PORT, () => {
  console.log(`🚀 AIOX Remotion Daemon v5.0 started on port ${PORT}`);
  console.log("[Daemon] Health endpoint ready; warmup is now explicit via POST /warm or first /render.");
});
