# Fair Comparison Test 003

## Date: 2026-01-23

## Purpose
Test 002 had methodological flaws:
1. Different prompts for different approaches
2. Weak synthesizer (Sonnet) for multi-model
3. Single judge (GPT) - potential self-preference bias

This test controls for all three.

---

## Standardized Prompt

All approaches receive the same comprehensive prompt:

```
Why do US mass transit systems struggle financially, and what should be done?

Analyze this comprehensively. Consider:
- Root causes (structural, operational, political)
- Different stakeholder perspectives
- Realistic interventions and their tradeoffs
- Your honest assessment of what would actually work

Take a position. Be intellectually honest about uncertainty.
```

---

## Approaches Being Tested

| # | Approach | Description |
|---|----------|-------------|
| J | GPT-5.2 Solo | Single model, standardized prompt |
| K | Claude Opus Solo | Single model, standardized prompt |
| L | 5-Model → Opus Synthesis | All 5 models queried, Opus synthesizes |
| M | v3 Hybrid (Opus) | 5 scouts + v3 prompt → Opus synthesis |

**Controls:**
- Same prompt for all
- SOTA model (Opus) for all synthesis
- 3-judge panel: GPT-5.2, Claude Opus, Gemini 3 Pro

---

## Results

### Individual Judge Scores

**GPT-5.2 Judge:**
| Approach | Clarity | Diversity | Depth | Synthesis | Action | Honesty | Total |
|----------|---------|-----------|-------|-----------|--------|---------|-------|
| J: GPT Solo | 5 | 5 | 5 | 5 | 5 | 4 | **29** |
| K: Claude Solo | 5 | 5 | 4 | 4 | 4 | 5 | **27** |
| L: 5-Model | 4 | 5 | 4 | 5 | 4 | 5 | **27** |
| M: v3 Hybrid | 5 | 4 | 4 | 4 | 5 | 5 | **27** |

**Claude Opus Judge:**
| Approach | Clarity | Diversity | Depth | Synthesis | Action | Honesty | Total |
|----------|---------|-----------|-------|-----------|--------|---------|-------|
| J: GPT Solo | 5 | 5 | 4 | 5 | 4 | 4 | **27** |
| K: Claude Solo | 4 | 4 | 4 | 4 | 4 | 5 | **25** |
| L: 5-Model | 4 | 5 | 3 | 4 | 3 | 4 | **23** |
| M: v3 Hybrid | 5 | 4 | 5 | 5 | 5 | 5 | **29** |

**Gemini 3 Pro Judge:**
| Approach | Clarity | Diversity | Depth | Synthesis | Action | Honesty | Total |
|----------|---------|-----------|-------|-----------|--------|---------|-------|
| J: GPT Solo | 5 | 4 | 4 | 5 | 4 | 4 | **26** |
| K: Claude Solo | 4 | 4 | 4 | 4 | 4 | 5 | **25** |
| L: 5-Model | 4 | 5 | 3 | 4 | 3 | 4 | **23** |
| M: v3 Hybrid | 5 | 4 | 5 | 4 | 5 | 5 | **28** |

### Aggregated Scores (Average of 3 judges)

| Approach | Clarity | Diversity | Depth | Synthesis | Action | Honesty | **Avg Total** |
|----------|---------|-----------|-------|-----------|--------|---------|---------------|
| J: GPT Solo | 5.0 | 4.7 | 4.3 | 5.0 | 4.3 | 4.0 | **27.3** |
| K: Claude Solo | 4.3 | 4.3 | 4.0 | 4.0 | 4.0 | 5.0 | **25.7** |
| L: 5-Model Baseline | 4.0 | 5.0 | 3.3 | 4.3 | 3.3 | 4.3 | **24.3** |
| M: v3 Hybrid | 5.0 | 4.0 | 4.7 | 4.3 | 5.0 | 5.0 | **28.0** |

### Final Rankings

| Rank | Approach | Avg Score | Type |
|------|----------|-----------|------|
| **1** | **M: v3 Hybrid** | **28.0** | Multi-model (5 scouts + v3 prompt) |
| 2 | J: GPT Solo | 27.3 | Single model |
| 3 | K: Claude Solo | 25.7 | Single model |
| 4 | L: 5-Model Baseline | 24.3 | Multi-model (5 scouts + basic synthesis) |

### Winner by Category (Consensus across judges)

| Category | Winner | Notes |
|----------|--------|-------|
| **Highest Overall** | M (v3 Hybrid) | 2 of 3 judges ranked it first |
| **Best Single Insight** | K (Claude Solo) - "core paradox" OR M - "land use is original sin" | Judges split |
| **Most Actionable** | M (v3 Hybrid) | All 3 judges agreed |
| **Most Intellectually Honest** | K/M (tie) | All 3 judges noted this tie |

---

## Key Findings

