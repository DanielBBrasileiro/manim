#!/usr/bin/env python3
"""Apply stable local patches to the Remotion runtime after npm install.

These patches make the local renderer more reliable on this repo's Apple
Silicon setup by:
- avoiding eager rspack imports unless rspack is explicitly enabled
- avoiding eager fast-refresh imports in production bundling
- removing aliases that force-resolve optional Remotion studio/media parser
  modules during headless runtime bundling
"""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
REMOTION_ROOT = ROOT / "engines" / "remotion"
BUNDLER_DIST = REMOTION_ROOT / "node_modules" / "@remotion" / "bundler" / "dist"


def replace_once(
    text: str,
    old: str,
    new: str,
    *,
    label: str,
    path: Path,
    already_applied_markers: tuple[str, ...] = (),
) -> str:
    if new and new in text:
        return text
    if already_applied_markers and any(marker in text for marker in already_applied_markers):
        return text
    if old not in text:
        raise RuntimeError(f"[patch_remotion_runtime] pattern not found for {label} in {path}")
    return text.replace(old, new, 1)


def patch_bundle_js(path: Path) -> None:
    text = path.read_text()
    text = replace_once(
        text,
        'const rspack_config_1 = require("./rspack-config");\n',
        "",
        label="bundle.js eager rspack import",
        path=path,
        already_applied_markers=('const {rspackConfig} = require("./rspack-config");',),
    )
    text = replace_once(
        text,
        """    if (options.rspack) {
        return (0, rspack_config_1.rspackConfig)(configArgs);
    }
""",
        """    if (options.rspack) {
        const {rspackConfig} = require("./rspack-config");
        return rspackConfig(configArgs);
    }
""",
        label="bundle.js lazy rspack config",
        path=path,
        already_applied_markers=('const {rspackConfig} = require("./rspack-config");',),
    )
    path.write_text(text)


def patch_webpack_config_js(path: Path) -> None:
    text = path.read_text()
    text = replace_once(
        text,
        'const fast_refresh_1 = require("./fast-refresh");\n',
        "",
        label="webpack-config.js eager fast refresh import",
        path=path,
        already_applied_markers=('require("./fast-refresh").ReactFreshWebpackPlugin',),
    )
    text = replace_once(
        text,
        "new fast_refresh_1.ReactFreshWebpackPlugin(),",
        'new (require("./fast-refresh").ReactFreshWebpackPlugin)(),',
        label="webpack-config.js lazy fast refresh plugin",
        path=path,
        already_applied_markers=('require("./fast-refresh").ReactFreshWebpackPlugin',),
    )
    path.write_text(text)


def patch_shared_bundler_config_js(path: Path) -> None:
    text = path.read_text()
    block = """        '@remotion/media-parser/worker': node_path_1.default.resolve(require.resolve('@remotion/media-parser'), '..', 'esm', 'worker.mjs'),
        // test visual controls before removing this
        '@remotion/studio': require.resolve('@remotion/studio'),
"""
    if block in text:
        text = text.replace(block, "", 1)
        path.write_text(text)
        return

    if "@remotion/media-parser/worker" in text or "@remotion/studio" in text:
        raise RuntimeError(
            f"[patch_remotion_runtime] partial alias block found in {path}; refusing ambiguous patch"
        )


def main() -> int:
    targets = {
        BUNDLER_DIST / "bundle.js": patch_bundle_js,
        BUNDLER_DIST / "webpack-config.js": patch_webpack_config_js,
        BUNDLER_DIST / "shared-bundler-config.js": patch_shared_bundler_config_js,
    }

    for path, patcher in targets.items():
        if not path.exists():
            print(f"[patch_remotion_runtime] skip missing {path}")
            continue
        patcher(path)
        print(f"[patch_remotion_runtime] patched {path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
