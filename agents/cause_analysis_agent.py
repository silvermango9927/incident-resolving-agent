from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from .knowledge_base_ingest import query_kb
from .utils.bootstrap import bootstrap_analyzer_helpers

"""
Cause Analysis Agent
--------------------
Implements the flow:
- Caching system (via Chroma incidents_cache)
- Search through knowledge base (PDF chunks)
- Cause development (GCRNN placeholder with train/infer scaffolding)
- Ranking causes (weighted fusion)
"""


@dataclass
class CauseCandidate:
    label: str
    score: float
    evidence: str = ""


class CauseAnalysisAgent:
    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).parent / "analyzer-helpers" / "data"
        )

    # 1) Cache check (duplicate detection -> root cause)
    def cache_lookup(
        self, incident_report: str, threshold: float = 0.90
    ) -> Optional[str]:
        # Lazy import to avoid bootstrap at import-time
        bootstrap_analyzer_helpers(Path(__file__).parent)
        from analyzer_helpers.cache_requests import get_root_cause_for_incident  # type: ignore

        return get_root_cause_for_incident(
            incident_report, similarity_threshold=threshold
        )

    # 2) Knowledge base search: stub that returns empty
    def kb_search(self, incident_report: str, k: int = 5) -> List[CauseCandidate]:
        try:
            res = query_kb(incident_report, k=k)
            distances = res.get("distances", [[]])[0]
            docs = res.get("documents", [[]])[0]
            out: List[CauseCandidate] = []
            for d, doc in zip(distances, docs):
                sim = 1.0 - float(d)
                out.append(
                    CauseCandidate(
                        label="kb_evidence", score=max(0.0, sim), evidence=str(doc)
                    )
                )
            return out
        except Exception:
            return []

    # 3) Cause development (GCRNN placeholder)
    def gcrnn_infer(self, incident_report: str, top_k: int = 5) -> List[CauseCandidate]:
        # Placeholder scores; in real impl, map incident to subgraph and run model
        return []

    # 4) Rank causes by fusing signals
    def rank_causes(
        self,
        cache_cause: Optional[str],
        kb: List[CauseCandidate],
        gcrnn: List[CauseCandidate],
    ) -> List[CauseCandidate]:
        out: Dict[str, float] = {}
        if cache_cause:
            out[cache_cause] = out.get(cache_cause, 0.0) + 1.0
        for c in kb:
            out[c.label] = max(out.get(c.label, 0.0), c.score)
        for c in gcrnn:
            out[c.label] = max(out.get(c.label, 0.0), c.score)
        ranked = [
            CauseCandidate(label=k, score=v)
            for k, v in sorted(out.items(), key=lambda kv: kv[1], reverse=True)
        ]
        return ranked

    def analyze(self, incident_report: str) -> Dict[str, Any]:
        cache_cause = self.cache_lookup(incident_report)
        kb = self.kb_search(incident_report)
        gcrnn = self.gcrnn_infer(incident_report)
        ranked = self.rank_causes(cache_cause, kb, gcrnn)
        return {
            "incident_report": incident_report,
            "cache_cause": cache_cause,
            "ranked_causes": [c.__dict__ for c in ranked],
        }
