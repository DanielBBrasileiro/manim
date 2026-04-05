"""
coordinator.py — Multi-agent creative coordinator.

The central orchestrator that spawns specialized workers, manages task
execution order, handles parallel groups, resolves vetoes, and synthesizes
the final creative output.

Inspired by claude-code coordinatorMode.ts:
- Coordinator decomposes intent into subtasks
- Workers execute in dependency-resolved parallel groups
- Scratchpad enables inter-worker communication
- Vetoes from QA halt the pipeline with clear feedback
- Final synthesis produces a structured SessionReport

This replaces the linear AgenticOrchestrator.run_pipeline() with an
autonomous, parallel-aware, veto-capable creative pipeline.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from core.coordinator.scratchpad import Scratchpad
from core.coordinator.task_manager import (
    CreativeTask,
    TaskManager,
    TaskPhase,
    TaskState,
)
from core.coordinator.workers import (
    BaseWorker,
    WorkerResult,
    get_worker,
    list_workers,
)


@dataclass
class CoordinatorReport:
    """Complete report from a coordinated creative session."""
    session_id: str
    intent: str
    workers_used: list[str]
    tasks_total: int
    tasks_completed: int
    tasks_failed: int
    has_veto: bool
    veto_reasons: list[str]
    creative_plan: dict[str, Any]
    artifacts: list[str]
    scratchpad_summary: dict[str, Any]
    worker_results: list[dict[str, Any]]
    total_duration_ms: float

    def as_markdown(self) -> str:
        lines = [
            "# 🎬 AIOX Creative Coordinator Report",
            "",
            f"**Session:** `{self.session_id}`",
            f"**Intent:** {self.intent}",
            f"**Duration:** {self.total_duration_ms:.0f}ms",
            "",
            "## Workers",
            "",
        ]

        for result in self.worker_results:
            icon = "✓" if result.get("success") else "✗"
            lines.append(
                f"- {icon} **{result['worker']}** → {result['task_name']} "
                f"({result.get('duration_ms', 0):.0f}ms)"
            )
            if result.get("error"):
                lines.append(f"  ⚠ {result['error']}")

        if self.has_veto:
            lines.extend([
                "",
                "## ⛔ Vetoes",
                "",
            ])
            for reason in self.veto_reasons:
                lines.append(f"- {reason}")

        if self.creative_plan:
            lines.extend([
                "",
                "## Creative Plan",
                "",
                f"- **Archetype:** {self.creative_plan.get('archetype', '?')}",
                f"- **Aesthetic:** {self.creative_plan.get('aesthetic_family', '?')}",
                f"- **Pacing:** {self.creative_plan.get('pacing', '?')}",
            ])
            entropy = self.creative_plan.get("entropy", {})
            if entropy:
                lines.append(
                    f"- **Entropy:** PHY={entropy.get('physical', '?')} "
                    f"STR={entropy.get('structural', '?')} "
                    f"AES={entropy.get('aesthetic', '?')}"
                )

        if self.artifacts:
            lines.extend(["", "## Artifacts", ""])
            for path in self.artifacts:
                lines.append(f"- `{path}`")

        lines.extend([
            "",
            "## Scratchpad",
            "",
            f"- Entries: {self.scratchpad_summary.get('total_entries', 0)}",
            f"- Workers: {', '.join(self.scratchpad_summary.get('workers', []))}",
            f"- Phases: {', '.join(self.scratchpad_summary.get('phases', []))}",
        ])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "intent": self.intent,
            "workers_used": self.workers_used,
            "tasks": {"total": self.tasks_total, "completed": self.tasks_completed, "failed": self.tasks_failed},
            "has_veto": self.has_veto,
            "veto_reasons": self.veto_reasons,
            "creative_plan": self.creative_plan,
            "artifacts": self.artifacts,
            "scratchpad": self.scratchpad_summary,
            "worker_results": self.worker_results,
            "duration_ms": round(self.total_duration_ms, 2),
        }


class CreativeCoordinator:
    """
    Multi-agent creative coordinator.

    Usage:
        coordinator = CreativeCoordinator()
        report = await coordinator.run("quero um vídeo com tensão e silêncio")

    Lifecycle:
    1. Decompose intent into subtasks (TaskManager)
    2. Resolve parallel groups
    3. Execute each group (workers run in parallel within a group)
    4. Write results to Scratchpad
    5. Check for vetoes at each phase boundary
    6. Synthesize final output
    """

    def __init__(
        self,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        from uuid import uuid4
        self.session_id = session_id or uuid4().hex[:12]
        self.context = context or {}
        self.scratchpad = Scratchpad()
        self.task_manager = TaskManager()
        self._worker_results: list[WorkerResult] = []

    async def run(self, intent: str) -> CoordinatorReport:
        """Execute the full coordinated creative pipeline."""
        start = time.monotonic()

        # 1. Decompose
        tasks = self.task_manager.decompose_intent(intent, self.context)

        # 2. Execute phase by phase
        await self._execute_pipeline(tasks)

        # 3. Build report
        elapsed = (time.monotonic() - start) * 1000

        # Collect creative plan from scratchpad
        creative_plan = self._synthesize_plan()

        # Collect artifacts
        artifacts = [
            e.content for e in self.scratchpad.read_artifacts()
            if isinstance(e.content, str)
        ]

        # Collect vetoes
        veto_reasons = [
            str(e.content) for e in self.scratchpad.read_vetoes()
        ]

        progress = self.task_manager.progress()

        return CoordinatorReport(
            session_id=self.session_id,
            intent=intent,
            workers_used=list({r.worker for r in self._worker_results}),
            tasks_total=progress["total"],
            tasks_completed=progress["done"],
            tasks_failed=progress["failed"],
            has_veto=self.scratchpad.has_veto(),
            veto_reasons=veto_reasons,
            creative_plan=creative_plan,
            artifacts=artifacts,
            scratchpad_summary=self.scratchpad.summary(),
            worker_results=[
                {
                    "worker": r.worker,
                    "task_name": r.task_name,
                    "success": r.success,
                    "error": r.error,
                    "duration_ms": r.duration_ms,
                }
                for r in self._worker_results
            ],
            total_duration_ms=elapsed,
        )

    async def _execute_pipeline(self, tasks: list[CreativeTask]) -> None:
        """Execute tasks in dependency-resolved order."""

        # Process phase by phase in order
        phase_order = [
            TaskPhase.INTERPRET,
            TaskPhase.PLAN,
            TaskPhase.REVIEW,
            TaskPhase.BUILD,
            TaskPhase.REVIEW,
            TaskPhase.SYNTHESIZE,
        ]

        # Group tasks by execution wave
        executed: set[str] = set()
        max_iterations = len(tasks) + 2  # safety

        for _ in range(max_iterations):
            ready = self.task_manager.get_ready_tasks()
            ready = [t for t in ready if t.id not in executed]
            if not ready:
                break

            # Check for veto before BUILD phase
            if any(t.phase == TaskPhase.BUILD for t in ready) and self.scratchpad.has_veto():
                for t in ready:
                    if t.phase == TaskPhase.BUILD:
                        t.veto("Build blocked by QA veto")
                        executed.add(t.id)
                # Skip remaining pipeline
                for task in tasks:
                    if task.id not in executed and task.state == TaskState.PENDING:
                        task.veto("Pipeline halted by upstream QA veto")
                        executed.add(task.id)
                break

            # Execute ready tasks in parallel
            results = await self._execute_group(ready)

            for task, result in zip(ready, results):
                if result.success:
                    task.complete(result.output)
                else:
                    task.fail(result.error or "Unknown error")
                executed.add(task.id)

    async def _execute_group(self, tasks: list[CreativeTask]) -> list[WorkerResult]:
        """Execute a group of tasks in parallel."""
        coros = []
        for task in tasks:
            worker = get_worker(task.worker)
            if worker is None:
                # Coordinator tasks are handled internally
                if task.worker == "coordinator":
                    coros.append(self._synthesize_task(task))
                else:
                    coros.append(self._fallback_result(task))
            else:
                task.start()
                coros.append(
                    self._execute_worker(worker, task)
                )

        results = await asyncio.gather(*coros, return_exceptions=True)

        processed: list[WorkerResult] = []
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                wr = WorkerResult(
                    worker=task.worker,
                    task_name=task.name,
                    success=False,
                    error=str(result),
                )
            else:
                wr = result
            processed.append(wr)
            self._worker_results.append(wr)

        return processed

    async def _execute_worker(
        self, worker: BaseWorker, task: CreativeTask
    ) -> WorkerResult:
        """Execute a single worker with timing."""
        start = time.monotonic()
        result = await worker.run(task, self.scratchpad, self.context)
        result.duration_ms = (time.monotonic() - start) * 1000
        return result

    async def _synthesize_task(self, task: CreativeTask) -> WorkerResult:
        """Handle the final synthesis task."""
        task.start()
        plan = self._synthesize_plan()
        self.scratchpad.write(
            worker="coordinator",
            phase="synthesize",
            content=plan,
            entry_type="decision",
        )
        return WorkerResult(
            worker="coordinator",
            task_name=task.name,
            success=True,
            output=plan,
        )

    async def _fallback_result(self, task: CreativeTask) -> WorkerResult:
        """Fallback for unknown workers."""
        return WorkerResult(
            worker=task.worker,
            task_name=task.name,
            success=False,
            error=f"No worker registered for: {task.worker}",
        )

    def _synthesize_plan(self) -> dict[str, Any]:
        """Assemble the final creative plan from all scratchpad decisions."""
        plan: dict[str, Any] = {}

        for entry in self.scratchpad.read_decisions():
            if not isinstance(entry.content, dict):
                continue

            if entry.worker == "aria":
                plan["archetype"] = entry.content.get("archetype")
                plan["aesthetic_family"] = entry.content.get("aesthetic_family")

            elif entry.worker == "zara":
                plan["entropy"] = entry.content.get("entropy", {})
                plan["interpretation"] = {
                    "motion_signature": entry.content.get("motion_bias", ""),
                    "regime": "laminar",
                }

            elif entry.worker == "kael":
                plan["pacing"] = entry.content.get("pacing")

            elif entry.worker == "uma":
                plan["diversity_pass"] = entry.content.get("diversity_pass")
                plan["quality_pass"] = entry.content.get("quality_pass")

            elif entry.worker == "dara":
                plan["render_result"] = entry.content

        return plan
