# Plan: Issue #4 - HumanEval and MBPP Evals Setup

## Summary

Add HumanEval and MBPP benchmarks to the Socrates evaluation framework for rapid coding agent iteration with fast feedback loops.

## Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Docker requirement | No (NO_DOCKER) | Simpler setup, faster iteration |
| MBPP temperature | 0.5 | Matches inspect_evals default |
| Mini-validation subset | Yes, 20 problems each | Consistent comparison across runs |
| HumanEval epochs | 5 (standard), 1 (fast variant) | User requested fast variant for rapid iteration |

## Implementation Tasks

### 1. Update config.py - Add MBPP to NO_DOCKER set
- File: `eval/config.py`
- Change: Add `"mbpp"` to `NO_DOCKER` set (humaneval already present)

### 2. Update cli.py - Add benchmark tasks
- File: `eval/cli.py`
- Function: `_get_benchmark_task()`
- Add cases for:
  - `humaneval` - 5 epochs (standard)
  - `humaneval_fast` - 1 epoch (rapid iteration)
  - `mbpp` - temperature 0.5

### 3. Create mini-validation sample files
- File: `eval_mini_humaneval.json` - 20 curated HumanEval problem IDs
- File: `eval_mini_mbpp.json` - 20 curated MBPP problem IDs

### 4. Update documentation
- File: `README.md` - Add HumanEval/MBPP to quick start examples
- Add example commands for mini-validation runs

### 5. Add tests
- File: `tests/test_cli.py` - Test new benchmark task creation

## Execution Strategy

**Sequential execution** - Tasks are interdependent (config changes needed before CLI, CLI before docs).

Order: config.py -> cli.py -> mini samples -> README -> tests

## Target Quick Start

```bash
# Full HumanEval run (5 epochs, standard benchmarking)
socrates-eval run humaneval --solver baseline --model anthropic/claude-sonnet-4-20250514

# Fast HumanEval iteration (1 epoch)
socrates-eval run humaneval_fast --solver baseline --samples 20

# MBPP run
socrates-eval run mbpp --solver baseline --samples 20

# Mini-validation (near-instant feedback)
socrates-eval run humaneval_fast --solver baseline --sample-ids eval_mini_humaneval.json
```

## Files to Modify

1. `eval/config.py` - Add mbpp to NO_DOCKER
2. `eval/cli.py` - Add humaneval, humaneval_fast, mbpp to _get_benchmark_task()
3. `README.md` - Update documentation
4. `tests/test_cli.py` - Add tests (if exists, otherwise create minimal test)

## Files to Create

1. `eval_mini_humaneval.json` - 20 sample IDs for quick validation
2. `eval_mini_mbpp.json` - 20 sample IDs for quick validation
