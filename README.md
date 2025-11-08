# Axiomic Curriculum Engine

This repository contains a lightweight graph engine plus adapters/reporters for replaying
curriculum-style datasets (MIT OCW, YouTube playlists, etc.).  It now supports:

* Rich MIT curriculum extraction/builders (STEM, psych/humanities, lit/essay profiles)
* Signal heads for forecast/uncertainty/regime-change analysis
* Insight and curriculum-focused reporters suitable for human review or LLM tools

## Project Layout

```
adapters/      # Streams and preprocessors (curriculum_stream, conversation, ...)
builders/      # Dataset builders (curriculum MIT OCW, research_learning, ...)
configs/       # Dataset configs, core defaults
core/          # Engine, policies, signal heads, state tracking
reporters/     # Report generators (insight, curriculum_dynamics)
scripts/       # CLIs for extraction/build/build+report
tests/         # Pytest regression suite
reports/       # Generated outputs (insight + curriculum_dynamics JSON)
```

## Setup

1. Create a virtual environment (Python 3.10+ recommended) and install deps:

   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt  # if present
   ```

2. Place raw MIT OCW zips under `RawOCW/` (see filenames in `scripts/extract_mit_curriculum_html.py`).

3. Run the extractor/builder/test pipeline:

   ```bash
   # Extract normalized JSON for every course (profile overrides built into script)
   python -m scripts.extract_mit_curriculum_html --raw-root RawOCW --output-dir datasets/raw_mit_curriculum --profile stem

   # Rebuild zipped datasets (writes to datasets/mit_curriculum_datasets)
   python -m scripts.build_mit_curriculum_datasets

   # Run the showcase (engine + reporter) across all datasets
   python -m scripts.run_mit_curriculum_showcase \
       --compute-spread --compute-locality \
       --heads monte_carlo forecast regime_change \
       --reporter insight \
       --out-dir reports/mit_curriculum_insights
   ```

## Signal Heads

Heads are pluggable analyzers that receive each step and emit extra signals.
Enable them via `core_config["heads"]` or the showcase CLI `--heads` flag.

| Head            | Purpose                                             | Config Keys                           |
|-----------------|-----------------------------------------------------|---------------------------------------|
| `monte_carlo`   | robustness/uncertainty for q & TED                  | `monte_carlo.num_samples`, `edge_dropout`, `weight_jitter` |
| `forecast`      | trends + next-step type prediction                  | `forecast.window_size`                |
| `regime_change` | windowed change-point detection / phase boundaries | `regime_change.window`, `threshold`   |

Example `core_config` fragment:

```python
core_cfg = {
    "capacity": {"max_edges": 400},
    "heads": ["monte_carlo", "forecast", "regime_change"],
    "monte_carlo": {"num_samples": 32, "edge_dropout": 0.1, "weight_jitter": 0.1},
    "forecast": {"window_size": 3},
    "regime_change": {"window": 3, "threshold": 0.25},
}
```

## Reporters

Two reporters are available (`--reporter` flag in showcase script):

| Reporter              | Output Highlights                                                                                   |
|-----------------------|-----------------------------------------------------------------------------------------------------|
| `insight` (default)   | Classic per-step commentary, aggregates (avg_q/TED/spread), recommendations                         |
| `curriculum_dynamics` | Deep per-step log + course-level dynamics (trend slopes, phase segmentation, uncertainty ranking)  |

Example to generate dynamics reports:

```bash
python -m scripts.run_mit_curriculum_showcase \
  --reporter curriculum_dynamics \
  --heads monte_carlo forecast regime_change \
  --compute-spread --compute-locality \
  --out-dir reports/mit_curriculum_dynamics
```

Each report JSON includes `head_summaries` (from the signal heads) and reporter-specific sections.
These files are designed to be consumed by LLM tooling or dashboard layers.

## YouTube Curriculum Pipeline

The YouTube ingest flow mirrors the MIT pipeline but starts from playlist metadata:

1. Dump a playlist using `yt-dlp --dump-single-json --flat-playlist` (or the YouTube Data API) into `RawYT/<playlist>.raw.json`.
2. Normalize it:

   ```bash
   python -m scripts.normalize_youtube_playlist \
     --input RawYT/essence_linear_algebra.raw.json \
     --output datasets/youtube_raw/essence_linear_algebra.json \
     --course-id essence_linear_algebra \
     --videos-per-step 1
   ```

3. Build a dataset zip (reuses the curriculum builder):

   ```bash
   python -m scripts.build_youtube_curriculum \
     --input-json datasets/youtube_raw/essence_linear_algebra.json \
     --output-zip datasets/mit_curriculum_datasets/essence_linear_algebra.zip \
     --profile youtube_series \
     --step-semantics week
   ```

4. Run the showcase with signal heads + the desired reporter (insight or curriculum_dynamics).

The resulting dataset zips share the same structure as the MIT files, so the existing adapters,
signal heads, and reporters work without modification.

## Testing

Run the full suite (covers extractors, builders, signal heads, reporters, engine regression):

```bash
.\.venv\Scripts\python.exe -m pytest
```

Regression fixtures live under `tests/fixtures/`.  The suite now contains 22 tests guarding the curriculum pipeline.

## Useful Scripts

| Script                               | Description                                                    |
|--------------------------------------|----------------------------------------------------------------|
| `scripts/extract_mit_curriculum_html.py` | Parses RawOCW zips into normalized JSON per course            |
| `scripts/build_mit_curriculum_datasets.py` | Converts normalized JSON into canonical dataset zips         |
| `scripts/run_mit_curriculum_showcase.py`   | Runs the engine across all datasets and writes reports        |

Refer to `python -m scripts.<name> --help` for full argument lists.
