"""
spaCy-based incident cache lookup
---------------------------------

Given an incident report string, check if it is present (by semantic similarity)
in the consolidated CSV and return the associated root cause.

Rules/behavior:
- Compare against 'Incident_Report' in consolidated_incidents.csv using phrase-level
  similarity with spaCy and a 0.90 threshold (same as the notebook pipeline).
- If any consolidated incident matches, return its 'Root_Cause'. Otherwise, return None.
- Implements multiple caches to avoid re-processing text and repeated IO:
  - spaCy Doc cache
  - Phrase list cache
  - Pairwise similarity cache
  - Dataset cache (file mtime-aware)
  - Query result cache keyed by (cleaned_incident, threshold, dataset_mtime)

Default CSV path: data/processed-data/consolidated_incidents.csv (relative to this file).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import spacy
except Exception as e:  # pragma: no cover - environment-specific
    raise RuntimeError("spaCy must be installed for cache-requests to function") from e


# ---------------------------
# spaCy model load utilities
# ---------------------------
_NLP = None


def _load_spacy() -> "spacy.Language":
    global _NLP
    if _NLP is not None:
        return _NLP
    try:
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
_doc_cache: Dict[str, "spacy.tokens.Doc"] = {}
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

    - incident_report: New incident text to look up.
    - csv_path: Optional override path to consolidated_incidents.csv.
    - similarity_threshold: Default 0.90 to match the notebook pipeline.
    """
    if incident_report is None or str(incident_report).strip() == "":
        return None

    rows, mtime = _load_dataset(Path(csv_path) if csv_path is not None else None)

    cleaned_incident = clean_text(incident_report)
    cache_key = (cleaned_incident, float(similarity_threshold), float(mtime))
    if cache_key in _query_result_cache:
        return _query_result_cache[cache_key]

    # Compare against each consolidated incident
    best_match_cause: Optional[str] = None
    best_score = -1.0

    for r in rows:
        score = calculate_phrase_similarity(
            cleaned_incident, r["_clean"]
        )  # compare cleaned-to-cleaned
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