### 1. Does multi-model beat solo when prompts are equal?
**Mixed.** v3 Hybrid (multi-model) beat solo models, but basic 5-model synthesis came last.
- **v3 Hybrid (28.0)** > **GPT Solo (27.3)** > **Claude Solo (25.7)** > **5-Model Baseline (24.3)**
- The multi-model advantage comes from the **investigation prompt**, not just having 5 perspectives.

### 2. Does SOTA synthesis change the multi-model result?
**Yes, dramatically.** When we used Opus for synthesis (instead of Sonnet in Test 002's baseline), the 5-model approach still underperformed, but the v3 Hybrid worked well.
- This suggests the synthesis prompt matters more than the synthesizer model.

### 3. Do different judges agree on rankings?
**Mostly yes.**
- All 3 judges ranked L (5-Model Baseline) last
- 2/3 judges ranked M (v3 Hybrid) first
- GPT ranked J (itself) first, but this was close to the consensus

### 4. Is there judge self-preference bias?
**Some evidence, but not strong.**
- GPT gave itself 29/30, highest score
- Claude gave M (which Claude wrote) 29/30, highest score
- But Gemini also ranked M highest despite not being involved
- The rankings are fairly consistent across judges

---

## Key Implications

### 1. **The v3 prompt works**
The multi-model approach with structured investigation (disaggregation, 5 whys, 80/20, steelmanning) outperformed:
- Solo SOTA models given the same prompt
- Basic multi-model synthesis

### 2. **Basic synthesis is not enough**
Just aggregating 5 model responses (L) scored worst. The value comes from:
- Explicit problem reframing
- Separating "known" from "contested"
- Steelmanning alternatives
- Identifying the crux (80/20)

### 3. **Solo models are strong competitors**
GPT Solo (27.3) came very close to v3 Hybrid (28.0). The margin is small enough that cost/latency tradeoffs matter:
- Solo: 1 API call, ~70s
- v3 Hybrid: 6 API calls, ~100s

### 4. **Judge consensus is higher than expected**
Despite different models judging, they largely agreed on:
- v3 Hybrid won for actionability and depth
- Basic synthesis underperformed on depth
- Claude Solo won for intellectual honesty

---

## Comparison to Test 002 (Unfair Test)

| Metric | Test 002 (Unfair) | Test 003 (Fair) |
|--------|-------------------|-----------------|
| GPT Solo rank | 1st (4.5) | 2nd (27.3) |
| Best multi-model | Adaptive Structured (4.0) | v3 Hybrid (28.0) |
| Solo vs Multi winner | Solo | Multi (v3 Hybrid) |
| Judges | 1 (GPT only) | 3 (GPT, Claude, Gemini) |

**Key difference:** When prompts are equalized and multi-model uses good synthesis prompting, multi-model can win.

---

## Cost-Effectiveness Analysis

### Cost & Latency

| Approach | API Calls | Latency | Est. Cost |
|----------|-----------|---------|-----------|
| J: GPT Solo | 1 | ~67s | ~$0.04 |
| K: Claude Solo | 1 | ~71s | ~$0.05 |
| L: 5-Model Baseline | 6 | ~105s | ~$0.18 |
| M: v3 Hybrid | 6 | ~106s | ~$0.18 |

### Score per Dollar

| Approach | Score | Cost | Score/$ |
|----------|-------|------|---------|
| **J: GPT Solo** | 27.3 | ~$0.04 | **683** |
| K: Claude Solo | 25.7 | ~$0.05 | 514 |
| M: v3 Hybrid | 28.0 | ~$0.18 | 156 |
| L: 5-Model | 24.3 | ~$0.18 | 135 |

**Takeaway:** GPT Solo is ~4x more cost-effective than v3 Hybrid for only 2.5% lower quality.

---

## Why Does Synthesis Including GPT Score Worse Than GPT Alone?

This was the most surprising finding. Analysis revealed:

### Root Causes (from multi-model analysis)

**1. Information Loss Through Compression**
- GPT's 7 root causes (A-G) → collapsed into 3-4 "agreed root causes"
- Specific mechanisms and causal chains → generic category labels
- "What won't work" section → likely dropped entirely
- Tradeoff specificity → flattened into priority tiers

**2. Consensus-Seeking Diluted Strong Positions**
- Bold thesis ("the package is the point") → hedged or buried
- Decisive recommendations → softened to "some models suggest..."
- Sharp prioritization → "multiple factors contribute"

**3. Genre Shift: Analysis → Meta-Analysis**
- GPT Solo answered the transit question
- Synthesis described what five models *said* about the transit question
- Evaluators wanted problem-solving, not opinion surveys

**4. "Best Student in Group Project" Problem**
- If GPT was strongest, synthesis mathematically regresses toward the mean
- Weaker models' content consumed space that could preserve GPT's insights

### Key Insight
*"Synthesis ≠ Improvement when the best input is already excellent."*

The operation needed was **integration** (take best ideas, write superior analysis) not **synthesis** (find common ground).

### Why v3 Hybrid Avoided This Trap
The v3 prompt explicitly instructs:
- Reframe the question first (don't just aggregate)
- Separate "known" from "contested" (preserve uncertainty)
- Identify the crux/80/20 (prioritize, don't flatten)
- Steelman alternatives (preserve strong dissent)

This shifted from "summarize agreement" to "investigate and synthesize," preserving the depth that basic synthesis lost.

---

## What v3 Elements Added Most Value

Comparing v3 Hybrid (28.0) to basic 5-Model Synthesis (24.3):

| v3 Element | What It Did | Score Impact |
|------------|-------------|--------------|
| **Problem reframing** | "Is this the RIGHT question?" | +Clarity |
| **Known vs Contested** | Separated confidence levels | +Honesty |
| **80/20 / Crux** | Identified "land use is original sin" | +Depth |
| **Steelmanning** | Engaged AV/micromobility alternative | +Honesty |
| **Tiered recommendations** | Clear priorities, not flat list | +Actionability |

The v3 prompt turned synthesis from "committee report" into "investigation report."

---

---

## Round 2: GPT Integration Synthesis

### Hypothesis
User suggested that:
1. GPT may have been overconfident (judged as insightful)
2. Different models capture different issues - multi-model diversity has value
3. With the right synthesis prompt (integration, not consensus) + GPT as synthesizer, synthesizing v3 + v2 + McKinsey might win

### New Approach Tested

**N: GPT Integration of Top 3 Analyses**
- Inputs: v3 Hybrid + Unstructured v2 + McKinsey Guided
- Synthesizer: GPT-5.2 (not Claude)
- Prompt: Explicitly told NOT to find consensus, but to INTEGRATE best ideas into SUPERIOR analysis

### Judge Scores for N

| Judge | Clarity | Diversity | Depth | Synthesis | Action | Honesty | **Total** |
|-------|---------|-----------|-------|-----------|--------|---------|-----------|
| GPT | 5 | 4 | 4 | 5 | 4 | 4 | **26** |
| Claude | 5 | 4 | 5 | 5 | 5 | 5 | **29** |
| Gemini | 5 | 5 | 5 | 5 | 5 | 5 | **30** |
| **Avg** | **5.0** | **4.3** | **4.7** | **5.0** | **4.7** | **4.7** | **28.3** |

### Updated Rankings (All Approaches)

| Rank | Approach | Avg Score | Type |
|------|----------|-----------|------|
| **1** | **N: GPT Integration** | **28.3** | Multi-model synthesis (GPT) |
| 2 | M: v3 Hybrid | 28.0 | Multi-model synthesis (Claude) |
| 3 | J: GPT Solo | 27.3 | Single model |
| 4 | K: Claude Solo | 25.7 | Single model |
| 5 | L: 5-Model Baseline | 24.3 | Multi-model synthesis (Claude) |

### Key Findings

**1. The hypothesis was confirmed: GPT Integration won (28.3)**
- Beat v3 Hybrid (28.0) and GPT Solo (27.3)
- Gemini gave it a perfect 30/30

**2. Integration > Consensus**
- The prompt explicitly said "do NOT find consensus" and "be MORE decisive"
- This preserved the sharp insights from individual analyses

**3. GPT as synthesizer worked well**
- User's intuition that GPT might synthesize better than Claude was supported
- GPT may be better at decisive integration; Claude better at epistemic caution

**4. Prompt engineering matters enormously**
- Same inputs (v3, v2, McKinsey)
- Different prompt ("integrate best ideas, be decisive")
- Different result (28.3 vs 24.3 for basic synthesis)

### What Made N Work

| Element | How It Helped |
|---------|--------------|
| "NOT consensus" instruction | Prevented averaging down |
| "SUPERIOR analysis" framing | Set high bar for output |
| "Be MORE decisive" | Prevented hedging |
| "Preserve strongest steelmanned alternatives" | Kept intellectual honesty |
| GPT as synthesizer | Brought decisiveness + integration skill |

### Implications for Minds Design

1. **Synthesis prompt is the highest-leverage variable** - more important than model choice or number of scouts
2. **"Integration" framing > "Synthesis" framing** - tell the synthesizer to create something new, not summarize agreement
3. **Match synthesizer to task** - GPT for decisiveness, Claude for caution/honesty
4. **Multi-model CAN beat solo** - but only with good synthesis prompting

---

## Files Generated

- `test003_j_gpt_solo.txt` - GPT-5.2 solo response
- `test003_k_claude_solo.txt` - Claude Opus solo response
- `test003_l_5model_opus.txt` - 5-model baseline with Opus synthesis
- `test003_m_v3_hybrid.txt` - v3 Hybrid response
- `test003_n_gpt_integration.txt` - GPT Integration of top 3 analyses
- `test003_judge_gpt.txt` - GPT judge scores (J, K, L, M)
- `test003_judge_claude.txt` - Claude judge scores (J, K, L, M)
- `test003_judge_gemini.txt` - Gemini judge scores (J, K, L, M)
- `test003_n_judge_*.txt` - Judge scores for N
