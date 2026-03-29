import os
import json
import time
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from core.compiler.creative_compiler import compile_seed
from core.runtime.graph_runtime import GraphRuntime

console = Console()
SESSIONS_DIR = ".sessions"

def setup_sessions_dir():
    if not os.path.exists(SESSIONS_DIR):
        os.makedirs(SESSIONS_DIR)

def save_session(intent_text, plan):
    setup_sessions_dir()
    session_id = f"sess_{int(time.time())}"
    filepath = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    
    with open(filepath, 'w') as f:
        json.dump({
            "input": intent_text,
            "creative_plan": plan
        }, f, indent=2)
        
    return session_id

def render_human_logs(intent_text, result):
    """Fase 1: Feedback Humano das decisões de Inteligência."""
    console.print("\n[bold neon_blue]🧠 Motor de Inferência Darwiniana[/bold neon_blue]")
    console.print(f"[italic]Entendi sua intenção como:[/italic] [green]'{intent_text}'[/green]")
    
    intent_obj = result.get("intent", "")
    plan = result.get("creative_plan", {})
    
    arch = plan.get('archetype', 'unknown')
    sig = plan.get('interpretation', {}).get('motion_signature', 'unknown')
    
    console.print(f"\n[bold yellow]🎭 Escolhas do Otimizador[/bold yellow]")
    console.print(f"[blue]▶ Arquétipo: [/blue] [bold white]{arch}[/bold white]")
    console.print(f"  [dim]↳ Selecionado devido à geometria semântica solicitada.[/dim]")
    
    console.print(f"[blue]▶ Assinatura Visual: [/blue] [bold white]{sig}[/bold white]")
    console.print(f"  [dim]↳ Aprovado pelo sistema após 5 ciclos de mutação e coerência.[/dim]\n")

def render_ascii_timeline(plan):
    """Fase 2: Instant Preview em ASCII do Motor Contínuo."""
    console.print("[bold magenta]🎬 TIMELINE PREVIEW (Temporal Engine)[/bold magenta]")
    timeline = plan.get("timeline", [])
    
    if not timeline:
        console.print("[dim]Modelo estático (Sem timeline).[/dim]\n")
        return
        
    for idx, block in enumerate(timeline):
        phase = block.get('phase', [0.0, 1.0])
        sig = block.get('behavior', 'unknown')
        tension = block.get('tension', 'medium')
        
        # Gera o progresso ASCII base do phase
        # Ex: phase [0.4, 0.8] seria ▱▱▱▱▰▰▰▰▱▱
        total_bars = 20
        start_idx = int(phase[0] * total_bars)
        end_idx = int(phase[1] * total_bars)
        
        bar = ""
        for i in range(total_bars):
            if start_idx <= i <= end_idx:
                bar += "▰"
            else:
                bar += "▱"
                
        # Legenda por tensão
        color = "white"
        if tension == "high": color = "red"
        elif tension == "low": color = "cyan"
                
        console.print(f"[[yellow]{phase[0]*10:.1f}s[/yellow]] [{color}]{bar}[/{color}] [bold white][{sig}][/bold white]")
        console.print(f"         [dim]↳ Tensão {tension.upper()} (Fase {idx+1})[/dim]")
    print() # linha vazia para separar

def render_video(plan):
    """Inicia a engrenagem de render final empacotando o GraphRuntime"""
    console.print("\n[bold green]⚙️ Iniciando Renderização de Alta Fidelidade...[/bold green]")
    # Simulando o brief original com o plan fechado
    fake_brief = {
        "creative_seed": "AIOX_LAB_BYPASS",
        "director_mode": "auto"
    }
    
    runtime = GraphRuntime(mode="auto")
    runtime.load_seed(fake_brief)
    runtime.state["plan"] = plan
    runtime.state["status"] = "compiling"
    runtime.compilation_result = {
        "creative_plan": plan,
        "output_signature": plan.get("interpretation", {}).get("motion_signature", "unknown")
    }
    runtime.step_simulate()
    runtime.step_pause_or_render()

