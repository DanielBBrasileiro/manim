"""Remotion engine adapter — wraps daemon, CLI and direct subprocess paths."""
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from core.tools.engine_adapter import EngineAdapter

ROOT = Path(__file__).resolve().parent.parent.parent

_DEFAULT_RENDER_TIMEOUT = int(os.getenv("AIOX_REMOTION_CLI_TIMEOUT_SECONDS", "45"))
_DEFAULT_DIRECT_TIMEOUT = int(os.getenv("AIOX_REMOTION_DIRECT_TIMEOUT_SECONDS", "180"))
_DEFAULT_STILL_DIRECT_TIMEOUT = int(os.getenv("AIOX_REMOTION_STILL_TIMEOUT_SECONDS", "180"))
_DEFAULT_STILL_CLI_TIMEOUT = int(os.getenv("AIOX_REMOTION_STILL_CLI_TIMEOUT_SECONDS", "180"))
_DEFAULT_VIDEO_DIRECT_TIMEOUT = int(
    os.getenv("AIOX_REMOTION_VIDEO_TIMEOUT_SECONDS", str(max(_DEFAULT_DIRECT_TIMEOUT, 360)))
)
_DEFAULT_VIDEO_CLI_TIMEOUT = int(
    os.getenv("AIOX_REMOTION_VIDEO_CLI_TIMEOUT_SECONDS", str(max(_DEFAULT_RENDER_TIMEOUT, 360)))
)
_DEFAULT_DAEMON_BOOT_TIMEOUT = int(os.getenv("AIOX_REMOTION_DAEMON_BOOT_TIMEOUT_SECONDS", "15"))
_DAEMON_PORT = int(os.getenv("REMOTION_DAEMON_PORT", "3333"))
_DAEMON_URL = f"http://127.0.0.1:{_DAEMON_PORT}"


def _validate_output(output_path: Path) -> None:
    if not output_path.exists():
        raise RuntimeError(f"Render nao gerou arquivo: {output_path}")
    if output_path.stat().st_size == 0:
        raise RuntimeError(f"Render criou arquivo vazio: {output_path}")


def _runner() -> str:
    return str(ROOT / "scripts" / "run_remotion_node.sh")


def _build_env(
    props: dict[str, Any] | None = None,
    *,
    timeout_seconds: int | None = None,
    concurrency: int | None = None,
) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("AIOX_REMOTION_REUSE_BUNDLE", "1")
    if props is not None:
        env["REMOTION_INPUT_PROPS_JSON"] = json.dumps(props)
        try:
            audit_path = ROOT / "output" / "video" / "audit_manifest.json"
            audit_path.parent.mkdir(parents=True, exist_ok=True)
            with open(audit_path, "w") as fh:
                json.dump(props, fh, indent=2)
        except Exception:
            pass
    if timeout_seconds is not None:
        env["REMOTION_RENDER_TIMEOUT_MS"] = str(max(timeout_seconds, 1) * 1000)
    if concurrency is not None:
        env.setdefault("REMOTION_CONCURRENCY", str(concurrency))
    return env


def _run_direct_node(args: list[str], timeout: int | None = None) -> subprocess.CompletedProcess:
    script = str(ROOT / "scripts" / "remotion_direct.js")
    runner = _runner()
    env = _build_env()
    return subprocess.run(
        ["/bin/bash", runner, script] + args,
        check=True,
        cwd=str(ROOT),
        env=env,
        timeout=timeout,
    )


def _ping_daemon(timeout_seconds: float = 1.5) -> bool:
    try:
        with urllib.request.urlopen(f"{_DAEMON_URL}/health", timeout=timeout_seconds) as resp:
            return bool(json.loads(resp.read().decode())["ok"])
    except Exception:
        return False


def _start_daemon() -> None:
    runner = _runner()
    daemon_script = str(ROOT / "scripts" / "remotion_daemon.js")
    log_path = ROOT / "output" / "logs" / "remotion_daemon.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = _build_env(timeout_seconds=max(_DEFAULT_VIDEO_DIRECT_TIMEOUT, _DEFAULT_DAEMON_BOOT_TIMEOUT))
    env["REMOTION_DAEMON_PORT"] = str(_DAEMON_PORT)
    with open(log_path, "ab") as log_fh:
        subprocess.Popen(
            ["/bin/bash", runner, daemon_script],
            cwd=str(ROOT),
            env=env,
            stdout=log_fh,
            stderr=log_fh,
            start_new_session=True,
        )


def _ensure_daemon(timeout_seconds: int = _DEFAULT_DAEMON_BOOT_TIMEOUT) -> bool:
    if _ping_daemon():
        print(f"⚡ [Remotion] Daemon quente em {_DAEMON_URL}.")
        try:
            req = urllib.request.Request(
                f"{_DAEMON_URL}/warm", data=b"{}", headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=1.5).read()
        except Exception:
            pass
        return True

    print(f"🚀 [Remotion] Iniciando daemon em {_DAEMON_URL}...")
    try:
        _start_daemon()
    except Exception as err:
        print(f"⚠️ [Remotion] Falha ao iniciar daemon: {err}")
        return False

    deadline = time.time() + max(timeout_seconds, 1)
    while time.time() < deadline:
        if _ping_daemon():
            print("✅ [Remotion] Daemon pronto.")
            try:
                req = urllib.request.Request(
                    f"{_DAEMON_URL}/warm", data=b"{}", headers={"Content-Type": "application/json"}
                )
                urllib.request.urlopen(req, timeout=1.5).read()
            except Exception:
                pass
            return True
        time.sleep(0.25)

    print("⚠️ [Remotion] Daemon não respondeu. Voltando para subprocess.")
    return False


