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
