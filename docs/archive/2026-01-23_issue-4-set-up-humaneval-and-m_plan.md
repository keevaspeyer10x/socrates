# End-to-End Evaluation Test Plan for Phase 4-5

## Objective
Verify that the Phase 4-5 implementation (Learning Pipeline and Custom Solver Support) works correctly end-to-end.

## Test Scope

### 1. Run GSM8K Evaluation (5 samples)
- Use baseline solver
- Verify evaluation completes successfully
- Confirm episode logging works

### 2. Test Learning Pipeline (Phase 4)
- Run `socrates-eval learn <run_id>` on the evaluation
- Verify pattern-based lesson extraction
- Test lesson management commands:
  - `socrates-eval lessons --candidates`
  - `socrates-eval lessons --stats`
  - `socrates-eval lessons --approve <id>` (if candidates exist)

### 3. Test Custom Solver Loading (Phase 5)
- Create a minimal test solver
- Load it via `load_custom_solver()`
- Verify it can be instantiated with kwargs

### 4. Test Lesson Injection
- Verify BaselineSolver accepts `inject_lessons=True`
- Confirm lesson retrieval works with trigger matching

## Execution Plan
Sequential execution - each step depends on the previous:
1. Run evaluation -> generates episodes
2. Extract lessons -> needs episodes from step 1
3. Test CLI commands -> needs lessons from step 2
4. Verify custom solver loading -> independent

## Success Criteria
- Evaluation completes with 5 samples
- Learning pipeline extracts or reports "no patterns" (both valid)
- CLI commands execute without errors
- Custom solver loading works per unit tests
- All 94 existing tests continue to pass
