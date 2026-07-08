"""
Sanitized excerpt: partner discovery over Colombia's SECOP open data API.

Given a theme + minimum contract value, this finds companies with a real track
record so BetaGroup can invite them into a consortium to co-bid. Three ideas
worth showing:

  1. LLM keyword expansion with *cycle memory* — the system remembers, within a
     search cycle, which keywords it already tried, so it explores instead of
     repeating.
  2. Querying ~8M public contracts through the Socrata/SoQL API (public data;
     the app token is an env var, never hardcoded).
  3. Cohort sampling for downstream verification — don't only look at the
     giants-by-value; deliberately sample several complementary cohorts so
     mid-sized but qualified partners aren't missed.
"""
from __future__ import annotations

import os
from collections import defaultdict

SECOP_DATASET = "https://www.datos.gov.co/resource/jbjy-vk9h.json"  # public dataset


def build_soql(keyword: str, min_value: int, since: str | None) -> dict:
    """Build a Socrata (SoQL) query. Exact keyword match first, AI ranks later."""
    where = [f"upper(objeto_del_contrato) like upper('%{keyword}%')",
             f"valor_del_contrato >= {min_value}"]
    if since:
        where.append(f"fecha_de_firma >= '{since}'")
    return {"$where": " AND ".join(where), "$limit": 50000,
            "$$app_token": os.getenv("SECOP_APP_TOKEN", "")}  # never hardcode


KEYWORD_EXPANSION_PROMPT = """You expand a procurement theme into 8-12 exact search
keywords for a contracts database. Return ONLY a JSON list of strings.
Prefer terms that appear verbatim in contract objects; avoid stop-words and
overly generic terms that would match everything."""


async def expand_keywords(call_llm, theme: str, already_used: set[str]) -> list[str]:
    """Expand a theme, then drop anything already tried this cycle (memory)."""
    proposed = await call_llm(KEYWORD_EXPANSION_PROMPT, theme)   # -> list[str]
    return [k for k in proposed if k.lower() not in already_used]


def select_partners_for_verification(profiles: dict[str, dict]) -> dict[str, str]:
    """Pick companies to send to legal (RUP) verification using complementary
    cohorts, so we see a BROAD panorama, not only the biggest by value.

    Excludes public entities and likely consortia (they have no standalone RUP).
    Returns {company_id: reason_it_was_selected}.
    """
    private = [cid for cid, p in profiles.items()
               if not p.get("is_public_entity") and not p.get("is_consortium")]
    selected: dict[str, str] = {}

    def top(metric: str, n: int, reason: str):
        for cid in sorted(private, key=lambda c: profiles[c].get(metric, 0),
                          reverse=True)[:n]:
            selected.setdefault(cid, reason)

    top("theme_value_total", 50, "top_value_on_theme")     # the big, established
    top("theme_contract_count", 50, "top_count_on_theme")  # recurrent experts
    top("distinct_entities", 30, "most_diversified")       # broad reputation
    # + a random sample of the mid-tier so we don't only chase the giants
    return selected


class RunningKeywordMemory:
    """Remembers, per normalized theme, how productive each keyword has been
    (running averages of new companies / contracts it surfaced) so future
    cycles can prioritize keywords that historically pay off."""

    def __init__(self):
        self._stats: dict[tuple[str, str], dict] = defaultdict(
            lambda: {"uses": 0, "avg_new": 0.0})

    def record(self, theme: str, keyword: str, new_found: int) -> None:
        s = self._stats[(theme, keyword)]
        n = s["uses"]
        s["avg_new"] = (s["avg_new"] * n + new_found) / (n + 1)  # incremental mean
        s["uses"] = n + 1
