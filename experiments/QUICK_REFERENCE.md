# GPQA Experiment Quick Reference

## TL;DR Results

```
Best accuracy:     minds_critique     88.4%  ($184)
Best value:        Gemini solo        86.4%  ($4)
Avoid:             minds_baseline     84.3%  ($77)  <- worse than solo!
Avoid:             critique_challenge 86.9%  ($232) <- DA hurts
Avoid:             critique_aggressive 84.3% ($230) <- destroys gains
```

## What Works

| ✅ Do This | Why |
|-----------|-----|
| Use critique workflow | +4.1% over baseline |
| Use Gemini for cost-sensitive | Best $/accuracy |
| Cross-model critique | Catches errors |

## What Doesn't Work

| ❌ Don't Do This | Why |
|-----------------|-----|
| Multi-model without critique | Worse than best solo model |
| Devil's advocate on consensus | Hurts more than helps (-1.5%) |
| Always run aggressive challenge | Destroys all critique gains |

## Key Numbers

- **153/198** (77%) - Questions all methods got right
- **10/198** (5%) - Questions NO method got right
- **+4.1%** - Critique improvement over baseline
- **-1.5%** - Devil's advocate penalty
- **50x** - Cost multiplier for critique vs Gemini solo

## Commands

```bash
# Run the best configuration
socrates-eval run gpqa --solver minds --solver-mode critique

# Run cost-effective solo
socrates-eval run gpqa --solver baseline --model google/gemini-2.5-pro

# View results
socrates-eval results <run_id>
```

## Run IDs

| Config | Run ID | Accuracy |
|--------|--------|----------|
| critique (BEST) | 20260126_142437_gpqa_minds | 88.4% |
| challenge | 20260126_153204_gpqa_minds | 86.9% |
| baseline | 20260126_130227_gpqa_minds | 84.3% |
| aggressive | 20260126_164448_gpqa_minds | 84.3% |
| Gemini solo | 20260126_125213_gpqa_baseline | 86.4% |

## File Locations

```
experiments/
├── GPQA_EXPERIMENT_REPORT.md   # Full report
├── EXPERIMENT_STATUS.md        # Summary & status
├── FAILURE_ANALYSIS.md         # Failure patterns
└── QUICK_REFERENCE.md          # This file

eval/solvers/minds.py           # Solver implementation
eval_logs/runs/<run_id>/        # Episode data
```

## Failure Patterns

1. **Organic chemistry** - Most failures (regiochemistry issues)
2. **High confidence wrong** - All hard questions show overconfidence
3. **DA too persuasive** - Breaks correct answers with plausible objections

## Improvement Ideas

1. Only challenge when confidence < 85% or models disagree
2. Require challenger to beat consensus confidence by 15%+
3. Add subject-specific verification (regiochemistry checks)
4. Detect "no good answer" cases (physics violations)
