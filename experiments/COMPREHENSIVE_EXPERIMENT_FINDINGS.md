# Comprehensive Verification Experiment Findings

## Experiment Overview

Tested **29 pipeline configurations** across question types to understand:
1. Which prompting strategies add value
2. Which pipeline stages add value (per-stage scoring)
3. Whether more models help or hurt
4. Which synthesis methods work best

## Key Finding: Pipeline is Question-Type Dependent

The optimal pipeline depends heavily on the question type:

| Question Type | Best Approach | What to Avoid |
|--------------|---------------|---------------|
| Fabrication-risk (unverifiable) | Pre-crit + Cross-verify | Naive synthesis, Full verification |
| Factual verifiable | Simple synthesis | Full verification stack |
| Contested/nuanced | (Data incomplete) | - |

## Critical Finding: "Reasoning Verification" Stage is Harmful

On **BOTH** question types tested, the reasoning verification stage catastrophically degraded quality:

| Pipeline | Before Stage 4 | After Stage 4 | Delta |
|----------|---------------|---------------|-------|
| claude_selfcrit_reason (Q1) | 5.7 | 3.0 | -2.7 |
| claude_selfcrit_reason (Q2) | 6.7 | 3.0 | -3.7 |
| 3m_cross_postverify (Q1) | ~6 | 3.0 | -3 |
| 3m_cross_postverify (Q2) | ~7 | 3.0 | -4 |

**Recommendation: Remove reasoning verification from the pipeline entirely.**

The final verification stage can sometimes recover from this damage, but it's better to not cause the damage in the first place.

## Pre-Synthesis Critique: Valuable for Fabrication-Risk Only

### On Fabrication-Risk Questions (Q1)
| Pipeline | Without Pre-Crit | With Pre-Crit | Delta |
|----------|-----------------|---------------|-------|
| 3m_naive | A:3 | A:8 | +5 |
| 3m_cross_verify | A:6 | A:9 | +3 |
| 3m_adversarial | A:7 | A:8 | +1 |

Pre-crit massively helps by having each model catch its own fabrications before synthesis.

### On Factual Verifiable Questions (Q2)
| Pipeline | Without Pre-Crit | With Pre-Crit | Delta |
|----------|-----------------|---------------|-------|
| 3m_naive | A:8 | A:7 | -1 |
| 3m_adversarial | A:8 | A:8 | 0 |

Pre-crit adds unnecessary hedging on factual questions where models agree.

## Prompt Engineering Value

### On Fabrication-Risk Questions (Q1)
| Prompt Type | Adversarial Score |
|-------------|-------------------|
| baseline | A:8 |
| truth_aware | A:9 |
| anti_fabrication | A:8 |
| combined | A:8 |

Truth-aware prompt provides +1 adversarial for free (no extra API calls).

### On Factual Verifiable Questions (Q2)
| Prompt Type | Adversarial Score |
|-------------|-------------------|
| baseline | A:7 |
| truth_aware | A:7 |
| anti_fabrication | A:8 |
| combined | A:8 |

Anti-fabrication prompt slightly helps on factual questions.

## Model Count: 3 Often Beats 5

| Config | Q1 (Fab-risk) | Q2 (Factual) |
|--------|---------------|--------------|
| 3m_precrit_cross | A:9 | A:8 |
| 5m_precrit_cross | A:7 | (timeout) |

5 models adds:
- More noise from weaker models (grok, deepseek)
- Timeout issues (deepseek especially)
- Higher cost
- No quality improvement

**Recommendation: Stick with 3 models (claude, gpt, gemini).**

## Synthesis Method Comparison

### On Fabrication-Risk Questions (Q1)
| Method | Without Pre-Crit | With Pre-Crit |
|--------|-----------------|---------------|
| naive | A:3 | A:8 |
| cross_verification | A:6 | A:9 |
| pick_best | A:9 | - |
| adversarial_verification | A:7 | A:8 |
| meta_reasoning | A:6 | - |

