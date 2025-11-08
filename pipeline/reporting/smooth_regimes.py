#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List


def _load_series(fp: Path) -> List[dict]:
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("series") or data.get("steps") or []
    except Exception:
        return []


def _classify_basic(q: float, ted: float, cont: float) -> str:
    if ted >= 0.65 and cont <= 0.2:
        return "pivot"
    if q >= 0.85 and ted <= 0.25 and cont >= 0.4:
        return "checkpoint"
    if q >= 0.8 and cont >= 0.3:
        return "concept_dense"
    if q <= 0.4 and ted >= 0.5:
        return "scattered"
    if ted >= 0.4 and cont <= 0.25:
        return "exploring"
    return "mixed"


def _mode_smooth(labels: List[str], window: int = 3) -> List[str]:
    if not labels:
        return []
    out = []
    n = len(labels)
    half = window // 2
    for i in range(n):
        l = max(0, i - half)
        r = min(n, i + half + 1)
        win = labels[l:r]
        # mode
        best = max(set(win), key=win.count)
        out.append(best)
    return out


def _smooth_labels(series: List[dict]) -> List[str]:
    try:
        import numpy as np
        import ruptures as rpt  # type: ignore
        from pomegranate import HiddenMarkovModel, NormalDistribution  # type: ignore
    except Exception:
        # Fallback: compute labels from thresholds and smooth by majority vote
        base = []
        for s in series:
            q = float(s.get("q") or s.get("mean_q") or 0.0)
            ted = float(s.get("TED") or s.get("mean_ted") or 0.0)
            cont = float(s.get("continuity") or 0.0)
            base.append(_classify_basic(q, ted, cont))
        return _mode_smooth(base, window=5)

    if not series:
        return []
    # Build feature matrix [q, TED, continuity, spread]
    X = []
    for s in series:
        X.append([
            float(s.get("q") or s.get("mean_q") or 0.0),
            float(s.get("TED") or s.get("mean_ted") or 0.0),
            float(s.get("continuity") or 0.0),
            float(s.get("spread") or 0.0),
        ])
    import numpy as np
    X = np.asarray(X, dtype=float)
    # Change points via ruptures
    try:
        algo = rpt.Binseg(model="rbf").fit(X)
        n_bkps = max(1, min(len(X)//10, 8))
        bkps = algo.predict(n_bkps=n_bkps)
    except Exception:
        bkps = [len(X)]
    # Simple HMM with 5 regimes
    try:
        from pomegranate import GeneralMixtureModel
        # Build 5 Gaussian components for q only as proxy (keep simple)
        qs = X[:, 0]
        mus = np.linspace(qs.min(), qs.max(), 5) if qs.size else [0.2,0.4,0.6,0.8,0.9]
        dists = [NormalDistribution(m, 0.1) for m in mus]
        model = HiddenMarkovModel.from_matrix(
            transition_probabilities=[[0.7,0.075,0.075,0.075,0.075]]*5,
            distributions=dists,
            starts=[0.2]*5,
            state_names=["scattered","exploring","mixed","concept_dense","checkpoint"],
        )
        states = model.predict(qs.tolist()) if qs.size else [2]*len(X)
        names = model.state_names
        labels = [names[s] if s < len(names) else "mixed" for s in states]
        return labels
    except Exception:
        base = [_classify_basic(float(s.get("q") or s.get("mean_q") or 0.0),
                                 float(s.get("TED") or s.get("mean_ted") or 0.0),
                                 float(s.get("continuity") or 0.0)) for s in series]
        return _mode_smooth(base, window=5)


def main() -> None:
    ap = argparse.ArgumentParser(description="Smooth regime labels for dynamics series")
    ap.add_argument("--dynamics-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    src = Path(args.dynamics_dir)
    dst = Path(args.out_dir)
    dst.mkdir(parents=True, exist_ok=True)

    for fp in src.glob("*_curriculum_dynamics.json"):
        series = _load_series(fp)
        labels = _smooth_labels(series)
        out = {"file": fp.name, "smoothed_step_type": labels}
        (dst / (fp.stem + ".smoothed.json")).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
