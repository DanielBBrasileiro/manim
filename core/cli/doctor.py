#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.intelligence.model_capabilities import refresh_model_capabilities
from core.intelligence.model_profiles import get_active_profile
from core.runtime.capability_pool import build_capability_pool
from core.runtime.capability_registry import build_capability_registry

BUNDLE_MANIFEST = ROOT / "engines" / "remotion" / ".bundle-cache" / "bundle-manifest.json"


def _run_command(cmd: list[str], cwd: Path | None = None, timeout: float = 15.0) -> dict[str, Any]:
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {"ok": True, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except Exception as exc:
        return {"ok": False, "stdout": "", "stderr": str(exc)}


def _bundle_status() -> dict[str, Any]:
    """Read the persistent bundle manifest and return warm status."""
    if not BUNDLE_MANIFEST.exists():
        return {"warm": False, "reason": "no_manifest"}

    try:
        manifest = json.loads(BUNDLE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"warm": False, "reason": "manifest_unreadable"}

    bundle_path = manifest.get("bundlePath", "")
    bundle_js = Path(bundle_path) / "bundle.js" if bundle_path else None
    if not bundle_js or not bundle_js.exists():
        return {"warm": False, "reason": "bundle_missing", "path": bundle_path}

    manifest_mtime = float(manifest.get("sourceMtime", 0))
    created_at = float(manifest.get("createdAt", 0))
    age_hours = (time.time() * 1000 - created_at) / 3_600_000 if created_at else None

    return {
        "warm": True,
        "path": bundle_path,
        "age_hours": round(age_hours, 1) if age_hours is not None else None,
        "source_mtime": manifest_mtime,
    }


def _trigger_background_warm() -> None:
    """Spawn a background bundle warm — returns immediately."""
    runner = ROOT / "scripts" / "run_remotion_node.sh"
    direct = ROOT / "scripts" / "remotion_direct.js"
    if not runner.exists() or not direct.exists():
        return
    try:
        subprocess.Popen(
            ["/bin/bash", str(runner), str(direct), "warm"],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print("🔥 [Doctor] Bundle warm iniciado em background.")
    except Exception:
        pass


def collect_doctor_report() -> dict[str, Any]:
    profile = get_active_profile()
    registry = build_capability_registry()
    remotion = _run_command(["/bin/bash", str(ROOT / "scripts" / "run_remotion_node.sh"), "-v"], cwd=ROOT)
    manim = _run_command(["python3", "-m", "manim", "--version"], cwd=ROOT)
    playwright = _run_command(["python3", "-m", "playwright", "--version"], cwd=ROOT)
    npm = _run_command(
        [
            "/bin/bash",
            str(ROOT / "scripts" / "run_remotion_node.sh"),
            "-e",
            "console.log(require('./engines/remotion/node_modules/remotion/package.json').version)",
        ],
        cwd=ROOT,
    )
    models = refresh_model_capabilities()
    bundle = _bundle_status()

    # TurboQuant server health
    turbo_report: dict[str, Any] = {"installed": False}
    try:
        from core.intelligence.ollama_client import check_turbo_health
        turbo_report = check_turbo_health()
    except Exception:
        pass

    return {
        "profile": {
            "name": profile.name,
            "provider": profile.provider,
            "description": profile.description,
            "render_preferences": profile.render_preferences,
        },
        "system": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "machine": platform.machine(),
        },
        "checks": {
            "remotion_node": remotion,
            "manim": manim,
            "playwright": playwright,
            "remotion_cli": npm,
        },
        "bundle": bundle,
        "turbo": turbo_report,
        "models": [model.id for model in models],
        "registry": {
            "targets": len(registry.targets),
            "style_packs": len(registry.style_packs),
            "quality_gates": len(registry.quality_gates),
            "profiles": len(registry.profiles),
        },
        "capability_pool": build_capability_pool(),
    }


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnostico do runtime local AIOX")
    parser.add_argument("--json", action="store_true", help="Saida em JSON")
    parser.add_argument(
        "--warm",
        action="store_true",
        help="Dispara warm do bundle Remotion em background se necessario",
    )
    args = parser.parse_args(argv)

    report = collect_doctor_report()

    # Auto-warm: se Remotion OK mas bundle frio, aquece em background
    remotion_ok = report["checks"].get("remotion_cli", {}).get("ok", False)
    bundle_warm = report["bundle"].get("warm", False)
    if (args.warm or not bundle_warm) and remotion_ok:
        _trigger_background_warm()

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0

    print(f"Profile: {report['profile']['name']} ({report['profile']['provider']})")
    print(f"Python: {report['system']['python']} | Machine: {report['system']['machine']}")
    for name, result in report["checks"].items():
        status = "ok" if result["ok"] else "fail"
        detail = result["stdout"] or result["stderr"]
        print(f"- {name}: {status} {detail}".strip())
    bundle = report["bundle"]
    bundle_status = "warm" if bundle["warm"] else f"cold ({bundle.get('reason', '?')})"
    if bundle["warm"]:
        age = bundle.get("age_hours")
        bundle_status += f" ({age}h ago)" if age is not None else ""
    print(f"- bundle: {bundle_status}")
    turbo = report.get("turbo", {})
    if turbo.get("installed"):
        t_status = "healthy" if turbo.get("healthy") else ("running" if turbo.get("running") else "stopped")
        t_cache = f"K={turbo.get('cache_type_k', '?')} V={turbo.get('cache_type_v', '?')}"
        t_ctx = turbo.get("context_length", 0)
        print(f"- turbo: {t_status} ({t_cache}, ctx={t_ctx})")
    else:
        print(f"- turbo: not installed (run: bash scripts/setup_turboquant.sh)")
    print(f"Models: {', '.join(report['models']) if report['models'] else 'none'}")
    print(
        "Registry: "
        f"{report['registry']['targets']} targets, "
        f"{report['registry']['style_packs']} style packs, "
        f"{report['registry']['quality_gates']} quality gates"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
