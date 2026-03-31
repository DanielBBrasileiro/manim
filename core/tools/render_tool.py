import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from core.tools.fallback_artifact_renderer import (
    render_carousel_artifact,
    render_still_artifact,
    render_video_artifact,
)

ROOT = Path(__file__).resolve().parent.parent.parent
MANIM_SCENE_NAME = "EntropyDemo"
MANIM_SCRIPT_PATH = "scenes/cde_entropy_demo.py"
DEFAULT_RENDER_TIMEOUT = int(os.getenv("AIOX_REMOTION_CLI_TIMEOUT_SECONDS", "45"))
DEFAULT_DIRECT_TIMEOUT = int(os.getenv("AIOX_REMOTION_DIRECT_TIMEOUT_SECONDS", "30"))

LEGACY_OUTPUT_ALIASES = {
    "short_cinematic_vertical": "CinematicNarrative-v4",
    "linkedin_feed_4_5": "LinkedInStill-v4",
    "linkedin_carousel_square": "CarouselSlide-v4",
    "youtube_essay_16_9": "YouTubeEssay-v4",
    "youtube_thumbnail_16_9": "Thumbnail-v4",
}


def run_manim(scene_name: str, script_path: str) -> None:
    print(f"💎 [Manim Tool] Renderizando geometria de {scene_name}...")
    env = dict(os.environ, PYTHONPATH=str(ROOT))
    cmd = ["manim", "-f", "-qh", script_path, scene_name]
    subprocess.run(cmd, check=True, cwd=str(ROOT / "engines" / "manim"), env=env)


def bridge_engines(scene_name: str, script_path: str) -> None:
    script_name = Path(script_path).stem
    manim_output = (
        ROOT
        / "engines"
        / "manim"
        / "media"
        / "videos"
        / script_name
        / "1080p60"
        / f"{scene_name}.mp4"
    )
    remotion_public = ROOT / "engines" / "remotion" / "public" / "manim_base.mp4"
    if manim_output.exists():
        print(f"🌉 [Bridge Tool] Injetando {scene_name} no React...")
        os.makedirs(remotion_public.parent, exist_ok=True)
        shutil.copy(manim_output, remotion_public)


def _load_remotion_runner() -> str:
    return str(ROOT / "scripts" / "run_remotion_node.sh")


