# Runtime Governance Gap

## Governed today

- `GraphRuntime` now resolves an explicit execution policy before running.
- Important runs persist a governed JSON summary under `.sessions/runtime_runs/`.
- Step-level timing is captured for:
  - planning
  - preview
  - render
  - judge
  - persist
- Preview-loop evidence is preserved in governed run summaries.
- Benchmark runs now persist both:
  - benchmark result JSON in `core/memory/benchmark_runs/`
  - governed run metadata in `.sessions/runtime_runs/`

## Explicit execution modes

- `planning_only`
- `preview_only`
- `judge_only`
- `benchmark`
- `full_render`
- `safe_mode`

These modes currently govern whether AIOX may:
- stop after planning
- run preview/iteration only
- judge existing outputs without rendering
- run the normal full render path
- avoid heavier or mutating operations in safe mode

## Still heuristic

- `judge_only` depends on caller-provided `judge_outputs` / `existing_outputs`.
- Benchmark metrics are lightweight and preview-first by default.
- Total benchmark timing is not yet a full wall-clock rollup of each nested phase.
- Governance summaries are JSON-first; there is no dedicated CLI inspection surface yet.

## Main gaps

- No single operator-facing command to list and inspect governed runs.
- No retention or pruning policy for `.sessions/runtime_runs/`.
- No richer failure taxonomy beyond status + error count.
- No explicit governance policy around concurrent writes.
- Benchmark-to-runtime correlation uses shared run ids, but there is not yet a global index.

## Intended next step

Keep the governance layer local and operational:
- add a small run-inspection surface
- improve benchmark timing fidelity
- tighten failure classification

Without expanding AIOX into a generic agent harness.
