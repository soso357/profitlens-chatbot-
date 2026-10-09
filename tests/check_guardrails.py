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

print("\nIntroduction never doubled:")
own = "Hi, I'm Jelena, the AI assistant for ProfitLens. Thanks for asking!"
out = g.ensure_disclosure(own)
ok = out.count("Jelena") == 1 and "founder" in out
failures += not ok
print(f"  [{'OK' if ok else 'DOUBLED'}] -> {out}")

print("\nReply length cap (R6):")
long_reply = " ".join(f"Sentence {i} about the service." for i in range(9)) + " What is your email?"
out = g.cap_length(long_reply, "how much is it?")
ok = out.endswith("What is your email?") and len([x for x in out.split(".") if x.strip()]) <= 4
failures += not ok
print(f"  [{'OK' if ok else 'WRONG'}] 10 sentences -> {out!r}")
ok = g.cap_length(long_reply, "please explain in detail") == long_reply
failures += not ok
print(f"  [{'OK' if ok else 'WRONG'}] visitor asked for detail: left as is")

print("\nNumbered lists stay whole (plain text, R6 cap):")
lst = "You will need to send us:\n\n1. Invoices from the last 4 weeks.\n2. Any recipe notes.\n3. A photo of your menu.\n\nAnything else?"
out = g.cap_length(g.strip_markdown(lst), "What do I need to send?")
ok = "recipe notes" in out and "menu" in out and "2." not in out
failures += not ok
print(f"  [{'OK' if ok else 'BROKEN'}] -> {out!r}")

print("\nNo selling (rule 15):")
for reply, msg, expect_gone in [
    ("A founder can look at it. Would you like to book the intake call?", "is 40 percent bad?", True),
    ("Any questions about the service, or would you like to get started?", "who won the super bowl", True),
    ("Anything else you would like to know about ProfitLens, or would you like help getting started?", "Ok thanks.", True),
    ("Any questions, or would you like to know more before you start?", "Ok thanks.", False),
    ("Great, what is your first name?", "I want to book a call", False),
    ("It includes an Excel workbook. Would you like to get started?", "i want to use 99% service", False),
    ("Happy to help. Would you like to book the intake call?", "sign me up", False),
    ("Great. Shall we book your call?", "I am interested, lets do it", False),
]:
    out = g.remove_sales_push(reply, msg)
    ok = (out != reply and "book the" not in out.lower() and "started" not in out.lower()) if expect_gone else out == reply
    failures += not ok
    print(f"  [{'OK' if ok else 'WRONG'}] {reply!r} -> {out!r}")

print("\nNo option or price question (G8):")
for reply, expect_gone in [
    ("Which option are you interested in, the $99 or the $149?", True),
    ("Great. Would you like the $99 or the $149 option?", True),
    ("The $99 option covers food cost. The $149 adds the menu review. Which one sounds right for you?", True),
    ("Are you leaning toward the full report?", True),
    ("Great. Is it the $99.00 or the $149.00 option you want?", True),
    ("Would you prefer a founder to email you about the report?", False),
    ("Which state is your restaurant in?", False),
    ("What is the name of your restaurant?", False),
    ("What is the best email to reach you?", False),
]:
    out = g.remove_option_question(reply)
    ok = (out != reply and "$149?" not in out and "which one" not in out.lower()) if expect_gone else out == reply
    failures += not ok
    print(f"  [{'OK' if ok else 'WRONG'}] {reply!r} -> {out!r}")

print("\nNo filler closer, no leaks, no length of the free offer (B15, B17, G9):")
for reply, expect_changed in [
    ("The Food Cost Analysis is $99 (one-time, no subscription). Anything else you would like to know?", True),
    ("Per the approved answers, the cost is $99. A founder can help.", True),
    ("The visitor asked about cost. It is $99.", True),
    ("The easiest way is to book a call with us.", True),
    ("Please book your intake call here.", True),
    ("It is free for you for the first 20 clients.", True),
    ("It is free for you until December 1.", True),
    ("The offer is free for the next 3 months.", True),
    ("Only 5 spots left on the free offer.", True),
    ("Right now both are free for you, for a limited time, in exchange for honest feedback.", False),
    ("Results arrive within 5 business days of the 15 to 20 minute call. A founder will email you to set up the call.", False),
    ("Share your email and a founder will reply.", False),
]:
    out = g.clean_reply(reply)
    ok = (out != reply) if expect_changed else out == reply
    failures += not ok
    print(f"  [{'OK' if ok else 'WRONG'}] {reply!r} -> {out!r}")
only = g.clean_reply("Per the approved answers, I cannot say.")
ok = only == g.HANDOFF_REPLY
failures += not ok
print(f"  [{'OK' if ok else 'WRONG'}] all sentences leaked -> founder offer: {only!r}")

print("\nCard numbers in visitor messages:")
for msg, expect in [("my card is 4242 4242 4242 4242 exp 12/28", True), ("call me on 555 123 4567", False),
                    ("we have 45 dishes and 3 locations", False)]:
    got = g.contains_card_number(msg)
    failures += got != expect
    print(f"  [{'OK' if got == expect else 'WRONG'}] {msg!r} -> card detected: {got}")

print(f"\n{'ALL CHECKS PASSED' if not failures else f'{failures} CHECK(S) FAILED'}")
raise SystemExit(bool(failures))
