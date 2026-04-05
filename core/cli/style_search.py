#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from core.runtime.style_retriever import search_style_packs


def cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Busca style packs por query semantica leve")
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    results = search_style_packs(args.query, limit=args.limit)
    if args.json:
        print(json.dumps({"query": args.query, "results": results}, indent=2, ensure_ascii=True))
        return 0

    print(f"Style search: {args.query}")
    for item in results:
        print(f"- {item['pack_id']}: score={item['score']} tags={','.join(item.get('tags', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
