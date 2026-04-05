from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


DEFAULT_EXECUTION_STAGES = (
    "brief_parse",
    "creative_plan",
    "artifact_plan",
    "variant_generation",
    "previs",
    "quality_gate",
    "director_approval",
    "render",
    "artifact_verification",
    "decision_log",
)


@dataclass(frozen=True)
class ExecutionNode:
    id: str
    label: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExecutionEdge:
    source: str
    target: str


@dataclass
class ExecutionGraph:
    session_id: str = ""
    label: str = "execution_graph"
    stages: tuple[str, ...] = DEFAULT_EXECUTION_STAGES
    nodes: list[ExecutionNode] = field(default_factory=list)
    edges: list[ExecutionEdge] = field(default_factory=list)

    def record_step(self, step_id: str, label: str, details: dict[str, Any] | None = None, previous: str | None = None) -> None:
        node = ExecutionNode(id=step_id, label=label, details=details or {})
        self.nodes.append(node)
        if previous:
            self.edges.append(ExecutionEdge(source=previous, target=step_id))

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "label": self.label,
            "stages": list(self.stages),
            "nodes": [asdict(node) for node in self.nodes],
            "edges": [asdict(edge) for edge in self.edges],
        }

    def as_markdown(self) -> str:
        lines = ["# Execution Graph", ""]
        if self.nodes:
            lines.extend(f"- {node.id}: {node.label}" for node in self.nodes)
        else:
            lines.extend(f"- {stage}" for stage in self.stages)
        return "\n".join(lines)


def build_execution_graph(
    plan: dict[str, Any] | None = None,
    *,
    artifact_plan: dict[str, Any] | None = None,
    session_id: str = "",
    extra_stages: tuple[str, ...] = (),
) -> dict[str, Any]:
    graph = ExecutionGraph(
        session_id=session_id,
        label="execution_graph",
        stages=tuple(dict.fromkeys((*DEFAULT_EXECUTION_STAGES, *extra_stages))),
    )
    graph.record_step("brief_parse", "Parse briefing", {"has_plan": bool(plan)})
    graph.record_step(
        "creative_plan",
        "Creative planning",
        {
            "archetype": (plan or {}).get("archetype"),
            "duration": (plan or {}).get("duration"),
        },
        previous="brief_parse",
    )
    graph.record_step(
        "artifact_plan",
        "Artifact planning",
        {
            "targets": len((artifact_plan or {}).get("targets", [])),
            "distribution_mode": (artifact_plan or {}).get("distribution_mode"),
        },
        previous="creative_plan",
    )
    return graph.to_dict()
