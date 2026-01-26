# GPQA Diamond Full Comparison - FINAL RESULTS

**Completed**: 2026-01-26 17:57 UTC
**Goal**: Run full 198-sample comparison to understand value-add at each step

## Final Results (All 198 samples)

| Rank | Configuration | Accuracy | Passed | Cost | Time | Run ID |
|------|--------------|----------|--------|------|------|--------|
| 1 | **minds_critique** | **88.4%** | 175/198 | $183.94 | 64min | 20260126_142437_gpqa_minds |
| 2 | minds_critique_challenge | 86.9% | 172/198 | $231.55 | 71min | 20260126_153204_gpqa_minds |
| 3 | Gemini 2.5 Pro solo | 86.4% | 171/198 | $3.71 | 24min | 20260126_125213_gpqa_baseline |
| 4 | minds_baseline | 84.3% | 167/198 | $77.37 | 35min | 20260126_130227_gpqa_minds |
| 4 | minds_critique_aggressive | 84.3% | 167/198 | $229.95 | 72min | 20260126_164448_gpqa_minds |
| 5 | Claude Opus 4.5 solo | 82.8% | 164/198 | $11.95 | 5min | - |
| 6 | GPT-5.2 solo | 72.2% | 143/198 | $1.15 | 2min | - |

## Key Findings

### 1. The Critique Workflow is the Key Value-Add (+4.1% over baseline)
- minds_critique (88.4%) beats minds_baseline (84.3%) by 4.1 percentage points
- This is the ONLY multi-model configuration that beats the best solo model
- Cost: $183.94 vs Gemini's $3.71 (50x more expensive for +2% accuracy)

### 2. Devil's Advocate HURTS on Full Dataset
**This contradicts our 50-sample findings!**

| Mode | 50-sample | 198-sample | Change |
|------|-----------|------------|--------|
| critique_challenge | 94% | 86.9% | -7.1% |
| critique (no DA) | ~84%* | 88.4% | +4.4% |

The devil's advocate mechanism:
- **Helps** on the subset of questions where there's genuine ambiguity
- **Hurts** when it challenges correct consensus (introduces noise)
- Net effect on full dataset: **NEGATIVE** (-1.5% vs critique alone)

### 3. Aggressive Challenge is Even Worse
- critique_aggressive (84.3%) = same as baseline
- Running challenge on EVERY question destroys the critique gains
- The challenge mechanism is not calibrated correctly

### 4. Multi-Model Baseline is Worthless
- minds_baseline (84.3%) is WORSE than Gemini solo (86.4%)
- Synthesis without critique averages away the best model's advantage
- Cost: $77.37 for worse results

## Cost-Effectiveness Analysis

| Configuration | $/accuracy point | Notes |
|--------------|------------------|-------|
| GPT-5.2 solo | $0.016 | Cheapest but lowest accuracy |
| Gemini solo | $0.043 | **Best cost/accuracy ratio** |
| Claude solo | $0.144 | Good accuracy, moderate cost |
| minds_baseline | $0.920 | Terrible - pays more for less |
| minds_critique | $2.080 | Highest accuracy, very expensive |
| minds_critique_challenge | $2.665 | Worse than critique, costs more |
| minds_critique_aggressive | $2.725 | Same as baseline, costs 3x more |

## Recommendations

1. **For cost-sensitive use**: Gemini 2.5 Pro solo (86.4%, $3.71)
2. **For maximum accuracy**: minds_critique without devil's advocate (88.4%, $184)
3. **AVOID**: minds_baseline, critique_challenge, critique_aggressive

## What Went Wrong with Devil's Advocate?

The 50-sample run showed 94% accuracy, but full 198 shows only 86.9%. Hypotheses:

1. **Sample bias**: The 50-sample subset may have been enriched for questions where challenge helps
2. **Overchallenging**: The challenge is too aggressive and overturns correct consensus
3. **Noise introduction**: When consensus is correct (which is most of the time), challenge just adds noise

**The challenge is not well-calibrated** - it doesn't distinguish between:
- Consensus that's wrong and should be challenged
- Consensus that's right and should be preserved

## File Locations

- Solver code: `/home/keeva/socrates/eval/solvers/minds.py`
- Episode logs: `eval_logs/runs/<run_id>/episodes/`
- Full critique results: `eval_logs/runs/20260126_142437_gpqa_minds/`
- Full critique_challenge results: `eval_logs/runs/20260126_153204_gpqa_minds/`
- Full critique_aggressive results: `eval_logs/runs/20260126_164448_gpqa_minds/`

## Next Steps for Research

1. **Analyze delta**: Compare critique vs critique_challenge question-by-question to see where challenge helps vs hurts
2. **Calibrate challenge**: Only challenge when confidence is low or models disagree
3. **Selective challenge**: Use challenge only for specific question types where it helps
4. **Confidence thresholds**: Only accept challenge if it has HIGHER confidence than consensus

---

## Related Documentation

- **Full Report**: `experiments/GPQA_EXPERIMENT_REPORT.md` - Comprehensive methodology, results, and analysis
- **Failure Analysis**: `experiments/FAILURE_ANALYSIS.md` - Detailed breakdown of failure patterns
- **Solver Code**: `eval/solvers/minds.py` - Implementation of all multi-model modes
