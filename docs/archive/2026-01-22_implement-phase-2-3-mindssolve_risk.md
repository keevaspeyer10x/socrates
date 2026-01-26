# Risk Analysis: Phase 1 Inspect Eval Integration

## Risk Assessment Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| API key exposure in logs | Medium | High | Never log full keys, mask in output |
| Inspect API version breaks | Medium | Medium | Pin version, create adapter layer |
| Docker not available | High | Low | Graceful degradation to non-Docker benchmarks |
| Cost overrun during eval | Medium | Medium | Add `--max-cost` flag, warn before expensive runs |
| Rate limiting from providers | High | Low | Per-provider semaphores, backoff |

## Detailed Risk Analysis

### 1. Security: API Key Handling
**Risk**: API keys could be logged or exposed in error messages

**Mitigation**:
- Load keys from `.env` file (not command line args)
- Mask keys in all log output (show only last 4 chars)
- Never persist keys in state files
- Add `.env` to `.gitignore`

### 2. Dependency: Inspect AI Version Coupling
**Risk**: Inspect AI is actively developed; breaking changes possible

**Mitigation**:
- Create `eval/adapters/inspect_adapter.py` isolation layer
- Pin inspect-ai version in pyproject.toml
- Test against specific versions before upgrade
- Document supported versions

### 3. Infrastructure: Docker Availability
**Risk**: Users may not have Docker installed

**Mitigation**:
- Preflight check detects Docker before run
- Clear error message with install instructions
- Non-Docker benchmarks (GSM8K, MMLU) always available
- Document which benchmarks need Docker

### 4. Cost: Unexpected API Spend
**Risk**: Running large evaluations could incur significant costs

**Mitigation**:
- Show estimated cost before run starts
- Add `--max-cost` flag to abort if exceeded
- Default to small sample sizes (5-10) for testing
- Track actual cost in episode logs

### 5. Reliability: Provider Rate Limits
**Risk**: Multi-model queries may hit rate limits

**Mitigation**:
- Per-provider semaphores (different limits)
- Exponential backoff on 429 errors
- Log rate limit events for debugging
- Allow `--provider` flag to limit to one provider

## Impact on Plan

No changes to plan required. Mitigations are already incorporated:
- Adapter layer in project structure
- Preflight command in Phase 1
- Cost tracking in episode format

## Approval

**Risk Level**: LOW-MEDIUM
**Recommendation**: Proceed with implementation
