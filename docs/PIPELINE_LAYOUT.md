Pipeline Layout and Data Contracts

This repository uses a strict two-tier data policy and a single manifest-driven orchestrator. The goal is to keep raw/intermediate artifacts clearly separated from finalized datasets and to make report locations predictable.

Tiers

- RAWDATA (raw + intermediate)
  - RAWDATA/RawYT
    - <course>.raw.json  (yt-dlp or API dump)
    - <course>.json      (normalized playlist)
  - RAWDATA/raw_mit_curriculum
    - *.json (normalized MIT course items)
  - RAWDATA/RawConversation
    - PDFs/TXT by subfolder (PositiveExample, NegativeExample, …)
  - RAWDATA/ConversationClean
    - *.json (actors, context, transcript turns)
    - *.md   (human-readable transcript)

- datasets (final, core-ready)
  - datasets/mit_curriculum_datasets
    - *.zip (canonical MIT/YouTube curriculum datasets)
  - datasets/mit_curriculum_fs
    - Zipless extraction of the above (used for zipless analysis)
  - datasets/conversation_datasets
    - conversation_*.zip (canonical conversation datasets)

- reports (outputs)
  - reports/mit_curriculum_insights_fs
    - Per-course *_insight.json + comparison.json
  - reports/mit_curriculum_dynamics_fs
    - Per-course *_curriculum_dynamics.json (stepwise timeseries)
  - reports/curriculum_insight_fs
    - Domain summary variants (aggregated metrics across courses)
  - reports/conversation_insight_fs
    - Per-conversation *.metrics.json (conversation health and pivots)

Orchestrator

- Entry: `python -m pipeline.run --manifest manifests/curriculum_conversation_example.json`
- Responsibilities:
  - Normalize YouTube playlists (RAWDATA/RawYT)
  - Build MIT and YouTube datasets (datasets/mit_curriculum_datasets)
  - Scrub conversation transcripts (RAWDATA/ConversationClean)
  - Build conversation datasets (datasets/conversation_datasets)
  - Run zipless curriculum reports (reports/*_fs)
  - Run conversation health reports (reports/conversation_insight_fs)

Adapter Contracts (high level)

- Curriculum builder emits canonical zips with:
  - nodes.csv (id, label, kind, attrs)
  - edges.csv (from_id, to_id, step_id, edge_type)
  - meta.json (course_id, profile, step_semantics, counts)

- Conversation scrubber emits JSON with:
  - source_file, title, actors, context, transcript: [{speaker, text}]
  - Dataset builder converts to canonical conversation zip (nodes/edges/meta)

Guidelines

- Only RAWDATA should contain raw dumps and intermediate normalized/cleaned files.
- Only datasets should contain canonical zips and zipless FS extracts.
- Only reports should contain generated metrics/insights.
- Never mix tiers; the orchestrator paths enforce this separation by default.

