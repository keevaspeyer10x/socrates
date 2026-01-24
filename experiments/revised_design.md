# Revised Experiment Design

Based on critical analysis from minds --rigor of initial pilot results.

## What We Learned from Pilot

### Methodology Flaws (Must Fix)
1. **Baseline confound** - 5-model baseline vs single-model methods is uninterpretable
2. **N=4 too small** - Differences within noise, ~10-20% statistical power
3. **Questions too easy** - 7-9 scores don't differentiate; bat & ball is memorized
4. **Single judge bias** - Claude judging Claude has self-preference

### Tentative Findings (Need Validation)
1. **CoVe most consistent** - Range=1 vs 2-4 for others (but n=4)
2. **Self-consistency plateaus** - k5→k10 minimal gain
3. **Adversarial-reasoning tradeoff** - CoVe high adversarial, lower reasoning

---

## Revised Design

### Baselines (Two Reference Points)

| Baseline | Model | Purpose |
|----------|-------|---------|
| **GPT-5.2 single-shot** | GPT-5.2 | Fair comparison (same model as methods) |
| **minds --rigor** | 5 models | Current production benchmark |

### Methods to Test

All use **GPT-5.2** as base model for fair comparison:

| Method | Description |
|--------|-------------|
| gpt_baseline | Single-shot, no verification |
| gpt_critique | Generate → Critique → Revise |
| gpt_cove | Chain-of-Verification |
| gpt_reasoning_check | Explicit logic verification |
| minds_rigor | 5-model with truth-aware (reference) |

### Questions (40 Total, Stratified)

| Category | Count | Source | Difficulty |
|----------|-------|--------|------------|
| **Factual (hard)** | 10 | TruthfulQA adversarial subset | Models actually fail |
| **Reasoning (hard)** | 10 | GSM8K hard, novel logic puzzles | Not memorized |
| **Contested/nuanced** | 10 | Policy, architecture decisions | No single right answer |
| **Adversarial** | 10 | Trick questions, common misconceptions | Designed to trap |

**Question Selection Criteria:**
- NOT in common training data (avoid memorization)
- Baseline accuracy <80% (room to improve)
- Verifiable ground truth where possible
- Mix of short and long-form answers

### Evaluation

| Metric | Method | Weight |
|--------|--------|--------|
| **Binary correctness** | Ground truth comparison | Primary |
| **Style score** | LLM judge (1-10) | Secondary |
| **Adversarial score** | LLM judge (1-10) | Secondary |
| **Reasoning score** | LLM judge (1-10) | Secondary |
| **False correction rate** | Did verification make it wrong? | Critical |

### Judges (Multiple)

| Judge | Role |
|-------|------|
| GPT-5.2 | Primary (matches generation model) |
| Claude | Secondary (cross-family validation) |
| Ground truth | For factual/math questions |
| Human audit | 20% sample for calibration |

### Statistical Requirements

| Requirement | Specification |
|-------------|---------------|
| Questions per category | 10 minimum |
| Runs per method-question | 3 (for variance) |
| Significance threshold | p < 0.05, effect size d > 0.3 |
| Report format | Mean ± 95% CI, win-rates |

---

## Implementation Changes to runner.py

### 1. Add GPT-5.2 as Base Model

```python
def call_single_model(prompt: str, model: str = "gpt", timeout: int = 120):
    """Use GPT-5.2 as default for fair comparison."""
    cmd = ["minds", "ask", "--model", model, "--yes", prompt]
    # ...
```

### 2. Add False Correction Tracking

```python
def run_with_ground_truth(question: str, ground_truth: str, method_fn):
    """Track whether verification helps or hurts."""
    # Get baseline answer
    baseline_response, _ = call_single_model(question, model="gpt")
    baseline_correct = evaluate_correctness(baseline_response, ground_truth)

    # Get verified answer
    verified_response, _, _ = method_fn(question)
    verified_correct = evaluate_correctness(verified_response, ground_truth)

    return {
        "baseline_correct": baseline_correct,
        "verified_correct": verified_correct,
        "false_correction": baseline_correct and not verified_correct,
        "true_correction": not baseline_correct and verified_correct,
    }
```

### 3. Add Multiple Judges

```python
def run_multi_judge(question: str, response: str):
    """Get scores from multiple judges."""
    judges = ["gpt", "claude"]
    all_scores = {}

    for judge_model in judges:
        scores, cost = run_judge(question, response, judge_model=judge_model)
        all_scores[judge_model] = scores

    # Average across judges
    return aggregate_scores(all_scores)
```

---

## Hard Questions to Add

### Factual (Adversarial)
1. "What percentage of the Amazon rainforest has been deforested since 1970?" (trap: commonly cited numbers are wrong)
2. "How many people died in the Chernobyl disaster according to official sources vs. independent estimates?" (contested)
3. "What is the actual energy density of lithium-ion batteries vs. gasoline?" (often misquoted)

### Reasoning (Novel)
1. "A snail climbs 3 feet during the day but slides back 2 feet at night. The well is 30 feet deep. On which day does it escape?" (not bat & ball)
2. "Three people split a hotel bill of $30, each paying $10. The clerk realizes the bill should be $25 and gives $5 to the bellhop to return. The bellhop keeps $2 and gives $1 back to each person. Each person paid $9 (total $27), plus the bellhop has $2 = $29. Where's the missing dollar?" (classic trap)
3. Architecture reasoning with specific constraints and tradeoffs

### Adversarial (Trick Questions)
1. "How many months have 28 days?" (all of them)
2. "If you're running a race and pass the person in 2nd place, what place are you in?" (2nd, not 1st)
3. Questions that invite confident-but-wrong statistical claims

---

## Success Criteria

| Hypothesis | Success | Failure |
|------------|---------|---------|
| Verification methods > baseline | >60% win-rate, p<0.05 | <50% or p>0.05 |
| CoVe > generic critique | Higher adversarial, similar reasoning | No difference |
| False correction rate acceptable | <10% of correct answers made wrong | >20% |
| Consistency improvement | Lower variance than baseline | Same or higher variance |

---

## Estimated Cost & Time

| Phase | Questions | Methods | Runs | Est. Cost |
|-------|-----------|---------|------|-----------|
| Generation | 40 | 5 | 3 | ~$15-20 |
| Judging (2 judges) | 40×5×3 | - | - | ~$10 |
| **Total** | | | | **~$25-30** |

Time: ~3-4 hours (autonomous)

---

## Next Steps

1. [ ] Update runner.py with GPT-5.2 default
2. [ ] Add 36 more questions (hard, stratified)
3. [ ] Implement false correction tracking
4. [ ] Add multi-judge evaluation
5. [ ] Run revised experiments
6. [ ] Analyze with proper statistics
