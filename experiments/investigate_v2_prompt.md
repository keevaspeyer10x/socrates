# Unstructured v2 Prompt

## Design Principles
- Empower, don't direct
- Principles as toolkit, not checklist
- Explicit permission to ignore
- Self-annotation for learning

---

## The Prompt (~175 words)

```
You're investigating a complex question. Scouts have mapped initial terrain—now you go deeper.

Your job: Follow what's interesting. Push on weak reasoning. Find the structure underneath obvious answers. You have full autonomy over method.

**Optional tools (use what helps, ignore what doesn't):**
- *Disaggregation:* Big questions hide smaller ones. What are the actual sub-questions?
- *5 Whys:* Surface answers hide deeper causes. Keep asking "why is that true?"
- *First Principles:* What do we actually know vs. assume? Why does that heuristic exist?
- *Prioritization:* Not all threads matter equally. What's the crux?
- *Steelman:* What's the strongest version of the opposing view?
- *So What?:* Does this insight imply action, or is it just interesting?

As you work, briefly note in [APPROACH NOTE: ...] what you tried and whether it helped—we're learning too.
Example: [APPROACH NOTE: Used disaggregation—revealed key sub-question]
Example: [APPROACH NOTE: Tried 5 whys, hit bedrock after 2—moved on]

**Output:** Your synthesis of what's actually going on, with honest assessment of confidence and remaining uncertainty. Multiple valid frames are acceptable—don't force false convergence.

**Scout reports follow. The question is: [INSERT]**
```

---

## Tracking Template

After investigation, we'll extract from logs:

| Principle | Used? | Self-reported helpfulness | Evaluator assessment |
|-----------|-------|---------------------------|---------------------|
| Disaggregation | | | |
| 5 Whys | | | |
| First Principles | | | |
| Prioritization | | | |
| Steelman | | | |
| So What? | | | |

Plus: "What principle would have helped but wasn't used?"

---

## Differences from v1

| Aspect | v1 | v2 |
|--------|----|----|
| Principles | Implicit | Explicit toolkit (optional) |
| Tracking | None | Self-annotation |
| False convergence | Not addressed | "Multiple frames acceptable" |
| User context | Not included | Can add decision intent/stakes |
