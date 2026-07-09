# Stopping silent errors before they become decisions

### Oversight checkpoints for hierarchical multi-agent AI systems

> Concise, browsable summary of my research proposal. The **authoritative, full
> version (10 pp, with figures and my prior AI-assurance background)** is the
> [technical work sample PDF](TECHNICAL_WORK_SAMPLE.pdf). This page exists so the
> proposal is readable directly on GitHub.

## The question

**Plain language:** if an AI agent makes a small mistake at the beginning of a
workflow, *where* should automated checks or human review intervene so the
mistake does not become a major decision?

**Formal:** which combination of automated verification and human-review
checkpoints most effectively prevents silent, high-cost errors from propagating
through hierarchical multi-agent systems, while preserving task performance,
speed, and cost efficiency?

## Why this is grounded, not hypothetical

I am not proposing this from a blank page. I am proposing to **generalize what my
production system already does piecemeal** — and to systematize failures I have
already watched happen. Each component of the study exists, in embryonic form, in
a system I run today:

| Study component | Already exists in my system as… |
|---|---|
| **Tracer** (log every hand-off) | an asynchronous **mission queue** where every agent-to-agent hand-off is a durable database row, plus per-action logs |
| **Deterministic check before the LLM** | a **rule-based classifier that decides 99.4%** of cases before any LLM is called |
| **Human checkpoint placement** | mandatory **`review` states** and an explicit **human review gate** before consequential outputs |
| **A measured placement result** | my [eval](../evals/): at the judge stage a **$0.02 deterministic check beat a $0.41 model upgrade** — one real point on the safety-per-cost frontier |

And the failure mode is not theoretical — I have fixed real instances of it:

- A scraper silently captured a **job title instead of the person's name**; the
  wrong value flowed downstream into every evaluation, invisible until inspected.
- A search agent silently chose a **narrower filter**, quietly collapsing a result
  set from **803 to 51** — an early error that shrank the whole downstream pool.
- **Duplicate records propagated as inflated counts** (50,044 rows were only
  **27,956 real people**). These are the *quiet, propagating* errors the study
  targets — and real traces I can use to seed realistic fault models.

## Hypotheses

- **H1** — Final-only review detects fewer upstream errors than checkpointed
  oversight, because the original evidence becomes less visible after consolidation.
- **H2** — Fixed checkpoints reduce harmful error propagation but impose
  unnecessary human-review burden on low-risk missions.
- **H3** — Adaptive oversight, triggered by risk signals (missing evidence,
  contradiction, abnormal result counts, high-risk actions), achieves a better
  safety–efficiency trade-off than fixed review.
- **H4** — Deterministic verification combined with evidence-grounded LLM
  evaluation outperforms prompting alone, especially for explicit legal or
  eligibility constraints.

## Experimental design

- **Test bed:** sanitized résumé-evaluation and tender-analysis pipelines, with
  synthetic English/Spanish documents and labelled ground truth (no personal or
  client data).
- **Oversight conditions** (same tasks, models, and inputs across all four):
  **(A)** no review · **(B)** final-output review only · **(C)** fixed review
  after selected ranks · **(D)** adaptive review triggered by risk signals.
- **Fault injection** at the soldier, lieutenant, and captain levels: wrong-field
  extraction, omitted evidence, incorrect filter, contradictory documents,
  fabricated support, malformed structured output, and an injected instruction
  from an untrusted source. Location and intended effect known in advance.

**Metrics:** harmful error rate (high-cost false positives reaching final
output) · propagation depth (hand-offs before detection) · detection location ·
human-review burden (cases/minutes of expert attention) · latency and API cost.

## Preliminary evidence

The repo already contains a reproducible [eval](../evals/): across `gpt-4o-mini`
and `gpt-4o`, prompt-only fixes were modest and model-dependent, while a
deterministic verifier drove false-positive PASS verdicts to 0 — and
`gpt-4o-mini + verifier` (FPR 0, $0.024) beat `gpt-4o` with prompting alone
(FPR 0.04, $0.41, ~17× the cost). That is one point on the safety-per-cost
frontier this study would map across a whole agent hierarchy.

## Deliverables (an 11-week plan)

- A **research paper** on oversight placement and silent-error propagation in
  hierarchical agent systems.
- An **open-source evaluation harness** with controlled fault injection and
  replayable mission logs.
- A **bilingual (EN/ES) benchmark** of realistic, labelled failure cases.
- A **prototype adaptive-oversight policy** using risk signals.
- A **practical implementation note** for public-sector and enterprise teams
  deploying agentic workflows.

## Why it matters

The project treats "where humans and automated checks should sit in an autonomous
pipeline" as an empirical, optimizable question rather than a matter of taste —
and asks not *whether* humans should stay involved, but *how scarce human
attention should be allocated* inside a multi-agent workflow. It is especially
relevant for resource-constrained and Global South contexts: a smaller model plus
a targeted verifier can be safer *and* cheaper than escalating to a larger model.

## Honest risks

Synthetic faults may not match real failures (mitigation: seed from real traces);
catch rates and costs shift across inputs and models (report distributions, not
point values); and the human-review checkpoint is itself the hardest thing to
model — a research contribution in its own right.
