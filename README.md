# Socrates

**An iterative, self-learning engine for AI agents**

Socrates is a framework for building AI systems that can think deeply, collaborate effectively, and learn from experience. Named after the philosopher known for the Socratic method of inquiry, it embodies the principle that wisdom comes through questioning, dialogue, and reflection.

## Vision

> "Ask minds a question and it runs through frameworks, goes away for half an hour, thinks about the problem perhaps 5 different ways, tests it, reflects, iterates and comes back with a great answer."

## Core Concepts

### The General Person Algorithm (GPA)

A unified framework for how AI agents think, act, and learn:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     GENERAL PERSON ALGORITHM v2                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ LEARNING                                                                     ││
│  │ • Single unified format                                                     ││
│  │ • Evidence tiers (hypothesis → candidate → validated)                       ││
│  │ • Auto-decay (30 days if no validation)                                     ││
│  │ • Effectiveness tracking (did it improve outcomes?)                         ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ EXECUTION (MVP Loop)                                                         ││
│  │  ┌────────┐    ┌────────┐    ┌────────┐    ┌────────┐                      ││
│  │  │ SENSE  │───►│ DECIDE │───►│  ACT   │───►│REFLECT │                      ││
│  │  └────────┘    └───┬────┘    └────────┘    └────────┘                      ││
│  │         [Budget check + stakes check]                                       ││
│  │         ┌─────────┴─────────┐                                               ││
│  │    [FAST: pattern    [DEEP: Sophisticated                                   ││
│  │     match only]       Minds if budget allows]                               ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │ CONTEXT                                                                      ││
│  │ • Resource budgets (time, tokens, cost)                                     ││
│  │ • Human integration (approval gates, escalation)                            ││
│  │ • Multi-agent coordination (handoffs, conflicts)                            ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Three Interconnected Pieces

| Piece | Purpose | Core Principle |
|-------|---------|----------------|
| **Problem Solving** (Sophisticated Minds) | Decide HOW to approach | Deep thinking with multiple frameworks |
| **Workflow Execution** (ISLE Loop) | DO the work | Sense → Decide → Act → Reflect |
| **Learning** (Rich Capture) | Get BETTER over time | Preserve reasoning, not just rules |

### Key Insight on Learning

> "The insight isn't in the suggested change, it's in the WHY of the change, what was weighed up, the considerations and trade-offs, issues, uncertainties, risks. Without knowing this - perhaps it addresses the signal optimally in this case, but it may not be optimal in other cases - it's a false learning."

## Documentation

- [General Person Algorithm](docs/research/general-person-algorithm.md) - Main framework document
- [Multi-Model Collaboration Design](docs/research/multi-model-collaboration-design.md) - Phase 1 research
- [Multi-Model Collaboration Phase 2](docs/research/multi-model-collaboration-phase2.md) - Collaboration patterns
- [Multi-Model Collaboration Phase 3](docs/research/multi-model-collaboration-phase3.md) - Workflow execution
- [Multi-Model Collaboration Phase 4](docs/research/multi-model-collaboration-phase4.md) - Deep iteration

## Evaluation Framework

Socrates includes an evaluation harness built on [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) for empirically validating AI agent designs.

### Quick Start

```bash
# Install with eval dependencies
pip install -e ".[eval]"

# Check environment
socrates-eval preflight

# Run baseline evaluation
socrates-eval run gsm8k --solver baseline --samples 10
```

### Features

- **Pluggable Solvers**: Compare baseline (single model) vs minds (multi-model) vs custom agents
- **Episode Logging**: 4-tuple format (context, traces, action, outcome) for learning
- **Cost Tracking**: Automatic USD cost calculation per evaluation
- **Benchmark Support**: GSM8K, MMLU, HumanEval (no Docker), SWE-bench, GAIA (Docker required)

### CLI Commands

```bash
socrates-eval preflight    # Check environment readiness
socrates-eval run <bench>  # Run evaluation
socrates-eval status       # Show current state
socrates-eval results      # View run results
socrates-eval solvers      # List available solvers
```

See [docs/plan.md](docs/plan.md) for the full implementation plan.

## Status

**Phase 1 Complete** - Evaluation framework core infrastructure.

- Preflight checks (Docker, API keys, Python version)
- State persistence and episode logging
- Inspect AI adapter for log extraction
- Baseline solver implementation
- CLI with run/status/results commands

### Next Steps

1. Phase 2: Implement MindsSolver for multi-model collaboration
2. Phase 3: Statistical comparison (Wilson CI, McNemar test)
3. Phase 4: Learning pipeline for lesson extraction
4. Phase 5: Custom solver support

## Research Budget

- **Total budget**: ~$100
- **Spent**: ~$8.34
- **Remaining**: ~$91.66

## License

MIT
