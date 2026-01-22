#!/usr/bin/env python3
"""
Phase 0 Spike: Explore Inspect AI log format and structure
Run with: source .venv/bin/activate && python phase0_spike.py
"""

import os
import json
from pathlib import Path

# Ensure we have the API key
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set")
    print("Please run: export ANTHROPIC_API_KEY=your-key")
    exit(1)

from inspect_ai import eval as inspect_eval
from inspect_ai.log import read_eval_log
from inspect_evals.gsm8k import gsm8k

def main():
    print("=" * 60)
    print("Phase 0 Spike: Understanding Inspect AI")
    print("=" * 60)

    # Create a minimal GSM8K task (2 samples, no fewshot)
    print("\n1. Creating task: GSM8K with 2 samples...")
    task = gsm8k(fewshot=0)

    # Create log directory
    log_dir = Path("./phase0_logs")
    log_dir.mkdir(exist_ok=True)

    # Run evaluation
    print("\n2. Running evaluation with Claude Sonnet...")
    print("   (This will call the Anthropic API)")

    results = inspect_eval(
        task,
        model="anthropic/claude-sonnet-4-20250514",
        limit=2,  # Only 2 samples
        log_dir=str(log_dir),
    )

    print(f"\n3. Evaluation complete!")
    print(f"   Results: {results}")

    # Read the log
    print("\n4. Reading evaluation log...")
    log_files = list(log_dir.glob("*.eval"))
    if log_files:
        log_file = log_files[0]
        print(f"   Log file: {log_file}")

        eval_log = read_eval_log(log_file)

        print("\n5. Log structure analysis:")
        print(f"   - Model: {eval_log.eval.model}")
        print(f"   - Task: {eval_log.eval.task}")
        print(f"   - Samples: {len(eval_log.samples)}")

        print("\n6. Sample details:")
        for i, sample in enumerate(eval_log.samples):
            print(f"\n   Sample {i+1}:")
            print(f"   - ID: {sample.id}")
            print(f"   - Input: {str(sample.input)[:100]}...")
            print(f"   - Target: {sample.target}")
            print(f"   - Output: {sample.output.completion[:100] if sample.output else 'None'}...")
            print(f"   - Scores: {sample.scores}")
            print(f"   - Messages count: {len(sample.messages) if sample.messages else 0}")

            # Look at message structure
            if sample.messages:
                print(f"   - Message types: {[m.role for m in sample.messages]}")

        # Save log structure to JSON for analysis
        print("\n7. Saving sample to JSON for analysis...")
        if eval_log.samples:
            sample = eval_log.samples[0]
            sample_dict = {
                "id": sample.id,
                "input": str(sample.input),
                "target": sample.target,
                "output": sample.output.completion if sample.output else None,
                "scores": {k: v.value for k, v in (sample.scores or {}).items()},
                "messages": [
                    {"role": m.role, "content": m.content[:200] if m.content else None}
                    for m in (sample.messages or [])
                ],
            }
            with open(log_dir / "sample_structure.json", "w") as f:
                json.dump(sample_dict, f, indent=2)
            print(f"   Saved to: {log_dir}/sample_structure.json")

    print("\n" + "=" * 60)
    print("Phase 0 Spike Complete!")
    print("=" * 60)
    print("\nKey findings:")
    print("- Inspect logs contain: model, task, samples")
    print("- Each sample has: input, target, output, scores, messages")
    print("- Messages contain the full conversation history")
    print("- Scores contain the evaluation results")
    print("\nNext: Run with SWE-bench (requires Docker)")

if __name__ == "__main__":
    main()
