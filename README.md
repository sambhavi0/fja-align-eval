# fja-align-eval

An evaluation harness inspired by the position paper
**"LLM Alignment should go beyond Harmlessness–Helpfulness and incorporate Human Agency"**
(Naseem, Chakraborty, Chang, Dras, Nakov, Peng, Poria).

> **Unofficial.** This is an independent implementation by a reader of the paper,
> not the authors' code. The paper is a position paper: it proposes the
> Flourishing–Justice–Autonomy (FJA) framework conceptually and publishes no
> algorithm, prompts, or benchmark. Everything here is my operationalisation.

## What the paper claims
1. Many alignment failures come from operational choices in post-training and
   deployment (rigid filters, context-insensitive rules), not from the HHH
   principles themselves.
2. Alignment should be dynamic and participatory, preserving pluralism, autonomy
   and wellbeing, which the paper formalises as **FJA**.

## What this repo does
It turns the claim into a testable hypothesis:

> A context-sensitive FJA framing reduces over-refusal and improves cultural
> and autonomy handling versus a rigid HHH framing, **without** increasing
> unsafe compliance.

Pipeline (`run_eval.py`):
1. `fja/scenarios.json`: 11 scenarios (cultural, religious, health, legal,
   operator-constraint, autonomy, plus 2 genuinely harmful controls).
2. Three conditions (`fja/prompts.py`): `baseline` (no system prompt), `hhh`
   (rigid HHH), `fja` (FJA with a hard safety limit).
3. `fja/judge.py`: LLM judge scores Flourishing, Justice, Autonomy, plus
   Helpfulness / Harmlessness / Honesty on 1–5, and flags refusals and harmful uplift.
4. Aggregates: per-dimension means, **over-refusal rate** (refused when it
   shouldn't), **unsafe-compliance rate** (complied when it should refuse).

## Run
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="Use your anthropic key"
python run_eval.py --model claude-sonnet-5-5 --judge-model claude-sonnet-5-5
python run_eval.py --dry-run    # offline pipeline check
```
Outputs: `results/raw.jsonl`, `results/summary.md`.

## Limitations (read before citing any numbers)
- 11 scenarios is a smoke test, not a benchmark. No significance testing.
- The judge is an LLM, possibly the same model family as the generator
  (self-preference bias). Use a different judge model, and hand-check samples.
- The FJA prompt is one of many possible operationalisations. The paper's
  "participatory" and "dynamic" elements (stakeholder input, adaptation over
  time, training-time changes) are **not** implemented; this only tests
  prompt-level framing.
- Scenarios were written by one person and encode that person's view of
  what a good answer is, which is itself a pluralism problem.

## Roadmap
- Expand scenarios across languages/regions; add multiple annotators.
- Human-rating subset to calibrate the judge.
- Multi-sample runs with confidence intervals.
- Compare per-context FJA prompts (user-selected values profiles).

## Citation
Naseem et al., *LLM Alignment should go beyond Harmlessness–Helpfulness and
incorporate Human Agency* (position paper). Add the official arXiv/venue link.
