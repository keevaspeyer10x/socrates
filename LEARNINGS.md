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

1. **Phase 4 (Learning)**: Structured lesson extraction from episode outcomes ✅ DONE
2. **Synthesis improvement**: Try chain-of-thought or structured comparison prompts
3. **Model fallback**: Configure fallback models when primary unavailable ✅ DONE
4. **Pure Python stats**: Consider removing scipy dependency for lightweight installs

---

# Learnings from Phase 4-5: Learning Pipeline and Custom Solvers

## Technical Learnings

### 1. Learning Schema Design
- **3-layer model works**: Episode → CandidateLesson → LessonCard provides clear lifecycle
- **Deduplication essential**: Content-based hashing prevents lesson proliferation
- **Trigger-based retrieval**: Simple keyword matching works well for MVP; semantic search deferred
- **Confidence scoring**: Evidence count + failure proportion gives reasonable confidence estimates

### 2. Pattern-Based Extraction
- **LLM extraction deferred**: Started with pattern-based extraction from failure modes
- **20% threshold**: Only extract lessons when a failure mode represents >20% of failures
- **Failure mode taxonomy**: wrong_answer, timeout, crash, cost_limit covers most cases
- **Sample limiting**: Cap episode analysis at 10 failures + 5 successes to avoid context overflow

### 3. Custom Solver Loading
- **Dynamic module loading**: `importlib.util.spec_from_file_location` works well
- **Auto-discovery**: Scanning for Solver subclasses with `name` attribute is reliable
- **Registry integration**: Auto-register on load for seamless CLI integration
- **Validation important**: Check for proper Solver inheritance before use

### 4. Model Fallbacks (LEARNINGS Application)
- **Graceful degradation**: Try fallbacks in order, track which was used
- **Statistics tracking**: `_fallback_stats` helps understand model reliability
- **Return tuple pattern**: `(model_label, response)` allows tracking actual model used
- **Default chains**: Opus→Sonnet, GPT-5.2→GPT-4o, etc. cover common cases

## Architecture Learnings

### 1. State Cleanup Pattern
- **try...finally is crucial**: Previous code could leave state stuck in RUNNING
- **Reset on exit**: Always reset to IDLE in finally block
- **Success path first**: Put state.finish_run() in try block to avoid double-save

### 2. CLI Command Design
- **Subcommand flags**: `--candidates`, `--approve`, `--reject`, `--stats` cleaner than separate commands
- **Progressive disclosure**: Default shows approved lessons; flags reveal more
- **Helpful next steps**: Show "Run X to do Y" after each operation

### 3. File-Based Storage (MVP)
- **JSON files work fine**: candidates/ and approved/ directories provide clear lifecycle
- **Avoid premature database**: SQLite or Supabase can wait until retrieval performance matters
- **Cache on load**: Maintain in-memory cache after first load for performance

## Process Learnings

### 1. Test-First for Schemas
- **20 tests written first**: All passed after implementation
- **Boundary conditions**: Test dedupe hash, application tracking, promotion flow
- **Mock-light testing**: Most tests work with real objects, no mocking needed

### 2. LEARNINGS.md as Input
- **Recommendations worked**: Both "try...finally" and "model fallback" recommendations implemented
- **Evidence of value**: Phase 2-3 learnings directly improved Phase 4-5 code
- **Virtuous cycle**: This learning about learnings will inform future phases

### 3. Incremental Implementation
- **Pattern-based before LLM**: Started with simple pattern extraction, can add LLM later
- **Trigger matching before semantic**: Keyword triggers work; vector search deferred
- **File storage before database**: JSON files now; can migrate when needed

## Recommendations for Future Work

1. **LLM-based extraction**: Add optional LLM extraction with structured output
2. **Semantic retrieval**: Replace trigger matching with embedding-based retrieval
3. **Lesson injection**: Integrate retrieved lessons into solver prompts
4. **Effectiveness validation**: Run A/B tests with/without lessons to measure impact
5. **Auto-decay**: Archive lessons that haven't been applied in N days
6. **Cross-benchmark learning**: Apply lessons from gsm8k to mmlu when relevant
