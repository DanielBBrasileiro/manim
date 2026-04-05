#!/usr/bin/env python3
"""Minimal MCP stdio server exposing AIOX pipeline tools.

Usage (add to Claude Code):
    claude mcp add aiox-studio -- python3 /path/to/manim/core/cli/mcp_server.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "render_still",
        "description": "Render a Remotion composition as a PNG still image.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "composition": {
                    "type": "string",
                    "description": "Composition ID (e.g. linkedin-feed-4-5, youtube-thumbnail-16-9)",
                },
                "output_path": {
                    "type": "string",
                    "description": "Absolute output path for the PNG. Defaults to output/stills/<composition>.png",
                },
                "props": {
                    "type": "object",
                    "description": "Input props JSON passed directly to the composition",
                },
            },
            "required": ["composition"],
        },
    },
    {
        "name": "compile_seed",
        "description": "Compile a creative seed phrase into a full AIOX artifact plan and optionally render.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "seed": {
                    "type": "string",
                    "description": "Text seed / creative intent to compile",
                },
                "auto_render": {
                    "type": "boolean",
                    "description": "Trigger the render pipeline after compilation (default: false)",
                },
            },
            "required": ["seed"],
        },
    },
    {
        "name": "doctor_check",
        "description": "Run AIOX system diagnostics and return a full health report including models, bundle status, and registry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "warm": {
                    "type": "boolean",
                    "description": "Trigger background bundle warm if bundle is cold (default: false)",
                },
            },
        },
    },
    {
        "name": "list_targets",
        "description": "List all available render targets, style packs, and quality gates from the capability registry.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]

# ── Tool handlers ─────────────────────────────────────────────────────────────

def _handle_render_still(args: dict) -> str:
    from core.tools.render_tool import run_remotion_still

    composition = str(args.get("composition", "")).strip()
    if not composition:
        return json.dumps({"error": "composition is required"})

    raw_output = args.get("output_path")
    out = Path(raw_output) if raw_output else ROOT / "output" / "stills" / f"{composition}.png"
    props = args.get("props") or None

    try:
        result = run_remotion_still(composition, out, remotion_props=props)
        return json.dumps({"ok": True, "output": str(result), "size_bytes": result.stat().st_size})
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def _handle_compile_seed(args: dict) -> str:
    seed = str(args.get("seed", "")).strip()
    if not seed:
        return json.dumps({"error": "seed is required"})

    auto_render = bool(args.get("auto_render", False))
    try:
        from core.compiler.creative_compiler import CreativeCompiler

        compiler = CreativeCompiler()
        result = compiler.compile(seed)
        if auto_render and isinstance(result, dict):
            from core.tools.render_tool import render_pipeline

            render_out = render_pipeline(result)
            result["render"] = render_out
        return json.dumps(result, ensure_ascii=False, default=str)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def _handle_doctor_check(args: dict) -> str:
    warm = bool(args.get("warm", False))
    try:
        from core.cli.doctor import _trigger_background_warm, collect_doctor_report

        report = collect_doctor_report()
        if warm and report.get("checks", {}).get("remotion_cli", {}).get("ok"):
            _trigger_background_warm()
            report["bundle_warm_triggered"] = True
        return json.dumps(report, ensure_ascii=True)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def _handle_list_targets(args: dict) -> str:
    try:
        from core.runtime.capability_registry import build_capability_registry

        registry = build_capability_registry()
        return json.dumps(
            {
                "targets": [
                    t.__dict__ if hasattr(t, "__dict__") else str(t) for t in registry.targets
                ],
                "style_packs": registry.style_packs,
                "quality_gates": registry.quality_gates,
                "profiles": registry.profiles,
            },
            ensure_ascii=False,
            default=str,
        )
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


HANDLERS: dict[str, object] = {
    "render_still": _handle_render_still,
    "compile_seed": _handle_compile_seed,
    "doctor_check": _handle_doctor_check,
    "list_targets": _handle_list_targets,
}

# ── JSON-RPC / MCP wire protocol ──────────────────────────────────────────────


def _read_message() -> dict | None:
    """Read a Content-Length framed JSON-RPC message from stdin."""
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        stripped = line.rstrip(b"\r\n")
        if not stripped:
            break
        if b":" in stripped:
            key, _, value = stripped.partition(b":")
            headers[key.strip().lower().decode()] = value.strip().decode()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None

    raw = sys.stdin.buffer.read(length)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def _write_message(payload: dict) -> None:
    """Write a Content-Length framed JSON-RPC message to stdout."""
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii")
    sys.stdout.buffer.write(header + body)
    sys.stdout.buffer.flush()


def _ok(req_id, result: object) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _err(req_id, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _dispatch(message: dict) -> dict | None:
    method = message.get("method", "")
    req_id = message.get("id")
    params = message.get("params") or {}

    # Notifications have no id — do not reply
    if req_id is None:
        return None

    if method == "initialize":
        return _ok(req_id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "aiox-studio", "version": "1.0.0"},
        })

    if method == "tools/list":
        return _ok(req_id, {"tools": TOOLS})

    if method == "tools/call":
        tool_name = params.get("name", "")
        tool_args = params.get("arguments") or {}
        handler = HANDLERS.get(tool_name)
        if handler is None:
            return _err(req_id, -32601, f"Unknown tool: {tool_name}")
        try:
            content = handler(tool_args)  # type: ignore[operator]
            return _ok(req_id, {
                "content": [{"type": "text", "text": content}],
                "isError": False,
            })
        except Exception as exc:
            return _ok(req_id, {
                "content": [{"type": "text", "text": json.dumps({"error": str(exc)})}],
                "isError": True,
            })

    return _err(req_id, -32601, f"Method not found: {method}")


def serve() -> None:
    while True:
        message = _read_message()
        if message is None:
            break
        reply = _dispatch(message)
        if reply is not None:
            _write_message(reply)


if __name__ == "__main__":
    serve()
