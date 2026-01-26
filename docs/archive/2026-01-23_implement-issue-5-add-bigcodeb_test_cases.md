# Test Cases: Issue #5 - BigCodeBench + Fail Set Workflow

## Unit Tests

### T1: BigCodeBench Task Creation
**File**: `tests/test_cli.py`
**Function**: `test_get_benchmark_task_bigcodebench`

```python
def test_get_benchmark_task_bigcodebench():
    """Verify bigcodebench task can be created."""
    task = _get_benchmark_task("bigcodebench")
    assert task is not None
    assert task.sandbox is not None  # Should use Docker sandbox
```

### T2: BigCodeBench-Hard Task Creation
**File**: `tests/test_cli.py`
**Function**: `test_get_benchmark_task_bigcodebench_hard`

```python
def test_get_benchmark_task_bigcodebench_hard():
    """Verify bigcodebench_hard task can be created."""
    task = _get_benchmark_task("bigcodebench_hard")
    assert task is not None
    # Should have subset or version for hard problems
```

### T3: Analyze Failures - Single Run
**File**: `tests/test_cli.py`
**Function**: `test_analyze_failures_single_run`

```python
def test_analyze_failures_single_run(tmp_path, mock_episodes):
    """Test extracting failures from a single run."""
    # Create mock run directory with failed episodes
    run_dir = tmp_path / "eval_logs" / "runs" / "test_run"
    run_dir.mkdir(parents=True)

    # Write mock episodes (some passed, some failed)
    episodes_dir = run_dir / "episodes"
    episodes_dir.mkdir()

    # Episode 1: passed
    (episodes_dir / "1.json").write_text('{"sample_id": 1, "outcome": {"passed": true}}')
    # Episode 2: failed
    (episodes_dir / "2.json").write_text('{"sample_id": 2, "outcome": {"passed": false}}')
    # Episode 3: failed
    (episodes_dir / "3.json").write_text('{"sample_id": 3, "outcome": {"passed": false}}')

    result = runner.invoke(cli, ["analyze-failures", "test_run", "--output", str(tmp_path / "fail_set.json")])

    assert result.exit_code == 0
    fail_set = json.loads((tmp_path / "fail_set.json").read_text())
    assert fail_set["sample_ids"] == [2, 3]
```

### T4: Analyze Failures - Intersection
**File**: `tests/test_cli.py`
**Function**: `test_analyze_failures_intersection`

```python
def test_analyze_failures_intersection(tmp_path):
    """Test intersection of failures across multiple runs."""
    # Run 1 failures: [2, 3, 5]
    # Run 2 failures: [3, 4, 5]
    # Intersection: [3, 5]

    # Setup mock runs...

    result = runner.invoke(cli, [
        "analyze-failures", "run1", "run2",
        "--intersect", "--output", str(tmp_path / "intersect.json")
    ])

    assert result.exit_code == 0
    fail_set = json.loads((tmp_path / "intersect.json").read_text())
    assert set(fail_set["sample_ids"]) == {3, 5}
```

### T5: Fail Set JSON Format
**File**: `tests/test_cli.py`
**Function**: `test_fail_set_json_format`

```python
def test_fail_set_json_format(tmp_path):
    """Test that fail set JSON has required fields."""
    # Create and extract fail set
    # ...

    fail_set = json.loads((tmp_path / "fail_set.json").read_text())

    # Required fields
    assert "source_runs" in fail_set
    assert "sample_ids" in fail_set
    assert isinstance(fail_set["sample_ids"], list)

    # Optional fields
    if "mode" in fail_set:
        assert fail_set["mode"] in ["union", "intersect"]
```

### T6: Config DOCKER_REQUIRED
**File**: `tests/test_config.py`
**Function**: `test_docker_required_includes_bigcodebench`

```python
def test_docker_required_includes_bigcodebench():
    """Verify BigCodeBench is in DOCKER_REQUIRED set."""
    from eval.config import BenchmarkRequirements

    assert BenchmarkRequirements.requires_docker("bigcodebench")
    assert BenchmarkRequirements.requires_docker("bigcodebench_hard")
```

## Integration Tests

### T7: Sample IDs from Fail Set
**File**: `tests/test_cli.py`
**Function**: `test_run_with_fail_set_sample_ids`

```python
def test_run_with_fail_set_sample_ids(tmp_path):
    """Test that --sample-ids works with fail set JSON format."""
    # Create fail set JSON
    fail_set = {
        "source_runs": ["previous_run"],
        "sample_ids": [1, 2, 3]
    }
    fail_set_path = tmp_path / "fail_set.json"
    fail_set_path.write_text(json.dumps(fail_set))

    # Verify it parses correctly
    # (Mock the actual evaluation, just test parsing)
```

### T8: End-to-End Fail Set Workflow
**File**: `tests/test_cli.py`
**Function**: `test_fail_set_workflow_e2e`

```python
@pytest.mark.integration
def test_fail_set_workflow_e2e():
    """End-to-end test of fail set workflow (requires Docker)."""
    # 1. Run small benchmark
    # 2. Analyze failures
    # 3. Run again with fail set
    # This test is slow and requires Docker, mark as integration
```

## Edge Cases

### T9: Empty Fail Set
**File**: `tests/test_cli.py`
**Function**: `test_analyze_failures_all_passed`

```python
def test_analyze_failures_all_passed(tmp_path):
    """Test behavior when all samples passed (no failures)."""
    # All episodes have passed: true

    result = runner.invoke(cli, ["analyze-failures", "all_passed_run"])

    assert result.exit_code == 0
    # Should produce empty fail set or warning
```

### T10: Run Not Found
**File**: `tests/test_cli.py`
**Function**: `test_analyze_failures_run_not_found`

```python
def test_analyze_failures_run_not_found():
    """Test error handling for non-existent run."""
    result = runner.invoke(cli, ["analyze-failures", "nonexistent_run"])

    assert result.exit_code != 0
    assert "not found" in result.output.lower()
```

## Smoke Tests (Manual)

### S1: BigCodeBench with Docker
```bash
# Requires Docker running
socrates-eval run bigcodebench --solver baseline --samples 3
# Expected: Completes without error, shows pass rate
```

### S2: Fail Set Creation
```bash
# After running S1
socrates-eval analyze-failures <run_id_from_S1> --output test_fail.json
cat test_fail.json
# Expected: JSON with sample_ids array
```

### S3: Run with Fail Set
```bash
socrates-eval run bigcodebench --solver baseline --sample-ids test_fail.json
# Expected: Only runs samples in fail set
```

## Test Data Requirements

- Mock episodes with `outcome.passed` field
- Multiple mock runs for intersection tests
- BigCodeBench dataset available on HuggingFace
- Docker running for smoke tests
