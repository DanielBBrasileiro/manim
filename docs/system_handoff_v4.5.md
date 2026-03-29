# AIOX/Antigravity Engine v4.5 - Handoff Architecture 

## 1. CORE PARADIGM SHIFT
* **FROM:** Linear execution script (`entropy = 0.8` -> `noise_strength = 0.8`).
* **TO:** Creative Operating System (`Intent -> Compiler -> State Graph -> Tools`).
* **BEHAVIOR OVER MATH:** Entropy is now interpreted semantically (`turbulent`, `laminar`) by an intelligence layer before reaching the render engine (Manim). The math physics responds to `Motion Signatures` (e.g., `chaotic_dispersion`), not raw floats.

## 2. CURRENT DIRECTORY ARCHITECTURE (`core/`)
Refactored into a highly modular, MCP-like agentic hierarchy:

*   **`compiler/` (The Brain):** Transforms `creative_seed.yaml` (natural language intent) into a structured manifest.
    *   `creative_compiler.py`: Main orchestrator of the cognitive phase.
    *   `intent_parser.py` / `plan_generator.py` / `signature_simulator.py`.
*   **`runtime/` (State Machine):** `graph_runtime.py` handles the execution graph. Currently runs "Mode 2" (Assisted Director): pauses execution dynamically after generating a `creative_plan`, asks for human terminal approval `[Y/n]`, and only then fires the render engines.
*   **`intelligence/` (Translators):** `entropy_interpreter.py` (Zara v2). Maps physical entropy (0.0-1.0) into regimes (`oscillatory`), flow, stability, and motion signatures.
*   **`agents/` (Functions):** Personas translated to pure Python logic.
    *   `aria.py`: Archetype & aesthetic decisions.
    *   `zara.py`: Physical mapping.
    *   `kael.py`: Pacing profiles.
    *   `uma.py`: Anti-repetition logic leveraging JSON memory.
*   **`tools/` (Muscles):** `render_tool.py` (Manim -> Remotion wrapper), `memory_tool.py`.
*   **`contracts/` (Memory):** YAML-based library of 12 Narrative Archetypes (`emergence`, `fragmented_reveal`) and 8 Motion Signatures (`elastic_snap`, `vortex_pull`).

## 3. DATA FLOW (Modo 2)
`Input (creative_seed.yaml) -> Compiler (Aria/Zara dicts) -> GraphRuntime pauses -> Human approves -> Render Tool (Manim scene EntropyDemo generates MP4) -> Remotion bridges composition -> Final Output.`

## 4. FUTURE EXPANSION PATHS (Actionable for AI)
1.  **AI Native Brain (LLM API hook):** Replace deterministic heuristic strings in `agents/aria.py` and `compiler/` with real LLM API calls (Anthropic/Google). The system must natively "think" about intent instead of keyword matching.
2.  **Deep Math Implementation:** The 8 `Motion Signatures` (e.g., `vortex_pull`, `elastic_snap`) are defined in contracts but need complex math translation inside `core.primitives` (Manim `fields.py` and `particle_system.py`). Elevate the physics engine!
3.  **Preview Generation (`preview_tool.py`):** Before running the heavy 60fps Manim render upon human pause, generate a fast static SVG / lightweight wireframe matrix of what the exact frame 1 will look like for precise human validation.
4.  **Autonomous Memory Embeddings:** Upgrade `creative_memory.json` into semantic local vector search to prevent style repetition across dozens of creations without relying on exactly matching archetype IDs.
