"""Checks in code that run on every reply, so the rules do not depend on the AI obeying."""
import re

from app.content import APPROVED_ANSWERS, DISCLOSURE

HANDOFF_REPLY = (
    "That is something one of our founders should answer directly. "
    "If you share your email, a founder will reply to you."
)
PAYMENT_WARNING = (
    "Please do not share card or payment details in this chat. Payment is never taken here, "
    "and I have not stored what you sent. A founder will go over payment with you directly."
)

_NEGATION = re.compile(r"\b(not|no|never|cannot|can't|can not|don't|do not|won't|unable)\b[^.?!]{0,40}$", re.I)

_DOLLAR = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:k|m|thousand|million)\b)?", re.I)
_DOLLAR_WORDS = re.compile(r"\b\d[\d,]*(?:\.\d+)?\s?(?:dollars?|bucks|usd)\b", re.I)
_PERCENT = re.compile(r"\b\d+(?:\.\d+)?\s?(?:%|percent\b|per cent\b)", re.I)
_PERCENT_WORDS = re.compile(
    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|fifteen|twenty|"
    r"thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred)\s?(?:%|percent|per cent)", re.I)
_PROMISE = re.compile(
    r"\b(guarantee[sd]?|promise[sd]?|money[ -]back|you(?:'ll| will) (?:save|make|earn|keep more|increase|boost)|"
    r"(?:will|would) (?:increase|boost|double|raise|improve) your (?:profits?|margins?|revenue|sales|income))", re.I)
_PAYMENT_ASK = re.compile(
    r"\b(?:send|share|provide|enter|give|type)\b[^.?!]{0,20}\b(?:card|cvv|bank|account number|payment details)", re.I)
_LINK = re.compile(r"(?:https?://|www\.)(?!(?:www\.)?useprofitlens\.com)\S+|\b(?:paypal|stripe|venmo|zelle)\.\w+", re.I)
_CARD = re.compile(r"(?<!\d)(?:\d[ -]?){12,18}\d(?!\d)")


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text).lower()


_APPROVED_SQUASHED = _squash(APPROVED_ANSWERS)


def _approved(fragment: str) -> bool:
    """True only if the figure appears whole in the approved answers ($9 does not match $99)."""
    pattern = r"(?<![\d.,])" + re.escape(_squash(fragment).rstrip(".,")) + r"(?![\d]|[.,]\d)"
    return bool(re.search(pattern, _APPROVED_SQUASHED))


def _negated(text: str, start: int) -> bool:
    return bool(_NEGATION.search(text[:start]))


def find_violations(reply: str) -> list[str]:
    """Reasons this reply must not reach the visitor. Empty list means it is safe."""
    problems = []
    for pattern in (_DOLLAR, _DOLLAR_WORDS):
        for m in pattern.finditer(reply):
            if not _approved(m.group()):
                problems.append(f"dollar amount not in approved answers: {m.group()!r}")
    for pattern in (_PERCENT, _PERCENT_WORDS):
        for m in pattern.finditer(reply):
            if not _approved(m.group()):
                problems.append(f"percentage: {m.group()!r}")
    for m in _PROMISE.finditer(reply):
        if not _negated(reply, m.start()):
            problems.append(f"promise or guarantee: {m.group()!r}")
    for m in _PAYMENT_ASK.finditer(reply):
        if not _negated(reply, m.start()):
            problems.append(f"asks for payment details: {m.group()!r}")
    for m in _LINK.finditer(reply):
        problems.append(f"outside link: {m.group()!r}")
    return problems


def remove_dashes(text: str) -> str:
    """Rule 4: no em or en dashes. Ranges become 'to', everything else a comma."""
    text = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", text)
    text = re.sub(r"\s*[–—]\s*", ", ", text)
    text = re.sub(r"\s+-\s+", ", ", text)
    return re.sub(r",\s*,", ",", text)


