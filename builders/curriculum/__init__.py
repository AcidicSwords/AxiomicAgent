"""
Curriculum builders (MIT + YouTube) to materialize canonical datasets.

Responsibilities:
- Normalize item lists (MIT sections/lectures; YouTube episodes)
- Create nodes.csv and edges_obs.csv with per-step edges
- Inject transcript-derived segment/concept nodes (YouTube)
- Add thin cross-step continuity edges (shared concepts, title similarity)
- Guarantee non-empty steps with a self-edge fallback
"""

from __future__ import annotations

import io
import json
import math
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from PyPDF2 import PdfReader  # type: ignore
except ImportError:  # pragma: no cover
    PdfReader = None  # type: ignore

from core.transcripts import extract_keywords

EdgeEntry = Dict[str, object]
NodeEntry = Dict[str, object]


@dataclass
class CurriculumBuilderParams:
    """
    Parameters that control how canonical curriculum datasets are materialized.
    """

    step_semantics: str = "section_chunk"  # section_chunk | week | static
    profile: str = "stem"  # stem | psych_humanities | lit_essay


def build_from_items_json(
    items_json_path: Path,
    output_zip: Path,
    params: Optional[CurriculumBuilderParams] = None,
) -> None:
    """
    Convert a normalized items JSON file into a canonical curriculum dataset zip.
    """

    cfg = params or CurriculumBuilderParams()
    data = json.loads(Path(items_json_path).read_text(encoding="utf-8-sig"))
    course_id = data.get("course_id", items_json_path.stem)
    items: List[Dict[str, object]] = data.get("items", [])
    prereqs: List[Dict[str, object]] = data.get("prerequisites", [])
    sections: List[Dict[str, object]] = data.get("sections", [])

    profile = (cfg.profile or "stem").lower()
    profile = data.get("profile", profile)

    items = [_normalize_item(dict(item)) for item in items]
    videos_per_step = max(1, int(data.get("videos_per_step", 1)))

    nodes, id_map = _build_nodes(items, course_id)
    if profile in {"psych_humanities", "lit_essay"}:
        edges = _build_edges_profile(items, id_map, cfg.step_semantics, profile)
    elif profile.startswith("youtube"):
        edges = _build_edges_youtube_series(
            items,
            id_map,
            cfg.step_semantics,
            group_size=videos_per_step,
            profile=profile,
        )
    else:
        edges = _build_edges_from_prereqs(items, prereqs, id_map, cfg.step_semantics)

    _attach_resource_edges(items, id_map, edges, cfg.step_semantics)

    # Optional: augment with transcript-derived nodes/edges if present
    try:
        _augment_with_transcripts(
            items_json_path,
            nodes,
            edges,
            items,
            id_map,
            cfg.step_semantics,
        )
    except Exception:
        # Be tolerant; transcript augmentation is optional
        pass

    meta = _build_meta(
        course_id=course_id,
        title=data.get("title", course_id),
        sections=sections,
        step_semantics=cfg.step_semantics,
        node_count=len(nodes),
        edge_count=len(edges),
        profile=profile,
        items=items,
    )

    # Optional: FAISS-based thematic edges over item titles when enabled
    try:
        import os
        if os.environ.get("AXIOM_FAISS_ENABLED", "0") == "1":
            _add_ann_thematic_edges(items, id_map, edges, cfg.step_semantics)
    except Exception:
        pass

    # Ensure no step is empty: for any step with zero edges, add a self-edge on a representative node
    try:
        _ensure_nonempty_steps(items, id_map, edges, cfg.step_semantics)
    except Exception:
        pass

    _write_zip(output_zip, nodes, edges, meta)


# ---------------------------------------------------------------------------
# build helpers
# ---------------------------------------------------------------------------


def _build_nodes(items: List[Dict[str, object]], course_id: str):
    id_map: Dict[str, int] = {}
    nodes: List[NodeEntry] = []
    for idx, item in enumerate(items):
        item_id = str(item.get("item_id"))
        id_map[item_id] = idx
        metrics = item.get("metrics")
        metrics_str = ""
        if isinstance(metrics, dict):
            try:
                metrics_str = json.dumps(metrics)
            except (TypeError, ValueError):
                metrics_str = ""
        nodes.append(
            {
                "id": idx,
                "label": item.get("title", item_id),
                "item_id": item_id,
                "kind": item.get("kind", "unknown"),
                "course_id": course_id,
                "section_index": item.get("section_index"),
                "section_slug": item.get("section_slug"),
                "section_title": item.get("section_title"),
                "section_chunk_index": item.get("section_chunk_index"),
                "week": item.get("week"),
                "order": item.get("order"),
                "tags": ";".join(item.get("tags", [])),
                "source_path": item.get("source_path", ""),
                "metrics": metrics_str,
            }
        )
    return nodes, id_map


