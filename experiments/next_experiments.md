# Next Experiments: Prioritized Research Agenda

Based on Test 003 and Test 004 findings.

---

## What We Know Works (Evidence-Based)

| Improvement | Evidence | Effect Size |
|-------------|----------|-------------|
| Truth-aware prompting | Test 003 | +20 adversarial points |
| Self-critique (generate→critique→revise) | Test 004 | ~90% vs ~50% adversarial |
| "Do not over-hedge" instruction | Test 003 | Preserves actionability |
| Integration framing ("SUPERIOR, not consensus") | Test 003 | +4 style points |
| Longer/detailed prompts | Test 003/004 | Counteracts lazy responses |

## What Failed

| Approach | Evidence | Why |
|----------|----------|-----|
| Multi-model + simple synthesis | Test 003 | Agreement amplified overconfidence (63% < 70% solo) |
| Retrofitting quality | Test 003 | Lost 8 style points - hedging killed actionability |
| Consensus-seeking synthesis | Test 003 | Averaged down strong positions |

---

## Priority 1: Validate Self-Critique (Highest Confidence)

### Experiment 5A: Self-Critique on Multiple Question Types

**Hypothesis:** Self-critique works across question types, not just quantitative policy questions.

**Test questions:**
1. **Factual/verifiable:** "What were the key technical causes of the 737 MAX crashes?"
2. **Code architecture:** "What's the best way to implement real-time collaboration in a document editor?"
3. **Prediction:** "What will be the dominant AI model architecture in 2028?"
4. **Contested/political:** "What explains the US-China technology decoupling?"

**Protocol:**
- Run each with: (a) --rigor only, (b) self-critique
- Measure: style score, adversarial score
- Success: Self-critique consistently >80% adversarial across types

**Why this first:** Validates generalizability before investing in implementation.

---

### Experiment 5B: Cross-Model vs Self-Critique

**Hypothesis:** Different model doing critique catches different errors than self-critique.

**Test:**
- GPT generates → GPT critiques → GPT revises (self-critique)
- GPT generates → Claude critiques → GPT revises (cross-model)
- GPT generates → Gemini critiques → GPT revises (cross-model)

**Measure:**
- Do cross-model critiques find different issues?
- Does adversarial score improve further?

**Why:** If cross-model adds value, worth the complexity. If not, self-critique is simpler.

---

## Priority 2: Synergy Testing (1+1=3 Hypothesis)

### Experiment 6A: Prompt Engineering Combinations

**Hypothesis:** Multiple prompt improvements stack (compound returns).

**Minimal factor isolation:**

| Version | Prompt Additions |
|---------|-----------------|
| A: Baseline | None |
| B: +Truth-aware | "Claims will be adversarially challenged. Avoid absolutes." |
| C: +Citation | "Cite sources for factual claims where you can." |
| D: +Thoroughness | "Short answers score poorly. Be thorough." |
| E: +Confidence marking | "Mark claims: HIGH/MEDIUM/LOW confidence" |
| F: Combined | B + C + D + E |

**Protocol:**
- Same question for all
- Measure style + adversarial
- Compare F to B alone

**Success:** F > B (combination beats best single factor)

---

### Experiment 6B: Self-Critique + Multi-Model

**Hypothesis:** Multi-model adds value AFTER self-critique by surfacing disagreement.

**Test:**
- Solo + self-critique (baseline from Test 004)
- 3 models + self-critique each → synthesis
- 3 models + self-critique each → disagreement-aware synthesis

**Key question:** Does model disagreement (after self-critique) signal genuine uncertainty that solo can't surface?

---

## Priority 3: Token Budget Exploration

### Experiment 7A: Temperature Diversity

**Hypothesis:** Same model at different temperatures produces useful diversity.

**Test:**
- GPT @ temp 0.0 (deterministic)
- GPT @ temp 0.7 (balanced)
- GPT @ temp 1.0 (creative)
- Synthesize the three

**Measure:**
- Do different temps produce meaningfully different claims?
- Does disagreement between temps predict uncertainty?
- Does synthesis outperform single temp?

