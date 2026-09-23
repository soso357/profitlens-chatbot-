"""Preview the chatbot before the Anthropic API key exists.

Uses the real system prompt (app/content.py) and the real reply guardrails
(app/guardrails.py), but gets each reply from Claude Haiku through the local
Claude Code login (`claude -p`) instead of the API. For testing only; the live
service always uses the API (app/main.py). Rate limits, spend cap and logging
are not exercised here.

Chat in a Terminal window:   .venv/bin/python -m tests.preview_chat
Ask a list of questions:     .venv/bin/python -m tests.preview_chat "question one" "question two"

Booking is REAL: when times are shown, typing 1, 2 or 3 books a call in the calendar,
Google emails the invite to the email you gave, and founders get Telegram and email
alerts marked "PREVIEW TEST". Type "more" for other times.
Leads are saved to data/leads.csv. When you type quit, the whole conversation is
sent to the founders' Telegram group (in the live service: after 30 quiet minutes).
"""
import subprocess
import sys
import tempfile

from app import chat_booking, guardrails
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


SOURCE = "PREVIEW TEST"


def reply_to(history, message, state):
    """Same order of checks as app/main.py chat(). Returns (message, reply, notes, slots)."""
    first = not history
    choice = message.strip().rstrip(".").lower()
    if state.offered and choice in ("1", "2", "3", chat_booking.MORE):
        transcript = chat_booking.transcript_text(history)
        reply, slots = chat_booking.pick(state, choice, "preview", transcript, source=SOURCE)
        return message, reply, [], slots
    if guardrails.contains_card_number(message):
        message = guardrails.redact_card_numbers(message)
        reply = guardrails.PAYMENT_WARNING
        return message, (guardrails.ensure_disclosure(reply) if first else reply), ["card number removed"], []
    raw = ask_model(history + [("user", message)])
    typed = " ".join(t for r, t in history if r == "user") + " " + message
    text, details, lead = chat_booking.extract(raw, typed)
    reply = guardrails.strip_markdown(guardrails.remove_dashes(text))
    notes = guardrails.find_violations(reply)
    if notes:
        notes = ["guardrail blocked the model's reply: " + "; ".join(notes)]
        reply, details, lead = guardrails.HANDOFF_REPLY, None, None
    if first:
        reply = guardrails.ensure_disclosure(reply)
    slots = []
    so_far = chat_booking.transcript_text(history + [("user", message), ("assistant", reply)])
    if details and not state.details:
        extra, slots = chat_booking.offer(state, details, "preview", so_far, source=SOURCE)
        reply = f"{reply} {extra}".strip()
    if lead:
        if chat_booking.record_lead(state, lead, "preview", so_far, source=SOURCE):
            notes = notes + ["lead saved, founders alerted"]
    return message, reply, notes, slots


def main():
    history = []
    state = chat_booking.BookingState()
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
            message, reply, notes, slots = reply_to(history, message, state)
        except FileNotFoundError:
            print("   ERROR: the 'claude' command was not found in this Terminal. Run this tool from the same kind of window where you use Claude Code.\n")
            continue
        except Exception as e:
            print(f"   ERROR: {e}\n")
            continue
        if notes:
            print(f"   [{'; '.join(notes)}]")
        print(f"Bot: {reply}")
        for i, sl in enumerate(slots, 1):
            print(f"   [{i}] {sl['label']}")
        if slots:
            print("   Type 1, 2 or 3 to book (real booking), or 'more' for other times.")
        print()
        history += [("user", message), ("assistant", reply)]
    if history:
        full = chat_booking.transcript_text(history)
        chat_booking.finish(state, "preview", full, full, source=SOURCE)
        print("Conversation sent to the founders' Telegram group.")


if __name__ == "__main__":
    main()
