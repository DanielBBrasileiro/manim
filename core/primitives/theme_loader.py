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
