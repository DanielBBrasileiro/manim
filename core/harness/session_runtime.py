"""
session_runtime.py — The AIOX Agentic Runtime.

Connects: prompt → context loading → tool routing → execution → persistence.

This is the central runtime that ties together:
- ToolRegistry (tool discovery and routing)
- QueryEngine (session management and token budgets)
- Creative pipeline (compiler, renderer, memory)

Design inspired by:
- claw-code PortRuntime.bootstrap_session() (full session lifecycle)
- claude-code coordinatorMode.ts (phase-based task workflow)
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.harness.query_engine import EngineConfig, QueryEngine, TurnResult
from core.harness.tool_base import AIOXTool, ToolResult, ToolStatus
from core.harness.tool_registry import (
    RoutedMatch,
    ToolPermissionContext,
    ToolRegistry,
    get_registry,
)

ROOT = Path(__file__).resolve().parent.parent.parent


@dataclass
class RuntimeContext:
    """Context collected at session bootstrap (project state, assets, memory)."""
    project_root: str = ""
    contracts_loaded: list[str] = field(default_factory=list)
    assets_available: bool = False
    memory_entries: int = 0
    active_sessions: int = 0
    mode: str = "interactive"

    def as_markdown(self) -> str:
        return "\n".join([
            "## Runtime Context",
            f"- Project: {self.project_root}",
            f"- Contracts: {', '.join(self.contracts_loaded) or 'none'}",
            f"- Assets: {'✓' if self.assets_available else '✗'}",
            f"- Memory entries: {self.memory_entries}",
            f"- Mode: {self.mode}",
        ])


@dataclass
class SessionReport:
    """Complete report of a runtime session execution."""
    session_id: str
    prompt: str
    context: RuntimeContext
    routed_tools: list[RoutedMatch]
    tool_results: list[ToolResult]
    turn_result: TurnResult
    total_duration_ms: float

    def as_markdown(self) -> str:
        lines = [
            "# AIOX Session Report",
            "",
            f"**Session:** `{self.session_id}`",
            f"**Prompt:** {self.prompt}",
            f"**Duration:** {self.total_duration_ms:.0f}ms",
            "",
            self.context.as_markdown(),
            "",
            "## Tool Routing",
        ]

        if self.routed_tools:
            for match in self.routed_tools:
                lines.append(
                    f"- **{match.tool.name}** (score={match.score}) "
                    f"[{match.tool.permission_level.value}]"
                )
        else:
            lines.append("- No tools matched")

        lines.extend(["", "## Tool Execution"])
        if self.tool_results:
            for result in self.tool_results:
                status_icon = "✓" if result.ok else "✗"
                lines.append(
                    f"- {status_icon} **{result.tool_name}** — "
                    f"{result.status.value} ({result.duration_ms:.0f}ms)"
                )
                if result.error:
                    lines.append(f"  Error: {result.error}")
        else:
            lines.append("- No tools executed")

        lines.extend([
            "",
            "## Turn Result",
            f"- Stop reason: {self.turn_result.stop_reason}",
            f"- Usage: in={self.turn_result.usage.input_tokens} "
            f"out={self.turn_result.usage.output_tokens}",
            "",
            "### Output",
            self.turn_result.output,
        ])

        return "\n".join(lines)


class SessionRuntime:
    """
    The main AIOX runtime — orchestrates a complete session.

    Lifecycle (inspired by claw-code PortRuntime.bootstrap_session):
    1. Build context (load contracts, check assets, count memory)
    2. Assemble tool pool (filtered by mode and permissions)
    3. Route prompt against tools
    4. Execute matched tools
    5. Record turn in query engine
    6. Persist session

    Usage:
        runtime = SessionRuntime()
        report = await runtime.run("quero um vídeo com tensão e silêncio")
    """

    def __init__(
        self,
        registry: ToolRegistry | None = None,
        engine_config: EngineConfig | None = None,
        permission_context: ToolPermissionContext | None = None,
        mode: str = "interactive",
    ) -> None:
        self.registry = registry or get_registry()
        self.engine = QueryEngine(config=engine_config)
        self.permission_context = permission_context or ToolPermissionContext()
        self.mode = mode

    async def run(self, prompt: str, auto_execute: bool = True) -> SessionReport:
        """
        Execute a full session cycle for a prompt.

        Steps:
        1. Bootstrap context
        2. Route prompt to tools
        3. Execute tools (if auto_execute)
        4. Record turn
        5. Persist
        """
        session_start = time.monotonic()

        # 1. Build context
        context = self._build_context()

        # 2. Route prompt
        matches = self.registry.route_prompt(
            prompt,
            limit=5,
            permission_context=self.permission_context,
        )

        # 3. Execute matched tools
        tool_results: list[ToolResult] = []
        tool_outputs: dict[str, Any] = {}

        if auto_execute and matches:
            tool_results = await self._execute_tools(matches, prompt)
            tool_outputs = {r.tool_name: r.to_dict() for r in tool_results}

        # 4. Record turn in query engine
        matched_names = tuple(m.tool.name for m in matches)
        turn_result = self.engine.submit_message(
            prompt,
            matched_tools=matched_names,
            tool_outputs=tool_outputs,
        )

        # 5. Persist session
        self.engine.persist_session(status="completed")

        total_ms = (time.monotonic() - session_start) * 1000

        return SessionReport(
            session_id=self.engine.session_id,
            prompt=prompt,
            context=context,
            routed_tools=matches,
            tool_results=tool_results,
            turn_result=turn_result,
            total_duration_ms=total_ms,
        )

    async def run_turn_loop(
        self,
        prompt: str,
        max_turns: int = 3,
    ) -> list[TurnResult]:
        """
        Run multiple turns until completion or budget exhaustion.
        Inspired by claw-code PortRuntime.run_turn_loop().
        """
        results: list[TurnResult] = []
        matches = self.registry.route_prompt(
            prompt, limit=5, permission_context=self.permission_context
        )
        matched_names = tuple(m.tool.name for m in matches)

        for turn in range(max_turns):
            turn_prompt = prompt if turn == 0 else f"{prompt} [turn {turn + 1}]"
            result = self.engine.submit_message(turn_prompt, matched_tools=matched_names)
            results.append(result)
            if result.stop_reason != "completed":
                break

        return results

    def _build_context(self) -> RuntimeContext:
        """Collect project context for the session."""
        contracts_dir = ROOT / "contracts"
        contracts = []
        if contracts_dir.exists():
            contracts = [p.stem for p in contracts_dir.glob("*.yaml")]

        assets_dir = ROOT / "assets" / "brand"
        assets_available = assets_dir.exists() and any(assets_dir.iterdir())

        memory_path = ROOT / "core" / "memory" / "creative_memory.json"
        memory_entries = 0
        if memory_path.exists():
            try:
                import json
                with open(memory_path) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    memory_entries = len(data.get("entries", data.get("creations", [])))
                elif isinstance(data, list):
                    memory_entries = len(data)
            except Exception:
                pass

        sessions_dir = ROOT / ".sessions"
        active_sessions = len(list(sessions_dir.glob("*.json"))) if sessions_dir.exists() else 0

        return RuntimeContext(
            project_root=str(ROOT),
            contracts_loaded=contracts,
            assets_available=assets_available,
            memory_entries=memory_entries,
            active_sessions=active_sessions,
            mode=self.mode,
        )

    async def _execute_tools(
        self, matches: list[RoutedMatch], prompt: str
    ) -> list[ToolResult]:
        """Execute matched tools. READ tools run in parallel, WRITE sequential."""
        from core.harness.tool_base import PermissionLevel

        # Separate read-only from write tools
        read_tools = [m for m in matches if m.tool.permission_level == PermissionLevel.READ]
        write_tools = [m for m in matches if m.tool.permission_level != PermissionLevel.READ]

        results: list[ToolResult] = []

        # Run read-only tools in parallel (safe)
        if read_tools:
            read_results = await asyncio.gather(
                *(m.tool.execute({"prompt": prompt}) for m in read_tools),
                return_exceptions=True,
            )
            for match, result in zip(read_tools, read_results):
                if isinstance(result, Exception):
                    results.append(ToolResult(
                        tool_name=match.tool.name,
                        status=ToolStatus.ERROR,
                        error=str(result),
                    ))
                else:
                    results.append(result)

        # Run write tools sequentially (safe concurrency)
        for match in write_tools:
            result = await match.tool.execute({"prompt": prompt})
            results.append(result)

        return results
