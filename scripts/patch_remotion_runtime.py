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


def patch_ensure_browser_js(path: Path) -> None:
    text = path.read_text()
    text = replace_once(
        text,
        'const BrowserFetcher_1 = require("./browser/BrowserFetcher");\n',
        'const getBrowserFetcher = () => require("./browser/BrowserFetcher");\n',
        label="ensure-browser.js lazy BrowserFetcher import",
        path=path,
        already_applied_markers=('const getBrowserFetcher = () => require("./browser/BrowserFetcher");',),
    )
    replacements = (
        ("BrowserFetcher_1.TESTED_VERSION", "getBrowserFetcher().TESTED_VERSION"),
        ("BrowserFetcher_1.downloadBrowser", "getBrowserFetcher().downloadBrowser"),
        ("BrowserFetcher_1.getRevisionInfo", "getBrowserFetcher().getRevisionInfo"),
        ("BrowserFetcher_1.readVersionFile", "getBrowserFetcher().readVersionFile"),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    path.write_text(text)


def patch_get_local_browser_executable_js(path: Path) -> None:
    text = path.read_text()
    text = replace_once(
        text,
        'const BrowserFetcher_1 = require("./browser/BrowserFetcher");\n',
        'const getBrowserFetcher = () => require("./browser/BrowserFetcher");\n',
        label="get-local-browser-executable.js lazy BrowserFetcher import",
        path=path,
        already_applied_markers=('const getBrowserFetcher = () => require("./browser/BrowserFetcher");',),
    )
    text = text.replace("BrowserFetcher_1.getRevisionInfo", "getBrowserFetcher().getRevisionInfo")
    path.write_text(text)


def patch_open_browser_js(path: Path) -> None:
    text = path.read_text()
    replacements = (
        (
            'const Launcher_1 = require("./browser/Launcher");\n',
            'const launchChrome = (...args) => require("./browser/Launcher").launchChrome(...args);\n',
            "open-browser.js lazy Launcher import",
            ('const launchChrome = (...args) => require("./browser/Launcher").launchChrome(...args);',),
        ),
        (
            'const ensure_browser_1 = require("./ensure-browser");\n',
            'const internalEnsureBrowser = (...args) => require("./ensure-browser").internalEnsureBrowser(...args);\n',
            "open-browser.js lazy ensure-browser import",
            ('const internalEnsureBrowser = (...args) => require("./ensure-browser").internalEnsureBrowser(...args);',),
        ),
        (
            'const get_local_browser_executable_1 = require("./get-local-browser-executable");\n',
            'const getLocalBrowserExecutable = (...args) => require("./get-local-browser-executable").getLocalBrowserExecutable(...args);\n',
            "open-browser.js lazy get-local-browser-executable import",
            ('const getLocalBrowserExecutable = (...args) => require("./get-local-browser-executable").getLocalBrowserExecutable(...args);',),
        ),
        (
            'const get_video_threads_flag_1 = require("./get-video-threads-flag");\n',
            'const getIdealVideoThreadsFlag = (...args) => require("./get-video-threads-flag").getIdealVideoThreadsFlag(...args);\n',
            "open-browser.js lazy video threads import",
            ('const getIdealVideoThreadsFlag = (...args) => require("./get-video-threads-flag").getIdealVideoThreadsFlag(...args);',),
        ),
    )
    for old, new, label, markers in replacements:
        text = replace_once(
            text,
            old,
            new,
            label=label,
            path=path,
            already_applied_markers=markers,
        )
    trace_helper = """
const traceOpenBrowser = (message) => {
    const traceFile = process.env.AIOX_REMOTION_TRACE_FILE;
    if (!traceFile) {
        return;
    }
    try {
        require("node:fs").appendFileSync(traceFile, `${new Date().toISOString()} ${message}\\n`);
    }
    catch (_error) {}
};
"""
    if "const traceOpenBrowser = (message) => {" not in text:
        anchor = 'const logger_1 = require("./logger");\n'
        if anchor not in text:
            raise RuntimeError(
                f"[patch_remotion_runtime] anchor not found for open-browser trace helper in {path}"
            )
        text = text.replace(anchor, anchor + trace_helper, 1)
    text = text.replace(
        "await (0, ensure_browser_1.internalEnsureBrowser)({",
        "await internalEnsureBrowser({",
    )
    text = text.replace(
        "const executablePath = (0, get_local_browser_executable_1.getLocalBrowserExecutable)({",
        "const executablePath = getLocalBrowserExecutable({",
    )
    text = text.replace(
        "const browserInstance = await (0, Launcher_1.launchChrome)({",
        "const browserInstance = await launchChrome({",
    )
    text = text.replace(
        '            `--video-threads=${(0, get_video_threads_flag_1.getIdealVideoThreadsFlag)(logLevel)}`,\n',
        '            `--video-threads=${getIdealVideoThreadsFlag(logLevel)}`,\n',
    )
    trace_replacements = (
        (
            "const internalOpenBrowser = async ({ browser, browserExecutable, chromiumOptions, forceDeviceScaleFactor, indent, viewport, logLevel, onBrowserDownload, chromeMode, }) => {\n",
            "const internalOpenBrowser = async ({ browser, browserExecutable, chromiumOptions, forceDeviceScaleFactor, indent, viewport, logLevel, onBrowserDownload, chromeMode, }) => {\n    traceOpenBrowser(`openBrowser:enter chromeMode=${chromeMode ?? 'unknown'} browserExecutable=${browserExecutable ?? 'auto'}`);\n",
        ),
        (
            "    await internalEnsureBrowser({\n",
            "    traceOpenBrowser(\"openBrowser:before ensureBrowser\");\n    await internalEnsureBrowser({\n",
        ),
        (
            "    logger_1.Log.verbose({ indent, logLevel }, 'Ensured browser is available.');\n",
            "    logger_1.Log.verbose({ indent, logLevel }, 'Ensured browser is available.');\n    traceOpenBrowser(\"openBrowser:after ensureBrowser\");\n",
        ),
        (
            "    const executablePath = getLocalBrowserExecutable({\n",
            "    traceOpenBrowser(\"openBrowser:before getLocalBrowserExecutable\");\n    const executablePath = getLocalBrowserExecutable({\n",
        ),
        (
            "    const customGlRenderer = getOpenGlRenderer((_b = chromiumOptions.gl) !== null && _b !== void 0 ? _b : null);\n",
            "    traceOpenBrowser(`openBrowser:resolved executable=${executablePath}`);\n    const customGlRenderer = getOpenGlRenderer((_b = chromiumOptions.gl) !== null && _b !== void 0 ? _b : null);\n",
        ),
        (
            "    const browserInstance = await launchChrome({\n",
            "    traceOpenBrowser(\"openBrowser:before launchChrome\");\n    const browserInstance = await launchChrome({\n",
        ),
        (
            "    const pages = await browserInstance.pages();\n",
            "    traceOpenBrowser(\"openBrowser:after launchChrome\");\n    const pages = await browserInstance.pages();\n",
        ),
        (
            "    await ((_a = pages[0]) === null || _a === void 0 ? void 0 : _a.close());\n",
            "    traceOpenBrowser(`openBrowser:pages=${pages.length}`);\n    await ((_a = pages[0]) === null || _a === void 0 ? void 0 : _a.close());\n",
        ),
        (
            "    return browserInstance;\n",
            "    traceOpenBrowser(\"openBrowser:return browserInstance\");\n    return browserInstance;\n",
        ),
    )
    for old, new in trace_replacements:
        if old in text and new not in text:
            text = text.replace(old, new, 1)
    path.write_text(text)


def patch_get_browser_instance_js(path: Path) -> None:
    text = path.read_text()
    text = replace_once(
        text,
        'const open_browser_1 = require("./open-browser");\n',
        'const internalOpenBrowser = (...args) => require("./open-browser").internalOpenBrowser(...args);\n',
        label="get-browser-instance.js lazy open-browser import",
        path=path,
        already_applied_markers=('const internalOpenBrowser = (...args) => require("./open-browser").internalOpenBrowser(...args);',),
    )
    text = text.replace(
        "const browserInstance = await (0, open_browser_1.internalOpenBrowser)({",
        "const browserInstance = await internalOpenBrowser({",
    )
    path.write_text(text)


def patch_get_compositions_js(path: Path) -> None:
    text = path.read_text()
    lazy_imports = (
        (
            'const handle_javascript_exception_1 = require("./error-handling/handle-javascript-exception");\n',
            'const handleJavascriptException = (...args) => require("./error-handling/handle-javascript-exception").handleJavascriptException(...args);\n',
            "get-compositions.js lazy handle-javascript-exception import",
            ('const handleJavascriptException = (...args) => require("./error-handling/handle-javascript-exception").handleJavascriptException(...args);',),
        ),
        (
            'const find_closest_package_json_1 = require("./find-closest-package-json");\n',
            'const findRemotionRoot = () => require("./find-closest-package-json").findRemotionRoot();\n',
            "get-compositions.js lazy find-closest-package-json import",
            ('const findRemotionRoot = () => require("./find-closest-package-json").findRemotionRoot();',),
        ),
        (
            'const get_browser_instance_1 = require("./get-browser-instance");\n',
            'const getPageAndCleanupFn = (...args) => require("./get-browser-instance").getPageAndCleanupFn(...args);\n',
            "get-compositions.js lazy get-browser-instance import",
            ('const getPageAndCleanupFn = (...args) => require("./get-browser-instance").getPageAndCleanupFn(...args);',),
        ),
        (
            'const get_available_memory_1 = require("./memory/get-available-memory");\n',
            'const getAvailableMemory = (...args) => require("./memory/get-available-memory").getAvailableMemory(...args);\n',
            "get-compositions.js lazy get-available-memory import",
            ('const getAvailableMemory = (...args) => require("./memory/get-available-memory").getAvailableMemory(...args);',),
        ),
        (
            'const offthreadvideo_threads_1 = require("./options/offthreadvideo-threads");\n',
            'const getDefaultOffthreadVideoThreads = () => require("./options/offthreadvideo-threads").DEFAULT_RENDER_FRAMES_OFFTHREAD_VIDEO_THREADS;\n',
            "get-compositions.js lazy offthreadvideo-threads import",
            ('const getDefaultOffthreadVideoThreads = () => require("./options/offthreadvideo-threads").DEFAULT_RENDER_FRAMES_OFFTHREAD_VIDEO_THREADS;',),
        ),
        (
            'const prepare_server_1 = require("./prepare-server");\n',
            'const makeOrReuseServer = (...args) => require("./prepare-server").makeOrReuseServer(...args);\n',
            "get-compositions.js lazy prepare-server import",
            ('const makeOrReuseServer = (...args) => require("./prepare-server").makeOrReuseServer(...args);',),
        ),
        (
            'const puppeteer_evaluate_1 = require("./puppeteer-evaluate");\n',
            'const puppeteerEvaluateWithCatch = (...args) => require("./puppeteer-evaluate").puppeteerEvaluateWithCatch(...args);\n',
            "get-compositions.js lazy puppeteer-evaluate import",
            ('const puppeteerEvaluateWithCatch = (...args) => require("./puppeteer-evaluate").puppeteerEvaluateWithCatch(...args);',),
        ),
        (
            'const seek_to_frame_1 = require("./seek-to-frame");\n',
            'const waitForReady = (...args) => require("./seek-to-frame").waitForReady(...args);\n',
            "get-compositions.js lazy seek-to-frame import",
            ('const waitForReady = (...args) => require("./seek-to-frame").waitForReady(...args);',),
        ),
        (
            'const set_props_and_env_1 = require("./set-props-and-env");\n',
            'const setPropsAndEnv = (...args) => require("./set-props-and-env").setPropsAndEnv(...args);\n',
            "get-compositions.js lazy set-props-and-env import",
            ('const setPropsAndEnv = (...args) => require("./set-props-and-env").setPropsAndEnv(...args);',),
        ),
        (
            'const wrap_with_error_handling_1 = require("./wrap-with-error-handling");\n',
            'const wrapWithErrorHandling = (...args) => require("./wrap-with-error-handling").wrapWithErrorHandling(...args);\n',
            "get-compositions.js lazy wrap-with-error-handling import",
            ('const wrapWithErrorHandling = (...args) => require("./wrap-with-error-handling").wrapWithErrorHandling(...args);',),
        ),
    )
    for old, new, label, markers in lazy_imports:
        text = replace_once(
            text,
            old,
            new,
            label=label,
            path=path,
            already_applied_markers=markers,
        )
    replacements = (
        ("(0, set_props_and_env_1.setPropsAndEnv)({", "setPropsAndEnv({"),
        ("(0, get_available_memory_1.getAvailableMemory)(logLevel)", "getAvailableMemory(logLevel)"),
        ("(0, puppeteer_evaluate_1.puppeteerEvaluateWithCatch)({", "puppeteerEvaluateWithCatch({"),
        ("(0, seek_to_frame_1.waitForReady)({", "waitForReady({"),
        ("(0, handle_javascript_exception_1.handleJavascriptException)({", "handleJavascriptException({"),
        ("(0, find_closest_package_json_1.findRemotionRoot)()", "findRemotionRoot()"),
        (
            "offthreadvideo_threads_1.DEFAULT_RENDER_FRAMES_OFFTHREAD_VIDEO_THREADS",
            "getDefaultOffthreadVideoThreads()",
        ),
        ("const { page, cleanupPage } = await (0, get_browser_instance_1.getPageAndCleanupFn)({", "const { page, cleanupPage } = await getPageAndCleanupFn({"),
        ("(0, prepare_server_1.makeOrReuseServer)(server, {", "makeOrReuseServer(server, {"),
        (
            "exports.internalGetCompositions = (0, wrap_with_error_handling_1.wrapWithErrorHandling)(internalGetCompositionsRaw);",
            "exports.internalGetCompositions = wrapWithErrorHandling(internalGetCompositionsRaw);",
        ),
    )
    for old, new in replacements:
        text = text.replace(old, new)
    trace_helper = """
const traceGetCompositions = (message) => {
    const traceFile = process.env.AIOX_REMOTION_TRACE_FILE;
    if (!traceFile) {
        return;
    }
    try {
        require("node:fs").appendFileSync(traceFile, `${new Date().toISOString()} ${message}\\n`);
    }
    catch (_error) {}
};
"""
    if "const traceGetCompositions = (message) => {" not in text:
        anchor = 'const wrapWithErrorHandling = (...args) => require("./wrap-with-error-handling").wrapWithErrorHandling(...args);\n'
        if anchor not in text:
            raise RuntimeError(
                f"[patch_remotion_runtime] anchor not found for get-compositions trace helper in {path}"
            )
        text = text.replace(anchor, anchor + trace_helper, 1)
    trace_replacements = (
        (
            "const internalGetCompositionsRaw = async ({ browserExecutable, chromiumOptions, envVariables, indent, serializedInputPropsWithCustomSchema, onBrowserLog, port, puppeteerInstance, serveUrlOrWebpackUrl, server, timeoutInMilliseconds, logLevel, offthreadVideoCacheSizeInBytes, binariesDirectory, onBrowserDownload, chromeMode, offthreadVideoThreads, mediaCacheSizeInBytes, onLog, }) => {\n",
            "const internalGetCompositionsRaw = async ({ browserExecutable, chromiumOptions, envVariables, indent, serializedInputPropsWithCustomSchema, onBrowserLog, port, puppeteerInstance, serveUrlOrWebpackUrl, server, timeoutInMilliseconds, logLevel, offthreadVideoCacheSizeInBytes, binariesDirectory, onBrowserDownload, chromeMode, offthreadVideoThreads, mediaCacheSizeInBytes, onLog, }) => {\n    traceGetCompositions(\"getCompositions:entered internalGetCompositionsRaw\");\n",
        ),
        (
            "    const { page, cleanupPage } = await getPageAndCleanupFn({\n",
            "    traceGetCompositions(\"getCompositions:before getPageAndCleanupFn\");\n    const { page, cleanupPage } = await getPageAndCleanupFn({\n",
        ),
        (
            "    const cleanup = [cleanupPage];\n",
            "    traceGetCompositions(\"getCompositions:after getPageAndCleanupFn\");\n    const cleanup = [cleanupPage];\n",
        ),
        (
            "        makeOrReuseServer(server, {\n",
            "        traceGetCompositions(\"getCompositions:before makeOrReuseServer\");\n        makeOrReuseServer(server, {\n",
        ),
        (
            "            page.setBrowserSourceMapGetter(sourceMap);\n",
            "            traceGetCompositions(\"getCompositions:after makeOrReuseServer\");\n            page.setBrowserSourceMapGetter(sourceMap);\n",
        ),
        (
            "            return innerGetCompositions({\n",
            "            traceGetCompositions(\"getCompositions:before innerGetCompositions\");\n            return innerGetCompositions({\n",
        ),
        (
            "            return resolve(comp);\n",
            "            traceGetCompositions(\"getCompositions:after innerGetCompositions\");\n            return resolve(comp);\n",
        ),
    )
    for old, new in trace_replacements:
        if old in text and new not in text:
            text = text.replace(old, new, 1)
    path.write_text(text)


def patch_browser_runner_js(path: Path) -> None:
    text = path.read_text()
    trace_helper = """
const traceBrowserRunner = (message) => {
    const traceFile = process.env.AIOX_REMOTION_TRACE_FILE;
    if (!traceFile) {
        return;
    }
    try {
        require("node:fs").appendFileSync(traceFile, `${new Date().toISOString()} ${message}\\n`);
    }
    catch (_error) {}
};
"""
    if "const traceBrowserRunner = (message) => {" not in text:
        anchor = 'const util_1 = require("./util");\n'
        if anchor not in text:
            raise RuntimeError(
                f"[patch_remotion_runtime] anchor not found for BrowserRunner trace helper in {path}"
            )
        text = text.replace(anchor, anchor + trace_helper, 1)
    trace_replacements = (
        (
            "const makeBrowserRunner = async ({ executablePath, processArguments, userDataDir, logLevel, indent, timeout, }) => {\n",
            "const makeBrowserRunner = async ({ executablePath, processArguments, userDataDir, logLevel, indent, timeout, }) => {\n    traceBrowserRunner(`BrowserRunner:make start executable=${executablePath}`);\n",
        ),
        (
            "    const proc = childProcess.spawn(executablePath, processArguments, {\n",
            "    traceBrowserRunner(\"BrowserRunner:before spawn\");\n    const proc = childProcess.spawn(executablePath, processArguments, {\n",
        ),
        (
            "    const browserWSEndpoint = await waitForWSEndpoint({\n",
            "    traceBrowserRunner(`BrowserRunner:spawned pid=${proc.pid ?? 'unknown'}`);\n    const browserWSEndpoint = await waitForWSEndpoint({\n",
        ),
        (
            "    const transport = await NodeWebSocketTransport_1.NodeWebSocketTransport.create(browserWSEndpoint);\n",
            "    traceBrowserRunner(`BrowserRunner:ws endpoint=${browserWSEndpoint}`);\n    const transport = await NodeWebSocketTransport_1.NodeWebSocketTransport.create(browserWSEndpoint);\n",
        ),
        (
            "    const connection = new Connection_1.Connection(transport);\n",
            "    traceBrowserRunner(\"BrowserRunner:transport connected\");\n    const connection = new Connection_1.Connection(transport);\n",
        ),
        (
            "        browserStderr.addListener('data', onStdIoData);\n",
            "        traceBrowserRunner(\"BrowserRunner:waitForWSEndpoint begin\");\n        browserStderr.addListener('data', onStdIoData);\n",
        ),
        (
            "        function onClose(error) {\n",
            "        function onClose(error) {\n            traceBrowserRunner(`BrowserRunner:onClose ${error ? error.message : 'no-error'}`);\n",
        ),
        (
            "        function onTimeout() {\n",
            "        function onTimeout() {\n            traceBrowserRunner(`BrowserRunner:onTimeout timeout=${timeout}`);\n",
        ),
        (
            "        function onStdIoData(data) {\n",
            "        function onStdIoData(data) {\n            traceBrowserRunner(`BrowserRunner:stdio ${String(data).slice(0, 200).replace(/\\s+/g, ' ')}`);\n",
        ),
        (
            "            resolve(match[1]);\n",
            "            traceBrowserRunner(`BrowserRunner:resolved ws=${match[1]}`);\n            resolve(match[1]);\n",
        ),
    )
    for old, new in trace_replacements:
        if old in text and new not in text:
            text = text.replace(old, new, 1)
    path.write_text(text)


def patch_launcher_js(path: Path) -> None:
    text = path.read_text()
    trace_helper = """
const traceLauncher = (message) => {
    const traceFile = process.env.AIOX_REMOTION_TRACE_FILE;
    if (!traceFile) {
        return;
    }
    try {
        require("node:fs").appendFileSync(traceFile, `${new Date().toISOString()} ${message}\\n`);
    }
    catch (_error) {}
};
"""
    if "const traceLauncher = (message) => {" not in text:
        anchor = 'const Browser_1 = require("./Browser");\n'
        if anchor not in text:
            raise RuntimeError(
                f"[patch_remotion_runtime] anchor not found for Launcher trace helper in {path}"
            )
        text = text.replace(anchor, anchor + trace_helper, 1)
    bad_recursive = '    traceLauncher("Launcher:after HeadlessBrowser.create");\n'
    if bad_recursive in text:
        text = text.replace(bad_recursive, "", 1)
    trace_replacements = (
        (
            "const launchChrome = async ({ args, executablePath, defaultViewport, indent, logLevel, userDataDir, timeout, }) => {\n",
            "const launchChrome = async ({ args, executablePath, defaultViewport, indent, logLevel, userDataDir, timeout, }) => {\n    traceLauncher(`Launcher:enter executable=${executablePath}`);\n",
        ),
        (
            "    const browser = await Browser_1.HeadlessBrowser.create({\n",
            "    traceLauncher(\"Launcher:before HeadlessBrowser.create\");\n    const browser = await Browser_1.HeadlessBrowser.create({\n",
        ),
        (
            "    });\n    try {\n",
            "    });\n    traceLauncher(\"Launcher:after HeadlessBrowser.create\");\n    try {\n",
        ),
        (
            "        await browser.waitForTarget((t) => {\n",
            "        traceLauncher(\"Launcher:before waitForTarget(page)\");\n        await browser.waitForTarget((t) => {\n",
        ),
        (
            "    return browser;\n",
            "    traceLauncher(\"Launcher:return browser\");\n    return browser;\n",
        ),
    )
    for old, new in trace_replacements:
        if old in text and new not in text:
            text = text.replace(old, new, 1)
    path.write_text(text)


def main() -> int:
    targets = {
        BUNDLER_DIST / "bundle.js": patch_bundle_js,
        BUNDLER_DIST / "webpack-config.js": patch_webpack_config_js,
        BUNDLER_DIST / "shared-bundler-config.js": patch_shared_bundler_config_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "ensure-browser.js": patch_ensure_browser_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "get-local-browser-executable.js": patch_get_local_browser_executable_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "open-browser.js": patch_open_browser_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "get-browser-instance.js": patch_get_browser_instance_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "get-compositions.js": patch_get_compositions_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "browser" / "BrowserRunner.js": patch_browser_runner_js,
        REMOTION_ROOT / "node_modules" / "@remotion" / "renderer" / "dist" / "browser" / "Launcher.js": patch_launcher_js,
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