**Why:** Cheaper than multi-model if it works.

---

### Experiment 7B: Depth vs Breadth

**Hypothesis:** 3 calls on one model (self-critique) beats 3 different models (no critique).

**Test:**
- 1 model × 3 phases (generate→critique→revise) = 3 calls
- 3 models × 1 phase (standard multi-model) = 3 calls

**Same token budget, different allocation.**

**Measure:** Style + adversarial scores

**Why:** Informs whether --deep should replace default multi-model for some use cases.

---

## Priority 4: Prompt Engineering Deep Dive

### Experiment 8A: Minimal Effective Prompt

**Hypothesis:** Most of truth-aware's benefit comes from 1-2 key phrases.

**Test variants:**
1. Full truth-aware prompt (current)
2. Just "Claims will be adversarially challenged"
3. Just "Avoid absolute language"
4. Just "Cite sources or acknowledge when you can't"
5. Combination of top 2 performers

**Why:** Simpler prompts = faster, cheaper, more robust.

---

### Experiment 8B: Anti-Fabrication Prompt

**Hypothesis:** Explicitly telling models not to make up numbers prevents fabrication better than general truth-aware.

**Test:**
- Standard --rigor
- --rigor + "Do not fabricate statistics. If you don't have a cited source for a number, say 'I don't have a source for a specific figure' rather than inventing one."

**Why:** Test 004 showed --rigor doesn't prevent fabricated percentages. Maybe explicit instruction does.

---

## Priority 5: Production Validation

### Experiment 9: Real-World Question Battery

**Hypothesis:** Lab results generalize to real usage patterns.

**Create 20 diverse questions from actual use cases:**
- 5 code/architecture questions
- 5 research/analysis questions
- 5 factual/verification questions
- 5 strategic/decision questions

**Test each with:**
- Solo + simple
- Solo + --rigor
- Solo + --deep (self-critique)
- Multi-model + --rigor

**Build benchmark for ongoing regression testing.**

---

## Experiment Dependencies

```
5A (validate self-critique)
    ↓
5B (cross-model critique) ──→ Decide if worth implementing
    ↓
6B (self-critique + multi-model)

6A (prompt combinations) ──→ Update prompts.py with winners

7B (depth vs breadth) ──→ Inform default mode selection

8A + 8B (prompt deep dive) ──→ Minimal effective prompts
```

---

---

## Priority 6: Structured Thinking Methods (v3/McKinsey)

### What Worked in Earlier Tests

From Test 003 fair comparison, **v3 Hybrid (28.0) beat basic 5-model synthesis (24.3)** by +3.7 points. Key elements:

| Element | What It Did | Score Impact |
|---------|-------------|--------------|
| **Problem reframing** | "Is this the RIGHT question?" | +Clarity |
| **Disaggregation** | Break complex question into sub-questions | +Depth |
| **Known vs Contested** | Separate confidence levels explicitly | +Honesty |
| **5 Whys** | Trace to root cause | +Depth |
| **80/20 / Crux** | "Land use is the original sin" | +Actionability |
| **Tiered recommendations** | Clear priorities, not flat list | +Actionability |
| **Steelmanning** | Engaged alternatives seriously | +Honesty |

**McKinsey-guided approach** added:
- MECE structure (mutually exclusive, collectively exhaustive)
- Hypothesis-driven with conviction levels (HIGH/MEDIUM/LOW)
- "So what" statements after each finding

**GPT Integration (28.3)** beat v3 Hybrid (28.0) with:
- "NOT consensus" instruction
- "SUPERIOR analysis" framing
- "Be MORE decisive"
- "Preserve strongest steelmanned alternatives"

**Unstructured v2** added two potentially novel elements:
- **"What Won't Work" section** - Explicit negative filtering/red-teaming of interventions
- **Stakeholder tensions mapping** - Table of actors, interests, and blind spots (different from steelmanning)

### Experiment 10A: Structured Thinking + Truth-Aware

**Hypothesis:** Combining structured thinking (v3/McKinsey) with truth-aware calibration achieves higher scores than either alone.

**Test prompts:**

