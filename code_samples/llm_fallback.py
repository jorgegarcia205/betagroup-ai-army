"""
Sanitized excerpt: provider-agnostic LLM calls with a reliability-first
fallback chain and JSON-safe structured output.

Key idea: a transient error (503/429/timeout) retries; an ACCOUNT-LEVEL error
(spend cap / billing) skips the entire provider — retrying the same account
only fails again and wastes time/quota.
"""
from __future__ import annotations

import json
import re

# Ordered by cost/latency. The client walks down this chain on failure.
DEFAULT_CHAIN = [
    ("gemini", "gemini-2.5-flash"),
    ("openai", "gpt-4o-mini"),
    ("anthropic", "claude-haiku"),
]

_ACCOUNT_LEVEL = ("spending cap", "spend cap", "billing", "quota exceeded",
                  "monthly", "account")
_TRANSIENT = ("503", "429", "500", "502", "overloaded", "rate_limit",
              "timeout", "timed out", "unavailable", "connection")


def is_account_level_error(err: str) -> bool:
    e = err.lower()
    return any(k in e for k in _ACCOUNT_LEVEL)


def is_transient(err: str) -> bool:
    e = err.lower()
    return any(k in e for k in _TRANSIENT)


def build_fallback_chain(failed_provider: str, last_error: str) -> list[tuple[str, str]]:
    """Next (provider, model) options to try after a failure."""
    chain = list(DEFAULT_CHAIN)
    if is_account_level_error(last_error):
        # Skip EVERY model of the failed provider, not just the failed model.
        chain = [(p, m) for (p, m) in chain if p != failed_provider]
    return chain


def parse_json_lenient(raw: str) -> dict:
    """LLMs wrap JSON in markdown fences or prose. Strip and parse robustly."""
    cleaned = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found in model output")
    return json.loads(cleaned[start:end + 1])


async def chat_json(call_provider, system_prompt, user_prompt, max_retries=3):
    """Call the model and return validated JSON, retrying on malformed output
    or transient/account errors by walking the fallback chain.

    `call_provider(provider, model, system, user) -> str` is injected.
    """
    provider, model = DEFAULT_CHAIN[0]
    last_error = ""
    for attempt in range(max_retries):
        try:
            raw = await call_provider(provider, model, system_prompt, user_prompt)
            return parse_json_lenient(raw)          # may raise on bad JSON
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            chain = build_fallback_chain(provider, last_error)
            if not chain or (not is_transient(last_error)
                             and not is_account_level_error(last_error)
                             and "json" not in last_error.lower()):
                raise
            provider, model = chain[0]              # degrade and retry
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_error}")
