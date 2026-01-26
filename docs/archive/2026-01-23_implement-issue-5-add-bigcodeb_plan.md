# Issue #5: BigCodeBench + Fail Set Workflow

## Overview

Add BigCodeBench benchmark support and create a "fail set" workflow for iterating on the hardest problems that SOTA models consistently fail.

## Decisions

Based on clarifying questions (using recommendations):
1. **Docker**: Keep Docker requirement - BigCodeBench needs tensorflow, scipy, and other libraries
2. **Hard subset**: Use official BigCodeBench-Hard (148 problems) as starting point

## Phase 1: Add BigCodeBench

### 1.1 Add benchmark to cli.py `_get_benchmark_task()`

```python
elif benchmark == "bigcodebench":
    from inspect_evals.bigcodebench import bigcodebench
    return bigcodebench()
elif benchmark == "bigcodebench_hard":
    from inspect_evals.bigcodebench import bigcodebench
    # BigCodeBench-Hard uses version="v0.1.2_hard" or subset filtering
    return bigcodebench(version="v0.1.2_hard")
```

### 1.2 Add to config.py DOCKER_REQUIRED set

BigCodeBench requires Docker for sandboxed execution with Python libraries.

```python
DOCKER_REQUIRED = {
    ...
    "bigcodebench",
    "bigcodebench_hard",
}
```

### 1.3 Test with baseline

```bash
socrates-eval run bigcodebench --solver baseline --samples 10
```

## Phase 2: Fail Set Workflow

### 2.1 Create `analyze-failures` command in cli.py

New command to extract failed sample IDs from evaluation runs.

```python
@cli.command()
@click.argument("run_ids", nargs=-1)
@click.option("--output", "-o", type=str, help="Output JSON file for fail set")
@click.option("--intersect", is_flag=True, help="Only include samples that failed in ALL runs")
def analyze_failures(run_ids, output, intersect):
    """Extract failed samples from evaluation runs."""
```

### 2.2 Implementation

1. Load episodes from each run
2. Extract sample IDs where `outcome.passed == False`
3. If `--intersect`: compute intersection across all runs
4. Output as JSON compatible with `--sample-ids`

### 2.3 Output format

```json
{
  "source_runs": ["run1", "run2"],
  "mode": "intersect",
  "sample_ids": [123, 456, 789]
}
```

## Phase 3: Fast Iteration Subsets

### 3.1 Create `eval_mini_bigcodebench.json`

Curated 20-problem subset from BigCodeBench-Hard for rapid iteration.

Selection criteria:
- From official BigCodeBench-Hard (148 problems)
- Diverse library coverage (numpy, pandas, scipy, etc.)
- Mix of difficulty levels within "hard"

### 3.2 SOTA Failure Analysis Workflow

Run multiple SOTA models and intersect their failures to find the "hardest" problems:

```bash
# Run SOTA models on BigCodeBench-Hard
socrates-eval run bigcodebench_hard --solver baseline --model anthropic/claude-opus-4-5-20251101 --samples 148
socrates-eval run bigcodebench_hard --solver baseline --model openai/gpt-4o --samples 148
socrates-eval run bigcodebench_hard --solver baseline --model google/gemini-2.0-flash --samples 148

# Find problems ALL SOTA models failed (the truly hard ones)
socrates-eval analyze-failures <claude_run> <gpt_run> <gemini_run> --intersect --output sota_fail_set.json

# Iterate on SOTA failures with experimental solver
socrates-eval run bigcodebench_hard --solver minds --sample-ids sota_fail_set.json
```

This creates a feedback loop:
1. Run SOTA models → identify failures
2. Focus iteration on failures → improve solver
3. Re-run on fail set → measure progress
4. Repeat

### 3.3 Document workflow

Add to README.md:

```bash
# Quick validation on hard subset
socrates-eval run bigcodebench --solver minds --sample-ids eval_mini_bigcodebench.json

# Create fail set from multiple runs
socrates-eval analyze-failures run1 run2 --intersect --output fail_set.json

# Iterate on failures
socrates-eval run bigcodebench --solver improved_minds --sample-ids fail_set.json
```

## File Changes

### New Files
- `eval_mini_bigcodebench.json` - Curated 20-problem hard subset

### Modified Files
- `eval/cli.py` - Add `bigcodebench`, `bigcodebench_hard` benchmarks; add `analyze-failures` command
- `eval/config.py` - Add benchmarks to DOCKER_REQUIRED set

## Execution Strategy

**Sequential execution** is the appropriate approach because:
1. Phase 1 (add benchmark) must complete before testing
2. Phase 2 (fail set) needs working benchmark to generate failures
3. Phase 3 (mini subset) needs understanding of dataset structure

**Parallel execution assessment**: While there are multiple files to edit (cli.py, config.py), they are tightly coupled:
- cli.py imports from config.py (BenchmarkRequirements)
- Both changes are small (~20 lines each)
- Testing requires both to be complete

**Decision**: Use sequential execution. The changes are interdependent and small enough that parallel agents would add coordination overhead without benefit. I will verify all agent output by reading the actual files, not trusting summaries.

## Testing Strategy

### Unit Tests
- `analyze-failures` command with mock episode data
- Intersection logic for multiple runs
- JSON output format validation

### Integration Tests
- Run BigCodeBench with `--samples 3` to verify Docker setup
- Verify fail set JSON works with `--sample-ids`

### Smoke Test
```bash
# Verify BigCodeBench runs
socrates-eval run bigcodebench --solver baseline --samples 5

# Verify analyze-failures works
socrates-eval analyze-failures <run_id> --output test_fail_set.json

# Verify fail set can be used
socrates-eval run bigcodebench --solver baseline --sample-ids test_fail_set.json
```

## Success Criteria

1. `socrates-eval run bigcodebench --samples 5` completes successfully
2. `socrates-eval run bigcodebench_hard --samples 5` completes successfully
3. `socrates-eval analyze-failures <run_id> --output fail_set.json` creates valid JSON
4. `socrates-eval analyze-failures <run1> <run2> --intersect` finds common failures
5. `socrates-eval run bigcodebench --sample-ids fail_set.json` uses the fail set
6. All tests pass with `pytest`
7. SOTA failure workflow documented in README
