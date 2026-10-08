"""Leads inside the chat (Phases 2 and 3, spec B4, B7, B13). Call booking was removed (ADR 0032).

The model never sends alerts. It ends a reply with a hidden block and this module does the rest:

    <lead>{"name", "restaurant", "location", "email", "reason"}</lead>
        visitor needs a founder (or wants the intake call, once the four details are in):
        save the lead, alert the founders, who email the visitor to set up the call

The block is removed before the visitor sees the reply.
Implements: B4, B7, B13
"""
import json
import re
import threading
from dataclasses import dataclass, field

from app import chat_log, config, email_alerts, leads, telegram

LEAD = re.compile(r"<lead>(.*?)</lead>", re.S)
EMAIL_LOOSE = re.compile(r"^[^@\s]+@[^@\s]+$")  # lets "maria@gmailcom" reach the typo check (B13)
YES = re.compile(r"^\W*((oh|ah|um|sorry|oops)\W+)*(yes+|yeah|yea|ya|yep|yup|y|correct|right|that'?s (it|right|correct)|sure|"
                 r"ok(ay)?|absolutely|definitely|exactly|please do|yes please)\b", re.I)

# B13: big providers a typed domain is compared with, and real domains that look like typos of them.
PROVIDERS = ("gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "icloud.com", "aol.com")
REAL_NAMES = {"ymail", "mail", "email", "live", "me", "msn", "gmx", "aim", "rocketmail", "mac"}
# Common misspellings of big email providers. A typo means the invite never arrives.
EMAIL_TYPOS = {
    "gmial.com": "gmail.com", "gmal.com": "gmail.com", "gmai.com": "gmail.com", "gamil.com": "gmail.com",
    "gnail.com": "gmail.com", "gmaill.com": "gmail.com", "gmail.co": "gmail.com", "gmail.con": "gmail.com",
    "gmail.cm": "gmail.com", "gmail.om": "gmail.com", "yaho.com": "yahoo.com", "yahooo.com": "yahoo.com",
    "yahoo.co": "yahoo.com", "yahoo.con": "yahoo.com", "hotmial.com": "hotmail.com", "hotmal.com": "hotmail.com",
    "hotmail.co": "hotmail.com", "hotmail.con": "hotmail.com", "outlok.com": "outlook.com", "outlook.co": "outlook.com",
    "iclod.com": "icloud.com", "icloud.co": "icloud.com", "aol.co": "aol.com",
}

CHECK_AGAIN_REPLY = "That email address does not look complete. Could you type it again?"


@dataclass
class BookingState:
    lead_saved: bool = False             # a lead row exists for this conversation
    handoff_sent: bool = False
    pending: dict | None = None          # B13: {"data": {...}} waiting for "yes" or a retyped address
    checked: list[str] = field(default_factory=list)  # B13: addresses already read back once


def _json_block(pattern: re.Pattern, raw: str) -> dict | None:
    m = pattern.search(raw)
    if not m:
        return None
    try:
        d = json.loads(m.group(1))
    except ValueError:
        return None
    return d if isinstance(d, dict) else None


def extract(raw_reply: str, visitor_text: str = "") -> tuple[str, dict | None]:
    """Remove the hidden lead block. Returns (text for the visitor, lead or None).
    visitor_text: everything the visitor typed. An email is only accepted if the visitor typed it,
    so the model can never invent or guess one."""
    typed = visitor_text.lower()
    text = LEAD.sub("", raw_reply).strip()

    lead = _json_block(LEAD, raw_reply)
    if lead is not None:
        lead = {k: str(lead.get(k, "")).strip()[:300] for k in ("name", "restaurant", "location", "email", "reason")}
        if not EMAIL_LOOSE.match(lead["email"]) or lead["email"].lower() not in typed:
            lead = None
    return text, lead


def _distance(a: str, b: str) -> int:
    """Letters to add, remove, change or swap to turn a into b (gmil to gmail is 1, gamil to gmail is 1)."""
    prev2, prev = None, list(range(len(b) + 1))
    for i in range(1, len(a) + 1):
        cur = [i] + [0] * len(b)
        for j in range(1, len(b) + 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] != b[j - 1]))
            if prev2 and i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                cur[j] = min(cur[j], prev2[j - 2] + 1)
        prev2, prev = prev, cur
    return prev[-1]


def email_check(email: str) -> tuple[bool, str | None]:
    """B13: (looks wrong, suggested address or None). Wrong means no dot after the @, a known misspelling,
    or a name part 1 letter off a big provider (2 for the longer names), so gmil.com is caught while
    yahoo.ca, joe.com and ymail.com are left alone. Chat only: the chat asks once and then accepts."""
    user, _, domain = email.strip().rpartition("@")
    d = domain.lower()
    if not user or "." not in d.strip("."):
        return True, None
    if d in EMAIL_TYPOS:
        return True, f"{user}@{EMAIL_TYPOS[d]}"
    name = d.split(".")[0]
    names = [p.split(".")[0] for p in PROVIDERS]
    if name in names or name in REAL_NAMES:
        return False, None
    best = min(names, key=lambda n: _distance(name, n))
    if _distance(name, best) <= (1 if len(best) < 5 else 2):
        return True, f"{user}@{best}.com"
    return False, None


