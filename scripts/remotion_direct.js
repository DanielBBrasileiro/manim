#!/usr/bin/env node
'use strict';

/**
 * remotion_direct.js — Props-file IPC bridge for Remotion renders.
 *
 * Resolves inputProps from:
 *   1. REMOTION_INPUT_PROPS_PATH  — path to a JSON file (primary, no size limit)
 *   2. REMOTION_INPUT_PROPS_JSON  — inline JSON string  (transitional fallback, truncation risk)
 *
 * Fails explicitly when neither env var is set or when the resolved content
 * is not valid JSON.
 *
 * CLI usage:
 *   node scripts/remotion_direct.js \
 *     [--comp  <composition-id>]    default: CinematicNarrative-v4
 *     [--output <relative-path>]    default: output/renders/<comp>.mp4
 *     [--entry  <entry-file>]       default: src/index.tsx
 */

const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

// ---------------------------------------------------------------------------
// Arg parsing
// ---------------------------------------------------------------------------

const argv = process.argv.slice(2);

function getArg(flag) {
  const i = argv.indexOf(flag);
  return i !== -1 && i + 1 < argv.length ? argv[i + 1] : undefined;
}

const comp   = getArg('--comp')   || 'CinematicNarrative-v4';
const entry  = getArg('--entry')  || 'src/index.tsx';
const output = getArg('--output') || path.join('..', '..', 'output', 'renders', `${comp}.mp4`);

// ---------------------------------------------------------------------------
// Props resolution
// ---------------------------------------------------------------------------

/**
 * Returns the path to a validated JSON props file.
 * Throws with a clear message if no valid input exists.
 *
 * @returns {string} Absolute path to the props JSON file.
 */
function resolvePropsFile() {
  const propsPath = process.env.REMOTION_INPUT_PROPS_PATH;

  if (propsPath) {
    const abs = path.resolve(propsPath);

    if (!fs.existsSync(abs)) {
      throw new Error(
        `REMOTION_INPUT_PROPS_PATH points to missing file: ${abs}\n` +
        `Ensure the Python side writes the file before invoking this script.`
      );
    }

    let raw;
    try {
      raw = fs.readFileSync(abs, 'utf8');
    } catch (err) {
      throw new Error(`Failed to read props file ${abs}: ${err.message}`);
    }

    try {
      JSON.parse(raw);
    } catch (err) {
      throw new Error(`Invalid JSON in props file ${abs}: ${err.message}`);
    }

    return abs;
  }

  // -- Transitional fallback: inline JSON env var --
  const jsonEnv = process.env.REMOTION_INPUT_PROPS_JSON;

  if (jsonEnv) {
    process.stderr.write(
      '[remotion_direct] WARNING: falling back to REMOTION_INPUT_PROPS_JSON — ' +
      'large payloads risk OS env truncation. Set REMOTION_INPUT_PROPS_PATH instead.\n'
    );

    let parsed;
    try {
      parsed = JSON.parse(jsonEnv);
    } catch (err) {
      throw new Error(`Invalid JSON in REMOTION_INPUT_PROPS_JSON: ${err.message}`);
    }

    // Materialise to a temp file so Remotion receives it via --props <path>
    const tmpPath = path.join(os.tmpdir(), `aiox_props_fallback_${Date.now()}.json`);
    fs.writeFileSync(tmpPath, JSON.stringify(parsed), 'utf8');
    return tmpPath;
  }

  throw new Error(
    'No input props provided.\n' +
    '  Primary  : set REMOTION_INPUT_PROPS_PATH to a valid JSON file path.\n' +
    '  Fallback : set REMOTION_INPUT_PROPS_JSON to a JSON string (transitional only).'
  );
}

// ---------------------------------------------------------------------------
// Render
// ---------------------------------------------------------------------------

let propsFile;
try {
  propsFile = resolvePropsFile();
} catch (err) {
  process.stderr.write(`[remotion_direct] FATAL: ${err.message}\n`);
  process.exit(1);
}

const remotionRoot = path.resolve(__dirname, '..', 'engines', 'remotion');

try {
  execFileSync(
    'npx',
    ['remotion', 'render', entry, comp, output, '--props', propsFile, '--force'],
    { cwd: remotionRoot, stdio: 'inherit' }
  );
} catch (err) {
  process.stderr.write(`[remotion_direct] Remotion render failed: ${err.message}\n`);
  process.exit(1);
}
