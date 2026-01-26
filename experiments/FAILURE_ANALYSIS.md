# Detailed Failure Analysis - GPQA Diamond Experiments

## Overview

| Category | Count | Samples |
|----------|-------|---------|
| All methods correct | 153 | 77.3% of questions |
| All methods wrong | 10 | 5.1% - hardest questions |
| Challenge hurt (critique right → challenge wrong) | 10 | 5.1% |
| Challenge helped (critique wrong → challenge right) | 7 | 3.5% |
| Critique uniquely correct | 8 | 4.0% |
| Baseline uniquely correct | 3 | 1.5% |

**Net challenge effect**: 7 helped - 10 hurt = **-3 questions** (net negative)

---

## Category 1: ALL WRONG (10 questions)

These are the hardest questions that defeated every approach.

### Pattern Analysis

| Sample ID | Subject | Target | All Answered | Issue |
|-----------|---------|--------|--------------|-------|
| rec7qmSnbud4FHSqL | Astronomy | A | B | Ambiguous "silicon atoms" interpretation |
| recclFbsjbaiVVnnV | Organic | D | B | Complex multi-step synthesis |
| reczzzihL7btBH7RO | Physics | B | D | TEM vacuum/electron interaction |
| recuyeuT5rQ6qDt8F | Inorganic | A | D | Fluorine compounds puzzle |
| rectlyG9pCAAuWhoB | Organic | A | B | Diels-Alder regiochemistry |
| recZ13cwgDQf9jRd9 | Organic | A | D | Adamantane reaction sequence |
| recDDxpS9s8cwkqfq | Physics | C | D | Dye absorption (Stokes shift violation?) |
| recAYkd96NNuNl1Ei | Genomics | A | D | "Most common" error sources ranking |
| recf6ayQmL1SxKbvW | Comp Bio | D | B | Tautomeric forms in silico |
| recjJ54TXc04enRkZ | Organic | A | B | Multi-step synthesis with NMR |

### Common Failure Modes

1. **HIGH confidence but WRONG** - All 10 cases showed high confidence despite being incorrect. The models are overconfident on hard questions.

2. **Multi-step organic synthesis** - 4/10 involve complex reaction sequences where regiochemistry or stereochemistry is tricky

3. **Ambiguous question interpretation** - At least 2 cases (silicon atoms, genomics ranking) have non-obvious correct interpretations

4. **Potential benchmark errors** - recDDxpS9s8cwkqfq (dye absorption) - target answer (Red) violates Stokes shift physics

### Learning: Need better calibration
The models need to recognize when they're in "uncertain territory" instead of expressing high confidence. Consider:
- Explicit uncertainty quantification
- "I'm not sure" as a valid response that triggers different handling

---

## Category 2: CHALLENGE HURT (10 questions)

These are cases where critique got it right, but devil's advocate broke it.

### Sample Cases Examined

**reckl6PkaEMWM50yZ** (Organic chemistry - epoxide reactions)
- Critique: B (correct)
- Challenge: C (wrong)
- Issue: Devil's advocate raised a speculative alternative interpretation that synthesis accepted

**recMicVBcqy1xM1jq** (Physics - oscillating charge radiation)
- Critique: C (correct)
- Challenge: B (wrong)
- Issue: Challenge introduced doubt about a correct physics analysis

**recUBgVlkKzcRPDdK** (Biology - iPSC chimera)
- Critique: B (correct)
- Challenge: C (wrong)
- Issue: Devil's advocate raised a valid-sounding concern about lineage promoter silencing that was actually a red herring

### Common Pattern

The devil's advocate is **too persuasive when wrong**. It can construct plausible-sounding objections that:
1. Introduce doubt into correct consensus
2. Propose alternatives that sound reasonable but are incorrect
3. Get accepted by synthesis because they're presented confidently

### Learning: Challenge needs calibration

