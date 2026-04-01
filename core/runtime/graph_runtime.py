import json
import os
import time
from pathlib import Path

from core.intelligence.model_router import TASK_PLAN, confidence_threshold, get_route
from core.intelligence.model_profiles import get_active_profile_name
from core.runtime.artifact_parity_audit import run_artifact_parity_audit
from core.runtime.capability_pool import build_capability_pool
from core.runtime.execution_graph import ExecutionGraph
from core.runtime.review_session_store import ReviewSession, generate_review_session_id, save_review_session

ROOT = Path(__file__).resolve().parent.parent.parent


class GraphRuntime:
    """
    O Motor de Execução (Stateful Orchestration).
    Executa blocos da intenção criativa como nós de um grafo,
    permitindo pausa, inspeção do estado e retomada (Modo 2 assistido).
    """
    def __init__(self, mode="assisted"):
        self.mode = mode # 'assisted' (Modo 2) ou 'autonomous' (Modo 3)
        self.execution_graph = ExecutionGraph(label="graph_runtime")
        self.state = {
            "input": {},
            "intent": None,
            "plan": None,
            "artifact_plan": None,
            "signature": None,
            "manifest": None,
            "previs": {},
            "artifact_quality_report": None,
            "quality_report": None,
            "capability_pool": {},
            "review_session_id": None,
            "variants": [],
            "runtime_profile": get_active_profile_name(),
            "parity_audit": None,
            "approved": False,
            "output": None,
            "status": "idle", # idle, compiling, paused_for_approval, rendering, done
            "execution_graph": self.execution_graph.to_dict(),
        }
    
    def load_seed(self, seed: dict):
        self.execution_graph = ExecutionGraph(session_id=str(seed.get("session_id") or ""), label="graph_runtime")
        self.state["input"] = seed
        self.state["status"] = "compiling"
        self._record_step("load_seed", "Load seed", details={"keys": sorted(seed.keys()) if isinstance(seed, dict) else []})
        
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
        self.state["capability_pool"] = build_capability_pool()
        # Na Fase 5 o Compilador processa tudo de uma vez. O Runtime reage à matriz.
        self.compilation_result = compile_seed(
            self.state["input"],
            asset_registry=asset_registry,
            task_type=route.task_type,
        )
        self.state["intent"] = str(self.compilation_result["intent"])
        self._record_step(
            "interpret",
            "Interpret intent",
            details={
                "task_type": route.task_type,
                "intent": self.state["intent"],
                "profile": self.state["runtime_profile"],
            },
        )
        
    def step_plan(self):
        print("🧬 [Runtime] Gerando Creative Plan (RuleEngine DSL + Mutation Optimizer)")
        self.state["plan"] = self.compilation_result["creative_plan"]
        self.state["artifact_plan"] = self.compilation_result.get("artifact_plan")
        self.state["variants"] = list((self.state.get("artifact_plan") or {}).get("variants", []))
        self._record_step(
            "plan",
            "Build creative plan",
            details={
                "archetype": self.state["plan"].get("archetype") if isinstance(self.state.get("plan"), dict) else None,
                "targets": len((self.state.get("artifact_plan") or {}).get("targets", [])) if isinstance(self.state.get("artifact_plan"), dict) else 0,
                "variants": len(self.state["variants"]),
            },
        )

    def step_simulate(self):
        print("🎭 [Runtime] Simulando Output Signature")
        self.state["signature"] = self.compilation_result["output_signature"]
        self._record_step("simulate", "Simulate output signature", details={"signature": self.state["signature"]})

    def step_previs(self):
        print("🗂️ [Runtime] Gerando Storyboard e Quality Gate")
        artifact_plan = self.state.get("artifact_plan") or {}
        if not artifact_plan:
            self.state["artifact_quality_report"] = {"ok": True, "errors": [], "warnings": ["artifact_plan_missing"]}
            self._record_step("preview", "Generate preview", details={"artifact_plan_missing": True})
            return

        from core.tools.preview_tool import generate_preview
        from core.tools.quality_gate import evaluate_artifact_plan
        from core.tools.storyboard_tool import summarize_storyboard, write_storyboard

        preview_path = generate_preview(self.state["plan"])
        storyboard_paths = write_storyboard(artifact_plan)
        quality_report = evaluate_artifact_plan(artifact_plan)
        try:
            from core.runtime.variant_ranker import rank_variants

            ranking = rank_variants(artifact_plan)
            artifact_plan["chosen_variant"] = ranking.get("chosen_variant") or artifact_plan.get("chosen_variant")
            artifact_plan["variant_scores"] = ranking.get("variant_scores", {})
            artifact_plan["chosen_variant_reason"] = ranking.get("chosen_variant_reason", "rank_unavailable")
        except Exception:
            pass

        self.state["previs"] = {
            "plan_preview": preview_path,
            "storyboard": storyboard_paths,
            "storyboard_text": summarize_storyboard(artifact_plan),
        }
        self.state["artifact_quality_report"] = quality_report
        if isinstance(self.state.get("artifact_plan"), dict):
            review_session_id = generate_review_session_id()
            self.state["review_session_id"] = review_session_id
            self.state["artifact_plan"]["review_session_id"] = review_session_id
            save_review_session(
                ReviewSession(
                    review_session_id=review_session_id,
                    created_at=time.time(),
                    profile=self.state["runtime_profile"],
                    brief=self.state.get("input") or {},
                    artifact_plan=self.state["artifact_plan"],
                    variants=self.state.get("variants") or [],
                    chosen_variant=str((self.state["artifact_plan"] or {}).get("chosen_variant") or "variant_01"),
                    quality_report=quality_report,
                )
            )
        self._record_step(
            "preview",
            "Generate preview",
            details={
                "storyboard_paths": storyboard_paths,
                "quality_ok": quality_report.get("ok"),
                "review_session_id": self.state.get("review_session_id"),
            },
        )

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
            chosen_variant = (artifact_plan or {}).get("chosen_variant")
            if chosen_variant:
                print(f"🧪 Variante: {chosen_variant}")
            quality_report = self.state.get("artifact_quality_report") or {}
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
        self.step_quality()
        self.step_log()
        
    def step_render(self):
        print("⚙️ [Runtime] Engatilhando Render Tool")
        from core.tools.render_tool import render_pipeline
        self.state["output"] = render_pipeline(
            self.state["plan"],
            artifact_plan=self.state.get("artifact_plan"),
            briefing=self.state.get("input"),
            quality_report=self.state.get("artifact_quality_report"),
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
        self._record_step("render", "Render output", details={"ok": bool(render_ok), "status": self.state["status"]})

    def step_quality(self):
        exported_targets = (self.state["output"] or {}).get("outputs", []) if isinstance(self.state.get("output"), dict) else []
        if not exported_targets:
            self.state["quality_report"] = {
                "ok": False,
                "render_ok": False,
                "brand_ok": False,
                "vision_ok": False,
                "premium_ok": False,
                "quality_pass": False,
                "brand_precheck": False,
                "frame_scores": [],
                "iteration_count": 0,
                "final_quality_summary": "Nenhum output disponível para QA.",
                "native_vs_fallback": {"native_outputs": 0, "fallback_outputs": 0},
                "target_reports": {},
            }
        else:
            print("🧪 [Runtime] Rodando Quality Runtime canônico...")
            from core.quality.quality_runtime import run_quality_pipeline

            self.state["quality_report"] = run_quality_pipeline(
                exported_targets,
                self.state.get("artifact_plan") or {},
                context={
                    "archetype": (self.state.get("plan") or {}).get("archetype"),
                    "runtime_profile": self.state.get("runtime_profile"),
                    "capability_pool": self.state.get("capability_pool") or {},
                },
            )

        self.state["parity_audit"] = run_artifact_parity_audit(
            self.state.get("artifact_plan"),
            exported_targets,
            profile_name=self.state.get("runtime_profile"),
            quality_report=self.state.get("quality_report"),
        )
        summary = (self.state.get("quality_report") or {}).get("final_quality_summary")
        if summary:
            print(f"🛡️ [Runtime] Quality summary: {summary}")
        self._record_step(
            "quality",
            "Evaluate render quality",
            details={
                "quality_pass": bool((self.state.get("quality_report") or {}).get("quality_pass")),
                "premium_ok": bool((self.state.get("quality_report") or {}).get("premium_ok")),
            },
        )
        
    def step_log(self):
        try:
            from core.tools.memory_tool import save_entry
            from core.memory.feedback_store import save_decision_record, save_training_pair

            entry = {
                "timestamp": time.time(),
                "intent": self.state["intent"],
                "creative_plan": self.state["plan"],
                "artifact_plan": self.state.get("artifact_plan"),
                "artifact_quality_report": self.state.get("artifact_quality_report"),
                "quality_report": self.state.get("quality_report"),
                "output_signature": self.state["signature"],
                "execution_graph": self.execution_graph.to_dict(),
                "parity_audit": self.state.get("parity_audit").stats if self.state.get("parity_audit") else {},
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
                chosen_variant=str((self.state.get("artifact_plan") or {}).get("chosen_variant") or "variant_01"),
                exported_targets=(self.state.get("output") or {}).get("outputs", [])
                if isinstance(self.state.get("output"), dict)
                else [],
                approved=self.state["approved"],
                review_notes=[],
                variants=self.state.get("variants"),
                runtime_profile=self.state.get("runtime_profile"),
                review_session_id=self.state.get("review_session_id"),
                benchmark_metrics=self.state.get("parity_audit").stats if self.state.get("parity_audit") else {},
                quality_report=self.state.get("quality_report"),
            )
            print("🧠 [Runtime] Decisão gravada na Memória Criativa.")
        except Exception as exc:
            print(f"⚠️ [Runtime] Falha ao gravar memória: {exc}")
        self._record_step("persist", "Persist memory", details={"memory_entry": True})

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

    def _record_step(self, step_id: str, label: str, details: dict | None = None):
        previous = self.execution_graph.nodes[-1].id if self.execution_graph.nodes else None
        self.execution_graph.record_step(step_id, label, details=details or {}, previous=previous)
        self.state["execution_graph"] = self.execution_graph.to_dict()
