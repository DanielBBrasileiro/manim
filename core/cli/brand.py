import os
import sys
import yaml
import json
from pathlib import Path

def load_yaml(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}

def merge_dicts(dict1, dict2):
    """Funde dois dicionários recursivamente."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def sync_identity(identity_name="aiox_default"):
    # Resolve os caminhos absolutos baseados na localização deste script
    base_dir = Path(__file__).resolve().parent.parent.parent
    contracts_dir = base_dir / "contracts"
    identity_dir = contracts_dir / "identities" / identity_name
    output_dir = base_dir / "assets" / "brand"
    
    # Garante que a pasta de output existe
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"🧬 AIOX CLI: Compilando DNA da identidade '{identity_name}'...")
    
    # 1. Carrega as Leis Globais
    global_laws = load_yaml(contracts_dir / "global_laws.yaml")
    
    # 2. Carrega os Contratos da Identidade Específica
    brand_data = load_yaml(identity_dir / "brand.yaml")
    audio_data = load_yaml(identity_dir / "audio.yaml")
    
    # (No futuro, podemos adicionar motion.yaml, layout.yaml aqui)
    
    if not brand_data:
        print(f"⚠️ Aviso: Nenhum brand.yaml encontrado para '{identity_name}'.")
    
    # 3. Funde tudo em um Master Theme
    master_theme = {
        "_meta": {
            "active_identity": identity_name,
            "generated_by": "AIOX Antigravity Engine"
        },
        "laws": global_laws.get("constraints", {}),
        "brand": brand_data,
        "audio": audio_data
    }
    
    # 4. Exporta para JSON para consumo rápido do Manim e Remotion (Node.js)
    output_file = output_dir / "theme.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_theme, f, indent=2)
        
    print(f"✅ DNA visual fundido e exportado para: {output_file.relative_to(base_dir)}")

if __name__ == "__main__":
    # Permite passar a identidade via argumento ou usa a padrão
    target_identity = sys.argv[1] if len(sys.argv) > 1 else "aiox_default"
    sync_identity(target_identity)
