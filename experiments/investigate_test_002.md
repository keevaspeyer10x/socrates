# Investigate Mode Test 002

## Date: 2026-01-23

## Question
**"Why do US mass transit systems struggle financially, and what should be done?"**

Why this question:
- Multi-frame (economic, political, cultural, urban design)
- No single right answer
- Rewards both disaggregation AND creative reframing
- Deep structure underneath surface answers
- Real policy implications

---

## Approaches Being Tested

| # | Approach | Description |
|---|----------|-------------|
| A | Baseline | minds ask (5 models → synthesis) |
| B | Unstructured v1 | 5 scouts → follow interesting threads with judgment |
| C | Unstructured v2 | Empowered + optional toolkit + self-annotation |
| D | Adaptive Structured | Explore frames → find crux → go deep → steelman + synthesize |
| E | McKinsey Guided | Senior consulting partner principles |
| F | v3 Hybrid | Combines best elements from D, E, C |
| G | GPT-5.2 Solo | Single model, comprehensive prompt |
| H | Claude Opus Solo | Single model, comprehensive prompt |
| I | Top-3 Synthesis | Synthesis of D + E + C outputs |

---

## Results

### Scores (1-5 scale, judged by GPT-5.2)

| Approach | Problem Clarity | Frame Diversity | Depth | Synthesis | Actionability | Intellectual Honesty | **Avg** |
|----------|----------------|-----------------|-------|-----------|---------------|---------------------|---------|
| A: Baseline | 3 | 3 | 2 | 3 | 4 | 3 | 3.0 |
| B: Unstructured v1 | 4 | 3 | 4 | 3 | 2 | 3 | 3.2 |
| C: Unstructured v2 | 4 | 4 | 4 | 3 | 3 | 4 | 3.7 |
| D: Adaptive Structured | 4 | 4 | 4 | 4 | 3 | **5** | 4.0 |
| E: McKinsey Guided | **5** | 3 | 3 | 4 | 4 | 3 | 3.7 |
| F: v3 Hybrid | **5** | 4 | 4 | 4 | 4 | **5** | **4.3** |
| G: GPT-5.2 Solo | 4 | **5** | **5** | 4 | **5** | 4 | **4.5** |
| H: Claude Opus Solo | **5** | 4 | 4 | 4 | 3 | **5** | 4.2 |
| I: Top-3 Synthesis | 4 | **5** | 4 | **5** | 4 | 4 | **4.3** |

### Winner by Category

| Category | Winner | Why |
|----------|--------|-----|
| **Highest Overall** | G (GPT-5.2 Solo) | 4.5 avg - highest depth + actionability with strong frame coverage |
| **Best Reframing** | F (v3 Hybrid) | "No transit system anywhere is profitable—why does US get less value per subsidy dollar?" Cleanly redirects debate. |
| **Went Deepest** | G (GPT-5.2 Solo) | Comprehensive stakeholder + service model analysis |
| **Most Actionable** | G (GPT-5.2 Solo) | Concrete service model, "don't do X" guardrails, city-specific moves |
| **Most Intellectually Honest** | F/H (tie) | F: confidence levels + steelmanning; H: explicit hard constraints and uncomfortable options |
| **Best Synthesis** | I (Top-3 Synthesis) | 5/5 - best integration of multiple perspectives |

### Key Observations

**What each approach did well:**

- **Baseline**: Pragmatic menu of interventions, good briefing document
- **Unstructured v1**: Strong macro-frame ("hostile ecosystem"), deep political economy
- **Unstructured v2**: Good multi-level decomposition, specific cost drivers, stakeholder tensions
- **Adaptive Structured**: Best evidence quality distinction, stable conclusions from steelmanning
- **McKinsey Guided**: Best problem reframing ("it's a policy choice, not a failure")

**What each approach did poorly:**

- **Baseline**: Didn't reframe, limited depth, list-like recommendations
- **Unstructured v1**: Less operational detail, weak actionability
- **Unstructured v2**: Risk of catalogue, less crisp theory of change
- **Adaptive Structured**: Hedging can blunt decisiveness
- **McKinsey Guided**: Narrower frame diversity, may underweight operational realities

---

## Evaluation Dimensions

1. **Problem Clarity** - How well defined is the actual problem?
2. **Frame Diversity** - How many valid frames identified?
3. **Depth** - How deep does the analysis go?
4. **Synthesis Quality** - How well integrated is the conclusion?
5. **Actionability** - Are recommendations concrete and useful?
6. **Intellectual Honesty** - Uncertainty acknowledged? Alternatives considered?

---

## Principle Usage Tracking (v2 only)

| Principle | Used? | Self-reported helpfulness |
|-----------|-------|---------------------------|
| Disaggregation | YES | "helped reveal that scouts were mostly agreeing on different facets" |
| 5 Whys | YES | Applied to "why is farebox recovery low?" - traced chain |
| First Principles | No | - |
| Prioritization | No | - |
| Steelman | YES | Steelmanned "suburban taxpayer" position |
| So What? | No | - |

**Observation**: v2 used 3 of 6 tools. The self-annotation worked - we can see which tools were applied and whether they helped.

---

## Post-Mortem

### Surprising Results

1. **Adaptive Structured won overall** (4.0 avg) despite our hypothesis that structure hurts
   - But it won on INTELLECTUAL HONESTY (5/5), not depth or insight
   - The "confident vs contested" separation added real value
   - Steelmanning forced consideration of alternatives

2. **McKinsey Guided had the best SINGLE insight** (problem reframing)
   - "Should transit be self-sustaining?" changed the entire frame
   - But narrower overall - traded diversity for decisiveness

