# Socrates - AI Evaluation Framework

## Overview
Socrates is a framework for evaluating AI model performance on coding benchmarks using inspect_ai. It includes:
- Multi-solver support (baseline, minds multi-model)
- LLM-as-Judge evaluation (no ground truth needed)
- Learning system for extracting lessons from failures
- Fail set workflow for iterating on hard problems

## Key Commands

```bash
# Run evaluation
socrates-eval run <benchmark> --solver <solver> --model <model>

# Available benchmarks: gsm8k, mmlu, humaneval, humaneval_fast, mbpp, bigcodebench, bigcodebench_hard

# Analyze results
socrates-eval results <run_id>
socrates-eval analyze <run_id>
socrates-eval compare <run_a> <run_b>

# Learning system
socrates-eval learn <run_id> [--llm]
socrates-eval lessons [--candidates] [--approve <id>]

# Fail set workflow
socrates-eval analyze-failures <run_id> --output fail_set.json
socrates-eval analyze-failures run1 run2 --intersect --output hard_failures.json
socrates-eval run <benchmark> --sample-ids fail_set.json
```

## Test Scripts

### test_hard_question.py
Compares minds modes on challenging questions with automatic clarification retry.

**Features:**
- Parallel execution of multiple modes (minds synthesis, debate, individual models)
- **Automatic clarification**: If a model misunderstands (e.g., writes code when analysis expected), retries with clarification
- LLM-as-Judge evaluation
- Caches responses to avoid re-running

**Usage:**
```bash
python test_hard_question.py           # Fresh run with clarification retry
python test_hard_question.py --cache   # Re-evaluate cached responses
```

**Output:** `hard_question_responses.json`, `hard_question_results.json`

### test_individual_models.py
Tests each SOTA model individually on the same question.

### test_minds_judge.py
Compares minds modes (default, fast, cheap) using LLM-as-Judge.

## Architecture

```
eval/
  cli.py          # Main CLI (socrates-eval)
  config.py       # API keys, benchmark requirements
  state.py        # Run state tracking
  adapters/       # Inspect AI integration
  solvers/        # Solver implementations (baseline, minds)
  judge/          # LLM-as-Judge system
  learning.py     # Lesson extraction
```

## Notes
- BigCodeBench requires Docker
- HumanEval/MBPP use local sandbox (no Docker)
- minds CLI must be installed separately for multi-model queries
