from __future__ import annotations
from pathlib import Path
from agents.knowledge_base_ingest import index_kb_pdfs
from agents.utils.bootstrap import bootstrap_analyzer_helpers


def cli():  # pragma: no cover
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, required=True)
    p.add_argument("--kb", type=Path, default=Path("knowledge_base"))
    args = p.parse_args()
    # Expose analyzer-helpers as package 'analyzer_helpers'
    from pathlib import Path as _P

    bootstrap_analyzer_helpers(_P(__file__).resolve().parents[1] / "agents")
    from analyzer_helpers.build_vector_db import main as build_vdb  # type: ignore

    build_vdb(args.csv)
    index_kb_pdfs(args.kb)


if __name__ == "__main__":
    cli()
