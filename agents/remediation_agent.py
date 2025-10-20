from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
from .utils.bootstrap import bootstrap_analyzer_helpers
from pathlib import Path as _P

bootstrap_analyzer_helpers((_P(__file__).parent))

"""
Remediation Agent
-----------------
Maps a problem description to a sequence of remediation steps.

This module implements:
- Duplicate detection against problems_cache (via remediation_cache)
- Supervised baseline classifier over a fixed action catalog
- PPO-ready harness stub for future RL fine-tuning
"""


@dataclass
class Action:
    id: str
    text: str


class RemediationAgent:
    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = (
            Path(data_dir)
            if data_dir
            else Path(__file__).parent / "analyzer-helpers" / "data"
        )
        self.catalog_path = self.data_dir / "processed-data" / "action_catalog.json"
        self.model_path = self.data_dir / "processed-data" / "remediation_baseline.json"
        self._catalog: List[Action] = []
        self._clf = None  # lazy

    # ---------- Catalog ----------
    def load_action_catalog(self) -> List[Action]:
        if self._catalog:
            return self._catalog
        if self.catalog_path.exists():
            data = json.loads(self.catalog_path.read_text(encoding="utf-8"))
            self._catalog = [Action(**a) for a in data]
        else:
            # Minimal default catalog
            self._catalog = [
                Action(
                    id="notify_owner", text="Notify on-call owner with incident details"
                ),
                Action(id="restart_service", text="Restart affected service or pod"),
                Action(id="rollback_deploy", text="Rollback last deployment"),
                Action(id="scale_resources", text="Scale up compute resources"),
            ]
        return self._catalog

    # ---------- Supervised baseline ----------
    def _ensure_classifier(self):
        if self._clf is not None:
            return
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.pipeline import Pipeline
        from sklearn.linear_model import LogisticRegression

        catalog = self.load_action_catalog()
        # Construct a toy training set by pairing catalog phrases to labels
        X = [a.text for a in catalog]
        y = [a.id for a in catalog]
        clf = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=4096, ngram_range=(1, 2))),
                ("lr", LogisticRegression(max_iter=1000)),
            ]
        )
        try:
            clf.fit(X, y)
        except Exception:
            # If scikit isn't fitted due to environment, keep a placeholder
            pass
        self._clf = clf

    def classify_actions(self, problem_text: str, top_k: int = 3) -> List[Action]:
        self._ensure_classifier()
        catalog = self.load_action_catalog()
        if not self._clf:
            # Fallback: simple heuristic ordering
            return catalog[:top_k]
        try:
            import numpy as np

            proba = self._clf.predict_proba([problem_text])[0]
            classes = list(self._clf.classes_)
            idx = np.argsort(-proba)[:top_k]
            id_set = {classes[i] for i in idx}
            return [a for a in catalog if a.id in id_set][:top_k]
        except Exception:
            return catalog[:top_k]

    # ---------- RL harness (stub) ----------
    def suggest_with_rl(self, problem_text: str) -> List[Action]:
        # Placeholder: return baseline for now
        return self.classify_actions(problem_text)

    # ---------- Public API ----------
    def generate_solution(self, problem_text: str) -> Dict[str, Any]:
        # Check duplicates first
        meta = None
        try:
            from analyzer_helpers.remediation_cache import find_similar_problem  # type: ignore

            meta = find_similar_problem(problem_text)
        except Exception:
            meta = None

        baseline = self.classify_actions(problem_text)
        steps = [a.text for a in baseline]
        if meta and isinstance(meta, dict):
            # If prior solution steps exist in metadata, prefer them
            prior = meta.get("Solution_Steps") or meta.get("Remediation")
            if prior:
                steps = [str(prior)]

        return {
            "problem": problem_text,
            "proposed_steps": steps,
            "duplicate_match": meta,
        }
