# Test 004: Beating Solo + Rigor

## What We Actually Learned (not what I assumed)

### The Core Problem
Multi-model + simple synthesis scored WORSE than solo (63% vs 70% adversarial). Why?

**Synthesis amplified false confidence:**
- When GPT says "land use is the original sin" and Claude agrees → synthesis states it MORE absolutely
- Agreement ≠ Truth. Agreement just means models have similar training data/biases.
- The Integration prompt ("be decisive, take a position") made this worse

### What Solo + Rigor Gets Right
- Self-calibration from the start
- Falsification thinking improves precision
- "Do not over-hedge" preserves action
- Citations added naturally when warned

### What Solo + Rigor CANNOT Do
1. **Know what it doesn't know** - No external check
2. **Surface genuine disagreement** - You can't disagree with yourself
3. **Cross-check blind spots** - Same model, same biases
4. **Pool different knowledge** - GPT knows X, Claude knows Y

---

## The Synthesis Problem

Current synthesis failures:
1. **Consensus-seeking** → Averages down strong positions
2. **Integration** → Amplifies confidence from agreement
3. **Genre shift** → Describes what models said instead of answering

What synthesis SHOULD do:
1. **Agreement + Evidence** → State confidently (earned confidence)
2. **Agreement - Evidence** → Flag as "models agree but no one cites proof"
3. **Disagreement** → Flag as uncertain, DON'T smooth over
4. **Unique insight** → Preserve (don't average away just because only one model said it)
5. **Maintain decisiveness** → Still take positions where warranted

---

## Proposed Synthesis Prompt (building on what worked)

```
You are synthesizing responses from multiple expert models. Your goal is to produce an analysis that is BOTH decisive AND defensible.

## STEP 1: Map Agreement and Disagreement

For each substantive claim in the inputs:
- Do models AGREE or DISAGREE?
- Does ANY model cite evidence/sources for this claim?
- Note confidence levels expressed by each model

## STEP 2: Apply Decision Rules

| Scenario | Action |
|----------|--------|
| Models agree + evidence cited | State with confidence, cite the source |
| Models agree, no evidence | State the claim BUT note: "Models agree on this, but none cite specific evidence" |
| Models disagree | DO NOT smooth over. State: "This is contested: [Model A view] vs [Model B view]" |
| One model has unique insight | Preserve it if well-reasoned, note it came from one source |
| Absolute language ("cannot", "always") | Convert to comparative ("much harder", "typically") unless truly universal |

## STEP 3: Synthesize

Write a unified analysis that:
- States confident claims confidently (where earned)
- Flags uncertainty where it exists (disagreement = uncertainty signal)
- Preserves unique insights
- Takes positions where evidence supports them
- Uses comparative language for contested claims

## STEP 4: Self-Check

Before finalizing, ask for each claim:
- What would falsify this?
- Is my confidence level appropriate?
- Am I stating something absolutely that should be hedged?

## CRITICAL RULES
- Disagreement between models is INFORMATION, not a problem to solve
- Agreement without evidence is NOT proof
- Do NOT over-hedge - maintain decisive recommendations where warranted
- Unique insights from one model may be the most valuable (don't average them away)
```

---

## Why This Could Beat Solo + Rigor

Solo + rigor calibrates well but:
- Cannot identify where it might be wrong (no external check)
- Cannot surface genuine uncertainty (disagreement)
- Has single knowledge base

This synthesis:
- Uses disagreement as uncertainty signal (information solo can't have)
- Uses agreement + evidence as high-confidence signal
- Preserves unique knowledge from different models
- Still maintains truth-aware calibration

---

## Test Design

### Hard Question Requirements

To actually test whether multi-model beats solo, we need questions where:
1. Models have genuinely different knowledge/views (not just style differences)
2. Disagreement would surface real uncertainty
3. Agreement without evidence would be dangerous
4. One model's unique knowledge would add value

### Candidate Questions

**Q1: Recent/Evolving Facts**
"What is the current cost per mile of subway construction in the US vs Europe, and what are the specific causal factors with their relative contribution?"

Why hard:
- Requires specific numbers (models may have different/outdated data)
- Causal attribution is contested (experts disagree)
- Agreement without sources would be overconfident

**Q2: Prediction with Trade-offs**
"For a mid-sized US city (pop 500K) considering transit investment, what should they prioritize: BRT, light rail, or enhanced bus? Model a specific scenario."

Why hard:
- Genuine expert disagreement exists
- Models might recommend differently based on different frameworks
- Requires explicit trade-off reasoning

**Q3: Contested Causation**
"Does transit-oriented development actually increase transit ridership, or does it just attract people who would ride anyway? What's the causal effect size?"

Why hard:
- Correlation vs causation is genuinely tricky
- Studies disagree
- Models might cite different research

---

## Experimental Protocol

### Round 1: Baseline
- Solo (GPT) + Simple prompt
- Solo (GPT) + Rigor prompt (truth-aware)

### Round 2: Multi-Model with New Synthesis
- 5 models + new synthesis prompt (above)
- Compare to solo + rigor

### Metrics
1. **Style score** (3-judge panel) - Did we maintain quality?
2. **Adversarial score** - Did we improve defensibility?
3. **NEW: Disagreement utilization** - Did synthesis actually USE disagreement as signal?
4. **NEW: Evidence tracking** - Did synthesis correctly flag unsourced claims?

### Success Criteria
Multi-model synthesis beats solo + rigor if:
- Adversarial score > 90% (solo + rigor baseline)
- OR adversarial equal but catches errors solo missed (qualitative)
- OR surfaces genuine uncertainty that solo couldn't (disagreement detection)

---

## Key Insight

The goal is NOT to produce a "better consensus."

The goal is to produce a response that:
1. Has earned confidence where evidence supports it
2. Acknowledges uncertainty where models disagree
3. Preserves unique valuable insights
4. Doesn't amplify false confidence from agreement

This is a fundamentally different synthesis goal than "integrate best ideas" or "find consensus."

---

## What Would Make Me Wrong

This approach fails if:
- Models don't actually disagree on anything meaningful (transit Q was like this)
- Disagreement is just noise, not signal
- The complexity of the synthesis prompt hurts more than helps
- Flagging uncertainty destroys actionability

We need to test with questions where models ACTUALLY disagree.

---

## Proposed Investigate Modes

Based on what we learned, here are modes designed to beat solo + rigor:

### Mode: `--default` (Enhanced Synthesis)

**What changes:** New synthesis prompt that uses disagreement as signal instead of smoothing it over.

**Synthesis prompt:**
```
You're synthesizing expert analyses. Agreement ≠ truth. Disagreement = uncertainty signal.

RULES:
1. Where models agree AND cite evidence → state confidently with citation
2. Where models agree WITHOUT evidence → state but note "consensus without cited evidence"
3. Where models DISAGREE → DO NOT smooth over. State both views, flag as uncertain
4. Where one model has unique insight → preserve if well-reasoned
5. Convert absolutes to comparatives unless truly universal

Still be decisive. Take positions where evidence supports them.
Do NOT over-hedge. Uncertainty flags are for genuinely uncertain things.
```

**Why it could beat solo + rigor:**
- Uses disagreement (information solo doesn't have)
- Prevents false confidence amplification
- Preserves unique knowledge across models

### Mode: `--rigor` (Truth-Aware + Disagreement + Evidence)

**What changes:** Add truth-aware prompt to individual models BEFORE synthesis, plus evidence tracking.

**Individual model prompt addition:**
```
Your claims will be adversarially challenged.
- Absolute language is easy to falsify
- Cite sources for factual claims where possible
- Mark confidence: HIGH (would bet on it), MEDIUM (likely), LOW (plausible), SPECULATION

Be decisive where warranted. Don't over-hedge.
```

**Synthesis addition:**
```
EVIDENCE TRACKING:
- Note which claims are cited vs uncited across models
- If models cite conflicting sources, flag explicitly
- If all models agree but none cite sources, this is "confident consensus without evidence" - flag it

CONFIDENCE CALIBRATION:
- If models disagree on confidence level (one HIGH, one LOW), this is an uncertainty signal
- If all models are HIGH confidence + agree + cite evidence → highest confidence
- If all models are HIGH confidence + agree + NO evidence → potential overconfidence, flag
```

**Why it could beat solo + rigor:**
- Individual models self-calibrate (truth-aware)
- Synthesis catches what solo can't: disagreement, uncited consensus, confidence miscalibration
- Evidence tracking prevents "sounds right" from becoming confident claim

### Mode: `--deep` (Maximum Rigor)

**What changes:** All of the above PLUS:
1. Longer/more thorough individual responses
2. Explicit adversarial self-check in synthesis
3. Structured claim extraction

**Synthesis addition:**
```
BEFORE FINALIZING, for each core claim in your synthesis:
- State what would falsify it
- Check: did ANY model disagree with this? If so, have I flagged uncertainty?
- Check: did ANY model cite evidence for this? If not, have I flagged it?
- Check: am I using absolute language? Convert to comparative if not truly universal.
```

**Why it could beat solo + rigor:**
- More thorough coverage (longer responses)
- Explicit self-check catches remaining overconfidence
- Structured approach ensures nothing slips through

---

## The Key Leverage Points (from Test 003)

| What Worked | How to Preserve |
|-------------|-----------------|
| Integration framing ("SUPERIOR analysis, not consensus") | Keep in synthesis |
| Truth-aware calibration (adversarial warning) | Add to individual prompts |
| "Do not over-hedge" | Include in all prompts |
| Citation prompting | Add evidence tracking |
| **Longer/detailed prompts** | Models are lazy - detailed prompts counteract this |

| What Failed | How to Fix |
|-------------|-----------|
| Consensus-seeking (averaged down) | Disagreement-first synthesis |
| Amplified confidence from agreement | "Agreement ≠ truth" in synthesis |
| Absolutes ("original sin", "cannot") | Convert to comparatives |
| Retrofitting lost action | Build calibration in from start |

### The "Lazy Model" Factor

The truth-aware prompt wasn't just about calibration - it was also LONGER and more DETAILED. This matters because:

1. **Models default to quick/superficial answers** - Short prompts get short effort
2. **Detailed prompts set higher expectations** - "You will be scored on X, Y, Z" prompts more thorough work
3. **Explicit criteria = rubric prompting** - Research shows this gives 15-30% improvement
4. **Framework to fill in** - Better than open-ended "just answer"

So the individual model prompts should be:
- Detailed enough to counteract laziness
- Include explicit criteria
- Provide structure/framework
- Not just "answer this question"

This is separate from truth-aware calibration - it's about prompting for thoroughness.

### Individual Model Prompt (Rigor Mode)

Combines thoroughness + truth-aware calibration:

```
[QUESTION]

You are an expert analyst. Your response will be evaluated on:

1. DEPTH: Identify root causes with evidence. Multiple perspectives. Nuanced.

2. SPECIFICITY: Cite specific numbers, studies, examples. Vague claims score poorly.

3. CALIBRATION: Your claims will be adversarially challenged.
   - Absolute language ("cannot", "always", "never") is easily falsified
   - Quantitative claims without sources will be challenged
   - Causal claims need evidence, not just plausibility

4. ACTIONABILITY: Clear recommendations with prioritization.

CONFIDENCE MARKING (required for substantive claims):
- HIGH: I would bet on this, strong evidence exists
- MEDIUM: Likely true, some uncertainty
- LOW: Plausible but uncertain, limited evidence
- SPECULATION: My best guess, could easily be wrong

RULES:
- Be thorough. Short/superficial answers score poorly.
- Be decisive where evidence supports it.
- Do NOT over-hedge. Uncertainty markers are for genuinely uncertain things.
- Cite sources where possible. "I cannot cite a source for this" is acceptable if honest.

Now provide your analysis.
```

This prompt:
- Sets high expectations (counteracts laziness)
- Includes explicit criteria (rubric prompting)
- Adds truth-aware calibration
- Requires confidence marking
- Preserves decisiveness ("do not over-hedge")

---

## Why These Modes Should Win

**Solo + rigor gets to ~90% adversarial.** It fails on:
- Claims where the model is confidently wrong (no external check)
- Uncertainty it can't surface (no disagreement possible)

**Multi-model with enhanced synthesis adds:**
1. Disagreement detection → surfaces genuine uncertainty
2. Evidence pooling → catches uncited confident claims
3. Unique insight preservation → doesn't average away one model's correct but minority view
4. Cross-model verification → one model might catch another's error

**The synthesis prompt is the key.** It must:
- NOT seek consensus
- NOT amplify confidence from agreement
- USE disagreement as uncertainty signal
- PRESERVE unique insights
- MAINTAIN decisiveness where warranted

---

## Test Protocol

### Question Selection
Use questions where:
1. Models are likely to disagree (contested topics)
2. Specific claims can be verified
3. Agreement without evidence would be risky

### Comparison
1. Solo (GPT) + simple → baseline
2. Solo (GPT) + rigor (truth-aware) → current best
3. Multi-model + default (new synthesis)
4. Multi-model + rigor (truth-aware + new synthesis)

### Metrics
- Style score (3-judge)
- Adversarial score
- NEW: Did synthesis actually flag disagreements?
- NEW: Did synthesis catch uncited confident claims?
- NEW: Did multi-model catch something solo missed?

### Success = Multi-model scores higher on adversarial BECAUSE it used disagreement/evidence information that solo couldn't have.

---

## Correction: Truth-Aware Already Fixed Absolutes

Looking back at N-Truth and M-Truth results, the truth-aware prompt DID fix the absolutes problem. The remaining ~10% failures were:

**N1-T Partially Survives:** "high confidence" slightly strong for evidence available
**M2-T Partially Survives:** causal attribution without comparative dataset

These aren't absolutes - they're subtler calibration issues:
1. Confidence slightly too high relative to evidence
2. Causal claims that should cite comparative data

### Can Multi-Model Help With These?

**For over-confidence without evidence:**
- If one model is confident and another hedges → signal
- If all models are confident but none cite evidence → flag "confident consensus, uncited"
- Multi-model can catch: "everyone agrees, but no one has proof"

**For causal claims needing comparative data:**
- If one model cites data and others don't → synthesis can require citation
- If models cite different data → surfaces methodological uncertainty
- Multi-model can catch: "this needs evidence, who has it?"

### The Margin is Thin But Real

Solo + rigor gets to ~90%. The remaining 10% are:
- Slightly overconfident claims (confidence vs evidence mismatch)
- Causal claims without comparative support

Multi-model synthesis could catch these by:
1. Comparing confidence levels across models
2. Pooling citations (if Model A cites and Model B doesn't, Model A's citation wins)
3. Flagging "everyone agrees but no one proves"

This is a smaller improvement than I originally proposed, but it's the REAL margin where multi-model could add value.

---

## Revised Modes (More Honest)

### Mode: `--default`
Same as today but with improved synthesis that uses disagreement as signal.

### Mode: `--rigor`
Truth-aware prompts to individual models + synthesis that:
- Compares confidence levels across models
- Pools and cross-checks citations
- Flags confident-but-uncited consensus

**Expected improvement over solo + rigor:** Small but meaningful on claims where:
- Solo was overconfident relative to evidence
- Solo made causal claims without citation
- One model has evidence others lack

### Mode: `--deep`
All of the above plus:
- Longer individual responses for thoroughness
- Explicit claim-by-claim evidence audit in synthesis

---

## The Honest Assessment

**Solo + rigor is very good.** It gets ~90% adversarial, maintains style (~27), and is cheap/fast.

**Multi-model + enhanced synthesis MIGHT add ~5-10% on specific failure modes:**
- Confidence calibration (cross-model comparison)
- Evidence pooling (one model cites, others don't)
- Disagreement surfacing (signals genuine uncertainty)

**But we need to test with questions where these margins matter.** The transit question may have been too easy - models broadly agreed and even partial failures were defensible.

---

## Questions Designed to Expose the Multi-Model Margin

The transit question was too easy because:
- Models broadly agreed
- No specific verifiable numbers that could be wrong
- "Partially survives" meant directionally correct

We need questions where:
1. **Models might disagree on facts** (surfaces uncertainty)
2. **Models might have different knowledge** (one knows something others don't)
3. **Specific claims are verifiable** (can be right or wrong, not just "directional")
4. **Being confidently wrong is easy** (without cross-checking)

### Question 1: Contested Numbers
```
What is the actual cost per kilometer of recent US subway projects vs European comparables?
- Cite specific projects with costs
- Control for tunneling %, station count, labor costs
- What percentage of the difference is attributable to: procurement, labor, regulations, design?
```

**Why this exposes the margin:**
- Models may cite different numbers for the same projects
- One model may cite a source others don't have
- Causal attribution requires evidence most models lack
- Multi-model could catch: disagreement on numbers, uncited causal claims

### Question 2: Recent/Changing Data
```
What is the current (2025-2026) transit ridership recovery rate for:
- NYC MTA (subway)
- SF BART
- LA Metro Rail
- Chicago CTA

As a percentage of 2019 levels. Cite your source and date.
```

**Why this exposes the margin:**
- Models have different training cutoffs
- One model may have more recent data
- Specific numbers are verifiable
- Multi-model could: pool most recent data, flag disagreement on numbers

### Question 3: Causal Attribution with Trade-offs
```
The NYC subway has seen slower ridership recovery than peer US systems.
What percentage of the shortfall is attributable to:
(a) Remote work (office proximity effect)
(b) Safety/quality perception
(c) Service cuts/reliability
(d) Demographic shifts
(e) Other factors

Cite evidence for your attribution. Acknowledge which attributions are well-supported vs speculative.
```

**Why this exposes the margin:**
- Causal attribution is genuinely contested
- Models may have different frameworks
- Easy to be confidently wrong
- Multi-model could: surface disagreement on attribution, pool evidence, flag uncited claims

### Question 4: Prediction
```
What will US transit ridership be in 2030 as a percentage of 2019?
- Provide point estimate and 80% confidence interval
- Identify the 3 key uncertainties that could move the outcome outside your interval
- What probability do you assign to each scenario: <70%, 70-90%, 90-110%, >110%?
```

**Why this exposes the margin:**
- Inherently uncertain (no one knows)
- Models may disagree on probability distributions
- Calibration is the key skill
- Multi-model could: surface disagreement on ranges, flag overconfidence

---

## Final Synthesis Prompt (Building on What Worked)

Combining:
- Integration framing (worked) - "SUPERIOR analysis, not consensus"
- Truth-aware calibration (worked) - "claims will be challenged"
- "Do not over-hedge" (essential)
- Disagreement handling (new) - use it as signal
- Evidence pooling (new) - citations matter

```
You are synthesizing multiple expert analyses into a single authoritative response.

## YOUR GOAL
Create an analysis that is BOTH decisive AND defensible. Not a summary. Not a consensus. A SUPERIOR analysis that integrates the best evidence and insights.

## HOW TO HANDLE INPUTS

1. AGREEMENT WITH EVIDENCE
   When models agree AND at least one cites evidence:
   → State confidently, include the citation
   → Example: "US subway costs are consistently higher than European peers (Transit Costs Project, NYU)"

2. AGREEMENT WITHOUT EVIDENCE
   When models agree but none cite evidence:
   → State the claim BUT flag it
   → Example: "Models agree that labor costs are a major driver, though none cite comparative data"

3. DISAGREEMENT
   When models disagree on facts or attribution:
   → DO NOT smooth over. This is uncertainty signal.
   → Example: "Estimates of the cost premium vary: Model A suggests 2-3x, Model B suggests 4-5x for complex projects"

4. UNIQUE INSIGHTS
   When one model has a well-reasoned point others missed:
   → Preserve it (don't average away because it's minority)
   → Example: "Uniquely, Model C notes that utility relocation costs are often excluded from peer comparisons"

## CALIBRATION RULES

- Convert absolutes ("cannot", "always") to comparatives ("much harder", "typically") unless truly universal
- For any specific number, note if models agreed or disagreed
- For causal claims, note if evidence was cited
- Maintain decisiveness - take positions where evidence supports them
- Do NOT over-hedge - uncertainty flags are for genuinely uncertain things

## BEFORE FINALIZING

For each core claim, check:
- Did models agree or disagree? (Have I reflected this?)
- Did anyone cite evidence? (Have I included it or flagged its absence?)
- Am I more confident than the evidence supports?

## WHAT SUCCESS LOOKS LIKE

A response that:
- Makes confident claims where earned (agreement + evidence)
- Flags genuine uncertainty (disagreement or uncited consensus)
- Preserves valuable unique insights
- Maintains clear, actionable recommendations
- Would survive adversarial scrutiny
```

---

## Test Plan

### Round 1: Baseline
- Question 1 (Contested Numbers) + Solo GPT + simple prompt
- Question 1 + Solo GPT + rigor (truth-aware)

### Round 2: Multi-Model
- Question 1 + 5 models + current synthesis
- Question 1 + 5 models + new synthesis prompt (above)

### Evaluation
- Style score (3-judge)
- Adversarial score
- **Factual accuracy** (verify cited numbers)
- **Did synthesis use disagreement as signal?**
- **Did synthesis flag uncited confident claims?**

### Success Criteria
Multi-model + new synthesis beats solo + rigor if:
- Catches a factual error solo made (numbers wrong)
- Surfaces uncertainty solo couldn't (via disagreement)
- Achieves higher adversarial score through better evidence use
- Does NOT lose style score (maintains decisiveness)

---

## Unexplored Lever: Token Budget & Multiple Runs

Multi-model gives us 5× the tokens. We've been using this for breadth (5 different models). But we could use it differently:

### Option 1: Temperature Diversity (Same Model, Different Settings)
Instead of 5 different models, run:
- GPT @ temp 0 (precise, deterministic)
- GPT @ temp 0.5 (balanced)
- GPT @ temp 1.0 (creative, diverse)

**Why this might work:**
- Different temps genuinely produce different outputs
- temp 0 catches "obvious" answers, temp 1.0 catches "creative" answers
- Disagreement between temps = model's own uncertainty
- Avoids "different models, same training data" problem

### Option 2: Self-Critique Pass
Use token budget for depth instead of breadth:
- Model generates initial response
- Model critiques its own response (adversarial self-check)
- Model revises based on critique
- Synthesis integrates the refined output

**Why this might work:**
- Test 003 showed iteration works if you don't lose action
- Self-critique with explicit "find problems" prompt
- More tokens = more thorough critique
- Could catch errors single-pass misses

### Option 3: Generate → Critique → Revise (Cross-Model)
- Model A generates initial analysis
- Model B (different model) critiques A's claims
- Model A revises based on B's critique
- Synthesis integrates

**Why this might work:**
- Cross-model critique catches blind spots
- Model B has different knowledge/biases
- Revision is targeted (not wholesale hedge)
- Similar to what humans do in review

### Option 4: Draft → Evidence Check → Final
- Model generates draft with claims marked
- Second pass specifically checks: "For each claim, cite evidence or flag as uncited"
- Final pass integrates and resolves

**Why this might work:**
- Separates "thinking" from "evidence checking"
- Forces explicit evidence audit
- Uses tokens for depth on specific failure mode

### Which to Test First?

**Temperature diversity** is easy to implement and tests whether diversity itself (not just model difference) matters.

**Self-critique pass** directly addresses the "model can't catch its own errors" problem and builds on what worked (truth-aware prompting).

Recommendation: Test **self-critique pass** because:
1. Directly targets the failure mode (can't self-check)
2. Uses token budget for depth (more thorough)
3. Easy to A/B test vs single-pass
4. If it works, it's cheaper than 5 models

### Self-Critique Mode Design

```
PHASE 1: Generate
[Individual model prompt from above]
Generate your initial analysis.

PHASE 2: Critique (same model, different prompt)
You are a rigorous fact-checker reviewing an analysis. Your ONLY job is to find problems.

For each substantive claim in the analysis:
1. Is this claim well-supported or assumed?
2. What would falsify it?
3. Is the confidence level appropriate?
4. Are there counterexamples?

Be harsh. Find problems. Do not validate.

PHASE 3: Revise
You wrote an analysis and received a critique. Revise your analysis to:
- Fix legitimate criticisms
- Add evidence where it was missing
- Adjust confidence where it was overconfident
- BUT maintain actionable recommendations - do not retreat into pure hedging

SYNTHESIS: Integrate the revised outputs from all models.
```

This uses 3× the tokens per model but produces higher-quality individual outputs for synthesis.

---

## What Worked from "Unstructured" Tools & Principles (Test 003)

Looking back at the fair comparison, the **v3 Hybrid** approach used investigation principles:

| v3 Element | Style Impact | What It Did |
|------------|--------------|-------------|
| Problem reframing | +Clarity | "Is this the RIGHT question?" |
| Known vs Contested | +Honesty | Separated confidence levels |
| 80/20 / Crux | +Depth | "Land use is the original sin" |
| Steelmanning | +Honesty | Engaged alternatives seriously |
| Tiered recommendations | +Actionability | Clear priorities |

v3 Hybrid (28.0) beat basic synthesis (24.3) by 3.7 points - these principles worked.

**Then GPT Integration (28.3)** beat v3 by being more decisive:
- "NOT consensus, SUPERIOR analysis"
- "Be MORE decisive, take a position"
- "Preserve strongest steelmanned alternatives"

The integration framing unlocked something the investigation principles alone didn't.

---

## The Synergy Hypothesis: 1+1=3

We tested improvements **separately**:

| Improvement | Style Impact | Adversarial Impact | Tested With |
|-------------|--------------|-------------------|-------------|
| Truth-aware prompt | +5 | **+20** | Solo GPT |
| Integration framing | +4 | -7 (hurt!) | Multi-model |
| v3 investigation principles | +4 | Not tested alone | Multi-model |
| Longer detailed prompts | ? | ? | Mixed into truth-aware |

**The insight:** Integration framing HURT adversarial (63% vs 70%) because it said "be decisive" without "avoid absolutes."

What if we **combined**:
- Integration framing ("SUPERIOR analysis")
- + Truth-aware calibration ("avoid absolutes")
- + v3 investigation principles (steelmanning, known vs contested)
- + Longer/detailed prompts (counteract laziness)

These target DIFFERENT failure modes:
- Integration: prevents consensus averaging down
- Truth-aware: prevents absolutes/overconfidence
- v3 principles: ensures coverage/depth
- Detailed prompts: counteracts laziness

They shouldn't interfere - they should stack.

---

## Prompt Engineering Combinations to Test

### Minimal Factor Isolation

Create minimal prompts that isolate each factor:

| Version | Additions to Simple Prompt |
|---------|---------------------------|
| A: Baseline | None |
| B: +Truth-aware | "Your claims will be adversarially challenged. Avoid absolutes." |
| C: +Citation | "Cite sources for factual claims where you can." |
| D: +Thoroughness | "Short answers score poorly. Be thorough and specific." |
| E: +Confidence | "Mark substantive claims: HIGH/MEDIUM/LOW confidence" |
| F: +Integration | "Create a SUPERIOR analysis, not a summary. Take positions." |
| G: Combined | B + C + D + E (everything but F) |
| H: All | B + C + D + E + F |

**Hypothesis:** If factors are independent, G should score ~90%+ and H should match or exceed.

### For Multi-Model, Stack Everything

**Individual model prompt:**
```
[Question]

You are an expert analyst. Your response will be evaluated on:

1. DEPTH: Root causes with evidence. Multiple perspectives. Nuanced.
2. SPECIFICITY: Cite specific numbers, studies, examples.
3. CALIBRATION: Claims will be adversarially challenged.
   - Avoid absolutes ("cannot", "always")
   - Quantitative claims need sources
4. ACTIONABILITY: Clear recommendations with prioritization.

Mark confidence for substantive claims: HIGH / MEDIUM / LOW / SPECULATION

Be thorough. Be decisive where evidence supports it. Do NOT over-hedge.
```

**Synthesis prompt (combining everything that worked):**
```
You are synthesizing multiple expert analyses into a single SUPERIOR response.

## GOAL
Not a summary. Not a consensus. An analysis that is BOTH decisive AND defensible.

## FIRST: Map Agreement/Disagreement
For each substantive claim:
- Do models agree or disagree?
- Did anyone cite evidence?
- Note confidence levels

## THEN: Apply Decision Rules
| Scenario | Action |
|----------|--------|
| Agreement + evidence | State confidently with citation |
| Agreement - evidence | State but flag: "consensus without cited evidence" |
| Disagreement | DO NOT smooth over. Surface both views as uncertainty signal |
| Unique insight | Preserve if well-reasoned (don't average away) |

## CALIBRATION
- Convert absolutes to comparatives unless truly universal
- For numbers, note if models agreed/disagreed
- Maintain decisiveness - take positions where earned
- Do NOT over-hedge

## KNOWN vs CONTESTED (from v3)
Explicitly separate:
- What is well-established (models agree + evidence)
- What is plausible but uncertain (models agree, no evidence)
- What is genuinely contested (models disagree)

## CRUX
Identify the 80/20: what's the core insight or leverage point?

## STEELMAN
For any alternative view, present its strongest form.

## BEFORE FINALIZING
For each core claim:
- Did models agree or disagree? Reflected?
- Did anyone cite evidence? Included or flagged?
- Am I overconfident relative to evidence?
```

This synthesis combines:
- Integration framing (SUPERIOR, decisive)
- Truth-aware (calibration rules)
- v3 principles (known vs contested, crux, steelman)
- Disagreement-as-signal (new)
- Evidence tracking (new)

---

## Quick Win: Minimal Prompt Engineering Test

Before the full multi-model test, run a quick solo test to see if prompt factors compound:

### Protocol

Question: Same transit question (we have baseline scores)

| Run | Prompt | Expected |
|-----|--------|----------|
| 1 | Simple (baseline) | ~22 style, ~70% adv |
| 2 | +Truth-aware only | ~27 style, ~90% adv (confirmed) |
| 3 | +Citation only | ? |
| 4 | +Thoroughness only | ? |
| 5 | Combined (2+3+4) | ≥90%? Synergy? |

If 5 > 2, we have synergy. If 5 ≈ 2, truth-aware captures most of the value.

### Minimal Prompt Variants

**B: Truth-aware only:**
```
[Question]

Your claims will be adversarially challenged.
- Avoid absolute language (cannot, always, never)
- Quantitative claims without sources will be questioned
Be decisive where evidence supports it.
```

**C: Citation only:**
```
[Question]

For factual claims, cite a source if you know one.
If you don't have a source, say "I cannot cite a source for this."
```

**D: Thoroughness only:**
```
[Question]

Your response will be scored on depth and specificity.
- Short/superficial answers score poorly
- Include specific examples, numbers, studies
- Address multiple perspectives
```

**G: Combined:**
```
[Question]

Your claims will be adversarially challenged.
- Avoid absolutes (cannot, always)
- Cite sources for factual claims
- If no source, acknowledge it

Be thorough - short answers score poorly.
Be decisive where evidence supports it.
```

---

## Cheap Wins Checklist

Prompt engineering improvements that cost nothing:

| Improvement | Tested? | Works? | Cost |
|-------------|---------|--------|------|
| Truth-aware calibration | Yes | **+20 adv** | Free |
| "Do not over-hedge" | Yes | Essential | Free |
| Citation prompting | Partial | Helped | Free |
| Explicit criteria/rubric | Yes | Helps | Free |
| Longer/detailed prompt | Implicit | Likely helps | Free |
| Confidence marking | No | ? | Free |
| "Be thorough" | No | ? | Free |

Next: Test whether these stack (1+1=3) before investing in expensive multi-model improvements.
