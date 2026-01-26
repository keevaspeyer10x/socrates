# Test 004 Results: Hard Question Comparison

## Date: 2026-01-23

## CORRECTION: Original Test Didn't Use --rigor Flag Properly

The original "GPT Solo + Rigor" test manually added truth-aware text but didn't use the actual `--rigor` flag. Re-testing with proper `--rigor` shows much better calibration - GPT explicitly acknowledges that percentage decompositions are "estimates, not citations" and includes falsification conditions.

**Key difference with actual --rigor:**
- Explicitly says "No public source cleanly decomposes" the percentages
- Provides confidence levels (Medium-High, Medium, Medium)
- Includes falsification conditions for each attribution
- Notes "These shares are not additive 'truth'"

The original test failure was partly due to not using the full rigor system.

### Corrected Adversarial Scores

| Approach | Survives | Partial | Falls | Score |
|----------|----------|---------|-------|-------|
| GPT (manual prompt, no --rigor) | 0 | 5 | 1 | ~42% |
| **GPT (proper --rigor flag)** | 0 | 4 | **0** | **~50%** |
| Multi-Model + --rigor | 0 | 5 | 1 | ~42% |
| Self-Critique | **4** | 1 | 0 | **~90%** |

**Key insight:** The `--rigor` flag prevents claims from fully FALLING by adding caveats ("not additive truth", "estimates not citations"), but it doesn't prevent fabricated percentage decompositions. Self-critique still wins because the critique phase explicitly removes unsupported precision.

## Question (Designed to be Hard)
```
What is the actual cost per kilometer of recent US subway projects vs European comparables?
- Cite specific projects with costs
- Control for tunneling %, station count, labor costs
- What percentage of the cost difference is attributable to: procurement, labor, regulations, design?
- Provide confidence levels for your attributions
```

This question is hard because:
- Requires specific verifiable numbers
- Causal attribution is genuinely contested
- Easy to be confidently wrong
- Models may have different data

---

## Approaches Tested

| Approach | Description | Cost |
|----------|-------------|------|
| **A: GPT Solo + Rigor** | Single model with truth-aware prompt | 1 call |
| **B: Multi-Model + Rigor** | 5 models → Claude synthesis with --rigor flag | 6 calls |
| **C: Self-Critique** | GPT generates → Claude critiques → GPT revises | 3 calls |

---

## Results Summary

### Style Scores (3-judge panel, /40)

| Approach | Depth | Specificity | Calibration | Action | **Total** |
|----------|-------|-------------|-------------|--------|-----------|
| A: GPT Solo + Rigor | 8-9 | 7-9 | 8-10 | **4-5** | **~30/40** |
| B: Multi-Model + Rigor | 8-9 | 7-10 | 8-10 | 7-9 | **~34/40** |
| C: Self-Critique | 8-10 | 6-9 | **9-10** | **8-10** | **~35/40** |

### Adversarial Scores

| Approach | Survives | Partial | Falls | **Score** |
|----------|----------|---------|-------|-----------|
| A: GPT Solo + Rigor | 0 | 5 | 1 | **~42%** |
| B: Multi-Model + Rigor | 0 | 5 | 1 | **~42%** |
| C: Self-Critique | **4** | 1 | 0 | **~90%** |

---

## Key Finding: Self-Critique Mode Wins

### Why Self-Critique Outperformed

**GPT Solo + Rigor failed because:**
- Presented fabricated percentage decomposition (30% design, 25% procurement, etc.) with "High confidence"
- These percentages appear nowhere in cited sources
- Transit Costs Project doesn't provide this decomposition
- Adversarial challenger correctly identified this as speculation presented as evidence

**Multi-Model + Rigor failed similarly:**
- Synthesis amplified confident claims ("all models agree")
- Still presented crisp numerical claims (1.3-1.5x wage effect) without empirical basis
- Agreement ≠ truth - models agreed on plausible speculation

**Self-Critique succeeded because:**
1. **Critique explicitly removed fabricated percentages** - "I remove the 'Design 30%, Procurement 25%...' split"
2. **Forced acknowledgment of evidence limits** - "Where cost shares matter, I either cite project-specific breakdowns or explicitly say 'not reliably generalizable'"
3. **Maintained actionability** - Still provided clear recommendations with KPIs
4. **Adversarial thinking built in** - The critique phase caught exactly what the external adversarial test would catch

---

## What The Critique Caught

The Claude critique of GPT's original response identified:

1. **Circular sourcing** - Transit Costs Project used as both data and proof of causation
2. **Fabricated decomposition** - 30/25/20/15/10% split appears nowhere in sources
3. **Selection bias** - Used three notoriously expensive US projects
4. **Station density inconsistency** - SF denser than NYC but cheaper, unexplained
5. **Labor analysis contradiction** - Claims 15-25% but describes 2-3x productivity gaps
6. **PPP/exchange rate problem** - Madrid costs from 1995-2003 in unclear dollars
7. **"Soft costs" fuzziness** - Never defined or quantified from actual budgets
8. **Missing question** - Why hasn't any US city achieved European costs if we know the causes?

When GPT revised based on this critique, it:
- Removed false precision
- Added honest uncertainty acknowledgments
- Kept actionable recommendations
- Survived adversarial scrutiny

---

## Implications

### Self-Critique Mode Should Be Implemented

The self-critique approach:
- **Catches fabricated precision** before it reaches the user
- **Forces evidence grounding** through explicit challenge
- **Maintains actionability** with appropriate caveats
- **Costs 3x tokens** but achieves much higher adversarial scores

### Multi-Model Value Proposition Clarified

Multi-model synthesis with --rigor:
- **Improves style scores** (+4 over solo)
- **Does NOT improve adversarial scores** on its own
- **Agreement still ≠ truth** - models agreed on fabricated decomposition
- **Needs self-critique or cross-model critique** to add adversarial value

### Token Budget Should Be Used for Depth

The winning approach used 3 calls (generate + critique + revise) vs 6 calls for multi-model.

**Recommendation:** Instead of breadth (5 models), use tokens for depth:
1. Generate with rigor prompt
2. Critique with harsh fact-checker prompt
3. Revise based on critique

This achieves both high style AND high adversarial scores.

---

## Proposed --deep Mode for Minds

```
minds ask --deep "question"
```

Would run:
1. **Generate** with rigor prompt (truth-aware, thorough)
2. **Critique** with adversarial prompt (find problems, be harsh)
3. **Revise** based on critique (fix issues, maintain action)
4. **Synthesize** (if multi-model) with disagreement-aware prompt

**Expected outcome:** ~35/40 style + ~90% adversarial

---

## Files

- `test004_gpt_rigor.txt` - GPT solo + rigor response
- `test004_multimodel_rigor.txt` - Multi-model synthesis
- `test004_critique.txt` - Claude's critique of GPT
- `test004_selfcritique.txt` - GPT's revised response
- `test004_results.md` - This summary

---

## Next Steps

1. **Implement --deep flag** in minds CLI with generate → critique → revise flow
2. **Test on more questions** to verify self-critique generalizes
3. **Compare cost/quality tradeoffs** between --rigor, --deep, and multi-model
4. **Explore cross-model critique** (Model A generates, Model B critiques)
