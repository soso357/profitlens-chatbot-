"""Offline check of the code guardrails. No API key needed. Run: .venv/bin/python -m tests.check_guardrails"""
from app import guardrails as g

SHOULD_BLOCK = [
    "Most clients save around $2,000 a month after the report.",
    "A healthy food cost is 28 to 35 percent, so you are in good shape.",
    "Your food cost should be about 30%.",
    "We guarantee you will see higher profits within a month.",
    "This will increase your profit on every dish.",
    "You'll save money from the first week.",
    "I can do it for $49 today if you book now.",
    "You can pay here: https://paypal.me/profitlens",
    "Please send me your card number and I will take care of it.",
    "It costs 99 dollars plus a $9 setup fee.",
    "Price suggestions are never more than eight percent.",
]
SHOULD_PASS = [
    "The Food Cost Analysis is $99 and the Menu Analysis Report is $149.",
    "If you start with $99, the upgrade is $50.",
    "I cannot guarantee any results, but a founder can talk it through with you.",
    "I can't promise a specific outcome. Would you like a founder to email you?",
    "The call takes 15 to 20 minutes and results arrive within 5 business days.",
    "Please do not share your card number in this chat.",
    "You can see a sample at useprofitlens.com/sample.",
    "The report shows which dishes make money and which do not.",
]

failures = 0
print("Replies the guardrails must block:")
for text in SHOULD_BLOCK:
    v = g.find_violations(text)
    failures += not v
    print(f"  [{'BLOCKED' if v else 'MISSED '}] {text}\n            {v}")
print("\nReplies the guardrails must allow:")
for text in SHOULD_PASS:
    v = g.find_violations(text)
    failures += bool(v)
    print(f"  [{'ALLOWED' if not v else 'WRONGLY BLOCKED'}] {text} {v or ''}")

print("\nDash removal:")
for text in ["The call is 15–20 minutes — short and easy.", "Send invoices - any format works."]:
    out = g.remove_dashes(text)
    ok = not any(c in out for c in "–—") and " - " not in out
    failures += not ok
    print(f"  {text!r}\n  -> {out!r}")

print("\nAI disclosure on first reply:")
out = g.ensure_disclosure("The Food Cost Analysis is $99.")
failures += "AI assistant" not in out
print(f"  -> {out}")

print("\nCard numbers in visitor messages:")
for msg, expect in [("my card is 4242 4242 4242 4242 exp 12/28", True), ("call me on 555 123 4567", False),
                    ("we have 45 dishes and 3 locations", False)]:
    got = g.contains_card_number(msg)
    failures += got != expect
    print(f"  [{'OK' if got == expect else 'WRONG'}] {msg!r} -> card detected: {got}")

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
