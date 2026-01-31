# Session Bootstrap

**Load secrets using one of these methods (in priority order):**

## Method 1: Infisical (Recommended)
```bash
# Install Infisical CLI if needed
npm install -g @infisical/cli

# Set your service token (get from https://secrets.keeva.space)
export INFISICAL_TOKEN="st.xxx.xxx"

# Load secrets
source ~/keeva-devtools/scripts/secrets-loader.sh
# or: source ~/repos/keeva-devtools/scripts/secrets-loader.sh
```

## Method 2: .env.local (BYOK - Bring Your Own Keys)
```bash
# Copy template and add your keys
cp .env.example .env.local
# Edit .env.local with your API keys

# Load secrets
source ~/keeva-devtools/scripts/secrets-loader.sh
```

## Method 3: SOPS/AGE (Legacy)
```bash
export SOPS_KEY_PASSWORD="I love vibe coding"
source ~/keeva-devtools/scripts/secrets-loader.sh
```

The `secrets-loader.sh` script automatically detects which method is available and loads secrets accordingly.

---

## Cross-Repository Awareness

When working on tasks that affect multiple repositories, Claude should proactively check related repos for necessary changes.

### Related Repositories

| Repository | Purpose | GitHub URL |
|------------|---------|------------|
| `workflow-orchestrator` | Prevents AI agents from forgetting workflow steps | `keevaspeyer10x/workflow-orchestrator` |
| `keeva-devtools` | Dev tools distribution for AI coding environments | `keevaspeyer10x/keeva-devtools` |
| `multiminds` | Query multiple AI models and synthesize responses | `keevaspeyer10x/multiminds` |
| `ai-tool-bridge` | Natural language command translation - MCP server | `keevaspeyer10x/ai-tool-bridge` |
| `socrates` | Iterative, self-learning engine for AI agents | `keevaspeyer10x/socrates` |
| `meld` | Merge/diff tool wrapper | `keevaspeyer10x/meld` |
| `visual-verification-service` | AI-powered visual verification | `keevaspeyer10x/visual-verification-service` |
| `quiet-ping-v6` | Social notification service | `keevaspeyer10x/quiet-ping-v6` |

### How to Access Other Repos

With `gh auth login` configured (or GH_TOKEN loaded from secrets), Claude has full access.

**Read files on-demand** (quick lookups):
```bash
gh api repos/keevaspeyer10x/REPO/contents/FILE --jq '.content' | base64 -d
```

**List directory/issues:**
```bash
gh api repos/keevaspeyer10x/REPO/contents/src
gh issue list --repo keevaspeyer10x/REPO
```

### Making Changes to Other Repos

```bash
# Clone, edit, PR workflow
gh repo clone keevaspeyer10x/REPO /tmp/REPO
cd /tmp/REPO
git checkout -b claude/fix-xyz
# ... make changes ...
git add -A && git commit -m "fix: description"
git push -u origin claude/fix-xyz
gh pr create --title "Fix: description" --body "Changes from other-repo"
cd - && rm -rf /tmp/REPO
```

### Creating Issues

```bash
gh issue create --repo keevaspeyer10x/REPO \
  --title "Sync: Update X" \
  --body "## Context
Changes in this repo require updates there.

## Required Changes
- [ ] Update X in path/to/file.py

---
*Auto-generated cross-repo issue*"
```

---

# Socrates - AI Evaluation Framework

## Overview
Socrates is a framework for evaluating AI model performance on coding benchmarks using inspect_ai. It includes:
- Multi-solver support (baseline, minds multi-model)
- LLM-as-Judge evaluation (no ground truth needed)
- Learning system for extracting lessons from failures
- Fail set workflow for iterating on hard problems

## Key Commands

```bash
# Run evaluation
socrates-eval run <benchmark> --solver <solver> --model <model>

# Available benchmarks: gsm8k, mmlu, humaneval, humaneval_fast, mbpp, bigcodebench, bigcodebench_hard

# Analyze results
socrates-eval results <run_id>
socrates-eval analyze <run_id>
socrates-eval compare <run_a> <run_b>

# Learning system
socrates-eval learn <run_id> [--llm]
socrates-eval lessons [--candidates] [--approve <id>]

# Fail set workflow
socrates-eval analyze-failures <run_id> --output fail_set.json
socrates-eval analyze-failures run1 run2 --intersect --output hard_failures.json
socrates-eval run <benchmark> --sample-ids fail_set.json
```

## Test Scripts

### test_hard_question.py
Compares minds modes on challenging questions with automatic clarification retry.

**Features:**
- Parallel execution of multiple modes (minds synthesis, debate, individual models)
- **Automatic clarification**: If a model misunderstands (e.g., writes code when analysis expected), retries with clarification
- LLM-as-Judge evaluation
- Caches responses to avoid re-running

**Usage:**
```bash
python test_hard_question.py           # Fresh run with clarification retry
python test_hard_question.py --cache   # Re-evaluate cached responses
```

**Output:** `hard_question_responses.json`, `hard_question_results.json`

### test_individual_models.py
Tests each SOTA model individually on the same question.

### test_minds_judge.py
Compares minds modes (default, fast, cheap) using LLM-as-Judge.

## Architecture

```
eval/
  cli.py          # Main CLI (socrates-eval)
  config.py       # API keys, benchmark requirements
  state.py        # Run state tracking
  adapters/       # Inspect AI integration
  solvers/        # Solver implementations (baseline, minds)
  judge/          # LLM-as-Judge system
  learning.py     # Lesson extraction
```

## Notes
- BigCodeBench requires Docker
- HumanEval/MBPP use local sandbox (no Docker)
- minds CLI must be installed separately for multi-model queries

## GPQA Diamond Experiment Results (2026-01-26)

Full 198-sample comparison of multi-model approaches on PhD-level science questions.

### Key Findings

| Configuration | Accuracy | Cost | Recommendation |
|--------------|----------|------|----------------|
| minds_critique | **88.4%** | $184 | Best accuracy |
| Gemini 2.5 Pro solo | 86.4% | $4 | Best value |
| minds_baseline | 84.3% | $77 | AVOID - worse than solo |
| minds_critique_challenge | 86.9% | $232 | AVOID - DA hurts |

**Key insight**: Critique workflow adds +4.1%, but devil's advocate HURTS (-1.5%).

### Detailed Documentation
- `experiments/GPQA_EXPERIMENT_REPORT.md` - Full methodology and results
- `experiments/FAILURE_ANALYSIS.md` - Failure pattern analysis
- `experiments/QUICK_REFERENCE.md` - Quick lookup guide

### Solver Modes
```bash
# Best accuracy (88.4%)
socrates-eval run gpqa --solver minds --solver-mode critique

# Best cost/accuracy ratio (86.4%, $4)
socrates-eval run gpqa --solver baseline --model google/gemini-2.5-pro
```