def _load_remotion_env(remotion_props: dict[str, Any] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    if remotion_props is not None:
        env["REMOTION_INPUT_PROPS_JSON"] = json.dumps(remotion_props)
    return env


def _run_remotion_command(command: str, composition: str, output_path: Path, remotion_props: dict[str, Any] | None) -> None:
    runner = _load_remotion_runner()
    env = _load_remotion_env(remotion_props)
    render_mode = os.getenv("AIOX_REMOTION_RENDER_MODE", "auto").strip().lower()
    cli_timeout = int(os.getenv("AIOX_REMOTION_CLI_TIMEOUT_SECONDS", str(DEFAULT_RENDER_TIMEOUT)))
    direct_timeout = int(os.getenv("AIOX_REMOTION_DIRECT_TIMEOUT_SECONDS", str(DEFAULT_DIRECT_TIMEOUT)))

    cli_cmd = [
        "/bin/zsh",
        "-lc",
        f"cd {ROOT / 'engines' / 'remotion'} && {runner} ./node_modules/.bin/remotion {command} src/index.tsx {composition} {output_path.as_posix()} --force",
    ]
    direct_cmd = [
        "/bin/bash",
        runner,
        str(ROOT / "scripts" / "remotion_direct.js"),
        command,
        composition,
        str(output_path),
    ]

    if render_mode == "direct":
        subprocess.run(direct_cmd, check=True, cwd=str(ROOT), env=env, timeout=direct_timeout)
    elif render_mode == "cli":
        subprocess.run(cli_cmd, check=True, cwd=str(ROOT), env=env, timeout=cli_timeout)
    else:
        try:
            subprocess.run(direct_cmd, check=True, cwd=str(ROOT), env=env, timeout=direct_timeout)
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            print("⚠️ [Remotion Tool] Renderer direto falhou. Tentando CLI...")
            subprocess.run(
                cli_cmd,
                check=True,
                cwd=str(ROOT),
                env=env,
                timeout=cli_timeout,
            )


def _validate_output(output_path: Path) -> None:
    if not output_path.exists():
        raise RuntimeError(f"Render final nao gerou arquivo: {output_path}")

    current_mtime = output_path.stat().st_mtime
    if output_path.stat().st_size == 0:
        raise RuntimeError(f"Render final criou arquivo vazio: {output_path}")
    if current_mtime <= 0:
        raise RuntimeError(f"Render final com timestamp invalido: {output_path}")


def run_remotion_video(
    composition: str,
    output_path: Path,
    remotion_props: dict[str, Any] | None = None,
) -> Path:
    print("🎬 [Remotion Tool] Compondo narrativa final...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    previous_mtime = output_path.stat().st_mtime if output_path.exists() else 0

    _run_remotion_command("render", composition, output_path, remotion_props)
    _validate_output(output_path)

    current_mtime = output_path.stat().st_mtime
    if current_mtime <= previous_mtime:
        raise RuntimeError(f"Render final nao atualizou o arquivo esperado: {output_path}")

    return output_path


def run_remotion_still(
    composition: str,
    output_path: Path,
    remotion_props: dict[str, Any] | None = None,
) -> Path:
    print("🖼️ [Remotion Tool] Compondo still premium...")
    still_output = output_path if output_path.suffix.lower() == ".png" else output_path.with_suffix(".png")
    still_output.parent.mkdir(parents=True, exist_ok=True)
    previous_mtime = still_output.stat().st_mtime if still_output.exists() else 0

    _run_remotion_command("still", composition, still_output, remotion_props)
    _validate_output(still_output)

    current_mtime = still_output.stat().st_mtime
    if current_mtime <= previous_mtime:
        raise RuntimeError(f"Still nao atualizou o arquivo esperado: {still_output}")

    return still_output


def _write_dynamic_data(
    plan: dict,
    artifact_plan: dict | None,
    render_manifest: dict | None,
    briefing: dict | None,
    quality_report: dict | None,
) -> None:
    dynamic_data_path = ROOT / "assets" / "brand" / "dynamic_data.json"
    dynamic_data_path.parent.mkdir(parents=True, exist_ok=True)

    entropy_package = dict((plan.get("interpretation") or {}))
    if "entropy" in plan:
        entropy_package["raw"] = plan["entropy"]

    payload = {
        "tech_plan": {
            "archetype": plan.get("archetype"),
            "entropy": entropy_package,
        },
        "design_overlay": {
            "aesthetic_family": plan.get("aesthetic_family"),
        },
        "timeline": plan.get("timeline", []),
        "llm_scene_plan": plan.get("llm_scene_plan"),
        "render_manifest": render_manifest or plan.get("render_manifest", {}),
        "artifact_plan": artifact_plan or plan.get("artifact_plan", {}),
        "briefing": briefing or {},
        "quality_report": quality_report or {},
    }

    with open(dynamic_data_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _load_style_packs(artifact_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    style_packs: dict[str, dict[str, Any]] = {}
    for pack_id in artifact_plan.get("style_pack_ids", []):
        if not str(pack_id).strip():
            continue
        pack_path = ROOT / "contracts" / "references" / f"{pack_id}.yaml"
        if not pack_path.exists():
            continue
        try:
            import yaml

            with open(pack_path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
            if isinstance(data, dict):
                style_packs[str(pack_id)] = data
        except Exception:
            continue
    return style_packs


def _target_kind(render_mode: str) -> str:
    return "still" if render_mode in {"still", "carousel"} else "composition"


def _target_uses_base_video(target: dict[str, Any]) -> bool:
    target_id = str(target.get("id", "")).strip()
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    return render_mode == "video" and target_id == "short_cinematic_vertical"


def _requires_manim_pass(targets: list[dict[str, Any]]) -> bool:
    return any(isinstance(target, dict) and _target_uses_base_video(target) for target in targets)


def _build_target_text_cues(target: dict[str, Any], artifact_plan: dict[str, Any], render_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    target_id = str(target.get("id", "")).strip()
    story_atoms = artifact_plan.get("story_atoms", {})

    if target_id == "linkedin_feed_4_5":
        return [
            {
                "act": "turbulence",
                "at_sec": 0.8,
                "text": str(story_atoms.get("thesis", "")),
                "position": "center_climax",
                "role": "statement",
                "weight": 460,
                "color_state": "default",
            },
            {
                "act": "resolution",
                "at_sec": 1.8,
                "text": str(story_atoms.get("resolve_word", "")),
                "position": "bottom_zone",
                "role": "resolve",
                "weight": 560,
                "color_state": "default",
            },
        ]

    if target_id == "youtube_thumbnail_16_9":
        return [
            {
                "act": "turbulence",
                "at_sec": 0.8,
                "text": str(story_atoms.get("thesis", "")),
                "position": "top_zone",
                "role": "whisper",
                "weight": 320,
                "color_state": "default",
            },
            {
                "act": "resolution",
                "at_sec": 1.5,
                "text": str(story_atoms.get("resolve_word", "")),
                "position": "center_climax",
                "role": "resolve",
                "weight": 620,
                "color_state": "default",
            },
        ]

    if target_id == "youtube_essay_16_9":
        chapters = target.get("chapters", [])
        if isinstance(chapters, list) and chapters:
            cues: list[dict[str, Any]] = []
            cursor = 2.0
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    continue
                cues.append(
                    {
                        "act": "turbulence",
                        "at_sec": round(cursor, 2),
                        "text": str(chapter.get("label", "")),
                        "position": "center_climax" if chapter.get("archetype") == "resolve" else "bottom_zone",
                        "role": "resolve" if chapter.get("archetype") == "resolve" else "statement",
                        "weight": 520 if chapter.get("archetype") == "resolve" else 360,
                        "color_state": "default",
                    }
                )
                cursor += float(chapter.get("seconds", 8) or 8)
            return cues

    render_inputs = (render_manifest.get("render_inputs") or {}).get(target_id, {})
    cues = render_inputs.get("text_cues") or render_manifest.get("text_cues") or []
    return [cue for cue in cues if isinstance(cue, dict)]


def _build_target_acts(target: dict[str, Any], render_manifest: dict[str, Any]) -> list[dict[str, Any]]:
    target_id = str(target.get("id", "")).strip()
    if target_id == "youtube_essay_16_9":
        chapters = target.get("chapters", [])
        if isinstance(chapters, list) and chapters:
            acts: list[dict[str, Any]] = []
            cursor = 0.0
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    continue
                seconds = float(chapter.get("seconds", 8) or 8)
                acts.append(
                    {
                        "id": str(chapter.get("archetype", "chapter")),
                        "name": str(chapter.get("archetype", "chapter")),
                        "start_sec": round(cursor, 2),
                        "end_sec": round(cursor + seconds, 2),
                        "text_cues": [
                            {
                                "text": str(chapter.get("label", "")),
                                "at_sec": round(cursor + 1.0, 2),
                                "position": "center_climax" if chapter.get("archetype") == "resolve" else "bottom_zone",
                                "role": "resolve" if chapter.get("archetype") == "resolve" else "statement",
                                "weight": 520 if chapter.get("archetype") == "resolve" else 360,
                            }
                        ],
                    }
                )
                cursor += seconds
            return acts

    render_inputs = (render_manifest.get("render_inputs") or {}).get(target_id, {})
    acts = render_inputs.get("acts") or render_manifest.get("acts") or []
    return [act for act in acts if isinstance(act, dict)]


def _build_target_props(target: dict[str, Any], artifact_plan: dict[str, Any], render_manifest: dict[str, Any]) -> dict[str, Any]:
    target_id = str(target.get("id") or "target").strip()
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    target_kind = _target_kind(render_mode)
    story_atoms = artifact_plan.get("story_atoms", {})
    render_inputs = (render_manifest.get("render_inputs") or {}).get(target_id, {})
    target_duration = float(target.get("duration_sec", render_inputs.get("duration", render_manifest.get("duration", 12))) or 12.0)
    fps = int(target.get("fps", render_inputs.get("fps", render_manifest.get("fps", 30))) or 30)
    text_cues = _build_target_text_cues(target, artifact_plan, render_manifest)
    acts = _build_target_acts(target, render_manifest)
    style_packs = _load_style_packs(artifact_plan)

    manifest = {
        **render_manifest,
        "target": target_id,
        "targetId": target_id,
        "targetKind": target_kind,
        "duration": target_duration,
        "duration_in_frames": int(round(target_duration * fps)),
        "fps": fps,
        "layout": target.get("layout", render_inputs.get("layout", render_manifest.get("layout", {}))),
        "textCues": text_cues,
        "text_cues": text_cues,
        "acts": acts,
        "style_pack_ids": artifact_plan.get("style_pack_ids", []),
        "style_packs": style_packs,
        "story_atoms": story_atoms,
        "quality_constraints": artifact_plan.get("quality_constraints", {}),
        "summary": target.get("summary"),
        "beats": target.get("beats", []),
        "slides": target.get("slides", []),
        "chapters": target.get("chapters", []),
        "narrative": {
            "acts": acts,
            "resolveWord": story_atoms.get("resolve_word"),
        },
        "audio": {
            **(render_manifest.get("audio") or {}),
            "enabled": bool(_target_uses_base_video(target)),
        },
    }
    if not _target_uses_base_video(target):
        manifest["videoSrc"] = None
        manifest["video_src"] = None

    if target_kind == "still":
        manifest["frameOverride"] = target.get("still_frame")
        manifest["stillFrame"] = target.get("still_frame")

    return {
        "target": target_id,
        "targetId": target_id,
        "targetKind": target_kind,
        "frameOverride": target.get("still_frame") if target_kind == "still" else None,
        "resolveWord": story_atoms.get("resolve_word"),
        "renderManifest": manifest,
    }


def _target_output_path(target: dict[str, Any]) -> Path:
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    target_id = str(target.get("id", "target")).strip() or "target"
    if render_mode == "still":
        return ROOT / "output" / "stills" / f"{target_id}.png"
    if render_mode == "carousel":
        return ROOT / "output" / "carousel" / target_id
    return ROOT / "output" / "renders" / f"{target_id}.mp4"


def _alias_output_path(target: dict[str, Any], canonical_output: Path) -> Path | None:
    legacy_name = str(target.get("legacy_composition", "")).strip()
    if not legacy_name:
        composition_name = str(target.get("composition", "")).strip()
        target_id = str(target.get("id", "")).strip()
        if composition_name and composition_name != target_id:
            legacy_name = composition_name
    if not legacy_name:
        legacy_name = LEGACY_OUTPUT_ALIASES.get(str(target.get("id", "")).strip(), "")
    if not legacy_name:
        return None

    if canonical_output.suffix.lower() == ".png":
        return canonical_output.with_name(f"{legacy_name}.png")
    if canonical_output.is_dir():
        return canonical_output.parent / legacy_name
    return canonical_output.with_name(f"{legacy_name}.mp4")


def _copy_alias_output(canonical_output: Path, alias_output: Path | None) -> None:
    if alias_output is None:
        return

    alias_output.parent.mkdir(parents=True, exist_ok=True)
    if canonical_output.is_dir():
        if alias_output.exists():
            if alias_output.is_dir():
                shutil.rmtree(alias_output)
            else:
                alias_output.unlink()
        shutil.copytree(canonical_output, alias_output)
        return

    if alias_output.exists() and alias_output.is_dir():
        shutil.rmtree(alias_output)
    shutil.copy2(canonical_output, alias_output)


def _slide_to_props(
    artifact_plan: dict,
    target: dict[str, Any],
    slide: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    story_atoms = artifact_plan.get("story_atoms", {})
    slide_title = str(slide.get("title") or slide.get("archetype") or f"slide_{index + 1}")
    text_blocks = slide.get("text_blocks", [])
    cues = []
    for cue_index, text in enumerate(text_blocks):
        if not text:
            continue
        cues.append(
            {
                "act": "turbulence",
                "at_sec": round(0.8 + cue_index * 0.75, 3),
                "text": str(text),
                "position": "center_climax" if cue_index == 0 else "bottom_zone",
                "role": "statement" if cue_index == 0 else "brand",
                "weight": 420 if cue_index == 0 else 320,
                "color_state": "default",
            }
        )

    if not cues:
        cues = [
            {
                "act": "turbulence",
                "at_sec": 0.9,
                "text": slide_title,
                "position": "center_climax",
                "role": "statement",
                "weight": 420,
                "color_state": "default",
            }
        ]

    return {
        "target": target.get("id"),
        "targetId": target.get("id"),
        "targetKind": "still",
        "frameOverride": target.get("still_frame"),
        "resolveWord": story_atoms.get("resolve_word"),
        "renderManifest": {
            "target": target.get("id"),
            "targetId": target.get("id"),
            "targetKind": "still",
            "frameOverride": target.get("still_frame"),
            "stillFrame": target.get("still_frame"),
            "videoSrc": None,
            "video_src": None,
            "audio": {"enabled": False},
            "textCues": cues,
            "text_cues": cues,
            "acts": [],
            "narrative": {
                "acts": [],
                "resolveWord": story_atoms.get("resolve_word"),
            },
            "slide": {
                "index": index,
                "title": slide_title,
                "archetype": slide.get("archetype"),
            },
        },
    }


def _fallback_target_render(
    target: dict[str, Any],
    artifact_plan: dict[str, Any],
    canonical_output: Path,
) -> dict[str, Any]:
    target_id = str(target.get("id", "target")).strip() or "target"
    render_mode = str(target.get("render_mode", "video")).strip().lower()
    manim_base = ROOT / "engines" / "remotion" / "public" / "manim_base.mp4"

    if render_mode == "still":
        output = render_still_artifact(target, artifact_plan, canonical_output)
        return {"target": target_id, "mode": render_mode, "output": str(output), "fallback": True}

    if render_mode == "carousel":
        slides = render_carousel_artifact(target, artifact_plan, canonical_output)
        return {
            "target": target_id,
            "mode": render_mode,
            "output": str(canonical_output),
            "slides": [str(path) for path in slides],
            "fallback": True,
        }

    output = render_video_artifact(
        target,
        artifact_plan,
        canonical_output,
        source_video=manim_base if target_id == "short_cinematic_vertical" and manim_base.exists() else None,
    )
    return {"target": target_id, "mode": render_mode, "output": str(output), "fallback": True}


def render_pipeline(
    plan: dict,
    artifact_plan: dict | None = None,
    briefing: dict | None = None,
    quality_report: dict | None = None,
):
    """Encapsula a mecânica dura do antigo Orchestrator."""
    artifact_plan = artifact_plan or plan.get("artifact_plan") or {}
    render_manifest = plan.get("render_manifest") or {}

    if isinstance(quality_report, dict):
        errors = quality_report.get("errors") or []
        if errors:
            print(f"❌ [Render Tool] Quality gate bloqueou o render: {', '.join(errors)}")
            return {"ok": False, "errors": errors}

    _write_dynamic_data(plan, artifact_plan, render_manifest, briefing, quality_report)

    targets = artifact_plan.get("targets", []) if isinstance(artifact_plan, dict) else []
    if not targets:
        primary_target = artifact_plan.get("primary_target") if isinstance(artifact_plan, dict) else None
        if isinstance(primary_target, dict):
            targets = [primary_target]
        elif isinstance(render_manifest, dict) and isinstance(render_manifest.get("primary_target"), dict):
            targets = [render_manifest["primary_target"]]

    if _requires_manim_pass(targets):
        try:
            run_manim(MANIM_SCENE_NAME, MANIM_SCRIPT_PATH)
            bridge_engines(MANIM_SCENE_NAME, MANIM_SCRIPT_PATH)
        except subprocess.CalledProcessError as error:
            print(f"❌ [Render Tool] Falha no pre-render do Manim: {error}")
            return {"ok": False, "errors": [str(error)]}
    else:
        print("🪶 [Render Tool] Nenhum target exige base de video. Pulando Manim.")

    outputs: list[dict[str, Any]] = []
    remotion_unavailable_reason: str | None = None

    for target in targets:
        if not isinstance(target, dict):
            continue

        target_id = str(target.get("id") or target.get("composition") or MANIM_SCENE_NAME).strip()
        composition = target_id
        render_mode = str(target.get("render_mode", "video")).strip().lower()
        remotion_props = _build_target_props(target, artifact_plan, render_manifest)

        canonical_output = _target_output_path(target)
        alias_output = _alias_output_path(target, canonical_output)

        if remotion_unavailable_reason is not None:
            print(
                f"🛟 [Render Tool] Usando fallback direto para '{target_id}' "
                f"após indisponibilidade do Remotion: {remotion_unavailable_reason}"
            )
            try:
                fallback_output = _fallback_target_render(target, artifact_plan, canonical_output)
                _copy_alias_output(canonical_output, alias_output)
                fallback_output["alias_output"] = str(alias_output) if alias_output else None
                fallback_output["remotion_skipped"] = True
                outputs.append(fallback_output)
                continue
            except Exception as fallback_error:
                print(f"❌ [Render Tool] Falha ao renderizar target '{target_id}': {fallback_error}")
                return {"ok": False, "errors": [str(fallback_error)], "outputs": outputs}

        try:
            if render_mode == "still":
                output = run_remotion_still(composition, canonical_output, remotion_props=remotion_props)
            elif render_mode == "carousel":
                slides = target.get("slides", [])
                if not isinstance(slides, list) or not slides:
                    slides = [
                        {
                            "archetype": "cover",
                            "title": target.get("label", target_id),
                            "text_blocks": [artifact_plan.get("story_atoms", {}).get("thesis")],
                        }
                    ]

                canonical_output.mkdir(parents=True, exist_ok=True)
                slide_outputs: list[str] = []
                for index, slide in enumerate(slides, start=1):
                    slide_props = _slide_to_props(artifact_plan, target, slide if isinstance(slide, dict) else {}, index - 1)
                    slide_path = canonical_output / f"slide_{index:02d}.png"
                    rendered_slide = run_remotion_still(composition, slide_path, remotion_props=slide_props)
                    slide_outputs.append(str(rendered_slide))

                output = canonical_output
                _copy_alias_output(output, alias_output)
                outputs.append(
                    {
                        "target": target_id,
                        "mode": render_mode,
                        "composition": composition,
                        "output": str(output),
                        "slides": slide_outputs,
                    }
                )
                continue
            else:
                output = run_remotion_video(composition, canonical_output, remotion_props=remotion_props)

            _copy_alias_output(output, alias_output)
            outputs.append(
                {
                    "target": target_id,
                    "mode": render_mode,
                    "composition": composition,
                    "output": str(output),
                    "alias_output": str(alias_output) if alias_output else None,
                }
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, RuntimeError) as error:
            print(f"⚠️ [Render Tool] Remotion indisponivel para '{target_id}': {error}")
            remotion_unavailable_reason = str(error)
            try:
                fallback_output = _fallback_target_render(target, artifact_plan, canonical_output)
                _copy_alias_output(canonical_output, alias_output)
                fallback_output["alias_output"] = str(alias_output) if alias_output else None
                outputs.append(fallback_output)
            except Exception as fallback_error:
                print(f"❌ [Render Tool] Falha ao renderizar target '{target_id}': {fallback_error}")
                return {"ok": False, "errors": [str(fallback_error)], "outputs": outputs}

    return {"ok": True, "outputs": outputs}
