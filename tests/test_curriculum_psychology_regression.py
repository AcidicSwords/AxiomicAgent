from __future__ import annotations

from pathlib import Path

import pytest

from adapters.curriculum.stream import CurriculumStream


@pytest.mark.integration
def test_psychology_curriculum_richness():
    """
    Ensure the psychology curriculum dataset retains rich, multi-part content.
    Guards against regressions when tweaking non-STEM extraction heuristics.
    """

    root = Path(__file__).resolve().parents[1]
    dataset_path = root / "datasets" / "mit_curriculum_datasets" / "9.00sc-fall-2011.zip"
    if not dataset_path.exists():
        pytest.skip("Psychology dataset not present; skip regression check")

    stream = CurriculumStream(path=str(dataset_path))

    # overall coverage
    assert len(stream.nodes) >= 30
    meta = stream.meta()
    assert meta.get("steps", 0) >= 12

    # ensure multiple step windows carry structure
    nonempty_steps = sum(1 for edges in stream.obs_steps.values() if edges)
    assert nonempty_steps >= 9

    # ensure chunking metadata exists (multiple parts per section)
    step_lookup = meta.get("step_lookup", [])
    has_chunks = any(entry.get("chunk_index", 0) > 0 for entry in step_lookup)
    if not has_chunks:
        sections = meta.get("sections", [])
        has_chunks = any(
            len(chunk.get("item_ids", [])) > 1
            for section in sections
            for chunk in section.get("chunks", [])
        )
    assert has_chunks, "expected multi-part sections or chunk metadata"

    # verify non-concept nodes surface in summaries
    has_curriculum_variety = any("reading" in tags for tags in stream.node_tags.values())
    if not has_curriculum_variety:
        has_curriculum_variety = any("assessment" in tags for tags in stream.node_tags.values())
    assert has_curriculum_variety, "expected at least one non-concept curriculum node"