def _normalize_item(item: Dict[str, object]) -> Dict[str, object]:
    kind = str(item.get("kind") or "").strip().lower()
    if not kind:
        kind = "concept"
    item["kind"] = kind
    if "section_index" not in item or item.get("section_index") in ("", None):
        section = item.get("section_slug")
        if section:
            parts = section.split("-")
            for part in parts:
                if part.isdigit():
                    item["section_index"] = int(part)
                    break
    return item


def _build_edges_from_prereqs(
    items: List[Dict[str, object]],
    prereqs: List[Dict[str, object]],
    id_map: Dict[str, int],
    step_semantics: str,
) -> List[EdgeEntry]:
    edges: List[EdgeEntry] = []
    items_by_id = {item["item_id"]: item for item in items}

    def resolve_step(item: Dict[str, object]) -> int:
        if step_semantics == "week":
            return int(item.get("week") or item.get("section_index") or 0)
        if step_semantics == "section_chunk":
            section_idx = item.get("section_index") or 0
            chunk_idx = item.get("section_chunk_index") or 0
            return int(section_idx) * 100 + int(chunk_idx)
        return 0

    for rel in prereqs:
        src_key = rel.get("from")
        dst_key = rel.get("to")
        if not src_key or not dst_key:
            continue
        if src_key not in id_map or dst_key not in id_map:
            continue
        dst_item = items_by_id.get(dst_key, {})
        step_id = resolve_step(dst_item)
        edges.append(
            {
                "step": step_id,
                "src": id_map[src_key],
                "dst": id_map[dst_key],
                "val": 1,
            }
        )

    if not edges:
        for nid in id_map.values():
            edges.append({"step": 0, "src": nid, "dst": nid, "val": 1})

    return edges


def _build_edges_profile(
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    step_semantics: str,
    profile: str,
) -> List[EdgeEntry]:
    if profile == "lit_essay":
        return _build_edges_lit_essay(items, id_map, step_semantics)
    return _build_edges_psych_humanities(items, id_map, step_semantics)


def _build_edges_psych_humanities(
    items: List[Dict[str, object]], id_map: Dict[str, int], step_semantics: str
) -> List[EdgeEntry]:
    edges: List[EdgeEntry] = []
    added: set[Tuple[int, int]] = set()

    sessions = _sort_items(
        items, {"lecture", "discussion", "recitation", "concept"}, default_kind="lecture"
    )
    readings = _sort_items(items, {"reading"})
    writing_nodes = _sort_items(items, {"writing_assignment", "project"})
    exams = _sort_items(items, {"exam"})

    if not sessions and readings:
        sessions = readings[:]

    sessions_by_week = _group_by_week(sessions)
    readings_by_week = _group_by_week(readings)

    # Session spine
    _chain_items(edges, added, sessions, id_map, step_semantics)

    # Readings -> sessions (same week)
    for week, reading_list in readings_by_week.items():
        for reading in reading_list:
            for session in sessions_by_week.get(week, []):
                _add_edge(edges, added, reading, session, id_map, step_semantics)

    # Sessions/readings -> writing assignments (same week)
    for assignment in writing_nodes:
        week = _week_value(assignment)
        for session in sessions_by_week.get(week, []):
            _add_edge(edges, added, session, assignment, id_map, step_semantics)
        for reading in readings_by_week.get(week, []):
            _add_edge(edges, added, reading, assignment, id_map, step_semantics)

    # Sessions -> exams (all sessions up to that week)
    for exam in exams:
        exam_week = _week_value(exam)
        for session in sessions:
            if exam_week is None or _week_value(session) <= exam_week:
                _add_edge(edges, added, session, exam, id_map, step_semantics)

    # Sibling reading links per week
    for reading_list in readings_by_week.values():
        _chain_items(edges, added, reading_list, id_map, step_semantics)

    # Writing assignment progression
    _chain_items(edges, added, writing_nodes, id_map, step_semantics)

    if not edges:
        for item in items:
            _add_edge(edges, added, item, item, id_map, step_semantics)

    return edges


