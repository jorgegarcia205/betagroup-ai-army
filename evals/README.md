# Mini-eval: reducing false-positive PASS verdicts from an LLM evaluator

A small but real experiment on **LLM-as-a-judge reliability**. When an LLM
decides whether a candidate meets a strict, disqualifying requirement, the
dangerous error is the **false positive** — passing someone who should be
rejected. This measures three ways to reduce it, across two models, and reports
the harmful-direction error with confidence intervals, cost, and latency.

The point is the *method* and an honest reading of the result, not a headline.

## Why this is safety-relevant

This is a miniature of a general oversight problem: an LLM is used as an
evaluator whose verdict gates a decision, and the two error types have
**asymmetric cost** — a false negative is a missed good candidate; a false
positive silently lets an unqualified one through, the failure that survives to
cause harm. Measuring and driving down the harmful-direction error — and knowing
*when a cheap deterministic check beats a more expensive model* — is the shape of
practical evals / scalable-oversight work.

## Conditions

1. **naive** — a plain "read it and decide" prompt.
2. **grounded** — an evidence-first prompt: absence of evidence → reject;
   in-progress/undated degrees are not "completed"; a specialization is not a
   master's; the base profession must match.
3. **grounded + verifier** — the grounded verdict, then a cheap **deterministic
   guard** ([`verifier.py`](verifier.py)) that can only *tighten* an "eligible"
   verdict (checks degree completion, dated graduation, field, base profession,
   experience threshold). This mirrors the production philosophy — *rule first,
   LLM last* — where a rule-based classifier handled 99.4% of the real corpus
   before any LLM was involved.

## Method

- **Dataset:** 40 synthetic CVs (`dataset.json`) — 25 ineligible, 15 eligible —
  written without giveaways, spanning realistic traps (in-progress, undated, and
  specialization-not-master degrees; wrong-field master; wrong base profession;
  no master; insufficient experience).
- **Models:** `gpt-4o-mini` and `gpt-4o`, temperature 0, 5 runs/candidate,
  majority vote.
- **Metrics:** accuracy; false-positive rate with a **Wilson 95% CI**;
  false-negative rate; total cost (USD) and average latency.

## Results

```
40 candidates (25 ineligible, 15 eligible) | 5 runs/candidate

gpt-4o-mini   (cost $0.024 | 1.2 s/call)
  condition            acc     FPR    FPR 95% CI    FNR   FP  FN
  naive               0.925    0.12   [0.04,0.30]   0.0    3   0
  grounded            0.925    0.12   [0.04,0.30]   0.0    3   0
  grounded+verifier   1.000    0.00   [0.00,0.13]   0.0    0   0

gpt-4o        (cost $0.41  | 1.0 s/call)
  condition            acc     FPR    FPR 95% CI    FNR   FP  FN
  naive               0.950    0.08   [0.02,0.25]   0.0    2   0
  grounded            0.975    0.04   [0.01,0.20]   0.0    1   0
  grounded+verifier   1.000    0.00   [0.00,0.13]   0.0    0   0
```

## Findings

1. **The stronger model has a lower baseline error.** `gpt-4o` starts at 0.08
   FPR vs `gpt-4o-mini`'s 0.12 — more capability, fewer wrong passes, as expected.

2. **Prompt grounding helped — but only for the stronger model, and modestly.**
   It moved `gpt-4o` from 0.08 → 0.04, but did **nothing** for `gpt-4o-mini`
   (0.12 → 0.12) on this set. This is more sober than an earlier n=18 pilot,
   where grounding appeared to help the small model a lot — a good reminder that
   **small evals overstate effects**; expanding the set changed the conclusion.

3. **A free deterministic guard beat both prompts and both models: FPR → 0.**
   The verifier eliminated the residual false positives for both models, with no
   false negatives introduced.

4. **Cheaper *and* better than scaling the model.** `gpt-4o-mini + verifier`
   (FPR 0, **$0.024**) beat `gpt-4o` alone (FPR 0.04, **$0.41**, ~17× the cost).
   For requirements that are *rule-expressible*, spending on a bigger model is
   the wrong lever; a cheap external check dominates.

5. **Wide confidence intervals.** With 25 ineligible cases the CIs overlap, so
   the point differences between prompts should not be over-read — the robust,
   separable result is the verifier reaching 0.

## Honest caveat (why the verifier looks perfect)

The verifier scores 0 FPR / 0 FNR here **because every disqualifier in this
dataset is expressible as a rule** (a date, a field, a threshold). That is by
construction. In the real corpus, the interesting and hard cases are exactly the
ones that are **not** cleanly rule-expressible — which is why production keeps
the LLM for the long tail after rules handle the 99.4%. So the honest takeaway is
not "rules win"; it is *"put the deterministic check first, and reserve the LLM
(and the eval budget) for the fraction rules genuinely cannot decide."*

## Limitations & next steps

Small n (40), two models from one provider, synthetic data, one requirement,
majority-of-5. Natural extensions: more providers, many more traps (especially
non-rule-expressible ambiguity), bootstrap CIs, and measuring the *rule-coverage
frontier* — what fraction of real requirements a deterministic verifier can
safely decide before the LLM must take over.

## Reproduce

```bash
cd evals
pip install -r ../requirements.txt
OPENAI_API_KEY=... python run_eval.py --models gpt-4o-mini,gpt-4o --runs 5
# writes results.json and prints the tables above
```

## Takeaway

A cheap, auditable check placed *in front of* the LLM removed the harmful-
direction error entirely on rule-expressible requirements — for a fraction of
the cost of a stronger model — while prompt-only fixes were modest and
model-dependent. The generalizable lesson: **don't assume an LLM judge is
reliable; measure the error that actually hurts, and prefer a deterministic guard
wherever the decision is expressible as one.**