3. **Baseline was most actionable** (4/5)
   - Sometimes "list of interventions" IS what you need
   - Less intellectual depth, more practical utility

4. **Unstructured v2 beat v1** (3.7 vs 3.2)
   - The toolkit was actually used (3/6 principles)
   - Frame diversity improved (4 vs 3)
   - Intellectual honesty improved (4 vs 3)

### What Elements Worked Across Approaches

| Element | Appeared In | Value Added |
|---------|-------------|-------------|
| **Problem reframing** | McKinsey (best), v1 | Changes the solution space |
| **Confidence separation** | Adaptive (best), v2 | Reduces overclaiming |
| **Steelmanning** | Adaptive (explicit), v2 (used) | More stable conclusions |
| **Multi-level decomposition** | v2 (best) | Realistic causality |
| **Specific cost drivers** | v2 | Explanatory power |

### What Didn't Work

| Element | Issue |
|---------|-------|
| **Depth without synthesis** | v1 went deep but weak actionability |
| **Catalogue risk** | v2 named many factors without prioritizing |
| **Narrow framing** | McKinsey reframed well but missed operational detail |

### Implications for Design

1. **The best approach might be a HYBRID**:
   - McKinsey's problem reframing discipline
   - Adaptive's confidence separation + steelmanning
   - v2's toolkit availability (without mandating use)

2. **Intellectual honesty > raw depth**
   - Adaptive won by being honest about uncertainty, not by going deepest
   - This aligns with "empowering the model" - honesty is trained behavior

3. **Reframing is high-leverage**
   - McKinsey's single best contribution was questioning the premise
   - This should be explicitly encouraged (but not mandated)

4. **Principles as toolkit WORKS**
   - v2 used 3/6 tools based on judgment
   - Self-annotation lets us learn which tools help

### Recommended v3 Design

Combine best elements:
```
You're investigating [X]. Here's what we know from 5 diverse perspectives: [scouts]

Before diving in:
- Is the question framed right? What's the REAL question here?
- What do we KNOW vs ASSUME about this?

As you investigate:
- Use whatever approach feels right. Some find these helpful: [toolkit]
- Note when you're confident vs when evidence is contested.

Before concluding:
- What's the strongest alternative to your view?

Output what's useful. Multiple valid frames are fine. Uncertainty is honest.
```

---

## Round 2: Extended Testing

### New Approaches Added

| Approach | Description | Rationale |
|----------|-------------|-----------|
| F: v3 Hybrid | Combined best elements from D, E, C | Test if combining winners beats them individually |
| G: GPT-5.2 Solo | Single model with comprehensive prompt | Baseline: can one well-prompted model beat multi-model? |
| H: Claude Opus Solo | Single model with comprehensive prompt | Same baseline, different model |
| I: Top-3 Synthesis | Meta-synthesis of D + E + C outputs | Test if synthesizing top approaches adds value |

### Key Findings from Round 2

**1. GPT-5.2 Solo beat all multi-model approaches (4.5 avg)**
- This is the most important finding
- A single well-prompted SOTA model outperformed all our elaborate investigation frameworks
- Reasons: comprehensive prompt, full context, native reasoning without imposed structure

**2. The synthesis approaches tied for second (4.3 avg)**
- v3 Hybrid and Top-3 Synthesis both scored 4.3
- Synthesis adds value but didn't exceed solo model performance
- The "overhead" of multi-model coordination may not pay off

**3. Claude Opus Solo close behind (4.2 avg)**
- Different model, similar strong performance
- Notable for intellectual honesty (5/5) but less actionable (3/5)

**4. v3 Hybrid validated the design hypothesis**
- Scored higher than any previous multi-model approach (4.3 vs 4.0 for Adaptive)
- Best reframing of the question
- Combined with intellectual honesty effectively

### Implications

| Finding | Implication |
|---------|-------------|
| Solo model beat multi-model | The value of multi-model may be diversity of perspectives, not synthesis quality |
| Top models tied for honesty | SOTA models are already well-trained on epistemic honesty |
| Actionability gap | Claude prioritizes nuance; GPT prioritizes concrete recommendations |
| Synthesis ceiling | There may be diminishing returns to meta-synthesis |

### Updated Recommendations

1. **For maximum quality on complex questions:** Use a single SOTA model with a comprehensive, well-crafted prompt. Don't overthink the process.

2. **When multi-model adds value:**
   - Initial scout phase still valuable for surfacing diverse perspectives
   - May help when no single model has all relevant training data
   - Provides "audit trail" of different viewpoints

3. **The v3 prompt is the best multi-model design tested:**
   - Problem reframing + toolkit + confidence separation + steelmanning
   - But consider if the overhead is worth it vs. solo model

4. **Consider matching approach to problem type:**
   - Factual/technical: Solo model likely sufficient
   - Value-laden/contested: Multi-model diversity may help
   - Novel/unprecedented: Multi-model + synthesis may reduce blind spots

---

## Files Generated

- `test002_baseline.txt` - Minds ask synthesis
- `test002_scouts/` - Individual model responses (5 files)
- `test002_scouts_combined.txt` - All scouts combined
- `test002_unstructured_v1.txt` - Unstructured v1 output
- `test002_unstructured_v2.txt` - Unstructured v2 output (with approach notes)
- `test002_adaptive_structured.txt` - Adaptive Structured output
- `test002_mckinsey_guided.txt` - McKinsey Guided output
- `test002_v3_hybrid.txt` - v3 Hybrid output
- `test002_gpt_solo.txt` - GPT-5.2 solo output
- `test002_opus_solo.txt` - Claude Opus solo output
- `test002_top3_synthesis.txt` - Top-3 Synthesis output
