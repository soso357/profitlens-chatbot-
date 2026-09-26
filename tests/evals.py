"""One command for the Test step (ADR 0020): every offline check, then every scripted
visitor conversation against a safe local copy of the service, with a pass or fail score.

Run: .venv/bin/python -m tests.evals            (all, uses a little API credit)
     .venv/bin/python -m tests.evals --offline  (no API calls, free)

The local copy sends no Telegram or email alerts and keeps logs, leads and the spend
counter in a temporary folder. It reads the calendar (free times) but books nothing.
Writes tests/eval-report.md. Exit code 1 if anything failed: run before every pull request.
"""
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
OFFLINE = ["tests.check_guardrails", "tests.check_booking", "tests.check_sessions", "tests.check_workflow"]
PORT = 8765


def run(module, env=None):
    t = time.time()
    r = subprocess.run([PY, "-m", module], cwd=ROOT, capture_output=True, text=True, env=env, timeout=1800)
    tail = (r.stdout.strip().splitlines() or [""])[-1]
    print(f"{'PASS' if r.returncode == 0 else 'FAIL'}: {module} ({time.time() - t:.0f}s) {tail}")
    if r.returncode:
        print(r.stdout[-2000:], r.stderr[-2000:], sep="\n")
    return r.returncode == 0, tail


def safe_env():
    tmp = tempfile.mkdtemp(prefix="profitlens-eval-")
    return dict(os.environ, TELEGRAM_BOT_TOKEN="", TELEGRAM_CHAT_ID="", FOUNDER_NOTIFY_EMAIL="", TEST_PAGES="1",
                IP_RATE_LIMIT="1000/hour", LOG_DIR=f"{tmp}/logs", DATA_DIR=f"{tmp}/data",
                EVAL_BASE=f"http://127.0.0.1:{PORT}")


def wait_up(url, seconds=30):
    for _ in range(seconds * 4):
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except urllib.error.HTTPError:
            return True  # the server answered
        except Exception:
            time.sleep(0.25)
    return False


def main():
    offline = "--offline" in sys.argv
    rows = [(m, *run(m)) for m in OFFLINE]
    if not offline:
        env = safe_env()
        server = subprocess.Popen([PY, "-m", "uvicorn", "app.main:app", "--port", str(PORT)], cwd=ROOT, env=env,
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        try:
            if wait_up(env["EVAL_BASE"] + "/health"):
                rows.append(("tests.run_conversations", *run("tests.run_conversations", env)))
            else:
                rows.append(("tests.run_conversations", False, "local service did not start"))
                print("FAIL: local service did not start")
        finally:
            server.terminate()
            server.wait(timeout=10)
    ok = all(r[1] for r in rows)
    report = [f"# Eval report\n\nRun on {datetime.now():%Y-%m-%d %H:%M}{' (offline only)' if offline else ''}. "
              f"Result: **{'PASS' if ok else 'FAIL'}**\n", "| Check | Result | Last line |", "|---|---|---|"]
    report += [f"| {m} | {'PASS' if p else 'FAIL'} | {tail.replace('|', '/')} |" for m, p, tail in rows]
    if not offline:
        report.append("\nTranscripts with a verdict per conversation: tests/transcripts.md")
    (ROOT / "tests" / "eval-report.md").write_text("\n".join(report) + "\n")
    print(f"\n{'ALL EVALS PASSED' if ok else 'EVALS FAILED'} (tests/eval-report.md)")
    return ok


if __name__ == "__main__":
    raise SystemExit(0 if main() else 1)
