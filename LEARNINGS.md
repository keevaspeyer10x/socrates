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

1. **Phase 2 (MindsSolver)**: Use Inspect's `get_model()` for multi-provider support
2. **Phase 3 (Comparison)**: Implement Wilson CI before running large-scale comparisons
3. **Phase 4 (Learning)**: Consider structured lesson format for automated extraction
4. **Infrastructure**: Add try...finally pattern in CLI for state cleanup on errors
