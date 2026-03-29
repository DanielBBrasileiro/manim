def interpret_entropy(entropy):
    """
    Transforma dicionário de números brutos de entropia
    em uma interpretação de Comportamento e Dinâmica (Zara v2).

    Parâmetros esperados em `entropy`:
      - "physical"   (float 0-1): nível de energia física / agitação cinética
      - "structural" (float 0-1): grau de desordem estrutural / fragmentação

    Retorna:
      - regime            : "laminar" | "oscillatory" | "turbulent"
      - motion_signature  : assinatura de movimento mapeada para AIOXNoiseField
      - stability         : "high" | "medium" | "low"
      - rhythm            : "regular" | "periodic" | "irregular" | "erratic"
      - flow              : "linear" | "nonlinear"
      - grid_type         : "regular" | "adaptive" | "fragmented"
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

    # 3. Motion Signatures e Ritmo — lógica expandida
    if regime == "laminar":
        # phys < 0.3: fluxo laminar, sem turbulência
        if flow == "linear" and phys < 0.3:
            # Fluxo puramente laminar e direcional
            motion_signature = "laminar_flow"
            rhythm = "regular"
        else:
            # Laminar mas com alguma coerência macro
            motion_signature = "coherent_flow"
            rhythm = "regular"

    elif regime == "oscillatory":
        # 0.3 <= phys < 0.7: regime oscilatório
        if 0.3 <= phys < 0.5:
            # Oscilação suave, próxima ao laminar — usa oscillatory_wave
            motion_signature = "oscillatory_wave"
            rhythm = "periodic"
        elif struc < 0.3 and phys >= 0.5:
            # Estrutura muito fragmentada em regime oscilatório = ruído fragmentado
            motion_signature = "fragmented_noise"
            rhythm = "irregular"
        elif struc > 0.6:
            # Alta desordem estrutural em oscilação = dispersão crescente
            motion_signature = "scattered_to_aligned"
            rhythm = "irregular"
        else:
            # Oscilação padrão — alias semântico para uso pelo entropy_interpreter
            motion_signature = "pulsing_wave"
            rhythm = "periodic"

    else:
        # Turbulent: phys >= 0.7
        if struc < 0.3 and phys > 0.7:
            # Baixa estrutura + alta energia física = explosão caótica
            motion_signature = "chaotic_burst"
            rhythm = "erratic"
        elif struc > 0.6:
            # Alta desordem estrutural + turbulência = dispersão caótica
            motion_signature = "chaotic_dispersion"
            rhythm = "erratic"
        elif struc < 0.5:
            # Turbulento mas com núcleo ordenado = vórtice
            motion_signature = "vortex_pull"
            rhythm = "irregular"
        else:
            # Turbulento com convergência moderada
            motion_signature = "convergence_field"
            rhythm = "irregular"

    # 4. Cálculo da Estabilidade Macro
    if struc < 0.3:
        stability = "high"
    elif struc < 0.7:
        stability = "medium"
    else:
        stability = "low"

    # 5. Tipo de Grid — regular/adaptive/fragmented baseado no regime
    if regime == "laminar":
        grid_type = "regular"
    elif regime == "oscillatory":
        grid_type = "adaptive"
    else:
        # turbulent
        if struc > 0.6:
            grid_type = "fragmented"
        else:
            grid_type = "adaptive"

    return {
        "regime": regime,
        "motion_signature": motion_signature,
        "stability": stability,
        "rhythm": rhythm,
        "flow": flow,
        "grid_type": grid_type,
    }
