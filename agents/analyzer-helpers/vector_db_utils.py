"""
Utilities for building and querying Chroma-based vector databases for the
incident resolving agents. Designed to be lightweight and local-first.

Key collections (default names):
- incidents_cache: Embeddings for Incident_Report (cause analysis duplicate checking)
- problems_cache: Embeddings for Problems_Identified (remediation duplicate checking)
- kb_docs: Embeddings for PDF knowledge base chunks

All collections live under a single persistent directory so that separate
agents can reuse them without re-embedding.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

import pandas as pd

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:  # pragma: no cover
    raise RuntimeError("Please install chromadb to use the vector DB utilities.") from e

try:
    from sentence_transformers import SentenceTransformer
except Exception as e:  # pragma: no cover
    raise RuntimeError(
        "Please install sentence-transformers to compute embeddings."
    ) from e


DEFAULT_DB_DIR = (
    Path(__file__).parent / "data" / "processed-data" / "vector-db"
).resolve()


def _ensure_db_dir(db_dir: Optional[Path] = None) -> Path:
    d = Path(db_dir) if db_dir is not None else DEFAULT_DB_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_client(db_dir: Optional[Path] = None) -> "chromadb.Client":
    base = _ensure_db_dir(db_dir)
    client = chromadb.Client(
        Settings(
            is_persistent=True,
            persist_directory=str(base),
        )
    )
    return client


def get_or_create_collection(
    name: str,
    db_dir: Optional[Path] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    client = get_client(db_dir)
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(name=name, metadata=metadata or {})


@dataclass
class Embedder:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    _model: Optional[SentenceTransformer] = None

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: List[str]) -> List[List[float]]:
        model = self._load()
        # Use normalize_embeddings for better cosine search behavior
        return model.encode(texts, normalize_embeddings=True).tolist()


def _read_csv_column(
    csv_path: Path, text_column: str, id_column: Optional[str] = None
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    df = pd.read_csv(csv_path)
    if text_column not in df.columns:
        raise ValueError(
            f"Column '{text_column}' not found in CSV. Available: {list(df.columns)}"
        )
    texts: List[str] = []
    ids: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    for idx, row in df.iterrows():
        txt = str(row[text_column]).strip()
        if not txt:
            continue
        doc_id = (
            str(row[id_column]) if id_column and id_column in df.columns else str(idx)
        )
        meta = {k: (None if pd.isna(v) else v) for k, v in row.to_dict().items()}
        texts.append(txt)
        ids.append(doc_id)
        metadatas.append(meta)
    return texts, ids, metadatas


def build_chroma_collection_from_csv(
    *,
    collection_name: str,
    csv_path: Path,
    text_column: str,
    id_column: Optional[str] = None,
    db_dir: Optional[Path] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> None:
    """Create or refresh a Chroma collection from a CSV column.

    This overwrites existing docs in the collection by deleting and recreating it,
    keeping the DB directory intact for other collections.
    """
    client = get_client(db_dir)
    # Drop if exists to avoid ID collisions when rows changed
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass

    collection = client.create_collection(name=collection_name)
    embedder = Embedder(model_name)
    texts, ids, metadatas = _read_csv_column(csv_path, text_column, id_column)

    if not texts:
        return

    # Chunk inserts to avoid large payloads
    CHUNK = 512
    for start in range(0, len(texts), CHUNK):
        batch_texts = texts[start : start + CHUNK]
        batch_ids = ids[start : start + CHUNK]
        batch_metas = metadatas[start : start + CHUNK]
        embeddings = embedder.encode(batch_texts)
        collection.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metas,
        )


def query_collection(
    *,
    collection_name: str,
    query_text: str,
    k: int = 5,
    db_dir: Optional[Path] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, Any]:
    """Query a collection by text using cosine similarity.

    Returns a dict containing distances, ids, documents, and metadatas.
    """
    collection = get_or_create_collection(collection_name, db_dir=db_dir)
    embedder = Embedder(model_name)
    q_emb = embedder.encode([query_text])[0]
    result = collection.query(
        query_embeddings=[q_emb],
        n_results=k,
        include=["distances", "metadatas", "documents", "ids"],
    )
    return result
