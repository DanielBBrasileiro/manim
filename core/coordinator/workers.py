"""
workers.py — Specialized creative workers.

Each worker wraps an existing agent persona with async execution,
scratchpad integration, and tool access via the harness.

Workers:
- AriaWorker: Creative Director (archetype + aesthetic decisions)
- ZaraWorker: Physics Engineer (entropy + motion signature)
- KaelWorker: Temporal Master (pacing + rhythm)
- UmaWorker: Quality Controller (diversity + quality gate)
- DaraWorker: Production Engineer (render pipeline execution)

Inspired by claude-code coordinatorMode.ts worker pattern:
- Each worker has a run() method that reads inputs and writes to scratchpad
- Workers are stateless — context comes from task input + scratchpad
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from core.coordinator.scratchpad import Scratchpad
from core.coordinator.task_manager import CreativeTask, TaskPhase


@dataclass
class WorkerResult:
    """Result from a worker execution."""
    worker: str
    task_name: str
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    duration_ms: float = 0.0


class BaseWorker:
    """Base class for all creative workers."""
    name: str = "base"
    persona: str = "Generic Worker"

    async def run(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any] | None = None,
    ) -> WorkerResult:
        """Execute the worker's task and write results to scratchpad."""
        try:
            output = await self._execute(task, scratchpad, context or {})
            scratchpad.write(
                worker=self.name,
                phase=task.phase.value,
                content=output,
                entry_type="decision",
                confidence=output.get("confidence", 1.0) if isinstance(output, dict) else 1.0,
            )
            return WorkerResult(
                worker=self.name,
                task_name=task.name,
                success=True,
                output=output if isinstance(output, dict) else {"result": output},
            )
        except Exception as exc:
            error_msg = f"{type(exc).__name__}: {exc}"
            scratchpad.write(
                worker=self.name,
                phase=task.phase.value,
                content=error_msg,
                entry_type="error",
            )
            return WorkerResult(
                worker=self.name,
                task_name=task.name,
                success=False,
                error=error_msg,
            )

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        raise NotImplementedError


class AriaWorker(BaseWorker):
    """Creative Director — archetype and aesthetic decisions."""
    name = "aria"
    persona = "Aria: Creative Director"

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from core.agents.aria import decide_archetype, select_aesthetic_family

        intent = task.input_data.get("intent", "")
        identity = task.input_data.get("identity", "aiox_default")

        archetype = await asyncio.to_thread(decide_archetype, intent)
        aesthetic = await asyncio.to_thread(select_aesthetic_family, identity, intent)

        return {
            "archetype": archetype,
            "aesthetic_family": aesthetic,
            "intent": intent,
            "identity": identity,
        }


class ZaraWorker(BaseWorker):
    """Physics Engineer — entropy profiles and motion signatures."""
    name = "zara"
    persona = "Zara: Physics & Entropy Engineer"

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from core.agents.zara import define_entropy, resolve_motion_bias

        # Read Aria's decision from scratchpad
        aria_decision = scratchpad.latest_decision("interpret")
        archetype = (
            aria_decision.content.get("archetype", "emergence")
            if aria_decision and isinstance(aria_decision.content, dict)
            else "emergence"
        )

        entropy = await asyncio.to_thread(define_entropy, archetype)
        motion_bias = await asyncio.to_thread(resolve_motion_bias, archetype)

        return {
            "archetype": archetype,
            "entropy": entropy,
            "motion_bias": motion_bias,
        }


class KaelWorker(BaseWorker):
    """Temporal Master — pacing and rhythm."""
    name = "kael"
    persona = "Kael: Temporal Rhythm Master"

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from core.agents.kael import define_pacing

        aria_decision = scratchpad.latest_decision("interpret")
        archetype = (
            aria_decision.content.get("archetype", "emergence")
            if aria_decision and isinstance(aria_decision.content, dict)
            else "emergence"
        )
        intent = (
            aria_decision.content.get("intent", "")
            if aria_decision and isinstance(aria_decision.content, dict)
            else ""
        )

        pacing = await asyncio.to_thread(define_pacing, intent, archetype)

        return {
            "archetype": archetype,
            "pacing": pacing,
        }


