# Test 003 Summary: Multi-Model Investigation & Truth-Aware Prompting

## Date: 2026-01-23

## Executive Summary

We tested whether multi-model synthesis improves answer quality and defensibility. The surprising finding: **prompt engineering matters more than model count**. A single model with a "truth-aware" prompt outperforms multi-model synthesis with naive prompting on both style AND adversarial testing.

---

## Key Findings

### 1. The Hedging-Decisiveness Tradeoff is Avoidable

| Approach | Style Score | Adversarial Score | Trade-off? |
|----------|-------------|-------------------|------------|
| Original (bold) | ~28/30 | 40-63% | - |
| Retrofitted (hedged) | ~20/30 | 75-90% | **Yes - lost 8 pts** |
| Truth-Aware (built-in) | **~27/30** | **~90%** | **No trade-off** |

### 2. Prompt Engineering > Multi-Model

| Factor | Style Impact | Adversarial Impact |
|--------|--------------|-------------------|
| Simple → Truth-Aware Prompt | +5 pts | **+20 pts** |
| Solo → Multi-Model | +6 pts | **-7 pts** |

Multi-model with simple prompt scored WORSE adversarially than solo (63% vs 70%) because synthesis amplifies confidence.

### 3. What Survives Adversarial Scrutiny

**Survives:**
- Comparative language ("more likely", "tends to", "harder")
- Multi-causal framings
- Hedged quantitative claims with sources
- Appropriate confidence levels

**Falls:**
- Absolute language ("cannot", "useless", "will not")
- Precise unverified numbers
- Primacy claims ("original sin", "root cause")

### 4. Built-In > Retrofitted Quality

When models are told criteria upfront, they calibrate from the start. When asked to revise after criticism, they over-hedge and lose actionability.

---

## The Winning Prompt Pattern

```
[Your question]

Your claims will be adversarially challenged. For each claim:
- What evidence would falsify this?
- Absolute language is easy to falsify
- Quantitative claims need sources

Be decisive where evidence supports it. Hedge only where genuinely uncertain.
```

---

## Recommendations for Minds CLI

### 1. Default Prompt Should Include Truth-Aware Guidance

Add to synthesis prompts:
```
EPISTEMIC CALIBRATION:
- Avoid absolute language (cannot, will not, always, never)
- For quantitative claims, specify source or acknowledge uncertainty
- Distinguish well-supported claims from plausible-but-uncertain
- Be decisive where evidence supports it; do not over-hedge
```

### 2. Multi-Model Value is Identifying Disagreement

The real value of querying multiple models isn't consensus - it's surfacing where they disagree. Disagreement = genuine uncertainty worth flagging.

Consider adding a "disagreement detection" mode:
```
minds ask --show-disagreements "question"
```

### 3. Consider "Rigor Mode" Flag

```
minds ask --rigor "question"  # Adds truth-aware prompt
minds ask --adversarial "question"  # Runs adversarial challenge after
```

### 4. Synthesis Prompt Should NOT Emphasize Consensus

Current integration prompt works better than consensus prompt because it preserves sharp insights. But even better: include calibration guidance.

Bad: "Find where models agree"
Better: "Integrate the best ideas"
Best: "Integrate the best ideas. For each claim, note confidence level and what would falsify it."

---

## When to Use Multi-Model vs Solo

### Use Solo + Truth-Aware When:
- Cost matters
- Speed matters
- Question has well-established answers
- You want maximum defensibility

### Use Multi-Model When:
- You want to surface genuine uncertainty (disagreement = signal)
- Topic requires diverse framings
- You need comprehensive coverage
- You're exploring rather than concluding

---

## Files

Main results:
- `test003_adversarial.md` - Full experimental results
- `test003_fair_comparison.md` - Initial fair comparison setup
- `test003_truth_aware_prompt.md` - The winning prompt design
- `test003_summary.md` - This summary

Raw outputs:
- `test003_n_truth_aware.txt` - GPT with truth-aware prompt
- `test003_m_truth_aware.txt` - Claude with truth-aware prompt
- `test003_gpt_solo_simple.txt` - GPT solo baseline

---

## Next Steps

1. **Test on verifiable questions** - Use questions with known right answers to validate that adversarial scores correlate with actual accuracy

2. **Implement disagreement detection** - Surface where models disagree as a signal of genuine uncertainty

3. **Design simpler truth-aware prompt** - Current prompt is verbose; find minimal effective version

4. **Integrate into minds CLI** - Add --rigor flag or make truth-aware default

5. **Test across question types** - Verify findings generalize beyond policy analysis questions
