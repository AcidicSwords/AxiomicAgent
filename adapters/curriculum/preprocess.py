"""
Curriculum preprocessing: filter/weight nodes and edges, summarize steps.

Key features:
- Type inference and weights (concept/assessment/reading/meta/media/...)
- Stoplists + regexes to drop navigation/media artifacts
- Per-step summary: quality(q), stability, top_nodes, fractions, engagement
- YouTube extras:
  * continuity (concept Jaccard overlap between steps)
  * light q normalization for very dense per-step graphs
  * top_nodes filtering tuned for content phrases (anchors for singles)
"""

from __future__ import annotations

import json
import re
from typing import Dict, Iterable, List, Set, Tuple

from adapters.base import Edge, Frame, ProcessedStream, RawStream
from configs.datasets import CurriculumPreprocessorConfig, CurriculumTypeRule

DEFAULT_STOP_NODES = {
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

DEFAULT_STOP_PATTERNS = [
    r"^lec\d+(\.jpg|\.png|\.mp4|\.srt)$",
    r".*\.srt$",
    r"^\s*$",
]

# Labels that should never be surfaced as "top nodes" (but may still exist as nodes)
_TOPNODE_ARTIFACT_RE = re.compile(r"\.(pdf|docx?|pptx?|jar|zip|tar|gz|csv|xlsx)$", re.I)
_TOPNODE_FILLER = {
    "access",
    "address",
    "after",
    "ability",
    "although",
    "allowed",
    "almost",
    "before",
    "based",
    "adding",
    "also",
    "again",
    "actually",
    "another",
    "because",
    "between",
    "different",
    "example",
    "important",
    "instead",
    "really",
    "right",
    "something",
    "together",
    "using",
    "way",
    "well",
}

# Single-token anchors we still allow for YouTube top nodes
_SINGLE_TOKEN_ANCHORS = {
    # STEM
    "derivative","derivatives","integral","integrals","taylor","series",
    "matrix","matrices","vector","vectors","eigen","determinant","gradient",
    "algorithm","algorithms","network","compiler","memory","systems",
    # History
    "empire","revolution","civilization","samurai","communists"
}

DEFAULT_TYPE_WEIGHTS = {
    "exam": 0.70,
    "pset": 0.70,
    "concept": 1.00,
    "theorem": 1.00,
    "definition": 1.00,
    "segment": 0.70,
    "reading": 0.85,
    "nav": 0.05,
    "media": 0.05,
    "person": 0.30,
    "meta": 0.20,
    "unknown": 0.50,
}

DEFAULT_KEEP_THRESHOLD = 0.10
DEFAULT_TOPK_PER_NODE = 50


def _default_type_rules() -> List[CurriculumTypeRule]:
    return [
        CurriculumTypeRule(type="exam", weight=2.0, pattern=r"(exam|midterm|final|quiz)", tag="assessment"),
        CurriculumTypeRule(type="pset", weight=1.2, pattern=r"(problem set|pset|homework)", tag="assessment"),
        CurriculumTypeRule(type="concept", weight=1.0, pattern=r"(lecture|session|topic|unit)", tag="concept"),
        CurriculumTypeRule(type="reading", weight=0.8, pattern=r"(reading|reading list|text|novel|story)", tag="reading"),
        CurriculumTypeRule(type="assessment", weight=2.5, pattern=r"(essay|paper|writing assignment|portfolio)", tag="assessment"),
        CurriculumTypeRule(type="insight", weight=0.3, pattern=r"(insight|guideline|syllabus)", tag="meta"),
    ]


class CurriculumPreprocessor:
    def __init__(
        self,
        config: CurriculumPreprocessorConfig | None = None,
        *,
        stop_nodes: Set[str] | None = None,
        stop_patterns: Iterable[str] | None = None,
        type_weights: Dict[str, float] | None = None,
        keep_threshold: float | None = None,
        topk_per_node: int | None = None,
    ):
        cfg = config or CurriculumPreprocessorConfig(
            stop_nodes=list(DEFAULT_STOP_NODES),
            regex_patterns=list(DEFAULT_STOP_PATTERNS),
            type_rules=[],
            keep_threshold=DEFAULT_KEEP_THRESHOLD,
            topk_per_node=DEFAULT_TOPK_PER_NODE,
        )
        merged_stop_nodes = stop_nodes if stop_nodes is not None else set(cfg.stop_nodes or [])
        if not merged_stop_nodes:
            merged_stop_nodes = set(DEFAULT_STOP_NODES)
        else:
            merged_stop_nodes = set(merged_stop_nodes) | {s for s in DEFAULT_STOP_NODES}
        self.stop_nodes = set(merged_stop_nodes)
        self.stop_nodes_lower = {s.lower() for s in self.stop_nodes}

        pattern_values = list(stop_patterns if stop_patterns is not None else (cfg.regex_patterns or []))
        if not pattern_values:
            pattern_values = list(DEFAULT_STOP_PATTERNS)
        self.stop_re = [re.compile(p, re.I) for p in pattern_values]

        base_type_weights = dict(DEFAULT_TYPE_WEIGHTS)
        self.custom_rules: List[CurriculumTypeRule] = _default_type_rules()
        if cfg.type_rules:
            self.custom_rules.extend(cfg.type_rules)
        # normalize tokens to lowercase for simple containment checks
        for rule in self.custom_rules:
            if rule.match:
                rule.match = [token.lower() for token in rule.match]
            base_type_weights[rule.type] = rule.weight
        if type_weights:
            base_type_weights.update(type_weights)
        self.type_weights = base_type_weights
        self.keep_threshold = float(
            keep_threshold if keep_threshold is not None else cfg.keep_threshold or DEFAULT_KEEP_THRESHOLD
        )
        self.topk_per_node = int(topk_per_node if topk_per_node is not None else cfg.topk_per_node or DEFAULT_TOPK_PER_NODE)

        # Trusted connectivity configuration (can be overridden via env)
        # Components: verification (freq), authority (tags), recency (last seen), locality (node weight)
        import os
        def _env_float(name: str, default: float) -> float:
            try:
                return float(os.environ.get(name, default))
            except Exception:
                return default
        self.trusted_alpha = _env_float("AXIOM_TRUST_ALPHA", 0.4)
        self.trusted_beta  = _env_float("AXIOM_TRUST_BETA",  0.2)
        self.trusted_gamma = _env_float("AXIOM_TRUST_GAMMA", 0.2)
        self.trusted_delta = _env_float("AXIOM_TRUST_DELTA", 0.2)
        self.trusted_tau   = _env_float("AXIOM_TRUST_TAU",   0.6)

    def process(self, raw: RawStream) -> ProcessedStream:
        nodes = {nid: dict(data) for nid, data in raw.nodes.items()}
        node_type: Dict[int, str] = {}
        node_weights: Dict[int, float] = {}
        for nid, data in nodes.items():
            ntype, weight = self._infer_type(data)
            node_type[nid] = ntype
            node_weights[nid] = weight

        node_tags: Dict[int, Set[str]] = {
            nid: self._tags_for_type(ntype) for nid, ntype in node_type.items()
        }

        obs_steps: Dict[int, Frame] = {}
        for step, edges in raw.obs_steps.items():
            filtered = self._cap_step(
                [edge for edge in edges if self._keep_edge(edge, nodes, node_weights)]
            )
            obs_steps[step] = filtered

        true_steps: Dict[int, Frame] = {}
        for step, edges in raw.true_steps.items():
            filtered = self._cap_step(
                [edge for edge in edges if self._keep_edge(edge, nodes, node_weights)]
            )
            true_steps[step] = filtered

        used_nodes: Set[int] = set()
        for step_edges in obs_steps.values():
            for u, v in step_edges:
                used_nodes.add(u)
                used_nodes.add(v)
        for step_edges in true_steps.values():
            for u, v in step_edges:
                used_nodes.add(u)
                used_nodes.add(v)

        nodes = {nid: label for nid, label in nodes.items() if nid in used_nodes}
        node_tags = {nid: tags for nid, tags in node_tags.items() if nid in nodes}
        node_weights = {nid: node_weights.get(nid, 1.0) for nid in nodes}

        step_features: Dict[int, Dict[str, object]] = {}
        for step, edges in obs_steps.items():
            step_features[step] = self._summarize_step(step, edges, node_tags, node_weights, nodes)

        # --- Trusted connectivity (TED_tau) approximation ---
        # Compose a per-edge quality score from verification (freq), authority (tags),
        # recency (last seen distance), and locality (min node weight).
        # Then compute trusted TED as Jaccard on edges with quality >= tau.
        edge_freq: Dict[Edge, int] = {}
        last_seen: Dict[Edge, int] = {}
        for s in sorted(obs_steps.keys()):
            for e in obs_steps[s]:
                edge_freq[e] = edge_freq.get(e, 0) + 1
                last_seen[e] = s

        def authority(u: int, v: int) -> float:
            tags_u = node_tags.get(u, set()); tags_v = node_tags.get(v, set())
            def w(tags: Set[str]) -> float:
                if 'theorem' in tags or 'definition' in tags:
                    return 1.0
                if 'assessment' in tags:
                    return 0.8
                if 'reading' in tags:
                    return 0.6
                if 'concept' in tags:
                    return 0.7
                return 0.5
            return min(w(tags_u), w(tags_v))

        # weights for components (configurable via env)
        alpha, beta, gamma, delta = self.trusted_alpha, self.trusted_beta, self.trusted_gamma, self.trusted_delta
        tau = self.trusted_tau

        trusted_prev: Set[Edge] = set()
        for s in sorted(obs_steps.keys()):
            edges = obs_steps[s]
            trusted_now: Set[Edge] = set()
            for e in edges:
                u, v = e
                verif = min(1.0, edge_freq.get(e, 1) / 5.0)  # cap at 5 occurrences
                auth = authority(u, v)
                rec = 0.0
                if e in last_seen:
                    dist = max(0, s - last_seen[e])
                    rec = 1.0 / (1.0 + dist)  # closer = higher recency
                loc = min(float(node_weights.get(u, 0.5)), float(node_weights.get(v, 0.5)))
                q_edge = alpha * verif + beta * auth + gamma * rec + delta * loc
                if q_edge >= tau:
                    trusted_now.add(e)

            # compute trusted TED
            inter = len(trusted_now & trusted_prev)
            union = len(trusted_now | trusted_prev)
            ted_trusted = 0.0 if union == 0 else round(1.0 - inter / union, 3)
            feats = step_features.get(s, {})
            feats["trusted_edge_count"] = len(trusted_now)
            feats["ted_trusted"] = ted_trusted
            step_features[s] = feats
            trusted_prev = trusted_now

        # Compute continuity metric between consecutive steps (concept-node overlap Jaccard)
        steps_sorted = sorted(step_features.keys())
        prev_concepts: Set[int] | None = None
        for s in steps_sorted:
            feats = step_features[s]
            # nodes present in this step
            step_nodes: Set[int] = set(n for (u, v) in obs_steps.get(s, set()) for n in (u, v))
            # concept-only subset
            concept_nodes = {n for n in step_nodes if 'concept' in (node_tags.get(n, set()) or set())}
            if prev_concepts is None:
                feats['continuity'] = 0.0
            else:
                inter = len(concept_nodes & prev_concepts)
                union = len(concept_nodes | prev_concepts)
                feats['continuity'] = round((inter / union) if union else 0.0, 3)
            prev_concepts = concept_nodes

        meta = dict(raw.meta)
        meta.setdefault("filter", "curriculum")
        meta.setdefault("stop_nodes", sorted(self.stop_nodes))
        meta["type_weights"] = self.type_weights

        # Light normalization for YouTube-style profiles so q doesn't saturate due to segment density
        profile = str(meta.get("profile") or meta.get("course_profile") or "").lower()
        if profile.startswith("youtube"):
            for step, feats in step_features.items():
                q = feats.get("quality")
                if isinstance(q, (int, float)):
                    qf = float(q)
                    edge_count = int(feats.get("edge_count") or 0)
                    # soft cap + slight penalty for very large per-step graphs
                    cap = 0.95
                    penalty = 1.0
                    if edge_count >= 400:
                        penalty = 0.94
                    elif edge_count >= 250:
                        penalty = 0.97
                    feats["quality"] = min(cap, qf * penalty)
                # Filter top_nodes to prefer content titles/phrases over filler tokens
                tn = feats.get("top_nodes") or []
                filtered = []
                for item in tn:
                    label = str(item.get("label") or "")
                    if not label:
                        continue
                    if _TOPNODE_ARTIFACT_RE.search(label):
                        continue
                    L = label.strip().lower()
                    if L in _TOPNODE_FILLER:
                        continue
                    # Prefer multi-word or colon/pipe separated titles; allow single tokens only if anchors
                    if (" " in label) or (":" in label) or ("|" in label):
                        filtered.append(item)
                    else:
                        if L in _SINGLE_TOKEN_ANCHORS:
                            filtered.append(item)
                # Keep at most 8
                feats["top_nodes"] = filtered[:8]

        return ProcessedStream(
            nodes=nodes,
            obs_steps=obs_steps,
            true_steps=true_steps,
            meta=meta,
            step_features=step_features,
            node_tags=node_tags,
            node_weights=node_weights,
        )

    def _infer_type(self, node_entry: Dict[str, object]) -> Tuple[str, float]:
        text = str(
            node_entry.get("label")
            or node_entry.get("title")
            or node_entry.get("kind")
            or ""
        ).strip()
        lower = text.lower()
        kind_lower = str(node_entry.get("kind", "")).strip().lower()

        rule = self._match_custom_rule(lower)
        if rule:
            tag = (rule.tag or rule.type).lower()
            return tag, rule.weight

        if kind_lower == "reading":
            return "reading", self.type_weights.get("reading", 0.85)
        if kind_lower == "segment":
            return "segment", self.type_weights.get("segment", 0.70)

        if any(rx.search(text) for rx in self.stop_re):
            return "media", self.type_weights.get("media", 0.05)

        nav_tokens = [
            "contact",
            "browse",
            "help",
            "faq",
            "about",
            "give now",
            "syllabus",
            "calendar",
            "download",
            "transcript",
            "video",
        ]
        if any(tok in lower for tok in nav_tokens):
            return "nav", self.type_weights.get("nav", 0.05)

        if any(term in lower for term in ["exam", "midterm", "final", "quiz", "test"]):
            return "exam", self.type_weights.get("exam", 0.7)

        if any(term in lower for term in ["problem set", "pset", "assignment", "homework"]):
            return "pset", self.type_weights.get("pset", 0.7)

        if any(term in lower for term in ["definition", "def.", "def "]):
            return "definition", self.type_weights.get("definition", 1.0)

        if any(term in lower for term in ["theorem", "lemma", "proposition", "corollary"]):
            return "theorem", self.type_weights.get("theorem", 1.0)

        if any(term in lower for term in ["prof.", "instructor", "jerison", "strang"]):
            return "person", self.type_weights.get("person", 0.3)

        concept_tokens = [
            "derivative",
            "integral",
            "series",
            "limit",
            "taylor",
            "chain rule",
            "hopital",
            "riemann",
            "differential",
            "ode",
            "ftc",
            "improper",
            "partial",
            "gradient",
        ]
        if any(tok in lower for tok in concept_tokens):
            return "concept", self.type_weights.get("concept", 1.0)

        return "unknown", self.type_weights.get("unknown", 0.5)

    def _match_custom_rule(self, lower: str) -> CurriculumTypeRule | None:
        for rule in self.custom_rules:
            if rule.pattern and re.search(rule.pattern, lower):
                return rule
            if rule.match and any(token in lower for token in rule.match):
                return rule
        return None

    def _keep_edge(self, edge: Edge, nodes: Dict[int, Dict[str, object]], node_weights: Dict[int, float]) -> bool:
        u, v = edge
        label_u = self._label_text(nodes.get(u))
        label_v = self._label_text(nodes.get(v))

        if label_u in self.stop_nodes or label_v in self.stop_nodes:
            return False
        if label_u.lower() in self.stop_nodes_lower or label_v.lower() in self.stop_nodes_lower:
            return False
        if any(rx.search(label_u) for rx in self.stop_re):
            return False
        if any(rx.search(label_v) for rx in self.stop_re):
            return False

        weight = min(self._node_weight(u, node_weights), self._node_weight(v, node_weights))
        return weight >= self.keep_threshold

    def _node_weight(self, node_id: int, node_weights: Dict[int, float]) -> float:
        return float(node_weights.get(node_id, self.type_weights.get("unknown", 0.5)))

    def _parse_metrics(self, node_entry: Dict[str, object]) -> Dict[str, float]:
        raw = node_entry.get("metrics")
        if not raw:
            return {}
        data = raw
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except (TypeError, ValueError):
                return {}
        if not isinstance(data, dict):
            return {}
        result = {}
        for key in ("views", "likes", "duration"):
            value = data.get(key)
            if isinstance(value, (int, float)):
                result[key] = float(value)
        return result

    def _cap_step(self, edges: List[Edge]) -> Frame:
        if not edges:
            return set()

        indexed_edges = list(enumerate(edges))
        indexed_edges.sort(key=lambda item: -item[0])

        deg_counts: Dict[int, int] = {}
        result: List[Edge] = []
        for _, (u, v) in indexed_edges:
            if deg_counts.get(u, 0) >= self.topk_per_node:
                continue
            if deg_counts.get(v, 0) >= self.topk_per_node:
                continue
            result.append((u, v))
            deg_counts[u] = deg_counts.get(u, 0) + 1
            deg_counts[v] = deg_counts.get(v, 0) + 1
        return set(result)

    def _label_text(self, node_entry: Dict[str, object] | None) -> str:
        if not node_entry:
            return ""
        return str(node_entry.get("label") or node_entry.get("title") or node_entry.get("kind") or "")

    # ------------------------------------------------------------------

    def _tags_for_type(self, ntype: str) -> Set[str]:
        mapping = {
            "concept": {"concept"},
            "definition": {"definition"},
            "theorem": {"theorem"},
            "segment": {"meta"},
            "assessment": {"assessment"},
            "exam": {"assessment", "exam"},
            "pset": {"assessment", "pset"},
            "reading": {"reading"},
            "nav": {"navigation"},
            "media": {"media"},
            "person": {"person"},
            "meta": {"meta"},
            "insight": {"meta"},
        }
        return set(mapping.get(ntype, {"concept"}))

    def _summarize_step(
        self,
        step: int,
        edges: Frame,
        node_tags: Dict[int, Set[str]],
        node_weights: Dict[int, float],
        labels: Dict[int, Dict[str, object]],
    ) -> Dict[str, object]:
        if not edges:
            return {
                "quality": 0.0,
                "stability": 1.0,
                "top_nodes": [],
                "commentary": "No curriculum updates recorded.",
                "counts": {},
                "nav_noise": 0.0,
                "concept_fraction": 0.0,
                "assessment_fraction": 0.0,
                "reading_fraction": 0.0,
                "meta_fraction": 0.0,
                "edge_count": 0,
                "step_type": "empty",
                "weighted_node_mass": 0.0,
                "unique_node_count": 0,
                "avg_views": 0.0,
                "avg_duration": 0.0,
                "engagement_score": 0.0,
            }

        step_nodes: Set[int] = {n for edge in edges for n in edge}
        counts: Dict[str, int] = {
            "concept": 0,
            "definition": 0,
            "theorem": 0,
            "reading": 0,
            "assessment": 0,
            "navigation": 0,
            "media": 0,
            "meta": 0,
            "other": 0,
        }
        weight_totals: Dict[str, float] = {key: 0.0 for key in counts}
        node_scores: List[Tuple[float, int, str]] = []
        weighted_node_mass = 0.0
        metrics_totals = {"views": 0.0, "likes": 0.0, "duration": 0.0}
        metrics_count = 0

        for node_id in step_nodes:
            tags = node_tags.get(node_id, {"other"})
            categories_seen: Set[str] = set()
            base_weight = node_weights.get(node_id, 1.0)
            weighted_node_mass += base_weight
            score = 0.0
            for tag in tags:
                if tag == "concept":
                    categories_seen.add("concept")
                    score += 1.0
                elif tag == "definition":
                    categories_seen.add("definition")
                    score += 0.9
                elif tag == "theorem":
                    categories_seen.add("theorem")
                    score += 0.95
                elif tag in {"assessment", "exam", "pset"}:
                    categories_seen.add("assessment")
                    score += 0.8
                elif tag == "reading":
                    categories_seen.add("reading")
                    score += 0.85
                elif tag in {"navigation", "nav"}:
                    categories_seen.add("navigation")
                    score -= 0.4
                elif tag == "media":
                    categories_seen.add("media")
                    score -= 0.6
                elif tag == "meta":
                    categories_seen.add("meta")
                    score += 0.1
                else:
                    categories_seen.add("other")
                    score += 0.2
            for category in categories_seen:
                counts[category] += 1
                weight_totals[category] += base_weight
            label_entry = labels.get(node_id, {})
            label_text = str(
                label_entry.get("label")
                or label_entry.get("title")
                or label_entry.get("concept")
                or node_id
            )
            # Content-oriented boost: prefer multiword titles/phrases and known anchors
            lt = (label_text or "").strip().lower()
            if (":" in lt) or ("|" in lt) or (" " in lt and len(lt) >= 10):
                score += 0.15
            else:
                # single token: small boost only for anchors
                if lt in _SINGLE_TOKEN_ANCHORS:
                    score += 0.08
            node_scores.append((score, node_id, label_text))
            metrics_payload = self._parse_metrics(label_entry)
            if metrics_payload:
                metrics_count += 1
                for key in metrics_totals:
                    metrics_totals[key] += metrics_payload.get(key, 0.0)

        total_weight = max(1.0, sum(weight_totals.values()))
        concept_focus = (
            weight_totals["concept"]
            + 0.8 * weight_totals["definition"]
            + 0.9 * weight_totals["theorem"]
            + 0.7 * weight_totals["reading"]
            + 0.4 * weight_totals["other"]
        )
        assessment_focus = weight_totals["assessment"]
        meta_noise = weight_totals["navigation"] + weight_totals["media"] + weight_totals["meta"]

        quality = min(1.0, (concept_focus + 0.6 * assessment_focus) / total_weight)
        ted_noise = max(0.0, min(1.0, meta_noise / total_weight))
        stability = max(0.0, min(1.0, quality - 0.3 * ted_noise))

        node_scores.sort(key=lambda pair: (-pair[0], pair[2]))
        # Filter top nodes: drop media/meta/navigation/segment and artifact labels/fillers
        def _accept_top(node_id: int, label_text: str) -> bool:
            tags = node_tags.get(node_id, set()) or set()
            if {'media', 'navigation'} & tags:
                return False
            if 'meta' in tags and 'concept' not in tags:
                return False
            if _TOPNODE_ARTIFACT_RE.search(label_text or ''):
                return False
            if label_text and label_text.strip().lower() in _TOPNODE_FILLER:
                return False
            return True

        top_nodes: List[Dict[str, object]] = []
        for score, node_id, label_text in node_scores:
            if len(top_nodes) >= 8:
                break
            if not _accept_top(node_id, label_text):
                continue
            display = labels.get(node_id, {}).get("label") or labels.get(node_id, {}).get("title") or str(node_id)
            top_nodes.append(
                {
                    "id": node_id,
                    "label": display,
                    "tags": sorted(node_tags.get(node_id, {"other"})),
                    "score": round(score, 3),
                }
            )

        fractions = {
            "concept_fraction": round(weight_totals["concept"] / total_weight, 3),
            "assessment_fraction": round(weight_totals["assessment"] / total_weight, 3),
            "reading_fraction": round(weight_totals["reading"] / total_weight, 3),
            "meta_fraction": round(meta_noise / total_weight, 3),
        }

        avg_views = metrics_totals["views"] / metrics_count if metrics_count else 0.0
        avg_duration = metrics_totals["duration"] / metrics_count if metrics_count else 0.0
        avg_likes = metrics_totals["likes"] / metrics_count if metrics_count else 0.0
        like_ratio = avg_likes / max(avg_views, 1.0) if metrics_count else 0.0
        engagement_score = (avg_views * 0.001) + like_ratio if metrics_count else 0.0

        step_type, commentary = self._classify_step_focus(
            quality=quality,
            concept_fraction=fractions["concept_fraction"],
            assessment_fraction=fractions["assessment_fraction"],
            reading_fraction=fractions["reading_fraction"],
            meta_fraction=fractions["meta_fraction"],
            nav_noise=ted_noise,
            edge_count=len(edges),
        )

        counts_summary = {
            "concept": counts["concept"],
            "definition": counts["definition"],
            "theorem": counts["theorem"],
            "reading": counts["reading"],
            "assessment": counts["assessment"],
            "navigation": counts["navigation"],
            "media": counts["media"],
            "meta": counts["meta"],
            "other": counts["other"],
        }

        return {
            "quality": round(quality, 3),
            "stability": round(stability, 3),
            "top_nodes": top_nodes,
            "commentary": commentary,
            "counts": counts_summary,
            "nav_noise": round(ted_noise, 3),
            "edge_count": len(edges),
            "step_type": step_type,
            "weighted_node_mass": round(weighted_node_mass, 3),
            "unique_node_count": len(step_nodes),
            "avg_views": round(avg_views, 3),
            "avg_duration": round(avg_duration, 3),
            "engagement_score": round(engagement_score, 3),
            **fractions,
        }

    def _classify_step_focus(
        self,
        *,
        quality: float,
        concept_fraction: float,
        assessment_fraction: float,
        reading_fraction: float,
        meta_fraction: float,
        nav_noise: float,
        edge_count: int,
    ) -> Tuple[str, str]:
        if edge_count == 0 or quality <= 0.0:
            return "empty", "No curriculum updates recorded."
        if assessment_fraction >= 0.35 and concept_fraction >= 0.2:
            return (
                "checkpoint",
                f"Major checkpoint week; assessments tightly coupled to concepts (q={quality:.2f}).",
            )
        if concept_fraction >= 0.55 and assessment_fraction <= 0.25:
            return (
                "concept_dense",
                f"Concept-dense window; focus on core material (concept share={concept_fraction:.2f}).",
            )
        if reading_fraction >= 0.45 and assessment_fraction <= 0.2:
            return (
                "reading_heavy",
                f"Reading-heavy week; emphasize synthesis (reading share={reading_fraction:.2f}).",
            )
        if meta_fraction >= 0.3 or nav_noise >= 0.45:
            return (
                "transition",
                "Transition/structural week; navigation or meta content dominates.",
            )
        return "mixed", "Curriculum window progressing normally."
