"""Shared helpers for the workflow hooks. Standard library only (ADR 0009, 0010, 0012)."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def main_root(root):
    """The main project folder. In a git worktree (a second copy of the project on its own
    branch, ADR 0023) this is the original folder, so every terminal shares one memory."""
    try:
        common = subprocess.run(["git", "-C", str(root), "rev-parse", "--path-format=absolute", "--git-common-dir"],
                                capture_output=True, text=True, timeout=3).stdout.strip()
        if common.endswith("/.git") and Path(common).parent.is_dir():
            return Path(common).parent
    except Exception:
        pass
    return root


MAIN_ROOT = main_root(ROOT)
MEMORY = MAIN_ROOT / "memory"
WORKING = MEMORY / "working"
STATE = WORKING / "state"
SNAPSHOTS = WORKING / "snapshots"
HANDOFFS = WORKING / "handoffs"          # one handoff per task (ADR 0022)
SESSIONS = MEMORY / "episodic" / "sessions"
PROPOSALS = MEMORY / "proposals"
SEMANTIC = MEMORY / "semantic"

HANDOFF_PCT = 60        # ask Claude to update the task handoff
STOP_PCT = 70           # soft stop: hand off and continue in a new terminal (ADR 0022, 0023 C3)
COMPACT_PCT = 85        # auto compaction, safety net only (CLAUDE_AUTOCOMPACT_PCT_OVERRIDE)
MAX_COMPACTIONS = 1     # after this many, recommend a fresh session

# Staleness (foundation v2 step 2)
VERIFY_DAYS = 60        # semantic memory not verified for this long is flagged
DEFERRED_DAYS = 30      # deferred proposals come back after this long
DONE_HANDOFF_DAYS = 14  # handoffs marked done are deleted after this long

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


def summary_failures():
    """Sessions whose summary failed and has not been redone: {session_id: {time, error, transcript}}.
    One file per session (<id>.summary-failed.json), so parallel runs never overwrite each other."""
    out = {}
    for f in STATE.glob("*.summary-failed.json"):
        try:
            out[f.name[:-len(".summary-failed.json")]] = json.loads(f.read_text())
        except Exception:
            pass
    return out


def set_summary_failure(session_id, info=None):
    """Record (info given) or clear (info None) a failed summary for one session."""
    f = session_state_path(session_id).with_suffix(".summary-failed.json")
    if info:
        STATE.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps(info))
    else:
        f.unlink(missing_ok=True)


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


# Handoffs (ADR 0022): memory/working/handoffs/<task>.md with a small header, one per task or branch.

def task_slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")[:60] or "task"


def list_handoffs(include_done=False):
    """[(slug, meta)] newest first. meta has task, type, branch, worktree, commit, updated, status."""
    out = []
    for f in HANDOFFS.glob("*.md"):
        if f.name.startswith("_"):
            continue
        meta, _ = frontmatter(f)
        meta.setdefault("status", "open")
        meta.setdefault("updated", time.strftime("%Y-%m-%d %H:%M", time.localtime(f.stat().st_mtime)))
        if include_done or meta["status"] != "done":
            out.append((f.stem, meta))
    return sorted(out, key=lambda x: x[1]["updated"], reverse=True)


def write_handoff_index():
    rows = ["# Open and recent tasks (generated, do not edit)", "",
            "| Task | Type | Branch | Updated | Status |", "|---|---|---|---|---|"]
    for slug, m in list_handoffs(include_done=True):
        rows.append(f"| {slug} | {m.get('type', '?')} | {m.get('branch', '?')} | {m['updated']} | {m['status']} |")
    HANDOFFS.mkdir(parents=True, exist_ok=True)
    (HANDOFFS / "_index.md").write_text("\n".join(rows) + "\n")


def current_branch(cwd):
    try:
        return subprocess.run(["git", "--no-optional-locks", "-C", str(cwd), "branch", "--show-current"],
                              capture_output=True, text=True, timeout=2).stdout.strip()
    except Exception:
        return ""


def handoff_for_session(state, cwd):
    """This session's own task handoff: the one it wrote (recorded by handoff_track.py), else the
    newest open one on the same branch. Never another terminal's task on another branch."""
    task = state.get("task")
    if task and (HANDOFFS / f"{task}.md").exists():
        return HANDOFFS / f"{task}.md"
    branch = current_branch(cwd)
    for slug, m in list_handoffs():
        if branch and m.get("branch") == branch:
            return HANDOFFS / f"{slug}.md"
    return None


# Staleness (foundation v2 step 2)

def days_since(text):
    """Days since the first YYYY-MM-DD in text, or None if there is no date."""
    m = re.search(r"\d{4}-\d{2}-\d{2}", text or "")
    if not m:
        return None
    try:
        return int((time.time() - time.mktime(time.strptime(m.group(0), "%Y-%m-%d"))) // 86400)
    except ValueError:
        return None


def stale_note(path):
    """For a semantic memory file: '' if verified recently, else a short warning."""
    try:
        meta, _ = frontmatter(path)
    except Exception:
        return ""
    age = days_since(meta.get("last_verified", ""))
    if age is None:
        return "never verified"
    return f"not verified for {age} days" if age > VERIFY_DAYS else ""


def stale_semantic():
    return [(p, n) for p in sorted(SEMANTIC.glob("*.md")) if (n := stale_note(p))]


def deferred_due():
    """Deferred proposals whose decision date is more than DEFERRED_DAYS ago."""
    out = []
    for p in sorted(PROPOSALS.glob("[0-9]*.md")):
        meta, body = frontmatter(p)
        if meta.get("status") != "deferred":
            continue
        decision = body.split("## Decision", 1)[-1]
        age = days_since(decision) if "## Decision" in body else days_since(meta.get("created", ""))
        if age is not None and age > DEFERRED_DAYS:
            out.append((p.name, meta.get("title", p.stem), age))
    return out


def cleanup_done_handoffs():
    """Delete handoffs marked done more than DONE_HANDOFF_DAYS ago. Returns the deleted names."""
    gone = []
    for slug, m in list_handoffs(include_done=True):
        age = days_since(m.get("updated", ""))
        if m.get("status") == "done" and age is not None and age > DONE_HANDOFF_DAYS:
            (HANDOFFS / f"{slug}.md").unlink(missing_ok=True)
            gone.append(slug)
    return gone


def words(text):
    text = re.sub(r"\(from [^)]*\)", "", (text or "").lower())
    text = re.sub(r"^- \d{4}-\d{2}-\d{2}[^:]*:", "", text.strip())  # a list line's own date is not content
    return {w for w in re.findall(r"[a-z0-9]+", text) if len(w) > 3 or any(c.isdigit() for c in w)}


def similar(a, b, threshold=0.6):
    """True when the shorter text's longer words mostly appear in the other (same item, reworded).
    Different numbers mean different items ("step 1 merged" is not "step 2 merged")."""
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return False
    if {w for w in wa if any(c.isdigit() for c in w)} != {w for w in wb if any(c.isdigit() for c in w)}:
        return False
    return len(wa & wb) / min(len(wa), len(wb)) >= threshold
