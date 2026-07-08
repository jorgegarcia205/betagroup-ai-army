# Research interests & motivation

## The question I want to investigate

**How can we prevent small errors from propagating through a multi-agent system
and becoming bad final decisions?**

More specifically: *where* should automated checks and human review intervene to
catch errors early, while keeping the system fast, useful, and affordable?

Everything below is in service of that question.

## How I found it

I did not arrive at AI safety from theory. I arrived at it by *building* — I
designed and run a fleet of ~26 autonomous LLM agents that take real actions over
real data (evaluating people against legal requirements, searching millions of
public contracts, drafting formal proposals). Doing that in production, I watched
a single quiet mistake by one agent — a mis-extracted field, a mis-parsed
requirement — survive downstream into a final output, simply because nothing
between them was positioned to catch it. The failures that scared me were never
the loud crashes; they were the plausible, silent ones that propagate.

That is the problem I want to study rigorously instead of only patching in
production: not "is one model right?" but "how does error *flow* through a chain
of agents, and where do we best interrupt it?"

## Why I am positioned to work on it

- **I already have the testbed.** My system is a live multi-agent pipeline with an
  explicit mission queue and mandatory human-review checkpoints — a real
  environment in which to study where errors enter and propagate.
- **I already have a first result.** A controlled experiment of mine
  ([`../evals/`](../evals/)) shows that a cheap **deterministic check placed *in
  front of* an LLM** removes a whole class of errors for a fraction of the cost of
  a stronger model, while prompt-only fixes were modest and model-dependent. That
  is the smallest version of the placement question: *one* check, in *one* spot.
- **A builder's instinct for where systems actually fail**, from operating agents
  on high-stakes data — plus comfort **across cultures and disciplines** (I work
  across Colombia and Spain, bridging legal, technical, and product domains),
  which the fellowship explicitly values.

## The direction: generalize placement into a tool

The natural generalization of my eval is to stop asking about one check in one
spot and start asking: **given a whole chain of agents, where does a check —
automated or human — catch the most error per unit of cost and latency?**

I want the outcome to be **more than a paper.** I want to build an **open-source
evaluation tool** and a **practical oversight prototype** that organizations can
test on their own multi-agent systems: something that maps where errors enter a
pipeline, how far they propagate, and where a checkpoint would catch them
earliest and cheapest. A concrete sketch of that tool is in
[`PROJECT_PROPOSAL.md`](PROJECT_PROPOSAL.md).

## What I want from the fellowship

To turn a builder's intuition into rigorous method — to state this question
precisely, design experiments that could falsify my assumptions about it, and
ship both results and a usable artifact — alongside mentors working on
evaluations, scalable oversight, and trustworthy autonomous systems.
