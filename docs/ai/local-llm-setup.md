# Local LLM Setup

## Visao Geral

O AIOX Studio usa Ollama local para gerar `Scene Plan JSON` antes do pipeline pesado de render. Nesta configuracao, o roteamento foi ajustado para Apple Silicon com foco em:

- baixo uso de memoria em MacBook Air M4 com 16 GB
- planning criativo confiavel
- fallback seguro para heuristicas existentes
- cache simples em disco para evitar recomputacao cara

## Modelos Recomendados

### Planejamento padrao

- `qwen2.5:7b-instruct-q4_K_M`
- Motivo:
  - melhor equilibrio entre qualidade, memoria e latencia para planning normal

### Planejamento rapido

- `qwen3:4b-instruct-2507-q4_K_M`
- Motivo:
  - ideal para `lab`, `explore` e previews baratos

### Fallback de qualidade

- `qwen2.5:14b-instruct-q4_K_M`
- Motivo:
  - reservado para execucao explicita de `quality_plan` ou fallback automatico opcional
  - nao deve ficar residente no Mac por muito tempo

### Visao

- `qwen3-vl:4b-instruct-q4_K_M`
- Motivo:
  - reservado para referencia visual/keyframes; nao participa do fluxo de texto comum

## Por Que 7B e o Padrao

- O 7B quantizado oferece qualidade suficiente para `Scene Plan` sem pressionar tanto a memoria unificada.
- O 14B foi mantido como fallback, nao como default, para reduzir custo operacional no Mac.
- O 4B rapido cobre ideacao e exploracao sem comprometer o pipeline principal.

## Instalacao de Modelos

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull qwen3:4b-instruct-2507-q4_K_M
ollama pull qwen2.5:14b-instruct-q4_K_M
ollama pull qwen3-vl:4b-instruct-q4_K_M
```

## Variaveis de Ambiente

Consulte o exemplo em `docs/ai/local-llm-env.example`.

Variaveis principais:

- `OLLAMA_URL`
- `OLLAMA_TEXT_MODEL`
- `OLLAMA_TEXT_FAST_MODEL`
- `OLLAMA_TEXT_QUALITY_MODEL`
- `OLLAMA_VISION_MODEL`
- `OLLAMA_TIMEOUT_SECONDS`
- `OLLAMA_RETRY_TIMEOUT_SECONDS`
- `OLLAMA_TIMEOUT_FAST_SECONDS`
- `OLLAMA_RETRY_TIMEOUT_FAST_SECONDS`
- `OLLAMA_TIMEOUT_PLAN_SECONDS`
- `OLLAMA_RETRY_TIMEOUT_PLAN_SECONDS`
- `OLLAMA_TIMEOUT_QUALITY_SECONDS`
- `OLLAMA_RETRY_TIMEOUT_QUALITY_SECONDS`
- `OLLAMA_TIMEOUT_VISION_SECONDS`
- `OLLAMA_RETRY_TIMEOUT_VISION_SECONDS`
- `OLLAMA_KEEP_ALIVE_TEXT`
- `OLLAMA_KEEP_ALIVE_FAST`
- `OLLAMA_KEEP_ALIVE_QUALITY`
- `OLLAMA_KEEP_ALIVE_VISION`
- `AIOX_LLM_CONFIDENCE_THRESHOLD`
- `AIOX_LLM_ENABLE_CACHE`
- `AIOX_LLM_CACHE_DIR`
- `AIOX_LLM_DEBUG`
- `AIOX_LLM_ROUTING_MODE`
- `AIOX_LLM_FORCE_MODEL`
- `AIOX_LLM_QUALITY_FALLBACK_MODE`
- `AIOX_LLM_DISABLE_QUALITY_FALLBACK`

Valores recomendados para o MacBook Air M4 de 16 GB:

```env
OLLAMA_TIMEOUT_FAST_SECONDS=14
OLLAMA_RETRY_TIMEOUT_FAST_SECONDS=22
OLLAMA_TIMEOUT_PLAN_SECONDS=18
OLLAMA_RETRY_TIMEOUT_PLAN_SECONDS=30
OLLAMA_TIMEOUT_QUALITY_SECONDS=45
OLLAMA_RETRY_TIMEOUT_QUALITY_SECONDS=70
OLLAMA_KEEP_ALIVE_QUALITY=0
AIOX_LLM_QUALITY_FALLBACK_MODE=explicit
```

## Roteamento Implementado

- `plan`
  - usa `OLLAMA_TEXT_MODEL`
- `fast_plan`
  - usa `OLLAMA_TEXT_FAST_MODEL`
- `quality_plan`
  - usa `OLLAMA_TEXT_QUALITY_MODEL`
- `vision_plan`
  - usa `OLLAMA_VISION_MODEL`

Comportamento:

- fluxo principal do compilador/orchestrator usa `plan`
- `lab` e `explore` usam `fast_plan`
- `quality_plan` fica explicito por padrao
- fallback automatico para 14B so acontece se `AIOX_LLM_QUALITY_FALLBACK_MODE=auto`
- visao fica reservado para etapa futura
- o 14B e descarregado ao final do uso para evitar residency desnecessaria

## Como Testar o Health Check

```bash
python3 - <<'PY'
from core.intelligence.ollama_client import check_ollama_health
print(check_ollama_health())
PY
```

## Como Rodar um Smoke Test de Planning

```bash
python3 scripts/smoke_ollama_pipeline.py
```

Modo rapido:

```bash
python3 scripts/smoke_ollama_pipeline.py --task-type fast_plan
```

Modo qualidade explicito:

```bash
python3 scripts/benchmark_llm_routes.py --iterations 1 --task-types quality_plan --disable-cache
```

Esse script verifica:

1. health check do Ollama
2. JSON valido de `ScenePlan`
3. preenchimento de `llm_scene_plan` e `llm_confidence`
4. persistencia de training pair em JSONL de smoke

## Como o Cache Funciona

- Cache dedicado em disco: `output/cache/llm`
- Chave baseada em:
  - prompt normalizado
  - asset registry
  - `task_type`
  - modelo
  - versao do schema
- Falhas nao sao cacheadas
- Pode ser desligado por `AIOX_LLM_ENABLE_CACHE=0`

## Feedback Store e Fine-Tune Futuro

O feedback store continua salvando pares aprovados em:

- `core/memory/training_pairs.jsonl`

Formato atual:

- `prompt`
- `completion`
- `metadata` opcional do planning/modelo

Isso prepara o terreno para um futuro LoRA/adapter local em Apple Silicon, por exemplo com `mlx-lm`, sem tornar o treino obrigatorio agora.

## Fine-Tune Futuro

Fase posterior, nao incluida nesta entrega:

- consolidar `training_pairs.jsonl`
- normalizar/filtrar pares ruins
- treinar adapter local com `mlx-lm`
- usar 7B fine-tuned como substituto progressivo do fallback 14B

Nada disso e dependencia obrigatoria desta entrega.

## Limitacoes Conhecidas

- se o daemon Ollama estiver desligado, o sistema cai para heuristica
- se um modelo nao estiver instalado, o fallback tenta outra rota ou degrada com log curto
- no Air M4, `quality_plan` costuma precisar timeout maior do que o fluxo normal
- `vision_plan` esta preparado, mas ainda nao ha pipeline de keyframes/ref visual completa nesta entrega
