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
    
    # Comando SYNC: Apenas sincroniza o DNA visual (útil para testes)
    sync_parser = subparsers.add_parser("sync", help="Atualiza o theme.json com a identidade solicitada")
    sync_parser.add_argument("identity", help="Ex: aiox_default", nargs="?", default="aiox_default")
    
    args = parser.parse_args()
    
    if args.command == "create":
        print(f"🚀 IGNITION: AIOX Studio Engine -> Lendo {args.briefing}")
        orch = AgenticOrchestrator(args.briefing)
        orch.run_pipeline()
        
    elif args.command == "sync":
        subprocess.run(["python3", "core/cli/brand.py", args.identity], check=True)

if __name__ == "__main__":
    main()
