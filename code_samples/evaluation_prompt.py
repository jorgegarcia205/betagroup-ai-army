"""
Sanitized excerpt: the evidence-grounded evaluation prompt and output guard.

This is the most safety-relevant piece of the system. The goal is to stop an
LLM from behaving like a plausible-sounding narrator and force it to behave like
an auditable evaluator: every verdict must cite verbatim evidence, and the
absence of evidence resolves to REJECTION, never to a hopeful "maybe".

The returned JSON is then validated and bounded before it is ever persisted.
"""
from __future__ import annotations

EVALUATION_SYSTEM_PROMPT = """You evaluate professional profiles against the
mandatory and scored requirements of a public tender. Public tenders are
STRICT: a missing degree, an unfinished degree, or one short year of experience
DISQUALIFIES a profile. Zero tolerance on mandatory requirements is the rule.

Classify each MANDATORY requirement as exactly one of:
  - CUMPLE       (meets it, with clear verbatim evidence)
  - NO_CUMPLE    (does not meet it, or evidence shows something essential is missing)
  - OBSERVACION  (a GENUINE ambiguity in the CV, e.g. confusing dates)

CRITICAL RULES
1. EVIDENCE IS MANDATORY. Every conclusion MUST quote text from the CV.
   Do NOT invent data. If the CV says nothing about a requirement, the correct
   answer is NO_CUMPLE — never OBSERVACION, never CUMPLE.
2. A degree with no graduation year AND no evidence it was finished -> treat as
   NOT finished -> NO_CUMPLE.
3. "In progress" / "studying" / "pending thesis" -> NO_CUMPLE (not a maybe).
4. "Related field" is accepted ONLY if the tender says so literally.

Return STRICT JSON:
{
  "verdict": "eligible | manageable | rejected",
  "requirements": {
    "<name>": {"status": "CUMPLE|NO_CUMPLE|OBSERVACION",
               "evidence": "<verbatim text from the CV>"}
  },
  "score_total": <int>, "score_max": <int>,
  "reasoning": "<concise, <=400 words>"
}"""


def sanitize_evaluation(raw: dict, requirements: list[dict]) -> dict:
    """Validate & bound the model's output before persisting it.

    Never trust the shape or magnitude of an LLM's numbers. Coerce types, clamp
    ranges, and fall back to a safe default (rejected) on anything malformed.
    """
    verdict = raw.get("verdict")
    if verdict not in ("eligible", "manageable", "rejected"):
        verdict = "rejected"  # safe default: do not pass on ambiguity

    reqs = raw.get("requirements")
    if not isinstance(reqs, dict):
        reqs = {}

    try:
        score_total = max(0, int(float(raw.get("score_total", 0))))
    except (TypeError, ValueError):
        score_total = 0
    try:
        score_max = max(1, int(float(raw.get("score_max", 0))))
    except (TypeError, ValueError):
        score_max = sum(r.get("weight", 0) for r in requirements) or 100
    score_total = min(score_total, score_max)  # can't exceed the maximum

    reasoning = str(raw.get("reasoning", ""))[:5000]

    return {"verdict": verdict, "requirements": reqs,
            "score_total": score_total, "score_max": score_max,
            "reasoning": reasoning}