def _build_edges_lit_essay(
    items: List[Dict[str, object]], id_map: Dict[str, int], step_semantics: str
) -> List[EdgeEntry]:
    edges: List[EdgeEntry] = []
    added: set[Tuple[int, int]] = set()

    sessions = _sort_items(
        items, {"lecture", "discussion", "concept"}, default_kind="lecture"
    )
    readings = _sort_items(items, {"reading"})
    writing_nodes = _sort_items(items, {"writing_assignment", "project"})

    if not sessions and readings:
        sessions = readings[:]

    sessions_by_week = _group_by_week(sessions)
    readings_by_week = _group_by_week(readings)

    _chain_items(edges, added, sessions, id_map, step_semantics)

    for week, reading_list in readings_by_week.items():
        sessions_target = sessions_by_week.get(week)
        if not sessions_target:
            neighbor = _nearest_week(sessions_by_week, week)
            sessions_target = sessions_by_week.get(neighbor, []) if neighbor is not None else []
        for reading in reading_list:
            for session in sessions_target or []:
                _add_edge(edges, added, reading, session, id_map, step_semantics)

    for assignment in writing_nodes:
        week = _week_value(assignment)
        session_targets: List[Dict[str, object]]
        if week is None:
            session_targets = sessions
        else:
            session_targets = sessions_by_week.get(week, [])
            if not session_targets:
                neighbor = _nearest_week(sessions_by_week, week)
                session_targets = sessions_by_week.get(neighbor, []) if neighbor is not None else []
        for session in session_targets:
            _add_edge(edges, added, session, assignment, id_map, step_semantics)

        reading_targets: List[Dict[str, object]]
        if week is None:
            reading_targets = readings
        else:
            reading_targets = readings_by_week.get(week, [])
            if not reading_targets:
                neighbor = _nearest_week(readings_by_week, week)
                reading_targets = readings_by_week.get(neighbor, []) if neighbor is not None else []
        for reading in reading_targets or []:
            if week is None or (_week_value(reading) or 0) <= (week or 0):
                _add_edge(edges, added, reading, assignment, id_map, step_semantics)

        title_lower = (assignment.get("title") or "").lower()
        if "final" in title_lower or "portfolio" in title_lower:
            assignment_week = week or 0
            for prev in writing_nodes:
                if prev is assignment:
                    break
                prev_week = _week_value(prev) or 0
                if prev_week <= assignment_week:
                    _add_edge(edges, added, prev, assignment, id_map, step_semantics)
            for session in sessions:
                if (_week_value(session) or 0) <= assignment_week:
                    _add_edge(edges, added, session, assignment, id_map, step_semantics)

    _chain_items(edges, added, writing_nodes, id_map, step_semantics)

    if not edges:
        for item in items:
            _add_edge(edges, added, item, item, id_map, step_semantics)

    return edges


YOUTUBE_THEME_KEYWORDS: Dict[str, Tuple[str, ...]] = {
    "math": ("vector", "matrix", "calculus", "algebra", "derivative", "gradient"),
    "physics": ("gravity", "quantum", "mechanics", "electromagnetism", "thermo"),
    "history": ("history", "ancient", "empire", "war", "revolution", "dynasty"),
    "computer_science": ("algorithm", "programming", "code", "computer", "data", "software"),
    "literature": ("poem", "novel", "writing", "essay", "literature"),
    "chemistry": ("molecule", "reaction", "chemistry", "bond"),
}

YOUTUBE_SPECIAL_TAGS = {
    "3b1b": "math",
    "3blue1brown": "math",
    "crashcourse": "history",
}