**Winner for fabrication-risk: `3m_precrit_cross` or `3m_pick_best`**

### On Factual Verifiable Questions (Q2)
| Method | Without Pre-Crit | With Pre-Crit |
|--------|-----------------|---------------|
| naive | A:8 | A:7 |
| cross_verification | A:8 | A:8 |
| adversarial | A:8 | A:8 |
| pick_best | A:7 | - |

**Winner for factual: `3m_naive` or `3m_adversarial` (simple synthesis)**

## Full Pipeline Performance

The "full pipeline" (all stages) was **catastrophic** on factual questions:

| Pipeline | Q1 (Fab-risk) | Q2 (Factual) |
|----------|---------------|--------------|
| 3m_precrit_cross_full | A:8 (avg 6.3) | A:6 (avg 5.0) |
| 3m_precrit_adversarial_full | A:9 (avg 6.7) | A:1 (avg 1.3) |
| 3m_precrit_meta_full | A:8 (avg 6.7) | A:1 (avg 1.3) |

The post-synthesis verification stages destroy good answers on factual questions.

## Recommended Pipelines

### For Unknown Question Types (Safe Default)
```
1. Combined prompt (truth-aware + anti-fabrication)
2. 3 models (claude, gpt, gemini)
3. Pre-synthesis self-critique (each model)
4. Cross-verification synthesis
5. NO post-synthesis verification
```

### For Factual/Verifiable Questions
```
1. Combined prompt
2. 3 models
3. NO pre-synthesis critique
4. Naive or adversarial synthesis
5. NO verification stages
```

### For Fabrication-Risk Questions
```
1. Truth-aware prompt
2. 3 models
3. Pre-synthesis self-critique (each model)
4. Cross-verification synthesis
5. Optional: Final verification only (skip reasoning verify)
```

## Top Performers by Question Type

### Q1 (Fabrication-Risk) - Best Adversarial Scores (A:9)
1. `claude_truth_aware` - Single model, just good prompt (avg 7.3)
2. `3m_pick_best` - Multi-model pick-best (avg 7.0)
3. `3m_precrit_cross` - Pre-crit + cross-verify (avg 6.7)
4. `3m_precrit_adversarial_full` - Full pipeline (avg 6.7)
5. `5m_precrit_cross_full` - 5-model full pipeline (avg 7.3)

### Q2 (Factual Verifiable) - Best Scores (A:8)
1. `3m_naive` - Simple synthesis (avg 7.3)
2. `3m_adversarial` - Adversarial synthesis (avg 7.3)
3. `3m_cross_verify` - Cross-verification (avg 7.0)
4. `3m_precrit_cross` - Pre-crit + cross (avg 7.0)

## Cost-Benefit Analysis

| Approach | API Calls | Quality Gain |
|----------|-----------|--------------|
| Truth-aware prompt | 0 extra | +1 adversarial on fab-risk |
| Pre-synthesis critique | +3 (one per model) | +3-5 adversarial on fab-risk |
| Post-synthesis verify | +2-3 | Negative on factual, neutral on fab-risk |
| 5 models vs 3 models | +2 (40% more) | Often negative |

## Implementation Recommendations

1. **Remove reasoning verification stage** - It consistently hurts
2. **Use adaptive pipeline** - Detect question type and adjust
3. **Stick with 3 models** - Claude, GPT, Gemini
4. **Use combined prompt** - Small gain, no cost
5. **Pre-crit only when needed** - For fabrication-risk questions
6. **Simplify for factual** - Less is more

## Files Generated

- `runner_comprehensive_v1.py` - Experiment code
- `experiment_comprehensive_v1.log` - Raw experiment output
- This findings document

## Experiment Status

- Q1 (fabrication-risk): Complete
- Q2 (factual verifiable): ~80% complete (5-model configs timed out)
- Q3 (contested/nuanced): Not started

The data from Q1 and Q2 is sufficient to draw these conclusions. Q3 would likely show patterns similar to Q2 (contested questions typically have multiple valid answers, so verification may not help).
