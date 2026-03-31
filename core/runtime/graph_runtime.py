import json
import os
import time
from pathlib import Path

from core.intelligence.model_router import TASK_PLAN, confidence_threshold, get_route

ROOT = Path(__file__).resolve().parent.parent.parent


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
            "artifact_plan": None,
            "signature": None,
            "manifest": None,
            "previs": {},
            "quality_report": None,
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
            with open(ROOT / "assets" / "registry.json", "r") as f:
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
        self.state["artifact_plan"] = self.compilation_result.get("artifact_plan")

    def step_simulate(self):
        print("🎭 [Runtime] Simulando Output Signature")
        self.state["signature"] = self.compilation_result["output_signature"]

    def step_previs(self):
        print("🗂️ [Runtime] Gerando Storyboard e Quality Gate")
        artifact_plan = self.state.get("artifact_plan") or {}
        if not artifact_plan:
            self.state["quality_report"] = {"ok": True, "errors": [], "warnings": ["artifact_plan_missing"]}
            return

        from core.tools.preview_tool import generate_preview
        from core.tools.quality_gate import evaluate_artifact_plan
        from core.tools.storyboard_tool import summarize_storyboard, write_storyboard

        preview_path = generate_preview(self.state["plan"])
        storyboard_paths = write_storyboard(artifact_plan)
        quality_report = evaluate_artifact_plan(artifact_plan)

        self.state["previs"] = {
            "plan_preview": preview_path,
            "storyboard": storyboard_paths,
            "storyboard_text": summarize_storyboard(artifact_plan),
        }
        self.state["quality_report"] = quality_report

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
            artifact_plan = self.state.get("artifact_plan") or {}
            targets = artifact_plan.get("targets", []) if isinstance(artifact_plan, dict) else []
            if targets:
                print("🎯 Targets:")
                for target in targets:
                    if not isinstance(target, dict):
                        continue
                    print(
                        f"   - {target.get('label', target.get('id', 'target'))} "
                        f"[{target.get('render_mode', 'render')}]"
                    )
            quality_report = self.state.get("quality_report") or {}
            if quality_report.get("errors"):
                print(f"⚠️ Quality Gate errors: {', '.join(quality_report['errors'])}")
            elif quality_report.get("warnings"):
                print(f"⚠️ Quality Gate warnings: {', '.join(quality_report['warnings'])}")
            previs = self.state.get("previs") or {}
            storyboard_text = previs.get("storyboard_text")
            if storyboard_text:
                print("-" * 50)
                print(storyboard_text)
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
        self.state["output"] = render_pipeline(
            self.state["plan"],
            artifact_plan=self.state.get("artifact_plan"),
            briefing=self.state.get("input"),
            quality_report=self.state.get("quality_report"),
        )
        render_ok = self.state["output"]
        if isinstance(render_ok, dict):
            render_ok = bool(render_ok.get("ok"))
        if render_ok:
            self.state["status"] = "done"
            print("🏆 [Runtime] Cinema de Dados entregue.")
        else:
            self.state["status"] = "failed"
            print("❌ [Runtime] Render final falhou.")
        
    def step_log(self):
        try:
            from core.tools.memory_tool import save_entry
            from core.memory.feedback_store import save_decision_record, save_training_pair

            entry = {
                "timestamp": time.time(),
                "intent": self.state["intent"],
                "creative_plan": self.state["plan"],
                "artifact_plan": self.state.get("artifact_plan"),
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
            save_decision_record(
                brief=self.state.get("input"),
                creative_plan=self.state.get("plan"),
                artifact_plan=self.state.get("artifact_plan"),
                chosen_variant=str(
                    ((self.state.get("artifact_plan") or {}).get("primary_target_id"))
                    or ((self.state.get("plan") or {}).get("archetype"))
                    or "default"
                ),
                exported_targets=(self.state.get("output") or {}).get("outputs", [])
                if isinstance(self.state.get("output"), dict)
                else [],
                approved=self.state["approved"],
                review_notes=[],
            )
            print("🧠 [Runtime] Decisão gravada na Memória Criativa.")
        except Exception as exc:
            print(f"⚠️ [Runtime] Falha ao gravar memória: {exc}")

    def run_full(self, seed: dict):
        """Fluxo contínuo (usado para Testes ou Modo 3)."""
        self.load_seed(seed)
        self.step_interpret()
        self.step_plan()
        self.step_simulate()
        self.step_previs()

        llm_confidence = float((self.state.get("plan") or {}).get("llm_confidence", 1.0 if (self.state.get("plan") or {}).get("llm_scene_plan") else 0.0))
        if llm_confidence >= confidence_threshold():
            self.continue_execution()
        elif self.mode == "autonomous":
            self.continue_execution()
        else:
            self.pause_for_approval()
            
        return self.state
