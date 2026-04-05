"""
query_engine.py — Unified inference engine for AIOX Studio.

Manages LLM interaction sessions: message history, token budgets,
compaction, streaming events, structured output, and session persistence.

Adapted from claw-code QueryEnginePort (src/query_engine.py) with
AIOX-specific integrations for the model_router and ollama_client.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Generator
from uuid import uuid4

from core.memory.session_store import (
    build_session_record,
    load_session,
    save_session,
)


@dataclass(frozen=True)
class UsageSummary:
    """Token usage tracking."""
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add_turn(self, prompt: str, output: str) -> "UsageSummary":
        """Rough token estimation (4 chars ≈ 1 token)."""
        in_delta = max(1, len(prompt) // 4)
        out_delta = max(1, len(output) // 4)
        return UsageSummary(
            input_tokens=self.input_tokens + in_delta,
            output_tokens=self.output_tokens + out_delta,
        )

    def to_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass(frozen=True)
class EngineConfig:
    """Configuration for the query engine session."""
    max_turns: int = 16
    max_budget_tokens: int = 8000
    compact_after_turns: int = 12
    structured_output: bool = False
    structured_retry_limit: int = 2
    session_source: str = "harness"


@dataclass(frozen=True)
class TurnResult:
    """Immutable result from processing a single turn."""
    prompt: str
    output: str
    matched_tools: tuple[str, ...] = ()
    usage: UsageSummary = field(default_factory=UsageSummary)
    stop_reason: str = "completed"
    turn_index: int = 0
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "prompt": self.prompt,
            "output": self.output,
            "matched_tools": list(self.matched_tools),
            "usage": self.usage.to_dict(),
            "stop_reason": self.stop_reason,
            "turn_index": self.turn_index,
            "duration_ms": round(self.duration_ms, 2),
        }


class QueryEngine:
    """
    Manages an LLM conversation session with tool integration.

    Key features (inspired by claw-code QueryEnginePort):
    - Message history with automatic compaction
    - Token budget enforcement with stop reasons
    - Streaming event generation
    - Structured output with retry
    - Session persistence via session_store
    """

    def __init__(
        self,
        config: EngineConfig | None = None,
        session_id: str | None = None,
    ) -> None:
        self.config = config or EngineConfig()
        self.session_id = session_id or uuid4().hex
        self._messages: list[dict[str, Any]] = []
        self._usage = UsageSummary()
        self._turn_count = 0
        self._created_at = time.time()

    @classmethod
    def from_saved_session(cls, session_id: str) -> "QueryEngine":
        """Resume an engine from a persisted session."""
        record = load_session(session_id)
        if record is None:
            raise ValueError(f"Session not found: {session_id}")

        engine = cls(session_id=record["session_id"])
        plan = record.get("creative_plan", {})
        engine._messages = record.get("events", [])
        engine._turn_count = len(engine._messages)
        return engine

    def submit_message(
        self,
        prompt: str,
        matched_tools: tuple[str, ...] = (),
        tool_outputs: dict[str, Any] | None = None,
    ) -> TurnResult:
        """
        Process a single turn: prompt + optional tool results.

        Returns a TurnResult with output, usage, and stop_reason.
        """
        start = time.monotonic()

        # Check turn limit
        if self._turn_count >= self.config.max_turns:
            return TurnResult(
                prompt=prompt,
                output=f"Max turns reached ({self.config.max_turns})",
                matched_tools=matched_tools,
                usage=self._usage,
                stop_reason="max_turns_reached",
                turn_index=self._turn_count,
            )

        # Build output summary
        summary_lines = [f"Turn {self._turn_count + 1}: {prompt}"]
        if matched_tools:
            summary_lines.append(f"Matched tools: {', '.join(matched_tools)}")
        if tool_outputs:
            for tool_name, result in tool_outputs.items():
                status = result.get("status", "unknown") if isinstance(result, dict) else "ok"
                summary_lines.append(f"  → {tool_name}: {status}")

        output = self._format_output(summary_lines)

        # Update usage
        projected_usage = self._usage.add_turn(prompt, output)
        stop_reason = "completed"

        if projected_usage.total_tokens > self.config.max_budget_tokens:
            stop_reason = "max_budget_reached"

        # Record message
        self._messages.append({
            "role": "user",
            "content": prompt,
            "timestamp": time.time(),
            "turn": self._turn_count,
            "matched_tools": list(matched_tools),
        })
        self._usage = projected_usage
        self._turn_count += 1

        # Auto-compact if needed
        self._compact_if_needed()

        elapsed = (time.monotonic() - start) * 1000

        return TurnResult(
            prompt=prompt,
            output=output,
            matched_tools=matched_tools,
            usage=self._usage,
            stop_reason=stop_reason,
            turn_index=self._turn_count,
            duration_ms=elapsed,
        )

    def stream_events(
        self,
        prompt: str,
        matched_tools: tuple[str, ...] = (),
    ) -> Generator[dict[str, Any], None, None]:
        """
        Yield streaming events for a turn (inspired by claw-code).

        Events:
        - message_start: session info
        - tool_match: matched tools list
        - message_delta: output text chunks
        - message_stop: usage + stop reason
        """
        yield {
            "type": "message_start",
            "session_id": self.session_id,
            "prompt": prompt,
            "turn": self._turn_count,
        }

        if matched_tools:
            yield {"type": "tool_match", "tools": list(matched_tools)}

        result = self.submit_message(prompt, matched_tools)

        yield {"type": "message_delta", "text": result.output}

        yield {
            "type": "message_stop",
            "usage": result.usage.to_dict(),
            "stop_reason": result.stop_reason,
            "turn_index": result.turn_index,
        }

    def persist_session(self, status: str = "saved") -> str:
        """Save the current session state. Returns session_id."""
        # Extract prompt from first message
        intent = ""
        if self._messages:
            intent = self._messages[0].get("content", "")

        save_session(
            intent,
            creative_plan=None,
            events=self._messages,
            status=status,
            session_id=self.session_id,
            source=self.config.session_source,
            metadata={
                "engine_version": "5.0",
                "usage": self._usage.to_dict(),
                "turn_count": self._turn_count,
            },
        )
        return self.session_id

    def replay_messages(self) -> list[dict[str, Any]]:
        """Return all messages in the session (for context replay)."""
        return list(self._messages)

    def _compact_if_needed(self) -> None:
        """Drop old messages if over the compaction threshold."""
        if len(self._messages) > self.config.compact_after_turns:
            keep = self.config.compact_after_turns
            self._messages = self._messages[-keep:]

    def _format_output(self, lines: list[str]) -> str:
        if self.config.structured_output:
            return self._render_structured(lines)
        return "\n".join(lines)

    def _render_structured(self, lines: list[str]) -> str:
        payload = {
            "summary": lines,
            "session_id": self.session_id,
            "turn": self._turn_count,
        }
        for _ in range(self.config.structured_retry_limit):
            try:
                return json.dumps(payload, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                payload = {"summary": ["structured output retry"], "session_id": self.session_id}
        return json.dumps(payload)

    def summary(self) -> str:
        """Human-readable engine status."""
        return "\n".join([
            f"Session: {self.session_id}",
            f"Turns: {self._turn_count}",
            f"Messages: {len(self._messages)}",
            f"Usage: in={self._usage.input_tokens} out={self._usage.output_tokens}",
            f"Budget: {self._usage.total_tokens}/{self.config.max_budget_tokens}",
        ])