def _build_edges_youtube_series(
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    step_semantics: str,
    *,
    group_size: int = 1,
    profile: str = "youtube_series",
) -> List[EdgeEntry]:
    edges: List[EdgeEntry] = []
    added: set[Tuple[int, int]] = set()
    group_size = max(1, int(group_size))

    profile_key = profile.lower()
    for item in items:
        order_val = item.get("order")
        try:
            order = int(order_val)
        except (TypeError, ValueError):
            order = 0
        step_index = item.get("step_index")
        if step_index is None:
            step_index = order // group_size
            item["step_index"] = step_index
        if item.get("week") in (None, "", 0):
            item["week"] = step_index + 1
        if item.get("section_index") in (None, "", 0):
            item["section_index"] = item["week"]

    ordered = sorted(
        items,
        key=lambda it: (
            it.get("order") if it.get("order") is not None else _week_value(it) or 0,
            it.get("title", ""),
        ),
    )
    for prev, curr in zip(ordered, ordered[1:]):
        weight = _youtube_edge_weight(prev, curr)
        _add_edge(edges, added, prev, curr, id_map, step_semantics, weight=weight)

    theme_map: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    for item in items:
        for theme in _youtube_theme_tags(item, profile_key):
            theme_map[theme].append(item)

    for theme, group in theme_map.items():
        if len(group) < 2:
            continue
        sorted_group = sorted(group, key=lambda it: it.get("order") or 0)
        for prev, curr in zip(sorted_group, sorted_group[1:]):
            weight = _youtube_edge_weight(prev, curr, boost=1.2)
            _add_edge(edges, added, prev, curr, id_map, step_semantics, weight=weight)

    if not edges:
        for item in items:
            _add_edge(edges, added, item, item, id_map, step_semantics)

    return edges


def _youtube_theme_tags(item: Dict[str, object], profile: str) -> Set[str]:
    tags = {
        str(tag).lower()
        for tag in item.get("tags", [])
        if isinstance(tag, str)
    }
    text_bits = [
        str(item.get("title", "")),
        str(item.get("description", "")),
        " ".join(tags),
    ]
    text = " ".join(text_bits).lower()
    normalized: Set[str] = set(tags)
    for tag in list(tags):
        mapped = YOUTUBE_SPECIAL_TAGS.get(tag)
        if mapped:
            normalized.add(mapped)

    priorities: List[Tuple[str, Tuple[str, ...]]] = list(YOUTUBE_THEME_KEYWORDS.items())
    if profile == "youtube_crashcourse":
        priorities.sort(key=lambda kv: 0 if kv[0] in {"history"} else 1)
    elif profile == "youtube_3b1b":
        priorities.sort(key=lambda kv: 0 if kv[0] in {"math", "physics"} else 1)

    for theme, keywords in priorities:
        if theme in normalized:
            continue
        if any(keyword in text for keyword in keywords):
            normalized.add(theme)
    return normalized


def _youtube_edge_weight(
    src_item: Dict[str, object],
    dst_item: Dict[str, object],
    *,
    boost: float = 1.0,
) -> int:
    src_metrics = _youtube_metrics(src_item)
    dst_metrics = _youtube_metrics(dst_item)
    avg_views = (src_metrics["views"] + dst_metrics["views"]) / 2.0
    avg_likes = (src_metrics["likes"] + dst_metrics["likes"]) / 2.0
    avg_duration = (src_metrics["duration"] + dst_metrics["duration"]) / 2.0

    like_ratio = 0.0
    if avg_views > 0:
        like_ratio = avg_likes / max(avg_views, 1.0)

    base = math.log1p(max(avg_views, 0.0) + avg_duration) / 5.0
    weight = 1.0 + base * (1.0 + like_ratio)
    weight *= boost
    return max(1, int(round(weight)))


def _youtube_metrics(item: Dict[str, object]) -> Dict[str, float]:
    metrics = item.get("metrics")
    result = {"views": 0.0, "likes": 0.0, "duration": 0.0}
    if isinstance(metrics, dict):
        for key in result:
            value = metrics.get(key)
            if isinstance(value, (int, float)):
                result[key] = float(value)
    return result


