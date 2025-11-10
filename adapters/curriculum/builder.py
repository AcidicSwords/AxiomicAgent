"""Curriculum dataset builder."""

from __future__ import annotations

import json
import re
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from adapters.base.zip_writer import write_dataset_zip
from configs.datasets import (
    CurriculumBuilderConfig,
    CurriculumDatasetConfig,
    CurriculumPreprocessorConfig,
)


DEFAULT_CURRIC_STOP = {
    "Contact Us",
    "Browse Course Material",
    "Help & FAQs",
    "About OCW",
    "Give Now",
    "Syllabus",
    "Calendar",
    "Recitations",
    "Download",
    "Transcript",
    "Video",
    "Lecture Notes",
}


def _slug_to_title(slug: str) -> str:
    if not slug:
        return ""
    title = slug.split("/")[-1]
    title = title.replace("-", " ")
    title = re.sub(r"\s+", " ", title).strip()
    return title.title()


def _load_curriculum_titles(zf: zipfile.ZipFile) -> Tuple[str, Dict[str, str]]:
    course_meta = {}
    try:
        course_meta = json.load(zf.open("data.json"))
    except Exception:
        pass
    root_title = course_meta.get("course_title") or course_meta.get("title") or "Course"

    titles: Dict[str, str] = {}
    for name in zf.namelist():
        if not name.startswith("pages/") or not name.endswith("data.json"):
            continue
        rel = name[len("pages/"): -len("data.json")].rstrip("/")
        if not rel:
            continue
        try:
            data = json.load(zf.open(name))
            title = (data.get("title") or "").strip()
        except Exception:
            title = ""
        if not title:
            title = _slug_to_title(rel)
        if title and title not in DEFAULT_CURRIC_STOP:
            titles[rel] = title
    return root_title, titles


def build_dataset(config: CurriculumBuilderConfig) -> None:
    """Materialise the curriculum stream zip according to `config`."""
    with zipfile.ZipFile(config.source) as zf:
        root_title, page_titles = _load_curriculum_titles(zf)

    if not page_titles:
        raise ValueError("No curriculum pages found in raw archive")

    title_map: Dict[str, str] = {"": root_title}
    title_map.update(page_titles)
    children: Dict[str, List[str]] = defaultdict(list)

    def ensure_title(slug: str) -> None:
        if slug in title_map:
            return
        if slug:
            title_map[slug] = _slug_to_title(slug)
        else:
            title_map[slug] = root_title

    for slug in page_titles:
        parts = slug.split("/")
        parent_slug = "/".join(parts[:-1]) if len(parts) > 1 else ""
        ensure_title(parent_slug)
        ensure_title(slug)
        children[parent_slug].append(slug)
        children.setdefault(slug, [])

    def depth(slug: str) -> int:
        return 0 if not slug else slug.count("/") + 1

    ordered_slugs = [""] + sorted(
        [s for s in title_map.keys() if s],
        key=lambda s: (depth(s), s),
    )

    id_map = {slug: idx for idx, slug in enumerate(ordered_slugs)}
    nodes = {idx: title_map[slug] for slug, idx in id_map.items()}

    step_entries: List[List[Tuple[int, int]]] = []
    for parent_slug in ordered_slugs:
        child_slugs = sorted(children.get(parent_slug, []))
        if not child_slugs:
            continue
        if config.max_children is not None:
            child_slugs = child_slugs[:config.max_children]
        src_id = id_map[parent_slug]
        step_edges: List[Tuple[int, int]] = []
        for child_slug in child_slugs:
            dst_id = id_map[child_slug]
            step_edges.append((src_id, dst_id))
        if config.include_sibling_links:
            for i in range(len(child_slugs) - 1):
                a = id_map[child_slugs[i]]
                b = id_map[child_slugs[i + 1]]
                step_edges.append((a, b))
        step_entries.append(step_edges)
        if config.max_steps is not None and len(step_entries) >= config.max_steps:
            break

    cumulative: Set[Tuple[int, int]] = set()
    edges: List[Tuple[int, int, int]] = []
    for step_idx, step_edges in enumerate(step_entries):
        if config.keep_running_ancestor_edges:
            cumulative.update(step_edges)
            active_edges = sorted(cumulative)
        else:
            active_edges = sorted(set(step_edges))
        for src, dst in active_edges:
            edges.append((step_idx, src, dst))

    meta = {
        "type": "curriculum_concepts_stream",
        "source": config.source.name,
        "n": len(nodes),
        "T": len(step_entries),
        "window": 1,
        "stride": 1,
        "tau": 2,
        "max_children": config.max_children,
        "include_sibling_links": config.include_sibling_links,
        "keep_running_ancestor_edges": config.keep_running_ancestor_edges,
        "schema": {
            "edges": ["step", "src", "dst", "val"],
            "nodes": ["id", "concept"],
        },
    }
    write_dataset_zip(config.output, nodes, edges, meta, node_header="concept")


def build_from_config(cfg: CurriculumDatasetConfig) -> None:
    build_dataset(cfg.builder)


def buildercli_to_config(args) -> CurriculumDatasetConfig:
    """Legacy CLI bridge -> config dataclass."""
    builder_cfg = CurriculumBuilderConfig(
        source=Path(args.source),
        output=Path(args.out),
        max_steps=args.max_steps,
        max_children=args.max_children,
    )
    return CurriculumDatasetConfig(
        domain="curriculum",
        builder=builder_cfg,
        preprocessor=CurriculumPreprocessorConfig(),
    )


__all__ = [
    "build_dataset",
    "build_from_config",
    "buildercli_to_config",
]
