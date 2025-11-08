from __future__ import annotations

from builders.curriculum.mit_ocw import (
    _canonical_section_slug,
    _get_profile_heuristics,
    _should_skip_entry,
)


def test_skip_entry_filters_transcripts():
    payload = {
        "title": "Lecture 5 Transcript",
        "resource_type": "Document",
        "file_type": "application/pdf",
    }
    assert _should_skip_entry("resources/lecture-5-transcript/data.json", payload)

    payload_video = {
        "title": "Lecture 5: Semiconductors",
        "resource_type": "Video",
        "file_type": "video/mp4",
    }
    assert not _should_skip_entry("resources/lecture-5/data.json", payload_video)


def test_canonical_section_slug_prefers_known_sections():
    section_order = {"recitations": 1, "exams-and-quizzes": 2}
    heuristics = _get_profile_heuristics("stem")
    slug = _canonical_section_slug(
        "resources",
        kind="recitation",
        title="Recitation 2: Stoichiometry",
        learning_types=["Recitations"],
        section_order=section_order,
        section_parts=("mit3_091f18_rec2",),
        heuristics=heuristics,
    )
    assert slug == "recitations"

    slug_exam = _canonical_section_slug(
        "resources",
        kind="problem_set",
        title="Exam 1 Review",
        learning_types=[],
        section_order=section_order,
        section_parts=("mit3_091f18_exam1",),
        heuristics=heuristics,
    )
    assert slug_exam == "exams-and-quizzes"
