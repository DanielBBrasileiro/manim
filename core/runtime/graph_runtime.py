import json
import os
import time
from core.intelligence.model_router import TASK_PLAN, confidence_threshold, get_route

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
        asset_registry = {}
        try:
            with open("assets/registry.json", "r") as f:
                asset_registry = json.load(f)
        except Exception:
            asset_registry = {}

        route = get_route(TASK_PLAN)
        # Na Fase 5 o Compilador processa tudo de uma vez. O Runtime reage à matriz.
        self.compilation_result = compile_seed(
            self.state["input"],
            asset_registry=asset_registry,
            task_type=route.task_type,
        )
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
            if os.environ.get("AIOX_AUTO_APPROVE", "0").strip().lower() in {"1", "true", "yes"}:
                self.continue_execution()
                return
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
        self.state["output"] = render_pipeline(self.state["plan"])
        if self.state["output"]:
            self.state["status"] = "done"
            print("🏆 [Runtime] Cinema de Dados entregue.")
        else:
            self.state["status"] = "failed"
            print("❌ [Runtime] Render final falhou.")
        
    def step_log(self):
        from core.tools.memory_tool import save_entry
        from core.memory.feedback_store import save_training_pair

        entry = {
            "timestamp": time.time(),
            "intent": self.state["intent"],
            "creative_plan": self.state["plan"],
            "output_signature": self.state["signature"]
        }
        save_entry(entry)

        raw_input = self.state.get("input")
        if isinstance(raw_input, dict):
            prompt = " ".join(str(value) for value in raw_input.values() if isinstance(value, str))
        else:
            prompt = str(raw_input or "")

        llm_scene_plan = (self.state.get("plan") or {}).get("llm_scene_plan")
        llm_metadata = (self.state.get("plan") or {}).get("llm_metadata")
        if llm_scene_plan:
            save_training_pair(
                prompt=prompt,
                completion=llm_scene_plan,
                approved=self.state["approved"],
                metadata=llm_metadata,
            )
        print("🧠 [Runtime] Decisão gravada na Memória Criativa.")

    def run_full(self, seed: dict):
        """Fluxo contínuo (usado para Testes ou Modo 3)."""
        self.load_seed(seed)
        self.step_interpret()
        self.step_plan()
        self.step_simulate()

        llm_confidence = float((self.state.get("plan") or {}).get("llm_confidence", 1.0 if (self.state.get("plan") or {}).get("llm_scene_plan") else 0.0))
        if llm_confidence >= confidence_threshold():
            self.continue_execution()
        elif self.mode == "autonomous":
            self.continue_execution()
        else:
            self.pause_for_approval()
            
        return self.state