def _build_meta(
    *,
    course_id: str,
    title: str,
    sections: List[Dict[str, object]],
    step_semantics: str,
    node_count: int,
    edge_count: int,
    profile: str,
    items: List[Dict[str, object]],
) -> Dict[str, object]:
    meta = {
        "adapter": "curriculum",
        "course_id": course_id,
        "title": title,
        "num_items": node_count,
        "num_edges": edge_count,
        "step_semantics": step_semantics,
        "sections": sections,
        "step_lookup": [],
        "profile": profile,
    }

    if sections and step_semantics != "week":
        lookup = []
        for section in sections:
            section_index = section.get("index") or 0
            for chunk in section.get("chunks", []):
                chunk_index = chunk.get("index", 0)
                entry = {
                    "step": section_index * 100 + chunk_index,
                    "section_index": section_index,
                    "section_title": section.get("title"),
                    "chunk_index": chunk_index,
                    "chunk_label": chunk.get("label"),
                }
                lookup.append(entry)
        meta["step_lookup"] = lookup
    elif step_semantics == "week":
        weeks = []
        seen = set()
        for item in items:
            raw_week = item.get("week")
            try:
                week_val = int(raw_week)
            except (TypeError, ValueError):
                week_val = 0
            if week_val not in seen:
                seen.add(week_val)
                weeks.append(week_val)
        weeks.sort()
        meta["step_lookup"] = [
            {
                "step": week,
                "section_index": week,
                "section_title": f"Week {week}" if week else "Unscheduled",
                "chunk_index": 0,
                "chunk_label": f"Week {week}" if week else "Unscheduled",
            }
            for week in weeks
        ]

    return meta


def _write_zip(
    output_zip: Path,
    nodes: List[NodeEntry],
    edges: List[EdgeEntry],
    meta: Dict[str, object],
) -> None:
    node_fields = [
        "id",
        "label",
        "item_id",
        "kind",
        "course_id",
        "section_index",
        "section_slug",
        "section_title",
        "section_chunk_index",
        "week",
        "order",
        "tags",
        "source_path",
        "metrics",
    ]
    edge_fields = ["step", "src", "dst", "val"]

    node_csv = _dicts_to_csv(nodes, node_fields)
    edge_csv = _dicts_to_csv(edges, edge_fields)

    output_zip.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("nodes.csv", node_csv)
        zf.writestr("edges_obs.csv", edge_csv)
        zf.writestr("meta.json", json.dumps(meta, indent=2))


def _dicts_to_csv(rows: List[Dict[str, object]], fields: List[str]) -> str:
    buffer = io.StringIO()
    if not rows:
        buffer.write(",".join(fields))
        buffer.write("\n")
        return buffer.getvalue()

    buffer.write(",".join(fields))
    buffer.write("\n")
    for row in rows:
        values = []
        for field in fields:
            value = row.get(field, "")
            if value is None:
                value = ""
            values.append(str(value).replace("\n", " ").replace("\r", " "))
        buffer.write(",".join(values))
        buffer.write("\n")
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# helper utilities for profile-specific edges
# ---------------------------------------------------------------------------

