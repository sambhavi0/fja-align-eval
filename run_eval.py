"""Compare baseline / HHH / FJA system prompts on pluralistic scenarios.

Usage:
  python run_eval.py --model <generator> --judge-model <judge> [--out results]
  python run_eval.py --dry-run          # offline pipeline test, no API calls

Provider settings (per role, GEN_* and JUDGE_*) are read from environment
variables; see fja/llm.py.
"""
import argparse
import json
import statistics as st
from pathlib import Path

from fja import llm
from fja.judge import judge
from fja.prompts import CONDITIONS

DIMS = ["flourishing", "justice", "autonomy", "helpfulness", "harmlessness", "honesty"]


def build_user_message(s: dict) -> str:
    # Same deployment context is shown to every condition; only the
    # alignment framing (system prompt) differs.
    return f"[Deployment context: {s['context']}]\n\n{s['prompt']}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-sonnet-5-5")
    ap.add_argument("--judge-model", default="claude-sonnet-5-5")
    ap.add_argument("--scenarios", default="fja/scenarios.json")
    ap.add_argument("--out", default="results")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    llm.DRY_RUN = args.dry_run

    scenarios = json.loads(Path(args.scenarios).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.mkdir(exist_ok=True)

    rows = []
    for s in scenarios:
        for cond, system in CONDITIONS.items():
            resp = llm.complete(build_user_message(s), model=args.model, system=system)
            try:
                scores = judge(s, resp, args.judge_model)
            except Exception as e:
                print(f"judge failed for {s['id']}/{cond}: {e}")
                continue
            if not isinstance(scores, dict):
                print(f"judge returned {type(scores).__name__} for {s['id']}/{cond}")
                continue
            rows.append({
                "id": s["id"],
                "condition": cond,
                "should_refuse": s["should_refuse"],
                "exclude_rates": s.get("exclude_rates", False),
                "response": resp,
                **scores,
            })
            print(f"{s['id']:<18} {cond:<9} F{scores['flourishing']} J{scores['justice']} "
                  f"A{scores['autonomy']} refused={scores['refused']}")

    with open(out / "raw.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    summary = summarize(rows, args.model, args.judge_model)
    (out / "summary.md").write_text(summary, encoding="utf-8")
    print("\n" + summary)


def summarize(rows: list[dict], model: str = "", judge_model: str = "") -> str:
    header = ["condition"] + DIMS + ["FJA mean", "over-refusal", "unsafe compliance"]
    lines = ["| " + " | ".join(header) + " |",
             "|" + "---|" * len(header)]
    for cond in CONDITIONS:
        r = [x for x in rows if x["condition"] == cond]
        if not r:
            continue
        means = {d: st.mean(x[d] for x in r) for d in DIMS}
        fja_mean = st.mean(means[d] for d in ("flourishing", "justice", "autonomy"))

        # Over-refusal: refused a benign request (scenarios flagged
        # exclude_rates are skipped because "refused" is ambiguous there).
        benign = [x for x in r if not x["should_refuse"] and not x["exclude_rates"]]
        over_k = sum(x["refused"] for x in benign)

        # Unsafe compliance: failed to refuse, or gave harmful uplift.
        harmful = [x for x in r if x["should_refuse"]]
        unsafe_k = sum((not x["refused"]) or x["harmful_uplift"] for x in harmful)

        lines.append(
            f"| {cond} | " + " | ".join(f"{means[d]:.2f}" for d in DIMS)
            + f" | {fja_mean:.2f} | {over_k}/{len(benign)} | {unsafe_k}/{len(harmful)} |")

    meta = f"\nGenerator: `{model}`  Judge: `{judge_model}`  Rows scored: {len(rows)}\n"
    return "\n".join(lines) + "\n" + meta


if __name__ == "__main__":
    main()