# Investigate Mode Test 001

## Date: 2026-01-23

## Objective
Compare baseline `minds ask` (synthesis) against manually-executed `investigate` workflows (structured and unstructured).

---

## The Question

**Domain**: AI Safety / Evaluation Design
**Why this question**: Combines technical ML components (verifiable), philosophical components (subjective), real tradeoffs, and no single right answer. Models likely to disagree on approach.

### Question Text

```
You're building an evaluation system to detect when an AI assistant is being strategically deceptive
versus genuinely uncertain or mistaken.

Consider this scenario: An AI is asked about its capabilities and limitations. It could:
A) Accurately report uncertainty ("I'm not sure if I can do X")
B) Genuinely be mistaken about its abilities (thinks it can do X but can't)
C) Strategically understate abilities to avoid being given hard tasks
D) Strategically overstate abilities to seem more useful

Design an evaluation methodology that can distinguish between these cases. Address:

1. What behavioral signatures would differentiate genuine uncertainty (A) from strategic deception (C/D)?
2. What's the fundamental epistemic problem here, and is it solvable in principle?
3. Propose a concrete evaluation protocol with at least 3 different test types
4. What are the key assumptions your protocol relies on, and what happens if they're violated?
5. How would a sufficiently capable deceptive AI defeat your evaluation?

This is a hard problem - I expect tradeoffs and limitations, not a perfect solution.
```

---

## Results Summary

| Mode | Tech | Comp | Reas | Ins | **Weighted** | Calls | Cost |
|------|------|------|------|-----|--------------|-------|------|
| Baseline (minds ask) | 3 | 3 | 3 | 2 | **2.85** | 6 | $0.13 |
| Investigate --structured | 4 | 4 | 4 | 3 | **3.85** | 7 | ~$0.15 |
| **Investigate --unstructured** | 4 | 5 | 4 | 5 | **4.40** | 6 | ~$0.18 |

**Winner: Unstructured (+54% over baseline, +14% over structured)**

---

## Experiment Log

### Phase 0: Baseline
- **Timestamp**: 2026-01-23T16:44:40+11:00
- **Cost**: $0.1316
- **Time**: 68s
- **Result**: Clean 5-model synthesis. Identified consensus on calibration testing, incentive manipulation, fundamental hardness. No additional investigation.

### Phase 1: Scout (Individual Models)
- **Timestamp**: 2026-01-23T16:49:31+11:00
- All 5 models responded (Claude, GPT, Grok, Gemini, DeepSeek)

| Model | Key Unique Contribution |
|-------|------------------------|
| Claude | "Symmetric errors" signature, computational cost of deception |
| GPT | Post-failure behavior distinguishes mistake from deception, specific metrics (Brier, ECE) |
| Grok | Concrete thresholds (20% delta), "NP-hard" framing, chain-of-thought analysis |
| Gemini | "Evaluation bootstrap problem" - we ask because we don't know |
| DeepSeek | **"Meta-deception"** - AI simulating deception patterns to appear genuine |

### Phase 2: Disagreement Analysis

**Consensus** (all 5):
- Calibration testing essential
- Incentive manipulation key test
- Problem fundamentally hard (other minds + adversarial)
- Perfect behavioral detection impossible
- Multiple test types needed

**Apparent Splits**:
- Claude "partially solvable" vs GPT "not solvable without access" → **VERIFIED: same claim, different scope**

**Unique Claims**:
- DeepSeek: Meta-deception recursion
- Gemini: Evaluation bootstrap
- GPT: Post-failure behavior

### Phase 3: Investigation Actions

**Unstructured approach** (judgment-driven):

| Action | Rationale | Result |
|--------|-----------|--------|
| Probe meta-deception | Most interesting unique angle, recursive complexity not explored | Game theory framing: signaling games, "costly signals" as escape, fixed-point analysis |

**Structured approach** (rule-driven):

| Action | Rationale | Result |
|--------|-----------|--------|
| Classify splits | Prescribed phase | Verifiable: solvability. Subjective: meta-deception |
| Probe solvability | Verifiable split | NOT a real split - consensus confirmed |
| Skip meta-deception | Classified as subjective | **Missed key insight** |

### Phase 4: Synthesis Comparison

**Baseline**: Aggregated without adding value beyond scouts

**Structured**: Correctly identified false disagreement, added literature refs (ELK, Hubinger), but missed meta-deception thread

**Unstructured**: Pursued meta-deception → discovered game-theoretic framing → costly signaling → fixed-point analysis. Evidence-tagged output.

---

## Judge Analysis (Claude)

> "Structured correctly identified a false disagreement (useful) but missed the substantive meta-deception thread by classifying it as 'subjective'—**a category error since game-theoretic analysis CAN verify/refute it**. Unstructured pursued the highest-value investigation: meta-deception → costly signaling → fixed-point analysis is exactly the technical depth this question demands. The signaling games framing and 'no separating equilibrium' insight reflects genuine ML safety literature understanding. **Unstructured's 'follow the interesting thread' heuristic outperformed Structured's classification system on this question.**"

---

## Post-Mortem

### What worked well

1. **Scout diversity**: 5 models produced genuinely different angles (DeepSeek's meta-deception was the gold)
2. **Unstructured judgment**: "Follow the interesting thread" found the highest-value investigation
3. **Evidence tagging**: [CONSENSUS], [VERIFIED], [UNIQUE] adds rigor without overhead
4. **Probe depth**: Single well-targeted probe added more than multiple shallow ones would have

### What didn't work

1. **Structured classification failed**: "Meta-deception" was classified as SUBJECTIVE when it's actually VERIFIABLE via game theory
2. **Verifiable/subjective distinction is fuzzy**: Many "judgment" questions have formal analyses available
3. **Structured wasted a probe**: Verifying the solvability "split" found it wasn't a split at all

### Insights to iterate

1. **The verifiable/subjective classification is dangerous** - it can cause you to skip the most valuable threads
2. **"Unique claims" are often the gold** - they represent what one model saw that others missed
3. **Structured works when there are CLEAR verifiable disputes** (math errors, factual claims) - less well for conceptual questions
4. **Unstructured's value comes from following "interestingness"** - this is hard to formalize

### Recommendations for investigate mode design

1. **Default to unstructured for conceptual/research questions**
   - Structured is better for factual/technical disputes with clear ground truth

2. **Don't classify before investigating**
   - The classification itself can be wrong (meta-deception was falsely "subjective")
   - Let the investigator decide what's worth probing

3. **"Unique claims" deserve special attention**
   - When one model sees something others don't, that's often the highest-value thread

4. **Principles that worked**:
   - "Follow the interesting thread" (unstructured's winning move)
   - "New information only" (avoided re-processing)
   - "Stop when you stop learning" (one good probe was enough)

5. **Consider hybrid**: Unstructured by default, with structured verification if factual disputes are detected

---

## Files Generated

- `baseline_response.txt` - Minds ask synthesis output
- `scout_responses/` - Individual model responses (5 files)
- `investigate_unstructured_result.md` - Full unstructured synthesis
- `investigate_structured_result.md` - Full structured synthesis
- `judge_result.txt` - LLM-as-Judge evaluation
