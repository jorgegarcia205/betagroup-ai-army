# Research interests & motivation

## Why AI safety, for me

I did not arrive at AI safety from theory. I arrived at it by *building* — I
designed and run a fleet of ~26 autonomous LLM agents that take real actions
over real data (evaluating people against legal requirements, searching millions
of public contracts, drafting formal proposals). Doing that in production forced
me to confront, concretely, the questions the field cares about: How do you know
an autonomous evaluator is right? What happens when it is confidently wrong and
no one notices? How much of a system can you safely let act without a human in
the loop?

Those questions stopped being abstract the day an agent silently did the *wrong*
thing — passing an unqualified candidate, or quietly narrowing a search so it
returned a fraction of the real results. The failures that scared me were never
the loud crashes; they were the plausible, silent ones. That is the same
intuition that motivates a lot of AI-safety research, and I want to study it
rigorously rather than only patch it in production.

## What I want to work on

Three connected areas, all grounded in things I have already built:

1. **LLM evaluations & trustworthiness (LLM-as-a-judge).** I rely on LLMs to
   make gated judgments; I have seen how prompt framing changes the *direction*
   of their errors. I ran an experiment ([`../evals/`](../evals/), 40 cases, two
   models, 95% CIs) showing that prompt-only fixes were modest and
   model-dependent, but a cheap **deterministic verifier in front of the LLM**
   drove the harmful-direction (false-positive) error to zero on rule-expressible
   requirements — cheaper than upgrading the model. I want to study the boundary:
   *which* decisions can be safely delegated to a deterministic check, and when a
   model genuinely *follows* a rule versus merely appears to.

2. **Error propagation & oversight in multi-agent systems.** My system is a live
   case study in decomposing work across agents of increasing autonomy. A small
   mistake by one agent — a mis-extracted field, a mis-parsed requirement — can
   flow downstream and corrupt a final decision. I am interested in *where*
   automated checks and human review should intervene to catch such errors early,
   and how to keep that oversight cheap enough that the system stays fast and
   useful.

3. **Honesty & hallucination as engineering targets.** The single most useful
   thing I did was treat "no evidence → do not claim" as a hard rule and then
   *validate the model's output rather than trust it*. I want to understand how
   far that can be pushed, and where it breaks.

## What I bring

- A **builder's instinct for where systems actually fail**, from operating
  autonomous agents on real, high-stakes data — not a toy setting.
- Comfort **across cultures and disciplines** (I work across Colombia and Spain,
  bridging legal, technical, and product domains) — which the fellowship
  explicitly values.
- Strong engineering: async multi-agent systems, LLM orchestration with
  reliability guarantees, data pipelines over 50k+ records, evaluation design.

## The question I want to investigate in Singapore

**How can we prevent small errors from propagating through a multi-agent system
and becoming bad final decisions?**

More specifically: *where* should automated checks and human review intervene to
catch errors early, while keeping the system fast, useful, and affordable?

I have felt this problem directly. In my own fleet a quiet mistake by one agent
can survive into a final output simply because nothing downstream was positioned
to catch it. My eval work is a first step: it shows that a cheap deterministic
check placed *in front of* an LLM can remove a whole class of errors for a
fraction of the cost of a stronger model. I want to generalize that — to map, along
a chain of agents, where a check (automated or human) yields the most safety per
unit of cost and latency.

## What I want the outcome to be

I want the result to be **more than a paper.** I want to build an **open-source
evaluation tool** and a **practical oversight prototype** that organizations can
test in their own multi-agent systems — something that helps a team see where
errors enter a chain of agents and where a check would catch them earliest. The
fellowship is where I want to turn a builder's intuition into rigorous method,
alongside mentors working on evaluations, oversight, and trustworthy autonomous
systems.
