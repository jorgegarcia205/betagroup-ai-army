# Research interests & motivation

> **Draft — make it your own.** This is a starting point written in first person
> for the fellowship application. Edit freely so it sounds like you; replace the
> bracketed notes.

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
   of their errors. I ran a small experiment ([`../evals/`](../evals/)) showing
   that evidence-grounding cut an evaluator's harmful-direction (false-positive)
   error ~3×, but did **not** eliminate it. I want to work on how to measure and
   improve judge reliability where the two error types have asymmetric cost, and
   on when a model *follows* a rule versus merely appears to.

2. **Oversight of autonomous / multi-agent systems.** My system is a live case
   study in decomposing work across agents of increasing autonomy with mandatory
   human checkpoints. I am interested in scalable oversight: which decisions can
   be safely delegated, how to make an agent's reasoning legible enough to
   audit, and how to detect silent misbehavior before it propagates.

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

## What I want from the fellowship

To convert a builder's intuitions into **research** — to learn to state a
safety-relevant hypothesis precisely, design an experiment that could falsify it,
and contribute results the field can build on. [Add: the specific research areas
/ mentors you are ranking, and one concrete question you would want to pursue.]
