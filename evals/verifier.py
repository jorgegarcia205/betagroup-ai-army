"""
Deterministic verifier — the "rule first, LLM last" guard.

After the LLM produces a verdict, this applies cheap, auditable rules that can
only TIGHTEN the decision: if a hard disqualifier is present it overrides an
"eligible" verdict to "not_eligible". It never turns a rejection into a pass.

This mirrors the production philosophy (a rule-based classifier handled 99.4% of
the real corpus before any LLM was involved). The experiment measures whether
this guard removes the residual false positives the LLM misses — and at what
cost in false negatives (an over-eager rule can wrongly reject a good candidate).

Returns (final_verdict, list_of_reasons_the_guard_fired).
"""
from __future__ import annotations

import re
from datetime import datetime

CURRENT_YEAR = datetime.now().year
MIN_YEARS = 5

_INPROGRESS = re.compile(r"in progress|ongoing|pursuing|expected|cursando|en curso",
                         re.I)
_MASTER = re.compile(r"\bmaster'?s?\b|\bm\.?sc\b|\bmaestr", re.I)
_YEAR = re.compile(r"\b(19|20)\d{2}\b")


def _base_degree(cv: str) -> str:
    """The undergraduate entry = text after 'Education:' up to the first period."""
    m = re.search(r"Education:\s*(.+?)\.", cv, re.I)
    return (m.group(1) if m else cv).lower()


def _master_clause(cv: str) -> str | None:
    """Return the sentence that mentions the master's, if any."""
    for sentence in re.split(r"(?<=\.)\s+", cv):
        if _MASTER.search(sentence):
            return sentence
    return None


def verify(cv: str, llm_verdict: str) -> tuple[str, list[str]]:
    if llm_verdict != "eligible":
        return llm_verdict, []                 # guard only tightens

    reasons: list[str] = []
    base = _base_degree(cv)

    # 1) Base profession must be Civil Engineer (not architect/technologist/etc.)
    if "civil engineer" not in base or any(
        bad in base for bad in ("technolog", "architect", "scientist",
                                "mechanical", "industrial")):
        reasons.append("base_degree_is_not_civil_engineer")

    master = _master_clause(cv)
    if master is None:
        # 2) No master's at all (a specialization is not a master's)
        reasons.append("no_masters_degree_found")
    else:
        # 3) Master must be completed: not in-progress, and with a valid past year
        if _INPROGRESS.search(master):
            reasons.append("masters_in_progress_or_expected")
        years = [int(y) for y in re.findall(r"(?:19|20)\d{2}", master)]
        if not years:
            reasons.append("masters_has_no_graduation_year")
        elif max(years) > CURRENT_YEAR:
            reasons.append("masters_graduation_year_in_the_future")
        # 4) Master must be in an engineering field
        if "engineering" not in master.lower():
            reasons.append("masters_not_in_engineering")

    # 5) Experience threshold
    exp = re.search(r"(\d+)\s+years", cv, re.I)
    if exp and int(exp.group(1)) < MIN_YEARS:
        reasons.append(f"experience_below_{MIN_YEARS}_years")

    final = "not_eligible" if reasons else "eligible"
    return final, reasons
