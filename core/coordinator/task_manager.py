"""
task_manager.py — Creative task decomposition and tracking.

Decomposes a high-level creative intent into structured subtasks,
tracks their execution state, and reports progress.

Inspired by claude-code coordinatorMode.ts task decomposition:
- Creative tasks have phases: interpret → plan → build → review
- Each subtask maps to a worker and has dependencies
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskState(Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    BLOCKED = "blocked"
    VETOED = "vetoed"


class TaskPhase(Enum):
    """Standard phases of a creative production."""
    INTERPRET = "interpret"   # Understand intent, decide archetype
    PLAN = "plan"             # Structure narrative, timeline, entropy
    BUILD = "build"           # Render, compose, generate artifacts
    REVIEW = "review"         # QA, quality gate, repetition check
    SYNTHESIZE = "synthesize" # Final assembly and output


@dataclass
class CreativeTask:
    """A single subtask in a coordinated creative session."""
    id: str = field(default_factory=lambda: uuid4().hex[:8])
    name: str = ""
    description: str = ""
    phase: TaskPhase = TaskPhase.INTERPRET
    worker: str = ""  # Worker responsible (aria, dara, uma, zara, kael)
    state: TaskState = TaskState.PENDING
    depends_on: list[str] = field(default_factory=list)
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    started_at: float | None = None
    completed_at: float | None = None

    @property
    def duration_ms(self) -> float:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at) * 1000
        return 0.0

    def start(self) -> None:
        self.state = TaskState.RUNNING
        self.started_at = time.time()

    def complete(self, output: dict[str, Any] | None = None) -> None:
        self.state = TaskState.DONE
        self.completed_at = time.time()
        if output:
            self.output_data = output

    def fail(self, error: str) -> None:
        self.state = TaskState.FAILED
        self.completed_at = time.time()
        self.error = error

    def veto(self, reason: str) -> None:
        self.state = TaskState.VETOED
        self.completed_at = time.time()
        self.error = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "phase": self.phase.value,
            "worker": self.worker,
            "state": self.state.value,
            "depends_on": self.depends_on,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class TaskManager:
    """
    Decomposes creative intents into executable subtask graphs.

    Responsibilities:
    - Task creation from intent analysis
    - Dependency resolution
    - Progress tracking
    - Readiness checks
    """

    def __init__(self) -> None:
        self._tasks: dict[str, CreativeTask] = {}
        self._created_at = time.time()

    def decompose_intent(self, intent: str, context: dict[str, Any] | None = None) -> list[CreativeTask]:
        """
        Decompose a creative intent into a standard task graph.

        Standard creative pipeline:
        1. [INTERPRET]  Aria: archetype + aesthetic decision
        2. [PLAN]       Zara: entropy + motion signature
        3. [PLAN]       Kael: pacing + timeline
        4. [REVIEW]     Uma: repetition + diversity check
        5. [BUILD]      Dara: render pipeline execution
        6. [REVIEW]     Uma: output quality verification
        7. [SYNTHESIZE] Coordinator: final assembly
        """
        ctx = context or {}

        tasks = [
            CreativeTask(
                name="decide_archetype",
                description=f"Aria: choose narrative archetype for '{intent[:60]}'",
                phase=TaskPhase.INTERPRET,
                worker="aria",
                input_data={"intent": intent, **ctx},
            ),
            CreativeTask(
                name="define_entropy",
                description="Zara: compute entropy profile and motion signature",
                phase=TaskPhase.PLAN,
                worker="zara",
                depends_on=[],  # Will be set after first task is registered
            ),
            CreativeTask(
                name="define_pacing",
                description="Kael: determine pacing and temporal structure",
                phase=TaskPhase.PLAN,
                worker="kael",
                depends_on=[],
            ),
            CreativeTask(
                name="check_diversity",
                description="Uma: verify plan diversity against creative memory",
                phase=TaskPhase.REVIEW,
                worker="uma",
                depends_on=[],
            ),
            CreativeTask(
                name="render_artifacts",
                description="Dara: execute render pipeline",
                phase=TaskPhase.BUILD,
                worker="dara",
                depends_on=[],
            ),
            CreativeTask(
                name="quality_review",
                description="Uma: verify output quality",
                phase=TaskPhase.REVIEW,
                worker="uma",
                depends_on=[],
            ),
            CreativeTask(
                name="synthesize_output",
                description="Coordinator: assemble final output and report",
                phase=TaskPhase.SYNTHESIZE,
                worker="coordinator",
                depends_on=[],
            ),
        ]

        # Register tasks and resolve dependencies
        for task in tasks:
            self._tasks[task.id] = task

        # Set dependency chain
        task_ids = [t.id for t in tasks]
        tasks[1].depends_on = [task_ids[0]]  # zara depends on aria
        tasks[2].depends_on = [task_ids[0]]  # kael depends on aria (parallel w/ zara)
        tasks[3].depends_on = [task_ids[1], task_ids[2]]  # uma-check depends on zara+kael
        tasks[4].depends_on = [task_ids[3]]  # dara depends on uma-check
        tasks[5].depends_on = [task_ids[4]]  # uma-review depends on dara
        tasks[6].depends_on = [task_ids[5]]  # synthesize depends on uma-review

        return tasks

    def get_ready_tasks(self) -> list[CreativeTask]:
        """Return tasks whose dependencies are all completed."""
        ready = []
        for task in self._tasks.values():
            if task.state != TaskState.PENDING:
                continue
            deps_met = all(
                self._tasks.get(dep_id, CreativeTask()).state == TaskState.DONE
                for dep_id in task.depends_on
            )
            if deps_met:
                ready.append(task)
        return ready

    def get_parallel_groups(self) -> list[list[CreativeTask]]:
        """Return groups of tasks that can run in parallel."""
        groups: list[list[CreativeTask]] = []
        seen: set[str] = set()

        while True:
            ready = [
                t for t in self.get_ready_tasks()
                if t.id not in seen
            ]
            if not ready:
                break
            groups.append(ready)
            for t in ready:
                seen.add(t.id)
                # Simulate completion for dependency resolution
                t.state = TaskState.DONE

        # Reset states back to pending
        for task in self._tasks.values():
            if task.id in seen:
                task.state = TaskState.PENDING

        return groups

    def get_task(self, task_id: str) -> CreativeTask | None:
        return self._tasks.get(task_id)

    def all_done(self) -> bool:
        return all(
            t.state in (TaskState.DONE, TaskState.VETOED)
            for t in self._tasks.values()
        )

    def has_failure(self) -> bool:
        return any(t.state == TaskState.FAILED for t in self._tasks.values())

    def has_veto(self) -> bool:
        return any(t.state == TaskState.VETOED for t in self._tasks.values())

    def progress(self) -> dict[str, Any]:
        """Current progress report."""
        total = len(self._tasks)
        done = sum(1 for t in self._tasks.values() if t.state == TaskState.DONE)
        failed = sum(1 for t in self._tasks.values() if t.state == TaskState.FAILED)
        running = sum(1 for t in self._tasks.values() if t.state == TaskState.RUNNING)
        return {
            "total": total,
            "done": done,
            "running": running,
            "failed": failed,
            "pending": total - done - failed - running,
            "pct": round(done / max(total, 1) * 100),
            "all_done": self.all_done(),
            "has_failure": self.has_failure(),
            "duration_ms": round((time.time() - self._created_at) * 1000, 2),
        }

    def tasks_summary(self) -> list[dict[str, Any]]:
        return [t.to_dict() for t in self._tasks.values()]
