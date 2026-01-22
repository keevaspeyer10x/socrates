# Test Cases: Phase 2-3 Implementation

## Phase 2: MindsSolver Tests

### Unit Tests

#### TC-2.1: MindsSolver Initialization
- **Input**: Default models, custom synthesizer model
- **Expected**: Solver initializes with correct model list and synthesizer
- **File**: `tests/test_minds_solver.py::TestMindsSolver::test_initialization`

#### TC-2.2: MindsSolver Metadata
- **Input**: MindsSolver instance
- **Expected**: Metadata includes name="minds", models list, synthesizer
- **File**: `tests/test_minds_solver.py::TestMindsSolver::test_metadata`

#### TC-2.3: MindsSolver Registration
- **Input**: Import eval.solvers
- **Expected**: "minds" solver is in list_solvers()
- **File**: `tests/test_solvers.py::TestSolverRegistry::test_minds_solver_registered`

### Rate Limiter Tests

#### TC-2.4: Token Bucket Initialization
- **Input**: RPM=60
- **Expected**: Bucket starts with 60 tokens
- **File**: `tests/test_rate_limiter.py::TestTokenBucket::test_initialization`

#### TC-2.5: Token Acquisition
- **Input**: Acquire token when bucket has tokens
- **Expected**: Returns immediately, decrements token count
- **File**: `tests/test_rate_limiter.py::TestTokenBucket::test_acquire_available`

#### TC-2.6: Token Refill
- **Input**: Empty bucket, wait for refill period
- **Expected**: Bucket refills at correct rate
- **File**: `tests/test_rate_limiter.py::TestTokenBucket::test_refill`

#### TC-2.7: Rate Limiter Per-Provider
- **Input**: Different providers with different limits
- **Expected**: Each provider tracked independently
- **File**: `tests/test_rate_limiter.py::TestRateLimiter::test_per_provider`

## Phase 3: Statistical Comparison Tests

### Wilson Score Tests

#### TC-3.1: Wilson CI Normal Case
- **Input**: passed=75, total=100, confidence=0.95
- **Expected**: CI approximately (0.66, 0.83)
- **File**: `tests/test_compare.py::TestWilsonCI::test_normal_case`

#### TC-3.2: Wilson CI Edge Case - All Pass
- **Input**: passed=100, total=100
- **Expected**: CI upper bound = 1.0, lower bound < 1.0
- **File**: `tests/test_compare.py::TestWilsonCI::test_all_pass`

#### TC-3.3: Wilson CI Edge Case - All Fail
- **Input**: passed=0, total=100
- **Expected**: CI lower bound = 0.0, upper bound > 0.0
- **File**: `tests/test_compare.py::TestWilsonCI::test_all_fail`

#### TC-3.4: Wilson CI Small Sample
- **Input**: passed=2, total=5
- **Expected**: Wide CI due to small sample
- **File**: `tests/test_compare.py::TestWilsonCI::test_small_sample`

### McNemar Test Tests

#### TC-3.5: McNemar Significant Difference
- **Input**: A better than B on many samples
- **Expected**: p-value < 0.05, significant=True
- **File**: `tests/test_compare.py::TestMcNemar::test_significant_difference`

#### TC-3.6: McNemar No Difference
- **Input**: A and B perform similarly
- **Expected**: p-value > 0.05, significant=False
- **File**: `tests/test_compare.py::TestMcNemar::test_no_difference`

#### TC-3.7: McNemar Edge Case - Identical
- **Input**: A and B have identical results
- **Expected**: p-value = 1.0
- **File**: `tests/test_compare.py::TestMcNemar::test_identical`

### Failure Taxonomy Tests

#### TC-3.8: Failure Classification - Wrong Answer
- **Input**: Sample with incorrect output
- **Expected**: failure_mode = "wrong_answer"
- **File**: `tests/test_compare.py::TestFailureTaxonomy::test_wrong_answer`

#### TC-3.9: Failure Classification - Timeout
- **Input**: Sample with timeout error
- **Expected**: failure_mode = "timeout"
- **File**: `tests/test_compare.py::TestFailureTaxonomy::test_timeout`

### CLI Tests

#### TC-3.10: Compare Command Output
- **Input**: Two valid run IDs
- **Expected**: Shows pass rates, Wilson CI, McNemar p-value
- **File**: `tests/test_cli.py::TestCompareCommand::test_compare_output`

#### TC-3.11: Analyze Command Output
- **Input**: Valid run ID
- **Expected**: Shows pass rate, CI, failure breakdown
- **File**: `tests/test_cli.py::TestAnalyzeCommand::test_analyze_output`

#### TC-3.12: Compare Command - Missing Run
- **Input**: Non-existent run ID
- **Expected**: Error message, exit code 1
- **File**: `tests/test_cli.py::TestCompareCommand::test_missing_run`

## Integration Tests

### IT-1: MindsSolver with Mock Models
- **Setup**: Mock model responses for all 5 models
- **Action**: Run MindsSolver.solve() with sample task state
- **Expected**: Returns synthesized answer combining all responses
- **File**: `tests/test_integration.py::test_minds_solver_mock`

### IT-2: End-to-End Compare Flow
- **Setup**: Two pre-existing runs with episode data
- **Action**: Run `socrates-eval compare <run_a> <run_b>`
- **Expected**: Complete comparison report with statistics
- **File**: `tests/test_integration.py::test_compare_flow`

## Smoke Tests (Manual/CI)

### ST-1: MindsSolver on GSM8K
```bash
socrates-eval run gsm8k --solver minds --samples 3
```
- **Expected**: Completes successfully, shows pass rate and cost

### ST-2: Baseline vs Minds Comparison
```bash
socrates-eval run gsm8k --solver baseline --samples 5
socrates-eval run gsm8k --solver minds --samples 5
socrates-eval compare <baseline_run> <minds_run>
```
- **Expected**: Shows comparison with statistical analysis
