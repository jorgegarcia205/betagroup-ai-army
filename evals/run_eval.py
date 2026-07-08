"""
Mini-eval: does evidence-grounding reduce false-positive PASS verdicts?

Runs every synthetic candidate through two evaluator prompts (naive vs.
evidence-grounded) and compares each verdict to a ground-truth label. Reports,
per prompt: false-positive rate (an UNqualified candidate wrongly passed — the
safety-relevant error), false-negative rate, and accuracy.

Self-contained: uses only the local synthetic dataset. No production data, no
database, no secrets. Requires OPENAI_API_KEY in the environment and `openai`.

Usage:
    OPENAI_API_KEY=... python run_eval.py [--model gpt-4o-mini] [--runs 1]
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

from prompts import NAIVE_SYSTEM, GROUNDED_SYSTEM, build_user_prompt

HERE = Path(__file__).parent


def load_dataset():
    data = json.loads((HERE / "dataset.json").read_text(encoding="utf-8"))
    return data["requirement"], data["candidates"]


def call_model(client, model, system, user):
    resp = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
    )
    raw = resp.choices[0].message.content
    verdict = (json.loads(raw).get("verdict") or "").strip().lower()
    return "eligible" if verdict == "eligible" else "not_eligible"


def metrics(preds, labels):
    """preds/labels: lists of 'eligible'/'not_eligible'."""
    fp = fn = tp = tn = 0
    for p, y in zip(preds, labels):
        if y == "not_eligible" and p == "eligible":
            fp += 1                      # passed someone who should be rejected
        elif y == "eligible" and p == "not_eligible":
            fn += 1
        elif y == "eligible":
            tp += 1
        else:
            tn += 1
    n_neg = fp + tn
    n_pos = tp + fn
    return {
        "accuracy": round((tp + tn) / len(labels), 3),
        "false_positive_rate": round(fp / n_neg, 3) if n_neg else 0.0,
        "false_negative_rate": round(fn / n_pos, 3) if n_pos else 0.0,
        "false_positives": fp, "false_negatives": fn,
        "n": len(labels), "n_ineligible": n_neg, "n_eligible": n_pos,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="gpt-4o-mini")
    ap.add_argument("--runs", type=int, default=1)
    args = ap.parse_args()

    from openai import OpenAI
    client = OpenAI()

    requirement, candidates = load_dataset()
    labels = [c["label"] for c in candidates]

    variants = {"naive": NAIVE_SYSTEM, "grounded": GROUNDED_SYSTEM}
    per_variant_preds: dict[str, list[str]] = {}
    per_candidate = defaultdict(dict)

    for name, system in variants.items():
        # Majority vote across runs for stability (default 1 run).
        votes = [defaultdict(int) for _ in candidates]
        for _ in range(args.runs):
            for i, c in enumerate(candidates):
                pred = call_model(client, args.model, system,
                                  build_user_prompt(requirement, c["cv"]))
                votes[i][pred] += 1
        preds = ["eligible" if v["eligible"] >= v["not_eligible"] else "not_eligible"
                 for v in votes]
        per_variant_preds[name] = preds
        for c, p in zip(candidates, preds):
            per_candidate[c["id"]][name] = p

    results = {name: metrics(preds, labels)
               for name, preds in per_variant_preds.items()}
    results["_model"] = args.model
    results["_runs"] = args.runs
    (HERE / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Console report
    print(f"\nModel: {args.model} | runs/candidate: {args.runs} | "
          f"candidates: {len(candidates)} "
          f"({results['naive']['n_ineligible']} ineligible, "
          f"{results['naive']['n_eligible']} eligible)\n")
    print(f"{'variant':<10} {'accuracy':>9} {'FPR':>7} {'FNR':>7} {'false_pass':>11}")
    for name in ("naive", "grounded"):
        m = results[name]
        print(f"{name:<10} {m['accuracy']:>9} {m['false_positive_rate']:>7} "
              f"{m['false_negative_rate']:>7} {m['false_positives']:>11}")

    print("\nPer-candidate (label | naive | grounded):")
    for c in candidates:
        pc = per_candidate[c["id"]]
        flag = "  <-- differ" if pc["naive"] != pc["grounded"] else ""
        print(f"  {c['id']} [{c['trap']:<28}] {c['label']:<12} | "
              f"{pc['naive']:<12} | {pc['grounded']:<12}{flag}")


if __name__ == "__main__":
    main()
