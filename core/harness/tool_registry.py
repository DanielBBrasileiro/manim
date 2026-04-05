"""
tool_registry.py — Dynamic tool autodiscovery and routing.

Discovers AIOXTool subclasses in core/tools/, registers them, and
provides routing: given a prompt, find the best-matching tools.

Design inspired by:
- claude-code's tools.ts (tool registration with conditional loading)
- claw-code's tool_pool.py (assembly with permissions context)
- claw-code's runtime.py PortRuntime.route_prompt()
"""

from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from core.harness.tool_base import AIOXTool, PermissionLevel


@dataclass(frozen=True)
class RoutedMatch:
    """A tool matched against a prompt, with a relevance score."""
    tool: AIOXTool
    score: int
    source: str = "registry"


@dataclass
class ToolPermissionContext:
    """Controls which tools are allowed in a given context."""
    denied_tools: set[str] = field(default_factory=set)
    denied_prefixes: set[str] = field(default_factory=set)
    max_permission: PermissionLevel = PermissionLevel.DESTRUCTIVE

    def is_allowed(self, tool: AIOXTool) -> bool:
        if tool.name in self.denied_tools:
            return False
        if any(tool.name.startswith(prefix) for prefix in self.denied_prefixes):
            return False
        perm_order = {PermissionLevel.READ: 0, PermissionLevel.WRITE: 1, PermissionLevel.DESTRUCTIVE: 2}
        return perm_order.get(tool.permission_level, 0) <= perm_order.get(self.max_permission, 2)


class ToolRegistry:
    """
    Central registry for all AIOX tools.

    Supports:
    - Manual registration via register()
    - Autodiscovery from core/tools/ via discover()
    - Prompt-based routing via route_prompt()
    - Pool assembly with permission filtering via assemble_pool()
    """

    def __init__(self) -> None:
        self._tools: dict[str, AIOXTool] = {}

    @property
    def tools(self) -> dict[str, AIOXTool]:
        return dict(self._tools)

    @property
    def count(self) -> int:
        return len(self._tools)

    def register(self, tool: AIOXTool) -> None:
        """Register a single tool instance."""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> AIOXTool | None:
        """Remove a tool by name. Returns the removed tool or None."""
        return self._tools.pop(name, None)

    def get(self, name: str) -> AIOXTool | None:
        """Get a tool by exact name."""
        return self._tools.get(name)

    def discover(self, package_path: str = "core.tools") -> int:
        """
        Auto-discover AIOXTool subclasses in the given package.

        Walks all modules in the package and registers any class that:
        1. Is a subclass of AIOXTool
        2. Has a non-default 'name' attribute
        3. Is not AIOXTool itself

        Returns the number of newly discovered tools.
        """
        count_before = len(self._tools)

        try:
            package = importlib.import_module(package_path)
        except ImportError:
            return 0

        package_dir = getattr(package, "__path__", None)
        if package_dir is None:
            return 0

        for importer, module_name, is_pkg in pkgutil.walk_packages(
            package_dir, prefix=f"{package_path}."
        ):
            try:
                module = importlib.import_module(module_name)
            except Exception:
                continue

            for attr_name in dir(module):
                attr = getattr(module, attr_name, None)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, AIOXTool)
                    and attr is not AIOXTool
                    and getattr(attr, "name", "unnamed_tool") != "unnamed_tool"
                ):
                    try:
                        instance = attr()
                        self.register(instance)
                    except Exception:
                        continue

        return len(self._tools) - count_before

    def route_prompt(
        self,
        prompt: str,
        limit: int = 5,
        permission_context: ToolPermissionContext | None = None,
    ) -> list[RoutedMatch]:
        """
        Match tools to a prompt by keyword scoring.

        Inspired by claw-code PortRuntime.route_prompt():
        - Score each tool against the prompt tokens
        - Filter by permission context
        - Return top matches sorted by score (desc), then name (asc)
        """
        ctx = permission_context or ToolPermissionContext()
        matches: list[RoutedMatch] = []

        for tool in self._tools.values():
            if not ctx.is_allowed(tool):
                continue
            score = tool.matches_prompt(prompt)
            if score > 0:
                matches.append(RoutedMatch(tool=tool, score=score))

        matches.sort(key=lambda m: (-m.score, m.tool.name))
        return matches[:limit]

    def assemble_pool(
        self,
        mode: str = "all",
        permission_context: ToolPermissionContext | None = None,
    ) -> list[AIOXTool]:
        """
        Assemble a filtered tool pool for a given mode.

        Modes:
        - "all": All allowed tools
        - "read_only": Only READ permission tools
        - "creative": Tools related to creative pipeline
        - "lab": Tools suitable for interactive exploration

        Inspired by claw-code tool_pool.py.
        """
        ctx = permission_context or ToolPermissionContext()

        if mode == "read_only":
            ctx = ToolPermissionContext(
                denied_tools=ctx.denied_tools,
                denied_prefixes=ctx.denied_prefixes,
                max_permission=PermissionLevel.READ,
            )

        pool = [tool for tool in self._tools.values() if ctx.is_allowed(tool)]
        pool.sort(key=lambda t: t.name)
        return pool

    def list_schemas(self, permission_context: ToolPermissionContext | None = None) -> list[dict[str, Any]]:
        """Return JSON Schema descriptions of all allowed tools (for LLM function calling)."""
        pool = self.assemble_pool(permission_context=permission_context)
        return [tool.to_schema_dict() for tool in pool]

    def as_markdown(self) -> str:
        """Human-readable summary of registered tools."""
        lines = [f"# AIOX Tool Registry ({self.count} tools)", ""]
        for tool in sorted(self._tools.values(), key=lambda t: t.name):
            lines.append(
                f"- **{tool.name}** [{tool.permission_level.value}] — {tool.description}"
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_global_registry: ToolRegistry | None = None


def get_registry(auto_discover: bool = True) -> ToolRegistry:
    """Get or create the global tool registry."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
        if auto_discover:
            _global_registry.discover("core.tools")
    return _global_registry


def reset_registry() -> None:
    """Reset the global registry (for testing)."""
    global _global_registry
    _global_registry = None
