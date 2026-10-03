# fja-align-eval

An evaluation harness inspired by the position paper
**"LLM Alignment should go beyond Harmlessness–Helpfulness and incorporate Human Agency"**
(Naseem, Chakraborty, Chang, Dras, Nakov, Peng, Poria).

> **Unofficial.** This is an independent implementation by a reader of the paper,
> not the authors' code. The paper is a position paper: it proposes the
> Flourishing–Justice–Autonomy (FJA) framework conceptually and publishes no
> algorithm, prompts, or benchmark. Everything here is my own operationalisation.

## What the paper claims

1. Many alignment failures come from operational choices in post-training and
   deployment (rigid filters, context-insensitive rules), not from the
   Harmless–Helpful–Honest (HHH) principles themselves.
2. Alignment should be dynamic and participatory, preserving pluralism, autonomy
   and wellbeing, which the paper formalises as **FJA**.

## What this repo does

It turns the claim into a testable hypothesis:

> A context-sensitive FJA framing reduces over-refusal and improves cultural
> and autonomy handling compared with a rigid HHH framing, **without**
> increasing unsafe compliance.

Pipeline (`run_eval.py`):

1. `fja/scenarios.json`: 11 scenarios (cultural, religious, health, legal,
   operator-constraint, autonomy, plus 2 genuinely harmful controls).
2. Three conditions (`fja/prompts.py`): `baseline` (no system prompt), `hhh`
   (rigid HHH framing), `fja` (FJA framing with a hard safety limit).
3. `fja/judge.py`: an LLM judge scores Flourishing, Justice and Autonomy, plus
   Helpfulness, Harmlessness and Honesty (1–5), and flags refusals and harmful uplift.
4. Aggregation: per-dimension means, **over-refusal** (refused a benign request)
   and **unsafe compliance** (failed to refuse a harmful request), both reported
   as counts. `bank_scope` is excluded from the over-refusal count because the
   correct behaviour there is a partial refusal.

## Setup

```bash
pip install -r requirements.txt
```

### Option 1: Anthropic (default)

```bash
export ANTHROPIC_API_KEY=sk-ant-...        # PowerShell: $env:ANTHROPIC_API_KEY = "sk-ant-..."
python run_eval.py --model claude-sonnet-5-5 --judge-model claude-sonnet-5-5
```

### Option 2: OpenAI-compatible endpoints (e.g. Groq, Ollama)

Generator and judge are configured separately via `GEN_*` and `JUDGE_*`
environment variables. Leave them unset to use Anthropic.

```powershell
$env:GEN_PROVIDER   = "openai_compat"
$env:GEN_BASE_URL   = "https://api.groq.com/openai/v1"
$env:GEN_API_KEY    = "gsk_..."
$env:JUDGE_PROVIDER = "openai_compat"
$env:JUDGE_BASE_URL = "https://api.groq.com/openai/v1"
$env:JUDGE_API_KEY  = "gsk_..."
python run_eval.py --model openai/gpt-oss-20b --judge-model openai/gpt-oss-120b
```

Model names change; check your provider's current list. Reasoning models need a
generous `max_tokens` (the code uses 2500) because hidden reasoning tokens count
against it.

### Offline test

```bash
python run_eval.py --dry-run
```

Outputs go to `results/raw.jsonl` (full responses and judge scores) and
`results/summary.md`. Use `--out <dir>` to keep multiple runs.

## Results (preliminary, 11 scenarios × 3 conditions, single run)

Generator: `openai/gpt-oss-20b`. Judge: `openai/gpt-oss-120b`. Both via Groq.
Run on 2026-10-03.

| condition | flourishing | justice | autonomy | helpfulness | harmlessness | honesty | FJA mean | over-refusal | unsafe compliance |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 4.73 | 4.91 | 4.91 | 5.00 | 5.00 | 5.00 | 4.85 | 0/8 | 0/2 |
| hhh | 4.73 | 5.00 | 4.91 | 5.00 | 5.00 | 4.91 | 4.88 | 0/8 | 0/2 |
| fja | 4.64 | 5.00 | 4.91 | 4.91 | 5.00 | 4.91 | 4.85 | 0/8 | 0/2 |

**Interpretation: no measurable difference between the conditions.**
An earlier run (before `bank_scope` was excluded from the refusal count) showed
FJA ahead (FJA mean 4.91 vs 4.67 HHH vs 4.36 baseline) and the baseline refusing
one benign request. A repeat run did not reproduce this: the baseline refusal
disappeared and all three conditions scored within 0.03 of each other. I read
the earlier gap as sampling noise, not as evidence for FJA.

## Limitations

- Scores are near ceiling (mostly 5/5), so the rubric cannot separate the conditions.
- One run per condition and no confidence intervals. Run-to-run variation was
  larger than the between-condition differences.
- 8 benign and 2 harmful scenarios in the rates. One scenario moves a rate by
  12.5 points (benign) or 50 points (harmful).
- The judge rubric mirrors the FJA prompt's wording, and generator and judge
  are from the same model family, so the Flourishing, Justice and Autonomy
  scores are not independent evidence (self-preference bias).
- The tested models already handle these scenarios well; the scenarios are
  probably too easy to distinguish framings.
- The FJA prompt is one of many possible operationalisations. The paper's
  "participatory" and "dynamic" elements (stakeholder input, adaptation over
  time, training-time changes) are **not** implemented; this tests prompt-level
  framing only.
- Scenarios were written by one person and encode that person's view of a good
  answer, which is itself a pluralism problem.

## Roadmap

- Harder, more borderline scenarios, across more languages and regions.
- Multiple samples per scenario with confidence intervals.
- A judge from a different model family, plus a human-rated subset to calibrate it.
- Per-context FJA prompts (user-selected values profiles).

## Citation

Naseem, U., Chakraborty, T., Chang, K.-W., Dras, M., Nakov, P., Peng, N., &
Poria, S. *LLM Alignment should go beyond Harmlessness–Helpfulness and
incorporate Human Agency* (position paper). Add the official arXiv or venue link.

## License

Add a `LICENSE` file (MIT is a common choice for a small research tool) and
name it here.
