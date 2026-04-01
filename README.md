# 🏛️ branding v4.4 — The Invisible Architecture

> **branding é um compilador de conteúdo visual de elite.**
> Ele transforma intenções em linguagem natural em peças audiovisuais de padrão cinematográfico: vídeos, posts, carrosséis e posters. Cada frame é processado sob as leis da **Engenharia de Percepção**.

---

## 🎭 1. A Filosofia: Cinema de Dados Narrativo

O branding v4.4 marca a transição definitiva do "infográfico técnico" para o **"Cinema de Dados"**. 

Diferente de ferramentas tradicionais que usam ícones de nuvem e logos de tecnologias (AWS, Python, Rust), o AIOX utiliza **Primitivos Matemáticos Abstratos**. Uma base de dados não é um cilindro; é um ponto de origem. Uma pipeline não é uma seta; é uma curva orgânica ultrapassando limites geométricos.

### O Teste do Pôster
Cada segundo de um vídeo gerado pelo AIOX deve passar no **Teste do Pôster**: se você pausar o vídeo em qualquer frame, aquela imagem deve ser bela o suficiente para ser emoldurada e exposta em uma galeria.

---

## 📜 2. As 7 Leis de Design (Governance)

Toda produção do AIOX é regida por 7 leis absolutas, definidas nos `contracts/`:

1.  **O Espaço é o Protagonista**: Mínimo de 40% de espaço negativo em cada frame.
2.  **Monocromia + 1**: A paleta base é sempre Preto e Branco. Apenas um "Acento Cirúrgico" (Cyber Red) é permitido para guiar o olhar.
3.  **Zero Ícones, Zero Logos**: A identidade vem da geometria e do movimento, nunca de ativos externos.
4.  **Tipografia como Arquitetura**: Máximo de 2 pesos de fonte. O texto não legenda; o texto narra.
5.  **Movimento com Propósito**: Se uma animação pode ser removida sem alterar a emoção do ato, ela deve ser deletada.
6.  **Física de Mola (Springs)**: Nada se move de forma linear. Tudo tem massa, tensão e amortecimento.
7.  **A Referência é o Piso, não o Teto**: O output deve parecer que a marca de referência contratou um diretor de arte ainda melhor.

---

## 🤖 3. Orquestração Multi-Agente (Framework Aria/Dara/Uma)

A produção é automatizada por uma tríade de agentes especializados:

*   **Aria (Diretora Criativa)**: Analisa briefings, define o arco emocional (Gênese → Turbulência → Resolução) e gera planos de direção. Ela nunca toca no código; ela governa a visão.
*   **Dara (Engenheira de Produção)**: Converte os planos de Aria em código Manim (física) e Remotion (tipografia). Ela é a mestre da precisão técnica.
*   **Uma (Designer de Sistemas)**: Atua no QA visual. Revisa cada frame contra as 7 Leis e rejeita qualquer pixel que não atinja o padrão Premium.

---

## 🛠️ 4. Stack Tecnológica

O AIOX utiliza um pipeline híbrido de renderização:

1.  **Manim (Physics Engine)**: Renderiza a geometria, física e transformações matemáticas em alta definição (1080p60).
2.  **Remotion (Perception Engine)**: Renderiza a camada de tipografia, overlays de textura (grain), e sincronização rítmica usando React.
3.  **FFmpeg (Final Synthesis)**: Consolida as camadas e aplica o transcode industrial H.264 YUV420P para compatibilidade universal.

---

## 📂 5. Arquitetura do Repositório

```text
.
├── AIOX_STUDIO_CONTEXT.md       # Cérebro do Projeto (Comandos & Leis)
├── aiox.py                      # CLI Mestra (Entry Point Industrial)
├── assets/
│   └── brand/                   # Design Tokens (JSON) e Assets de Marca
├── briefings/                   # Projetos Ativos (Briefings YAML)
├── contracts/                   # As Leis Absolutas (YAML)
│   ├── identities/              # Brand, Motion, Layout, Narrative...
│   └── references/              # DNA de marcas reais (ex: Stripe, Linear)
├── core/                        # Inteligência do Sistema
│   ├── cli/                     # Implementação dos comandos da CLI
│   ├── generators/              # Motores (Vídeo, Estático, Carrossel)
│   ├── primitives/              # Biblioteca de Formas (LivingCurve, NeuralGrid)
│   └── orchestrator.py          # Gestão do Pipeline Narrativo
├── engines/                     # Motores de Renderização
│   ├── manim/                   # Scripts de Física Matemática
│   └── remotion/                # Composições React & Tipografia
├── output/                      # Entregas Finais
│   ├── posts/                   # Imagens e Estáticos (PNG)
│   └── renders/                 # Vídeos Cinematográficos (MP4)
└── templates/                   # Presets Reutilizáveis
    ├── formats/                 # Reels (9:16), LinkedIn (4:5), Square (1:1)
    ├── narratives/              # Roteiros (Three Act Tension, Reveal)
    └── styles/                  # Estéticas (Luxury Dark, Brutalist Raw, Editorial)
```

