# Phase 2-3 Implementation Plan: MindsSolver and Statistical Analysis

## Overview

Implement Phase 2 (MindsSolver) and Phase 3 (Statistical Comparison) of the Socrates evaluation framework as defined in Issue #3.

## Decisions Made

Based on user input:
1. **Models**: Use top models from multiminds including DeepSeek (5 models total):
   - Claude Opus 4.5 (`claude-opus-4-5`)
   - Gemini 3 Pro (`gemini-3-pro-preview`)
   - GPT-5.2 (`gpt-5.2`)
   - Grok 4.1 (`x-ai/grok-4.1-fast`)
   - DeepSeek V3.2 (`deepseek/deepseek-v3.2`)
2. **Synthesis**: Claude as synthesizer (given Inspect/Claude eval context)
3. **Rate Limiting**: Token bucket with configurable RPM per provider
4. **Statistical Tests**: Both Wilson CI and McNemar test

## Phase 2: MindsSolver Implementation

### 2.1 Create `eval/solvers/minds.py`

```python
class MindsSolver(Solver):
    """Multi-model collaboration solver using top models."""

    def __init__(
        self,
        models: list[str] = DEFAULT_MODELS,
        synthesizer_model: str = "anthropic/claude-opus-4-5-20251101",
        rate_limits: dict[str, int] = DEFAULT_RATE_LIMITS,
    ):
        ...

    async def solve(self, state, generate) -> TaskState:
        # 1. Query all models in parallel (with rate limiting)
        # 2. Collect responses
        # 3. Synthesize final answer using Claude
        # 4. Return updated state
```

### 2.2 Rate Limiting (`eval/rate_limiter.py`)

```python
class TokenBucketRateLimiter:
    """Per-provider rate limiting with token bucket algorithm."""

    def __init__(self, rpm: int = 60):
        self.rpm = rpm
        self.tokens = rpm
        self.last_refill = time.time()

    async def acquire(self):
        """Wait until a token is available."""
        ...
```

### 2.3 Model Registry Integration

- Use Inspect's `get_model()` for model instantiation
- Map multiminds model IDs to Inspect model strings
- Handle API key configuration through existing `APIKeyManager`

### 2.4 Synthesis Prompt

Design a synthesis prompt that:
- Presents all model responses
- Asks Claude to identify consensus and disagreements
- Produces a final answer with confidence level

## Phase 3: Statistical Comparison

### 3.1 Create `eval/compare.py`

```python
def wilson_score_interval(passed: int, total: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate Wilson score confidence interval for pass rate."""
    ...

def mcnemar_test(run_a_results: list[bool], run_b_results: list[bool]) -> dict:
    """Paired comparison using McNemar's test."""
    ...

def compare_runs(run_a: RunSummary, run_b: RunSummary, episodes_a: list, episodes_b: list) -> ComparisonResult:
    """Compare two evaluation runs with statistical rigor."""
    ...
```

### 3.2 Failure Taxonomy

Classify failures into categories:
- `wrong_answer`: Model produced incorrect output
- `timeout`: Exceeded time limit
- `crash`: Unexpected error
- `cost_limit`: Exceeded token budget
- `no_consensus`: Models disagreed (MindsSolver specific)

### 3.3 CLI Commands

Add to `eval/cli.py`:

```bash
# Compare two runs
socrates-eval compare <run_a> <run_b>

# Analyze a single run with statistics
socrates-eval analyze <run_id>
```

## File Changes

### New Files
- `eval/solvers/minds.py` - MindsSolver implementation
- `eval/rate_limiter.py` - Token bucket rate limiter
- `eval/compare.py` - Statistical comparison functions
- `tests/test_minds_solver.py` - MindsSolver tests
- `tests/test_compare.py` - Statistical comparison tests
- `tests/test_rate_limiter.py` - Rate limiter tests

### Modified Files
- `eval/solvers/__init__.py` - Register MindsSolver
- `eval/cli.py` - Add `compare` and `analyze` commands
- `eval/state.py` - Add failure taxonomy constants, update RunSummary

## Execution Strategy

**Sequential execution** is appropriate because:
1. Phase 2 (MindsSolver) must be complete before Phase 3 can test comparisons
2. The compare/analyze commands need MindsSolver to produce results to compare
3. Rate limiter is a dependency for MindsSolver

Order:
1. Implement rate limiter (dependency)
2. Implement MindsSolver
3. Register MindsSolver and test on GSM8K
4. Implement statistical functions (Wilson CI, McNemar)
5. Implement compare/analyze CLI commands
6. End-to-end test: baseline vs minds comparison

## Testing Strategy

### Unit Tests
- Rate limiter token bucket behavior
- Wilson CI calculation with known values
- McNemar test with known values
- MindsSolver model configuration

### Integration Tests
- MindsSolver with mock model responses
- Compare command with sample run data

### Smoke Test
- Run `socrates-eval run gsm8k --solver minds --samples 3`
- Run `socrates-eval compare <baseline_run> <minds_run>`

## Success Criteria

1. `socrates-eval solvers` shows both `baseline` and `minds`
2. `socrates-eval run gsm8k --solver minds --samples 5` completes successfully
3. `socrates-eval compare <run_a> <run_b>` shows Wilson CI and McNemar p-value
4. `socrates-eval analyze <run_id>` shows failure taxonomy breakdown
5. All tests pass with `pytest`
