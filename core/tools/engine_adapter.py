"""
Engine Adapter Interface — core/tools/engine_adapter.py

Decouples render_pipeline from concrete engine implementations.
Each engine (Remotion, PIL-fallback, future engines) implements this contract.

Architectural note — contracts/ vs .agents/briefs/:
  contracts/       Canonical runtime contracts: token shapes, RenderManifest schema,
                   dynamic_data structure. Authoritative SSoT consumed by both the
                   Python pipeline and the TypeScript build. Import from here in
                   production code paths.
  .agents/briefs/  Planning artefacts for AI agents describing *intent*. NOT
                   authoritative; never import from .agents/briefs/ in production code.
"""
from abc import ABC, abstractmethod
from pathlib import Path


class EngineAdapter(ABC):
    @abstractmethod
    def prepare(self, artifact_plan: dict) -> None:
        """Warmup / pre-allocate resources before the first render call."""

    @abstractmethod
    def render_still(self, composition: str, output_path: Path, props: dict) -> Path:
        """Render a single frame to output_path. Returns the actual output path."""

    @abstractmethod
    def render_video(self, composition: str, output_path: Path, props: dict) -> Path:
        """Render a full video to output_path. Returns the actual output path."""

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources acquired in prepare."""
