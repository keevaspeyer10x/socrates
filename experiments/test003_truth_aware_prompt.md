# Truth-Aware Prompt Design

## Hypothesis
If models know upfront they'll be adversarially tested, they can build in epistemic rigor from the start rather than retrofitting it.

## The Prompt

```
QUESTION: Why do US mass transit systems struggle financially compared to peer countries, and what should be done about it?

EVALUATION CRITERIA (you will be scored on ALL of these):

1. DEPTH OF ANALYSIS (0-10)
   - Identify root causes with evidence
   - Consider multiple perspectives
   - Show nuanced understanding

2. ACTIONABILITY (0-10)
   - Specific, implementable recommendations
   - Clear prioritization
   - Address political/practical feasibility

3. EPISTEMIC CALIBRATION (0-10) - CRITICAL
   Your claims will be adversarially challenged. For each claim you make:
   - A fact-checker will ask: "What evidence would falsify this?"
   - Claims using absolute language (cannot, will not, always, never, useless) are easy to falsify with single counterexamples
   - Quantitative claims without sources/methodology will be challenged
   - Primacy claims ("the root cause", "the original sin") require proof of causality

   TO SCORE WELL:
   - Use comparative language where appropriate ("more likely", "tends to", "harder")
   - Distinguish well-supported claims from plausible-but-uncertain ones
   - For numbers, specify scope and acknowledge uncertainty
   - Multi-causal framings survive better than single-cause explanations
   - Be decisive where evidence supports it; hedge only where genuinely uncertain

4. ADVERSARIAL SURVIVAL
   After you respond, each key claim will be challenged:
   - "What would prove this wrong?"
   - "What's the strongest counterargument?"
   - "Is confidence level appropriate?"

   Claims that SURVIVE: well-supported, appropriately confident
   Claims that PARTIALLY SURVIVE: direction correct but overconfident
   Claims that FALL: unsupported, wrong, or falsified by counterexamples

IMPORTANT: Do not over-hedge. Maintain decisive recommendations. The goal is CALIBRATED confidence, not maximum hedging. A well-supported claim stated confidently scores better than a hedge-everything approach.

Now provide your analysis.
```

## What This Tests
- Can models optimize for both style AND substance when told the criteria upfront?
- Does explicit adversarial warning improve calibration without killing decisiveness?
- Is "built-in quality" better than "retrofitted quality"?
