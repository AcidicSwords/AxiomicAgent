# Axiomic Curriculum Engine

Domain‑agnostic graph Core + domain adapters and reporters for structured curricula (MIT, YouTube) and conversations.

- Core computes q (cohesion), TED (drift), spread, continuity, uncertainty (MC), forecast, and regime changes.
- Adapters tailor hygiene and step features; reporters present domain‑specific highlights.

## Project Layout

```
core/          # Engine, policies, signal heads, state tracking (domain‑agnostic)
adapters/      # Streams + preprocessors (curriculum, conversation)
reporters/     # Shared + specialized reporters (curriculum_insight, conversation_insight, dynamics)
pipeline/      # Entry points for each domain + orchestrator (raw->extract->build->preprocess->core->report)
  curriculum/  # normalize_youtube_playlist, build_youtube, build_mit, run_zipless
  conversation/# scrub_transcripts, build_datasets, run_health
  run.py       # manifest‑driven pipeline orchestrator
manifests/     # Example manifests for orchestrated runs
docs/          # Pipeline overview + deprecations
tests/         # Pytest suite
```

See `docs/PIPELINE_OVERVIEW.md` for the skeleton.

## Setup

1) Create a virtual environment (Python 3.10+ recommended):

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt  # if present
```

2) Run tests:

```bash
python -m pytest -q
```

## How to Run (recommended)

Manifest‑driven raw→report orchestration (MIT + YouTube + Conversation in one go):

```bash
python -m pipeline.run --manifest manifests/curriculum_conversation_example.json
```

This performs:
- YouTube: normalize playlists from `RawYT/*.raw.json`, build datasets
- MIT: build datasets from normalized JSON
- Conversation: scrub PDFs/TXT → cleaned JSON → build datasets
- Core (zipless): runs insight + dynamics + domain‑specific reporters

Outputs land in:
- Shared: `reports/mit_curriculum_insights_fs`, `reports/mit_curriculum_dynamics_fs`
- Curriculum: `reports/curriculum_insight_fs`
- Conversation: `reports/conversation_insight_fs`

## Direct domain entry points

Curriculum:
- Normalize playlist: `python -m pipeline.curriculum.normalize_youtube_playlist --input RawYT/<file>.raw.json --output datasets/youtube_raw/<id>.json --course-id <id> --videos-per-step 1`
- Build YouTube dataset: `python -m pipeline.curriculum.build_youtube --input-json datasets/youtube_raw/<id>.json --output-zip datasets/mit_curriculum_datasets/<id>.zip --profile youtube_series --step-semantics week`
- Build MIT datasets: `python -m pipeline.curriculum.build_mit`
- Run Core zipless: `python -m pipeline.curriculum.run_zipless --zip-dir datasets/mit_curriculum_datasets --fs-dir datasets/mit_curriculum_fs --out-dir reports/mit_curriculum_insights_fs --reporter insight --heads monte_carlo forecast regime_change --compute-spread --compute-locality`

Conversation:
- Scrub transcripts: `python -m pipeline.conversation.scrub_transcripts --input-dir RawConversation --out-dir reports/conversation_clean`
- Build datasets: `python -m pipeline.conversation.build_datasets --input-dir reports/conversation_clean --output-dir datasets/mit_curriculum_datasets --window-size 6`
- Quick health metrics: `python -m pipeline.conversation.run_health --input-dir reports/conversation_clean --out-dir reports/conversation_metrics --window 6`

## Make targets (optional)

If you have `make` installed, common targets are provided:

```bash
make test           # run pytest
make run            # orchestrated run via pipeline.run
make build-mit      # build MIT datasets
make build-yt       # normalize+build YouTube datasets defined in manifest
make scrub-convo    # scrub conversation raw PDFs/TXT
make build-convo    # build conversation datasets from cleaned transcripts
```

## Reporters

- `insight` (shared): per‑step commentary + aggregates (avg_q, avg_TED, spread, continuity)
- `curriculum_dynamics` (shared): time‑series with head summaries and regime boundaries
- `curriculum_insight` (domain): phase counts, avg continuity, avg_ted_trusted
- `conversation_insight` (domain): avg adjacency ratio, question density, speaker counts

## Signal Heads

Enable via `--heads` or core_config:
- `monte_carlo`: uncertainty/robustness
- `forecast`: trend slopes + next‑step type
- `regime_change`: change‑point detection

## Deprecations

Legacy scripts under `scripts/` are now wrappers. See `docs/DEPRECATIONS.md` for replacements. Use `pipeline/*` modules and `pipeline/run.py` for all new work.
