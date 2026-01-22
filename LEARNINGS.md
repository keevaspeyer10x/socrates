# Learnings from Phase 1: Eval Framework Implementation

## Technical Learnings

### 1. Inspect AI Integration
- **EvalLog structure**: `EvalLog` → `samples` (list of `EvalSample`) → `events` (ToolEvent/ModelEvent)
- **Event-first extraction**: Tool calls and model outputs are in events list, not directly on sample
- **Log file formats**: `.eval` (newer) and `.json` (older) both supported

### 2. Docker Requirements
- SWE-bench, GAIA, and CyBench require Docker for sandboxed execution
- GSM8K, MMLU, HumanEval, ARC work without Docker
- Preflight checks should validate Docker early and adjust available benchmarks

### 3. Python Environment
- Modern Linux distros use PEP 668 (externally-managed-environment)
- Always create venv for project dependencies
- Use `datetime.now(timezone.utc)` instead of deprecated `datetime.utcnow()`

### 4. API Key Management
- Each provider has its own env var naming convention
- Inspect AI uses same env vars: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.
- .env file pattern works well for local development

## Architecture Learnings

### 1. Pluggable Solver Pattern
- Abstract base class with `solve(state, generate)` method
- Registry pattern for solver discovery
- Metadata (name, description) on solver instances

### 2. Episode Logging (4-Tuple)
- context: input, target, metadata
- traces: model/tool events with timing
- action: final output, tool call count
- outcome: passed/failed, score, failure_mode

### 3. State Persistence
- JSON serialization for cross-session persistence
- Phase-based state machine (IDLE → SETUP → RUNNING → ANALYZING → LEARNING)
- File-based storage with atomic writes

## Process Learnings

### 1. Test-First Development
- Writing tests before implementation caught API design issues early
- 37 tests provided confidence for refactoring datetime handling
- Mock-heavy tests for external dependencies (subprocess, imports)

### 2. Multi-Model Review Value
- 5-model minds review during planning identified:
  - Statistical rigor needs (Wilson CI, McNemar test)
  - Failure taxonomy requirement
  - Runtime Docker validation vs install-time
  - .env pattern for API keys

### 3. Orchestrator Workflow
- Force-skip requires >50 char justification
- Template variables ({{test_command}}) need project-specific config
- VERIFY phase gates may not apply to all project types (e.g., Playwright for CLI)

## Recommendations for Future Phases

1. **Phase 2 (MindsSolver)**: Use Inspect's `get_model()` for multi-provider support ✅ DONE
2. **Phase 3 (Comparison)**: Implement Wilson CI before running large-scale comparisons ✅ DONE
3. **Phase 4 (Learning)**: Consider structured lesson format for automated extraction
4. **Infrastructure**: Add try...finally pattern in CLI for state cleanup on errors

---

# Learnings from Phase 2-3: MindsSolver and Statistical Analysis

## Technical Learnings

### 1. Multi-Model Collaboration
- **Parallel queries**: `asyncio.gather()` with `return_exceptions=True` allows graceful degradation
- **Rate limiting**: Token bucket algorithm works well; per-provider tracking avoids cross-provider contention
- **Synthesis**: Simple "here are all responses, synthesize" prompt works but could be improved with structured comparison

### 2. Statistical Methods
- **Wilson CI**: Better than normal approximation for edge cases (0% or 100% pass rates)
- **McNemar test**: Requires paired samples (same sample IDs); falls back gracefully when unavailable
- **scipy dependency**: Only needed for `norm.ppf()` and `binom_test()` - could potentially be removed with pure Python implementations

### 3. API Model IDs
- Model IDs vary across providers and change over time
- OpenRouter may not have all models (e.g., `gpt-5.2-codex-max` not available)
- Default model list should be configurable and documented

## Architecture Learnings

### 1. Rate Limiter Design
- Lock-free token refill using timestamp comparison works for single-process use
- Per-provider tracking avoids single bottleneck across all models
- Configurable RPM allows tuning for different provider limits

### 2. CLI Command Structure
- `compare <run_a> <run_b>` natural for paired comparison
- `analyze <run>` provides single-run deep dive with failure taxonomy
- Consistent output formatting across commands improves UX

### 3. Test Assertions
- Floating point comparisons need tolerance (`4.9 < x < 5.1` not `x == 5`)
- numpy boolean vs Python boolean: use `== True` not `is True`
- Edge case tests (0/n, n/n) catch boundary issues early

## Process Learnings

### 1. TDD Approach
- Writing tests first (RED phase) confirmed they would fail
- 31 new tests all failed initially, then passed after implementation
- Tests caught floating point and numpy issues before merge

### 2. Multi-Model Reviews
- Codex model not available on OpenRouter - need fallback models
- Gemini 3 Pro and Grok 4.1 reviews completed successfully
- Design validation confirmed implementation matched plan

### 3. scipy Dependency Consideration
- scipy is a heavyweight dependency (~40MB)
- Only used for `norm.ppf()` and `binom_test()`
- Could implement pure Python versions for minimal installs (YAGNI for now)

## Recommendations for Phase 4+

1. **Phase 4 (Learning)**: Structured lesson extraction from episode outcomes
2. **Synthesis improvement**: Try chain-of-thought or structured comparison prompts
3. **Model fallback**: Configure fallback models when primary unavailable
4. **Pure Python stats**: Consider removing scipy dependency for lightweight installs
