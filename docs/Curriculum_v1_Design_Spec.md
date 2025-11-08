# Design Spec: Curriculum v1.0 — MIT + YouTube Transcript Integration

### Purpose

This module establishes a unified, high-fidelity curriculum layer capable of representing both formal (MIT OCW) and informal (YouTube) courses as structurally comparable learning graphs.
It is the foundation for LLM-driven tutoring and analysis.

---

## 1. System Overview

### Goal

To generate stable, interpretable curriculum datasets with per-step metrics that reflect learning structure, using:

* MIT OCW courses (HTML syllabi + structured materials)
* YouTube playlists (metadata + transcripts)

### Key Deliverables

* Normalized curriculum datasets (`*.zip`) under `datasets/curriculum/`
* Step-level metrics and trends (`avg_q`, `avg_TED`, `spread`, `continuity`, slopes, MC uncertainty, phases)
* Unified insight/dynamics reports (`reports/*`)
* Exportable CSV summary for dashboards and LLM agents
* Claude-ready state objects per step for tutoring or orchestration

---

## 2. Core Concepts & Metrics

| Metric                    | Meaning                              | Ideal Range             | Interpretation                               |
| ------------------------- | ------------------------------------ | ----------------------- | -------------------------------------------- |
| avg_q                     | Structural cohesion within a step    | 0.6–1.0                 | Higher → internally consistent lesson/module |
| avg_TED                   | Step-to-step drift                   | 0.02–0.18               | Lower → smoother transitions                 |
| spread                    | Cross-step connectivity              | 0.0–0.8                 | Higher → strong inter-unit links             |
| continuity                | Concept overlap between steps        | 0.0–0.3                 | Higher → recurring ideas                     |
| q/TED slopes              | Trend direction                      | ±0.02 typical           | Shows tightening or widening coherence       |
| q_mc_std / ted_mc_std     | Uncertainty (Monte Carlo robustness) | 0.001–0.007 / 0.02–0.13 | Lower → stable graph                         |
| phases                    | Regime-change segments               | 0–40+                   | Units or topic arcs automatically detected   |

---

## 3. Data Flow

```
Raw Source → Extractor → Builder → Adapter → Core → Reporter
                    ↓
               Transcript Parser
                    ↓
           Concept & Segment Graphs
```

### 3.1 Extractors

* `extract_mit_curriculum_html.py` — parses MIT OCW pages into JSON.
* `collect_youtube_course.py` — fetches playlist metadata and transcripts (via `yt-dlp` or `youtube_transcript_api`).

### 3.2 Builders

* MIT Builder — section/lecture hierarchy.
* YouTube Builder — episode → segment → concept hierarchy.

### 3.3 Adapters

Map dataset structures into core features and metrics:

* `curriculum_stream.py`
* `youtube_stream.py` (transcript-aware)

### 3.4 Core

Calculates signals:

* q — internal cohesion
* TED — drift
* spread / continuity
* MC heads — robustness
* Forecast / Regime heads — trends and phase detection

### 3.5 Reporters

Generate:

* `*_insight.json` — per-course aggregates
* `*_curriculum_dynamics.json` — per-step timeseries
* `comparison.json` — multi-course summary

---

## 4. Transcript Integration

### Source

* `yt-dlp` auto-subtitles (`.vtt`)
* `youtube_transcript_api` (JSON fallback)

### Normalization

`core/transcripts.py`

```
{
  "video_id": "abc123",
  "segments": [
    {"start": 0.0, "end": 27.3, "text": "Intro to derivatives"},
    {"start": 27.3, "end": 54.0, "text": "Visual intuition..."}
  ]
}
```

### Processing

1. Parse fine-grained captions.
2. Coarsen to ~30-second segments (`coarse_segments()`).
3. Extract keywords (simple TF-IDF or frequency filter).
4. Emit concept and segment nodes to builder.
5. Build intra-video edges:
   * `video_segment`
   * `segment_seq`
   * `segment_concept`
6. Optionally create cross-video thematic edges (concept overlap).

---

## 5. Reporting Outputs

