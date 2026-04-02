#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

# Garante que o Python carregue os módulos internos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    parser = argparse.ArgumentParser(description="AIOX Studio - Limitless Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Comando CREATE: O pipeline de ponta a ponta
    create_parser = subparsers.add_parser("create", help="Gera o vídeo final a partir de um briefing")
    create_parser.add_argument("briefing", help="Caminho para o YAML (ex: briefings/teste.yaml)")
    create_parser.add_argument("--reference", help="ID ou caminho de um contrato de referencia ja traduzido")
    create_parser.add_argument("--reference-zip", help="ZIP de snapshot de site para ingestao e producao guiada por referencia")
    create_parser.add_argument(
        "--reference-screenshot",
        dest="reference_screenshots",
        action="append",
        default=[],
        help="Screenshot opcional para enriquecer a traducao da referencia. Repetivel.",
    )
    create_parser.add_argument("--reference-notes", default="", help="Notas opcionais sobre o que emular/evitar da referencia")
    create_parser.add_argument(
        "--reference-output-dir",
        default="contracts/references",
        help="Diretorio onde contratos de referencia ingeridos via ZIP serao escritos",
    )
    create_parser.add_argument("--project", help="ID do projeto (ex: linkedin_tecnico) para carregar defaults")
    
    # NOVOS COMANDOS UX ELITE
    subparsers.add_parser("lab", help="Modo Interativo Conversacional (AIOX Lab)")
    
    explore_parser = subparsers.add_parser("explore", help="Modo Rapid Fire Massivo (Roll the dice)")
    explore_parser.add_argument("seed", help="Frase ou intenção base para o espaço latente testar")
    
    run_parser = subparsers.add_parser("run", help="Recupera uma Sessão Antiga Salva")
    run_parser.add_argument("session_id", help="Nome do arquivo em .sessions/")

    reference_parser = subparsers.add_parser(
        "reference",
        help="Captura um style pack reutilizavel a partir de uma ou mais URLs",
    )
    reference_parser.add_argument("urls", nargs="+", help="URLs de referencia")
    reference_parser.add_argument(
        "--output-dir",
        default="contracts/references",
        help="Diretorio de saida para os packs YAML/JSON",
    )

    doctor_parser = subparsers.add_parser("doctor", help="Diagnostica runtime local, modelos, renderers e style packs")
    doctor_parser.add_argument("--json", action="store_true")
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark leve do runtime local por profile")
    benchmark_parser.add_argument("--prompt", default="quero algo com silencio, tensao e resolucao elegante")
    benchmark_parser.add_argument("--iterations", type=int, default=1)
    benchmark_parser.add_argument("--profiles", nargs="+")
    benchmark_parser.add_argument("--task-roles", nargs="+")
    benchmark_parser.add_argument("--disable-cache", action="store_true")
    benchmark_parser.add_argument("--json", action="store_true")
    audit_parser = subparsers.add_parser("audit", help="Audita paridade entre artifact_plan e outputs")
    audit_parser.add_argument("--json", action="store_true")
    judge_parser = subparsers.add_parser("judge", help="Julga um artefato visual via quality runtime")
    judge_parser.add_argument("path")
    judge_parser.add_argument("--target", default="linkedin_feed_4_5")
    judge_parser.add_argument("--briefing")
    judge_parser.add_argument("--archetype", default="emergence")
    judge_parser.add_argument("--fallback", action="store_true")
    judge_parser.add_argument("--json", action="store_true")

    references_parent = subparsers.add_parser("references", help="Ferramentas de ingestao de referencias")
    references_subparsers = references_parent.add_subparsers(dest="references_command", required=True)
    references_ingest = references_subparsers.add_parser("ingest", help="Ingesta referencias em style packs")
    references_ingest.add_argument("urls", nargs="+")
    references_ingest.add_argument("--output-dir", default="contracts/references")

    style_parent = subparsers.add_parser("style", help="Ferramentas de busca de style packs")
    style_subparsers = style_parent.add_subparsers(dest="style_command", required=True)
    style_search = style_subparsers.add_parser("search", help="Busca style packs")
    style_search.add_argument("query")
    style_search.add_argument("--limit", type=int, default=5)
    style_search.add_argument("--json", action="store_true")

    variants_parent = subparsers.add_parser("variants", help="Ferramentas de ranqueamento de variantes")
    variants_subparsers = variants_parent.add_subparsers(dest="variants_command", required=True)
    variants_rank = variants_subparsers.add_parser("rank", help="Ranqueia variantes de um briefing")
    variants_rank.add_argument("briefing")
    variants_rank.add_argument("--json", action="store_true")
    variants_rank.add_argument("--heuristic", action="store_true")
    variants_rank.add_argument("--timeout-seconds", type=float)

    # Comando AGENT: Agentic Runtime (v5.0)
    agent_parser = subparsers.add_parser("agent", help="Agentic Runtime — executa prompt com tool routing automático")
    agent_parser.add_argument("prompt", nargs="?", help="Prompt para o runtime agentico")
    agent_parser.add_argument("--list-tools", action="store_true", help="Lista todas as tools registradas")
    agent_parser.add_argument("--tool", help="Executar uma tool específica pelo nome")
    agent_parser.add_argument("--mode", default="interactive", choices=["interactive", "autonomous", "read_only"], help="Modo de execução")
    agent_parser.add_argument("--json", dest="agent_json", action="store_true", help="Output em JSON")

    # Comando COORDINATE: Multi-agent creative coordinator (v5.0)
    coord_parser = subparsers.add_parser("coordinate", help="Coordena workers criativos em paralelo para uma produção autônoma")
    coord_parser.add_argument("intent", nargs="?", help="Intenção criativa para coordenar")
    coord_parser.add_argument("--list-workers", action="store_true", help="Lista workers disponíveis")
    coord_parser.add_argument("--briefing", help="Path para briefing YAML (ativa render)")
    coord_parser.add_argument("--json", dest="coord_json", action="store_true", help="Output em JSON")
    
    # Comando SYNC: Apenas sincroniza o DNA visual (útil para testes)
    sync_parser = subparsers.add_parser("sync", help="Atualiza o theme.json com a identidade solicitada")
    sync_parser.add_argument("identity", help="Ex: aiox_default", nargs="?", default="aiox_default")

    # Comando MCP: Model Context Protocol Server
    mcp_parser = subparsers.add_parser("mcp", help="Inicia o servidor MCP (Model Context Protocol) via stdio")

    args = parser.parse_args()
    
    if args.command == "create":
        import yaml
        print(f"🚀 IGNITION: AIOX Studio Engine -> Lendo {args.briefing}")
        with open(args.briefing, "r") as f:
            brief = yaml.safe_load(f)

        if getattr(args, "reference_zip", None):
            from core.compiler.reference_direction import attach_reference_to_brief, ingest_reference_zip_to_contract

            ingest_report = ingest_reference_zip_to_contract(
                args.reference_zip,
                screenshots=getattr(args, "reference_screenshots", []) or [],
                notes=getattr(args, "reference_notes", ""),
                output_dir=getattr(args, "reference_output_dir", "contracts/references"),
            )
            brief = attach_reference_to_brief(
                brief,
                reference_id=ingest_report.get("reference_contract_id"),
                translation=ingest_report.get("aiox_translation"),
                metadata={
                    "source": "reference_zip",
                    "reference_contract_path": ingest_report.get("reference_contract_path"),
                    "reference_contract_json_path": ingest_report.get("reference_contract_json_path"),
                },
            )
            print(
                f"🧭 Reference-native direction -> {ingest_report.get('reference_contract_id')} "
                f"({ingest_report.get('reference_contract_path')})"
            )
        elif getattr(args, "reference", None):
            from core.compiler.reference_direction import attach_reference_to_brief

            brief = attach_reference_to_brief(brief, reference_id=args.reference)
            print(f"🧭 Reference-native direction -> {args.reference}")

        if getattr(args, "project", None):
            brief["project_id"] = args.project
            print(f"📁 Project Profile -> {args.project}")

            
        from core.runtime.graph_runtime import GraphRuntime
        director_mode = str((brief or {}).get("director_mode", "assisted")).strip().lower()
        auto_approve = os.environ.get("AIOX_AUTO_APPROVE", "0").strip().lower() in {"1", "true", "yes"}
        runtime_mode = "autonomous" if auto_approve or director_mode in {"auto", "autonomous"} else "assisted"
        runtime = GraphRuntime(mode=runtime_mode)
        runtime.run_full(brief)
        
    elif args.command == "lab":
        from core.cli.interactive_lab import lab_mode
        lab_mode()
        
    elif args.command == "explore":
        from core.cli.interactive_lab import explore_mode
        explore_mode(args.seed)
        
    elif args.command == "run":
        from core.cli.interactive_lab import run_session
        run_session(args.session_id)

    elif args.command == "reference":
        from core.cli.reference import cli as reference_cli
        reference_args = [*args.urls, "--output-dir", args.output_dir]
        reference_cli(reference_args)
        return

    elif args.command == "references":
        if args.references_command == "ingest":
            from core.cli.reference import cli as reference_cli
            reference_cli([*args.urls, "--output-dir", args.output_dir])
            return

    elif args.command == "doctor":
        from core.cli.doctor import cli as doctor_cli
        doctor_cli(["--json"] if args.json else [])
        return

    elif args.command == "benchmark":
        from core.cli.benchmark import cli as benchmark_cli
        benchmark_args = []
        if args.prompt:
            benchmark_args.extend(["--prompt", args.prompt])
        benchmark_args.extend(["--iterations", str(args.iterations)])
        if args.profiles:
            benchmark_args.extend(["--profiles", *args.profiles])
        if args.task_roles:
            benchmark_args.extend(["--task-roles", *args.task_roles])
        if args.disable_cache:
            benchmark_args.append("--disable-cache")
        if args.json:
            benchmark_args.append("--json")
        benchmark_cli(benchmark_args)
        return

    elif args.command == "audit":
        from core.cli.audit import cli as audit_cli
        audit_args = ["--json"] if args.json else []
        audit_cli(audit_args)
        return

    elif args.command == "judge":
        from core.cli.judge import cli as judge_cli
        judge_args = [args.path, "--target", args.target, "--archetype", args.archetype]
        if args.briefing:
            judge_args.extend(["--briefing", args.briefing])
        if args.fallback:
            judge_args.append("--fallback")
        if args.json:
            judge_args.append("--json")
        judge_cli(judge_args)
        return

    elif args.command == "style":
        if args.style_command == "search":
            from core.cli.style_search import cli as style_search_cli
            style_args = [args.query, "--limit", str(args.limit)]
            if args.json:
                style_args.append("--json")
            style_search_cli(style_args)
            return

    elif args.command == "variants":
        if args.variants_command == "rank":
            from core.cli.variants_rank import cli as variants_rank_cli
            variant_args = [args.briefing]
            if args.json:
                variant_args.append("--json")
            if args.heuristic:
                variant_args.append("--heuristic")
            if args.timeout_seconds is not None:
                variant_args.extend(["--timeout-seconds", str(args.timeout_seconds)])
            variants_rank_cli(variant_args)
            return

    elif args.command == "agent":
        import asyncio as _asyncio
        from core.harness.tool_registry import get_registry
        from core.harness.session_runtime import SessionRuntime

        registry = get_registry(auto_discover=True)

        if args.list_tools:
            if getattr(args, "agent_json", False):
                import json as _json
                print(_json.dumps(registry.list_schemas(), indent=2))
            else:
                print(registry.as_markdown())
            return

        if not args.prompt:
            print("❌ Forneça um prompt ou use --list-tools")
            return

        runtime = SessionRuntime(registry=registry, mode=args.mode)
        report = _asyncio.run(runtime.run(args.prompt))

        if getattr(args, "agent_json", False):
            import json as _json
            print(_json.dumps({
                "session_id": report.session_id,
                "prompt": report.prompt,
                "tools_matched": [m.tool.name for m in report.routed_tools],
                "tool_results": [r.to_dict() for r in report.tool_results],
                "turn": report.turn_result.to_dict(),
                "duration_ms": round(report.total_duration_ms, 2),
            }, indent=2))
        else:
            print(report.as_markdown())
        return

    elif args.command == "coordinate":
        import asyncio as _asyncio
        from core.coordinator.coordinator import CreativeCoordinator
        from core.coordinator.workers import list_workers

        if args.list_workers:
            workers = list_workers()
            print(f"Workers disponíveis ({len(workers)}):")
            from core.coordinator.workers import WORKERS
            for name, w in WORKERS.items():
                print(f"  - {name}: {w.persona}")
            return

        if not args.intent:
            print("❌ Forneça uma intenção criativa ou use --list-workers")
            return

        context = {}
        if getattr(args, "briefing", None):
            context["briefing_path"] = args.briefing

        coordinator = CreativeCoordinator(context=context)
        report = _asyncio.run(coordinator.run(args.intent))

        if getattr(args, "coord_json", False):
            import json as _json
            print(_json.dumps(report.to_dict(), indent=2))
        else:
            print(report.as_markdown())
        return

    elif args.command == "sync":
        subprocess.run(["python3", "core/cli/brand.py", args.identity], check=True)

    elif args.command == "mcp":
        from core.mcp.server import serve
        serve()
        return

if __name__ == "__main__":
    main()
