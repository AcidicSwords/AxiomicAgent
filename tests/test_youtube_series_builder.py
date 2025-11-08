from __future__ import annotations

from builders.curriculum import _build_edges_youtube_series
from builders.curriculum.youtube_series import normalize_playlist_payload


def make_raw_playlist():
    return {
        "playlist_id": "PL123",
        "title": "Sample Series",
        "channel_title": "CrashCourse",
        "entries": [
            {
                "id": "vid1",
                "title": "Introduction to Calculus",
                "description": "overview",
                "playlist_index": 1,
                "view_count": 1000,
                "like_count": 100,
                "duration": 600,
            },
            {
                "id": "vid2",
                "title": "Derivatives and practice quiz",
                "description": "quiz inside",
                "playlist_index": 2,
                "view_count": 1200,
                "like_count": 150,
                "duration": 700,
            },
            {
                "id": "vid3",
                "title": "Integrals project demo",
                "description": "project build",
                "playlist_index": 3,
                "view_count": 1400,
                "like_count": 160,
                "duration": 800,
            },
        ],
    }


def test_normalize_playlist_payload_outputs_items():
    payload = normalize_playlist_payload(make_raw_playlist(), videos_per_step=1)
    assert payload["course_id"] == "PL123"
    assert payload["profile"] == "youtube_crashcourse"
    items = payload["items"]
    assert len(items) == 3
    assert items[1]["kind"] == "assessment"
    assert "crashcourse" in items[0]["tags"]
    assert items[0]["week"] == 1
    assert items[1]["week"] == 2


def test_youtube_edges_include_sequential_links():
    payload = normalize_playlist_payload(make_raw_playlist(), videos_per_step=1)
    items = payload["items"]
    id_map = {item["item_id"]: idx for idx, item in enumerate(items)}
    edges = _build_edges_youtube_series(items, id_map, step_semantics="week", group_size=1)
    assert edges, "expected sequential edges"
    sequential_pairs = {(edge["src"], edge["dst"]) for edge in edges}
    assert (0, 1) in sequential_pairs
    assert any(edge["val"] > 1 for edge in edges)
    steps = {edge["step"] for edge in edges}
    assert max(steps) >= 2
