"""Audit log: one JSON line per decision. Done for you; extend the fields if your policy needs more."""
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

# gate.py judge/try set GATE_LOG_DIR so evaluation runs never pollute your demo audit sample.
LOG = Path(os.getenv("GATE_LOG_DIR") or Path(__file__).parent) / "audit_log.jsonl"
_lock = threading.Lock()


def record(persona, text, context, decision):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "persona": persona,
        "input": text,
        "context": context,
        "decision": decision.decision,
        "reason": decision.reason,
        "evidence": decision.evidence,
        "ezio": decision.ezio,
        "action_executed": decision.decision == "APPROVE",
    }
    with _lock, LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def history(limit=30):
    if not LOG.exists():
        return []
    with _lock:
        lines = LOG.read_text().splitlines()[-limit:]
    result = []
    for line in reversed(lines):
        try:
            entry = json.loads(line)
            result.append({k: entry.get(k) for k in ("timestamp", "type", "input", "decision", "outcome", "reason", "evidence", "action_executed")})
        except json.JSONDecodeError:
            continue
    return result


def review(text, outcome, reason):
    entry = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "type": "human_review", "input": text, "outcome": outcome, "reason": reason,
             "action_executed": False}
    with _lock, LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
