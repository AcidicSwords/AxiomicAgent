from __future__ import annotations

from builders.curriculum import (
    _build_edges_psych_humanities,
    _build_meta,
    CurriculumBuilderParams,
)


def make_item(item_id: str, kind: str, week: int | None = None, title: str | None = None):
    return {
        "item_id": item_id,
        "kind": kind,
        "week": week,
        "title": title or item_id,
        "section_index": 1,
        "section_slug": "section",
        "section_title": "Section",
        "section_chunk_index": 0,
    }


def test_build_meta_week_lookup():
    items = [
        make_item("lec1", "lecture", 1),
        make_item("readingA", "reading", 2),
        make_item("assignment", "writing_assignment", None),
    ]
    meta = _build_meta(
        course_id="test",
        title="Test",
        sections=[],
        step_semantics="week",
        node_count=3,
        edge_count=2,
        profile="psych_humanities",
        items=items,
    )
    steps = meta["step_lookup"]
    assert steps[0]["step"] == 0
    assert steps[1]["step"] == 1
    assert steps[2]["step"] == 2


def test_psych_builder_fallback_without_sessions():
    readings = [make_item("reading1", "reading", 1)]
    writing = [make_item("essay1", "writing_assignment", 1)]
    items = readings + writing
    id_map = {item["item_id"]: idx for idx, item in enumerate(items)}
    edges = _build_edges_psych_humanities(items, id_map, step_semantics="week")
    assert edges, "expected fallback edges when sessions missing"
