#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _read_manifest(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in {".yaml", ".yml"}:
        try:
            import yaml  # type: ignore
            return yaml.safe_load(text) or {}
        except Exception as e:
            raise SystemExit(f"YAML manifest requested but PyYAML not installed: {e}")
    return json.loads(text)


def _run(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=check, cwd=str(cwd) if cwd else None)


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def fetch_youtube_raw(playlist_url: str) -> Dict[str, Any]:
    try:
        proc = subprocess.run(["yt-dlp", "--dump-single-json", "--flat-playlist", playlist_url], check=True, capture_output=True, text=True, encoding="utf-8")
        return json.loads(proc.stdout)
    except FileNotFoundError:
        raise SystemExit("yt-dlp not found on PATH. Install yt-dlp or add raw_json to manifest.")


def process_youtube_entry(entry: Dict[str, Any]) -> Optional[Path]:
    course_id = entry.get("course_id") or "youtube_course"
    playlist_url = entry.get("playlist_url")
    raw_json = entry.get("raw_json")
    normalized_out = Path(entry.get("normalized_out") or f"RAWDATA/RawYT/{course_id}.json")
    # Write YouTube course datasets under a dedicated directory to avoid confusion
    output_zip = Path(entry.get("output_zip") or f"datasets/youtube_curriculum_datasets/{course_id}.zip")
    profile = entry.get("profile") or "youtube_series"
    videos_per_step = int(entry.get("videos_per_step") or 1)

    if playlist_url:
        payload = fetch_youtube_raw(playlist_url)
        ensure_dir(normalized_out.parent)
        raw_path = normalized_out.parent / f"{course_id}.raw.json"
        raw_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        _run([sys.executable, "-m", "pipeline.curriculum.normalize_youtube_playlist", "--input", str(raw_path), "--output", str(normalized_out), "--course-id", course_id, "--profile", profile, "--videos-per-step", str(videos_per_step)])
    elif raw_json:
        raw_path = Path(raw_json)
        _run([sys.executable, "-m", "pipeline.curriculum.normalize_youtube_playlist", "--input", str(raw_path), "--output", str(normalized_out), "--course-id", course_id, "--profile", profile, "--videos-per-step", str(videos_per_step)])
    elif normalized_out.exists():
        print(f"[yt] Using existing normalized: {normalized_out}")
    else:
        print(f"[yt] Skip {course_id}: no playlist_url/raw_json/normalized provided")
        return None

    ensure_dir(output_zip.parent)
    _run([sys.executable, "-m", "pipeline.curriculum.build_youtube", "--input-json", str(normalized_out), "--output-zip", str(output_zip), "--profile", profile, "--step-semantics", entry.get("step_semantics") or "week"])
    return output_zip


def _merge_zips_into(zip_paths: List[Path], dest_dir: Path) -> None:
    """Copy the provided zip files into dest_dir for unified reporting.
    Existing files with identical names are left as-is.
    """
    ensure_dir(dest_dir)
    for zp in zip_paths:
        if zp is None:
            continue
        target = dest_dir / zp.name
        try:
            if not target.exists():
                target.write_bytes(zp.read_bytes())
        except Exception as e:
            print(f"[merge] Skip {zp} -> {target}: {e}")


def process_mit_group(entry: Dict[str, Any]) -> None:
    if entry.get("rebuild"):
        _run([sys.executable, "-m", "pipeline.curriculum.build_mit"])  # builds into default dir
    else:
        print("[mit] Using existing datasets; set rebuild=true to rebuild")


def build_conversation_datasets(clean_dir: Path, zip_dir: Path, window_size: int, prefix: str) -> None:
    ensure_dir(zip_dir)
    _run([sys.executable, "-m", "pipeline.conversation.build_datasets", "--input-dir", str(clean_dir), "--output-dir", str(zip_dir), "--window-size", str(window_size), "--prefix", prefix])


def process_conversation(entry: Dict[str, Any], default_zip_dir: Path) -> Path:
    raw_dir = Path(entry.get("raw_dir") or "RawConversation")
    # Clean transcripts are intermediate inputs; keep under RAWDATA
    clean_out = Path(entry.get("clean_out") or "RAWDATA/ConversationClean")
    # Metrics/reports remain under reports; align name with other *_insight_fs outputs
    metrics_out = Path(entry.get("metrics_out") or "reports/conversation_insight_fs")
    window_size = int(entry.get("window_size") or 6)
    prefix = entry.get("prefix") or "conversation"
    build_zip_dir = Path(entry.get("zip_dir") or default_zip_dir)

    ensure_dir(clean_out); ensure_dir(metrics_out)
    _run([sys.executable, "-m", "pipeline.conversation.scrub_transcripts", "--input-dir", str(raw_dir), "--out-dir", str(clean_out)])
    build_conversation_datasets(clean_out, build_zip_dir, window_size, prefix)
    _run([sys.executable, "-m", "pipeline.conversation.run_health", "--input-dir", str(clean_out), "--out-dir", str(metrics_out), "--window", str(window_size)])
    return metrics_out