def _augment_with_transcripts(
    items_json_path: Path,
    nodes: List[NodeEntry],
    edges: List[EdgeEntry],
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    step_semantics: str,
) -> None:
    """
    If items include transcript_path fields, create per-video segment nodes and
    concept nodes, and wire them with edges assigned to the video's step.

    Also records short lists of per-video keywords for thin cross-step continuity
    glue: conceptâ†’next-video edges (shared keywords) and a title-similarity
    videoâ†’video link (when a content anchor overlaps).
    """
    # Lazy import to avoid creating a hard builder->core cycle at import time
    from core.transcripts import coarse_segments, extract_keywords

    base_dir = items_json_path.parent
    concept_node_id: Dict[str, int] = {}
    next_id = max((int(n.get("id", -1)) for n in nodes), default=-1) + 1

    def _add_node(entry: Dict[str, object]) -> int:
        nonlocal next_id
        entry = dict(entry)
        entry["id"] = next_id
        nodes.append(entry)
        nid = next_id
        next_id += 1
        return nid

    # Keep light cross-step glue derived from transcript keywords
    video_keywords: Dict[str, Set[str]] = {}
    ordered_items = sorted(
        items,
        key=lambda it: (
            it.get("order") if it.get("order") is not None else _week_value(it) or 0,
            it.get("title", ""),
        ),
    )

    for item in ordered_items:
        transcript_rel = item.get("transcript_path")
        if not transcript_rel:
            continue
        # Resolve path and load transcript (JSON or VTT)
        tpath = (base_dir / str(transcript_rel)).resolve()
        if not tpath.exists():
            continue
        transcript = None
        try:
            if tpath.suffix.lower() == ".vtt":
                from core.transcripts import parse_vtt_to_segments
                transcript = parse_vtt_to_segments(str(item.get("item_id") or "video"), tpath)
            else:
                transcript = json.loads(tpath.read_text(encoding="utf-8-sig"))
        except Exception:
            transcript = None
        if not transcript:
            continue
        video_item_id = str(item.get("item_id"))
        video_node_id = id_map.get(video_item_id)
        if video_node_id is None:
            continue
        # Compute step for this video
        step = _step_from_item(item, step_semantics)

        # Build coarse segments
        segments = coarse_segments(transcript, segment_duration=30.0)
        prev_seg_nid: Optional[int] = None
        kws_for_video: Set[str] = set()
        for seg_idx, seg in enumerate(segments):
            seg_nid = _add_node(
                {
                    "label": f"{item.get('title','')} [segment {seg_idx}]",
                    "item_id": f"{video_item_id}::seg{seg_idx}",
                    "kind": "segment",
                    "course_id": nodes[video_node_id].get("course_id", ""),
                    "section_index": item.get("section_index"),
                    "section_slug": item.get("section_slug"),
                    "section_title": item.get("section_title"),
                    "section_chunk_index": item.get("section_chunk_index"),
                    "week": item.get("week"),
                    "order": item.get("order"),
                    "tags": "",
                    "source_path": item.get("source_path", ""),
                    "metrics": "",
                }
            )
            # video -> segment
            edges.append({"step": step, "src": video_node_id, "dst": seg_nid, "val": 1})
            # segment sequence
            if prev_seg_nid is not None:
                edges.append({"step": step, "src": prev_seg_nid, "dst": seg_nid, "val": 1})
            prev_seg_nid = seg_nid

            # segment -> concept keywords
            for kw in extract_keywords(seg.get("text", ""), max_keywords=5):
                if kw not in concept_node_id:
                    cid = _add_node(
                        {
                            "label": kw,
                            "item_id": f"kw::{kw}",
                            "kind": "concept",
                            "course_id": nodes[video_node_id].get("course_id", ""),
                            "week": None,
                            "order": None,
                            "tags": "",
                            "source_path": "",
                            "metrics": "",
                        }
                    )
                    concept_node_id[kw] = cid
                edges.append({"step": step, "src": seg_nid, "dst": concept_node_id[kw], "val": 1})
                kws_for_video.add(kw)

        video_keywords[video_item_id] = kws_for_video

    # Thin cross-step edges: connect shared concepts across adjacent items
    MAX_CROSS_PER_STEP = 15
    for prev_item, curr_item in zip(ordered_items, ordered_items[1:]):
        prev_id = str(prev_item.get("item_id"))
        curr_id = str(curr_item.get("item_id"))
        prev_kws = video_keywords.get(prev_id, set())
        curr_kws = video_keywords.get(curr_id, set())
        if not prev_kws or not curr_kws:
            continue
        overlap = list(prev_kws & curr_kws)
        if not overlap:
            continue
        step_curr = _step_from_item(curr_item, step_semantics)
        added = 0
        curr_vid_nid = id_map.get(curr_id)
        if curr_vid_nid is None:
            continue
        for kw in overlap:
            cid = concept_node_id.get(kw)
            if cid is None:
                continue
            edges.append({"step": step_curr, "src": cid, "dst": curr_vid_nid, "val": 1})
            added += 1
            if added >= MAX_CROSS_PER_STEP:
                break

    # Title-similarity: connect previous video to current if titles share informative tokens
    def _title_tokens(title: str) -> Set[str]:
        import re
        raw = re.findall(r"[a-zA-Z][a-zA-Z\-']{3,}", (title or "").lower())
        stop = {"the","and","with","from","into","your","what","when","where","how","this","that","these","those","again","also","just","really","very","more","most","much","some","any","like","over","under","onto","into"}
        return {t for t in raw if t not in stop}

    TITLE_ANCHORS = {
        # math / cs anchors
        "derivative","integral","taylor","series","matrix","vector","eigen","determinant","gradient","limit",
        "algorithm","network","compiler","memory","systems","operating","protocol",
        # history anchors
        "empire","revolution","civilization","samurai","communists","columbus","commerce","industrial",
    }

    for prev_item, curr_item in zip(ordered_items, ordered_items[1:]):
        prev_id = str(prev_item.get("item_id"))
        curr_id = str(curr_item.get("item_id"))
        prev_vid = id_map.get(prev_id)
        curr_vid = id_map.get(curr_id)
        if prev_vid is None or curr_vid is None:
            continue
        a = _title_tokens(str(prev_item.get("title", "")))
        b = _title_tokens(str(curr_item.get("title", "")))
        if not a or not b:
            continue
        inter_terms = a & b
        inter = len(inter_terms)
        union = len(a | b)
        jacc = inter / union if union else 0.0
        # require at least one anchor term in common to avoid generic overlaps
        has_anchor = any(t in TITLE_ANCHORS for t in inter_terms)
        if jacc >= 0.12 and has_anchor:
            step_curr = _step_from_item(curr_item, step_semantics)
            edges.append({"step": step_curr, "src": prev_vid, "dst": curr_vid, "val": 1})


