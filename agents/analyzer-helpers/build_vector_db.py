"""
Build Chroma vector DB collections from processed CSVs.

Collections produced:
- incidents_cache: from consolidated_incidents.csv, column 'Incident_Report'
- problems_cache: from consolidated_incidents.csv, column 'Problems_Identified' (if present)

Usage (not executed automatically):
  python -m agents.analyzer-helpers.build_vector_db --csv path/to/consolidated_incidents.csv

The script is idempotent: it recreates the collections on each run.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .vector_db_utils import build_chroma_collection_from_csv, DEFAULT_DB_DIR


def main(
    csv: Path,
    db_dir: Optional[Path] = None,
    model: str = "sentence-transformers/all-MiniLM-L6-v2",
) -> None:
    db_dir = db_dir or DEFAULT_DB_DIR
    # incidents_cache
    build_chroma_collection_from_csv(
        collection_name="incidents_cache",
        csv_path=csv,
        text_column="Incident_Report",
        id_column="id" if False else None,  # plug if you add a stable id column later
        db_dir=db_dir,
        model_name=model,
    )

    # problems_cache (optional)
    try:
        build_chroma_collection_from_csv(
            collection_name="problems_cache",
            csv_path=csv,
            text_column="Problems_Identified",
            id_column="id" if False else None,
            db_dir=db_dir,
            model_name=model,
        )
    except Exception:
        # Column may not exist in early datasets; skip gracefully
        pass


if __name__ == "__main__":  # pragma: no cover
    p = argparse.ArgumentParser()
    p.add_argument(
        "--csv", type=Path, required=True, help="Path to consolidated_incidents.csv"
    )
    p.add_argument(
        "--db-dir", type=Path, default=None, help="Chroma persistent directory"
    )
    p.add_argument(
        "--model",
        type=str,
        default="sentence-transformers/all-MiniLM-L6-v2",
        help="SentenceTransformer model name",
    )
    args = p.parse_args()
    main(args.csv, args.db_dir, args.model)
