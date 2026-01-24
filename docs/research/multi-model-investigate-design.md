# Multi-Model Investigate Mode Design

## Research Date: 2026-01-23

## Background: Why Debate Failed

### Empirical Results

Testing on a hard distributed consensus algorithm question:

| Mode | Score | Notes |
|------|-------|-------|
| minds (synthesis) | 0.82 | Independent parallel → synthesize |
| minds debate | 0.77 | Structured argumentation |
| minds debate --thorough | 0.76 | More rounds scored LOWER |
| GPT-5.2 solo | 0.61 | Incomplete coverage |
| Claude Opus 4.5 solo | 0.49 | Truncated/wrong approach |

**Key finding**: More debate rounds = worse results, not better.

### Why Debate Hurts Quality

From multi-model analysis:

1. **Forces "advocate mode" over truth-seeking**: Models optimize for winning arguments rather than accuracy, activating persuasion heuristics instead of natural error-correction loops

2. **More rounds = more entrenchment**: Early positions anchor reasoning; subsequent rounds become rationalization, not exploration

3. **Context/token pollution**: Debate overhead (framing, rebuttals, restating positions) crowds out substantive reasoning

4. **Overrides billion-dollar optimization**: AI companies spend billions fine-tuning reasoning. Imposing amateur "thinking structures" fights this optimization.

### What Actually Works (High-Performing Teams Analysis)

Elite human teams (surgery, fighter pilots, research labs):
- Standardize *interfaces and coordination*, not internal cognition
- Leverage *orthogonal detection surfaces* (different vantage points catch different errors)
- Don't tell experts how to think—add checklists, handoffs, and stop-conditions

**Core insight**: The multi-model benefit comes from **diverse independent perspectives + good synthesis**, not from adversarial interaction.

## The Investigate Mode Design

### Philosophy

> Your advantage is *information models can't generate alone* (another perspective's conclusion); your intervention should be *minimal in structure* but *effective at creating and surfacing genuine independence*.

### High-Value vs Low-Value Token Spend

| High Value | Low Value |
|------------|-----------|
| Verifiable outputs (code, math, constraints) | Subjective judgment deliberation |
| When models genuinely disagree | When models already agree |
| Focused critique on specific failure modes | Open-ended "find problems" |
| Independent generation before comparison | Asking model to check its own reasoning |

### Design: `minds investigate`

**Core pattern** (strong consensus from 5 models):

