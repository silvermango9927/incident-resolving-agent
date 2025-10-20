from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .cause_analysis_agent import CauseAnalysisAgent
from .remediation_agent import RemediationAgent
from .execution_agent import select_contact, draft_email, send_email, render_summary_md


@dataclass
class OrchestratorConfig:
    consent_required: bool = True


class IncidentOrchestrator:
    def __init__(self, cfg: Optional[OrchestratorConfig] = None) -> None:
        self.cfg = cfg or OrchestratorConfig()
        self.cause_agent = CauseAnalysisAgent()
        self.rem_agent = RemediationAgent()

    def run(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        # 1) Cause analysis
        analysis = self.cause_agent.analyze(
            incident["summary"]
        )  # using 'summary' as incident report text
        best_cause = analysis.get("cache_cause") or (
            analysis.get("ranked_causes") and analysis["ranked_causes"][0].get("label")
        )
        cause_text = best_cause or "Cause under investigation"

        # 2) Remediation planning
        remedy = self.rem_agent.generate_solution(
            incident.get("problem", incident["summary"])
        )
        steps = remedy.get("proposed_steps", [])

        # 3) Execution prep (contact + email draft)
        contact = select_contact(incident.get("component", "")) or {
            "team": "Unknown",
            "email": "",
        }
        email_text = draft_email(contact, incident, cause_text, steps)

        # Consent gate (do not actually send unless consent satisfied)
        email_result = {"status": "skipped"}
        if not self.cfg.consent_required:
            to_addr = contact.get("email") or ""
            if to_addr:
                email_result = send_email(email_text, to_addr)

        # 4) Escalation Summary artifacts
        steps_taken = ["Prepared escalation email"]
        pending = (
            [] if email_result.get("status") == "sent" else ["Send escalation email"]
        )
        md = render_summary_md(incident, cause_text, steps_taken, pending)

        return {
            "incident": incident,
            "cause_analysis": analysis,
            "remediation": remedy,
            "contact": contact,
            "email": {"draft": email_text, "result": email_result},
            "summary": {
                "json": {
                    "incident": incident,
                    "identified_cause": cause_text,
                    "steps_taken": steps_taken,
                    "pending_actions": pending,
                },
                "markdown": md,
                "html": f"<html><body>{md.replace('\n', '<br/>')}</body></html>",
            },
        }


def cli():  # pragma: no cover - simple entrypoint
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--summary", required=True, help="Incident report text")
    p.add_argument("--time", default="", help="Incident time")
    p.add_argument("--sender", default="", help="Sender")
    p.add_argument(
        "--component", default="", help="Component hint for contact selection"
    )
    p.add_argument(
        "--problem", default="", help="Problem description for remediation agent"
    )
    p.add_argument(
        "--no-consent", action="store_true", help="Send email without consent gate"
    )
    args = p.parse_args()

    inc = {
        "summary": args.summary,
        "time": args.time,
        "sender": args.sender,
        "component": args.component,
        "problem": args.problem or args.summary,
    }
    orch = IncidentOrchestrator(
        OrchestratorConfig(consent_required=not args.no_consent)
    )
    result = orch.run(inc)
    print(json.dumps(result["summary"]["json"], indent=2))


if __name__ == "__main__":  # pragma: no cover
    cli()
