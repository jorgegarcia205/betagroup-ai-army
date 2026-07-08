"""
Mini-eval (extended): does evidence-grounding — and a deterministic verifier on
top of it — reduce false-positive PASS verdicts from an LLM evaluator, and does
a stronger model need the scaffolding less?

Three conditions:
  1. naive               — a plain "read it and decide" prompt
  2. grounded            — an evidence-first prompt (absence of evidence -> reject)
  3. grounded+verifier   — grounded, then a cheap rule-based guard that can only
                           tighten an "eligible" verdict ("rule first, LLM last")

Reports, per (model x condition): accuracy, false-positive rate with a Wilson
95% CI, false-negative rate, cost (USD), avg latency, and FPR by trap category.

Self-contained: local synthetic dataset only. No production data, no secrets.
Requires OPENAI_API_KEY and the `openai` package.

Usage:
    python run_eval.py --models gpt-4o-mini,gpt-4o --runs 5
"""
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from prompts import NAIVE_SYSTEM, GROUNDED_SYSTEM, build_user_prompt
from verifier import verify

HERE = Path(__file__).parent

# Approx. USD per 1M tokens (input, output). Update if prices change.
PRICES = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o":      (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
}


def load_dataset():
    d = json.loads((HERE / "dataset.json").read_text(encoding="utf-8"))
    return d["requirement"], d["candidates"]


def wilson_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (round(max(0, center - half), 3), round(min(1, center + half), 3))


def call(client, model, system, user):
    """One LLM call -> (verdict, in_tokens, out_tokens, latency_s)."""
    for attempt in range(3):
        try:
            t0 = time.time()
            r = client.chat.completions.create(
                model=model, temperature=0,
                response_format={"type": "json_object"},
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            dt = time.time() - t0
            v = (json.loads(r.choices[0].message.content).get("verdict") or "").lower()
            v = "eligible" if v == "eligible" else "not_eligible"
            return v, r.usage.prompt_tokens, r.usage.completion_tokens, dt
        except Exception:
            if attempt == 2:
                return "not_eligible", 0, 0, 0.0
            time.sleep(1.5 * (attempt + 1))


def metrics(preds, cands):
    labels = [c["label"] for c in cands]
    fp = [i for i, (p, y) in enumerate(zip(preds, labels))
          if y == "not_eligible" and p == "eligible"]
    fn = [i for i, (p, y) in enumerate(zip(preds, labels))
          if y == "eligible" and p == "not_eligible"]
    n_neg = sum(1 for y in labels if y == "not_eligible")
    n_pos = len(labels) - n_neg
    correct = sum(1 for p, y in zip(preds, labels) if p == y)
    # FPR by trap category
    by_cat = defaultdict(lambda: [0, 0])   # trap -> [false_pos, total_ineligible]
    for c, p in zip(cands, preds):
        if c["label"] == "not_eligible":
            by_cat[c["trap"]][1] += 1
            if p == "eligible":
                by_cat[c["trap"]][0] += 1
    return {
        "accuracy": round(correct / len(labels), 3),
        "false_positive_rate": round(len(fp) / n_neg, 3) if n_neg else 0.0,
        "fpr_ci95": wilson_ci(len(fp), n_neg),
        "false_negative_rate": round(len(fn) / n_pos, 3) if n_pos else 0.0,
        "false_positives": len(fp), "false_negatives": len(fn),
        "n": len(labels), "n_ineligible": n_neg, "n_eligible": n_pos,
        "fpr_by_category": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_cat.items())},
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default="gpt-4o-mini,gpt-4o")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--workers", type=int, default=10)
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    from openai import OpenAI
    client = OpenAI()
    requirement, cands = load_dataset()

    results = {"_models": models, "_runs": args.runs, "_n": len(cands)}

    for model in models:
        cost = {"in": 0, "out": 0}
        lat = []
        # Build the list of LLM tasks: (condition, cand_index, run)
        tasks = [("naive", i, r) for i in range(len(cands)) for r in range(args.runs)]
        tasks += [("grounded", i, r) for i in range(len(cands)) for r in range(args.runs)]
        sysmap = {"naive": NAIVE_SYSTEM, "grounded": GROUNDED_SYSTEM}
        votes = {"naive": [Counter() for _ in cands],
                 "grounded": [Counter() for _ in cands]}

        def run_task(t):
            cond, i, _ = t
            v, ti, to, dt = call(client, model, sysmap[cond],
                                 build_user_prompt(requirement, cands[i]["cv"]))
            return cond, i, v, ti, to, dt

        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for cond, i, v, ti, to, dt in pool.map(run_task, tasks):
                votes[cond][i][v] += 1
                cost["in"] += ti
                cost["out"] += to
                lat.append(dt)

        def majority(counter):
            return "eligible" if counter["eligible"] >= counter["not_eligible"] else "not_eligible"

        preds_naive = [majority(votes["naive"][i]) for i in range(len(cands))]
        preds_grounded = [majority(votes["grounded"][i]) for i in range(len(cands))]
        # Condition 3: verifier on top of grounded (no extra LLM calls)
        preds_verified = [verify(cands[i]["cv"], preds_grounded[i])[0]
                          for i in range(len(cands))]

        pin, pout = PRICES.get(model, (0, 0))
        usd = round(cost["in"] / 1e6 * pin + cost["out"] / 1e6 * pout, 4)
        results[model] = {
            "naive": metrics(preds_naive, cands),
            "grounded": metrics(preds_grounded, cands),
            "grounded+verifier": metrics(preds_verified, cands),
            "cost_usd_total": usd,
            "avg_latency_s": round(sum(lat) / len(lat), 2) if lat else 0,
            "llm_calls": len(lat),
        }

    (HERE / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    # Console report
    print(f"\nDataset: {len(cands)} candidates | runs/candidate: {args.runs}\n")
    for model in models:
        r = results[model]
        print(f"### {model}  (cost ${r['cost_usd_total']} | "
              f"{r['avg_latency_s']}s/call | {r['llm_calls']} calls)")
        print(f"{'condition':<20}{'acc':>6}{'FPR':>7}{'  FPR 95% CI':>16}{'FNR':>7}{'FP':>4}{'FN':>4}")
        for cond in ("naive", "grounded", "grounded+verifier"):
            m = r[cond]
            ci = f"[{m['fpr_ci95'][0]:.2f},{m['fpr_ci95'][1]:.2f}]"
            print(f"{cond:<20}{m['accuracy']:>6}{m['false_positive_rate']:>7}"
                  f"{ci:>16}{m['false_negative_rate']:>7}"
                  f"{m['false_positives']:>4}{m['false_negatives']:>4}")
        print()


if __name__ == "__main__":
    main()
