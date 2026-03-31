#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.intelligence.model_capabilities import refresh_model_capabilities
from core.intelligence.model_profiles import get_active_profile
from core.runtime.capability_pool import build_capability_pool
from core.runtime.capability_registry import build_capability_registry


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
    args = parser.parse_args(argv)

    report = collect_doctor_report()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0

    print(f"Profile: {report['profile']['name']} ({report['profile']['provider']})")
    print(f"Python: {report['system']['python']} | Machine: {report['system']['machine']}")
    for name, result in report["checks"].items():
        status = "ok" if result["ok"] else "fail"
        detail = result["stdout"] or result["stderr"]
        print(f"- {name}: {status} {detail}".strip())
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
