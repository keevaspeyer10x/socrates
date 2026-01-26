# GPQA Diamond Multi-Model Evaluation Report

**Date**: 2026-01-26
**Benchmark**: GPQA Diamond (198 PhD-level science questions)
**Goal**: Understand where multi-model collaboration adds value over single models

---

## Executive Summary

We tested 7 configurations on the full GPQA Diamond benchmark (198 questions):

| Rank | Configuration | Accuracy | Cost | Key Finding |
|------|--------------|----------|------|-------------|
| 1 | minds_critique | **88.4%** | $184 | Best overall - critique workflow adds value |
| 2 | minds_critique_challenge | 86.9% | $232 | Devil's advocate HURTS (-1.5%) |
| 3 | Gemini 2.5 Pro solo | 86.4% | $4 | Best cost/accuracy ratio |
| 4 | minds_baseline | 84.3% | $77 | Multi-model without critique is WORSE than best solo |
| 4 | minds_critique_aggressive | 84.3% | $230 | Always challenging destroys gains |
| 5 | Claude Opus 4.5 solo | 82.8% | $12 | Strong solo performance |
| 6 | GPT-5.2 solo | 72.2% | $1 | Weakest but cheapest |

**Key Insight**: The critique/revision workflow is valuable (+4.1% over baseline), but the devil's advocate mechanism hurts on the full dataset despite showing promise on a 50-sample subset.

---

## Methodology

### Benchmark
- **GPQA Diamond**: 198 PhD-level multiple choice questions
- **Subjects**: Physics, Chemistry, Biology, Astronomy, Computer Science
- **Format**: 4-choice multiple choice (A, B, C, D)
- **Difficulty**: Designed to be challenging even for domain experts

### Configurations Tested

#### Solo Models
1. **Claude Opus 4.5** (`anthropic/claude-opus-4-5-20251101`)
2. **GPT-5.2** (`openai/gpt-5.2`)
3. **Gemini 2.5 Pro** (`google/gemini-2.5-pro`)

#### Multi-Model Configurations
4. **minds_baseline**: 3 models answer independently → synthesis combines
5. **minds_critique**: 3 models answer → cross-critique → revise → synthesis
6. **minds_critique_challenge**: critique + devil's advocate on consensus
7. **minds_critique_aggressive**: critique + always run aggressive challenge

### Prompts Used

All multi-model configurations use a structured prompt requiring:
- Identification of approach/textbook method
- Validity check of assumptions
- Scale/regime analysis
- Steelman of alternative answers
- Explicit confidence level (HIGH/MEDIUM/LOW)

The critique prompt asks models to:
- Check accuracy of calculations
- Verify completeness of analysis
- Validate conclusion follows from reasoning

The devil's advocate prompt challenges consensus by:
- Looking for interpretation errors
- Checking hidden assumptions
- Verifying correct regime/formula usage
- Computing alternative answers when possible

---

## Detailed Results

### Full 198-Sample Results

| Configuration | Passed | Failed | Accuracy | Std Error | Cost | Time |
|--------------|--------|--------|----------|-----------|------|------|
| minds_critique | 175 | 23 | 88.4% | ±2.3% | $183.94 | 64min |
| minds_critique_challenge | 172 | 26 | 86.9% | ±2.4% | $231.55 | 71min |
| Gemini 2.5 Pro | 171 | 27 | 86.4% | ±2.4% | $3.71 | 24min |
| minds_baseline | 167 | 31 | 84.3% | ±2.6% | $77.37 | 35min |
| minds_critique_aggressive | 167 | 31 | 84.3% | ±2.6% | $229.95 | 72min |
| Claude Opus 4.5 | 164 | 34 | 82.8% | ±2.7% | $11.95 | 5min |
| GPT-5.2 | 143 | 55 | 72.2% | ±3.2% | $1.15 | 2min |

### Run IDs for Reproducibility

| Configuration | Run ID |
|--------------|--------|
| minds_critique | 20260126_142437_gpqa_minds |
| minds_critique_challenge | 20260126_153204_gpqa_minds |
| Gemini 2.5 Pro | 20260126_125213_gpqa_baseline |
| minds_baseline | 20260126_130227_gpqa_minds |
| minds_critique_aggressive | 20260126_164448_gpqa_minds |

---

## Analysis

### Value Chain Analysis

```
GPT-5.2 solo:        72.2%  (baseline)
                       ↓ +10.6%
Claude solo:         82.8%  (better model)
                       ↓ +1.5%
minds_baseline:      84.3%  (3 models, no critique) - WORSE than Gemini!
                       ↓ +4.1%
minds_critique:      88.4%  (critique workflow adds value)
                       ↓ -1.5%
minds_critique_challenge: 86.9%  (devil's advocate HURTS)
```

### Where Each Step Adds/Loses Value

| Transition | Delta | Interpretation |
|-----------|-------|----------------|
| GPT → Claude | +10.6% | Better model = better results |
| Claude → Gemini | +3.6% | Gemini is best solo model |
| Gemini → baseline | -2.1% | **Multi-model synthesis LOSES value** |
| baseline → critique | +4.1% | **Critique workflow ADDS value** |
| critique → challenge | -1.5% | **Devil's advocate HURTS** |
| challenge → aggressive | -2.6% | **More challenge = worse results** |

### Cost-Effectiveness