def strip_markdown(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"^\s*#+\s*", "", text, flags=re.M)
    text = re.sub(r"^\s*[*•]\s+", "", text, flags=re.M)
    # Rule 10, plain text: numbered list items become ordinary sentences.
    text = re.sub(r"^\s*\d+[.)]\s+(.*?)[.;,]?\s*$", r"\1.", text, flags=re.M)
    text = re.sub(r":\s*\n+(?=\S)", ": ", text)
    return text


FOUNDER_LINE = "The call itself is with one of our founders."


def ensure_disclosure(reply: str) -> str:
    """Rule 3: the first reply must say this is an AI and that a founder takes the call.
    Adds only what is missing, so the introduction never appears twice."""
    lower = reply.lower()
    has_ai, has_founder = "ai assistant" in lower, "founder" in lower
    if has_ai and has_founder:
        return reply
    if has_ai:
        return f"{reply} {FOUNDER_LINE}"
    return f"{DISCLOSURE} {reply}"


DETAIL_ASKED = re.compile(r"\b(detail|details|explain|tell me more|more about|in depth|everything)\b", re.I)


_PUSH = re.compile(
    r"(would you like|do you want|shall we|ready|want me|can i help you|how about|or would you like)[^.?!]*"
    r"\b(book|booking|get started|move forward|start|sign up|schedule)\b[^.?!]*\?", re.I)
_ASKED_TO_START = re.compile(r"\b(book|call|start|started|sign up|schedule|next step|analysis|report|how do i)\b", re.I)


def remove_sales_push(reply: str, visitor_message: str) -> str:
    """Rule 15, do not sell: drop a sentence that pushes booking when the visitor did not ask
    about starting. If that leaves nothing, keep the reply as it was."""
    if _ASKED_TO_START.search(visitor_message):
        return reply
    parts = [p for p in re.split(r"(?<=[.!?])\s+", reply.strip()) if p]
    # "Any questions, or would you like to get started?" keeps the neutral question
    parts = [re.sub(r",?\s*or would you like to (book|get started|start)[^?]*\?", "?", p, flags=re.I) for p in parts]
    kept = [p for p in parts if not _PUSH.search(p)]
    return " ".join(kept) if kept else reply


def cap_length(reply: str, visitor_message: str, max_words: int = 80, max_sentences: int = 4) -> str:
    """Rule R6: keep replies short. If the visitor did not ask for detail and the reply is over
    max_words or max_sentences, keep whole sentences from the start. A closing question (for
    example asking for their email) is always kept, so a handoff is never cut off."""
    parts = [p for p in re.split(r"(?<!\b\d[.])(?<=[.!?])\s+", reply.strip()) if p]
    if DETAIL_ASKED.search(visitor_message) or (len(reply.split()) <= max_words and len(parts) <= max_sentences):
        return reply
    closing = parts.pop() if parts[-1].endswith("?") else ""
    budget_s = max_sentences - (1 if closing else 0)
    budget_w = max_words - len(closing.split())
    kept, words = [], 0
    for p in parts:
        n = len(p.split())
        if len(kept) >= budget_s or (kept and words + n > budget_w):
            break
        kept.append(p)
        words += n
    return " ".join(kept + ([closing] if closing else []))


def trim_to_sentence(text: str) -> str:
    """If a reply was cut off by the token cap, end it at the last full sentence."""
    cut = max(text.rfind(". "), text.rfind("? "), text.rfind("! "))
    if text.rstrip().endswith((".", "?", "!")):
        return text.strip()
    return text[: cut + 1].strip() if cut > 0 else text.strip()


def contains_card_number(message: str) -> bool:
    for m in _CARD.finditer(message):
        digits = [int(d) for d in re.sub(r"\D", "", m.group())]
        total = 0
        for i, d in enumerate(reversed(digits)):
            if i % 2:
                d *= 2
                d = d - 9 if d > 9 else d
            total += d
        if total % 10 == 0:
            return True
    return False


def redact_card_numbers(message: str) -> str:
    return _CARD.sub("[card number removed]", message)
