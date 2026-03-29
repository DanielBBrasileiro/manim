import json
import os
from pathlib import Path

class ThemeLoader:
    _instance = None
    _theme_data = None
    _state = "dark" # Padrão para "dark mode"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeLoader, cls).__new__(cls)
            cls._instance._load_theme()
        return cls._instance

    def _load_theme(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        theme_path = base_dir / "assets" / "brand" / "theme.json"
        
        if not os.path.exists(theme_path):
            raise FileNotFoundError(f"Tema não encontrado em {theme_path}. Rode o CLI brand.py primeiro.")
            
        with open(theme_path, 'r', encoding='utf-8') as f:
            self._theme_data = json.load(f)

    def set_state(self, state):
        """Alterna entre 'dark' ou 'inverted'"""
        if state in self._theme_data["brand"]["color_states"]:
            self._state = state
        else:
            raise ValueError(f"Estado de cor '{state}' não existe no contrato.")

    @property
    def colors(self):
        return self._theme_data["brand"]["color_states"][self._state]

    @property
    def accent_color(self):
        return self._theme_data["brand"]["color_states"]["accent"]["color"]

    @property
    def materials(self):
        return self._theme_data["brand"]["materials"]

# Instância global para facilitar importação
theme = ThemeLoader()

class IntelligenceLoader:
    """Carrega o contexto unificado gerado pelo CDE para a cena Manim."""
    def __init__(self):
        self._data = self._load_data()

    def _load_data(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        data_path = base_dir / "assets" / "brand" / "dynamic_data.json"
        
        if not os.path.exists(data_path):
            return {}
            
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_intelligence(self):
        """Unifica o CDE (dynamic_data) na nova estrutura semântica."""
        # Se não houver dados gerados, retorna um mock seguro
        if not self._data:
            return {
                "entropy": {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5},
                "interpretation": {"regime": "laminar", "motion_signature": "coherent_flow", "stability": "high", "rhythm": "regular", "flow": "linear"},
                "creative": {"archetype": "emergence", "aesthetic_family": "aiox_default"}
            }

        tech_plan = self._data.get("tech_plan", {})
        design = self._data.get("design_overlay", {})
        
        # dynamic_data.json atual tem tech_plan.entropy misturado. Vamos extrair "raw" para formar "entropy".
        imported_entropy = tech_plan.get("entropy", {})
        raw_entropy = imported_entropy.pop("raw", {"physical": 0.5, "structural": 0.5, "aesthetic": 0.5})
        
        # Retorna o modelo V2 de Inteligência
        return {
            "entropy": raw_entropy,
            "interpretation": imported_entropy,  # Regime, rhythm, motion_signature
            "creative": {
                "archetype": tech_plan.get("archetype", "emergence"),
                "aesthetic_family": design.get("aesthetic_family", "aiox_default")
            }
        }

# Expor o dicionário unificado diretamente
intelligence = IntelligenceLoader().get_intelligence()
