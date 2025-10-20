"""
Remediation cache: detect duplicates for 'Problems_Identified' using the Chroma
collection `problems_cache`. Returns the associated recommended actions/solution
fields from metadata when available.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any

try:
    from .vector_db_utils import DEFAULT_DB_DIR, query_collection
except Exception as e:  # pragma: no cover
    raise RuntimeError("Chroma vector DB not available; build the DB first.") from e


def find_similar_problem(
    problem_text: str,
    *,
    k: int = 5,
    similarity_threshold: float = 0.90,
    db_dir: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    if not problem_text or not str(problem_text).strip():
        return None
    result = query_collection(
        collection_name="problems_cache",
        query_text=str(problem_text),
        k=k,
        db_dir=db_dir or DEFAULT_DB_DIR,
    )
    distances = result.get("distances", [[]])[0] if result else []
    metas = result.get("metadatas", [[]])[0] if result else []
    best = None
    best_sim = -1.0
    for dist, meta in zip(distances, metas):
        if dist is None:
            continue
        sim = 1.0 - float(dist)
        if sim >= similarity_threshold and sim > best_sim:
            best_sim = sim
            best = meta
    return best
