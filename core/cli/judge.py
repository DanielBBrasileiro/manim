#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.compiler.render_manifest import build_artifact_plan
from core.quality.quality_runtime import run_quality_pipeline


def _load_brief(path: str | None) -> dict:
    if not path:
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Julga um still/video exportado pelo motor de qualidade")
    parser.add_argument("path", help="Caminho do artefato (png/mp4/gif/webm)")
    parser.add_argument("--target", default="linkedin_feed_4_5")
    parser.add_argument("--briefing")
    parser.add_argument("--archetype", default="emergence")
    parser.add_argument("--fallback", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    brief = _load_brief(args.briefing)
    artifact_plan = build_artifact_plan({"archetype": args.archetype, "duration": 12}, brief or {"output_targets": [args.target]})
    artifact_plan["targets"] = [target for target in artifact_plan.get("targets", []) if str(target.get("id", "")).strip() == args.target]

    suffix = Path(args.path).suffix.lower()
    mode = "still" if suffix == ".png" else "video"
    if args.target == "linkedin_carousel_square":
        mode = "carousel"
    report = run_quality_pipeline(
        [{"target": args.target, "mode": mode, "output": args.path, "fallback": args.fallback}],
        artifact_plan,
        context={"archetype": args.archetype},
    )

    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
        return 0

    print(report.get("final_quality_summary"))
    for target_id, target_report in (report.get("target_reports") or {}).items():
        print(f"- {target_id}: {target_report.get('status')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
