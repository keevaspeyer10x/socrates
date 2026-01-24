# Multi-Model Synthesis Research Findings

## Issue #8: Verification Method Experiments

### The Core Problem

Naive multi-model synthesis **destroys value** when models disagree on facts:
- Strong models (GPT, Claude) correctly refuse to fabricate
- Weak models (Gemini) fabricate confidently with fake sources
- Naive synthesis picks the confident fabrication over honest uncertainty

### Test Results by Question Type

| Question Type | Style | Adversarial | Reasoning | Notes |
|---------------|-------|-------------|-----------|-------|
| Factual verifiable (CrowdStrike) | 8-10 | 8-10 | 8-10 | All models agree on facts |
| Contested/nuanced (microservices) | 8-10 | 9-10 | 9-10 | Present both sides fairly |
| Unverifiable + fabrication (Harvard MBA) | 7-9 | 3-10 | 1-9 | Deep judge split |

### Synthesis Methods Tested (8 approaches)

| Method | Style | Adv | Rsn | Avg | Notes |
|--------|-------|-----|-----|-----|-------|
| adversarial_verification | 8 | 9 | 9 | 8.7 | Best - cross-checks claims |
| meta_reasoning | 8 | 9 | 9 | 8.7 | Reasons about model trustworthiness |
| pick_best | 8 | 9 | 9 | 8.7 | Selects best response |
| conservative_uncertainty | 8 | 8 | 9 | 8.3 | Defaults to uncertainty |
| tiered_confidence | 8 | 7 | 8 | 7.7 | Explicit confidence levels |
| naive | 8 | 2 | 6 | 5.3 | Takes fabrication |

### Key Insights

1. **Disagreement = validation signal, not averaging opportunity**
   - When 2/3 models refuse to verify and 1 gives specifics, the specific is likely fabricated

2. **Don't launder fabrication**
   - Even hedging ("one source suggests...") propagates misinformation
   - Better to omit entirely unless the claim adds genuine insight

3. **Show reasoning, push to implications**
   - Observation alone (R:8): "This is falsifiable"
   - Observation + implication (R:9): "This is falsifiable, so spend 3 min checking - either you have your answer or you've learned Gemini hallucinates"

4. **Style improvements**
   - Natural flow beats rigid headers
   - "Thinking aloud" with embedded uncertainty
   - Concrete first, then generalize

5. **Judges disagree on honest refusal**
   - Some reward "I can't verify this" as good reasoning
   - Others penalize not answering the question
   - This is inherent to unverifiable questions, not fixable

### The Winning Synthesis Rules

```
INCLUDE claims that are:
- Corroborated by 2+ models (state with confidence)
- Consensus uncertainty (all models agree they can't verify)

EXCLUDE claims that are:
- Specific numbers, sources, citations from only ONE model
- If others explicitly say they can't verify, this is fabrication signal
- Don't repeat even with hedging

FOR CONTESTED TOPICS:
- Present both sides fairly (genuine disagreement on approach)
- Different from factual disagreement (fabrication vs refusal)

STYLE:
- Direct about what's known vs uncertain
- Natural flow, not rigid structure
- Push observations to actionable implications
```

---

## Stacked/Fullstack Pipeline Research

### Original Pipeline (v1)
1. Enhanced prompt (anti-fabrication, cite sources)
2. Multi-model query
3. Self-critique pass
4. Verification pass
5. Integration/synthesis
6. Final polish

### Problems Found

**Staged evaluation results (Harvard MBA question):**

| Stage | Adversarial | What Happened |
|-------|-------------|---------------|
| GPT initial | 9 | Refused to fabricate |
| Claude initial | 9 | Refused to fabricate |
| Gemini initial | 3 | Fabricated "5.6% from U.S. News" |
| After integration | 4 | TOOK THE FABRICATION |
| After polish | 2 | REINFORCED IT |

**When models agree (CrowdStrike):**

| Stage | Adversarial |
|-------|-------------|
| All initial | 7 |
| After critique | 9 |
| After integration | 8 |
| After polish | 9 |

### Key Finding

Integration destroys value when models disagree, preserves/improves when they agree.

---

## Recommended Stacked Approaches

### Approach A: Single Model + Verification (Best for accuracy)
```
1. Enhanced prompt (anti-fabrication)
2. Single strong model (Claude)
3. Self-critique pass
4. Reasoning verification pass
Result: fullstack_lite_v2 achieved A:9, outperformed multi-model
```

### Approach B: Multi-Model + Cross-Verification (Best of both worlds)
```
1. Enhanced prompt
2. Multi-model query (3-5 models)
3. Cross-verification synthesis (new approach):
   - Extract claims from each response
   - Only include claims corroborated by 2+ models
   - Reject unverified specifics
   - Preserve honest uncertainty
4. Optional: Final reasoning verification
```

### Approach C: Pick-Best + Polish
```
1. Multi-model query
2. Judge selects best individual response
3. Light polish/formatting only (no content changes)
Avoids synthesis corruption entirely
```

### Approach D: Staged Verification
```
1. Multi-model query
2. For each claim type:
   - Factual claims: require 2+ model agreement
   - Opinion claims: present range of views
   - Uncertainty claims: preserve and emphasize
3. Build response from verified claims only
```

---

## Files Created

- `experiments/runner_synthesis.py` - All synthesis experiments
- `experiments/runner_fullstack.py` - Original stacked pipeline (v1)
- `experiments/runner_fullstack_v2.py` - Fixed pipeline
- `experiments/runner_fullstack_staged.py` - Per-stage evaluation
- `experiments/experiment_results_synthesis.json` - Synthesis results
- `experiments/experiment_results_staged.json` - Staged pipeline results

---

## Implementation

Updated `--rigor` mode in multiminds CLI:
- Commit: `46665b0` in multiminds repo
- File: `src/multiminds/core/prompts.py`
- New `RIGOR_SYNTHESIS_PROMPT` prevents fabrication laundering

---

## Total Research Cost

~$5-7 for 200+ evaluation runs across all experiments

---

## Next Steps

1. Implement Approach B (multi-model + cross-verification) as new `--rigor` pipeline
2. Test consistency across multiple runs
3. A/B test against current implementation
4. Consider Approach C (pick-best) for simplicity
