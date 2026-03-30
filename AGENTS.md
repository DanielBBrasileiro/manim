# AGENTS.md

## Visao Rapida

- Projeto: AIOX Studio / `branding`
- Objetivo: compilar briefings em videos e artefatos visuais usando um pipeline hibrido Python + Manim + Remotion.
- Entrada principal: `aiox.py`
- Documentacao-base antes de editar:
  - `README.md`
  - `docs/system_handoff_v4.5.md`
  - `docs/v4_industrialization_plan.md`
  - `docs/superpowers/specs/2026-03-30-creative-ai-upgrade-design.md`

## Stack Principal

- Python 3 no root do repositorio
- Manim CE para render fisico/matematico
- Playwright para screenshots e exportadores estaticos
- Remotion + React 18 em `engines/remotion`
- YAML/JSON como contratos e memoria local

## Diretorios Importantes

- `core/`: compilador, runtime, CLI, geradores e primitivas
- `engines/manim/`: cenas e theme para Manim
- `engines/remotion/`: composicoes React/Remotion
- `briefings/`: briefings ativos
- `contracts/`: regras de narrativa, motion, layout e identidade
- `assets/brand/`: tokens e dados sincronizados de marca
- `docs/`: handoff, planos e specs
- `.agents/`: briefs, personas, templates e skills locais
- `scripts/`: automacoes leves e utilitarios

## Areas Sensiveis

- `assets/brand/dynamic_data.json`: gerado/sobrescrito pelo pipeline
- `core/memory/creative_memory.json`: memoria persistida; nao apague historico sem pedido explicito
- `engines/remotion/public/manim_base.mp4`: artefato intermediario gerado pela ponte Manim -> Remotion
- `engines/manim/manim_theme.py`: arquivo sincronizado por identidade/brand tooling
- `output/`: artefatos de render; evite editar manualmente

## Regras de Trabalho para Agentes

- Leia a documentacao relevante antes de editar.
- Prefira mudancas minimas, localizadas e reversiveis.
- Nao altere APIs publicas da CLI ou contratos sem atualizar docs e validacao associada.
- Nao adicione segredos, tokens, credenciais ou valores sensiveis em arquivos versionados.
- Preserve o estilo do projeto: YAML/JSON como contratos, Python para orquestracao, Remotion para camada tipografica.
- Reaproveite scripts e comandos existentes antes de criar novos fluxos.
- Se tocar em arquivos gerados, explique o motivo claramente no resumo final.

## Fluxo Operacional

### Instalar dependencias

- Python:
  - `python3 -m pip install -r requirements.txt`
- Remotion:
  - `cd engines/remotion && npm install`
- Playwright browser:
  - `python3 -m playwright install chromium`

### Rodar localmente

- Criar/renderizar a partir de um briefing:
  - `python3 aiox.py create briefings/<arquivo>.yaml`
- Modo interativo:
  - `python3 aiox.py lab`
- Exploracao rapida:
  - `python3 aiox.py explore "seu prompt"`
- Sincronizar identidade:
  - `python3 aiox.py sync aiox_default`

### Lint

- Nao ha lint formal configurado no repositorio.
- Para mudancas em Python, use ao menos:
  - `python3 -m py_compile aiox.py`
  - `python3 -m py_compile <arquivos_python_editados>`

### Testes

- Nao existe suite automatizada de testes unitarios/E2E configurada no repositorio.
- Validacao minima recomendada:
  - `python3 -m py_compile <arquivos_python_editados>`
  - smoke check do fluxo tocado pela mudanca

### Validar build

- Para alteracoes em Remotion:
  - `cd engines/remotion && npm run render -- --help`
- Para alteracoes no pipeline completo, prefira um smoke check com briefing pequeno em vez de render longo desnecessario.

### E2E

- Nao existe suite E2E formal.
- Playwright e usado como dependencia de geradores/exportadores, nao como framework de testes configurado.

## Convencoes de Edicao

- Codigo Python novo: `core/`, `scripts/` ou `engines/manim/`, conforme a responsabilidade.
- Codigo React/Remotion novo: `engines/remotion/src/`.
- Contratos/configs: `contracts/`, `assets/brand/`, `templates/`.
- Documentacao nova: `docs/`.
- Nao crie migrations ou schemas externos sem necessidade real; este repo usa YAML/JSON como principal camada de configuracao e memoria.
- Variaveis de ambiente devem ser opcionais, documentadas e nunca commitadas com valores reais.

## Frontend / Remotion

- Preserve o papel do Remotion como camada de tipografia, overlay e composicao.
- Evite mudar a estrutura de `engines/remotion/src/` sem atualizar o fluxo que renderiza via `core/orchestrator.py` e `core/tools/render_tool.py`.

## Backend / Runtime Python

- Mudancas em `core/compiler/`, `core/runtime/` e `core/tools/` afetam todo o pipeline.
- Ao alterar parser, runtime ou orchestrator, valide pelo menos import, compilacao Python e um smoke check do caminho principal.

## Banco / Persistencia

- Nao ha banco tradicional.
- Persistencia atual usa JSON local (`core/memory/`, `assets/brand/`).
- Trate escrita concorrente e sobrescrita com cuidado.

## CI/CD

- Nenhum workflow CI/CD foi encontrado em `.github/workflows/`.
- Nao assuma a existencia de lint/test/build em automacao remota.

## Observabilidade

- O projeto usa logs stdout e alguns arquivos de log locais em `engines/manim/` e `engines/remotion/`.
- Nao introduza telemetria externa sem pedido explicito.

## Skills Locais

- O repo ja possui skills uteis em `.agents/skills/`, incluindo `manim-expert`, `remotion-context`, `storytelling-optimizer`, `precision-renderer` e `video-director`.
- Se a tarefa casar claramente com uma skill, use-a antes de improvisar um fluxo paralelo.

## Criterios de Conclusao

- Codigo alterado compila/importa corretamente.
- Validacoes relevantes para a area tocada foram executadas.
- Documentacao foi atualizada quando a mudanca afetou fluxo, setup ou operacao.
- Nenhum segredo foi introduzido.
