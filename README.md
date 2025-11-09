# Axiomic Curriculum Engine

Domainâ€‘agnostic graph Core + domain adapters and reporters for structured curricula (MIT, YouTube) and conversations.

- Core computes q (cohesion), TED (drift), spread, continuity, uncertainty (MC), forecast, and regime changes.
- Adapters tailor hygiene and step features; reporters present domainâ€‘specific highlights.

## Project Layout

```
core/          # Engine, policies, signal heads, state tracking (domainâ€‘agnostic)
adapters/      # Streams + preprocessors (curriculum, conversation)
reporters/     # Shared + specialized reporters (curriculum_insight, conversation_insight, dynamics)
pipeline/      # Entry points for each domain + orchestrator (raw->extract->build->preprocess->core->report)
  curriculum/  # normalize_youtube_playlist, build_youtube, build_mit, run_zipless
  conversation/# scrub_transcripts, build_datasets, run_health
  run.py       # manifestâ€‘driven pipeline orchestrator
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

Manifest-driven orchestration (MIT + YouTube + Conversation in one go):

`ash
python -m pipeline.run --manifest manifests/curriculum_conversation_example.json
`

This performs:
- YouTube: normalize playlists from RAWDATA/RawYT/*.raw.json, build datasets
- MIT: build datasets from normalized JSON
- Conversation: prefers parsed JSON in RAWDATA/ConversationParsed; if none, scrubs PDFs/TXT into RAWDATA/ConversationClean then builds datasets
- Core (zipless): runs insight + dynamics + domain-specific reporters

Outputs land in:
- Shared: eports/mit_curriculum_insights_fs, eports/mit_curriculum_dynamics_fs
- Curriculum: eports/curriculum_insight_fs
- Conversation: eports/conversation_insight_fs (includes QA: zero_node_fraction, zero_edge_fraction, 	otal_turns)
- Combined + sidecars: eports/comprehensive (includes combined.json, perf_summary.json, optional graph_units/ and 	opics_js/)

## Data Layout## Data Layout

See `docs/PIPELINE_LAYOUT.md` for the full map. In short:
- RAWDATA: raw dumps and intermediate normalized/cleaned files
- datasets: canonical, coreâ€‘ready zips and zipless FS extracts
- reports: generated insights/dynamics/metrics

## Direct domain entry points

Curriculum:
- Normalize playlist: python -m pipeline.curriculum.normalize_youtube_playlist --input RAWDATA/RawYT/<file>.raw.json --output RAWDATA/RawYT/<id>.json --course-id <id> --videos-per-step 1
- Build YouTube dataset: python -m pipeline.curriculum.build_youtube --input-json RAWDATA/RawYT/<id>.json --output-zip datasets/youtube_curriculum_datasets/<id>.zip --profile youtube_series --step-semantics week
- Build MIT datasets: python -m pipeline.curriculum.build_mit --raw-dir RAWDATA/raw_mit_curriculum --out-dir datasets/mit_curriculum_datasets
- Run Core zipless: python -m pipeline.curriculum.run_zipless --zip-dir datasets/mit_curriculum_datasets --fs-dir datasets/mit_curriculum_fs --out-dir reports/mit_curriculum_insights_fs --reporter insight --heads monte_carlo forecast regime_change --compute-spread --compute-locality

Conversation (recommended):
- Scrub transcripts (if starting from PDFs/TXT):
  python -m pipeline.conversation.scrub_transcripts --input-dir RAWDATA/RawConversation --out-dir RAWDATA/ConversationClean
- Parse turns with optional sentence chunking to stabilize drift:
  python -m pipeline.conversation.parse_turns --input-dir RAWDATA/ConversationClean --out-dir RAWDATA/ConversationParsed --chunk-size 3
- Build datasets from parsed JSON:
  python -m pipeline.conversation.build_datasets --input-dir RAWDATA/ConversationParsed --output-dir datasets/conversation_datasets --window-size 6 --prefix conversation
- Health metrics with smoothing and progress (skips up-to-date; add --force to recompute):
  python -m pipeline.conversation.run_health --input-dir RAWDATA/ConversationParsed --out-dir reports/conversation_insight_fs --window 12

## Advanced Options## Advanced Options

- Parallel builds: set in manifest `{ "orchestrator": { "parallel": 4 } }`.
- Skip phases: YouTube entries support `skip_normalize` / `skip_build`; conversation supports `skip_scrub` / `skip_build`.
- ANN thematic edges (YouTube/curriculum): set env `AXIOM_FAISS_ENABLED=1` to add forward-only topâ€‘k edges via sentenceâ€‘transformers+FAISS (falls back to cosine).
- Sidecar analyses:
  - Units/community counts: `python -m pipeline.reporting.graph_units --fs-dir datasets/mit_curriculum_fs --out-dir reports/comprehensive/graph_units`
  - Topics + JS drift: `python -m pipeline.reporting.topics_js --fs-dir datasets/mit_curriculum_fs --out-dir reports/comprehensive/topics_js`

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

- `insight` (shared): perâ€‘step commentary + aggregates (avg_q, avg_TED, spread, continuity)
- `curriculum_dynamics` (shared): timeâ€‘series with head summaries and regime boundaries
- `curriculum_insight` (domain): phase counts, avg continuity, avg_ted_trusted
- `conversation_insight` (domain): avg adjacency ratio, question density, speaker counts

## Signal Heads

Enable via `--heads` or core_config:
- `monte_carlo`: uncertainty/robustness
- `forecast`: trend slopes + nextâ€‘step type
- `regime_change`: changeâ€‘point detection

## Deprecations

Legacy scripts under `scripts/` are now wrappers. See `docs/DEPRECATIONS.md` for replacements. Use `pipeline/*` modules and `pipeline/run.py` for all new work.


