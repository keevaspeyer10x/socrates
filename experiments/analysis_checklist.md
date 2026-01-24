# Experiment Analysis Checklist

Use this checklist BEFORE presenting results to ensure rigorous analysis.

## 1. Methodology Audit (Do First)

### Comparisons
- [ ] Are all methods using the same base model? If not, **FLAG AS CONFOUND**
- [ ] Are all methods using the same questions? (paired design)
- [ ] Are conditions identical except the variable being tested?
- [ ] What is the baseline? Document it explicitly.

### Sample Size
- [ ] Is N sufficient? (N<10 = pilot only, N<30 = exploratory, N>50 = confirmatory)
- [ ] Calculate statistical power - can we detect meaningful effects?
- [ ] Report confidence intervals, not just point estimates

### Question Quality
- [ ] What's the baseline accuracy? (If >85%, questions too easy)
- [ ] Is there ceiling/floor compression? (All scores 7-9 = no differentiation)
- [ ] Are questions contaminated? (In training data, memorized)
- [ ] Is there stratification by type? (factual, reasoning, adversarial)

### Judge Quality
- [ ] Is there self-preference bias? (Same model judging its own output)
- [ ] Are multiple judges used?
- [ ] Is there ground truth validation where possible?

## 2. Results Analysis

### Central Tendency
- [ ] Report mean ± CI, not just mean
- [ ] Report effect sizes (Cohen's d), not just differences
- [ ] Calculate win rates (% of questions where method A > method B)

### Variance & Consistency
- [ ] Report range/variance per method across questions
- [ ] Identify high-variance methods (unreliable)
- [ ] Check for question-type interactions (works on reasoning but not factual?)

### All Metrics
- [ ] Analyze ALL metrics (style, adversarial, reasoning), not just one
- [ ] Discuss which metric matters most for the use case
- [ ] Check for tradeoffs (high adversarial but low style?)

## 3. Interpretation Checks

### Conclusions
- [ ] What conclusions ARE supported by this data?
- [ ] What conclusions are NOT supported? (Be explicit)
- [ ] What's the confidence level? (Strong/Moderate/Weak/Not supported)

### Alternative Explanations
- [ ] What confounds could explain the results?
- [ ] What would falsify these findings?
- [ ] Are there obvious issues a reviewer would catch?

### Limitations
- [ ] List all methodology limitations explicitly
- [ ] Quantify uncertainty where possible
- [ ] What follow-up is needed to confirm findings?

## 4. Presentation Format

### Always Include
```
## Methodology
- Baseline: [what it was]
- Methods compared: [list with key differences]
- N: [number] questions, [stratification]
- Model: [which model(s) used]
- Judge: [which judge(s), any bias concerns]

## Results Summary
[Table with mean ± CI for each metric]

## Consistency Analysis
[Variance/range per method, question-type breakdown]

## Methodology Limitations
[Explicit list of confounds, sample size issues, etc.]

## Conclusions by Confidence
- Strong: [only if N>30, no confounds, large effect]
- Moderate: [if N>10, effects consistent across strata]
- Weak/Exploratory: [if N<10 or confounds present]
- Not Supported: [what we cannot conclude]
```

## 5. Before Presenting: Final Checks

- [ ] Did I use minds --rigor for deeper analysis?
- [ ] Would a skeptical reviewer find obvious flaws?
- [ ] Am I presenting limitations upfront, not buried?
- [ ] Have I distinguished pilot/exploratory from confirmatory findings?
- [ ] Did I address: What should we optimize for? What's the baseline? Is this a fair comparison?

## Common Failure Modes (From This Experiment)

1. **Presented averages without checking for confounds** - Missed that baseline used different model count
2. **Didn't question high scores** - 7-9 range suggests ceiling effects
3. **Focused on one metric** - Initially emphasized adversarial, missed reasoning/style
4. **Didn't show consistency** - Variance analysis was an afterthought
5. **Superficial interpretation** - Required follow-up questions to surface real issues
6. **Didn't use minds for analysis** - Only used when prompted

## Standard Analysis Process

```
1. Run methodology audit checklist
2. Generate results with full metrics
3. Run consistency/variance analysis
4. Identify limitations explicitly
5. Put to minds --rigor for critical review
6. Revise based on minds feedback
7. Present with confidence levels and limitations upfront
```
