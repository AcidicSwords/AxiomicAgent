# Curriculum Pipeline (MIT + YouTube)

This document traces the end-to-end path from raw sources to reports.

## 1) Sources
- MIT OCW HTML + assets (extracted to normalized JSON by `extract_mit_curriculum_html.py`).
- YouTube playlist metadata + transcripts via `scripts/collect_youtube_course.py` using `yt-dlp` and `youtube_transcript_api`.

## 2) Builders (`builders/curriculum`)
- Normalize items (course sections/lectures for MIT; episodes for YT).
- Create nodes.csv and edges_obs.csv with per-step edges.
- YouTube augmentation:
  - Parse transcripts (`core/transcripts.py`), coarsen segments (~30s), extract content keywords.
  - Add segment + concept nodes; edges: video_segment, segment_seq, segment_concept.
  - Thin cross-step edges: shared concept → next video; title-similarity video→video.
  - Ensure non-empty steps by adding a self-edge if needed.

## 3) Adapter (`adapters/curriculum`)
- Preprocess and filter edges/nodes:
  - Stoplists + regex patterns for media/navigation.
  - Type weights for concept/assessment/reading/meta/…
- Summarize step features:
  - quality(q), stability, top_nodes, fractions, engagement.
  - continuity (concept Jaccard overlap vs previous step).
  - YouTube: light q normalization; top_nodes filtering tuned for content phrases.

## 4) Core (`core`)
- Compute signals (`core/signals.py`): q, ted, stability, ted_delta; optional spread/locality.
- Heads (`core/mc_head.py`, `core/forecast_head.py`, `core/regime_head.py`): robustness, trend slopes, change points.
- Engine (`core/engine.py`): orchestrate steps, attach head outputs, pass to reporters.

## 5) Reporters (`reporters`)
- Insight (`insight.py`): per-course aggregates + per-step summaries.
- Dynamics (`curriculum_dynamics.py`): per-step traces + phases, guidance, uncertainty, continuity.

## 6) Exports (`scripts`)
- `run_mit_curriculum_showcase.py`: regenerate insights/dynamics for all datasets.
- `export_curriculum_metrics.py`: write CSV with key metrics across all courses.
- `export_curriculum_dashboard.py`: emit Markdown/HTML dashboards from CSV.
- `export_top_pivots.py`: emit top ΔTED steps with clean titles.

## File Layout Summary
- datasets/mit_curriculum_datasets/*.zip — canonical course datasets.
- reports/yt_insights/* — per-course insight JSON + comparison.
- reports/yt_dynamics/* — per-course dynamics JSON + comparison.
- reports/comparisons/* — CSV/MD/HTML summaries + top pivots.

## Notes & Conventions
- YouTube spread ≈ 0.0 (intra-step concept graphs); continuity captures cross-step glue.
- MIT spread varies: high for cross-linked courses (e.g., 8.01/9.00), low for modular imports.
- Step 1 often shows a ΔTED spike (expected baseline vs empty history).

