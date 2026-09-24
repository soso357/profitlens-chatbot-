"""Gets the next reply from Claude.

Live: the Anthropic API (key in ANTHROPIC_API_KEY), with prompt caching and spend tracking.
Local testing only (TEST_PAGES=1 and MODEL_VIA_CLAUDE_CODE=1): the same model through the
Claude Code login on this Mac, so the widget can be tried before the API key exists.
"""
import os
import subprocess
import tempfile
from dataclasses import dataclass

import anthropic

from app import config, spend

_client = anthropic.Anthropic(max_retries=2, timeout=30.0)
CLAUDE_CODE_ALIAS = "haiku"


@dataclass
class Reply:
    text: str
    stop_reason: str
    cost_usd: float = 0.0
    usage: dict | None = None


def via_claude_code() -> bool:
    return config.TEST_PAGES and config.MODEL_VIA_CLAUDE_CODE


OPENED = "(The visitor opened the chat window.)"


def _api_messages(history: list[dict]) -> list[dict]:
    """The API needs the conversation to start with the visitor. When the widget greeting comes
    first, put a short placeholder in front so the model knows it already introduced itself."""
    if history and history[0]["role"] == "assistant":
        return [{"role": "user", "content": OPENED}] + history
    return history


def ask_claude_code(system: str, history: list[dict]) -> str:
    lines = [f"{'Visitor' if m['role'] == 'user' else 'You'}: {m['content']}" for m in history]
    prompt = ("Conversation so far on the website chat:\n\n" + "\n\n".join(lines)
              + "\n\nWrite only your next reply to the visitor, nothing else.")
    with tempfile.TemporaryDirectory() as tmp:  # outside the project so project hooks do not run
        r = subprocess.run(
            ["claude", "-p", "--model", CLAUDE_CODE_ALIAS, "--system-prompt", system, "--tools", "",
             "--no-session-persistence", "--output-format", "text"],
            input=prompt, capture_output=True, text=True, cwd=tmp, timeout=180,
            env={**os.environ, "PL_WORKFLOW_SUMMARIZER": "1"},
        )
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or r.stdout.strip())
    return r.stdout.strip()


def reply(system: str, history: list[dict]) -> Reply:
    if via_claude_code():
        return Reply(ask_claude_code(system, history), "end_turn")
    response = _client.messages.create(
        model=config.MODEL,
        max_tokens=config.MAX_REPLY_TOKENS,
        system=system,
        messages=_api_messages(history),
        cache_control={"type": "ephemeral"},
    )
    cost = spend.cost_of(response.usage)
    spend.add(cost)
    text = "".join(b.text for b in response.content if b.type == "text").strip()
    usage = {"input_tokens": response.usage.input_tokens,
             "cache_read_tokens": response.usage.cache_read_input_tokens,
             "output_tokens": response.usage.output_tokens}
    return Reply(text, response.stop_reason or "", cost, usage)