---

## 🚀 6. Fluxo de Utilização (The Industrial Loop)

O AIOX foi desenhado para ser operado via linguagem natural ou comandos diretos.

### 6.1 Criar uma Nova Peça (Vídeo)
Para gerar um vídeo completo a partir de um briefing:
```bash
python3 aiox.py create briefings/seu_projeto.yaml
```
Este comando executa um fluxo unificado: **creative_plan** → **artifact_plan** → **previs/quality gate** → **render por target**.
Um briefing forte agora pode gerar, no mesmo pacote, short vertical, still para LinkedIn, carousel quadrado, essay 16:9 e thumbnail.

Se o Remotion local estiver indisponivel ou lento demais para responder dentro do timeout configurado, o pipeline abre um fallback automatico por target sem abortar o run inteiro. Os outputs canônicos ficam em:
- `output/renders/short_cinematic_vertical.mp4`
- `output/stills/linkedin_feed_4_5.png`
- `output/carousel/linkedin_carousel_square/`
- `output/renders/youtube_essay_16_9.mp4`
- `output/stills/youtube_thumbnail_16_9.png`
Para priorizar o still hero em Remotion nativo, voce pode ajustar timeouts separados:
- `AIOX_REMOTION_STILL_TIMEOUT_SECONDS`
- `AIOX_REMOTION_VIDEO_TIMEOUT_SECONDS`
- `AIOX_REMOTION_BUNDLE_TIMEOUT_SECONDS`

O renderer direto agora tenta reaproveitar bundles por padrao (`AIOX_REMOTION_REUSE_BUNDLE=1`) e faz um prewarm antes do primeiro target nativo. Isso evita que cada artefato pague novamente o cold start pesado do Remotion local.

No ambiente local deste repo, o caminho estavel do Remotion usa webpack classico por padrao. O modo `rspack` fica desativado, e os patches de runtime sao reaplicados automaticamente no `npm install` de `engines/remotion` via `scripts/patch_remotion_runtime.py`. Para experimentar `rspack` manualmente, use `AIOX_REMOTION_USE_RSPACK=1`.

### 6.2 Extrair DNA de Design
Para capturar as cores, fontes e espaçamento de qualquer site:
```bash
python3 aiox.py reference https://stripe.com
```
Isso gera um style pack reutilizavel em `contracts/references/stripe_com.yaml` e `contracts/references/stripe_com.json`, que pode ser usado em qualquer briefing futuro.

Para a trilha lab de referencias e busca de linguagem visual:
```bash
python3 aiox.py references ingest https://stripe.com
python3 aiox.py style search "poster curve minimal"
```

### 6.3 Julgar qualidade e ranquear variantes
Para rodar o juiz visual/brand sobre um artefato especifico:
```bash
python3 aiox.py judge output/stills/linkedin_feed_4_5.png --target linkedin_feed_4_5 --json
```

Para ranquear variantes do artifact plan:
```bash
python3 aiox.py variants rank briefings/seu_projeto.yaml --json
```

Se quiser uma execucao local mais previsivel, sem esperar pelo rankeamento via LLM:
```bash
python3 aiox.py variants rank briefings/seu_projeto.yaml --heuristic --json
```

### 6.4 Sincronizar Marca
Para atualizar os tokens de design sem renderizar:
```bash
python3 aiox.py sync briefings/projeto.yaml
```

---

## 🎨 7. Estéticas e Presets

O sistema já vem configurado com 6 presets de alto nível:

| ID | Estética | Inspiração |
|----|----------|------------|
| `monochrome_cinema` | Preto & Branco Puro | Cinema Noir / Dados Puros |
| `luxury_dark` | Deep Black + Gold | Apple Keynotes / Porsche |
| `editorial_minimal` | White Space + Indigo | Stripe / Linear / Vercel |
| `brutalist_raw` | Tipo Massiva + Bordas | Balenciaga / Brutalismo |
| `organic_warm` | Papel + Serifas | Notion / Wellness / Craft |
| `data_narrative` | Gráficos Narrativos | NYT Graphics / Pudding |

---

## 🧩 8. Primitivos Narrativos (Primal Data)

Em vez de ícones, use os primitivos localizados em `core/primitives/`:

*   **`LivingCurve`**: Uma linha que respira e reage a ruído (noise), representando evolução.
*   **`NeuralGrid`**: Uma malha sutil de fundo que dá textura e escala técnica.
*   **`DataStream`**: Fluxos de pontos que simulam processamento de dados em tempo real.
*   **`StorageHex`**: Contêineres geométricos para representar nodos de informação.

---

## ⚖️ 9. Conclusão e Qualidade

branding não é apenas uma ferramenta de automação; é uma fôrma de excelência. Ele garante que, não importa quem o opere, o resultado final terá o peso visual e a autoridade de uma marca de elite.

**O invisível agora é visível.** 🏛️🎬💎
