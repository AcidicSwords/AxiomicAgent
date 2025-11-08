#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.conversation_brainstorm import (
    ConversationBuilderConfig,
    build_dataset_from_jsonl as build_conversation_dataset,
)
from adapters.research_learning import (
    ResearchActivityBuilderConfig,
    ResearchCorpusBuilderConfig,
    build_dataset_from_activity_logs,
    build_dataset_from_corpus_json,
)
from adapters.creation_blueprint import (
    CreationBlueprintBuilderConfig,
    build_dataset_from_json as build_blueprint_dataset,
)
from builders.curriculum import CurriculumBuilderParams, build_from_items_json
from builders.curriculum.mit_ocw import extract_items_from_zip


def load_config(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset builder utility")
    parser.add_argument("--config", required=True, help="Path to dataset config JSON")
    args = parser.parse_args()

    cfg = load_config(args.config)
    domain = cfg.get("domain")

    if domain == "curriculum":
        _build_curriculum_dataset(cfg)
        return

    inputs = [Path(p) for p in cfg.get("inputs", [])]
    output = Path(cfg.get("output", ""))

    if not inputs:
        raise ValueError("Config must include a non-empty 'inputs' array.")
    if not output:
        raise ValueError("Config must include an 'output' path.")

    if domain == "conversation_brainstorm":
        builder_cfg = ConversationBuilderConfig(**cfg.get("builder", {}))
        build_conversation_dataset(inputs, output, builder_cfg)
    elif domain == "research_learning":
        mode = cfg.get("mode", "activity")
        if mode == "activity":
            builder_cfg = ResearchActivityBuilderConfig(**cfg.get("builder", {}))
            build_dataset_from_activity_logs(inputs, output, builder_cfg)
        elif mode == "corpus":
            builder_cfg = ResearchCorpusBuilderConfig(**cfg.get("builder", {}))
            build_dataset_from_corpus_json(inputs, output, builder_cfg)
        else:
            raise ValueError(f"Unsupported research_learning mode: {mode}")
    elif domain == "creation_blueprint":
        builder_cfg = CreationBlueprintBuilderConfig(**cfg.get("builder", {}))
        build_blueprint_dataset(inputs, output, builder_cfg)
    else:
        raise ValueError(f"Unsupported domain: {domain}")


def _build_curriculum_dataset(cfg: dict) -> None:
    builder_cfg = cfg.get("builder", {})
    source = builder_cfg.get("source")
    items_json = Path(builder_cfg.get("items_json", "datasets/raw_items/course.json"))
    output = Path(builder_cfg.get("output", "datasets/curriculum/course.zip"))
    step_semantics = builder_cfg.get("step_semantics", "section_chunk")
    profile = builder_cfg.get("profile", "stem")
    rebuild_items = builder_cfg.get("rebuild_items", False)

    if not source:
        raise ValueError("Curriculum builder config requires 'source'.")

    source_path = Path(source)
    if not items_json.exists() or rebuild_items:
        if builder_cfg.get("source_format", "mit_ocw") != "mit_ocw":
            raise ValueError("Only 'mit_ocw' source_format is supported right now.")
        print(f"Extracting items from {source_path} ...")
        course = extract_items_from_zip(source_path, profile=profile)
        items_json.parent.mkdir(parents=True, exist_ok=True)
        items_json.write_text(json.dumps(course, indent=2), encoding="utf-8")

    print(f"Building canonical dataset {output} ...")
    params = CurriculumBuilderParams(step_semantics=step_semantics, profile=profile)
    build_from_items_json(items_json, output, params)
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