| Version | Elements |
|---------|----------|
| A: Truth-aware only | Current --rigor prompt |
| B: v3 only | Disaggregation, 5 Whys, Known vs Contested, 80/20, Steelman |
| C: McKinsey only | MECE, hypothesis-driven, conviction levels, "so what" |
| D: Truth-aware + v3 | Combine A + B |
| E: Truth-aware + McKinsey | Combine A + C |

**Measure:** Style score + adversarial score

**Why:** v3/McKinsey improved style (+3.7) but we never tested adversarial. Truth-aware improved adversarial (+20) but didn't use structured thinking. Combining could stack benefits.

---

### Experiment 10B: Which Structural Elements Matter Most?

**Hypothesis:** Some structural elements provide most of the value.

**Test each element in isolation:**

*From v3:*
1. Disaggregation only ("First, let me break this question into sub-questions...")
2. 5 Whys only ("Let me trace this to root causes...")
3. Known vs Contested only ("Let me separate what we know from what's uncertain...")
4. 80/20 only ("What's the one thing that matters most here?")
5. Steelmanning only ("Let me present the strongest counterargument...")

*From v2 (potentially novel):*
6. "What Won't Work" only ("Before recommendations, explicitly list approaches that won't work and why...")
7. Stakeholder tensions only ("Map key stakeholders, their interests, and their blind spots in a table...")

**Measure:** Which single element provides most lift?

**Why:** Simpler prompts are more robust. Find the essential elements.

**Note on v2 elements:**
- "What Won't Work" differs from steelmanning: steelmanning engages the *best* counter-argument; "What Won't Work" red-teams *your own* recommendations
- Stakeholder tensions differs from steelmanning: maps multiple actors' positions rather than presenting one strong alternative

---

### Experiment 10C: Self-Critique + Structured Thinking

**Hypothesis:** Self-critique catches different errors than structured thinking methods.

**Test:**
- Generate with v3 structured thinking → Critique → Revise
- Generate with truth-aware → Critique with v3 lens ("Did you disaggregate? Did you identify the crux?")

**Why:** Structured thinking might prevent some errors that self-critique catches, or vice versa.

---

## Priority 7: Meta-Experiment - Prompt Engineering Research

### Experiment 11: Ask Models About Prompt Engineering

**Hypothesis:** SOTA models can synthesize prompt engineering research better than we can manually.

**Question to test:**
```
What are the most effective prompt engineering techniques for getting accurate, well-calibrated responses from LLMs?

Based on research and documented techniques:
1. What techniques have the strongest evidence for improving accuracy?
2. What techniques help with calibration (appropriate confidence)?
3. What techniques reduce hallucination/fabrication?
4. What are common failure modes of prompting, and how to avoid them?

Cite specific research or documented best practices where possible.
```

**Then:** Test the top 3 techniques the models recommend that we haven't tried.

**Why:**
- Models may know about research we haven't found
- We can adversarially test their recommendations
- Meta-learning: the system improves itself

---

### Experiment 11B: Prompt Engineering Literature Review

**Task:** Use minds with --deep to research:
1. Chain-of-thought prompting research
2. Self-consistency / majority voting
3. Constitutional AI / principle-based prompting
4. Reflexion / self-correction research
5. Tree-of-thought / deliberative alignment

**Output:** Ranked list of techniques to test with evidence quality ratings.

---

## Priority 8: Research-Backed Techniques (From Literature Review)

Based on multi-model research synthesis of published work. These techniques have strong empirical evidence but we're not currently using them.

### Critical Warning: Ungrounded Self-Correction May Be Unreliable

**Huang et al. (2023/2024) "Large Language Models Cannot Self-Correct Reasoning Yet"** found that models flip correct answers to incorrect as often as vice versa *without external grounding*.

**Implication for our self-critique:** Our Test 004 success may be because we caught *fabricated facts* (verifiable), not reasoning errors. Self-critique needs grounding (retrieval, code execution, verification) to be reliable.

---

### Experiment 12A: Self-Consistency Sampling

**Hypothesis:** Generating k solutions and majority voting outperforms single-shot, even with good prompting.

