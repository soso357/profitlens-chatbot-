"""Shared helpers for the workflow hooks. Standard library only (ADR 0009, 0010, 0012)."""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
MEMORY = ROOT / "memory"
WORKING = MEMORY / "working"
STATE = WORKING / "state"
SESSIONS = MEMORY / "episodic" / "sessions"
PROPOSALS = MEMORY / "proposals"
HANDOFF = WORKING / "handoff.md"

HANDOFF_PCT = 60        # ask Claude to write the handoff
COMPACT_PCT = 70        # auto compaction (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE)
MAX_COMPACTIONS = 3     # after this many, recommend a fresh session

# Set in the environment of the background summarizer so no hook re-enters.
GUARD_ENV = "PL_WORKFLOW_SUMMARIZER"

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{10,}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{30,}\b"),  # Telegram bot token
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)((?:password|passwd|app_password|api_key|secret|token)\s*[=:]\s*)[^\n]+"),  # whole rest of line: passwords can contain spaces
]


def scrub(text):
    for p in SECRET_PATTERNS:
        text = p.sub(lambda m: (m.group(1) if m.groups() else "") + "[REDACTED]", text)
    return text


def read_hook_input():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def session_state_path(session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "", session_id or "unknown")[:80] or "unknown"
    return STATE / f"{safe}.json"


def load_state(session_id):
    try:
        return json.loads(session_state_path(session_id).read_text())
    except Exception:
        return {"compactions": 0, "pct": 0, "handoff_nudged_cycle": -1, "limit_nudged": False}


def save_state(session_id, state):
    STATE.mkdir(parents=True, exist_ok=True)
    state["updated"] = int(time.time())
    tmp = session_state_path(session_id).with_suffix(".tmp")
    tmp.write_text(json.dumps(state))
    tmp.replace(session_state_path(session_id))


def frontmatter(path):
    """Return (dict, body) for a Markdown file with simple 'key: value' frontmatter."""
    text = Path(path).read_text(errors="replace")
    meta = {}
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip().strip('"')
            text = text[end + 4:].lstrip("\n")
    return meta, text


def open_proposals():
    out = []
    for p in sorted(PROPOSALS.glob("[0-9]*.md")):
        meta, _ = frontmatter(p)
        if meta.get("status", "proposed") in ("proposed", "approved"):
            out.append((p.name, meta.get("status", "proposed"), meta.get("title", p.stem)))
    return out


NOISE_PREFIXES = ("<system-reminder", "<command-", "<local-command", "<task-notification", "<bash-")


def is_real_user_text(content):
    """True for text a person typed or pasted, False for harness noise and tool results."""
    return isinstance(content, str) and bool(content.strip()) and not content.lstrip().startswith(NOISE_PREFIXES)


def emit_context(event, text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))
