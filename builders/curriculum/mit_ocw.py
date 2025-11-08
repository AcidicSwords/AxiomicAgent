from __future__ import annotations

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse
from zipfile import ZipFile

try:
    from bs4 import BeautifulSoup  # type: ignore
except ImportError:  # pragma: no cover
    raise SystemExit("Please install beautifulsoup4 to use this extractor.")

PROBLEM_TOKENS = ("problem set", "homework", "assignment", "pset")
EXAM_TOKENS = ("exam", "midterm", "final", "quiz")
RECITATION_TOKENS = ("recitation", "tutorial", "discussion")
LECTURE_TOKENS = ("lecture", "session", "class", "video")
READING_TOKENS = (
    "reading",
    "readings",
    "essay",
    "writing",
    "case study",
    "case-study",
    "bibliography",
)
WRITING_TOKENS = (
    "essay",
    "paper",
    "writing assignment",
    "short paper",
    "term paper",
    "portfolio",
    "reflection",
)
DISCUSSION_TOKENS = ("discussion", "section", "recitation", "seminar", "small group")

DATA_PREFIXES = ("pages/", "resources/", "video_galleries/")
NOISE_TOKENS = ("transcript", "caption", "captions", "thumbnail", "thumb", "image")


@dataclass(frozen=True)
class ProfileHeuristics:
    lecture_tokens: Tuple[str, ...] = LECTURE_TOKENS
    reading_tokens: Tuple[str, ...] = READING_TOKENS
    writing_tokens: Tuple[str, ...] = WRITING_TOKENS
    discussion_tokens: Tuple[str, ...] = DISCUSSION_TOKENS
    default_sections: Dict[str, str] = field(
        default_factory=lambda: {
            "lecture": "lecture-videos",
            "recitation": "recitations",
            "reading": "readings",
            "problem_set": "practice-problems",
            "exam": "exams-and-quizzes",
            "writing_assignment": "assignments",
            "project": "projects",
            "concept": "concepts",
            "insight": "instructor-insights",
        }
    )
    include_resources: Tuple[str, ...] = DATA_PREFIXES


PROFILE_HEURISTICS: Dict[str, ProfileHeuristics] = {
    "stem": ProfileHeuristics(),
    "psych_humanities": ProfileHeuristics(
        lecture_tokens=LECTURE_TOKENS + ("topic", "unit", "session"),
        reading_tokens=READING_TOKENS + ("article", "chapter"),
        writing_tokens=WRITING_TOKENS + ("response", "reflection"),
        discussion_tokens=DISCUSSION_TOKENS + ("seminar", "section"),
        default_sections={
            **ProfileHeuristics().default_sections,
            "writing_assignment": "writing-assignments",
            "reading": "readings",
        },
    ),
    "lit_essay": ProfileHeuristics(
        lecture_tokens=LECTURE_TOKENS + ("theme", "unit", "discussion"),
        reading_tokens=READING_TOKENS + ("novel", "poem", "story"),
        writing_tokens=WRITING_TOKENS + ("draft", "portfolio"),
        discussion_tokens=DISCUSSION_TOKENS + ("workshop", "discussion"),
        default_sections={
            **ProfileHeuristics().default_sections,
            "lecture": "themes",
            "reading": "primary-readings",
            "writing_assignment": "essays",
        },
    ),
}


@dataclass
class CourseItem:
    item_id: str
    title: str
    kind: str
    section_index: Optional[int]
    section_slug: str
    section_title: str
    source_path: str
    chunk_index: Optional[int] = None
    week: Optional[int] = None
    order: int = 0

    def to_dict(self) -> Dict[str, object]:
        return {
            "item_id": self.item_id,
            "title": self.title,
            "kind": self.kind,
            "section_index": self.section_index,
            "section_slug": self.section_slug,
            "section_title": self.section_title,
            "section_chunk_index": self.chunk_index,
            "week": self.week,
            "order": self.order,
            "source_path": self.source_path,
        }


@dataclass
class ResourceGuide:
    section_order: Dict[str, int]
    section_titles: Dict[str, str]
    resource_types: Dict[str, str]


def _iter_data_files(zf: ZipFile, profile: str) -> List[str]:
    heuristics = _get_profile_heuristics(profile)
    prefixes = list({*heuristics.include_resources, *DATA_PREFIXES})
    paths = [
        name
        for name in zf.namelist()
        if name.endswith("data.json") and any(name.startswith(pref) for pref in prefixes)
    ]
    return sorted(paths)


