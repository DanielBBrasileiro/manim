import os
import sys
import yaml
import json
from pathlib import Path
import sys
import os

# Add core path to import tools
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from core.tools.color_engine import HCTColorEngine

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
    
    # 2. Carrega os Contratos da Identidade Específica e as Leis de Motion Globais
    brand_data = load_yaml(identity_dir / "brand.yaml")
    audio_data = load_yaml(identity_dir / "audio.yaml")
    motion_data = load_yaml(contracts_dir / "motion.yaml")
    layout_data = load_yaml(contracts_dir / "layout.yaml")
    
    if not brand_data:
        raise KeyError(
            f"brand.yaml ausente para identidade '{identity_name}' em {identity_dir}. "
            "Crie contracts/identities/{identity_name}/brand.yaml antes de compilar."
        )

    # Valida chaves obrigatórias — falha rápida antes de gerar tokens corrompidos
    _required_paths = [
        ["color_states"],
        ["color_states", "dark"],
        ["color_states", "dark", "background"],
        ["color_states", "dark", "foreground"],
    ]
    for key_path in _required_paths:
        node = brand_data
        for k in key_path:
            if not isinstance(node, dict) or k not in node:
                raise KeyError(
                    f"Chave obrigatória ausente em brand.yaml [{identity_name}]: "
                    f"{' > '.join(key_path)}"
                )
            node = node[k]

    if "constraints" not in global_laws:
        raise KeyError(
            "global_laws.yaml está ausente ou não contém a chave 'constraints'. "
            "Verifique contracts/global_laws.yaml."
        )

    # Generate HCT Color Palettes
    primary_color = brand_data.get("color_states", {}).get("dark", {}).get("primary", "#ffffff")
    generated_colors = HCTColorEngine.generate_semantic_tokens(primary_color)
    brand_data["colors"] = generated_colors
    
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
    
    # 4. Exporta para JSON para consumo rápido do Manim
    output_file = output_dir / "theme.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(master_theme, f, indent=2)
    
    # 5. Mestre Ouro: O Token Bridge (TypeScript genérico imutável)
    # AIOX Studio - The Token Bridge ensuring single Source of Truth
    remotion_gen_dir = base_dir / "engines" / "remotion" / "src" / "generated"
    remotion_gen_dir.mkdir(parents=True, exist_ok=True)
    
    ts_content = f"""// ⚠️ GERADO AUTOMATICAMENTE VIA core/cli/brand.py - NÃO EDITE
// Pipeline de Governança de Design Física AIOX

export const AIOX_TOKENS = {{
  layout: {json.dumps(layout_data, indent=2)},
  motion: {json.dumps(motion_data, indent=2)},
  brand: {json.dumps(master_theme['brand'], indent=2)}
}} as const;
"""
    ts_output_file = remotion_gen_dir / "aiox_tokens.ts"
    with open(ts_output_file, 'w', encoding='utf-8') as f:
        f.write(ts_content)
        
    print(f"✅ DNA visual fundido e exportado para: {output_file.relative_to(base_dir)}")
    print(f"🌉 Token Bridge compilada em TypeScript: {ts_output_file.relative_to(base_dir)}")

if __name__ == "__main__":
    # Permite passar a identidade via argumento ou usa a padrão
    target_identity = sys.argv[1] if len(sys.argv) > 1 else "aiox_default"
    sync_identity(target_identity)
