# Project sketch — an oversight-placement tool for multi-agent systems

*Working title:* **Interlock** — *find where to catch errors before they become
bad decisions.*

> A concrete sketch of what I would build during the fellowship. It generalizes
> my [evaluation study](../evals/) from "one check in one place" to "where, along a
> whole chain of agents, should checks go?"

## Problem

Multi-agent LLM systems are chains: an agent's output is the next agent's input.
A small, quiet error early in the chain (a mis-extracted field, a mis-parsed
requirement) can propagate and corrupt the final decision — the failure mode that
is hardest to see and most dangerous. Teams add checks (deterministic validators,
LLM-judges, human review) mostly by intuition. There is no principled way to
answer: **which checks, in which positions, catch the most error for the least
cost and latency?**

## Why this is grounded, not hypothetical

I am not proposing this from a blank page. I am proposing to **generalize what my
production system already does piecemeal** — and to systematize failures I have
already watched happen. The tool's components each exist, in embryonic form, in a
system I run today:

| Tool component | Already exists in my system as… |
|---|---|
| **Tracer** (log every hand-off) | an asynchronous **mission queue** where every agent-to-agent hand-off is already a durable database row, plus per-action logs |
| **Deterministic check before the LLM** | a **rule-based classifier that decides 99.4%** of cases (homogenizing 50k+ records against an official taxonomy) *before* any LLM is called |
| **Human checkpoint placement** | mandatory **`review` states** and an explicit **human index-review gate** before a proposal is generated — checkpoints already sit at chosen points in the chain |
| **A measured placement result** | my [eval](../evals/): at the judge stage, a **$0.02 deterministic check beat a $0.41 model upgrade** — one real point on the safety-per-cost frontier |

And the failure mode is not theoretical — I have fixed real instances of it:

- A scraper silently captured a **job title instead of the person's name**; the
  wrong value flowed into the database and into every downstream evaluation,
  invisible until someone inspected it.
- A search agent silently chose a **narrower filter** ("Doctorate in Economics"
  instead of "Economics"), quietly collapsing a result set from **803 to 51** — an
  early-stage error that shrank the entire downstream candidate pool.
- **Duplicate records propagated as inflated counts**: 50,044 rows were only
  **27,956 real people**; any downstream metric that didn't de-duplicate was wrong.

These are exactly the *quiet, propagating* errors the tool is built to locate — and
they are real traces I can use to seed realistic fault models rather than guessing.
The research contribution is turning this hard-won, ad-hoc experience into a
**measurable, reusable method**.

## Core idea

Model the system as a directed graph of stages ending in a decision `D`. Then:

1. **Measure the blast radius of each stage.** For each stage `i`, inject a
   realistic fault and measure `P(D is wrong | fault at i)` — how far errors
   introduced there actually propagate to the final decision. Not all stages are
   equally dangerous; this tells you which ones are.
2. **Characterize candidate checks.** Each check `c` (a deterministic verifier,
   an LLM-judge, a human review step) has a *catch rate* on a given fault type
   and a *cost profile* (latency, $, and false-positive burden — an over-eager
   check wrongly blocks good work).
3. **Optimize placement.** Given a budget on added latency/cost, choose *where*
   to place checks to minimize final-decision error — and expose the
   **safety-per-cost frontier** so a team can pick their point on it.

The one-line objective: **maximize error caught per unit of cost + latency
added.** My eval already showed one striking point on this frontier — a $0.02
deterministic check beat a $0.41 model upgrade. The tool asks that question for
every position in the chain.

## What the tool does (components)

- **Tracer** — lightweight instrumentation that logs each agent's input/output at
  every hand-off, turning a running system into an analyzable graph.
- **Fault injector** — a library of realistic, per-stage fault models to measure
  propagation, with ground-truth final labels.
- **Check library** — pluggable checks (rule-based verifier, LLM-judge, human
  gate) with measured catch-rate and cost profiles.
- **Placement optimizer** — computes recommended checkpoint locations and the
  safety-per-cost frontier (greedy + budgeted search).
- **Report** — a pipeline map highlighting error entry points, propagation paths,
  and where a check earns its keep.

## 3-month MVP (deliberately tractable)

- Instrument **one real chain** I already run (extract → parse requirement →
  LLM-judge → aggregate) plus one public benchmark pipeline.
- Synthetic fault injection at each stage; 3 check types; a greedy placement
  optimizer; one clear visualization.
- Validate against the generalized version of my existing eval set.

**Deliverables:** a pip-installable open-source library + a written analysis (the
paper) reporting per-stage blast radius and the placement frontier on ≥2 systems.

## Why it matters for safety

It is a practical, measurable instrument for **scalable oversight and
defense-in-depth**: it treats "where humans and automated checks should sit in an
autonomous pipeline" as an empirical, optimizable question rather than a matter of
taste — and produces something teams can actually run on their own systems.

## Honest risks & unknowns

- **Fault realism.** Synthetic faults may not match how real agents fail;
  mitigation is to seed them from real traces.
- **Non-stationarity.** Catch rates and costs shift across inputs and models; the
  frontier is a distribution, not a fixed number — CIs everywhere.
- **The human-review check is the hardest to model** (cost, latency, and human
  error itself). I would start with a conservative stub and treat modeling it
  well as a research contribution in its own right.