def _should_skip_entry(rel_path: str, payload: Dict[str, object]) -> bool:
    """Drop obvious boilerplate like transcripts, caption files, thumbnails."""
    path_lower = rel_path.lower()
    title_lower = str(payload.get("title") or "").lower()
    resource_type = str(payload.get("resource_type") or "").lower()
    file_type = str(payload.get("file_type") or "").lower()

    if any(token in path_lower for token in NOISE_TOKENS):
        return True
    if any(token in title_lower for token in NOISE_TOKENS + ("3play",)):
        return True
    if "caption" in resource_type or "transcript" in resource_type:
        return True
    if resource_type == "image":
        return True
    if file_type in {"application/x-subrip", "text/vtt"}:
        return True
    return False


def _canonical_section_slug(
    slug: str,
    *,
    kind: str,
    title: str,
    learning_types: Iterable[str],
    section_order: Dict[str, int],
    section_parts: Tuple[str, ...],
    heuristics: ProfileHeuristics,
) -> str:
    slug_lower = slug.lower()
    if slug_lower in section_order:
        return slug_lower

    title_lower = title.lower()
    lrts = [entry.lower() for entry in learning_types or []]

    for lrt in lrts:
        if "recitation" in lrt:
            return "recitations"
        if "lecture" in lrt or "podcast" in lrt:
            return "lecture-videos"
        if "reading" in lrt:
            return "readings"

    if "goodie bag" in title_lower or "goodie" in "-".join(section_parts).lower():
        return "goodie-bags"
    if "why this matters" in title_lower:
        return "why-this-matters-videos"
    if any(tok in title_lower for tok in ("practice", "problem")):
        return "practice-problems"
    if any(tok in title_lower for tok in ("exam", "quiz", "midterm", "final")):
        return "exams-and-quizzes"
    if any(tok in title_lower for tok in ("recitation", "tutorial")):
        return "recitations"

    defaults = heuristics.default_sections
    return defaults.get(kind, slug_lower or defaults.get("concept", "content"))


def _title_for_slug(slug: str) -> str:
    if not slug:
        return "Content"
    return slug.replace("-", " ").title()


def extract_items_from_zip(zip_path: Path, profile: str = "stem") -> Dict[str, object]:
    with ZipFile(zip_path) as zf:
        guide = _parse_resource_index(zf)
        course = _extract_course(zf, zip_path.stem, guide, profile)
    course["profile"] = profile
    return course


def extract_items_from_directory(course_dir: Path, profile: str = "stem") -> Dict[str, object]:
    zip_path = course_dir.with_suffix(".zip")
    if zip_path.exists():
        return extract_items_from_zip(zip_path, profile=profile)
    raise ValueError(f"Unsupported MIT OCW source: {course_dir}")


