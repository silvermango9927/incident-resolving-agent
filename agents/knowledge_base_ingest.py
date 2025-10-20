from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
from .utils.bootstrap import bootstrap_analyzer_helpers

"""
Knowledge base ingestion: load PDFs from knowledge_base/ into Chroma collection
`kb_docs` and provide a simple query interface.
"""


def iter_pdf_texts(kb_dir: Path) -> List[Dict[str, Any]]:
    try:
        from pypdf import PdfReader  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("Please install pypdf for PDF loading.") from e
    items: List[Dict[str, Any]] = []
    for pdf in kb_dir.glob("*.pdf"):
        reader = PdfReader(str(pdf))
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            text = text.strip()
            if not text:
                continue
            items.append(
                {
                    "id": f"{pdf.name}::p{i}",
                    "document": text,
                    "metadata": {"file": pdf.name, "page": i},
                }
            )
    return items


def index_kb_pdfs(
    kb_dir: Path,
    *,
    collection_name: str = "kb_docs",
    db_dir: Optional[Path] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> None:
    # Lazy import to ensure bootstrap works across environments
    bootstrap_analyzer_helpers(Path(__file__).parent)
    from analyzer_helpers.vector_db_utils import get_client, Embedder  # type: ignore

    client = get_client(db_dir)
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    col = client.create_collection(collection_name)
    embedder = Embedder(model_name)
    items = iter_pdf_texts(kb_dir)
    if not items:
        return
    CHUNK = 256
    for s in range(0, len(items), CHUNK):
        batch = items[s : s + CHUNK]
        texts = [b["document"] for b in batch]
        embeddings = embedder.encode(texts)
        col.add(
            ids=[b["id"] for b in batch],
            documents=texts,
            embeddings=embeddings,
            metadatas=[b["metadata"] for b in batch],
        )


def query_kb(
    query: str,
    *,
    k: int = 5,
    collection_name: str = "kb_docs",
    db_dir: Optional[Path] = None,
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> Dict[str, Any]:
    bootstrap_analyzer_helpers(Path(__file__).parent)
    from analyzer_helpers.vector_db_utils import get_or_create_collection, Embedder  # type: ignore

    col = get_or_create_collection(collection_name, db_dir)
    emb = Embedder(model_name).encode([query])[0]
    return col.query(
        query_embeddings=[emb],
        n_results=k,
        include=["documents", "metadatas", "distances", "ids"],
    )
