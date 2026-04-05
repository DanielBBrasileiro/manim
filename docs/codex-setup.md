# Codex Setup

## Objetivo

Usar este repositorio com Codex de forma eficiente e previsivel, respeitando a arquitetura real do projeto: Python + Manim no root, Remotion/React em `engines/remotion`, contratos em YAML/JSON e um pipeline orientado por briefings.

## O Que Foi Configurado no Repo

- `AGENTS.md`
  - Instrucoes operacionais especificas para este projeto.
- `.codex/config.toml`
  - Defaults conservadores para uso do Codex neste repositorio.
  - MCPs recomendados do projeto ja foram registrados aqui como configuracao de referencia.
- `scripts/setup-codex.sh`
  - Script idempotente de verificacao de ambiente. Nao instala nada automaticamente.
- `.mcp.json`
  - Mantido no repo e ampliado com presets para `openaiDeveloperDocs`, `context7`, `github` e `playwright`, todos com `autoStart: false`.

## O Que Voce Ainda Pode Configurar Fora do Repo

- Seu config global pessoal do Codex
- Login/autenticacao para MCPs
- Plugins opcionais
- Editor/IDE
- Instalacao de binarios locais como `manim`, `ffmpeg`, `ollama` e MCP servers externos

## MCPs Recomendados para Este Projeto

### OpenAI Docs MCP

- Quando usar:
  - Se voce for tocar integracoes OpenAI, comparar modelos, migrar SDKs ou revisar docs oficiais atualizadas.
- Por que ajuda:
  - Traz documentacao primaria e recente para trabalho de integracao.
- Pre-requisitos:
  - Binario/comando do servidor MCP disponivel no ambiente.
- Estado neste repo:
  - Configurado em `.codex/config.toml` e pre-registrado em `.mcp.json`.

### Context7

- Quando usar:
  - Para consultar documentacao recente de React, Remotion, Playwright e outras bibliotecas rapidas de mudar.
- Por que ajuda:
  - Este repo mistura Python e frontend de video; docs atualizadas de dependencias podem destravar mudancas pontuais.
- Pre-requisitos:
  - Opcionalmente, uma API key do Context7 para limites melhores.
- Estado neste repo:
  - Configurado em `.codex/config.toml` e pre-registrado em `.mcp.json`.
- Observacao:
  - A configuracao versionada nao inclui credenciais. Se voce quiser limites maiores, adicione sua credencial no ambiente pessoal, nao no repo.

### GitHub MCP Server

- Quando usar:
  - Ao revisar PRs, issues, diffs remotos e estado de integracao no GitHub.
- Por que ajuda:
  - Este repo tem fluxo de evolucao por specs e handoffs; GitHub MCP agrega valor se o trabalho estiver preso a PRs/issues.
- Pre-requisitos:
  - Autenticacao GitHub/OAuth em cliente MCP compativel.
- Estado neste repo:
  - Configurado em `.codex/config.toml` e pre-registrado em `.mcp.json`.

### Playwright MCP

- Quando usar:
  - Para validacao em navegador de fluxos visuais, tooling de screenshot ou futuras verificacoes de UI.
- Por que ajuda:
  - Playwright ja aparece no stack Python para exportadores estaticos, entao ha afinidade real com o projeto.
- Pre-requisitos:
  - Node.js e acesso ao pacote `@playwright/mcp@latest` via `npx`.
- Estado neste repo:
  - Configurado em `.codex/config.toml` e pre-registrado em `.mcp.json`.

## Plugins Opcionais

### Gmail

- Vale a pena se:
  - Voce usa Codex para operar briefs, feedbacks ou aprovacoes que chegam por email.
- Nao vale a pena se:
  - Seu fluxo e puramente local/terminal.

### Google Drive

- Vale a pena se:
  - Briefings, referencias ou entregas finais vivem no Drive.
- Nao vale a pena se:
  - Tudo ja esta versionado no repo ou em storage local.

### Slack

- Vale a pena se:
  - Revisoes e aprovacoes acontecem no Slack e voce quer fechar o loop de execucao/comunicacao.
- Nao vale a pena se:
  - O trabalho acontece sem dependencia de mensagens em workspace.

## Skills

Este repo se beneficia de skills locais ja existentes em `.agents/skills/`, principalmente:

- `manim-expert`
- `remotion-context`
- `storytelling-optimizer`
- `precision-renderer`
- `video-director`

Prioridade:

- Use essas skills quando a tarefa casar claramente com o dominio.
- Nao e prioridade criar novas skills para o setup de Codex agora; o repo ja tem uma base boa.

## Fluxos Recomendados

### Entender a arquitetura antes de editar

1. Leia `README.md`.
2. Leia `docs/system_handoff_v4.5.md`.
3. Leia `AGENTS.md`.
4. So depois abra os arquivos de implementacao.

### Corrigir bug com validacao

1. Identifique o caminho afetado em `core/`, `engines/manim/` ou `engines/remotion/`.
2. Edite de forma localizada.
3. Rode `python3 -m py_compile <arquivos_python_editados>` para mudancas em Python.
4. Se tocou Remotion, rode `cd engines/remotion && npm run render -- --help` ou um render smoke pequeno.

### Implementar feature pequena

1. Confirme a fonte de verdade em docs/specs/briefings.
2. Reaproveite scripts e contratos existentes.
3. Atualize docs se o fluxo operacional mudou.

### Atualizar documentacao e testes

1. Prefira complementar docs existentes em vez de reescrever tudo.
2. Como nao ha suite formal, registre claramente quais smoke checks foram usados.

### Revisar impacto em CI

- Nao existe CI formal detectado em `.github/workflows/`.
- Trate a validacao local como obrigatoria antes de propor commit.

## Troubleshooting

### Binario MCP ausente

- Sintoma:
  - O servidor MCP nao inicia.
- Acao:
  - Mantenha o MCP desabilitado no seu cliente e instale/configure o servidor no seu ambiente antes de tentar usar.

### Timeout ao iniciar MCP

- Sintoma:
  - Inicializacao muito lenta ou handshake falhando.
- Acao:
  - Teste o comando manualmente fora do Codex e reduza o numero de MCPs ativos ao mesmo tempo.

### Falta de credenciais

- Sintoma:
  - GitHub/OpenAI/servicos externos negam acesso.
- Acao:
  - Configure credenciais no ambiente do usuario; nao salve nada sensivel no repo.

### Ambiente sem rede

- Sintoma:
  - MCPs/documentacao remota nao carregam.
- Acao:
  - Trabalhe com docs locais e com o fallback offline do projeto. Este setup foi feito para degradar graciosamente.

### Comando de lint/test nao encontrado

- Situacao deste repo:
  - Nao ha lint/test formal configurado.
- Acao:
  - Use `py_compile`, smoke checks do pipeline e validacoes de Remotion/Manim conforme a area alterada.

### Projeto grande demais ou instrucoes conflitantes

- Acao:
  - Priorize `README.md`, `docs/system_handoff_v4.5.md`, o spec mais recente em `docs/superpowers/specs/` e `AGENTS.md`.

## Proximos Passos

- Rode `bash scripts/setup-codex.sh`
- Instale dependencias faltantes
- Habilite no seu cliente apenas os MCPs que quiser usar no dia a dia
- Complete a autenticacao do GitHub MCP e, se quiser limites melhores, do Context7
- Ajuste seu config global pessoal do Codex se quiser
- Valide o primeiro fluxo com um smoke check pequeno antes de mudancas maiores
