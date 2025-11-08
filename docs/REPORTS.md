Reports Overview

This document summarizes the report artifacts and how to interpret the new sidecars.

Main Reports

- Curriculum insights: `reports/mit_curriculum_insights_fs`
  - One JSON per course with aggregates: avg_q, avg_ted, avg_spread, steps, and head summaries.
- Curriculum dynamics: `reports/mit_curriculum_dynamics_fs`
  - One JSON per course with stepwise signals (q, TED, continuity, spread) and optional head output.
- Conversation insights: `reports/conversation_insight_fs`
  - One JSON per conversation with overall metrics, per-turn/step signals, inflection summaries (plain-language), and top_content_nodes.
- Conversation dynamics: `reports/conversation_dynamics_fs`
  - Time-series perspective for conversations (mirrors curriculum dynamics where applicable).
- Combined: `reports/comprehensive` (JSON + Markdown)
  - `combined.json` aggregates curriculum and conversation summaries. When available, it also includes:
    - `units`: avg unit counts from `graph_units` sidecar
    - `topics`: avg JS drift from `topics_js` sidecar
  - `combined.md` is a human-readable short list of course summaries.
  - `perf_summary.json` contains phase timings for orchestrated runs.

Sidecars

- Graph units: `reports/comprehensive/graph_units/*.units.json`
  - Per-step `unit_count` computed from step graphs (community count or connected components) with an `avg_unit_count` summary.
  - Use this as a proxy for “substructure per lesson” (e.g., concept, example, assessment threads).

- Topics + JS drift: `reports/comprehensive/topics_js/*.topics.json`
  - Per-course topic models derived from TF‑IDF + NMF; provides `avg_ted_js` (semantic drift across steps) and top topic terms.
  - On very small/imbalanced steps, JS is clamped and may return 0.0.

Conversation-specific Fields

- `summary.inflections`: list of inferred pivot points with `reasons` and a plain-language `summary` (e.g., “Shift toward apollo, spacecraft, technical”).
- `summary.top_content_nodes`: TF‑IDF-like ranking of content terms (concept/entity/question weighted), with conversational fillers removed.
- `signals[].step_type`: per-step labels aligned with curriculum types: pivot, checkpoint, concept_dense, exploring, scattered, mixed.

ANN Edges (Optional)

- Enabling `AXIOM_FAISS_ENABLED=1` adds forward-only, top‑k thematic edges (YouTube/curriculum) via sentence‑transformers + FAISS. If dependencies are missing, it falls back to cosine similarity.
- Expect modest continuity improvements and limited spread increases, with bounded runtime.

Regime Smoothing (Optional)

- When the `smooth_regimes` sidecar runs, it writes smoothed label sequences to `reports/comprehensive/regime_smoothed/*.smoothed.json`.
- If heavy dependencies are missing, a lightweight threshold + majority vote fallback is used.

