# Deprecations

The project has been refactored to make the pipeline skeleton explicit and domain‑modular.
Prefer the entry points under `pipeline/` and the manifest orchestrator.

Deprecated (kept for backward compatibility):
- `scripts/run_curriculum_zipless_pipeline.py` → use `pipeline/curriculum/run_zipless.py` or the orchestrator (`scripts/ingest_and_analyze.py`).
- `scripts/run_mit_curriculum_showcase.py` → use `pipeline/curriculum/run_zipless.py`.
- `scripts/build_mit_curriculum_datasets.py` → use `pipeline/curriculum/build_mit.py`.
- `scripts/normalize_youtube_playlist.py` → use `pipeline/curriculum/normalize_youtube_playlist.py`.
- `scripts/build_youtube_curriculum.py` → use `pipeline/curriculum/build_youtube.py`.
- `scripts/scrub_transcripts.py` → use `pipeline/conversation/scrub_transcripts.py`.
- `scripts/build_conversation_datasets.py` → use `pipeline/conversation/build_datasets.py`.
- `scripts/run_conversation_health.py` → use `pipeline/conversation/run_health.py`.

These scripts will emit a deprecation notice when invoked directly and internally call the new pipeline entry points.
