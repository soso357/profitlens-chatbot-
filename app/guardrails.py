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
    return text


def ensure_disclosure(reply: str) -> str:
    """Rule 3: the first reply must say this is an AI and that a founder takes the call."""
    lower = reply.lower()
    if "ai assistant" in lower and "founder" in lower:
        return reply
    return f"{DISCLOSURE} {reply}"


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
