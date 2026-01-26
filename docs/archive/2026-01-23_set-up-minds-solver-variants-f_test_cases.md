# Test Cases: Issue #4 - HumanEval and MBPP Evals

## Unit Tests

### TC-1: _get_benchmark_task returns HumanEval task
- **Input**: `_get_benchmark_task("humaneval")`
- **Expected**: Returns inspect_evals.humaneval task with default epochs
- **Validation**: Task object has correct configuration

### TC-2: _get_benchmark_task returns HumanEval Fast task
- **Input**: `_get_benchmark_task("humaneval_fast")`
- **Expected**: Returns inspect_evals.humaneval task with 1 epoch
- **Validation**: Task has single epoch configured

### TC-3: _get_benchmark_task returns MBPP task
- **Input**: `_get_benchmark_task("mbpp")`
- **Expected**: Returns inspect_evals.mbpp task with temperature=0.5
- **Validation**: Task object configured correctly

### TC-4: BenchmarkRequirements classifies correctly
- **Input**: `BenchmarkRequirements.requires_docker("humaneval")`
- **Expected**: Returns `False`
- **Input**: `BenchmarkRequirements.requires_docker("mbpp")`
- **Expected**: Returns `False`

### TC-5: Benchmark normalization handles variants
- **Input**: `_get_benchmark_task("human-eval")`, `_get_benchmark_task("HumanEval")`
- **Expected**: Both return valid HumanEval task
- **Validation**: Case-insensitive, hyphen-to-underscore conversion

## Integration Tests

### TC-6: CLI accepts humaneval benchmark
- **Command**: `socrates-eval run humaneval --solver baseline --samples 1`
- **Expected**: Runs without error, produces episode output
- **Note**: Requires API key, may incur cost

### TC-7: CLI accepts humaneval_fast benchmark
- **Command**: `socrates-eval run humaneval_fast --solver baseline --samples 1`
- **Expected**: Runs with single epoch
- **Note**: Faster than standard HumanEval

### TC-8: CLI accepts mbpp benchmark
- **Command**: `socrates-eval run mbpp --solver baseline --samples 1`
- **Expected**: Runs without error, produces episode output

### TC-9: Mini-sample files work with --sample-ids
- **Command**: `socrates-eval run humaneval_fast --solver baseline --sample-ids eval_mini_humaneval.json`
- **Expected**: Runs only the specified sample IDs

## Manual Verification

### TC-10: Documentation updated
- **Check**: README.md includes HumanEval/MBPP in examples
- **Check**: Quick start commands work as documented