1. **Start with independent parallel queries** (preserves the 0.82 synthesis baseline)
2. **Detect disagreement structurally** (without models seeing each other's responses)
3. **Classify disagreement by type** (verifiable vs. judgment/subjective)
4. **Trigger focused verification only on verifiable disputes** (high ROI)
5. **Surface—don't resolve—subjective disagreements** (low ROI to debate these)
6. **Synthesize with an evidence ledger** showing what was verified vs. uncertain

### Implementation Spec

```
minds investigate "query" [--thorough] [--verify-only] [--budget N]

1. parallel_query(5_models, query + format_contract) → responses[]
2. analyze_disagreement(responses) → {consensus[], splits[], unique[]}
3. if no splits: return fast_synthesis(responses)
4. for each verifiable split (max 3):
     evidence = verify(claim, fresh_model_or_tool)
     update split with verdict
5. synthesize(responses, verdicts, unresolved_judgments)
6. output: answer + verification_report + tokens_used
```

### Phase Details

**Phase 1: Parallel Scouts**
- 5 models (Claude, GPT, Grok, Gemini, DeepSeek)
- Structured output: answer + key claims + confidence
- No cross-contamination (genuine independence)
- ~10-15k tokens

**Phase 2: Disagreement Detection**
- Cheap analyzer call (Haiku-class)
- Clusters responses into: consensus, splits, unique claims
- Classifies splits as verifiable vs. subjective
- ~1-2k tokens

**Phase 3: Conditional Verification**
- **No disagreement** → fast exit (standard synthesis)
- **Verifiable disputes** → verification probes (fresh models, narrow prompts, or code execution)
- **Judgment disputes** → surface both sides with "subjective" labeling
- Max 3 verifiable splits investigated
- ~0-15k tokens (only if disputes exist)

**Phase 4: Evidence-Tagged Synthesis**
- Final answer with tags: `[VERIFIED]`, `[CONSENSUS]`, `[JUDGMENT CALL]`, `[UNCERTAIN]`
- Brief verification report
- ~3k tokens

### Token Budget

| Phase | Tokens/Calls |
|-------|--------------|
| Parallel scouts | 5 models × ~2-3k = 10-15k |
| Disagreement detection | 1 cheap call ~1-2k |
| Verification probes | 0-9 calls (~10-15k) *only if disputes* |
| Final synthesis | 1 call ~3k |
| **Total** | **15-35k typical, <50k max** |

### Stop Conditions

- Hard caps: max 1-2 probe rounds, max ~10-20 calls
- Agreement threshold: ≥80% model agreement
- All verifiable claims resolved
- Budget exhausted

### Why This Should Beat 0.82

Preserves independence (source of 0.82) **plus** adds new information via verification **plus** focuses compute only where disagreement exists **plus** avoids debate's entrenchment failure mode.

## Output Format

```
╭─────────────── Investigation Results ───────────────╮
│ Answer: [Final synthesized answer]                  │
│                                                     │
│ Confidence: HIGH / MEDIUM / LOW                     │
│                                                     │
│ Verification Report:                                │
│ ✓ [VERIFIED] Claim X confirmed by code execution    │
│ ✓ [CONSENSUS] All 5 models agree on Y               │
│ ⚖ [JUDGMENT] Models split on Z (3-2), subjective    │
│ ? [UNCERTAIN] Claim W couldn't be verified          │
│                                                     │
│ Models: 5/5 | Probes: 2 | Tokens: 28k | Cost: $0.08 │
╰─────────────────────────────────────────────────────╯
```

---

## Unstructured Mode: `minds investigate --unstructured`

### Philosophy

The structured mode prescribes HOW to investigate. The unstructured mode trusts the synthesizer's judgment—it provides a clear objective, tools, and budget, then delegates the approach entirely.

> "AI companies spend billions on reasoning. Give the model a goal and resources, then get out of the way."

### Core Design (Strong Consensus)

The synthesizer receives:
1. The original question
2. Initial responses from 5 models (independent, parallel)
3. A budget (calls + tokens) to spend however it wants
4. High-level principles (not procedures)
5. Tools to query models, run code, search, verify

It does NOT receive:
- Prescribed phases or steps
- Required structure for investigation
- Rules about when to probe vs synthesize

### Objective & Principles

**Primary objective**: Produce the most accurate, well-supported answer possible.

**Principles** (guide judgment, don't prescribe method):
- **Truth over consensus**: 1 model with evidence can outweigh 4 without
- **Disagreement = signal**: Investigate it, don't ignore it
- **New information only**: Avoid "meetings" (re-processing without new data)
- **Uncertainty is valid**: "I don't know" is an acceptable answer
- **Diminishing returns**: Stop when you stop learning

### Tools to Expose

| Tool | Purpose |
|------|---------|
| `query_model(model, prompt)` | Query any available model with any prompt |
| `run_code(code)` | Execute Python for verification/calculation |
| `web_search(query)` | External fact-checking (if enabled) |
| `verify_claim(claim)` | Request targeted verification |
| `done(answer, confidence, reasoning)` | Declare investigation complete |

### Budget & Guardrails

**Hard limits**:
- Max calls: ~10-15
- Max tokens: ~50k
- Max wall time: ~2-5 minutes

**Soft guidance**:
- "Prefer fewer, targeted calls over many exploratory ones"
- Display remaining budget in every turn (encourages self-regulation)
- Require brief justification for each tool call (purpose + expected value)

**Stop conditions**:
- Synthesizer calls `done()`
- Budget exhausted
- Loop detection (3+ similar calls → inject warning or auto-stop)

### Synthesizer Prompt Template

```markdown
## Your Mission
Produce the most accurate answer to: {{question}}

## Initial Responses
{{5 model responses, labeled by model}}

## Budget
{{N}} calls remaining. {{M}} tokens remaining.

## Principles
- Truth over consensus
- Disagreement = investigate
- New info only (no meetings)
- Uncertainty is valid
- Stop when you stop learning

## Tools
- query_model(model, prompt) — ask any model anything
- run_code(code) — execute Python
- web_search(query) — search the web
- done(answer, confidence, reasoning) — finish

You decide what to do. When ready, call done().
```

### Example Scenarios

**Scenario 1: Clear consensus**
- Models agree, high confidence
- Synthesizer: "All 5 agree with consistent reasoning. No investigation needed."
- Action: Calls `done()` immediately
- Tokens used: ~15k (just initial responses + synthesis)

**Scenario 2: Factual dispute**
- 3 models say X, 2 say Y (verifiable claim)
- Synthesizer: "This is a factual question. Let me verify."
- Action: `run_code()` or `query_model()` with targeted verification prompt
- Tokens used: ~25k

**Scenario 3: Complex disagreement**
- Models disagree on approach AND have different assumptions
- Synthesizer: "I need to understand why they disagree first."
- Action: `query_model("claude", "Given these 5 responses, what's the crux of disagreement?")`
- Then targeted follow-ups based on analysis
- Tokens used: ~40k

**Scenario 4: Subjective question**
- Models give different but defensible answers
- Synthesizer: "This is fundamentally subjective. I'll present the spectrum."
- Action: Calls `done()` with multiple perspectives, no single answer
- Tokens used: ~18k

### Output Format

```
╭──────────────── Investigation Complete ─────────────────╮
│ Answer: [Synthesized answer]                            │
│                                                         │
│ Confidence: HIGH / MEDIUM / LOW                         │
│                                                         │
│ Key Evidence:                                           │
│ • [What was verified and how]                           │
│ • [What models agreed on]                               │
│                                                         │
│ Unresolved:                                             │
│ • [What remains uncertain and why]                      │
│                                                         │
│ Investigation Log:                                      │
│ 1. Analyzed 5 initial responses                         │
│ 2. query_model(gpt, "verify claim X") → confirmed       │
│ 3. run_code(calculation) → Y = 42                       │
│ 4. done()                                               │
│                                                         │
│ Budget: 3/10 calls | 28k/50k tokens | Cost: $0.09       │
╰─────────────────────────────────────────────────────────╯
```

### Structured vs Unstructured Comparison

| Aspect | --structured (default) | --unstructured |
|--------|------------------------|----------------|
| Investigation approach | Prescribed phases | Synthesizer decides |
| When to probe | Rules (verifiable splits) | Judgment |
| What to probe | Classified disagreements | Anything |
| Stop condition | Phases complete | Synthesizer says done |
| Predictability | High | Low |
| Token efficiency | Optimized for common cases | Variable |
| Best for | Most questions | Complex/novel questions |
| Risk | May miss edge cases | May waste tokens |

### Implementation Notes

- Use agentic loop: synthesizer can make tool calls until `done()` or budget exhausted
- Each tool call should return result + updated budget
- Loop detection: track call signatures, warn after 3 similar calls
- Consider "circuit breaker": inject guidance if synthesizer seems stuck (rather than hard-stop)

---

## Additional Ideas (Lower Confidence)

- **Unique claims handling**: Validate claims from only one model via a second model
- **Confidence weighting**: Weight synthesis by model confidence scores
- **Task-type critics**: Specialized critics (math checker, code runner) triggered by task classifier
- **User clarification**: Prompt user when models answer different questions (structural disagreement)
- **Role-based querying**: `query_model_as_role(model, role, prompt)` for orthogonal perspectives (adversary, domain expert, etc.)
- **Mini-debate tool**: `debate(model_a, model_b, question)` available as one tool option (not mandatory)

---

## Experiment Results & Learnings (2026-01-23)

### Test Results

| Mode | Score | Notes |
|------|-------|-------|
| Baseline (minds ask) | 2.85 | Aggregated without adding value |
| Structured | 3.85 | Missed key insight via classification error |
| **Unstructured** | **4.40** | Followed interesting thread to game theory insight |

### Unstructured's Weaknesses (Critical)

**We got lucky.** The 4.40 win masked significant risks:

1. **Higher variance / lower floor**: Structured had tighter, more predictable performance
2. **Completeness gaps**: Skipped "boring but necessary" checks
3. **Skill dependency**: Success required good judgment - not a system property
4. **Rabbit hole vulnerability**: No defense against fascinating-but-irrelevant tangents
5. **Confirmation bias risk**: Freedom to follow intuition = freedom to cherry-pick
6. **Stopping ambiguity**: "Felt done" is not reliable

**Risks we got lucky on:**
- Problem rewarded exploration (biased toward unstructured's strengths)
- Initial hunches happened to be productive
- No adversarial red herrings
- Clear "done" signals existed

### Key Principle

> "Rules help in well-defined solution spaces; hurt during frame discovery."
> — Universal consensus

Structured failed because it tried to classify before understanding. "Verifiable" is often an OUTPUT of investigation, not an input.

### The Recommended Design: "Adaptive Investigator"

**One system, not two modes.** Absorb structured's benefits into improved unstructured.

**Opening (Unstructured)**
```
1. Restate problem in own words
2. Assess frame clarity: Low/Med/High
3. Start with most informative single action
4. Follow the signal
```

**Running Discipline (Lightweight checkpoints every 3-4 calls)**
```
- What I learned (1 sentence)
- Current hypothesis (1 sentence)
- What would change my mind (1 sentence)
```

**Shift Point (Add structure when hypothesis solidifies)**
```
- STOP exploring
- Verify directly
- Check one alternative (the "boring" one)
- Trace mechanism: cause → symptom
```

**Before Concluding (Mandatory)**
```
1. State strongest alternative explanation
2. Explain why your conclusion beats it
3. Note confidence and remaining uncertainty
```

**Rabbit Hole Prevention**
```
- 5-call budget per path; explicit decision to continue
- 10-call total checkpoint: summarize or ask clarifying questions
- Track relevance to original question
```

**Non-Arbitrary Stopping (stop when ANY):**
1. Complete causal chain traced (trigger → mechanism → symptom)
2. Found specific fix
3. Last 2-3 explorations yielded no new information
4. Actively ruled out main alternatives

### Guardrails That Preserve Judgment

| Guardrail | Purpose |
|-----------|---------|
| **Steel man alternative** | Before concluding, articulate strongest competing hypothesis |
| **Disconfirmation requirement** | Actively seek evidence that would disprove your theory |
| **Evidence tagging** | Mark claims as Observed / Derived / Assumed / Speculative |
| **Confidence calibration** | State confidence level + what would change it |

### When to Keep Structured Elements

- Well-defined, routine problems (audits, known incident types)
- Compliance/auditability requirements
- Novice users who need scaffolding
- Fallback when unstructured confidence is low

### The Formula

> **Unstructured's flexibility + Structured's insurance**, unified through:
> 1. Explicit confidence tracking
> 2. Mandatory alternative consideration
> 3. Information-theoretic stopping rules
> 4. Adaptive structure that increases as the problem clarifies

This makes unstructured's implicit judgment **explicit enough to be teachable and consistent**, without making it **rigid enough to hurt discovery**.

---

## References

- test_hard_question.py results (2026-01-23)
- Multi-model synthesis on team performance (5 models)
- Multi-model synthesis on investigate design (5 models)
- Experiment: experiments/investigate_test_001.md
