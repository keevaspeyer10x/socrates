# Inspect Eval Integration Plan for Socrates

## Goal
Build an evaluation harness with pluggable solvers to compare baseline (single model) vs minds (multi-model) vs custom agents on standard benchmarks. Enable rapid iteration and validation of AI agent designs.

## Phase 0 Findings (Completed)

Key discoveries from spike:
- **Inspect Log Structure**: `EvalLog` → `EvalSample` → `events` (ToolEvent/ModelEvent)
- **Docker Required**: SWE-bench and GAIA need Docker for sandboxed execution
- **Non-Docker Benchmarks**: GSM8K, MMLU, HumanEval work without Docker
- **API Keys**: Must align with Inspect's env var names (`ANTHROPIC_API_KEY`, etc.)

## Core Architecture: Pluggable Solvers

```
┌─────────────────────────────────────────────────────────────┐
│                    INSPECT EVAL HARNESS                      │
├─────────────────────────────────────────────────────────────┤
│  Dataset: SWE-bench / GAIA / GSM8K / MMLU                   │
├─────────────────────────────────────────────────────────────┤
│                      SOLVER (pluggable)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ baseline │  │  minds   │  │ agent-v1 │  │ agent-v2 │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
├─────────────────────────────────────────────────────────────┤
│  Scorer: Same for all (did it solve the problem?)           │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure (Updated from Phase 0)

```
socrates/
├── .claude/commands/
│   └── inspect-eval.md          # CLI command spec
├── eval/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   ├── config.py                 # API key management
│   ├── preflight.py              # Environment validation
│   ├── state.py                  # State machine, data models
│   ├── runner.py                 # Orchestrates eval runs
│   ├── compare.py                # Cross-run comparison + stats
│   ├── adapters/
│   │   ├── __init__.py
│   │   └── inspect_adapter.py    # Event-first extraction
│   └── solvers/
│       ├── __init__.py           # Solver base class + registry
│       ├── baseline.py           # Single model (wraps Inspect)
│       └── minds.py              # Multi-model collaboration
├── .env.example                  # API key template
├── .eval_state.json              # Current state
├── eval_logs/
│   └── runs/{run_id}/
│       ├── config.json
│       ├── summary.json
│       └── episodes/
└── pyproject.toml
```

## Implementation Phases

### Phase 1: Core Infrastructure (Current)

#### 1.1 Config & Preflight
- [ ] Create `eval/config.py` - API key loading from .env
- [ ] Create `eval/preflight.py` - Docker/key/Python validation
- [ ] Create `.env.example` template
- [ ] Add benchmark requirements mapping (Docker vs no-Docker)

#### 1.2 Core Data Models
- [ ] Create `eval/state.py` with:
  - `EvalState` - workflow state machine
  - `Episode` - 4-tuple format (context, traces, action, outcome)
  - `RunConfig` - solver, model, benchmark, samples
  - `RunSummary` - results with confidence intervals

#### 1.3 Inspect Adapter (Event-First)
- [ ] Create `eval/adapters/inspect_adapter.py`
- [ ] Extract from `ToolEvent` → action traces
- [ ] Extract from `ModelEvent` → rationale
- [ ] Map `sample.scores` → outcome with failure taxonomy
- [ ] Map `sample.model_usage` → cost

#### 1.4 Baseline Solver
- [ ] Create `eval/solvers/__init__.py` - base class + registry
- [ ] Create `eval/solvers/baseline.py` - wraps Inspect generate()

#### 1.5 CLI Foundation
- [ ] Create `eval/cli.py` with Click
- [ ] Implement `socrates-eval preflight` - environment check
- [ ] Implement `socrates-eval run <benchmark> --solver <name>`
- [ ] Implement `socrates-eval status`
- [ ] Implement `socrates-eval results [run_id]`

#### 1.6 Smoke Test
- [ ] Run GSM8K with 2-3 samples (no Docker needed)
- [ ] Verify episode extraction works
- [ ] Validate cost tracking

### Phase 2: Minds Solver
- [ ] Implement `MindsSolver` using Inspect's `get_model()`
- [ ] Add per-provider rate limiting
- [ ] Test on GSM8K first (no Docker)

### Phase 3: Comparison & Analysis
- [ ] Implement statistical metrics (Wilson CI, McNemar test)
- [ ] Add failure taxonomy classification
- [ ] Implement `compare` and `analyze` CLI commands

### Phase 4: Learning Pipeline
- [ ] Episode logging with observable traces
- [ ] Lesson extraction with structured format
- [ ] Human review CLI flow

### Phase 5: Custom Solver Support
- [ ] Solver registration from external files
- [ ] Template for custom agents

## Benchmark Requirements

| Benchmark | Docker | API Keys | Notes |
|-----------|--------|----------|-------|
| GSM8K | No | Anthropic/OpenAI | Math word problems, good for smoke tests |
| MMLU | No | Anthropic/OpenAI | Multiple choice, fast |
| HumanEval | No* | Anthropic/OpenAI | *Local Python exec |
| SWE-bench | **Yes** | Anthropic/OpenAI | Full sandbox required |
| GAIA | **Yes** | Anthropic/OpenAI | Web browsing sandbox |

## API Key Configuration

```bash
# .env.example
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
XAI_API_KEY=...
```

## Episode Format (4-Tuple + Traces)

```json
{
  "sample_id": "gsm8k_42",
  "context": {
    "input": "Problem statement...",
    "target": "Expected answer"
  },
  "traces": [
    {"type": "model", "content": "Let me think...", "tokens": 150},
    {"type": "tool", "function": "calculator", "args": {}, "result": "42"}
  ],
  "action": {
    "output": "The answer is 42",
    "tool_calls_count": 1
  },
  "outcome": {
    "passed": true,
    "score": 1.0,
    "failure_mode": null
  },
  "cost": {"input_tokens": 500, "output_tokens": 200, "usd": 0.01}
}
```

## Preflight Command Output

```
$ socrates-eval preflight

Socrates Evaluation Framework - Preflight Check
================================================

Python:     ✓ 3.12.0 (required: 3.11+)
Inspect AI: ✓ 0.3.163

API Keys:
  ANTHROPIC_API_KEY: ✓ configured
  OPENAI_API_KEY:    ✓ configured
  GOOGLE_API_KEY:    ✗ missing

Docker:     ✗ not available
  → SWE-bench and GAIA benchmarks will be unavailable
  → GSM8K, MMLU, HumanEval will work

Ready for: gsm8k, mmlu, humaneval
Blocked:   swe_bench, gaia (requires Docker)
```

## Verification

1. `socrates-eval preflight` passes
2. `socrates-eval run gsm8k --solver baseline --samples 3` completes
3. `socrates-eval results` shows episode data with cost
4. Episodes contain traces from ToolEvent/ModelEvent
