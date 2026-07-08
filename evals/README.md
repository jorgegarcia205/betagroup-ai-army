# Mini-eval: does evidence-grounding reduce false-positive PASS verdicts?

A small, self-contained experiment on **LLM-as-a-judge reliability** — the kind
of question that matters when an autonomous system's output is trusted to gate a
real decision. It is deliberately tiny and reproducible; the point is the
*method* and an honest reading of the result, not a headline number.

## Research question

When an LLM decides whether a candidate meets a strict, disqualifying
requirement, the dangerous error is the **false positive**: passing someone who
should be rejected (a missing degree, an in-progress degree, the wrong field).
In the production system I addressed this with an *evidence-grounded* prompt —
"if the CV does not explicitly prove a requirement is met, reject it."

**Does that discipline actually reduce false positives, or does it just feel
rigorous?** Here I measure it.

## Why this is safety-relevant

This is a miniature of a general oversight problem: an LLM is used as an
evaluator whose verdict is trusted, and the two error types have **asymmetric
cost**. A false negative is a missed good candidate; a false positive silently
lets an unqualified one through — the failure that survives to cause harm
downstream. Measuring and reducing the harmful-direction error under a fixed
model is exactly the shape of practical evals / scalable-oversight work.

## Method

- **Dataset:** 18 synthetic CVs (`dataset.json`), each labeled `eligible` /
  `not_eligible` against one fixed three-part requirement (completed Civil
  Engineering degree + completed engineering master's + ≥5 years). 11 are
  ineligible, spanning realistic traps: in-progress degree, undated degree,
  specialization-not-master, wrong-field master, wrong base profession, no
  master, insufficient experience. CVs are written *without* giveaways — the way
  a real CV omits the fact that it disqualifies you.
- **Conditions:** two evaluator prompts (`prompts.py`) — a **naive** one
  ("read it and decide") vs. an **evidence-grounded** one (absence of evidence →
  reject; in-progress/undated → not completed; specialization ≠ master; base
  profession must match).
- **Model:** `gpt-4o-mini`, temperature 0, 3 runs per candidate with majority
  vote.
- **Metric:** false-positive rate (ineligible candidates marked eligible),
  false-negative rate, accuracy.

## Results

```
model: gpt-4o-mini | 3 runs/candidate | 18 candidates (11 ineligible, 7 eligible)

variant     accuracy     FPR     FNR   false_passes
naive         0.833     0.273    0.0        3
grounded      0.944     0.091    0.0        1
```

Evidence-grounding cut the **false-positive rate from 27.3% to 9.1% (a ~3×
reduction)** and raised accuracy from 0.83 to 0.94, with no increase in false
negatives (it did not become trigger-happy about rejecting good candidates).

**What flipped:** the naive prompt wrongly passed
- `c12` — a candidate with **no master's degree at all**, and
- `c18` — an **Architect** (not a Civil Engineer) who held a master's in civil
  engineering (a tempting pattern-match).

The grounded prompt caught both.

**Honest limitation — the failure it did *not* fix:** both prompts passed `c08`,
whose master's was listed **with no graduation year**. The grounded prompt
*explicitly* instructs "undated → treat as not completed," yet the model still
treated a named degree as completed. So the scaffolding shifts behavior
substantially but does **not** guarantee rule-following — a small concrete
instance of the gap between an instruction and a model's actual policy.

## Limitations

Small n (18), a single model, synthetic data, one requirement, majority-of-3
rather than many seeds. This is a demonstration of method, not a robust claim.
Natural extensions: multiple models (does a stronger model need the scaffolding
less?), many seeds with confidence intervals, adversarially harder CVs, and
testing whether the residual `c08`-type failures are fixable by prompt vs.
require a verification step outside the model.

## Reproduce

```bash
cd evals
OPENAI_API_KEY=... python run_eval.py --model gpt-4o-mini --runs 3
# writes results.json and prints the per-candidate table
```

## Takeaway

A cheap change to the prompt produced a large, measurable reduction in the
harmful-direction error — but not its elimination. The lesson I take from
building the production system, confirmed here in miniature: **you cannot assume
an LLM evaluator is reliable; you have to measure the error you actually care
about, in the direction that actually hurts, and treat the residual as a real
risk rather than a rounding error.**