def _run_via_daemon(
    command: str,
    composition: str,
    output_path: Path,
    props: dict[str, Any],
    timeout_seconds: int,
) -> bool:
    try:
        if not _ensure_daemon():
            return False
        data = json.dumps(
            {
                "command": command,
                "requestedCompositionId": composition,
                "outputLocation": str(output_path),
                "inputProps": props,
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            f"{_DAEMON_URL}/render", data=data, headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            if not res.get("ok"):
                print(f"⚠️ [Daemon] Erro interno: {res.get('error')}")
                return False
            print(f"⚡ [Remotion] {command} via daemon para '{composition}'.")
            return True
    except Exception:
        return False


def _run_command(
    command: str,
    composition: str,
    output_path: Path,
    props: dict[str, Any],
    *,
    direct_timeout_seconds: int,
    cli_timeout_seconds: int,
    concurrency: int | None = None,
) -> None:
    runner = _runner()
    render_mode = os.getenv("AIOX_REMOTION_RENDER_MODE", "auto").strip().lower()
    effective_timeout = max(cli_timeout_seconds, direct_timeout_seconds)

    if os.getenv("AIOX_SKIP_REMOTION") == "1":
        raise RuntimeError("Remotion skipped by user")

    if render_mode in ("auto", "daemon"):
        if _run_via_daemon(command, composition, output_path, props, effective_timeout):
            return

    env = _build_env(props, timeout_seconds=effective_timeout, concurrency=concurrency)
    cli_cmd = [
        "/bin/zsh",
        "-lc",
        (
            f"cd {ROOT / 'engines' / 'remotion'} && {runner} "
            f"./node_modules/.bin/remotion {command} src/index.tsx "
            f"{composition} {output_path.as_posix()} --force"
        ),
    ]
    direct_cmd = [
        "/bin/bash",
        runner,
        str(ROOT / "scripts" / "remotion_direct.js"),
        command,
        composition,
        str(output_path),
    ]

    if render_mode == "direct":
        subprocess.run(direct_cmd, check=True, cwd=str(ROOT), env=env, timeout=direct_timeout_seconds)
    elif render_mode == "cli":
        subprocess.run(cli_cmd, check=True, cwd=str(ROOT), env=env, timeout=cli_timeout_seconds)
    else:
        try:
            subprocess.run(direct_cmd, check=True, cwd=str(ROOT), env=env, timeout=direct_timeout_seconds)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("⚠️ [Remotion] Renderer direto falhou. Tentando CLI...")
            subprocess.run(cli_cmd, check=True, cwd=str(ROOT), env=env, timeout=cli_timeout_seconds)


class RemotionAdapter(EngineAdapter):
    """Remotion engine: daemon-first with subprocess fallback."""

    def prepare(self, artifact_plan: dict) -> None:
        targets = artifact_plan.get("targets", [])
        if targets and all(
            str(t.get("render_mode", "")).lower() == "still"
            for t in targets
            if isinstance(t, dict)
        ):
            print("🪶 [Remotion] Pipeline de stills. Pulando warmup redundante.")
            return
        print("🔥 [Remotion] Preaquecendo bundle...")
        try:
            _run_direct_node(["warm"], timeout=180)
        except Exception as err:
            print(f"⚠️ [Remotion] Warmup não completou: {err}. Continuando...")

    def render_still(self, composition: str, output_path: Path, props: dict) -> Path:
        print("🖼️ [Remotion] Compondo still premium...")
        still_output = (
            output_path if output_path.suffix.lower() == ".png" else output_path.with_suffix(".png")
        )
        still_output.parent.mkdir(parents=True, exist_ok=True)
        previous_mtime = still_output.stat().st_mtime if still_output.exists() else 0

        _run_command(
            "still",
            composition,
            still_output,
            props,
            direct_timeout_seconds=_DEFAULT_STILL_DIRECT_TIMEOUT,
            cli_timeout_seconds=_DEFAULT_STILL_CLI_TIMEOUT,
        )
        _validate_output(still_output)
        if still_output.stat().st_mtime <= previous_mtime:
            raise RuntimeError(f"Still não atualizou o arquivo esperado: {still_output}")
        return still_output

    def render_video(self, composition: str, output_path: Path, props: dict) -> Path:
        print("🎬 [Remotion] Compondo narrativa final...")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        previous_mtime = output_path.stat().st_mtime if output_path.exists() else 0

        _run_command(
            "render",
            composition,
            output_path,
            props,
            direct_timeout_seconds=_DEFAULT_VIDEO_DIRECT_TIMEOUT,
            cli_timeout_seconds=_DEFAULT_VIDEO_CLI_TIMEOUT,
            concurrency=2,
        )
        _validate_output(output_path)
        if output_path.stat().st_mtime <= previous_mtime:
            raise RuntimeError(f"Render não atualizou o arquivo esperado: {output_path}")
        return output_path

    def cleanup(self) -> None:
        pass  # Daemon is persistent; no teardown needed per-render.
