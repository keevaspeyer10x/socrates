# Risk Analysis: Issue #5 - BigCodeBench + Fail Set Workflow

## Risk Assessment

### R1: Docker Dependency (Medium)

**Risk**: BigCodeBench requires Docker for execution. Users without Docker cannot run this benchmark.

**Impact**: Reduced usability for some users; CI/CD environments may need Docker configuration.

**Mitigation**:
- Clear error message when Docker not available
- Document Docker requirement in README
- Already handled by existing preflight checks and BenchmarkRequirements.DOCKER_REQUIRED

**Residual Risk**: Low - consistent with existing Docker-required benchmarks (swe_bench, gaia)

### R2: BigCodeBench-Hard Version Availability (Low)

**Risk**: The "v0.1.2_hard" or similar version may not exist as a distinct HuggingFace split.

**Impact**: May need to filter by task IDs instead of using a version string.

**Mitigation**:
- Check HuggingFace dataset structure before implementation
- Fall back to subset filtering if no hard split exists
- Use `subset` parameter of bigcodebench() function

**Residual Risk**: Low - fallback approach is well-defined

### R3: Episode Format Compatibility (Low)

**Risk**: `analyze-failures` command assumes episode format with `outcome.passed` field.

**Impact**: Command may fail if episode format differs.

**Mitigation**:
- Validate episode structure before processing
- Use defensive coding with `.get()` methods
- Add unit tests with various episode formats

**Residual Risk**: Low - episode format is controlled by our InspectAdapter

### R4: Large Fail Sets (Low)

**Risk**: If a model fails many problems, fail set JSON could be large.

**Impact**: Minor performance impact; JSON file size.

**Mitigation**:
- JSON is compact (just IDs)
- 1140 problems max = small JSON even if all fail

**Residual Risk**: Negligible

### R5: Cost of Full BigCodeBench Run (Medium)

**Risk**: Running full BigCodeBench (1140 problems) with expensive models could be costly.

**Impact**: Research budget depletion.

**Mitigation**:
- Default to `--samples` limit
- Provide `eval_mini_bigcodebench.json` for rapid iteration
- Clear cost warnings in documentation

**Residual Risk**: Low - user controls via --samples flag

## Security Considerations

### S1: Docker Sandbox Isolation

**Status**: Safe - BigCodeBench uses Docker sandbox by default, isolating code execution.

### S2: Fail Set JSON Injection

**Status**: Safe - Sample IDs are integers parsed by JSON; no code execution from fail set files.

## Compatibility Assessment

### Backward Compatibility

- **CLI**: New commands/options only; no breaking changes
- **Config**: Additive changes to DOCKER_REQUIRED set
- **Episodes**: Uses existing format; no changes needed

### Forward Compatibility

- Fail set JSON format is extensible (has `source_runs` metadata)
- New benchmarks can be added following same pattern

## Impact Summary

| Area | Impact | Risk Level |
|------|--------|------------|
| CLI | 2 new benchmarks, 1 new command | Low |
| Config | 2 new entries in DOCKER_REQUIRED | Low |
| Dependencies | None new (uses existing inspect_evals) | None |
| Storage | Small JSON files for fail sets | Negligible |
| Cost | User-controlled via --samples | Medium (user choice) |

## Recommendation

**Proceed with implementation**. All risks are low-to-medium and have clear mitigations in place. The implementation follows existing patterns in the codebase.
