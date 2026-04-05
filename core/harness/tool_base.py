"""
tool_base.py — AIOX Tool base class.

Every capability of the AIOX pipeline is a Tool: a self-contained module
with its own input schema, permission model, and execution logic.

Design inspired by:
- claude-code's Tool.ts (29K lines, ~40 tools)
- claw-code's tool_pool.py (Python port of the same pattern)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class PermissionLevel(Enum):
    """Permission levels for tool execution."""
    READ = "read"              # No side effects (preview, query, list)
    WRITE = "write"            # Creates or modifies files (render, save)
    DESTRUCTIVE = "destructive"  # Deletes data or runs shell commands


class ToolStatus(Enum):
    """Execution status of a tool invocation."""
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"


@dataclass(frozen=True)
class ToolResult:
    """Immutable result from a tool execution."""
    tool_name: str
    status: ToolStatus
    output: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == ToolStatus.SUCCESS

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
            "metadata": self.metadata,
        }


class AIOXTool:
    """
    Base class for all AIOX tools.

    Subclasses must implement:
        - name: str
        - description: str
        - input_schema: dict (JSON Schema)
        - permission_level: PermissionLevel
        - _execute(params) -> Any

    Usage:
        result = await tool.execute({"briefing": "path/to/file.yaml"})
    """

    name: str = "unnamed_tool"
    description: str = "No description provided."
    input_schema: dict[str, Any] = {}
    permission_level: PermissionLevel = PermissionLevel.READ

    # Optional: keywords for prompt-based routing
    keywords: tuple[str, ...] = ()

    # Optional: when should the agent consider using this tool?
    when_to_use: str | None = None

    async def execute(self, params: dict[str, Any] | None = None) -> ToolResult:
        """Execute the tool with timing + error handling."""
        params = params or {}
        start = time.monotonic()
        try:
            output = await self._execute(params)
            elapsed = (time.monotonic() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                output=output,
                duration_ms=elapsed,
            )
        except TimeoutError as exc:
            elapsed = (time.monotonic() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                error=str(exc),
                duration_ms=elapsed,
            )
        except Exception as exc:
            elapsed = (time.monotonic() - start) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.ERROR,
                error=f"{type(exc).__name__}: {exc}",
                duration_ms=elapsed,
            )

    async def _execute(self, params: dict[str, Any]) -> Any:
        """Override in subclasses. Return value becomes ToolResult.output."""
        raise NotImplementedError(f"{self.name} has not implemented _execute()")

    def matches_prompt(self, prompt: str) -> int:
        """
        Score how well this tool matches a prompt (0 = no match).
        Inspired by claw-code PortRuntime._score().
        """
        tokens = {t.lower() for t in prompt.replace("/", " ").replace("-", " ").split() if t}
        haystacks = [
            self.name.lower(),
            self.description.lower(),
            *(kw.lower() for kw in self.keywords),
        ]
        if self.when_to_use:
            haystacks.append(self.when_to_use.lower())

        score = 0
        for token in tokens:
            if any(token in h for h in haystacks):
                score += 1
        return score

    def to_schema_dict(self) -> dict[str, Any]:
        """Return tool metadata for LLM function-calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.input_schema,
            "permission": self.permission_level.value,
        }

    def __repr__(self) -> str:
        return f"<{type(self).__name__} name={self.name!r} perm={self.permission_level.value}>"
