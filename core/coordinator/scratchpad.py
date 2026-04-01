"""
scratchpad.py — Shared memory for inter-worker communication.

A structured scratchpad that workers use to share observations,
decisions, and artifacts during a coordinated creative session.

Inspired by claude-code's coordinator scratchpad pattern:
- Workers write observations and artifacts
- Coordinator reads the scratchpad to synthesize results
- Each entry is timestamped and tagged with the worker who wrote it
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ScratchEntry:
    """A single entry in the scratchpad."""
    worker: str
    phase: str
    content: Any
    entry_type: str = "observation"  # observation, decision, artifact, error, veto
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "worker": self.worker,
            "phase": self.phase,
            "type": self.entry_type,
            "content": self.content,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class Scratchpad:
    """
    Shared scratchpad for multi-agent coordination.

    Thread-safe (single-threaded async), ordered, filterable.
    Workers write, coordinator reads and synthesizes.
    """

    def __init__(self) -> None:
        self._entries: list[ScratchEntry] = []
        self._created_at = time.time()

    def write(
        self,
        worker: str,
        phase: str,
        content: Any,
        entry_type: str = "observation",
        confidence: float = 1.0,
    ) -> ScratchEntry:
        """Add an entry to the scratchpad."""
        entry = ScratchEntry(
            worker=worker,
            phase=phase,
            content=content,
            entry_type=entry_type,
            confidence=confidence,
        )
        self._entries.append(entry)
        return entry

    def read_all(self) -> list[ScratchEntry]:
        """Read all entries in order."""
        return list(self._entries)

    def read_by_worker(self, worker: str) -> list[ScratchEntry]:
        """Read all entries from a specific worker."""
        return [e for e in self._entries if e.worker == worker]

    def read_by_phase(self, phase: str) -> list[ScratchEntry]:
        """Read all entries from a specific phase."""
        return [e for e in self._entries if e.phase == phase]

    def read_by_type(self, entry_type: str) -> list[ScratchEntry]:
        """Read all entries of a specific type."""
        return [e for e in self._entries if e.entry_type == entry_type]

    def read_decisions(self) -> list[ScratchEntry]:
        """Read all decision entries."""
        return self.read_by_type("decision")

    def read_vetoes(self) -> list[ScratchEntry]:
        """Read all veto entries (from QA/Uma)."""
        return self.read_by_type("veto")

    def read_artifacts(self) -> list[ScratchEntry]:
        """Read all artifact entries (paths to generated files)."""
        return self.read_by_type("artifact")

    def has_veto(self) -> bool:
        """Check if any worker issued a veto."""
        return any(e.entry_type == "veto" for e in self._entries)

    def latest_decision(self, phase: str | None = None) -> ScratchEntry | None:
        """Get the most recent decision, optionally filtered by phase."""
        decisions = self.read_decisions()
        if phase:
            decisions = [d for d in decisions if d.phase == phase]
        return decisions[-1] if decisions else None

    def summary(self) -> dict[str, Any]:
        """Produce a summary of the scratchpad state."""
        workers = set(e.worker for e in self._entries)
        phases = set(e.phase for e in self._entries)
        types = {}
        for e in self._entries:
            types[e.entry_type] = types.get(e.entry_type, 0) + 1
        return {
            "total_entries": len(self._entries),
            "workers": sorted(workers),
            "phases": sorted(phases),
            "entry_types": types,
            "has_veto": self.has_veto(),
            "duration_seconds": round(time.time() - self._created_at, 2),
        }

    def to_context_string(self, max_entries: int = 20) -> str:
        """Render scratchpad as a context string for LLM prompts."""
        recent = self._entries[-max_entries:]
        lines = ["## Scratchpad Context"]
        for entry in recent:
            prefix = f"[{entry.worker}/{entry.phase}]"
            content = (
                str(entry.content)[:200]
                if not isinstance(entry.content, dict)
                else str(entry.content)[:200]
            )
            lines.append(f"- {prefix} ({entry.entry_type}) {content}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary(),
            "entries": [e.to_dict() for e in self._entries],
        }
