"""
VectorDB-backed incident cache lookup (Chroma)
----------------------------------------------

Given an incident report string, check for near-duplicates in a Chroma collection
and return the associated root cause from row metadata. This replaces the earlier
spaCy/CSV similarity implementation. For compatibility, the public API remains the
same, and the function will fall back to the CSV method if the vector DB is not
available.

Collections expected (built by build_vector_db.py):
- incidents_cache: embeddings of the 'Incident_Report' column of consolidated_incidents.csv
    with per-row metadata including 'Root_Cause'.

Default CSV path (used for fallback and for metadata display):
data/processed-data/consolidated_incidents.csv (relative to this file).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Vector DB utils (preferred path)
try:
    from .vector_db_utils import (
        DEFAULT_DB_DIR,
        query_collection,
    )

    _VDB_AVAILABLE = True
except Exception:
    _VDB_AVAILABLE = False

# Fallback spaCy utilities (kept for backward compatibility if Chroma not present)
try:
    import spacy
except Exception:
    spacy = None  # type: ignore


# ---------------------------
# spaCy model load utilities
# ---------------------------
_NLP = None


def _load_spacy():
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
        if spacy is None:  # pragma: no cover
            raise RuntimeError("spaCy is not installed")
        _NLP = spacy.load("en_core_web_md")
    except OSError:
        # Try to download the medium model; if it fails, fall back to small
        try:
            import subprocess  # pragma: no cover

            subprocess.run(
                ["python", "-m", "spacy", "download", "en_core_web_md"], check=False
            )
            _NLP = spacy.load("en_core_web_md")
        except Exception:
            _NLP = spacy.load("en_core_web_sm")
    return _NLP


# ---------------------------
# Text preprocessing and caches
# ---------------------------
_doc_cache: Dict[str, object] = {}
_phrase_cache: Dict[str, List[str]] = {}
_sim_cache: Dict[Tuple[str, str], float] = {}


def _get_doc(text: str):
    nlp = _load_spacy()
    if text in _doc_cache:
        return _doc_cache[text]
    d = nlp(text)
    _doc_cache[text] = d
    return d


def clean_text(text: object) -> str:
    """Clean text by removing variable details while preserving problem description.

    Mirrors the notebook's logic: remove timestamps, long numbers/IDs, ticket refs,
    and extra whitespace; lowercase the result.
    """
    if text is None:
        return ""
    s = str(text)

    # Dates/times
    s = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "[DATE]", s)  # 2025-10-18
    s = re.sub(
        r"\b\d{1,2}[:/\-]\d{1,2}[:/\-]\d{2,4}\b", "[DATE]", s
    )  # 10/18/2025, 18-10-25
    s = re.sub(
        r"\b\d{1,2}:\d{2}(:\d{2})?(\s?[AaPp][Mm])?\b", "[TIME]", s
    )  # 10:30, 10:30 AM

    # IDs and ticket numbers
    s = re.sub(r"\b[A-Z]{2,}\d+\b", "[ID]", s)  # INC123, REQ456, ALR-12345 (partial)
    s = re.sub(r"\b\d{5,}\b", "[ID]", s)  # long numbers
    s = re.sub(r"#\d+", "[ID]", s)  # #12345

    # Standalone numbers
    s = re.sub(r"\s\d+\s", " ", s)
    s = re.sub(r"^\d+\s", "", s)
    s = re.sub(r"\s\d+$", "", s)

    # Normalize whitespace and case
    s = re.sub(r"\s+", " ", s).strip()
    return s.lower()


def get_phrases(cleaned_text: str) -> List[str]:
    """Split cleaned text into meaningful phrases (sentences). Cached."""
    if not cleaned_text:
        return []
    if cleaned_text in _phrase_cache:
        return _phrase_cache[cleaned_text]
    doc = _get_doc(cleaned_text)
    phrases: List[str] = []
    for sent in doc.sents:
        phrase = sent.text.strip()
        if len(phrase.split()) >= 2:
            phrases.append(phrase)
    _phrase_cache[cleaned_text] = phrases
    return phrases


def calculate_phrase_similarity(a: str, b: str) -> float:
    """Average best-match phrase similarity between two texts (0..1).

    - Clean inputs
    - Split into sentences (phrases)
    - For each phrase in A, take max similarity with any phrase in B
    - Average those maxima
    - Cache by cleaned pair (order-independent)
    """
    ca = clean_text(a)
    cb = clean_text(b)
    if not ca or not cb:
        return 0.0

    # Order-independent cache key
    key = (ca, cb) if ca <= cb else (cb, ca)
    if key in _sim_cache:
        return _sim_cache[key]

    p1 = get_phrases(ca)
    p2 = get_phrases(cb)

    if not p1 or not p2:
        d1 = _get_doc(ca)
        d2 = _get_doc(cb)
        sim = float(d1.similarity(d2))
        _sim_cache[key] = sim
        return sim

    sims: List[float] = []
    for s1 in p1:
        d1 = _get_doc(s1)
        best = 0.0
        for s2 in p2:
            d2 = _get_doc(s2)
            best = max(best, float(d1.similarity(d2)))
        if best:
            sims.append(best)

    avg = float(np.mean(sims)) if sims else 0.0
    _sim_cache[key] = avg
    return avg


# ---------------------------
# Dataset cache (mtime-aware)
# ---------------------------
_dataset_cache = {
    "path": None,  # type: Optional[Path]
    "mtime": None,  # type: Optional[float]
    "rows": None,  # type: Optional[List[Dict[str, str]]]
}


def _default_csv_path() -> Path:
    return (
        Path(__file__).parent / "data" / "processed-data" / "consolidated_incidents.csv"
    ).resolve()


def _load_dataset(
    csv_path: Optional[Path] = None,
) -> Tuple[List[Dict[str, str]], float]:
    """Load consolidated CSV into memory with mtime for cache invalidation.

    Returns (rows, mtime). Each row contains keys: 'Incident_Report', 'Root_Cause'.
    """
    path = Path(csv_path) if csv_path is not None else _default_csv_path()
    if not path.exists():
        raise FileNotFoundError(f"Consolidated CSV not found at: {path}")

    mtime = path.stat().st_mtime
    if (
        _dataset_cache["path"] == path
        and _dataset_cache["mtime"] == mtime
        and _dataset_cache["rows"] is not None
    ):
        return _dataset_cache["rows"], mtime

    df = pd.read_csv(path, encoding="utf-8")

    # Validate required columns
    expected_cols = {"Incident_Report", "Root_Cause"}
    missing = expected_cols - set(df.columns)
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    # Drop null/empty
    df = df.dropna(subset=["Incident_Report", "Root_Cause"]).copy()
    df["Incident_Report"] = df["Incident_Report"].astype(str).str.strip()
    df["Root_Cause"] = df["Root_Cause"].astype(str).str.strip()
    df = df[(df["Incident_Report"] != "") & (df["Root_Cause"] != "")]

    # Precompute cleaned text for faster comparisons
    rows: List[Dict[str, str]] = []
    for _, r in df.iterrows():
        ir = r["Incident_Report"]
        rc = r["Root_Cause"]
        cleaned = clean_text(ir)
        rows.append(
            {
                "Incident_Report": ir,
                "Root_Cause": rc,
                "_clean": cleaned,
                # phrases will be computed lazily via get_phrases cache
            }
        )

    _dataset_cache.update({"path": path, "mtime": mtime, "rows": rows})
    return rows, mtime


# ---------------------------
# Query result cache
# ---------------------------
_query_result_cache: Dict[Tuple[str, float, float], Optional[str]] = {}


def get_root_cause_for_incident(
    incident_report: str,
    csv_path: Optional[Path | str] = None,
    similarity_threshold: float = 0.90,
) -> Optional[str]:
    """Return the root cause for a given incident by semantic match or None.

    Preferred path: Query Chroma collection 'incidents_cache' and accept a hit
    if cosine distance implies similarity >= threshold. Fallback path: CSV+spaCy
    phrase similarity (legacy). The threshold is interpreted the same way for both
    paths as a similarity in [0,1].
    """
    if incident_report is None or str(incident_report).strip() == "":
        return None

    # Try vector DB first
    if _VDB_AVAILABLE:
        try:
            # Query the collection
            result = query_collection(
                collection_name="incidents_cache",
                query_text=str(incident_report),
                k=5,
                db_dir=DEFAULT_DB_DIR,
            )

            # Chroma returns distances (smaller is closer). We used normalized embeddings,
            # which makes cosine distance = 1 - cosine similarity.
            distances = result.get("distances", [[]])[0] if result else []
            metas = result.get("metadatas", [[]])[0] if result else []

            best_match_cause: Optional[str] = None
            best_sim = -1.0
            for dist, meta in zip(distances, metas):
                if dist is None:
                    continue
                sim = 1.0 - float(dist)
                if sim >= similarity_threshold and sim > best_sim:
                    best_sim = sim
                    # Expect Root_Cause in metadata; if missing, try to be resilient
                    rc = meta.get("Root_Cause") if isinstance(meta, dict) else None
                    best_match_cause = str(rc) if rc is not None else None

            # Cache by current dataset mtime surrogate: use 0.0 because Chroma persists
            cleaned_incident = clean_text(incident_report)
            cache_key = (cleaned_incident, float(similarity_threshold), 0.0)
            _query_result_cache[cache_key] = best_match_cause
            if best_match_cause is not None:
                return best_match_cause
        except Exception:
            # Fall through to CSV fallback
            pass

    # Fallback to legacy CSV+spaCy
    rows, mtime = _load_dataset(Path(csv_path) if csv_path is not None else None)

    cleaned_incident = clean_text(incident_report)
    cache_key = (cleaned_incident, float(similarity_threshold), float(mtime))
    if cache_key in _query_result_cache:
        return _query_result_cache[cache_key]

    best_match_cause: Optional[str] = None
    best_score = -1.0
    for r in rows:
        score = calculate_phrase_similarity(cleaned_incident, r["_clean"])  # type: ignore[arg-type]
        if score >= similarity_threshold and score > best_score:
            best_score = score
            best_match_cause = r["Root_Cause"]

    _query_result_cache[cache_key] = best_match_cause
    return best_match_cause


def clear_caches() -> None:
    """Clear all in-memory caches (docs, phrases, similarities, dataset, query)."""
    _doc_cache.clear()
    _phrase_cache.clear()
    _sim_cache.clear()
    _dataset_cache.update({"path": None, "mtime": None, "rows": None})
    _query_result_cache.clear()


if __name__ == "__main__":  # Manual quick test (optional)
    # Adjust this incident string to try different lookups without importing this file.
    test_incident = "Database connection failed for order #12345 at 10:30 AM"
    try:
        cause = get_root_cause_for_incident(test_incident)
        print("Match:", bool(cause))
        print("Root Cause:", cause)
    except Exception as exc:  # pragma: no cover
        print("Error:", exc)
