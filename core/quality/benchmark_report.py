from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


def _safe_mean(values: list[float]) -> float | None:
    cleaned = [float(value) for value in values if value is not None]
    if not cleaned:
        return None
    return round(mean(cleaned), 2)


def _effective_score(case: dict[str, Any]) -> float | None:
    final_score = case.get("final_score")
    if final_score is not None:
        return float(final_score)
    preview_score = case.get("preview_score")
    if preview_score is not None:
        return float(preview_score)
    return None


def _premium_flag(case: dict[str, Any]) -> bool:
    return bool(case.get("final_premium") or case.get("quality_band") == "premium")


def _weak_dimensions(case: dict[str, Any], *, threshold: float = 70.0) -> list[str]:
    dims = case.get("dimension_scores", {}) if isinstance(case.get("dimension_scores", {}), dict) else {}
    return [
        name
        for name, score in dims.items()
        if isinstance(score, (int, float)) and float(score) < threshold
    ]


def aggregate_benchmark_run(run_report: dict[str, Any]) -> dict[str, Any]:
    cases = [case for case in run_report.get("cases", []) if isinstance(case, dict)]
    dimension_buckets: dict[str, list[float]] = defaultdict(list)
    dimension_failures: Counter[str] = Counter()
    weak_dimensions: Counter[str] = Counter()

    def _bucket(by: str) -> dict[str, dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for case in cases:
            key = str(case.get(by) or "unknown").strip() or "unknown"
            grouped[key].append(case)

        summary: dict[str, dict[str, Any]] = {}
        for key, entries in grouped.items():
            scores = [_effective_score(entry) for entry in entries]
            preview_scores = [entry.get("preview_score") for entry in entries if entry.get("preview_score") is not None]
            summary[key] = {
                "count": len(entries),
                "avg_score": _safe_mean([score for score in scores if score is not None]),
                "avg_preview_score": _safe_mean([float(score) for score in preview_scores]),
                "avg_premium_score": _safe_mean(
                    [float(_effective_score(entry)) for entry in entries if _premium_flag(entry) and _effective_score(entry) is not None]
                ),
                "premium_rate": round(sum(1 for entry in entries if _premium_flag(entry)) / max(len(entries), 1), 3),
                "hard_veto_frequency": round(sum(1 for entry in entries if entry.get("hard_veto")) / max(len(entries), 1), 3),
                "avg_preview_delta": _safe_mean(
                    [float(entry.get("preview_improvement_delta", 0.0) or 0.0) for entry in entries]
                ),
                "common_weak_dimensions": [
                    item[0]
                    for item in Counter(
                        dimension
                        for entry in entries
                        for dimension in _weak_dimensions(entry)
                    ).most_common(3)
                ],
            }
        return summary

    for case in cases:
        dims = case.get("dimension_scores", {}) if isinstance(case.get("dimension_scores", {}), dict) else {}
        for name, score in dims.items():
            if not isinstance(score, (int, float)):
                continue
            value = float(score)
            dimension_buckets[name].append(value)
            if value < 70.0:
                dimension_failures[name] += 1
        weak_dimensions.update(_weak_dimensions(case))

    dimension_summary = {
        name: {
            "avg_score": _safe_mean(values),
            "fail_count": int(dimension_failures.get(name, 0)),
            "sample_count": len(values),
        }
        for name, values in dimension_buckets.items()
    }

    preview_deltas = [float(case.get("preview_improvement_delta", 0.0) or 0.0) for case in cases]
    effective_scores = [_effective_score(case) for case in cases if _effective_score(case) is not None]
    return {
        "case_count": len(cases),
        "avg_effective_score": _safe_mean([score for score in effective_scores if score is not None]),
        "avg_preview_improvement_delta": _safe_mean(preview_deltas),
        "hard_veto_frequency": round(sum(1 for case in cases if case.get("hard_veto")) / max(len(cases), 1), 3) if cases else 0.0,
        "preview_accept_rate": round(sum(1 for case in cases if case.get("preview_accepted")) / max(len(cases), 1), 3) if cases else 0.0,
        "by_target": _bucket("target"),
        "by_artifact_class": _bucket("artifact_class"),
        "by_style_pack": _bucket("style_pack"),
        "by_judge_profile": _bucket("judge_profile"),
        "by_dimension": dimension_summary,
        "most_common_weak_dimensions": [item[0] for item in weak_dimensions.most_common(5)],
    }


def compare_benchmark_runs(baseline_run: dict[str, Any], candidate_run: dict[str, Any]) -> dict[str, Any]:
    baseline_cases = {
        str(case.get("case_id", "")).strip(): case
        for case in baseline_run.get("cases", [])
        if isinstance(case, dict) and str(case.get("case_id", "")).strip()
    }
    candidate_cases = {
        str(case.get("case_id", "")).strip(): case
        for case in candidate_run.get("cases", [])
        if isinstance(case, dict) and str(case.get("case_id", "")).strip()
    }
    overlapping_ids = sorted(set(baseline_cases) & set(candidate_cases))
    case_deltas = []
    regressions = []

    for case_id in overlapping_ids:
        baseline = baseline_cases[case_id]
        candidate = candidate_cases[case_id]
        baseline_score = _effective_score(baseline)
        candidate_score = _effective_score(candidate)
        delta = None
        if baseline_score is not None and candidate_score is not None:
            delta = round(candidate_score - baseline_score, 2)
        status = "no_change"
        if delta is not None:
            if delta >= 2.0:
                status = "improved"
            elif delta <= -2.0:
                status = "declined"
        if baseline.get("hard_veto") is False and candidate.get("hard_veto") is True:
            regressions.append(case_id)
        if baseline.get("final_passed") is True and candidate.get("final_passed") is False:
            regressions.append(case_id)
        case_deltas.append(
            {
                "case_id": case_id,
                "target": candidate.get("target"),
                "style_pack": candidate.get("style_pack"),
                "baseline_score": baseline_score,
                "candidate_score": candidate_score,
                "delta": delta,
                "status": status,
            }
        )

    baseline_aggregate = baseline_run.get("aggregate") or aggregate_benchmark_run(baseline_run)
    candidate_aggregate = candidate_run.get("aggregate") or aggregate_benchmark_run(candidate_run)

    def _compare_group(group_name: str) -> dict[str, dict[str, Any]]:
        baseline_group = baseline_aggregate.get(group_name, {}) if isinstance(baseline_aggregate.get(group_name, {}), dict) else {}
        candidate_group = candidate_aggregate.get(group_name, {}) if isinstance(candidate_aggregate.get(group_name, {}), dict) else {}
        keys = sorted(set(baseline_group) | set(candidate_group))
        return {
            key: {
                "baseline": baseline_group.get(key, {}).get("avg_score"),
                "candidate": candidate_group.get(key, {}).get("avg_score"),
                "delta": round(
                    float(candidate_group.get(key, {}).get("avg_score") or 0.0)
                    - float(baseline_group.get(key, {}).get("avg_score") or 0.0),
                    2,
                ) if baseline_group.get(key, {}).get("avg_score") is not None or candidate_group.get(key, {}).get("avg_score") is not None else None,
            }
            for key in keys
        }

    dimension_delta: dict[str, dict[str, Any]] = {}
    baseline_dims = baseline_aggregate.get("by_dimension", {}) if isinstance(baseline_aggregate.get("by_dimension", {}), dict) else {}
    candidate_dims = candidate_aggregate.get("by_dimension", {}) if isinstance(candidate_aggregate.get("by_dimension", {}), dict) else {}
    for name in sorted(set(baseline_dims) | set(candidate_dims)):
        baseline_score = baseline_dims.get(name, {}).get("avg_score")
        candidate_score = candidate_dims.get(name, {}).get("avg_score")
        delta = None
        if baseline_score is not None or candidate_score is not None:
            delta = round(float(candidate_score or 0.0) - float(baseline_score or 0.0), 2)
        dimension_delta[name] = {
            "baseline": baseline_score,
            "candidate": candidate_score,
            "delta": delta,
        }

    return {
        "baseline_run_id": baseline_run.get("run_id"),
        "candidate_run_id": candidate_run.get("run_id"),
        "case_deltas": case_deltas,
        "score_delta_by_target": _compare_group("by_target"),
        "score_delta_by_style_pack": _compare_group("by_style_pack"),
        "score_delta_by_dimension": dimension_delta,
        "regressions": sorted(set(regressions)),
        "summary": {
            "improved_cases": sum(1 for entry in case_deltas if entry.get("status") == "improved"),
            "declined_cases": sum(1 for entry in case_deltas if entry.get("status") == "declined"),
            "unchanged_cases": sum(1 for entry in case_deltas if entry.get("status") == "no_change"),
        },
    }


def render_benchmark_markdown(run_report: dict[str, Any], comparison: dict[str, Any] | None = None) -> str:
    aggregate = run_report.get("aggregate") or aggregate_benchmark_run(run_report)
    by_target = aggregate.get("by_target", {}) if isinstance(aggregate.get("by_target", {}), dict) else {}
    by_style_pack = aggregate.get("by_style_pack", {}) if isinstance(aggregate.get("by_style_pack", {}), dict) else {}

    def _best_and_worst(group: dict[str, Any]) -> tuple[str, str]:
        ranked = [
            (key, float(value.get("avg_score") or 0.0))
            for key, value in group.items()
            if isinstance(value, dict) and value.get("avg_score") is not None
        ]
        if not ranked:
            return ("n/a", "n/a")
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked[0][0], ranked[-1][0]

    strongest_target, weakest_target = _best_and_worst(by_target)
    strongest_style_pack, weakest_style_pack = _best_and_worst(by_style_pack)
    lines = [
        f"# Benchmark Report: {run_report.get('run_id', 'pending')}",
        "",
        f"- Cases: {aggregate.get('case_count', 0)}",
        f"- Avg effective score: {aggregate.get('avg_effective_score')}",
        f"- Avg preview delta: {aggregate.get('avg_preview_improvement_delta')}",
        f"- Hard veto frequency: {aggregate.get('hard_veto_frequency')}",
        f"- Preview accept rate: {aggregate.get('preview_accept_rate')}",
        f"- Strongest target: {strongest_target}",
        f"- Weakest target: {weakest_target}",
        f"- Strongest style pack: {strongest_style_pack}",
        f"- Weakest style pack: {weakest_style_pack}",
        f"- Common weak dimensions: {', '.join(aggregate.get('most_common_weak_dimensions', [])) or 'n/a'}",
    ]
    if comparison:
        lines.extend(
            [
                "",
                "## Comparison",
                f"- Improved cases: {comparison.get('summary', {}).get('improved_cases', 0)}",
                f"- Declined cases: {comparison.get('summary', {}).get('declined_cases', 0)}",
                f"- Regressions: {', '.join(comparison.get('regressions', [])) or 'none'}",
            ]
        )
    return "\n".join(lines).strip() + "\n"
