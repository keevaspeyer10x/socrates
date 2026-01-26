# E2E Test Cases for Phase 4-5

## Test Case 1: Run GSM8K Evaluation
**Command:** `socrates-eval run gsm8k --samples 5`
**Expected:** Evaluation completes, episodes logged to eval_logs/runs/

## Test Case 2: Pattern-Based Lesson Extraction
**Command:** `socrates-eval learn <run_id>`
**Expected:** Extracts 0+ lessons based on failure patterns (0 is valid if all pass)

## Test Case 3: View Lesson Statistics
**Command:** `socrates-eval lessons --stats`
**Expected:** Shows statistics without error

## Test Case 4: View Candidates
**Command:** `socrates-eval lessons --candidates`
**Expected:** Lists candidates or shows "No candidates"

## Test Case 5: Custom Solver Loading (Unit Test)
**Covered by:** `tests/test_learning.py::TestCustomSolverLoading`
**Expected:** All 4 tests pass

## Test Case 6: Lesson Injection (Unit Test)
**Covered by:** `tests/test_learning.py::TestBaselineSolverLessonInjection`
**Expected:** All 4 tests pass

## Test Case 7: Full Test Suite
**Command:** `pytest tests/`
**Expected:** 94 tests pass
