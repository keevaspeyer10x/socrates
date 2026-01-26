# Investigate v3 Prompt (Hybrid)

## Design Philosophy
Combines the best elements from:
- **Adaptive Structured**: Confidence separation + mandatory steelmanning
- **McKinsey Guided**: Problem reframing discipline + "So What?" test
- **Unstructured v2**: Empowerment + optional toolkit + self-annotation

Key principles:
- Empower, don't direct
- Information > rules
- Reframing is high-leverage
- Intellectual honesty > raw depth

---

## The Prompt (~200 words)

```
You're investigating a complex question. You have insights from 5 diverse perspectives below.

**Before diving in:**
- Is this the RIGHT question? What's the REAL problem here? (Clients often ask the wrong question.)
- What do we actually KNOW vs ASSUME?

**As you investigate:**
Use whatever approach feels right. Some find these helpful:
- *Disaggregation:* Big questions hide smaller ones
- *5 Whys:* Surface answers hide deeper causes
- *First Principles:* Why does that heuristic exist? What's underneath?
- *80/20:* What's the ONE thing that would change the answer?
- *So What?:* Does this insight imply action, or just interesting?

Note when you're confident vs when evidence is contested—this adds real value.

**Before concluding:**
- What's the strongest alternative to your view? (Steelman it.)
- Does your synthesis beat it, or is there genuine tension?

**Output:** Your synthesis of what's actually going on. Take a position but be honest about uncertainty. Multiple valid frames are fine—don't force false convergence.

If you use any approach explicitly, note it briefly: [APPROACH: ...]

**Scout perspectives follow. The question is: [INSERT]**
```

---

## Key Differences from Previous Approaches

| Element | v1 | v2 | Adaptive | McKinsey | v3 (Hybrid) |
|---------|----|----|----------|----------|-------------|
| Problem reframing | Implicit | Implicit | Explore phase | Core principle | Explicit prompt |
| Toolkit | None | Optional + annotate | None | Principles | Optional + annotate |
| Steelmanning | Implicit | Optional tool | Required | Implicit | Explicit requirement |
| Confidence separation | None | Implicit | Required | None | Encouraged |
| "So What?" | None | Tool | None | Core principle | Tool |
| Output format | Free | Free + notes | Structured | Free + position | Free + notes |

## Expected Strengths
- Reframing discipline from McKinsey (highest single-insight value)
- Confidence separation from Adaptive (won intellectual honesty)
- Toolkit availability from v2 (used and helpful)
- Empowerment framing (respects model reasoning)

## Expected Weaknesses
- Longer prompt (~200 words vs ~175 for v2)
- Multiple "before X" sections might feel prescriptive
- Steelman requirement might cause hedging (as seen in Adaptive)
