from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass(frozen=True)
class ArtifactParityAuditResult:
    ok: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]
    stats: dict[str, Any]

    def to_markdown(self) -> str:
        lines = ["# Artifact Parity Audit", ""]
        lines.append(f"Status: **{'PASS' if self.ok else 'FAIL'}**")
        lines.append(f"Targets requested: **{self.stats.get('requested_target_count', 0)}**")
        lines.append(f"Targets exported: **{self.stats.get('exported_target_count', 0)}**")
        lines.append(f"Native outputs: **{self.stats.get('native_outputs', 0)}**")
        lines.append(f"Fallback outputs: **{self.stats.get('fallback_outputs', 0)}**")
        lines.append(f"Premium approved: **{self.stats.get('premium_approved', 0)}**")
        lines.append(f"Brand passed: **{self.stats.get('brand_passed', 0)}**")
        lines.append(f"Vision passed: **{self.stats.get('vision_passed', 0)}**")
        lines.append(f"Judge disagreement: **{self.stats.get('judge_disagreement_rate', 0.0)}**")
        lines.append("")
        lines.append("Errors:")
        lines.extend([f"- {entry}" for entry in self.errors] or ["- none"])
        lines.append("")
        lines.append("Warnings:")
        lines.extend([f"- {entry}" for entry in self.warnings] or ["- none"])
        return "\n".join(lines)


def _latest_decision_record() -> dict[str, Any] | None:
    path = ROOT / "core" / "memory" / "decision_records.jsonl"
    if not path.exists():
        return None
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines:
        return None
    try:
        return json.loads(lines[-1])
    except json.JSONDecodeError:
        return None


def run_artifact_parity_audit(
    artifact_plan: dict[str, Any] | None = None,
    exported_targets: list[dict[str, Any]] | None = None,
    *,
    profile_name: str | None = None,
    benchmark_results: dict[str, Any] | None = None,
    quality_report: dict[str, Any] | None = None,
) -> ArtifactParityAuditResult:
    latest: dict[str, Any] = {}
    if artifact_plan is None and exported_targets is None:
        latest = _latest_decision_record() or {}
        artifact_plan = latest.get("artifact_plan", {})
        exported_targets = latest.get("exported_targets", [])
        quality_report = quality_report or latest.get("quality_report", {})
    if not profile_name and latest:
        profile_name = latest.get("runtime_profile")

    artifact_plan = artifact_plan or {}
    exported_targets = exported_targets or []
    quality_report = quality_report or {}

    requested_targets = {
        str(target.get("id", "")).strip()
        for target in artifact_plan.get("targets", [])
        if isinstance(target, dict) and str(target.get("id", "")).strip()
    }
    exported_target_ids = {
        str(item.get("target", "")).strip()
        for item in exported_targets
        if isinstance(item, dict) and str(item.get("target", "")).strip()
    }

    errors: list[str] = []
    warnings: list[str] = []
    native_outputs = 0
    fallback_outputs = 0
    premium_approved = 0
    brand_passed = 0
    vision_passed = 0

    for target_id in sorted(requested_targets - exported_target_ids):
        errors.append(f"target_missing_output:{target_id}")

    for item in exported_targets:
        if not isinstance(item, dict):
            continue
        output_path = str(item.get("output", "")).strip()
        if not output_path:
            errors.append(f"target_missing_output_path:{item.get('target', 'unknown')}")
            continue
        path = Path(output_path)
        if not path.exists():
            errors.append(f"output_missing_on_disk:{item.get('target', 'unknown')}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"output_empty:{item.get('target', 'unknown')}")

        if bool(item.get("fallback")):
            fallback_outputs += 1
        else:
            native_outputs += 1

    target_reports = quality_report.get("target_reports", {}) if isinstance(quality_report.get("target_reports", {}), dict) else {}
    for target_id, target_report in target_reports.items():
        if not isinstance(target_report, dict):
            continue
        if target_report.get("status") == "premium_pass":
            premium_approved += 1
        if target_report.get("brand_precheck"):
            brand_passed += 1
        if target_report.get("vision_ok"):
            vision_passed += 1

    hero_target = str(
        ((artifact_plan.get("fallback_policy") or {}).get("hero_target"))
        or artifact_plan.get("primary_target_id")
        or "linkedin_feed_4_5"
    ).strip()
    hero_output = next((item for item in exported_targets if isinstance(item, dict) and item.get("target") == hero_target), None)
    if hero_output and hero_output.get("fallback"):
        warnings.append(f"hero_target_used_fallback:{hero_target}")
    hero_quality = target_reports.get(hero_target, {}) if isinstance(target_reports, dict) else {}
    if hero_quality and hero_quality.get("status") != "premium_pass":
        warnings.append(f"hero_target_not_premium:{hero_target}")

    for style_pack_id in artifact_plan.get("style_pack_ids", []):
        pack_path = ROOT / "contracts" / "references" / f"{style_pack_id}.yaml"
        if not pack_path.exists():
            warnings.append(f"style_pack_missing:{style_pack_id}")

    if profile_name and benchmark_results and benchmark_results.get("profile") != profile_name:
        warnings.append(f"profile_benchmark_mismatch:{profile_name}")

    return ArtifactParityAuditResult(
        ok=not errors,
        errors=tuple(errors),
        warnings=tuple(warnings),
        stats={
            "requested_target_count": len(requested_targets),
            "exported_target_count": len(exported_target_ids),
            "native_outputs": native_outputs,
            "fallback_outputs": fallback_outputs,
            "premium_approved": premium_approved,
            "brand_passed": brand_passed,
            "vision_passed": vision_passed,
            "judge_disagreement_rate": float(quality_report.get("judge_disagreement_rate", 0.0) or 0.0),
            "profile": profile_name,
            "quality_pass": bool(quality_report.get("quality_pass")),
            "premium_ok": bool(quality_report.get("premium_ok")),
        },
    )