def _ensure_nonempty_steps(
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    edges: List[EdgeEntry],
    step_semantics: str,
) -> None:
    # Build set of steps implied by items
    wanted_steps: Set[int] = set()
    first_item_for_step: Dict[int, Dict[str, object]] = {}
    for it in items:
        s = _step_from_item(it, step_semantics)
        wanted_steps.add(s)
        if s not in first_item_for_step:
            first_item_for_step[s] = it

    # Current edges per step
    has_edges: Set[int] = set(e.get("step", 0) for e in edges)
    missing = [s for s in sorted(wanted_steps) if s not in has_edges]
    for s in missing:
        it = first_item_for_step.get(s)
        if not it:
            continue
        key = str(it.get("item_id"))
        if key not in id_map:
            continue
        nid = id_map[key]
        edges.append({"step": s, "src": nid, "dst": nid, "val": 1})


def _week_value(item: Dict[str, object]) -> Optional[int]:
    week = item.get("week")
    if week not in (None, ""):
        try:
            return int(week)
        except (TypeError, ValueError):
            return None
    section_idx = item.get("section_index")
    if section_idx not in (None, ""):
        try:
            return int(section_idx)
        except (TypeError, ValueError):
            return None
    return None


def _step_from_item(item: Dict[str, object], step_semantics: str) -> int:
    if step_semantics == "week":
        return int(_week_value(item) or 0)
    if step_semantics == "section_chunk":
        section_idx = int(item.get("section_index") or _week_value(item) or 0)
        chunk_idx = int(item.get("section_chunk_index") or 0)
        return section_idx * 100 + chunk_idx
    return 0


def _sort_items(
    items: List[Dict[str, object]],
    kinds: set[str],
    *,
    default_kind: Optional[str] = None,
) -> List[Dict[str, object]]:
    filtered = []
    for item in items:
        kind = (item.get("kind") or "").lower()
        if kind in kinds or (default_kind and kind == "" and default_kind in kinds):
            filtered.append(item)
    return sorted(
        filtered,
        key=lambda it: (
            _week_value(it) or 0,
            it.get("order") or 0,
            it.get("title", ""),
        ),
    )


def _group_by_week(items: List[Dict[str, object]]) -> Dict[int, List[Dict[str, object]]]:
    grouped: Dict[int, List[Dict[str, object]]] = {}
    for item in items:
        week = _week_value(item)
        key = int(week) if week is not None else 0
        grouped.setdefault(key, []).append(item)
    return grouped


def _nearest_week(grouped: Dict[int, List[Dict[str, object]]], target: Optional[int]) -> Optional[int]:
    if not grouped:
        return None
    keys = sorted(grouped.keys())
    if target is None:
        return keys[0]
    best = min(keys, key=lambda k: abs(k - target))
    return best


def _chain_items(
    edges: List[EdgeEntry],
    added: set[Tuple[int, int]],
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    step_semantics: str,
) -> None:
    for prev, curr in zip(items, items[1:]):
        _add_edge(edges, added, prev, curr, id_map, step_semantics)


def _add_edge(
    edges: List[EdgeEntry],
    added: set[Tuple[int, int]],
    src_item: Dict[str, object],
    dst_item: Dict[str, object],
    id_map: Dict[str, int],
    step_semantics: str,
    *,
    weight: float | int = 1,
) -> None:
    if not src_item or not dst_item:
        return
    src_key = src_item.get("item_id")
    dst_key = dst_item.get("item_id")
    if src_key not in id_map or dst_key not in id_map:
        return
    src_id = id_map[src_key]
    dst_id = id_map[dst_key]
    pair = (src_id, dst_id)
    if pair in added:
        return
    added.add(pair)
    step = _step_from_item(dst_item, step_semantics)
    edges.append(
        {
            "step": step,
            "src": src_id,
            "dst": dst_id,
            "val": weight,
        }
    )


