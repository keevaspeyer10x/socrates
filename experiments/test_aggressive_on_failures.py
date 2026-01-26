#!/usr/bin/env python3
"""Test aggressive devil's advocate on the 3 samples that failed at 94%."""

import subprocess
import json
from pathlib import Path

# The 3 samples that failed in the 94% run
FAILED_SAMPLES = [
    "rec7qmSnbud4FHSqL",  # Stellar abundances - all chose D, correct is C
    "recCJJOeBGERaHYax",  # Organic stereo - models split, synthesis chose A, correct is D
    "recDDxpS9s8cwkqfq",  # Dye absorption - all chose A, correct is C
]

def run_test(mode: str):
    """Run eval on just the 3 failed samples."""
    # Create temp sample file
    sample_file = Path("experiments/failed_sample_ids.json")
    sample_file.write_text(json.dumps(FAILED_SAMPLES))

    cmd = [
        "socrates-eval", "run", "gpqa",
        "--solver", "minds",
        "--model", "anthropic/claude-opus-4-5-20251101",
        "--solver-mode", mode,
        "--sample-ids", str(sample_file)
    ]

    print(f"\n{'='*60}")
    print(f"Testing mode: {mode}")
    print(f"{'='*60}")

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    return result.returncode

if __name__ == "__main__":
    import sys

    # Test both modes
    modes = ["critique_challenge", "critique_aggressive"]

    if len(sys.argv) > 1:
        modes = [sys.argv[1]]

    for mode in modes:
        run_test(mode)