### Insight Summary Example

```
{
  "course_id": "essence_calculus",
  "avg_q": 0.856,
  "avg_TED": 0.165,
  "avg_spread": 0.000,
  "avg_continuity": 0.028,
  "phases": 5,
  "q_mc_std": 0.0016,
  "ted_mc_std": 0.0096,
  "q_slope": 0.016,
  "TED_slope": -0.017
}
```

### Dynamics Report Example

```
{
  "step_id": 7,
  "phase": "implicit_differentiation",
  "q": 0.892,
  "TED": 0.172,
  "continuity": 0.045,
  "step_type": "concept_dense",
  "top_concepts": ["derivative", "implicit", "chain rule"]
}
```

---

## 6. Export & Integration

### 6.1 CSV Export

Script: `scripts/export_curriculum_metrics.py`

* Consolidates all courses into a flat table:

```
course_id,source_type,avg_q,avg_TED,avg_spread,avg_continuity,q_slope,TED_slope,q_mc_std,ted_mc_std,phases
```

* Target: `reports/comparisons/curriculum_summary.csv`

### 6.2 Claude-Ready JSON State

Each step emits a compact, LLM-digestible object:

```
{
  "course_id": "18.01sc",
  "step": 42,
  "phase": "integration_basics",
  "q": 0.92,
  "TED": 0.03,
  "continuity": 0.08,
  "step_type": "checkpoint",
  "top_concepts": ["definite integral", "area", "antiderivative"],
  "guidance": "Review definitions; apply to problem set 4."
}
```

Used as context + system guidance for the Claude tutoring loop.

---

## 7. Implementation Checklist

### Data Pipeline

* [x] Add transcript parser + coarsener.
* [x] Update YouTube builder with segment/concept nodes.
* [x] Integrate continuity metric (concept overlap per step).
* [x] Recompute insights/dynamics with transcript-aware data.
* [x] Add cross-step thematic edges.
* [ ] Apply playlist-level TF-IDF keyword weighting.

### Reporting

* [x] Append `avg_continuity` to comparison JSON.
* [x] Add continuity trend to dynamics JSON.
* [x] Export unified CSV for dashboards.

### Validation

* [x] MIT baselines produce q ≈ 0.9+, TED ≤ 0.1, multi-phase graphs.
* [x] YouTube sets produce q 0.77–0.95, TED 0.08–0.17, 2–9 phases.
* [x] MC stds within stable bounds (≤ 0.007 / ≤ 0.13).
* [x] Phase detection matches pedagogical arcs.

---

## 8. Expected Outcomes

| Objective                                 | Result                                       |
| ----------------------------------------- | -------------------------------------------- |
| Structural parity between MIT and YouTube | ✅ Achieved via transcript graphing           |
| Stable q/TED metrics                      | ✅ Cohesion + drift consistent across domains |
| Regime detection                          | ✅ Correct phase segmentation for both styles |
| LLM-readable step state                   | ✅ Simple JSON representation available       |
| Low-uncertainty graphs                    | ✅ Monte Carlo stds near baseline             |

---

## 9. Recommended Next Steps

1. Polish:
   * Add TF-IDF filtering for transcript keywords.
   * Consider raising cross-step caps where playlists are tightly sequential.
2. Freeze:
   * Tag this branch as `curriculum_v1.0` once CSV + continuity fields verified.
3. Integrate with Claude:
   * Use the per-step state JSONs as the tutoring context.
   * Control loop: if `TED` high → explanation mode; if `phase_boundary` → summary; if `q` low → exploratory questions.
4. Iterate:
   * Collect LLM feedback → adjust step granularity or weighting as needed.

---

## 10. Summary

Curriculum v1.0 fuses structured academic data (MIT OCW) and open educational media (YouTube) into one coherent analytical and instructional substrate.
The transcript system converts raw video dialogue into concept graphs, enabling fine-grained cohesion, drift, and continuity metrics.
The resulting datasets are robust, interpretable, and ready for LLM integration, forming the first fully validated domain in the AxiomicAgent ecosystem.