| Configuration | $/accuracy point | Relative to Gemini |
|--------------|------------------|-------------------|
| GPT-5.2 | $0.016 | 0.4x cost, 84% accuracy |
| Gemini 2.5 Pro | $0.043 | **Baseline (best ratio)** |
| Claude Opus | $0.144 | 3.4x cost, 96% accuracy |
| minds_baseline | $0.920 | 21x cost, 98% accuracy |
| minds_critique | $2.080 | 48x cost, 102% accuracy |
| minds_challenge | $2.665 | 62x cost, 101% accuracy |

---

## Failure Analysis

### Distribution of Outcomes

| Category | Count | % | Description |
|----------|-------|---|-------------|
| All correct | 153 | 77.3% | Every method got it right |
| All wrong | 10 | 5.1% | No method succeeded |
| Challenge hurt | 10 | 5.1% | Critique right, challenge wrong |
| Challenge helped | 7 | 3.5% | Critique wrong, challenge right |
| Critique unique | 8 | 4.0% | Only critique got it right |
| Baseline unique | 3 | 1.5% | Only baseline got it right |

### The 10 Hardest Questions (All Methods Failed)

| Sample ID | Subject | Issue |
|-----------|---------|-------|
| rec7qmSnbud4FHSqL | Astronomy | Ambiguous "silicon atoms" interpretation |
| recclFbsjbaiVVnnV | Organic | Complex multi-step synthesis |
| reczzzihL7btBH7RO | Physics | TEM vacuum/electron interaction |
| recuyeuT5rQ6qDt8F | Inorganic | Fluorine compounds puzzle |
| rectlyG9pCAAuWhoB | Organic | Diels-Alder regiochemistry |
| recZ13cwgDQf9jRd9 | Organic | Adamantane reaction sequence |
| recDDxpS9s8cwkqfq | Physics | Dye absorption (possible benchmark error) |
| recAYkd96NNuNl1Ei | Genomics | "Most common" error sources ranking |
| recf6ayQmL1SxKbvW | Comp Bio | Tautomeric forms in silico |
| recjJ54TXc04enRkZ | Organic | Multi-step synthesis with NMR |

**Common pattern**: All showed HIGH confidence despite being wrong.

### Why Devil's Advocate Hurt

The challenge mechanism hurt in 10 cases and helped in only 7, for a net loss of 3 questions.

**When it hurt**:
- Introduced doubt into correct consensus
- Constructed plausible-sounding but wrong objections
- Synthesis accepted challenger's argument too easily

**When it helped**:
- Identified specific, concrete calculation errors
- Pointed to overlooked constraints
- Forced reconsideration with clear evidence

**Root cause**: Challenge is not calibrated - it can't distinguish correct consensus from incorrect consensus.

---

## Recommendations

### For Production Use

1. **Cost-sensitive**: Use Gemini 2.5 Pro solo (86.4%, $4)
2. **Accuracy-focused**: Use minds_critique without devil's advocate (88.4%, $184)
3. **Avoid**: minds_baseline (worse than solo), critique_challenge, critique_aggressive

### For Research/Improvement

1. **Conditional Challenge**: Only trigger when confidence < threshold or initial disagreement exists
2. **Stricter Acceptance**: Require challenger confidence > consensus + margin
3. **Better Calibration**: Train models to recognize uncertainty
4. **Subject-Specific**: Add regiochemistry verification for organic chemistry

### Proposed Code Changes

```python
# In minds.py synthesis

# Only challenge if consensus is weak
if consensus_confidence < 0.85 or had_model_disagreement:
    challenge_result = run_challenge(consensus)

    # Only accept if challenger is MORE confident
    if challenge_confidence > consensus_confidence + 0.15:
        if challenge_has_concrete_proof:
            accept_challenge()
        else:
            keep_consensus()
    else:
        keep_consensus()
else:
    # Strong consensus - don't challenge
    keep_consensus()
```

---

## File Locations

### Code
- Solver implementation: `/home/keeva/socrates/eval/solvers/minds.py`
- CLI: `/home/keeva/socrates/eval/cli.py`

### Results
- Episode logs: `eval_logs/runs/<run_id>/episodes/`
- This report: `experiments/GPQA_EXPERIMENT_REPORT.md`
- Status file: `experiments/EXPERIMENT_STATUS.md`
- Failure analysis: `experiments/FAILURE_ANALYSIS.md`

### Key Run IDs
- Best result (critique): `20260126_142437_gpqa_minds`
- Challenge comparison: `20260126_153204_gpqa_minds`
- Baseline comparison: `20260126_130227_gpqa_minds`

---

## Appendix: Token Usage

### minds_critique (best method)
- Claude Opus: 2,889,187 tokens
- GPT-5.2: 1,677,526 tokens
- Gemini 2.5 Pro: 5,215,306 tokens (includes reasoning tokens)

### minds_critique_challenge
- Claude Opus: 3,194,202 tokens
- GPT-5.2: 2,486,768 tokens
- Gemini 2.5 Pro: 5,242,331 tokens

The challenge mode uses ~15-20% more tokens due to the devil's advocate step.

---

## Conclusion

Multi-model collaboration CAN improve accuracy on PhD-level science questions, but the mechanism matters:

1. **Critique/revision works** (+4.1% over baseline)
2. **Simple synthesis doesn't work** (worse than best solo model)
3. **Devil's advocate hurts on average** (not well-calibrated)

The key insight is that having models critique each other's reasoning catches errors, but having a model try to disprove consensus introduces more noise than signal when the consensus is usually correct.

Future work should focus on **selective challenging** - only questioning answers that show signs of being wrong (low confidence, disagreement, unusual reasoning patterns).
