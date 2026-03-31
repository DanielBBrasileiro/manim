#!/usr/bin/env node

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const {createRequire} = require("node:module");

const ROOT = path.resolve(__dirname, "..");
const REMOTION_ROOT = path.join(ROOT, "engines", "remotion");
const ENTRY_POINT = path.join(REMOTION_ROOT, "src", "index.tsx");
const PUBLIC_DIR = path.join(REMOTION_ROOT, "public");
const PUBLIC_VIDEO = path.join(PUBLIC_DIR, "manim_base.mp4");
const DEFAULT_COMPOSITION = "CinematicNarrative-v4";
const DEFAULT_TIMEOUT_MS = Number(process.env.REMOTION_RENDER_TIMEOUT_MS || "120000");
const SYSTEM_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const requireFromRemotion = createRequire(path.join(REMOTION_ROOT, "package.json"));
const RENDERER_DIST = path.join(REMOTION_ROOT, "node_modules", "@remotion", "renderer", "dist");

const command = (process.argv[2] || "render").toLowerCase();
const compositionId = process.argv[3] || DEFAULT_COMPOSITION;
const outputLocation = process.argv[4]
  ? path.resolve(process.argv[4])
  : path.join(ROOT, "output", "renders", `${compositionId}.mp4`);

const loadInputProps = () => {
  const raw = process.env.REMOTION_INPUT_PROPS_JSON;
  if (!raw) {
    return {};
  }

  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`REMOTION_INPUT_PROPS_JSON is invalid JSON: ${error.message}`);
  }
};

const inputProps = loadInputProps();

const resolveBrowserExecutable = () => {
  const fromEnv = process.env.REMOTION_BROWSER_EXECUTABLE;
  if (fromEnv && fs.existsSync(fromEnv)) {
    return fromEnv;
  }

  if (fs.existsSync(SYSTEM_CHROME)) {
    return SYSTEM_CHROME;
  }

  return null;
};

const browserExecutable = resolveBrowserExecutable();
let bundlerApi = null;
let rendererApi = null;

const statMtime = (filePath) => {
  if (!fs.existsSync(filePath)) {
    return 0;
  }

  return fs.statSync(filePath).mtimeMs;
};

const latestMtimeInTree = (rootPath) => {
  if (!fs.existsSync(rootPath)) {
    return 0;
  }

  const stat = fs.statSync(rootPath);
  if (!stat.isDirectory()) {
    return stat.mtimeMs;
  }

  let latest = stat.mtimeMs;
  for (const entry of fs.readdirSync(rootPath, {withFileTypes: true})) {
    latest = Math.max(latest, latestMtimeInTree(path.join(rootPath, entry.name)));
  }
  return latest;
};

const syncPublicAssets = (bundlePath) => {
  const bundlePublicDir = path.join(bundlePath, "public");
  console.log(`Sincronizando assets publicos em ${bundlePublicDir}...`);
  fs.mkdirSync(bundlePublicDir, {recursive: true});
  fs.cpSync(PUBLIC_DIR, bundlePublicDir, {recursive: true, force: true});
  console.log("Assets publicos sincronizados.");
};

const findReusableBundle = () => {
  if (process.env.AIOX_REMOTION_REUSE_BUNDLE === "0") {
    return null;
  }

  const tmpDir = os.tmpdir();
  const sourceMtime = Math.max(
    latestMtimeInTree(path.join(REMOTION_ROOT, "src")),
    statMtime(path.join(REMOTION_ROOT, "package.json")),
  );

  try {
    const candidates = fs
      .readdirSync(tmpDir)
      .filter((name) => name.startsWith("remotion-webpack-bundle-"))
      .map((name) => path.join(tmpDir, name))
      .filter((dirPath) => fs.existsSync(path.join(dirPath, "bundle.js")))
      .sort((a, b) => statMtime(b) - statMtime(a));

    for (const candidate of candidates) {
      const bundleMtime = statMtime(candidate);
      if (bundleMtime >= sourceMtime) {
        return candidate;
      }
    }
  } catch (_error) {
    return null;
  }

  return null;
};

const loadBundler = () => {
  if (bundlerApi) {
    return bundlerApi;
  }

  console.log("Carregando @remotion/bundler...");
  const startedAt = Date.now();
  bundlerApi = requireFromRemotion("@remotion/bundler");
  console.log(`@remotion/bundler pronto em ${Date.now() - startedAt}ms`);
  return bundlerApi;
};

const loadRenderer = () => {
  if (rendererApi) {
    return rendererApi;
  }

  console.log("Carregando renderer Remotion...");
  const startedAt = Date.now();
  const {getCompositions} = require(path.join(RENDERER_DIST, "get-compositions.js"));
  const {renderMedia} = require(path.join(RENDERER_DIST, "render-media.js"));
  rendererApi = {getCompositions, renderMedia};
  console.log(`Renderer Remotion pronto em ${Date.now() - startedAt}ms`);
  return rendererApi;
};