def _attach_resource_edges(
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    edges: List[EdgeEntry],
    step_semantics: str,
) -> None:
    added: set[Tuple[int, int]] = {(edge["src"], edge["dst"]) for edge in edges}
    resource_weight = 0.9
    reverse_weight = 0.5
    chunk_weight = 0.6
    slug_targets: Dict[str, Optional[Dict[str, object]]] = {}
    resource_groups: Dict[str, List[Dict[str, object]]] = {}
    for item in items:
        slug = item.get("section_slug")
        if not slug:
            continue
        kind = (item.get("kind") or "").lower()
        if kind in {"lecture", "session", "lecture-videos", "lecture_notes"}:
            slug_targets.setdefault(slug, item)
        if kind == "resource":
            resource_groups.setdefault(slug, []).append(item)
    slug_sequence = sorted(
        (
            slug,
            (
                slug_targets.get(slug) or {}
            ).get("section_index") or 0,
        )
        for slug in slug_targets
    )
    slug_order = [slug for slug, _idx in slug_sequence]
    slug_next: Dict[str, str] = {
        slug_order[i]: slug_order[i + 1] for i in range(len(slug_order) - 1)
    }

    for slug, segments in resource_groups.items():
        target = slug_targets.get(slug)
        prev_seg: Optional[Dict[str, object]] = None
        segments.sort(key=lambda it: it.get("order") or 0)
        for seg in segments:
            if prev_seg:
                _add_edge(edges, added, prev_seg, seg, id_map, step_semantics, weight=chunk_weight)
            if target:
                _add_edge(edges, added, target, seg, id_map, step_semantics, weight=resource_weight)
                _add_edge(edges, added, seg, target, id_map, step_semantics, weight=reverse_weight)
            prev_seg = seg
        next_slug = slug_next.get(slug)
        next_target = slug_targets.get(next_slug) if next_slug else None
        if next_target:
            for seg in segments:
                _add_edge(edges, added, seg, next_target, id_map, step_semantics, weight=reverse_weight)
                _add_edge(edges, added, next_target, seg, id_map, step_semantics, weight=chunk_weight)


def _add_ann_thematic_edges(
    items: List[Dict[str, object]],
    id_map: Dict[str, int],
    edges: List[EdgeEntry],
    step_semantics: str,
    *,
    model_name: str = "all-MiniLM-L6-v2",
    top_k: int = 8,
    min_sim: float = 0.35,
) -> None:
    """Add forward-only thematic edges using ANN over item titles.

    Uses sentence-transformers (if present) and FAISS (if present). Falls back to a
    simple cosine search with numpy if FAISS is not available.
    """
    from core.embeddings import encode_texts
    import numpy as np
    titles = [(it.get("title") or "").strip() for it in items]
    if not titles:
        return
    X = np.array(encode_texts(titles, model_name=model_name))
    n = len(items)
    # Build index
    use_faiss = False
    try:
        import faiss  # type: ignore
        d = X.shape[1]
        index = faiss.IndexFlatIP(d)
        # normalize (already normalized likely)
        index.add(X.astype(np.float32))
        use_faiss = True
    except Exception:
        index = None

    added: set[tuple[int, int]] = set()
    for i, src_item in enumerate(items):
        # Only connect to future items to preserve course order semantics
        if use_faiss:
            import faiss  # type: ignore
            D, I = index.search(X[i : i + 1].astype(np.float32), top_k + 1)
            neighs = [(int(j), float(s)) for j, s in zip(I[0], D[0]) if j != i]
        else:
            # cosine similarities
            sims = (X[i] @ X.T).tolist()
            neighs = sorted(((j, float(s)) for j, s in enumerate(sims) if j != i), key=lambda t: t[1], reverse=True)[: top_k + 10]
        # Filter by position and threshold, cap per-source
        cnt = 0
        for j, sim in neighs:
            if sim < min_sim:
                continue
            if j <= i:
                continue
            src_key = items[i].get("item_id")
            dst_key = items[j].get("item_id")
            if src_key not in id_map or dst_key not in id_map:
                continue
            pair = (id_map[src_key], id_map[dst_key])
            if pair in added:
                continue
            step = _step_from_item(items[j], step_semantics)
            edges.append({"step": step, "src": pair[0], "dst": pair[1], "val": float(sim)})
            added.add(pair)
            cnt += 1
            if cnt >= top_k:
                break





