#!/usr/bin/env python3
import argparse
import sys
import os
import subprocess

# Garante que o Python carregue os módulos internos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.orchestrator import AgenticOrchestrator

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
    
    # Comando SYNC: Apenas sincroniza o DNA visual (útil para testes)
    sync_parser = subparsers.add_parser("sync", help="Atualiza o theme.json com a identidade solicitada")
    sync_parser.add_argument("identity", help="Ex: aiox_default", nargs="?", default="aiox_default")
    
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
        
    elif args.command == "sync":
        subprocess.run(["python3", "core/cli/brand.py", args.identity], check=True)

if __name__ == "__main__":
    main()