**Evidence:** Wei et al. (2022), Wang et al. (2022/2023) - Strongest single technique in the literature. 10-30% gains on reasoning benchmarks with strong replication.

**Test:**
- Single shot with --rigor (baseline)
- k=5 samples, majority vote
- k=10 samples, majority vote
- Compare to multi-model (same token budget)

**Key question:** Does same-model sampling provide different value than multi-model diversity?

**Why we're missing this:** We use multi-model diversity but not same-model sampling. These may catch different types of errors.

---

### Experiment 12B: Chain-of-Verification (CoVe)

**Hypothesis:** Generating specific fact-checking questions outperforms generic "critique this" prompts.

**Evidence:** Dhuliawala et al. (2023) - Breaks confirmation bias by generating independent verification questions before re-evaluating.

**Test:**
- Current self-critique: "Critique this response for accuracy and reasoning"
- CoVe approach: "Generate 5 specific fact-checking questions about claims in this response. Then answer each question independently. Then revise based on findings."
- Falsification-first: "Find the strongest evidence AGAINST the main conclusion"

**Why:** More specific than generic adversarial framing. Forces model to check specific claims rather than vaguely "look for problems."

---

### Experiment 12C: Agreement-as-Calibration

**Hypothesis:** Model disagreement is a better uncertainty signal than asking "how confident are you?"

**Evidence:** Consensus across all models in research synthesis. Verbalized confidence produces overconfidence; consistency correlates with correctness.

**Test:**
- Run same question across 5 models
- Measure agreement level per claim
- Compare: claims with high agreement vs low agreement vs adversarial challenge outcomes
- Test: Does flagging disagreement improve user decision-making?

**Implementation:** Report agreement level in synthesis, not just merged answer. "4/5 models agree on X" vs "Models disagree on Y."

---

### Experiment 12D: Tool-Grounded Verification

**Hypothesis:** Self-critique with retrieval/citation checking outperforms ungrounded self-critique.

**Evidence:** Consensus that tool-grounding transforms self-correction from unreliable to effective.

**Test:**
- Ungrounded self-critique (current)
- Self-critique with "verify each citation exists and says what you claim"
- Self-critique with web search for fact-checking
- Self-critique with code execution (for code questions)

**Why:** This may explain why our self-critique worked on factual questions but might fail on reasoning.

---

### Experiment 12E: Reasoning-Specific Verification

**Hypothesis:** Explicit logic-checking prompts catch reasoning errors that generic critique and factual verification miss.

**Evidence:** Lightman et al. (2023) "Process Reward Models" - checking individual reasoning steps outperforms checking final answers. Generic critique may catch factual errors but miss logical fallacies.

**Test approaches:**

| Variant | Prompt |
|---------|--------|
| **Step-by-step audit** | "For each inference step, identify the premise and check if the conclusion logically follows" |
| **Formalize argument** | "Rewrite this argument as: Premise 1, Premise 2... → Conclusion. Check each logical link." |
| **Logical fallacy check** | "Check for these fallacies: false dichotomy, hasty generalization, circular reasoning, post hoc, straw man, appeal to authority" |
| **Counterfactual test** | "For each key claim: If this premise were false, would the conclusion still hold?" |
| **Dependency mapping** | "Map which conclusions depend on which claims. If claim A were wrong, what else would fall?" |

**Test questions (reasoning-heavy, not fact-heavy):**
1. "Should we implement microservices or keep the monolith?" (architecture reasoning)
2. "What explains the productivity paradox of AI?" (causal reasoning)
3. "Is remote work better for company culture long-term?" (contested reasoning)

**Measure:**
- Compare: generic critique vs CoVe (factual) vs reasoning-specific verification
- Which catches more logical errors?
- Does combining factual + reasoning verification stack?

**Why this matters:** If self-critique only works for factual claims, we need a separate mechanism for reasoning. This tests whether explicit logic-checking fills that gap.

---

## Quick Wins to Run First