def lab_mode():
    """Fase 1: CLI Interativa Instantânea"""
    os.system('clear')
    console.print(Panel("[bold magenta]AIOX Studio - Creative OS Lab[/bold magenta]\n[dim]Sintetizador Narrativo Interativo v6.0[/dim]"))
    
    while True:
        idea = Prompt.ask("\n[bold cyan]> Descreva sua ideia (ou 'exit' para sair)[/bold cyan]")
        if idea.lower() in ('exit', 'quit', 'q'):
            break
            
        with console.status("[bold green]Pensando no Latent Space...[/bold green]"):
            result = compile_seed(idea)
            
        plan = result["creative_plan"]
        
        render_human_logs(idea, result)
        render_ascii_timeline(plan)
        
        action = Prompt.ask(
            "[bold white]O que deseja fazer?[/bold white]\n"
            "[[green]A[/green]] Aprovar e Renderizar\n"
            "[[yellow]R[/yellow]] Regerar (Mudar Padrão)\n"
            "[[blue]S[/blue]] Salvar Sessão\n"
            "[[red]C[/red]] Cancelar",
            choices=["A", "R", "S", "C"],
            default="C"
        )
        
        if action == "A":
            render_video(plan)
            # Salva pra caso queira repetir depois
            sid = save_session(idea, plan)
            console.print(f"[dim]Sessão gravada em {sid}[/dim]")
            break
        elif action == "S":
            sid = save_session(idea, plan)
            console.print(f"[bold green]✔ O DNA criativo foi salvo na sessão {sid}[/bold green]")

def explore_mode(idea_seed):
    """Fase 3: O Modo Rapid Fire (Exploração Massiva)"""
    os.system('clear')
    console.print(Panel(f"[bold yellow]AIOX Studio - Roleta de Exploração Massiva[/bold yellow]\n[dim]Explorando 4 ramificações vetoriais para: '{idea_seed}'[/dim]"))
    
    options = []
    with console.status("[bold magenta]Mapeando quadrantes do espaço latente...[/bold magenta]"):
        for i in range(4):
            # No explore forçamos a mutação desobedecer um pouco
            res = compile_seed(idea_seed + f" VARIATION_{i}")
            options.append(res["creative_plan"])
            
    for idx, plan in enumerate(options):
        arch = plan.get("archetype", "unknown")
        sig = plan.get("interpretation", {}).get("motion_signature", "unknown")
        console.print(f"\n[bold white][ {idx+1} ][/bold white] [cyan]{arch}[/cyan] • [magenta]{sig}[/magenta]")
        
        # Mostra a timeline condensada pra ele decidir
        tls = " -> ".join([b.get('behavior', '') for b in plan.get('timeline', [])])
        console.print(f"      [dim]Fases: {tls}[/dim]")
        
    escolha = Prompt.ask("\n[bold green]> Digite o número do comportamento (ou 0 para cancelar)[/bold green]", choices=["1", "2", "3", "4", "0"])
    
    if escolha != "0":
        plan_escolhido = options[int(escolha) - 1]
        save_session(idea_seed, plan_escolhido)
        render_video(plan_escolhido)

def run_session(session_id):
    """Fase 4: Reprodução instantânea de DNA passado"""
    filepath = os.path.join(SESSIONS_DIR, session_id if session_id.endswith('.json') else f"{session_id}.json")
    if not os.path.exists(filepath):
        console.print(f"[bold red]❌ Sessão {session_id} não encontrada em {SESSIONS_DIR}.[/bold red]")
        return
        
    with open(filepath, 'r') as f:
        data = json.load(f)
        
    plan = data.get("creative_plan")
    if plan:
        console.print(f"[bold green]✔ Sessão recuperada: {data.get('input')}[/bold green]")
        render_ascii_timeline(plan)
        render_video(plan)
