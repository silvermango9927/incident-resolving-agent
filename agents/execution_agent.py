from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import os
import smtplib
from email.mime.text import MIMEText

import pandas as pd
from jinja2 import Environment, BaseLoader


CONTACTS_CSV = (
    Path(__file__).parent
    / "analyzer-helpers"
    / "data"
    / "processed-data"
    / "contacts.csv"
)


def _load_contacts(path: Path = CONTACTS_CSV) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["team", "role", "email", "component_keywords"])
    return pd.read_csv(path)


def select_contact(component_hint: str) -> Optional[Dict[str, Any]]:
    df = _load_contacts()
    if df.empty:
        return None
    if not component_hint:
        return df.iloc[0].to_dict()
    scores = []
    for _, row in df.iterrows():
        kw = str(row.get("component_keywords", "")).lower()
        score = 1 if component_hint.lower() in kw else 0
        scores.append(score)
    idx = int(max(range(len(scores)), key=lambda i: scores[i]))
    return df.iloc[idx].to_dict()


EMAIL_TEMPLATE = """
Subject: {{ subject }}

Hello {{ contact.team or 'Team' }},

An incident requires attention.

- Incident time: {{ incident.time }}
- Sender: {{ incident.sender }}
- Summary: {{ incident.summary }}
- Identified Cause: {{ cause }}

Recommended steps:
{% for step in steps %}- {{ step }}
{% endfor %}

Thanks,
Duty Officer Bot
"""


def draft_email(
    contact: Dict[str, Any], incident: Dict[str, Any], cause: str, steps: List[str]
) -> str:
    env = Environment(loader=BaseLoader())
    t = env.from_string(EMAIL_TEMPLATE)
    return t.render(
        contact=contact,
        incident=incident,
        cause=cause,
        steps=steps,
        subject="Incident Escalation",
    )


def send_email(
    message_text: str, to_addr: str, dry_run_default: bool = True
) -> Dict[str, Any]:
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    dry = os.getenv("SMTP_DRY_RUN", "").lower() in {"1", "true", "yes"}
    dry = dry or dry_run_default or not all([smtp_host, smtp_user, smtp_pass])

    msg = MIMEText(message_text, _charset="utf-8")
    msg["Subject"] = "Incident Escalation"
    msg["From"] = smtp_user or "no-reply@example.com"
    msg["To"] = to_addr

    if dry:
        return {"status": "dry-run", "to": to_addr, "message": message_text[:5000]}

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(msg["From"], [to_addr], msg.as_string())
    return {"status": "sent", "to": to_addr}


SUMMARY_TEMPLATE_MD = """
# Escalation Summary

## Details about the Incident Report
- Time sent: {{ incident.time }}
- Sender: {{ incident.sender }}
- Summary: {{ incident.summary }}

## Identified Cause
{{ cause }}

## Steps taken
{% for s in steps_taken %}- {{ s }}
{% endfor %}

## List of pending actions
{% for s in pending %}- {{ s }}
{% endfor %}
"""


def render_summary_md(
    incident: Dict[str, Any], cause: str, steps_taken: List[str], pending: List[str]
) -> str:
    env = Environment(loader=BaseLoader())
    t = env.from_string(SUMMARY_TEMPLATE_MD)
    return t.render(
        incident=incident, cause=cause, steps_taken=steps_taken, pending=pending
    )