1. **Experiment 12A** (self-consistency) - High evidence, we're completely missing it
2. **Experiment 8B** (anti-fabrication prompt) - 30 min, could solve Test 004's main failure
3. **Experiment 5A** (self-critique on different questions) - 1 hour, validates generalizability
4. **Experiment 12B** (CoVe) - Better critique approach than generic
5. **Experiment 6A** (prompt combinations) - 1 hour, tests synergy hypothesis
6. **Experiment 10B** (structural element isolation) - 1 hour, finds essential elements

---

## Success Metrics for the Research Program

| Metric | Current Best | Target |
|--------|--------------|--------|
| Hard question adversarial score | ~90% (self-critique) | Maintain >85% across question types |
| Style score | ~35/40 | Maintain >32/40 |
| Cost efficiency | 3x tokens for self-critique | Find if 2x achieves similar results |
| Generalization | Tested on 2 questions | Validated on 20+ diverse questions |

---

## Notes

- All experiments should use the same hard question from Test 004 as baseline for comparability
- New question types should be pre-registered before testing to avoid cherry-picking
- Document negative results - knowing what doesn't work is valuable

---

## Phase 2C Results (2026-01-24) - Integrated Findings

### Experiments Completed

| Experiment | Status | Key Finding |
|------------|--------|-------------|
| 12A: Self-Consistency (k=5) | ✅ Complete | Did NOT outperform baseline (8.3 vs 9.0 adversarial) |
| 8B: Anti-Fabrication Prompt | ✅ Complete | **+6 adversarial points** on hallucination question |
| 5A: Self-Critique Across Types | ✅ Complete | Generalizes: consistent 8/10 across factual, reasoning, prediction, contested |
| 12B: CoVe | ✅ Complete | Tied with self-critique (both 9.0 adversarial) |
| 6A: Prompt Combinations | ✅ Complete | No differentiation - questions may be too easy |
| 10B: Structural Elements | ✅ Complete | No differentiation - all elements ≈ baseline |
| Additive Verification | ✅ Complete | No improvement over self-critique alone |

### Overall Method Rankings (71 runs, $0.38)

| Method | Style | Adv | Reasoning | Avg | N |
|--------|-------|-----|-----------|-----|---|
| additive_verification | 9.3 | 9.0 | 9.3 | **9.2** | 3 |
| self_critique | 8.9 | 8.6 | 9.1 | **8.9** | 10 |
| cove_structured | 8.0 | 9.0 | 8.7 | 8.6 | 3 |
| baseline | 8.6 | 8.1 | 8.9 | 8.5 | 17 |
| **rigor** | 8.1 | **5.9** | 8.0 | **7.3** | 9 |

### Critical Finding: rigor Underperforms

`minds --rigor` (5-model synthesis) consistently scores **lowest on adversarial (5.9)** - well below single-model baseline (8.1).

**However:** This is likely an **execution problem, not a concept problem**:
- Ensemble methods work in ML generally
- OpenAI/Anthropic spend billions on reasoning improvements
- Those improvements are NOT multi-model - they're single-model reasoning (CoT, process reward models, extended thinking)

**Hypothesis:** Our synthesis method is flawed, not multi-model itself.

---

## Priority 2.5: Fix rigor (NEW - Insert Before Priority 3)

Based on Phase 2C findings, we need to test whether rigor can be fixed before abandoning it.

### Experiment 13A: Disagreement Surfacing

**Hypothesis:** Showing raw disagreement helps users more than synthesis.

**Method:** Instead of synthesizing, output:
- "3/5 models said X"
- "2/5 models said Y"
- "Key disagreement: [specific point]"

**Success:** Users find disagreement info more useful than blended answer.

---

### Experiment 13B: Majority Voting vs Synthesis

**Hypothesis:** Simple voting beats prose synthesis.

**Method:**
- Get 5 model responses
- Extract key claims from each
- Report majority position per claim
- Compare to current synthesis

**Success:** Majority voting outperforms current synthesis on adversarial score.

---

### Experiment 13C: Critique-Then-Synthesize

**Hypothesis:** Having models critique each other before synthesis improves output.

**Method:**
1. Get 5 initial responses
2. Have each model critique the others' responses
3. Then synthesize with critiques visible

