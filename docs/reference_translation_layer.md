# Reference Translation Layer

## Purpose

Translate site snapshots into AIOX-native design intelligence.

This layer is intentionally:
- ZIP-first
- heuristic and structured
- compatible with `contracts/references/`

It is **not** a website copier and does not try to reconstruct browser runtime behavior.

## Supported inputs

- Primary: website ZIP snapshot
- Optional: screenshots of key sections/pages
- Optional: operator notes about what to emulate or avoid

## Command

```bash
python3 aiox.py reference path/to/site_snapshot.zip --screenshot path/to/hero.png --notes "like the restraint, not the product UI"
```

URL ingestion remains supported:

```bash
python3 aiox.py reference https://stripe.com
```

## Output

The ingest writes YAML + JSON under `contracts/references/` with:
- reference analysis
- design DNA synthesis
- AIOX translation hints
- compact contract-compatible fields

## Translation intent

The output should help AIOX reason about:
- what to emulate
- what to avoid copying literally
- what maps into:
  - `style_pack_hint`
  - `typography_system_hint`
  - `still_family_hint`
  - `motion_grammar_hint`

## Current limits

- ZIP analysis reads HTML/CSS/JS/assets heuristically
- screenshot analysis is optional and uses existing fast visual metrics
- no browser replay, no DOM execution, no full animation reconstruction
