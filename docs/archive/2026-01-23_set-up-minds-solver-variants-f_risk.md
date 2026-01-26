# Risk Analysis: Issue #4 - HumanEval and MBPP Evals

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Code execution without sandbox | Medium | Medium | Using NO_DOCKER mode - code runs in local Python. Mitigated by: only running on trusted benchmark code |
| inspect_evals API changes | Low | Low | Using stable inspect_evals package already in venv |
| Epoch configuration issues | Low | Low | Testing with --samples flag first |

## Security Considerations

### Code Execution Risk
- **Risk**: HumanEval/MBPP execute generated Python code
- **Without Docker**: Code runs in the local Python environment
- **Mitigation**:
  - Benchmark test cases are trusted (from official HumanEval/MBPP datasets)
  - Generated code is tested against known inputs/outputs
  - No file system or network access in test execution

### API Key Exposure
- **Risk**: None - using existing SOPS/env var infrastructure
- **No new secrets required**

## Impact Analysis

### Positive Impacts
- Fast feedback loops for agent development
- Industry-standard benchmarks for comparison
- Foundation for progression to harder benchmarks (BigCodeBench, SWE-bench)

### Breaking Changes
- **None** - additive changes only
- Existing benchmarks (gsm8k, mmlu, swe_bench) unchanged

## Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| inspect_evals.humaneval | Available | Already in venv |
| inspect_evals.mbpp | Available | Already in venv |
| Docker | Optional | Not required for these benchmarks |

## Rollback Plan

If issues arise:
1. Revert changes to cli.py and config.py
2. Delete mini-sample JSON files
3. No data migration required