def email_typo(email: str) -> str | None:
    """The leave your email form: only the known misspellings list, since the form cannot ask once and then accept."""
    fixed = EMAIL_TYPOS.get(email.rpartition("@")[2].lower())
    return f"{email.rpartition('@')[0]}@{fixed}" if fixed else None


def handle(state: BookingState, lead: dict | None, sid: str, transcript: str = "", source: str = "") -> str:
    """Act on the hidden lead block of one reply. Returns text to add to the reply.
    If the email looks wrong (B13), nothing is saved; the address is read back once."""
    email = (lead or {}).get("email", "")
    if lead and state.handoff_sent:
        email = ""  # a founder was already alerted; nothing new would be saved
    if email and state.pending and email.lower() in state.checked:
        # still waiting for "yes" or a retyped address: never save the unconfirmed one
        return f"Just to check, did you mean {state.pending['data']['email']}? Reply yes, or type the right email."
    if email:
        wrong, suggestion = email_check(email)
        # a near miss is asked about once (it may be real); an address with no dot is never accepted
        if wrong and (suggestion is None or email.lower() not in state.checked):
            state.checked.append(email.lower())
            chat_log.log(sid, "email_typo", suggestion=suggestion or "")
            if suggestion:
                state.pending = {"data": dict(lead or {}, email=suggestion)}
                return f"Just to check, did you mean {suggestion}? Reply yes, or type the right email."
            state.pending = None
            return CHECK_AGAIN_REPLY
    if lead:
        record_lead(state, lead, sid, transcript, source)
    return ""


def confirm(state: BookingState, message: str, sid: str, transcript: str = "", source: str = "") -> str | None:
    """B13: the visitor answered a "did you mean ...?" question. A short "yes" uses the suggested address
    without asking the model. A message with an address in it clears the question (the model sends that
    address and it is checked again; the same one typed again is accepted). Anything else keeps waiting."""
    pending = state.pending
    if not pending:
        return None
    if "@" in message:
        state.pending = None
        return None
    original = next((e for e in reversed(state.checked)), "")
    typo_name = original.rpartition("@")[2].split(".")[0]
    plain_yes = (YES.match(message) and len(message.split()) <= 4
                 and not (typo_name and typo_name in message.lower()))  # "yes, gmil.com is correct" is not a plain yes
    if not plain_yes:
        return None
    state.pending = None
    data = pending["data"]
    chat_log.log(sid, "email_confirmed", email=data["email"])
    if record_lead(state, data, sid, transcript, source):
        return f"Thanks, I will use {data['email']}. A founder will email you there."
    return None


def transcript_text(pairs) -> str:
    """pairs: iterable of (role, text) with role 'user' or 'assistant'."""
    return "\n".join(f"{'Visitor' if r == 'user' else 'Bot'}: {t}" for r, t in pairs)


def _alert(subject: str, body: str) -> None:
    telegram.send_long(f"{subject}\n{body}")
    email_alerts.alert_founders(subject, body)


def _details_text(d: dict) -> str:
    lines = [f"Name: {d.get('name') or '(not given)'}", f"Restaurant: {d.get('restaurant') or '(not given)'}",
             f"Location: {d.get('location') or '(not given)'}", f"Email: {d.get('email')}"]
    if d.get("reason"):
        lines.append(f"Needs: {d['reason']}")
    return "\n".join(lines)


def _with_chat(body: str, transcript: str) -> str:
    return body + (f"\n\nConversation:\n{transcript}" if transcript else "")


def _tag(source: str) -> str:
    return f" ({source})" if source else ""


def record_lead(state: BookingState, lead: dict, sid: str, transcript: str = "", source: str = "") -> bool:
    """Visitor needs a founder and left an email (B7). False if already done."""
    if state.handoff_sent:
        return False
    outcome = "founder needed"
    leads.save(sid, lead, outcome, source=source)
    subject = f"Chat handoff: founder needed{_tag(source)}: {lead.get('restaurant') or lead['email']}"
    _alert(subject, _with_chat(_details_text(lead), transcript))
    state.lead_saved = state.handoff_sent = True
    chat_log.log(sid, "lead_saved", outcome=outcome)
    return True


def live_update(sid: str, visitor: str, reply: str, source: str = "", first: bool = False) -> None:
    """ADR 0019: mirror one exchange to the founders' Telegram group right away, in the
    background so the visitor never waits for Telegram."""
    head = f"{'New chat' if first else 'Chat'} {sid[-6:]}{_tag(source)}"
    text = f"{head}\nVisitor: {visitor}\nJelena: {reply}"
    threading.Thread(target=telegram.send_long, args=(text,), daemon=True).start()


def finish(sid: str, new_part: str, source: str = "") -> None:
    """The conversation went quiet (or the preview ended). Send it to Telegram (ADR 0015)."""
    if new_part.strip() and not config.TELEGRAM_LIVE:  # with live updates the founders already saw it
        telegram.send_long(f"Chat conversation{_tag(source)} {sid[:8]}\n\n{new_part}")
    chat_log.log(sid, "conversation_sent_to_telegram")
