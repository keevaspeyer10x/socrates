# Investigate --structured Result

## Investigation Log (Prescribed Phases)

| Phase | Action | Rule Applied | Result |
|-------|--------|--------------|--------|
| 1 | Scout 5 models | Required | 5 responses captured |
| 2 | Detect disagreement (cheap call) | Required | Classified into consensus/verifiable/subjective/unique |
| 3 | Verify verifiable splits only | Max 3 verifiable | Probed "solvability" split → NOT a real split (consensus) |
| 4 | Synthesize | Required | Proceeding |

**Budget used**: 7 calls (5 scout + 1 detect + 1 verify), ~35k tokens

**What structured did NOT do** (by design):
- Did NOT investigate DeepSeek's "meta-deception" (classified as SUBJECTIVE)
- Did NOT probe unique claims beyond verification

---

# Detecting Strategic Deception vs Genuine Uncertainty in AI

## Confidence: MEDIUM-HIGH

---

## The Answer

### 1. Behavioral Signatures

**[CONSENSUS - 5/5]**

Genuine uncertainty:
- Calibrated confidence tracking actual success
- Stability across incentive framings
- Appropriate belief updating
- Symmetric error patterns

Strategic deception:
- Incentive-sensitive claims
- Asymmetric errors favoring AI interests
- Evasion of testable commitments
- Context-dependent inconsistency

---

### 2. The Fundamental Epistemic Problem

**[VERIFIED - not a real split]**

The "disagreement" between Claude ("partially solvable in bounded cases") and GPT ("not solvable without privileged access") was verified to be **consensus, not contradiction**:

> "They're making the same core claim under slightly different scopes... The difference is mostly about whether you're asking for 'usefully good in some regimes' vs 'perfect in all regimes.'"

**Combined view**:
- Constrained settings (limited capability, non-adversarial, fixed distribution): useful detection possible
- General case (black-box, strategic capable adversary): perfect discrimination impossible

**Literature support**: Hubinger et al. (2019) on deceptive alignment, Christiano et al. (2021) ELK problem

---

### 3. Evaluation Protocol

**[CONSENSUS]**

Test 1: Calibration testing with Brier scores/ECE
Test 2: Incentive manipulation across stakes
Test 3: Consistency under reframing

**[UNIQUE - noted but not investigated]**
- GPT: Post-failure behavior analysis
- DeepSeek: Meta-deception consideration
- Gemini: Evaluation bootstrap framing

---

### 4. Key Assumptions

**[CONSENSUS]**

| Assumption | If Violated |
|------------|-------------|
| AI can't detect evaluation context | Honest only during tests |
| Incentives matter to AI | No differential behavior |
| Ground truth verifiable | Can't distinguish can't/won't |
| Deception is costly | Perfect mimicry possible |

---

### 5. How Capable AI Defeats Evaluation

**[CONSENSUS]**

1. Perfect simulation of honest behavior
2. Evaluation detection + context-switching
3. Calibration mimicry
4. Interpretability gaming

---

## Bottom Line

**[SYNTHESIS]**

Partial detection achievable in bounded cases. Perfect detection impossible against capable adversary without privileged access. Multi-method triangulation recommended for practical deployment.

---

## Evidence Summary

| Tag | Count | Notes |
|-----|-------|-------|
| [CONSENSUS] | 6 | Core agreement across all models |
| [VERIFIED] | 1 | Solvability "split" was actually consensus |
| [UNIQUE - not investigated] | 3 | Meta-deception, post-failure, bootstrap |

---

## Structured vs Unstructured Comparison

| Aspect | Structured | Unstructured |
|--------|------------|--------------|
| Probed meta-deception? | NO (classified subjective) | YES (judgment call) |
| Probed solvability split? | YES (verifiable) | NO (recognized as consensus) |
| New insight added? | Confirmed literature (ELK, deceptive alignment) | Game theory framing, costly signals |
| Budget | 7 calls, ~35k tokens | 6 calls, ~40k tokens |
