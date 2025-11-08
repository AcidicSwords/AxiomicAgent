from __future__ import annotations

from typing import List, Optional


def encode_texts(texts: List[str], model_name: str = "all-MiniLM-L6-v2"):
    """Return sentence embeddings for texts using sentence-transformers if available.

    Falls back to simple bag-of-words hash embeddings if transformers are not installed.
    """
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        model = SentenceTransformer(model_name)
        return model.encode(texts, normalize_embeddings=True)
    except Exception:
        # Lightweight fallback: hash-based vectors
        import numpy as np
        vecs = []
        for t in texts:
            words = (t or "").lower().split()
            # 64-dim simple hash embedding
            v = np.zeros(64, dtype=float)
            for w in words[:32]:
                h = hash(w) % 64
                v[h] += 1.0
            n = np.linalg.norm(v)
            if n > 0:
                v = v / n
            vecs.append(v)
        return vecs