def run_core_report(zip_dir: Path, fs_dir: Path, out_dir: Path, reporter_name: str, heads: List[str], compute_spread: bool, compute_locality: bool):
    ensure_dir(out_dir)
    cmd = [sys.executable, "-m", "pipeline.curriculum.run_zipless", "--zip-dir", str(zip_dir), "--fs-dir", str(fs_dir), "--out-dir", str(out_dir), "--heads", *heads, "--reporter", reporter_name]
    if compute_spread: cmd.append("--compute-spread")
    if compute_locality: cmd.append("--compute-locality")
    _run(cmd)


def run_zipless_curriculum(zip_dir: Path, fs_dir: Path, insights_out: Path, dynamics_out: Path, heads: List[str], compute_spread: bool, compute_locality: bool) -> None:
    run_core_report(zip_dir, fs_dir, insights_out, "insight", heads, compute_spread, compute_locality)
    run_core_report(zip_dir, fs_dir, dynamics_out, "curriculum_dynamics", heads, compute_spread, compute_locality)


def _move_conversation_dynamics(src_dir: Path, dst_dir: Path) -> None:
    """Move any conversation_* dynamics files out of curriculum dynamics into a dedicated folder."""
    ensure_dir(dst_dir)
    for fp in src_dir.glob("conversation_*_curriculum_dynamics.json"):
        target = dst_dir / fp.name
        try:
            fp.replace(target)
        except Exception as e:
            print(f"[move] Unable to move {fp} -> {target}: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Manifest-driven orchestrator for curriculum + conversation")
    ap.add_argument("--manifest", required=True, help="Path to JSON/YAML manifest")
    args = ap.parse_args()

    manifest = _read_manifest(Path(args.manifest))

    curriculum_cfg = manifest.get("curriculum") or {}
    zip_dir = Path(curriculum_cfg.get("zip_dir") or "datasets/mit_curriculum_datasets")
    fs_dir = Path(curriculum_cfg.get("fs_dir") or "datasets/mit_curriculum_fs")
    insights_out = Path(curriculum_cfg.get("insights_out") or "reports/mit_curriculum_insights_fs")
    dynamics_out = Path(curriculum_cfg.get("dynamics_out") or "reports/mit_curriculum_dynamics_fs")
    curriculum_insight_out = Path(curriculum_cfg.get("curriculum_insight_out") or "reports/curriculum_insight_fs")
    conversation_insight_out = Path(curriculum_cfg.get("conversation_insight_out") or "reports/conversation_insight_fs")
    conversation_dynamics_out = Path(curriculum_cfg.get("conversation_dynamics_out") or "reports/conversation_dynamics_fs")
    heads = curriculum_cfg.get("heads") or ["monte_carlo", "forecast", "regime_change"]
    compute_spread = bool(curriculum_cfg.get("compute_spread", True))
    compute_locality = bool(curriculum_cfg.get("compute_locality", True))

    yt_built: List[Path] = []
    for yt in manifest.get("youtube", []) or []:
        zp = process_youtube_entry(yt)
        if zp is not None:
            yt_built.append(zp)

    if manifest.get("mit"):
        process_mit_group(manifest["mit"])

    if manifest.get("conversation"):
        process_conversation(manifest["conversation"], zip_dir)

    # Ensure YouTube datasets are visible to reporting by merging into the main zip_dir
    try:
        _merge_zips_into(yt_built, zip_dir)
    except Exception as e:
        print(f"[merge] Unable to merge YouTube zips into {zip_dir}: {e}")

    run_zipless_curriculum(zip_dir, fs_dir, insights_out, dynamics_out, heads, compute_spread, compute_locality)
    # Split conversation dynamics into its own folder
    try:
        _move_conversation_dynamics(dynamics_out, conversation_dynamics_out)
    except Exception as e:
        print(f"[split] Unable to split conversation dynamics: {e}")
    run_core_report(zip_dir, fs_dir, curriculum_insight_out, "curriculum_insight", heads, compute_spread, compute_locality)
    run_core_report(zip_dir, fs_dir, conversation_insight_out, "conversation_insight", heads, compute_spread, compute_locality)

    # Build a combined comprehensive analysis (curriculum + conversation)
    try:
        _run([sys.executable, "-m", "pipeline.reporting.combine_reports",
              "--curriculum-insights", str(insights_out),
              "--curriculum-dynamics", str(dynamics_out),
              "--conversation-insights", str(conversation_insight_out),
              "--conversation-dynamics", str(conversation_dynamics_out),
              "--out-dir", "reports/comprehensive" ])
    except Exception as e:
        print(f"[combine] Failed to write comprehensive report: {e}")

    print("\nOrchestration complete.")


if __name__ == "__main__":
    main()
