"""Preview the chatbot before the Anthropic API key exists.

Uses the real system prompt (app/content.py) and the real reply guardrails
(app/guardrails.py), but gets each reply from Claude Haiku through the local
Claude Code login (`claude -p`) instead of the API. For testing only; the live
service always uses the API (app/main.py). Rate limits, spend cap and logging
are not exercised here.

Chat in a Terminal window:   .venv/bin/python -m tests.preview_chat
Ask a list of questions:     .venv/bin/python -m tests.preview_chat "question one" "question two"
"""
import subprocess
import sys
import tempfile

from app import guardrails
from app.content import SYSTEM_PROMPT

MODEL = "haiku"


def ask_model(history):
    """history: list of (role, text). Returns the model's next reply as plain text."""
    lines = []
    for role, text in history:
        lines.append(f"{'Visitor' if role == 'user' else 'You'}: {text}")
    prompt = ("Conversation so far on the website chat:\n\n" + "\n\n".join(lines)
              + "\n\nWrite only your next reply to the visitor, nothing else.")
    with tempfile.TemporaryDirectory() as tmp:  # outside the project so project hooks do not run
        r = subprocess.run(
            ["claude", "-p", "--model", MODEL, "--system-prompt", SYSTEM_PROMPT, "--tools", "",
             "--no-session-persistence", "--output-format", "text"],
            input=prompt, capture_output=True, text=True, cwd=tmp, timeout=180,
            env={**__import__("os").environ, "PL_WORKFLOW_SUMMARIZER": "1"},
        )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()


def reply_to(history, message):
    """Same order of checks as app/main.py chat()."""
    first = not history
    if guardrails.contains_card_number(message):
        message = guardrails.redact_card_numbers(message)
        reply = guardrails.PAYMENT_WARNING
        return message, (guardrails.ensure_disclosure(reply) if first else reply), ["card number removed"]
    raw = ask_model(history + [("user", message)])
    reply = guardrails.strip_markdown(guardrails.remove_dashes(raw))
    notes = guardrails.find_violations(reply)
    if notes:
        reply = guardrails.HANDOFF_REPLY
    if first:
        reply = guardrails.ensure_disclosure(reply)
    return message, reply, notes


def main():
    history = []
    questions = sys.argv[1:]
    interactive = not questions
    if interactive:
        print("ProfitLens chatbot preview (Haiku via Claude Code). Type a question and press Enter. Type 'quit' to stop.\n", flush=True)
    while True:
        if interactive:
            try:
                message = input("You: ").strip()
            except EOFError:
                break
            if message.lower() in ("quit", "exit"):
                break
            if not message:
                continue
        else:
            if not questions:
                break
            message = questions.pop(0)
            print(f"You: {message}")
        print("   (thinking, about 10 seconds...)", flush=True)
        try:
            message, reply, notes = reply_to(history, message)
        except FileNotFoundError:
            print("   ERROR: the 'claude' command was not found in this Terminal. Run this tool from the same kind of window where you use Claude Code.\n")
            continue
        except Exception as e:
            print(f"   ERROR: {e}\n")
            continue
        if notes:
            print(f"   [guardrail blocked the model's reply: {'; '.join(notes)}]")
        print(f"Bot: {reply}\n")
        history += [("user", message), ("assistant", reply)]


if __name__ == "__main__":
    main()