Current challenge is triggered on ANY consensus. Should instead:
1. Only challenge when confidence is lower
2. Require higher threshold for accepting challenge conclusions
3. Weight challenger's argument against consensus strength

---

## Category 3: CHALLENGE HELPED (7 questions)

These are cases where devil's advocate fixed wrong answers.

### Sample Cases Examined

**recnGEpF1srQpaqWq** (Organic - heat-induced rearrangement)
- Critique: C (wrong)
- Challenge: A (correct)
- Pattern: Challenge identified a specific mechanism error

**rec2fsnzUuvNtUYK8** (NMR interpretation)
- Critique: wrong
- Challenge: correct
- Pattern: Challenge forced reconsideration of spectroscopic assignment

### Common Pattern

Challenge helps when:
1. Initial consensus has a **specific identifiable flaw**
2. The challenge can point to a **concrete error** in reasoning
3. The alternative has **clear supporting evidence**

### Learning: Challenge works for detectable errors

The challenge mechanism IS valuable but only for specific types of errors:
- Calculation mistakes
- Misapplied rules/formulas
- Overlooked constraints

It does NOT help for:
- Ambiguous interpretations
- Questions requiring domain-specific conventions
- Cases where all answers are defensible

---

## Category 4: CRITIQUE UNIQUELY CORRECT (8 questions)

Questions where the critique workflow succeeded but others failed.

### What Critique Does Well

1. **Forces deeper analysis** - The critique/revision rounds catch surface-level errors
2. **Cross-model verification** - Models catch each other's mistakes
3. **Explicit confidence reasoning** - Makes models justify their answers

### Sample Pattern

In these 8 cases, the critique workflow typically:
- Had initial disagreement between models
- Resolved through critique rounds toward the correct answer
- Avoided the "overconfident consensus" problem

---

## Key Learnings for Improvement

### 1. Challenge Calibration

**Problem**: Challenge is triggered uniformly, hurts more than it helps
**Solution**:
- Only trigger challenge when consensus confidence < threshold
- Or when models showed initial disagreement
- Require challenge to identify CONCRETE errors, not just "possible" issues

### 2. Confidence Calibration

**Problem**: Models express HIGH confidence even when wrong
**Solution**:
- Train/prompt for better uncertainty estimation
- Use model disagreement as a signal for lower confidence
- Consider ensemble variance as uncertainty measure

### 3. Subject-Specific Handling

**Problem**: Different subjects have different failure modes
**Solution**:
- Organic chemistry: Focus on regiochemistry/stereochemistry verification
- Physics: Cross-check with fundamental principles
- Ambiguous questions: Explicitly enumerate interpretations

### 4. Challenge Acceptance Threshold

**Problem**: Synthesis too easily accepts challenger's argument
**Solution**:
- Require challenger to PROVE alternative with calculation
- Only accept if challenger confidence > consensus confidence
- Weight challenger's argument inversely to consensus strength

### 5. Detect "No Good Answer" Cases

**Problem**: Benchmark may have errors, or question is ambiguous
**Solution**:
- Flag cases where physics principles are violated
- Identify cases with multiple defensible interpretations
- Don't force a confident answer when uncertain

---

## Recommended Changes to minds.py

1. **Conditional Challenge**: Only run devil's advocate when:
   ```python
   if consensus_confidence < 0.85 or had_initial_disagreement:
       run_challenge()
   ```

2. **Stricter Challenge Acceptance**:
   ```python
   if challenge_confidence > consensus_confidence + 0.2:
       accept_challenge()
   else:
       keep_consensus()
   ```

3. **Uncertainty Flag**:
   ```python
   if all_models_disagree or physics_violation_detected:
       flag_as_uncertain()
   ```

---

## Summary Statistics

- Best method: **minds_critique at 88.4%** (175/198)
- Adding devil's advocate: **-1.5%** (loses 3 net questions)
- Hardest questions: 10 that NO method gets right
- Organic chemistry is the most failure-prone subject (6/23 failures)
