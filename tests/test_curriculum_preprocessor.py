from __future__ import annotations

from adapters.base import RawStream
from adapters.curriculum.preprocess import CurriculumPreprocessor


def test_curriculum_preprocessor_emits_weighted_features():
    raw = RawStream(
        nodes={
            1: {"id": "1", "label": "Lecture 1: Limits"},
            2: {"id": "2", "label": "Reading: Foundations"},
            3: {"id": "3", "label": "Essay 1 - Reflection"},
        },
        obs_steps={
            0: {(1, 2), (1, 3)},
        },
        true_steps={},
        meta={"dataset_path": "test"},
    )

    pre = CurriculumPreprocessor()
    processed = pre.process(raw)

    assert processed.node_tags[3] == {"assessment"}
    assert processed.node_weights[1] >= processed.node_weights[2]

    features = processed.step_features[0]
    assert features["unique_node_count"] == 3
    assert features["weighted_node_mass"] > 0
    assert features["assessment_fraction"] > 0
    assert "step_type" in features
    assert features["concept_fraction"] >= features["reading_fraction"]
    assert "avg_views" in features
    assert "engagement_score" in features
