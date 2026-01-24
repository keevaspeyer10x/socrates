# Experiments Framework

Tools and scripts for running autonomous LLM verification experiments.

## Quick Start

```bash
# Run experiments (survives crashes, saves checkpoints)
python3 experiments/runner.py

# Monitor progress
tail -f experiments/experiment.log

# Resume after interruption
python3 experiments/runner.py  # Automatically resumes from checkpoint

# Analyze results only
python3 experiments/runner.py --analyze
```

## Running in Background (Survives Session Disconnection)

```bash
# Start in background with nohup
nohup python3 experiments/runner.py > /tmp/runner_output.log 2>&1 &
echo "Started with PID: $!"

# Check if running
ps aux | grep runner.py | grep -v grep

# Monitor progress
tail -f experiments/experiment.log

# Quick status check
python3 -c "import json; d=json.load(open('experiments/experiment_state.json')); print(f'Done: {sum(1 for r in d[\"runs\"].values() if r[\"generation\"][\"done\"])}/24')"

# Kill if needed
pkill -f "runner.py"
```

## Architecture

### Crash Recovery

The runner uses a checkpoint-based architecture:

1. **State file** (`experiment_state.json`) - Updated after each run
2. **Atomic writes** - Write to `.tmp`, then `os.replace()` for crash safety
3. **Resume logic** - On restart, skips completed runs automatically

```python
# Simplified checkpoint flow
for run in all_runs:
    if run.generation.done:
        continue  # Skip completed

    response = call_minds(...)
    run.generation = {"done": True, "response": response}
    save_state()  # Checkpoint after each run
```

### Cost Tracking

- Parses `Total: XXXms | Cost: $X.XX | Models: X/X` from minds output
- Budget limit enforced before each API call
- Single-model calls don't report cost (limitation of CLI output)

### Method Implementations

| Method | Implementation | API Calls |
|--------|----------------|-----------|
| baseline | `minds ask --rigor <question>` | 1 (5 models) |
| self_consistency_k5 | Generate 5 attempts → Synthesize | 2 |
| self_consistency_k10 | Generate 10 attempts → Synthesize | 2 |
| generic_critique | Generate → Critique → Revise | 3 |
| cove | Draft → Verification Qs → Answer & Revise | 3 |
| reasoning_verification | Generate → Check logic → Revise | 3 |

## Files

| File | Purpose |
|------|---------|
| `runner.py` | Main experiment runner |
| `experiment_state.json` | Checkpoint state (survives crashes) |
| `experiment.log` | Human-readable progress log |
| `experiment_results.json` | Final analysis with scores |
| `next_experiments.md` | Prioritized experiment agenda |
| `EXPERIMENT_STATUS.md` | Quick monitoring reference |

## Extending

### Adding New Methods

```python
def run_my_method(question: str) -> tuple[str, float, list]:
    """My custom verification method."""
    intermediates = []
    total_cost = 0.0

    # Step 1: Initial generation
    response, cost = call_single_model(question, model="claude")
    intermediates.append({"step": "initial", "response": response})
    total_cost += cost

    # Step 2: Your verification logic
    # ...

    return final_response, total_cost, intermediates

# Register in METHOD_RUNNERS dict
METHOD_RUNNERS["my_method"] = run_my_method
```

### Adding New Questions

```python
QUESTIONS["my_question"] = {
    "type": "reasoning",  # or "factual"
    "question": "Your question text here",
    "notes": "Why this tests what we want"
}
```

### Changing Models

```python
# For single-model calls
response, cost = call_single_model(prompt, model="gpt")  # or "claude", "gemini", etc.

# For multi-model calls
response, cost = call_minds(prompt, rigor=True)  # Uses 5 models
```

## Known Limitations

1. **Cost tracking incomplete** - Single-model calls show $0 (CLI doesn't report)
2. **Cost parsing fragile** - May match dollar amounts in responses (fixed with specific regex)
3. **LLM-as-judge biases** - Verbosity preference, self-preference when Claude judges Claude
4. **No ground truth** - Relies on LLM judgment, not objective correctness

## Lessons Learned

### Experiment Design
- **N=4 questions is too small** - Need 30-50+ for statistical power
- **Same model for all methods** - Avoid confounds from model differences
- **Include hard questions** - Scores of 7-9 don't differentiate methods
- **Multiple judges** - Reduces single-judge bias

### Methodology
- **Pre-register questions** - Avoid cherry-picking after seeing results
- **Track variance** - High variance (range 4) suggests unreliable method
- **Measure false corrections** - When verification makes correct answers wrong

## Related

- GitHub Issue #8: Full experiment tracking and roadmap
- `next_experiments.md`: Prioritized list of experiments to run
- Huang et al. (2023): "LLMs Cannot Self-Correct Reasoning Yet" - critical background
