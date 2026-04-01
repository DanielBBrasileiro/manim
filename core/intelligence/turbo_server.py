"""
turbo_server.py — TurboQuant llama-server lifecycle manager.

Manages a local llama-server instance with TurboQuant KV cache compression.
Provides an OpenAI-compatible API endpoint for the AIOX inference pipeline,
with automatic fallback to Ollama if the turbo server is unavailable.

TurboQuant (ICLR 2026) compresses KV cache 3.8-4.9x via PolarQuant +
Walsh-Hadamard Transform, enabling:
  - 14B models where 7B used to fit
  - 32K context where 4K was the limit
  - No retraining required
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.env_loader import load_repo_env

load_repo_env()

ROOT = Path(__file__).resolve().parent.parent.parent
TURBO_DIR = ROOT / ".turbo"
TURBO_ENV = TURBO_DIR / "turbo.env"


@dataclass
class TurboConfig:
    """Configuration for the TurboQuant server."""
    server_bin: str = ""
    model_path: str = ""
    port: int = 8081
    cache_type_k: str = "q8_0"
    cache_type_v: str = "turbo4"
    flash_attention: bool = True
    context_length: int = 32768
    gpu_layers: int = 99
    threads: int = 0  # 0 = auto
    batch_size: int = 512

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def completion_url(self) -> str:
        return f"{self.base_url}/v1/chat/completions"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}/health"

    @property
    def is_configured(self) -> bool:
        return bool(self.server_bin) and Path(self.server_bin).exists()

    @property
    def has_model(self) -> bool:
        return bool(self.model_path) and Path(self.model_path).exists()


@dataclass
class TurboServerStatus:
    """Status of the TurboQuant server."""
    installed: bool = False
    running: bool = False
    healthy: bool = False
    port: int = 8081
    pid: int | None = None
    model_loaded: str = ""
    cache_type_k: str = ""
    cache_type_v: str = ""
    context_length: int = 0
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "installed": self.installed,
            "running": self.running,
            "healthy": self.healthy,
            "port": self.port,
            "pid": self.pid,
            "model_loaded": self.model_loaded,
            "cache_type_k": self.cache_type_k,
            "cache_type_v": self.cache_type_v,
            "context_length": self.context_length,
            "error": self.error,
        }


def _load_turbo_env() -> dict[str, str]:
    """Load configuration from .turbo/turbo.env."""
    config: dict[str, str] = {}
    if not TURBO_ENV.exists():
        return config
    for line in TURBO_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip()
    return config


def load_config() -> TurboConfig:
    """Load TurboQuant configuration from env + turbo.env."""
    turbo_env = _load_turbo_env()

    return TurboConfig(
        server_bin=os.environ.get(
            "AIOX_TURBO_SERVER_BIN",
            turbo_env.get("AIOX_TURBO_SERVER_BIN", ""),
        ),
        model_path=os.environ.get(
            "AIOX_TURBO_MODEL_PATH",
            turbo_env.get("AIOX_TURBO_MODEL_PATH", ""),
        ),
        port=int(os.environ.get(
            "AIOX_TURBO_PORT",
            turbo_env.get("AIOX_TURBO_PORT", "8081"),
        )),
        cache_type_k=os.environ.get(
            "AIOX_TURBO_CACHE_TYPE_K",
            turbo_env.get("AIOX_TURBO_CACHE_TYPE_K", "q8_0"),
        ),
        cache_type_v=os.environ.get(
            "AIOX_TURBO_CACHE_TYPE_V",
            turbo_env.get("AIOX_TURBO_CACHE_TYPE_V", "turbo4"),
        ),
        flash_attention=os.environ.get(
            "AIOX_TURBO_FLASH_ATTENTION",
            turbo_env.get("AIOX_TURBO_FLASH_ATTENTION", "1"),
        ) in ("1", "true", "yes"),
        context_length=int(os.environ.get(
            "AIOX_TURBO_CONTEXT_LENGTH",
            turbo_env.get("AIOX_TURBO_CONTEXT_LENGTH", "32768"),
        )),
        gpu_layers=int(os.environ.get(
            "AIOX_TURBO_GPU_LAYERS",
            turbo_env.get("AIOX_TURBO_GPU_LAYERS", "99"),
        )),
    )


# ---------------------------------------------------------------------------
# Server lifecycle
# ---------------------------------------------------------------------------

def check_health(config: TurboConfig | None = None, timeout: float = 3.0) -> TurboServerStatus:
    """Check if the TurboQuant server is running and healthy."""
    cfg = config or load_config()
    status = TurboServerStatus(
        installed=cfg.is_configured,
        port=cfg.port,
        cache_type_k=cfg.cache_type_k,
        cache_type_v=cfg.cache_type_v,
        context_length=cfg.context_length,
    )

    if not cfg.is_configured:
        status.error = "TurboQuant not installed. Run: bash scripts/setup_turboquant.sh"
        return status

    try:
        req = urllib.request.Request(cfg.health_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        status.running = True
        status.healthy = data.get("status") == "ok" or "slots" in data
        status.model_loaded = data.get("model", "")
    except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError, OSError) as exc:
        status.error = f"Server not reachable: {type(exc).__name__}"
    except Exception as exc:
        status.error = f"Health check error: {exc}"

    return status


def start_server(
    config: TurboConfig | None = None,
    wait_seconds: float = 8.0,
) -> TurboServerStatus:
    """
    Start the TurboQuant llama-server in the background.

    Returns the server status after startup.
    """
    cfg = config or load_config()

    if not cfg.is_configured:
        return TurboServerStatus(error="TurboQuant not installed")
    if not cfg.has_model:
        return TurboServerStatus(
            installed=True,
            error=f"No model configured. Set AIOX_TURBO_MODEL_PATH in .env",
        )

    # Check if already running
    current = check_health(cfg)
    if current.healthy:
        return current

    # Build command
    cmd = [
        cfg.server_bin,
        "-m", cfg.model_path,
        "--cache-type-k", cfg.cache_type_k,
        "--cache-type-v", cfg.cache_type_v,
        "--port", str(cfg.port),
        "-ngl", str(cfg.gpu_layers),
        "-c", str(cfg.context_length),
        "--batch-size", str(cfg.batch_size),
    ]

    if cfg.flash_attention:
        cmd.extend(["-fa", "1"])

    if cfg.threads > 0:
        cmd.extend(["-t", str(cfg.threads)])

    # Launch in background
    try:
        log_path = TURBO_DIR / "server.log"
        log_file = open(log_path, "a")
        proc = subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        pid_path = TURBO_DIR / "server.pid"
        pid_path.write_text(str(proc.pid))
    except Exception as exc:
        return TurboServerStatus(
            installed=True,
            error=f"Failed to start: {exc}",
        )

    # Wait for healthy status
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        status = check_health(cfg, timeout=2.0)
        if status.healthy:
            status.pid = proc.pid
            return status
        time.sleep(0.5)

    return TurboServerStatus(
        installed=True,
        running=proc.poll() is None,
        pid=proc.pid,
        port=cfg.port,
        error="Server started but not healthy within timeout",
    )


def stop_server(config: TurboConfig | None = None) -> bool:
    """Stop the TurboQuant server."""
    cfg = config or load_config()
    pid_path = TURBO_DIR / "server.pid"

    if not pid_path.exists():
        return False

    try:
        pid = int(pid_path.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        pid_path.unlink(missing_ok=True)
        return True
    except (ProcessLookupError, ValueError, OSError):
        pid_path.unlink(missing_ok=True)
        return False


# ---------------------------------------------------------------------------
# OpenAI-compatible API client
# ---------------------------------------------------------------------------

def turbo_generate(
    prompt: str,
    config: TurboConfig | None = None,
    *,
    system_prompt: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = 2048,
    response_format: dict[str, Any] | None = None,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """
    Generate a completion using the TurboQuant server's OpenAI-compatible API.

    Returns the raw API response dict.
    Falls back with clear error if server is unavailable.
    """
    cfg = config or load_config()

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload: dict[str, Any] = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    if response_format:
        payload["response_format"] = response_format

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        cfg.completion_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        return raw
    except (urllib.error.URLError, TimeoutError, socket.timeout, ConnectionError) as exc:
        return {
            "error": f"TurboQuant server unreachable: {type(exc).__name__}: {exc}",
            "choices": [],
        }
    except Exception as exc:
        return {
            "error": f"TurboQuant API error: {exc}",
            "choices": [],
        }


def turbo_extract_text(response: dict[str, Any]) -> str:
    """Extract the text content from a TurboQuant generate response."""
    if "error" in response:
        return ""
    choices = response.get("choices", [])
    if not choices:
        return ""
    message = choices[0].get("message", {})
    return message.get("content", "")


# ---------------------------------------------------------------------------
# Convenience: check if turbo is available for routing
# ---------------------------------------------------------------------------

_turbo_available_cache: bool | None = None
_turbo_cache_time: float = 0.0
_TURBO_CACHE_TTL = 30.0  # check every 30s


def is_turbo_available(force_check: bool = False) -> bool:
    """
    Fast cached check: is the TurboQuant server available?
    Used by ollama_client.py to decide routing.
    """
    global _turbo_available_cache, _turbo_cache_time

    now = time.monotonic()
    if not force_check and _turbo_available_cache is not None:
        if now - _turbo_cache_time < _TURBO_CACHE_TTL:
            return _turbo_available_cache

    cfg = load_config()
    if not cfg.is_configured:
        _turbo_available_cache = False
        _turbo_cache_time = now
        return False

    status = check_health(cfg, timeout=2.0)
    _turbo_available_cache = status.healthy
    _turbo_cache_time = now
    return status.healthy
