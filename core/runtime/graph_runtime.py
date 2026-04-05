import json
import time

class GraphRuntime:
    """
    O Motor de Execução (Stateful Orchestration).
    Executa blocos da intenção criativa como nós de um grafo,
    permitindo pausa, inspeção do estado e retomada (Modo 2 assistido).
    """
    def __init__(self, mode="assisted"):
        self.mode = mode # 'assisted' (Modo 2) ou 'autonomous' (Modo 3)
        self.state = {
            "input": {},
            "intent": None,
            "plan": None,
            "signature": None,
            "manifest": None,
            "approved": False,
            "output": None,
            "status": "idle" # idle, compiling, paused_for_approval, rendering, done
        }
    
    def load_seed(self, seed: dict):
        self.state["input"] = seed
        self.state["status"] = "compiling"
        
    def step_interpret(self):
        print("🧠 [Runtime] Parseando Intenção de Texto Livre (N-Grams)")
        from core.compiler.creative_compiler import compile_seed
        
        # Na Fase 5 o Compilador processa tudo de uma vez. O Runtime reage à matriz.
        self.compilation_result = compile_seed(self.state["input"])
        self.state["intent"] = str(self.compilation_result["intent"])
        
    def step_plan(self):
        print("🧬 [Runtime] Gerando Creative Plan (RuleEngine DSL + Mutation Optimizer)")
        self.state["plan"] = self.compilation_result["creative_plan"]
        
    def step_simulate(self):
        print("🎭 [Runtime] Simulando Output Signature")
        self.state["signature"] = self.compilation_result["output_signature"]
        
    def pause_for_approval(self):
        """No Modo 2, expõe o plano para o usuário antes de instanciar render."""
        if self.mode == "assisted":
            self.state["status"] = "paused_for_approval"
            print("\n" + "="*50)
            print("👁  [DIRETOR ASSISTIDO] Plano Criativo Pronto para Revisão")
            print("="*50)
            print(f"🎬 Intenção: {self.state['intent']}")
            print(f"🧬 Arquétipo: {self.state['plan'].get('archetype')} | Estética: {self.state['plan'].get('aesthetic_family')}")
            print(f"🔥 Motion Signature: {self.state['signature'].get('motion')}")
            print("="*50)
            print("Aguardando confirmação do Diretor para Renderizar...")
            # Na CLI real, aqui teríamos o prompt com 'input()'.
            try:
                ans = input("Continuar para renderização? [Y/n]: ")
                if ans.strip().lower() in ['n', 'no']:
                    print("🛑 [Diretor] Operação abortada. Nenhum frame foi renderizado.")
                    return
            except EOFError:
                pass
            
            # Se aprovou, segue o fluxo
            self.continue_execution()
            
    def continue_execution(self):
        self.state["approved"] = True
        self.state["status"] = "rendering"
        self.step_render()
        self.step_log()
        
    def step_render(self):
        print("⚙️ [Runtime] Engatilhando Render Tool")
        from core.tools.render_tool import render_pipeline
        self.state["output"] = render_pipeline(self.state["plan"], briefing=self.state["input"])
        self.state["status"] = "done"
        print("🏆 [Runtime] Cinema de Dados entregue.")
        
    def step_log(self):
        from core.tools.memory_tool import save_entry
        save_entry({
            "timestamp": time.time(),
            "intent": self.state["intent"],
            "creative_plan": self.state["plan"],
            "output_signature": self.state["signature"]
        })
        print("🧠 [Runtime] Decisão gravada na Memória Criativa.")

    def run_full(self, seed: dict):
        """Fluxo contínuo (usado para Testes ou Modo 3)."""
        self.load_seed(seed)
        self.step_interpret()
        self.step_plan()
        self.step_simulate()
        
        if self.mode == "autonomous":
            self.continue_execution()
        else:
            self.pause_for_approval()
            
        return self.state
