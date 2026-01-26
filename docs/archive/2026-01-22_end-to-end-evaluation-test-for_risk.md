# Risk Analysis: Phase 2-3 Implementation

## Risk Assessment

### High Impact Risks

#### 1. API Cost Overrun
- **Risk**: MindsSolver queries 5 models per sample, multiplying costs 5x+
- **Likelihood**: Medium (if not careful with sample limits)
- **Impact**: High (budget is ~$92 remaining)
- **Mitigation**:
  - Default to small sample sizes (--samples 3-5 for testing)
  - Add cost estimation before run (`--dry-run` flag)
  - Track cumulative cost in EvalState
  - Add cost limit parameter to abort if exceeded

#### 2. Rate Limiting Failures
- **Risk**: Different providers have different rate limits; hitting limits causes failures
- **Likelihood**: High (especially with parallel queries)
- **Impact**: Medium (failed samples, wasted cost)
- **Mitigation**:
  - Conservative default RPM (30 requests/minute per provider)
  - Exponential backoff on 429 errors
  - Per-provider configuration in config

### Medium Impact Risks

#### 3. Model API Incompatibilities
- **Risk**: Inspect's `get_model()` may not support all multiminds models
- **Likelihood**: Medium (Inspect supports major providers)
- **Impact**: Medium (may need to use httpx directly for some models)
- **Mitigation**:
  - Start with well-supported models (Claude, GPT, Gemini)
  - Fall back to direct API calls if needed
  - Test each model individually before full integration

#### 4. Synthesis Quality Variance
- **Risk**: Claude synthesizer may not always produce best answer from diverse responses
- **Likelihood**: Medium
- **Impact**: Low-Medium (affects benchmark scores but data is logged)
- **Mitigation**:
  - Log all individual model responses in traces
  - Allow analysis of which model was "right" even if synthesis failed
  - Iterate on synthesis prompt based on results

### Low Impact Risks

#### 5. Statistical Test Edge Cases
- **Risk**: Wilson CI undefined for 0/n or n/n pass rates; McNemar requires paired samples
- **Likelihood**: Low (edge cases)
- **Impact**: Low (just need proper handling)
- **Mitigation**:
  - Handle edge cases with appropriate defaults/warnings
  - Require matching sample IDs for McNemar comparison

#### 6. Async Complexity
- **Risk**: Race conditions or deadlocks in parallel model queries
- **Likelihood**: Low (asyncio is well-understood)
- **Impact**: Low (would show as test failures)
- **Mitigation**:
  - Use asyncio.gather with return_exceptions=True
  - Add timeouts to all async operations
  - Comprehensive async tests

## Security Considerations

- **API Keys**: Already handled by existing APIKeyManager + SOPS integration
- **No new attack surface**: This is evaluation code, not user-facing
- **Data handling**: Benchmark data is public; no PII concerns

## Rollback Plan

If implementation fails:
1. MindsSolver is optional - baseline solver remains functional
2. Statistical functions are isolated in compare.py
3. CLI commands can be disabled without affecting core functionality
4. No database migrations or state format changes required

## Dependencies

| Dependency | Version | Risk |
|------------|---------|------|
| inspect-ai | >=0.3.150 | Low - already in use |
| scipy | New | Low - well-maintained, for statistical tests |
| asyncio | stdlib | None |

## Estimated Cost

For testing:
- MindsSolver smoke test (5 samples x 5 models): ~$0.50-1.00
- Full GSM8K comparison (100 samples): ~$10-15

Total Phase 2-3 testing budget: ~$15-20

## Go/No-Go Checklist

- [x] Budget sufficient for testing (~$92 remaining)
- [x] API keys configured for all 5 models
- [x] No breaking changes to existing functionality
- [x] Rollback path exists
- [x] Security review: no new attack vectors
