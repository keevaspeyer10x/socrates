# Adaptive Structured Approach

## Design Philosophy
Captures our best structured ideas:
- Explore FIRST (frame discovery), THEN converge
- "Shift point" - add structure only when hypothesis solidifies
- Mandatory steelman before concluding
- Multiple frames as valid output
- Find the "crux" - what evidence would change minds?

---

## The Prompt

```
You're investigating a complex question. You have scout reports from 5 models providing diverse perspectives.

**Phase 1: EXPLORE (required)**
Your first job is frame discovery. Don't rush to answers.
- What are the different WAYS to think about this problem?
- What frames/lenses do the scouts use? What's missing?
- Where do they genuinely disagree vs. talk past each other?

**Phase 2: FIND THE CRUX**
Once you've mapped the frames:
- What's the core disagreement or tension?
- What evidence or analysis would actually distinguish between frames?
- What do we KNOW vs. ASSUME?

**Phase 3: GO DEEP (your choice where)**
Pick the most promising thread(s) and investigate:
- Follow the reasoning. Where does it break down?
- Apply 5 whys if helpful. What's underneath?
- What would change your mind?

**Phase 4: SYNTHESIZE (required)**
Before concluding:
- State the strongest alternative to your view (steelman)
- Explain why your synthesis beats it, OR acknowledge genuine tension
- Be honest about confidence and uncertainty

**Output format:**
- Frames identified (2-4)
- The crux (what the real disagreement is about)
- Your synthesis (may include multiple valid positions)
- Key uncertainties and what would resolve them

**Scout reports follow. The question is: [INSERT]**
```

---

## Key Differences from Pure Unstructured

| Aspect | Unstructured | Adaptive Structured |
|--------|--------------|---------------------|
| Frame discovery | Implicit | Explicit required phase |
| Finding crux | May happen | Required before going deep |
| Steelman | Optional tool | Mandatory before concluding |
| Output format | Free | Light structure (frames, crux, synthesis) |
| Going deep | Full autonomy | After exploration phase |