const makeRendererOptions = () => ({
  browserExecutable,
  chromiumOptions: {
    headless: true,
    ignoreCertificateErrors: true,
  },
  logLevel: "info",
  timeoutInMilliseconds: DEFAULT_TIMEOUT_MS,
});

const makeBundle = async () => {
  const reusableBundle = findReusableBundle();
  if (reusableBundle) {
    console.log(`Reutilizando bundle existente: ${reusableBundle}`);
    syncPublicAssets(reusableBundle);
    return reusableBundle;
  }

  console.log("Bundling Remotion project...");
  console.log(
    JSON.stringify({
      entryPoint: ENTRY_POINT,
      publicDir: PUBLIC_DIR,
      browserExecutable,
      timeoutMs: DEFAULT_TIMEOUT_MS,
    }),
  );
  const startedAt = Date.now();
  let lastLoggedProgress = -1;
  const {bundle} = loadBundler();

  const serveUrl = await bundle({
    entryPoint: ENTRY_POINT,
    enableCaching: true,
    ignoreRegisterRootWarning: true,
    publicDir: PUBLIC_DIR,
    onProgress: (progress) => {
      const pct = Math.round(progress * 100);
      if (pct >= lastLoggedProgress + 10 || pct === 100) {
        console.log(`Bundle ${pct}%`);
        lastLoggedProgress = pct;
      }
    },
  });

  console.log(`Bundle pronto em ${Date.now() - startedAt}ms`);
  syncPublicAssets(serveUrl);
  return serveUrl;
};

const loadCompositions = async (serveUrl) => {
  console.log("Carregando composicoes...");
  const startedAt = Date.now();
  const {getCompositions} = loadRenderer();
  const compositions = await getCompositions(serveUrl, {
    ...makeRendererOptions(),
    inputProps,
  });
  console.log(`Composicoes carregadas em ${Date.now() - startedAt}ms`);
  return compositions;
};

const listCompositions = async () => {
  const serveUrl = await makeBundle();
  const compositions = await loadCompositions(serveUrl);
  console.log(
    JSON.stringify(
      compositions.map((composition) => ({
        id: composition.id,
        width: composition.width,
        height: composition.height,
        fps: composition.fps,
        durationInFrames: composition.durationInFrames,
      })),
      null,
      2,
    ),
  );
};

const renderComposition = async () => {
  const serveUrl = await makeBundle();
  const compositions = await loadCompositions(serveUrl);
  const composition = compositions.find((item) => item.id === compositionId);

  if (!composition) {
    throw new Error(
      `Composition "${compositionId}" nao encontrada. Disponiveis: ${compositions
        .map((item) => item.id)
        .join(", ")}`,
    );
  }

  fs.mkdirSync(path.dirname(outputLocation), {recursive: true});

  console.log(`Renderizando ${compositionId} para ${outputLocation}...`);
  const startedAt = Date.now();
  let lastLoggedProgress = -1;
  const {renderMedia} = loadRenderer();

  await renderMedia({
    ...makeRendererOptions(),
    codec: "h264",
    composition,
    concurrency: 1,
    inputProps,
    logLevel: "info",
    outputLocation,
    overwrite: true,
    serveUrl,
    timeoutInMilliseconds: DEFAULT_TIMEOUT_MS,
    onProgress: (progress) => {
      const pct = Math.round(progress.progress * 100);
      if (pct >= lastLoggedProgress + 5 || pct === 100) {
        console.log(
          JSON.stringify({
            progress_pct: pct,
            renderedFrames: progress.renderedFrames,
            encodedFrames: progress.encodedFrames,
            stitchStage: progress.stitchStage,
          }),
        );
        lastLoggedProgress = pct;
      }
    },
  });

  if (!fs.existsSync(outputLocation)) {
    throw new Error(`Render finalizado sem criar arquivo: ${outputLocation}`);
  }

  const stats = fs.statSync(outputLocation);
  if (stats.size === 0) {
    throw new Error(`Render criou arquivo vazio: ${outputLocation}`);
  }

  console.log(`Render concluido em ${Date.now() - startedAt}ms`);
  console.log(
    JSON.stringify({
      outputLocation,
      sizeBytes: stats.size,
      mtimeMs: stats.mtimeMs,
    }),
  );
};

const main = async () => {
  if (command === "list") {
    await listCompositions();
    return;
  }

  if (command === "render") {
    await renderComposition();
    return;
  }

  throw new Error(`Comando desconhecido: ${command}. Use "list" ou "render".`);
};

main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