def extract_and_write(root: Path, output_dir: Path, profile: str = "stem") -> List[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results: List[Path] = []
    sources = sorted(root.glob("*.zip"))
    if not sources:
        raise SystemExit(f"No course zips found in {root}")

    for src in sources:
        print(f"Extracting {src.name} ...")
        course = extract_items_from_zip(src, profile=profile)
        course["profile"] = profile
        out_path = output_dir / f"{src.stem}.json"
        out_path.write_text(json.dumps(course, indent=2), encoding="utf-8")
        results.append(out_path)
        print(f"  wrote {out_path}")
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _extract_course(
    zf: ZipFile, course_id: str, guide: ResourceGuide, profile: str
) -> Dict[str, object]:
    heuristics = _get_profile_heuristics(profile)
    items: List[CourseItem] = []
    seen: set[Tuple[str, str]] = set()

    section_order = dict(guide.section_order)
    section_titles = dict(guide.section_titles)
    next_section_index = max(section_order.values(), default=0)

    data_paths = _iter_data_files(zf, profile)
    for rel_path in data_paths:
        parts = Path(rel_path).parts
        if not parts:
            continue
        base_dir = parts[0]
        if base_dir not in {"pages", "resources", "video_galleries"}:
            continue
        if len(parts) < 3:
            if base_dir == "pages" and len(parts) == 2:
                section_slug = parts[1]
                try:
                    data = json.loads(zf.read(rel_path).decode("utf-8"))
                except Exception:
                    continue
                section_titles.setdefault(section_slug, data.get("title") or section_slug.title())
            continue
        try:
            data = json.loads(zf.read(rel_path).decode("utf-8"))
        except Exception:
            continue
        if _should_skip_entry(rel_path, data):
            continue
        title = data.get("title") or parts[-2].replace("-", " ").title()
        content = data.get("content", "")
        key = (title, rel_path)
        if key in seen:
            continue
        seen.add(key)

        section_slug = parts[1] if base_dir == "pages" else base_dir
        if section_slug not in section_order:
            next_section_index += 1
            section_order[section_slug] = next_section_index
        if len(parts) == 3 and base_dir == "pages":
            section_titles.setdefault(section_slug, title)
            continue

        section_parts = tuple(parts[1:-1]) or (parts[-2],)
        section_title = (
            guide.section_titles.get(section_slug)
            or section_titles.get(section_slug)
            or section_slug.replace("-", " ").title()
        )
        section_titles.setdefault(section_slug, section_title)

        source_path = "/".join(parts[:-1])
        kind = _classify_kind(section_parts, title, content, source_path, profile, heuristics)

        learning_types = data.get("learning_resource_types") or []
        canonical_slug = _canonical_section_slug(
            section_slug,
            kind=kind,
            title=title,
            learning_types=learning_types,
            section_order=section_order,
            section_parts=section_parts,
            heuristics=heuristics,
        )
        section_slug = canonical_slug or section_slug
        if section_slug not in section_order:
            next_section_index += 1
            section_order[section_slug] = next_section_index
        section_index = section_order[section_slug]
        section_title = section_titles.get(section_slug) or guide.section_titles.get(section_slug) or _title_for_slug(section_slug)
        section_titles.setdefault(section_slug, section_title)

        item_id = "-".join(section_parts)
        resource_label = guide.resource_types.get(source_path)
        if resource_label:
            kind = _kind_from_resource_column(resource_label, kind)

        order_hint = len(items)
        week = _infer_week(
            title, content, source_path, section_index, profile, order_hint=order_hint
        )

        items.append(
            CourseItem(
                item_id=item_id,
                title=title,
                kind=kind,
                section_index=section_index,
                section_slug=section_slug,
                section_title=section_title,
                source_path=source_path,
                week=week,
                order=order_hint,
            )
        )

    return _post_process_items(course_id, items, section_order, section_titles)


def _post_process_items(
    course_id: str,
    items: List[CourseItem],
    section_order: Dict[str, int],
    section_titles: Dict[str, str],
) -> Dict[str, object]:
    for item in items:
        if item.week is None and item.section_index is not None:
            try:
                item.week = int(item.section_index)
            except (TypeError, ValueError):
                item.week = None

    items_sorted = sorted(
        items,
        key=lambda it: (it.section_index if it.section_index is not None else 999, it.item_id),
    )
    prereqs: List[Dict[str, str]] = []
    prereq_pairs: set[Tuple[str, str]] = set()
    connected_items: set[str] = set()

    def add_prereq(src: str, dst: str) -> None:
        if not src or not dst:
            return
        pair = (src, dst)
        if pair in prereq_pairs:
            return
        prereq_pairs.add(pair)
        prereqs.append({"from": src, "to": dst})
        connected_items.add(src)
        connected_items.add(dst)

    items_by_section: Dict[int, List[CourseItem]] = {}
    for item in items_sorted:
        if item.section_index is None:
            continue
        items_by_section.setdefault(item.section_index, []).append(item)

    kind_order = {
        "lecture": 0,
        "recitation": 1,
        "concept": 2,
        "definition": 2,
        "theorem": 2,
        "reading": 2,
        "problem_set": 3,
        "pset": 3,
        "exam": 4,
    }

    section_sequences: Dict[int, List[CourseItem]] = {}
    chunk_map: Dict[Tuple[int, int], List[CourseItem]] = {}
    section_chunk_info: Dict[int, List[Dict[str, object]]] = {}
    chunk_of_item: Dict[str, Tuple[int, int]] = {}
    for section_idx, sec_items in items_by_section.items():
        sec_sorted = sorted(
            sec_items,
            key=lambda it: (
                kind_order.get(it.kind, 5),
                it.source_path,
            ),
        )
        section_sequences[section_idx] = sec_sorted
        if not sec_sorted:
            continue
        chunk_size = 5 if len(sec_sorted) > 5 else len(sec_sorted) or 1
        chunk_entries: Dict[int, List[CourseItem]] = {}
        for idx, item in enumerate(sec_sorted):
            chunk_idx = 0 if len(sec_sorted) <= chunk_size else idx // chunk_size
            item.chunk_index = chunk_idx
            chunk_map.setdefault((section_idx, chunk_idx), []).append(item)
            chunk_entries.setdefault(chunk_idx, []).append(item)
            chunk_of_item[item.item_id] = (section_idx, chunk_idx)
        section_chunk_info[section_idx] = [
            {
                "index": chunk_idx,
                "label": (
                    f"{sec_sorted[0].section_title} (Part {chunk_idx + 1})"
                    if len(chunk_entries) > 1
                    else sec_sorted[0].section_title
                ),
                "item_ids": [ci.item_id for ci in chunk_entries[chunk_idx]],
            }
            for chunk_idx in sorted(chunk_entries.keys())
        ]
        for prev, curr in zip(sec_sorted, sec_sorted[1:]):
            add_prereq(prev.item_id, curr.item_id)

    chunk_has_edge: Dict[Tuple[int, int], bool] = {key: False for key in chunk_map}
    for rel in prereqs:
        dst_info = chunk_of_item.get(rel["to"])
        if dst_info is not None:
            chunk_has_edge[dst_info] = True

    prev_tail: Optional[CourseItem] = None
    for section_idx in sorted(section_sequences.keys()):
        seq = section_sequences[section_idx]
        if not seq:
            continue
        if prev_tail is not None:
            add_prereq(prev_tail.item_id, seq[0].item_id)
        prev_tail = seq[-1]
        chunk_indices = sorted({item.chunk_index or 0 for item in seq})
        for chunk_idx in chunk_indices:
            if not chunk_has_edge.get((section_idx, chunk_idx), False):
                chunk_items = chunk_map.get((section_idx, chunk_idx), [])
                if chunk_items:
                    add_prereq(chunk_items[0].item_id, chunk_items[0].item_id)

    for item in items_sorted:
        if item.item_id not in connected_items:
            add_prereq(item.item_id, item.item_id)

    sections = [
        {
            "slug": slug,
            "index": idx,
            "title": section_titles.get(slug) or slug.replace("-", " ").title(),
            "chunks": section_chunk_info.get(
                idx,
                [
                    {
                        "index": 0,
                        "label": section_titles.get(slug)
                        or slug.replace("-", " ").title(),
                        "item_ids": [
                            item.item_id
                            for item in section_sequences.get(idx, [])
                        ],
                    }
                ],
            ),
        }
        for slug, idx in sorted(section_order.items(), key=lambda item: item[1])
    ]

    return {
        "course_id": course_id,
        "title": course_id,
        "items": [item.to_dict() for item in items_sorted],
        "prerequisites": prereqs,
        "sections": sections,
    }


def _normalize_href(href: str) -> Optional[str]:
    if not href:
        return None
    parsed = urlparse(href)
    path = parsed.path or href
    while path.startswith("../"):
        path = path[3:]
    if path.startswith("/"):
        path = path[1:]
    if not (
        path.startswith("pages/")
        or path.startswith("resources/")
        or path.startswith("video_galleries/")
    ):
        return None
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    return path.rstrip("/")


def _slug_from_path(path: str) -> Optional[str]:
    if path.startswith("pages/"):
        parts = path.split("/")
    elif path.startswith("resources/"):
        parts = path.split("/")
    else:
        return None
    return parts[1] if len(parts) > 1 else None


def _kind_from_resource_column(column: str, default_kind: str) -> str:
    col = column.lower()
    if "problem" in col or "pset" in col:
        return "problem_set"
    if "exam" in col or "quiz" in col:
        return "exam"
    if "clicker" in col:
        return "problem_set"
    if "lecture notes" in col or "reading" in col or "textbook" in col:
        return "reading"
    if "behind the scenes" in col:
        return "media"
    if "video" in col and "lecture" in col:
        return "lecture"
    if "video" in col:
        return "media"
    return default_kind


def _contains_any(text: str, tokens: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(tok in lowered for tok in tokens)


def _infer_week(
    title: str,
    content: str,
    source_path: str,
    section_index: Optional[int],
    profile: str,
    *,
    order_hint: Optional[int] = None,
) -> Optional[int]:
    search_space = [title, source_path, content[:500]]
    patterns = [
        r"(?:week|wk)\s*([0-9]{1,2})",
        r"(?:session|class|lec)\s*([0-9]{1,2})",
        r"(?:unit)\s*([0-9]{1,2})",
    ]
    for text in search_space:
        lowered = text.lower()
        for pattern in patterns:
            match = re.search(pattern, lowered)
            if match:
                try:
                    value = int(match.group(1))
                    if "session" in pattern and profile in {"psych_humanities", "lit_essay"}:
                        return max(1, (value + 1) // 2)
                    return value
                except ValueError:
                    continue
        for part in re.split(r"[/_-]", lowered):
            if part.isdigit():
                try:
                    return int(part)
                except ValueError:
                    continue
    if section_index not in (None, ""):
        try:
            return int(section_index)
        except (TypeError, ValueError):
            return None
    if order_hint is not None:
        return max(1, (order_hint // 2) + 1)
    return None


def _parse_resource_index(zf: ZipFile) -> ResourceGuide:
    try:
        html = zf.read("pages/resource-index/index.html")
    except KeyError:
        return ResourceGuide({}, {}, {})

    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup

    section_order: Dict[str, int] = {}
    section_titles: Dict[str, str] = {}
    resource_types: Dict[str, str] = {}
    next_order = 1

    for heading in main.find_all("h3"):
        title = heading.get_text(strip=True)
        if not title:
            continue
        title_lower = title.lower()
        if title_lower.startswith("browse") or title_lower.startswith("course info"):
            continue

        slug_counts: Dict[str, int] = defaultdict(int)
        tables: List = []
        sibling = heading.next_sibling
        while sibling and getattr(sibling, "name", None) not in {"h2", "h3"}:
            if getattr(sibling, "name", None) == "table":
                tables.append(sibling)
            sibling = sibling.next_sibling

        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                for idx, cell in enumerate(cells):
                    column_label = headers[idx] if idx < len(headers) else ""
                    for anchor in cell.find_all("a", href=True):
                        norm = _normalize_href(anchor["href"])
                        if not norm:
                            continue
                        slug = _slug_from_path(norm)
                        if slug:
                            slug_counts[slug] += 1
                        if column_label:
                            resource_types.setdefault(norm, column_label)
                            base = norm.split("#", 1)[0]
                            resource_types.setdefault(base, column_label)

        if slug_counts:
            slug = max(slug_counts.items(), key=lambda kv: kv[1])[0]
            if slug not in section_order:
                section_order[slug] = next_order
                section_titles[slug] = title
                next_order += 1

    return ResourceGuide(section_order, section_titles, resource_types)


def _classify_kind(
    path_parts: Tuple[str, ...],
    title: str,
    content: str,
    source_path: str,
    profile: str,
    heuristics: ProfileHeuristics,
) -> str:
    title_lower = title.lower()
    path_text = " ".join(path_parts).lower()
    src_lower = source_path.lower()
    content_lower = content.lower()
    blob = " ".join((title_lower, content_lower, path_text, src_lower))

    is_session = "session" in title_lower or "session" in path_text or "class" in title_lower

    if "insight" in blob:
        return "insight"

    if any(token in blob for token in heuristics.discussion_tokens):
        return "discussion" if profile in {"psych_humanities", "lit_essay"} else "recitation"

    if any(token in blob for token in EXAM_TOKENS):
        return "exam"

    writing_tokens = heuristics.writing_tokens
    reading_tokens = heuristics.reading_tokens
    lecture_tokens = heuristics.lecture_tokens

    if profile in {"psych_humanities", "lit_essay"} and _contains_any(blob, writing_tokens):
        return "writing_assignment"

    if profile in {"psych_humanities", "lit_essay"} and "assignment" in blob:
        return "writing_assignment"

    if _contains_any(blob, reading_tokens) or "reading" in src_lower:
        return "reading"

    if any(token in blob for token in PROBLEM_TOKENS):
        return "problem_set"

    if (
        any(token in blob for token in lecture_tokens)
        or is_session
        or "brain" in title_lower
        or "unit" in title_lower
    ):
        return "lecture"

    return "concept"
def _get_profile_heuristics(profile: str) -> ProfileHeuristics:
    base = PROFILE_HEURISTICS.get(profile.lower())
    if base:
        return base
    return PROFILE_HEURISTICS["stem"]
