def interpret_entropy(entropy):
    """
    Transforma dicionário de números brutos de entropia
    em uma interpretação de Comportamento e Dinâmica (Zara v2).
    """
    phys = entropy.get("physical", 0.5)
    struc = entropy.get("structural", 0.5)
    
    # 1. Determinação do Regime
    if phys < 0.3:
        regime = "laminar"
    elif phys < 0.7:
        regime = "oscillatory"
    else:
        regime = "turbulent"
        
    # 2. Definição do Tipo de Fluxo (Flow)
    if phys < 0.5:
        flow = "linear"
    else:
        flow = "nonlinear"
        
    # 3. Motion Signatures e Ritmo Baseados no Regime
    if regime == "laminar":
        motion_signature = "coherent_flow"
        rhythm = "regular"
    elif regime == "oscillatory":
        motion_signature = "pulsing_wave"
        rhythm = "periodic"
    else:
        # Turbulent
        if struc > 0.6:
            motion_signature = "chaotic_burst"
            rhythm = "erratic"
        else:
            # Turbulento mas ordenado centralmente = Vórtice
            motion_signature = "vortex_pull"
            rhythm = "irregular"
            
    # 4. Cálculo da Estabilidade Macro
    if struc < 0.3:
        stability = "high"
    elif struc < 0.7:
        stability = "medium"
    else:
        stability = "low"
        
    return {
        "regime": regime,
        "motion_signature": motion_signature,
        "stability": stability,
        "rhythm": rhythm,
        "flow": flow
    }
