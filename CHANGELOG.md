# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-22

### Added
- **Learning Pipeline (Phase 4)**: Extract lessons from evaluation episodes
  - `CandidateLesson` and `LessonCard` schemas for structured knowledge
  - `LearningEngine` for extraction, retrieval, and lifecycle management
  - Pattern-based lesson extraction from failure modes
  - Deduplication using content hashes
  - Candidate approval/rejection workflow
  - Lesson retrieval based on context triggers
  - Effectiveness tracking (application count, success rate)
- **Custom Solver Support (Phase 5)**: Load solvers from external files
  - `load_custom_solver()` for file or module path loading
  - Auto-registration of loaded solvers
  - `create_solver_instance()` for instantiation with kwargs
- **Model Fallbacks**: Automatic fallback when primary models fail
  - Configurable fallback chains per model
  - Fallback usage statistics tracking
  - Graceful degradation with error reporting
- **CLI Commands**: `socrates-eval learn` and `socrates-eval lessons`
  - `learn <run_id>`: Extract lessons from evaluation run
  - `lessons`: View approved lessons
  - `lessons --candidates`: View pending candidates
  - `lessons --approve <id>`: Approve a candidate
  - `lessons --reject <id>`: Reject a candidate
  - `lessons --stats`: View learning statistics

### Improved
- **State Cleanup**: Added try...finally pattern for robust state cleanup on errors
- **MindsSolver**: Now supports fallback models and tracks fallback usage

### Technical Details
- 90 tests total (20 new tests for Phase 4-5)
- LessonCard schema with confidence, triggers, evidence refs
- Trigger-based retrieval for relevant lesson injection
- Model fallback configuration via `DEFAULT_FALLBACKS` mapping

---

## [0.2.0] - 2026-01-22

### Added
- **MindsSolver**: Multi-model collaboration solver querying 5 top models (Claude Opus 4.5, Gemini 3 Pro, GPT-5.2, Grok 4.1, DeepSeek V3.2) with Claude as synthesizer
- **Rate Limiting**: Token bucket algorithm with per-provider RPM limits for parallel model queries
- **Statistical Comparison**: Wilson score confidence intervals and McNemar's paired test for rigorous run comparison
- **Failure Taxonomy**: Automatic classification of failures (wrong_answer, timeout, crash, cost_limit)
- **CLI Commands**: `socrates-eval compare` and `socrates-eval analyze` for statistical analysis
- **scipy dependency**: Added for statistical calculations

### Technical Details
- 70 tests total (31 new tests for Phase 2-3)
- Async rate limiter with lock-free token bucket refill
- Pluggable model configuration for MindsSolver

---

## [0.1.0] - 2026-01-22

### Added
- **Evaluation Framework**: Built on Inspect AI for empirically validating AI agent designs
- **CLI Commands**: `socrates-eval` with preflight, run, status, results, and solvers subcommands
- **Pluggable Solver Architecture**: Base class with registry for baseline, minds, and custom solvers
- **Episode Logging**: 4-tuple format (context, traces, action, outcome) for learning
- **Cost Tracking**: Automatic USD cost calculation per evaluation
- **Preflight Checks**: Environment validation for Docker, API keys, Python version, Inspect AI
- **Benchmark Support**: GSM8K, MMLU, HumanEval (no Docker), SWE-bench, GAIA (Docker required)
- **State Persistence**: EvalState for workflow tracking across sessions
- **Inspect Adapter**: Extract episodes from Inspect AI evaluation logs

### Technical Details
- 37 tests with full coverage
- Type hints throughout
- Dataclass-based models for serialization
- Click-based CLI interface
