# Dataset Builder Configuration Guide

This document describes the JSON configuration schema expected by `scripts/build_dataset.py`. Use this as a reference when generating zipped datasets for each adapter domain.

## Common Layout

```json
{
  "domain": "<adapter-name>",
  "inputs": ["path/to/raw/file", "..."],
  "output": "datasets/output.zip",
  "mode": "...",        // optional (domain-specific)
  "builder": { ... }    // optional builder-specific options
}
```

`domain` must match one of the supported adapters. `inputs` is a non-empty array of files that feed the builder, and `output` is the path where the dataset zip will be written. Additional fields depend on the domain.

## conversation_brainstorm

- **Raw format**: JSONL lines with `session_id`, `turn_index`, `speaker`, and `text`.
- **Example configuration**

```json
{
  "domain": "conversation_brainstorm",
  "inputs": ["tests/fixtures/conversation_brainstorm_small.jsonl"],
  "output": "datasets/convo_brainstorm_test.zip",
  "builder": {
    "min_turn_tokens": 1,
    "max_sessions": null,
    "max_turns_per_session": null
  }
}
```

- **Builder options**
  - `min_turn_tokens` (default `1`): drop turns shorter than this token count.
  - `max_sessions` (optional): cap the number of sessions processed.
  - `max_turns_per_session` (optional): limit turns per session.

## research_learning

Supports two modes (`mode` field):

### Activity mode (learning activity logs)

- **Raw format**: JSONL lines containing `user_id`, `timestamp`, `resource_id`, `resource_label`, `event_type`, `score`, `course_id`.
- **Example configuration**

```json
{
  "domain": "research_learning",
  "mode": "activity",
  "inputs": ["tests/fixtures/research_learning_activity_small.jsonl"],
  "output": "datasets/research_activity_test.zip",
  "builder": {
    "min_events_per_user": 1,
    "max_users": null,
    "max_events_per_user": null,
    "event_types_of_interest": null
  }
}
```

- **Builder options**
  - `min_events_per_user` (default `3`): drop users with fewer events.
  - `max_users`: limit number of users processed.
  - `max_events_per_user`: cap events per user.
  - `event_types_of_interest`: filter by specific event types.

### Corpus mode (knowledge corpus)

- **Raw format**: JSON list (or single object) of documents with optional `sections` and `outlinks`.
- **Example configuration**

```json
{
  "domain": "research_learning",
  "mode": "corpus",
  "inputs": ["tests/fixtures/research_learning_corpus_small.json"],
  "output": "datasets/research_corpus_test.zip",
  "builder": {
    "include_section_nodes": true,
    "include_doc_edges": true,
    "include_within_doc_order": true,
    "max_docs": null
  }
}
```

- **Builder options**
  - `include_section_nodes` (default `true`): add section nodes.
  - `include_doc_edges` (default `true`): add doc-level citation edges.
  - `include_within_doc_order` (default `true`): link sections sequentially.
  - `max_docs`: truncate corpus to first `N` documents.

## creation_blueprint

- **Raw format**: JSON specs with `requirements`, `components`, `processes`, and optional `links`.
- **Example configuration**

```json
{
  "domain": "creation_blueprint",
  "inputs": ["tests/fixtures/creation_blueprint_small.json"],
  "output": "datasets/creation_blueprint_test.zip",
  "builder": {
    "treat_process_steps_as_nodes": true,
    "include_requirement_to_component_edges": true
  }
}
```

- **Builder options**
  - `treat_process_steps_as_nodes` (default `true`): create nodes for each process step.
  - `include_requirement_to_component_edges` (default `true`): link requirements to matching components by keyword heuristics.

## curriculum (MIT OCW)

Curriculum datasets are generated in two stages:

1. `scripts/extract_mit_curriculum_html.py` parses raw OCW zips into normalized JSON with `items`, `sections`, and `profile` metadata.
2. `scripts/build_mit_curriculum_datasets.py` converts those JSON files into canonical `nodes.csv` / `edges_obs.csv` zips.

The builder does not use the generic `build_dataset.py` flow; instead configure profiles/step semantics via the CLI (see README).

- **Raw format**: normalized JSON with `items` + `prerequisites` (produced by the extractor).
- **Profiles**: `stem`, `psych_humanities`, `lit_essay` (controls heuristics for sections/edges).
- **Step semantics**: `section_chunk` (default) or `week`.

Example CLI invocation (after extraction):

```bash
python -m scripts.build_mit_curriculum_datasets
```

Builder behavior (per profile) matches the heuristics documented in `builders/curriculum/__init__.py` and the README.

## Running the builder

Invoke the CLI with a configuration file:

```bash
python scripts/build_dataset.py --config path/to/config.json
```

Each builder writes `nodes.csv`, `edges_obs.csv`, and `meta.json` into the specified zip file. The resulting datasets can be replayed through the engine and reporters using `scripts/run_insight.py`.
