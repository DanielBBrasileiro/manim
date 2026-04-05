#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.compiler.creative_compiler import compile_seed
from core.intelligence.model_router import TASK_FAST_PLAN, TASK_PLAN
from core.intelligence.ollama_client import check_ollama_health, generate_scene_plan
from core.memory.feedback_store import save_training_pair


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test do caminho Ollama -> compile_seed -> feedback_store")
    parser.add_argument(
        "--prompt",
        default="quero algo que respire, com curva viva emergindo da nevoa e resolucao elegante",
        help="Prompt usado no smoke test",
    )
    parser.add_argument(
        "--identity",
        default="aiox_default",
        help="Identity passada para compile_seed()",
    )
    parser.add_argument(
        "--training-path",
        default="core/memory/training_pairs.smoke.jsonl",
        help="Arquivo JSONL de saida para teste de persistencia",
    )
    parser.add_argument(
        "--task-type",
        default=TASK_PLAN,
        choices=[TASK_PLAN, TASK_FAST_PLAN],
        help="Tipo de tarefa usado no planning",
    )
    args = parser.parse_args()

    registry = _load_registry()

    print("1. Checando saude do Ollama...")
    health = check_ollama_health()
    print(json.dumps(health, ensure_ascii=True, indent=2))
    if not health["ok"]:
        print("\nSmoke test interrompido: o endpoint local do Ollama nao respondeu.")
        return 2

    print("\n2. Gerando Scene Plan estruturado...")
    scene_plan, metadata = generate_scene_plan(
        args.prompt,
        asset_registry=registry,
        task_type=args.task_type,
        return_metadata=True,
    )
    if scene_plan is None:
        print("Falha: o modelo nao retornou JSON valido para ScenePlan.")
        print(json.dumps(metadata, ensure_ascii=True, indent=2))
        return 3
    print(json.dumps(scene_plan.to_dict(), ensure_ascii=True, indent=2))
    print(json.dumps(metadata, ensure_ascii=True, indent=2))

    print("\n3. Rodando compile_seed() com o registry...")
    result = compile_seed(args.prompt, identity=args.identity, asset_registry=registry, task_type=args.task_type)
    plan = result["creative_plan"]
    llm_scene_plan = plan.get("llm_scene_plan")
    llm_confidence = plan.get("llm_confidence")
    print(
        json.dumps(
            {
                "has_llm_scene_plan": bool(llm_scene_plan),
                "llm_confidence": llm_confidence,
                "archetype": plan.get("archetype"),
                "timeline_blocks": len(plan.get("timeline", [])),
                "llm_metadata": plan.get("llm_metadata", {}),
            },
            ensure_ascii=True,
            indent=2,
        )
    )
    if not llm_scene_plan or llm_confidence is None:
        print("Falha: compile_seed() nao preencheu llm_scene_plan/llm_confidence.")
        return 4

    print("\n4. Testando persistencia de training pair...")
    training_path = ROOT / args.training_path
    if training_path.exists():
        training_path.unlink()
    ok = save_training_pair(
        args.prompt,
        llm_scene_plan,
        approved=True,
        metadata=plan.get("llm_metadata"),
        path=str(training_path),
    )
    if not ok or not training_path.exists():
        print("Falha: training pair nao foi persistido.")
        return 5

    lines = training_path.read_text(encoding="utf-8").splitlines()
    last_row = json.loads(lines[-1]) if lines else {}
    print(
        json.dumps(
            {
                "path": str(training_path.relative_to(ROOT)),
                "rows": len(lines),
                "last_row_keys": sorted(last_row.keys()),
            },
            ensure_ascii=True,
            indent=2,
        )
    )

    print("\nSmoke test concluido com sucesso.")
    return 0


def _load_registry() -> dict:
    with (ROOT / "assets" / "registry.json").open("r", encoding="utf-8") as handle:
        return json.load(handle)


if __name__ == "__main__":
    raise SystemExit(main())
