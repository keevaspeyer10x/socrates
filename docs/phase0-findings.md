# Phase 0 Spike Findings: Inspect AI Exploration

**Date:** 2026-01-22

## Executive Summary

Explored Inspect AI framework to understand its log format, data structures, and requirements before building the Socrates evaluation harness.

## Key Findings

### 1. Requirements for Running Evaluations

| Requirement | Status | Notes |
|-------------|--------|-------|
| **API Keys** | Required | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc. must be set |
| **Docker** | Required for SWE-bench/GAIA | Both benchmarks need sandboxed execution |
| **Python 3.11+** | Installed | Using 3.12 |
| **inspect-ai** | Installed | v0.3.163 |
| **inspect-evals** | Installed | v0.3.105 |

### 2. Inspect Log Structure

The framework produces structured logs with rich metadata:

```
EvalLog
├── version: int
├── status: "started" | "success" | "cancelled" | "error"
├── eval: EvalSpec
│   ├── model: str (e.g., "anthropic/claude-sonnet-4-20250514")
│   ├── task: str
│   └── ... config
├── results: EvalResults | None
├── samples: list[EvalSample]
└── stats: EvalStats
```

### 3. Sample Structure (Key for Episode Extraction)

Each sample contains:

```
EvalSample
├── id: int | str
├── input: str | list[ChatMessage]      # The problem
├── target: str | list[str]              # Expected answer
├── messages: list[ChatMessage]          # Full conversation
├── output: ModelOutput                  # Final model output
├── scores: dict[str, Score]             # Evaluation results
├── events: list[Event]                  # Detailed trace
├── model_usage: dict[str, ModelUsage]   # Token counts
├── total_time: float                    # Duration
└── error: EvalError | None
```

### 4. Event Types (For 4-Tuple Extraction)

Events provide the detailed trace:

```
ToolEvent
├── function: str              # Tool name
├── arguments: dict            # Tool input
├── result: str | Content      # Tool output
├── error: ToolCallError | None
└── working_time: float

ModelEvent
├── model: str                 # Which model
├── input: list[ChatMessage]   # Input messages
├── output: ModelOutput        # Response
├── tools: list[ToolInfo]      # Available tools
└── working_time: float
```

### 5. SWE-bench Specific Requirements

```python
swe_bench(
    dataset="princeton-nlp/SWE-bench_Verified",  # HuggingFace dataset
    split="test",
    sandbox_type="docker",      # REQUIRED
    build_docker_images=True,   # Builds per-repo images
    allow_internet=False,       # Sandboxed
)
```

- Requires Docker for sandboxed code execution
- Each instance gets its own Docker container
- Images are built from SWE-bench repository specifications

### 6. GAIA Requirements

```python
gaia(
    subset="2023_all",
    split="validation",
    sandbox=("docker", "compose.yaml"),  # Also needs Docker
    max_messages=100,
)
```

- Requires Docker for web browsing and tool execution
- Uses multi-modal inputs (questions + files)

## Mapping to Socrates Episode Format

| Inspect Field | Socrates 4-Tuple | Notes |
|---------------|------------------|-------|
| `sample.input` + `sample.target` | **context** | Problem definition |
| `events` (filter ModelEvent) | **rationale** | Extract reasoning from model messages |
| `events` (filter ToolEvent) | **action** | Tool calls and outputs |
| `sample.scores` + `sample.error` | **outcome** | Pass/fail + failure mode |
| `sample.model_usage` | **cost** | Token counts for cost calculation |

## Adapter Strategy

Based on findings, the Inspect adapter should:

1. **Use Inspect's native log format** - Don't fight it, post-process
2. **Extract events for traces** - ToolEvent and ModelEvent contain the detail
3. **Compute costs from model_usage** - Per-model token counts available
4. **Map scores to outcome** - Inspect scorers return structured Score objects

## Next Steps

1. **Set up API keys** - Need ANTHROPIC_API_KEY at minimum
2. **Install Docker** - Required for SWE-bench and GAIA
3. **Run minimal test** - GSM8K or MMLU (no Docker needed) to validate log parsing
4. **Implement adapter** - Convert Inspect logs to Socrates episode format

## Code Artifacts

- `phase0_spike.py` - Test script (needs API key to run)
- `.venv/` - Python virtual environment with Inspect installed

## Blockers

1. **No API key in environment** - Cannot run actual evaluations
2. **No Docker** - Cannot run SWE-bench or GAIA

These are infrastructure requirements, not code issues. Once resolved, Phase 1 can proceed.
