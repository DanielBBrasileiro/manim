"""Remotion engine adapter — wraps daemon, CLI and direct subprocess paths."""
import json
import os
import socket
import subprocess
import tempfile
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
    props_path: Path | None = None,
    props_json: dict[str, Any] | None = None,
    *,
    timeout_seconds: int | None = None,
    concurrency: int | None = None,
) -> dict[str, str]:
    env = dict(os.environ)
    env.setdefault("AIOX_REMOTION_REUSE_BUNDLE", "1")
    if props_path is not None:
        env["REMOTION_INPUT_PROPS_PATH"] = str(props_path)
    if props_json is not None:
        env["REMOTION_INPUT_PROPS_JSON"] = json.dumps(props_json)
    if timeout_seconds is not None:
        env["REMOTION_RENDER_TIMEOUT_MS"] = str(max(timeout_seconds, 1) * 1000)
    if concurrency is not None:
        env.setdefault("REMOTION_CONCURRENCY", str(concurrency))
    return env


def _write_props_file(props: dict[str, Any]) -> Path | None:
    try:
        props_dir = ROOT / "output" / "remotion_props"
        props_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            prefix="props_",
            dir=props_dir,
            delete=False,
        ) as handle:
            json.dump(props, handle, indent=2)
            return Path(handle.name)
    except Exception:
        return None


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


def _port_is_open(timeout_seconds: float = 0.5) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout_seconds)
    try:
        return sock.connect_ex(("127.0.0.1", _DAEMON_PORT)) == 0
    finally:
        sock.close()


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
        return True

    deadline = time.time() + max(timeout_seconds, 1)
    if _port_is_open():
        print(f"⏳ [Remotion] Porta {_DAEMON_PORT} já está ocupada. Aguardando daemon existente...")
        while time.time() < deadline:
            if _ping_daemon():
                print(f"⚡ [Remotion] Daemon respondeu em {_DAEMON_URL}.")
                return True
            time.sleep(0.25)
        print("⚠️ [Remotion] Porta ocupada, mas o daemon não respondeu. Voltando para subprocess.")
        return False

    print(f"🚀 [Remotion] Iniciando daemon em {_DAEMON_URL}...")
    try:
        _start_daemon()
    except Exception as err:
        print(f"⚠️ [Remotion] Falha ao iniciar daemon: {err}")
        return False

    while time.time() < deadline:
        if _ping_daemon():
            print("✅ [Remotion] Daemon pronto.")
            return True
        time.sleep(0.25)

    print("⚠️ [Remotion] Daemon não respondeu. Voltando para subprocess.")
    return False


def _run_via_daemon(
    command: str,
    composition: str,
    output_path: Path,
    props: dict[str, Any],
    props_path: Path | None,
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
                "propsPath": str(props_path) if props_path else None,
                "inputProps": props if props_path is None else None,
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
    props_path = _write_props_file(props)

    if os.getenv("AIOX_SKIP_REMOTION") == "1":
        raise RuntimeError("Remotion skipped by user")

    if render_mode in ("auto", "daemon"):
        if _run_via_daemon(command, composition, output_path, props, props_path, effective_timeout):
            return

    env = _build_env(
        props_path=props_path,
        props_json=props if props_path is None else None,
        timeout_seconds=effective_timeout,
        concurrency=concurrency,
    )
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
        print("🔥 [Remotion] Verificando daemon antes do render...")
        if not _ensure_daemon():
            print("⚠️ [Remotion] Daemon indisponível. Continuando com fallback lazy.")
            return
        print("⚡ [Remotion] Daemon pronto. Bundle seguirá lazy no primeiro render.")

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
