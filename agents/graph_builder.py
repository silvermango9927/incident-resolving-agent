from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json

import pandas as pd
import networkx as nx


def build_graph_from_incidents(
    csv_path: Path, out_path: Path | None = None
) -> Dict[str, Any]:
    df = pd.read_csv(csv_path)
    g = nx.DiGraph()

    comp_col = None
    for c in ["Component", "component", "Service", "service"]:
        if c in df.columns:
            comp_col = c
            break

    cause_col = None
    for c in ["Root_Cause", "Cause", "root_cause"]:
        if c in df.columns:
            cause_col = c
            break

    if comp_col is None and cause_col is None:
        # Nothing to extract
        data = {"nodes": [], "edges": []}
        if out_path:
            Path(out_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
        return data

    for _, row in df.iterrows():
        comp = str(row.get(comp_col, "")).strip() if comp_col else ""
        cause = str(row.get(cause_col, "")).strip() if cause_col else ""
        if comp:
            g.add_node(comp, type="component", label=comp)
        if cause:
            g.add_node(cause, type="cause", label=cause)
        if comp and cause:
            g.add_edge(cause, comp, relation="affects")

    data = {
        "nodes": [{"id": n, **g.nodes[n]} for n in g.nodes],
        "edges": [{"src": u, "dst": v, **g.edges[u, v]} for u, v in g.edges],
    }
    if out_path:
        Path(out_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data
