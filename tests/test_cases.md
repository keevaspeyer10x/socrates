# Test Cases: Phase 1 Inspect Eval Integration

## Unit Tests

### 1. Config Module (`eval/config.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Load API key from env | `ANTHROPIC_API_KEY=sk-test` in env | Returns `sk-test` |
| Load API key from .env file | .env file with key | Key loaded into env |
| Missing key returns None | No key set | Returns None |
| Mask key for logging | Full key | Shows `...xxxx` (last 4 chars) |
| Validate required keys | List of models | Dict of model→bool |

### 2. Preflight Module (`eval/preflight.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Detect Docker available | Docker running | `docker_available: True` |
| Detect Docker missing | No Docker | `docker_available: False` |
| Check Python version | Python 3.12 | `python_ok: True` |
| Check Inspect installed | inspect-ai in env | `inspect_ok: True` |
| Benchmark requirements | `swe_bench` | `requires_docker: True` |
| Benchmark requirements | `gsm8k` | `requires_docker: False` |

### 3. State Module (`eval/state.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create EvalState | Default | Phase=IDLE |
| Serialize to JSON | EvalState | Valid JSON string |
| Load from JSON | JSON string | EvalState object |
| Update phase | IDLE→RUNNING | Phase=RUNNING |
| Track progress | 5/10 complete | `progress: 0.5` |

### 4. Episode Data Model

| Test | Input | Expected Output |
|------|-------|-----------------|
| Create Episode | Sample data | Valid Episode |
| Serialize Episode | Episode object | JSON with all fields |
| Calculate cost | Token counts | USD amount |
| Determine failure mode | Error type | Correct enum value |

### 5. Inspect Adapter (`eval/adapters/inspect_adapter.py`)

| Test | Input | Expected Output |
|------|-------|-----------------|
| Extract context | EvalSample | Context dict |
| Extract traces from ToolEvent | ToolEvent | Trace dict |
| Extract traces from ModelEvent | ModelEvent | Trace dict |
| Map scores to outcome | Score dict | Outcome with pass/fail |
| Calculate cost from usage | ModelUsage | Cost in USD |
| Handle missing events | Empty events list | Empty traces |

### 6. Solver Registry

| Test | Input | Expected Output |
|------|-------|-----------------|
| Register solver | Solver class | Added to registry |
| Get solver by name | `"baseline"` | BaselineSolver class |
| Unknown solver | `"unknown"` | Raises KeyError |

## Integration Tests

### 7. CLI Commands

| Test | Command | Expected Behavior |
|------|---------|-------------------|
| Preflight check | `socrates-eval preflight` | Shows environment status |
| Run with missing key | `socrates-eval run gsm8k` (no key) | Error with helpful message |
| Run with valid setup | `socrates-eval run gsm8k --samples 1` | Completes, creates logs |
| Status check | `socrates-eval status` | Shows current state |
| View results | `socrates-eval results` | Shows run summary |

### 8. End-to-End: GSM8K Smoke Test

| Test | Steps | Expected Outcome |
|------|-------|------------------|
| Full pipeline | 1. Set API key<br>2. Run GSM8K (2 samples)<br>3. Check results | Episodes created with traces |

## Verification Criteria

### Phase 1 Complete When:

1. [ ] `socrates-eval preflight` runs and reports environment status
2. [ ] `socrates-eval run gsm8k --solver baseline --samples 2` completes
3. [ ] `eval_logs/runs/{run_id}/` contains:
   - `config.json` with run configuration
   - `summary.json` with pass rate and cost
   - `episodes/` with per-sample JSON files
4. [ ] Episodes contain:
   - `context` with input and target
   - `traces` array with model/tool events
   - `outcome` with pass/fail and score
   - `cost` with token counts and USD
5. [ ] API keys are never logged in full
