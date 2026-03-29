import yaml
import json
import os
import random
from pathlib import Path

class CreativeDecisionEngine:
    def __init__(self, memory_path="core/memory/creative_memory.json", archetypes_dir="contracts/narrative/archetypes"):
        self.memory_path = memory_path
        self.archetypes_dir = archetypes_dir
        self.history = self._load_json(memory_path)
        self.archetypes = self._load_archetypes()
        
    def _load_json(self, path):
        if not os.path.exists(path):
            return {"history": []}
        with open(path, 'r') as f:
            return json.load(f)

    def _load_archetypes(self):
        archetypes = {}
        if not os.path.exists(self.archetypes_dir):
            return archetypes
        for f in os.listdir(self.archetypes_dir):
            if f.endswith(".yaml"):
                with open(os.path.join(self.archetypes_dir, f), 'r') as file:
                    data = yaml.safe_load(file)
                    archetypes[Path(f).stem] = data
        return archetypes

    def decide_archetype(self, theme):
        """
        Simula a lógica da Persona 'Aria' (Creative Director).
        No futuro, isso pode ser uma chamada de LLM via MCP.
        """
        # Mapping rústico (heurística) para a versão 4.5 demo
        theme_lower = theme.lower()
        if any(w in theme_lower for w in ["scale", "growth", "birth", "emergence", "starting"]):
            return "emergence"
        if any(w in theme_lower for w in ["speed", "tension", "fragment", "breaking", "complex"]):
            return "fragmented_reveal"
        if any(w in theme_lower for w in ["result", "order", "stability", "final", "organized"]):
            return "resolution"
        
        # Default de segurança (mutação baseada no histórico)
        available = list(self.archetypes.keys())
        last_archetype = self.history.get("stats", {}).get("last_archetype")
        if last_archetype in available and len(available) > 1:
            available.remove(last_archetype)
        return random.choice(available) if available else "emergence"

    def select_aesthetic_family(self, identity):
        """
        Define a estética baseada na marca e intenção.
        """
        families = ["silent_architecture", "brutalist_signal", "organic_field", "data_narrative"]
        # Por enquanto, escolhemos baseados na identidade ou aleatório inteligente
        if identity == "aiox_default":
            return "silent_architecture"
        return random.choice(families)

    def calculate_entropy_mix(self, archetype_name, base_entropy=0.5):
        """
        Calibra a base de entropia bruta (numbers) baseada no perfil do arquétipo.
        """
        archetype = self.archetypes.get(archetype_name, {})
        profile = archetype.get("entropy_profile", "medium")
        
        # Mapeamento do perfil string para mix escalar bruto
        if profile == "low_to_medium":
            return {"physical": 0.3, "structural": 0.2, "aesthetic": 0.4}
        elif profile == "high_to_low":
            return {"physical": 0.8, "structural": 0.6, "aesthetic": 0.7}
        elif profile == "low_to_high":
            return {"physical": 0.4, "structural": 0.3, "aesthetic": 0.5}
        elif profile == "high_structural":
            return {"physical": 0.6, "structural": 0.9, "aesthetic": 0.6}
        elif profile == "rhythmic":
            return {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5}
        
        return {"structural": base_entropy, "aesthetic": base_entropy, "physical": base_entropy}

    def generate_creative_plan(self, brief):
        """
        Gera o plano final que Dara e a Engine de Matemática irão consumir.
        """
        # Extrair intenção do "creative_seed" ou do formato legado
        if "creative_seed" in brief:
            seed = brief["creative_seed"]
            intent = f"{seed.get('transformation','')} {seed.get('pacing','')} tension {seed.get('tension','')}"
        else:
            intent = brief.get("meta", {}).get("project", "") + " " + str(brief.get("scenes", []))

        identity = brief.get("meta", {}).get("active_identity", "aiox_default")
        
        selected_archetype = self.decide_archetype(intent)
        selected_aesthetic = self.select_aesthetic_family(identity)
        base_entropy = self.calculate_entropy_mix(selected_archetype)
        
        # Zara v2 (Interpretação Semântica)
        from core.intelligence.entropy_interpreter import interpret_entropy
        interpretation = interpret_entropy(base_entropy)

        arch_data = self.archetypes.get(selected_archetype, {})
        if "motion_bias" in arch_data:
            interpretation["motion_signature"] = arch_data["motion_bias"]
        
        plan = {
            "archetype": selected_archetype,
            "aesthetic_family": selected_aesthetic,
            "entropy": base_entropy,
            "interpretation": interpretation,
            "metadata": {
                "persona": "Aria & Zara v2",
                "logic": "v4.5-CDE-Director-Assisted"
            }
        }
        
        return plan

    def save_to_memory(self, plan):
        """
        Persiste a decisão para evitar repetição no próximo ciclo.
        """
        self.history["history"].append(plan)
        self.history["stats"]["total_videos"] = self.history["stats"].get("total_videos", 0) + 1
        self.history["stats"]["last_archetype"] = plan["narrative_archetype"]
        self.history["stats"]["last_aesthetic_family"] = plan["aesthetic_family"]
        
        with open(self.memory_path, 'w') as f:
            json.dump(self.history, f, indent=2)