**Success:** Critique-then-synthesize beats direct synthesis.

---

### Experiment 13D: Selective Synthesis

**Hypothesis:** Should only synthesize when models agree.

**Method:**
- Measure agreement level (cosine similarity of responses)
- If high agreement: synthesize normally
- If low agreement: flag uncertainty, show divergent views

**Success:** Selective approach beats always-synthesize.

---

### Experiment 13E: Confidence-Weighted Aggregation

**Hypothesis:** Weighting by model confidence helps.

**Method:**
- Ask each model to rate confidence (1-10) on each claim
- Weight claims by confidence in final output
- Compare to equal-weight synthesis

**Success:** Confidence-weighted beats equal-weight.

---

### Experiment 13F: Anti-Fabrication + rigor ⭐ DO THIS FIRST

**Hypothesis:** The anti-fabrication prompt fixes rigor's fabrication problem.

**Method:**
- Run rigor with anti-fabrication instruction in synthesis prompt
- Compare to baseline rigor

**Why first:** Quick test (~30 min), may fix rigor cheaply. Anti-fabrication showed +6 adversarial in Phase 2C.

**Success:** rigor + anti-fabrication matches or beats baseline adversarial score.

---

## Updated Quick Wins (Post-Phase 2C)

| Priority | Experiment | Rationale | Status |
|----------|------------|-----------|--------|
| 1 | **13F: Anti-fabrication + rigor** | May fix rigor cheaply | NEW |
| 2 | 13C: Critique-then-synthesize | Tests adversarial multi-model | NEW |
| 3 | 5B: Cross-model critique | Does different critiquer help? | Pending |
| 4 | 13B: Majority voting | Tests structured aggregation | NEW |
| ~~5~~ | ~~12A: Self-consistency~~ | ~~Did not outperform~~ | ✅ Complete |
| ~~6~~ | ~~8B: Anti-fabrication~~ | ~~+6 adversarial points~~ | ✅ Complete |
| ~~7~~ | ~~5A: Self-critique types~~ | ~~Generalizes well~~ | ✅ Complete |

---

## Key Insights for Implementation

### What To Ship Now

1. **Anti-fabrication prompt** - Add to all prompts:
   ```
   IMPORTANT: Do not fabricate statistics. If you don't have a verified source
   for a specific figure, say "I don't have a verified source" rather than
   inventing one.
   ```

2. **Self-critique as default** - Consistent 8.6+ adversarial across all question types

### What To Fix

1. **rigor synthesis** - Test experiments 13A-13F before removing

### What Doesn't Matter (Yet)

1. **Prompt engineering variants** - No differentiation on current questions (need harder questions)
2. **Structural elements** - No differentiation (need harder questions)
3. **Stacking methods** - Additive ≈ single method (do one thing well)

---

## CRITICAL FINDING: Integration Destroys Value (2026-01-24)

### Staged Evaluation Results

On the Harvard CEO question:
- GPT alone: A:9 (correctly refused to fabricate)
- Claude alone: A:9 (correctly refused to fabricate)  
- Gemini alone: A:3 (fabricated statistics)
- **After multi-model integration: A:4** ← Averaging good with bad = bad
- **After polish: A:2** ← Made it even worse

### Root Cause
When you synthesize:
- 2 responses that say "I don't know the exact figure"
- 1 response that fabricates "approximately 5-6%"

The synthesis says something like "estimates suggest 5-6%" - turning honest uncertainty into confident fabrication.

### Implication for rigor
This explains why `--rigor` (5-model synthesis) underperforms baseline. More perspectives aren't better if synthesis corrupts the best ones.

### Solution Approaches
1. **Don't synthesize** - pick best response (requires judge)
2. **Weighted synthesis** - weight by confidence/quality
3. **Conservative synthesis** - preserve maximum uncertainty
4. **Pre-filter** - only integrate responses that pass quality threshold

### What Works
From v2 experiment:
- fullstack_lite_v2 (Claude + critique + verification): A:9
- enhanced_single (Claude with good prompt): A:8
- baseline: A:7

Single strong model with verification >> Multi-model synthesis