class UmaWorker(BaseWorker):
    """Quality Controller — diversity checks and quality gates."""
    name = "uma"
    persona = "Uma: Quality & Memory Controller"

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from core.agents.uma import evaluate

        if task.name == "check_diversity":
            return await self._check_diversity(task, scratchpad, context)
        elif task.name == "quality_review":
            return await self._quality_review(task, scratchpad, context)
        return {"status": "no_action"}

    async def _check_diversity(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        from core.agents.uma import evaluate

        # Collect decisions from scratchpad
        zara_decision = scratchpad.latest_decision("plan")
        aria_decision = scratchpad.latest_decision("interpret")

        archetype = "emergence"
        if aria_decision and isinstance(aria_decision.content, dict):
            archetype = aria_decision.content.get("archetype", "emergence")

        signature = {"structure": archetype}
        if zara_decision and isinstance(zara_decision.content, dict):
            signature["entropy"] = zara_decision.content.get("entropy", {})

        is_diverse = await asyncio.to_thread(evaluate, signature)

        if not is_diverse:
            scratchpad.write(
                worker=self.name,
                phase=task.phase.value,
                content=f"Repetition detected for archetype '{archetype}'",
                entry_type="veto",
                confidence=0.85,
            )

        return {
            "diversity_pass": is_diverse,
            "archetype_checked": archetype,
        }

    async def _quality_review(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        artifacts = scratchpad.read_artifacts()
        render_decision = scratchpad.latest_decision("build")

        render_ok = False
        if render_decision and isinstance(render_decision.content, dict):
            render_ok = render_decision.content.get("ok", False)

        image_extensions = (".png", ".jpg", ".jpeg", ".webp")
        frame_paths = [
            str(a.content) for a in artifacts
            if isinstance(a.content, str) and any(
                str(a.content).lower().endswith(ext) for ext in image_extensions
            )
        ]

        # -- Fast brand pre-check (no LLM, milliseconds) --
        brand_veto = False
        all_brand_violations: list[str] = []
        if frame_paths:
            try:
                from core.quality.brand_validator import validate_frame
                for fpath in frame_paths[:3]:
                    brand_result = await asyncio.to_thread(validate_frame, fpath)
                    if brand_result.violations:
                        all_brand_violations.extend(brand_result.violations)
                    if not brand_result.passed and brand_result.color_purity_score < 50:
                        brand_veto = True

                if brand_veto:
                    scratchpad.write(
                        worker=self.name,
                        phase=task.phase.value,
                        content=f"Brand pre-check VETO: {'; '.join(all_brand_violations[:3])}",
                        entry_type="veto",
                        confidence=0.95,
                    )
                    return {
                        "render_ok": render_ok,
                        "artifacts_count": len(artifacts),
                        "brand_precheck": False,
                        "brand_violations": all_brand_violations,
                        "vision_qa": False,
                        "quality_pass": False,
                    }
            except Exception as exc:
                scratchpad.write(
                    worker=self.name,
                    phase=task.phase.value,
                    content=f"Brand pre-check unavailable: {exc}",
                    entry_type="observation",
                )

        # -- Vision QA (LLM scoring) --
        scored_frames: list[dict] = []
        if frame_paths:
            try:
                from core.quality.frame_scorer import score_frame, batch_summary

                scores = []
                for fpath in frame_paths[:5]:
                    score = await asyncio.to_thread(
                        score_frame, fpath, threshold=70.0, context=context,
                    )
                    scores.append(score)
                    scored_frames.append(score.to_dict())

                summary = batch_summary(scores)
                quality_pass = summary["passed"] > 0 and summary["avg_score"] >= 70.0

                if not quality_pass and summary["failed"] > 0:
                    worst = min(scores, key=lambda s: s.composite_score)
                    scratchpad.write(
                        worker=self.name,
                        phase=task.phase.value,
                        content=f"Quality gate failed: {worst.summary_line()}",
                        entry_type="veto",
                        confidence=0.9,
                    )

                return {
                    "render_ok": render_ok,
                    "artifacts_count": len(artifacts),
                    "brand_precheck": not brand_veto,
                    "brand_violations": all_brand_violations,
                    "vision_qa": True,
                    "quality_pass": quality_pass,
                    "frame_scores": scored_frames,
                    "batch_summary": summary,
                }
            except Exception as exc:
                scratchpad.write(
                    worker=self.name,
                    phase=task.phase.value,
                    content=f"Vision QA unavailable: {exc}",
                    entry_type="observation",
                )

        return {
            "render_ok": render_ok,
            "artifacts_count": len(artifacts),
            "brand_precheck": not brand_veto,
            "brand_violations": all_brand_violations,
            "vision_qa": False,
            "quality_pass": render_ok,
        }


class DaraWorker(BaseWorker):
    """Production Engineer — render pipeline execution."""
    name = "dara"
    persona = "Dara: Production Engineer"

    async def _execute(
        self,
        task: CreativeTask,
        scratchpad: Scratchpad,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        # Check for vetoes before rendering
        if scratchpad.has_veto():
            vetoes = scratchpad.read_vetoes()
            veto_reasons = [v.content for v in vetoes]
            return {
                "ok": False,
                "skipped": True,
                "reason": f"Vetoed by QA: {'; '.join(str(r) for r in veto_reasons)}",
            }

        # Collect the creative plan from scratchpad
        aria_decision = scratchpad.latest_decision("interpret")
        zara_decision = None
        kael_decision = None

        for entry in scratchpad.read_decisions():
            if entry.worker == "zara":
                zara_decision = entry
            elif entry.worker == "kael":
                kael_decision = entry

        plan = self._assemble_plan(aria_decision, zara_decision, kael_decision)

        # Check if we should actually render (requires briefing)
        briefing_path = context.get("briefing_path") or task.input_data.get("briefing_path")
        if briefing_path:
            from core.agents.dara import build_scene
            result = await asyncio.to_thread(build_scene, plan)
            if isinstance(result, dict):
                # Record artifact paths
                for output in result.get("outputs", []):
                    if isinstance(output, dict) and output.get("output"):
                        scratchpad.write(
                            worker=self.name,
                            phase="build",
                            content=output["output"],
                            entry_type="artifact",
                        )
                return result
            return {"ok": True, "result": str(result)}
        else:
            # Preview-only mode: return the assembled plan
            return {
                "ok": True,
                "mode": "plan_only",
                "plan": plan,
            }

    def _assemble_plan(
        self,
        aria: Any | None,
        zara: Any | None,
        kael: Any | None,
    ) -> dict[str, Any]:
        """Assemble a creative plan from worker decisions."""
        plan: dict[str, Any] = {}

        if aria and isinstance(aria.content, dict):
            plan["archetype"] = aria.content.get("archetype", "emergence")
            plan["aesthetic_family"] = aria.content.get("aesthetic_family", "silent_architecture")

        entropy = {}
        interpretation = {}
        if zara and isinstance(zara.content, dict):
            entropy = zara.content.get("entropy", {})
            interpretation["motion_signature"] = zara.content.get("motion_bias", "")
            interpretation["regime"] = "laminar"

        plan["entropy"] = entropy
        plan["interpretation"] = interpretation

        if kael and isinstance(kael.content, dict):
            plan["pacing"] = kael.content.get("pacing", "cinematic")

        return plan


# ---------------------------------------------------------------------------
# Worker registry
# ---------------------------------------------------------------------------

WORKERS: dict[str, BaseWorker] = {
    "aria": AriaWorker(),
    "zara": ZaraWorker(),
    "kael": KaelWorker(),
    "uma": UmaWorker(),
    "dara": DaraWorker(),
}


def get_worker(name: str) -> BaseWorker | None:
    """Get a worker by name."""
    return WORKERS.get(name)


def list_workers() -> list[str]:
    """List all available worker names."""
    return list(WORKERS.keys())
