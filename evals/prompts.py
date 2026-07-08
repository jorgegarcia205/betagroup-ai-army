"""The two evaluator prompts under test.

NAIVE is a reasonable, ordinary instruction — the kind most people write.
GROUNDED adds the evidence-first discipline used in the production system:
absence of evidence resolves to rejection, and unfinished/undated degrees do
not count. The experiment measures whether that discipline reduces the rate at
which the model wrongly PASSES an unqualified candidate (a false positive).
"""

NAIVE_SYSTEM = """You evaluate whether a candidate meets a job requirement.
Read the requirement and the CV and decide.
Return ONLY JSON: {"verdict": "eligible" | "not_eligible", "reason": "<short>"}"""

GROUNDED_SYSTEM = """You evaluate whether a candidate meets a job requirement for
a STRICT public tender, where a missing or unproven qualification disqualifies
the candidate. Apply these rules:

1. EVIDENCE IS REQUIRED. If the CV does not explicitly state that a required
   qualification is held and COMPLETED, treat it as NOT met. Absence of
   evidence -> not_eligible. Do not give the benefit of the doubt.
2. A degree that is "in progress", "expected", undated, or with a future
   graduation year is NOT completed -> not_eligible.
3. A specialization is NOT a master's. An MBA is not an engineering master's.
4. The undergraduate degree must match exactly what is required (a different
   base profession does not qualify, even with a relevant master's).
5. All mandatory requirements must be met simultaneously.

Return ONLY JSON:
{"verdict": "eligible" | "not_eligible", "reason": "<cite the CV text you relied on>"}"""


def build_user_prompt(requirement: str, cv: str) -> str:
    return f"REQUIREMENT:\n{requirement}\n\nCANDIDATE CV:\n{cv}\n\nDecide now."
