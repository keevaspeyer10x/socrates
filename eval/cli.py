"""Command-line interface for Socrates evaluation framework."""

import sys
from pathlib import Path
from typing import Optional

import click

from .config import APIKeyManager, BenchmarkRequirements, mask_api_key
from .preflight import run_preflight, format_preflight_report
from .state import EvalState


# Default paths
STATE_FILE = Path(".eval_state.json")
LOGS_DIR = Path("eval_logs")


@click.group()
@click.version_option(version="0.1.0", prog_name="socrates-eval")
def cli():
    """Socrates Evaluation Framework - Compare AI solvers on benchmarks."""
    pass


@cli.command()
def preflight():
    """Check environment readiness (Docker, API keys, etc.)."""
    result = run_preflight()
    click.echo(format_preflight_report(result))

    if not result.all_ok:
        sys.exit(1)


@cli.command()
def status():
    """Show current evaluation state."""
    state = EvalState.load(STATE_FILE)

    click.echo(f"Phase: {state.phase}")
    if state.current_run_id:
        click.echo(f"Run ID: {state.current_run_id}")
        click.echo(f"Benchmark: {state.current_benchmark}")
        click.echo(f"Solver: {state.current_solver}")
        click.echo(f"Progress: {state.samples_completed}/{state.samples_total}")
    else:
        click.echo("No active run")


@cli.command()
@click.argument("benchmark")
@click.option("--solver", default="baseline", help="Solver to use")
@click.option("--model", default="anthropic/claude-opus-4-5-20251101", help="Model for evaluation")
@click.option("--samples", type=int, default=None, help="Limit number of samples")
@click.option("--sample-ids", type=str, default=None, help="JSON file with sample indices or comma-separated IDs")
@click.option("--solver-mode", type=str, default="baseline", help="Solver mode (baseline, rigor, deep) for minds solver")
@click.option("--synthesizer", type=str, default=None, help="Synthesizer model for minds solver (default: same as model)")
def run(benchmark: str, solver: str, model: str, samples: Optional[int], sample_ids: Optional[str], solver_mode: str, synthesizer: Optional[str]):
    """Run evaluation on a benchmark.

    BENCHMARK is the name of the benchmark (e.g., gsm8k, mmlu, swe_bench).
    """
    # Preflight checks
    preflight_result = run_preflight([model])

    if not preflight_result.all_ok:
        click.echo("Preflight checks failed. Run 'socrates-eval preflight' for details.")
        sys.exit(1)

    # Check benchmark availability
    if BenchmarkRequirements.requires_docker(benchmark):
        if benchmark not in preflight_result.ready_benchmarks:
            click.echo(f"Error: {benchmark} requires Docker, which is not available.")
            click.echo("Available benchmarks: " + ", ".join(preflight_result.ready_benchmarks[:5]))
            sys.exit(1)

    # Check API key
    key_manager = APIKeyManager()
    if not key_manager.get_key(model.split("/")[0] if "/" in model else "anthropic"):
        click.echo(f"Error: No API key for {model}")
        click.echo("Set the appropriate environment variable or create a .env file.")
        sys.exit(1)

    # Generate run ID
    from datetime import datetime
    run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{benchmark}_{solver}"

    # Parse sample IDs if provided (can be string IDs or integers)
    parsed_sample_ids: Optional[list[str | int]] = None
    if sample_ids:
        if sample_ids.endswith('.json'):
            import json
            parsed_sample_ids = json.loads(Path(sample_ids).read_text())
        else:
            # Try to parse as integers, otherwise keep as strings
            raw_ids = [x.strip() for x in sample_ids.split(',')]
            try:
                parsed_sample_ids = [int(x) for x in raw_ids]
            except ValueError:
                parsed_sample_ids = raw_ids

    click.echo(f"Starting evaluation: {benchmark}")
    click.echo(f"  Solver: {solver}")
    click.echo(f"  Model: {model}")
    if parsed_sample_ids:
        click.echo(f"  Samples: {len(parsed_sample_ids)} (custom selection)")
    else:
        click.echo(f"  Samples: {samples or 'all'}")
    click.echo(f"  Run ID: {run_id}")
    click.echo()

    # Update state
    state = EvalState.load(STATE_FILE)
    state.start_run(run_id, benchmark, solver, len(parsed_sample_ids) if parsed_sample_ids else (samples or 0))
    state.save(STATE_FILE)

    # Run evaluation with try...finally for state cleanup (LEARNINGS recommendation)
    try:
        _run_evaluation(benchmark, solver, model, samples, run_id, parsed_sample_ids, solver_mode, synthesizer)
        state.finish_run()
        state.save(STATE_FILE)

        click.echo()
        click.echo(f"Evaluation complete. View results with: socrates-eval results {run_id}")
        click.echo(f"Extract lessons with: socrates-eval learn {run_id}")
    except Exception as e:
        click.echo(f"Error: {e}")
        sys.exit(1)
    finally:
        # Always reset state on exit to prevent stuck state
        if state.phase != "IDLE":
            state.phase = "IDLE"
            state.save(STATE_FILE)


def _run_evaluation(
    benchmark: str,
    solver: str,
    model: str,
    samples: Optional[int],
    run_id: str,
    sample_ids: Optional[list[str | int]] = None,
    solver_mode: str = "baseline",
    synthesizer_model: Optional[str] = None
):
    """Internal function to run evaluation."""
    from inspect_ai import eval as inspect_eval
    from inspect_ai.log import read_eval_log

    from .solvers import get_solver
    from .adapters import InspectAdapter

    # Get the benchmark task
    task = _get_benchmark_task(benchmark)

    # Create log directory
    log_dir = LOGS_DIR / "runs" / run_id
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get the solver if not using baseline
    # Inspect AI expects a callable decorated with @solver
    inspect_solver = None
    if solver != "baseline":
        from inspect_ai.solver import solver as solver_decorator

        solver_class = get_solver(solver)
        # Pass mode to minds solver
        if solver == "minds":
            kwargs = {"mode": solver_mode}
            if synthesizer_model:
                kwargs["synthesizer_model"] = synthesizer_model
            solver_instance = solver_class(**kwargs)
            synth_info = f", synthesizer={synthesizer_model}" if synthesizer_model else ""
            click.echo(f"Using solver: {solver_instance.name} (mode={solver_mode}{synth_info})")
        else:
            solver_instance = solver_class()
            click.echo(f"Using solver: {solver_instance.name}")

        # Create an Inspect-compatible solver using the @solver decorator
        # The decorator returns a factory function. Calling it returns the actual
        # solver function with registry_params set (required by Inspect AI).
        @solver_decorator(name=solver_instance.name)
        def custom_solver():
            async def solve(state, generate):
                return await solver_instance.solve(state, generate)
            return solve

        inspect_solver = custom_solver()  # Call it to get solver with registry_params

    # Run Inspect evaluation
    click.echo("Running Inspect evaluation...")
    results = inspect_eval(
        task,
        model=model,
        solver=inspect_solver,
        limit=samples if not sample_ids else None,
        sample_id=sample_ids,
        log_dir=str(log_dir / "inspect_logs"),
    )

    # Find and process the log
    inspect_log_dir = log_dir / "inspect_logs"
    log_files = list(inspect_log_dir.glob("*.eval")) + list(inspect_log_dir.glob("*.json"))

    if not log_files:
        click.echo("Warning: No evaluation log found")
        return

    # Extract episodes
    click.echo("Extracting episodes...")
    eval_log = read_eval_log(log_files[0])
    adapter = InspectAdapter()
    episodes = adapter.extract_episodes(eval_log, run_id)

    # Save episodes
    episodes_dir = log_dir / "episodes"
    episodes_dir.mkdir(exist_ok=True)
    for episode in episodes:
        episode.save(episodes_dir / f"{episode.sample_id}.json")

    # Generate summary
    passed = sum(1 for e in episodes if e.outcome.get("passed"))
    failed = len(episodes) - passed
    total_cost = sum(e.cost.get("usd", 0) for e in episodes)

    from .state import RunSummary
    summary = RunSummary(
        run_id=run_id,
        benchmark=benchmark,
        solver=solver,
        total_samples=len(episodes),
        passed=passed,
        failed=failed,
        pass_rate=passed / len(episodes) if episodes else 0,
        total_cost_usd=total_cost,
    )

    # Save summary
    (log_dir / "summary.json").write_text(summary.to_json())

    click.echo(f"Results: {passed}/{len(episodes)} passed ({summary.pass_rate:.1%})")
    click.echo(f"Cost: ${total_cost:.4f}")


def _get_benchmark_task(benchmark: str):
    """Get Inspect task for a benchmark."""
    benchmark = benchmark.lower().replace("-", "_").replace("human_eval", "humaneval")

    if benchmark == "gsm8k":
        from inspect_evals.gsm8k import gsm8k
        return gsm8k(fewshot=0)
    elif benchmark == "mmlu":
        from inspect_evals.mmlu import mmlu
        return mmlu()
    elif benchmark in ("swe_bench", "swe_bench_verified"):
        from inspect_evals.swe_bench import swe_bench
        return swe_bench()
    elif benchmark == "humaneval":
        from inspect_evals.humaneval import humaneval
        task = humaneval(sandbox="local")  # Use local sandbox (no Docker)
        task.epochs = 5  # Default: 5 epochs for pass@k metrics
        return task
    elif benchmark == "humaneval_fast":
        from inspect_evals.humaneval import humaneval
        task = humaneval(sandbox="local")  # Use local sandbox (no Docker)
        task.epochs = 1  # Fast mode: 1 epoch for rapid iteration
        return task
    elif benchmark == "mbpp":
        from inspect_evals.mbpp import mbpp
        from inspect_ai.util._sandbox.environment import SandboxEnvironmentSpec
        task = mbpp()  # Uses default temperature=0.5
        task.sandbox = SandboxEnvironmentSpec(type="local")  # Use local sandbox (no Docker)
        return task
    elif benchmark == "bigcodebench":
        from inspect_evals.bigcodebench import bigcodebench
        return bigcodebench()  # Uses Docker sandbox by default
    elif benchmark in ("gpqa", "gpqa_diamond"):
        from inspect_evals.gpqa import gpqa_diamond
        # Default: 4 epochs, chain-of-thought enabled
        # Use 1 epoch for faster iteration
        return gpqa_diamond(cot=True, epochs=1)
    elif benchmark == "bigcodebench_hard":
        # BigCodeBench-Hard requires loading from bigcode/bigcodebench-hard dataset
        # Since inspect_evals bigcodebench() loads from bigcode/bigcodebench,
        # we need to create a custom task that loads from the hard dataset
        from inspect_ai import Task
        from inspect_ai.dataset import Sample
        from inspect_evals.bigcodebench.bigcodebench import (
            get_record_to_sample, verify, INSTRUCTION_PROMPT
        )
        from inspect_evals.utils.huggingface import load_dataset
        from inspect_evals.utils import get_images_from_compose, force_build_or_pull_docker_image, DockerHandling
        from pathlib import Path
        import inspect_evals.bigcodebench as bigcodebench_module

        # Load from the hard dataset
        bigcode_hard = load_dataset("bigcode/bigcodebench-hard", split="v0.1.2")
        record_to_sample = get_record_to_sample(INSTRUCTION_PROMPT)
        dataset = [record_to_sample(record) for record in bigcode_hard]

        # Use same Docker setup as regular bigcodebench
        module_dir = Path(bigcodebench_module.__file__).parent
        compose_file = module_dir / "compose.yaml"
        image_name = get_images_from_compose(compose_file)
        dockerfile_fp = module_dir / "Dockerfile"

        assert len(image_name) == 1, "Expected only 1 service"
        force_build_or_pull_docker_image(
            image=image_name[0],
            dockerfile_path=dockerfile_fp,
            docker_handling=DockerHandling.DEFAULT,
        )

        return Task(
            dataset=dataset,
            scorer=verify(),
            sandbox=("docker", str(compose_file)),
            version="1.0.0",
        )
    else:
        raise ValueError(f"Unknown benchmark: {benchmark}")


@cli.command()
@click.argument("run_id", required=False)
def results(run_id: Optional[str]):
    """View evaluation results."""
    if run_id:
        _show_run_results(run_id)
    else:
        _list_runs()


def _show_run_results(run_id: str):
    """Show detailed results for a specific run."""
    run_dir = LOGS_DIR / "runs" / run_id

    if not run_dir.exists():
        click.echo(f"Run not found: {run_id}")
        sys.exit(1)

    summary_file = run_dir / "summary.json"
    if summary_file.exists():
        import json
        summary = json.loads(summary_file.read_text())

        click.echo(f"Run: {summary['run_id']}")
        click.echo(f"Benchmark: {summary['benchmark']}")
        click.echo(f"Solver: {summary['solver']}")
        click.echo()
        click.echo(f"Samples: {summary['total_samples']}")
        click.echo(f"Passed: {summary['passed']} ({summary['pass_rate']:.1%})")
        click.echo(f"Failed: {summary['failed']}")
        click.echo(f"Cost: ${summary['total_cost_usd']:.4f}")
    else:
        click.echo(f"No summary found for run: {run_id}")


def _list_runs():
    """List all evaluation runs."""
    runs_dir = LOGS_DIR / "runs"
    if not runs_dir.exists():
        click.echo("No runs found.")
        return

    runs = sorted(runs_dir.iterdir(), reverse=True)
    if not runs:
        click.echo("No runs found.")
        return

    click.echo("Recent runs:")
    for run_dir in runs[:10]:
        summary_file = run_dir / "summary.json"
        if summary_file.exists():
            import json
            summary = json.loads(summary_file.read_text())
            click.echo(f"  {summary['run_id']}: {summary['pass_rate']:.1%} ({summary['benchmark']})")
        else:
            click.echo(f"  {run_dir.name}: (no summary)")


@cli.command()
def solvers():
    """List available solvers."""
    from .solvers import list_solvers

    click.echo("Available solvers:")
    for name in list_solvers():
        click.echo(f"  - {name}")


@cli.command()
@click.argument("run_a_id")
@click.argument("run_b_id")
def compare(run_a_id: str, run_b_id: str):
    """Compare two evaluation runs with statistical analysis.

    RUN_A_ID and RUN_B_ID are the run identifiers to compare.
    """
    import json
    from .compare import compare_runs, wilson_score_interval
    from .state import RunSummary

    # Load run A
    run_a_dir = LOGS_DIR / "runs" / run_a_id
    if not run_a_dir.exists():
        click.echo(f"Run not found: {run_a_id}")
        sys.exit(1)

    # Load run B
    run_b_dir = LOGS_DIR / "runs" / run_b_id
    if not run_b_dir.exists():
        click.echo(f"Run not found: {run_b_id}")
        sys.exit(1)

    # Load summaries (filter out computed properties not in the dataclass)
    summary_a = json.loads((run_a_dir / "summary.json").read_text())
    summary_b = json.loads((run_b_dir / "summary.json").read_text())

    # Remove computed properties that shouldn't be passed to __init__
    for key in ['cost_per_success']:
        summary_a.pop(key, None)
        summary_b.pop(key, None)

    run_a = RunSummary(**summary_a)
    run_b = RunSummary(**summary_b)

    # Load episodes
    episodes_a = _load_episodes(run_a_dir / "episodes")
    episodes_b = _load_episodes(run_b_dir / "episodes")

    # Run comparison
    result = compare_runs(run_a, run_b, episodes_a, episodes_b)

    # Display results
    click.echo("=" * 60)
    click.echo("COMPARISON: {} vs {}".format(run_a_id, run_b_id))
    click.echo("=" * 60)
    click.echo()

    # Run A
    click.echo(f"Run A: {result['run_a']['solver']}")
    click.echo(f"  Pass rate: {result['run_a']['pass_rate']:.1%} ({result['run_a']['passed']}/{result['run_a']['total']})")
    click.echo(f"  95% CI: [{result['wilson_ci_a'][0]:.1%}, {result['wilson_ci_a'][1]:.1%}]")
    click.echo()

    # Run B
    click.echo(f"Run B: {result['run_b']['solver']}")
    click.echo(f"  Pass rate: {result['run_b']['pass_rate']:.1%} ({result['run_b']['passed']}/{result['run_b']['total']})")
    click.echo(f"  95% CI: [{result['wilson_ci_b'][0]:.1%}, {result['wilson_ci_b'][1]:.1%}]")
    click.echo()

    # McNemar test
    mcnemar = result['mcnemar']
    if mcnemar.get('p_value') is not None:
        click.echo("McNemar's Test (paired comparison):")
        click.echo(f"  p-value: {mcnemar['p_value']:.4f}")
        click.echo(f"  Significant: {'Yes' if mcnemar['significant'] else 'No'} (alpha=0.05)")
        click.echo(f"  A better on {mcnemar['n_a_better']} samples, B better on {mcnemar['n_b_better']}")
    else:
        click.echo("McNemar's Test: Not applicable (no common samples)")
    click.echo()

    # Cost efficiency
    cost = result['cost_efficiency']
    click.echo("Cost Efficiency:")
    click.echo(f"  A: ${cost['run_a_cost_per_sample']:.4f}/sample, ${cost['run_a_cost_per_success']:.4f}/success")
    click.echo(f"  B: ${cost['run_b_cost_per_sample']:.4f}/sample, ${cost['run_b_cost_per_success']:.4f}/success")


@cli.command()
@click.argument("run_id")
def analyze(run_id: str):
    """Analyze a single run with statistics and failure breakdown.

    RUN_ID is the run identifier to analyze.
    """
    import json
    from .compare import wilson_score_interval, analyze_failures
    from .state import RunSummary

    # Load run
    run_dir = LOGS_DIR / "runs" / run_id
    if not run_dir.exists():
        click.echo(f"Run not found: {run_id}")
        sys.exit(1)

    # Load summary
    summary_data = json.loads((run_dir / "summary.json").read_text())
    summary = RunSummary(**summary_data)

    # Load episodes
    episodes = _load_episodes(run_dir / "episodes")

    # Calculate Wilson CI
    lower, upper = wilson_score_interval(summary.passed, summary.total_samples)

    # Analyze failures
    failure_breakdown = analyze_failures(episodes)

    # Display results
    click.echo("=" * 60)
    click.echo(f"ANALYSIS: {run_id}")
    click.echo("=" * 60)
    click.echo()

    click.echo(f"Benchmark: {summary.benchmark}")
    click.echo(f"Solver: {summary.solver}")
    click.echo()

    click.echo("Results:")
    click.echo(f"  Pass rate: {summary.pass_rate:.1%} ({summary.passed}/{summary.total_samples})")
    click.echo(f"  95% CI: [{lower:.1%}, {upper:.1%}]")
    click.echo()

    click.echo("Cost:")
    click.echo(f"  Total: ${summary.total_cost_usd:.4f}")
    click.echo(f"  Per sample: ${summary.total_cost_usd / summary.total_samples:.4f}" if summary.total_samples > 0 else "  Per sample: N/A")
    click.echo(f"  Per success: ${summary.cost_per_success:.4f}" if summary.passed > 0 else "  Per success: N/A")
    click.echo()

    click.echo("Failure Breakdown:")
    total_failures = sum(failure_breakdown.values())
    if total_failures > 0:
        for mode, count in sorted(failure_breakdown.items(), key=lambda x: -x[1]):
            if count > 0:
                pct = count / total_failures * 100
                click.echo(f"  {mode}: {count} ({pct:.1f}%)")
    else:
        click.echo("  No failures!")


def _load_episodes(episodes_dir: Path) -> list[dict]:
    """Load all episodes from a directory."""
    import json

    episodes = []
    if episodes_dir.exists():
        for ep_file in episodes_dir.glob("*.json"):
            episodes.append(json.loads(ep_file.read_text()))
    return episodes


# =============================================================================
# Learning Commands (Phase 4)
# =============================================================================

@cli.command()
@click.argument("run_id")
@click.option("--llm", is_flag=True, help="Use LLM for deeper lesson extraction (costs tokens)")
def learn(run_id: str, llm: bool):
    """Extract lessons from an evaluation run.

    RUN_ID is the run identifier to extract lessons from.

    By default, uses pattern-based extraction (free, fast).
    Use --llm for deeper analysis using Claude (costs tokens).
    """
    import json
    from .learning import LearningEngine

    # Load run
    run_dir = LOGS_DIR / "runs" / run_id
    if not run_dir.exists():
        click.echo(f"Run not found: {run_id}")
        sys.exit(1)

    # Load summary
    summary_file = run_dir / "summary.json"
    if not summary_file.exists():
        click.echo(f"No summary found for run: {run_id}")
        sys.exit(1)

    summary = json.loads(summary_file.read_text())

    # Load episodes
    episodes = _load_episodes(run_dir / "episodes")
    if not episodes:
        click.echo("No episodes found to analyze.")
        sys.exit(1)

    method = "LLM-based" if llm else "pattern-based"
    click.echo(f"Analyzing {len(episodes)} episodes from run {run_id} ({method})...")
    click.echo()

    # Extract lessons
    engine = LearningEngine(lessons_dir=LOGS_DIR / "lessons")
    candidates = engine.extract_lessons_from_episodes(
        episodes,
        run_id,
        summary["benchmark"],
        summary["solver"],
        use_llm=llm
    )

    if not candidates:
        click.echo("No new lessons extracted (no patterns found or all duplicates).")
        return

    click.echo(f"Extracted {len(candidates)} candidate lesson(s):")
    click.echo()
    for i, lesson in enumerate(candidates, 1):
        click.echo(f"{i}. [{lesson.confidence:.0%} confidence] {lesson.what}")
        click.echo(f"   Why: {lesson.why}")
        click.echo(f"   Triggers: {', '.join(lesson.triggers)}")
        click.echo()

    click.echo("Review candidates with: socrates-eval lessons --candidates")
    click.echo("Approve a lesson with:  socrates-eval lessons --approve <lesson_id>")


@cli.command()
@click.option("--candidates", is_flag=True, help="Show candidate lessons pending approval")
@click.option("--approve", type=str, help="Approve a candidate lesson by ID")
@click.option("--reject", type=str, help="Reject a candidate lesson by ID")
@click.option("--stats", is_flag=True, help="Show learning statistics")
def lessons(candidates: bool, approve: Optional[str], reject: Optional[str], stats: bool):
    """View and manage lessons.

    Shows approved lessons by default. Use flags to manage candidates.
    """
    from .learning import LearningEngine

    engine = LearningEngine(lessons_dir=LOGS_DIR / "lessons")

    # Handle approval
    if approve:
        lesson = engine.approve_candidate(approve)
        if lesson:
            click.echo(f"Approved lesson: {lesson.lesson_id}")
            click.echo(f"  What: {lesson.what}")
        else:
            click.echo(f"Candidate not found: {approve}")
            sys.exit(1)
        return

    # Handle rejection
    if reject:
        if engine.reject_candidate(reject):
            click.echo(f"Rejected and deleted: {reject}")
        else:
            click.echo(f"Candidate not found: {reject}")
            sys.exit(1)
        return

    # Show statistics
    if stats:
        stat = engine.get_statistics()
        click.echo("Learning System Statistics:")
        click.echo(f"  Total lessons: {stat['total_lessons']}")
        click.echo(f"  Pending candidates: {stat['total_candidates']}")
        click.echo(f"  Approved: {stat['approved_lessons']}")
        click.echo(f"  Embedded: {stat['embedded_lessons']}")
        click.echo(f"  Archived: {stat['archived_lessons']}")
        click.echo()
        click.echo(f"  Avg confidence: {stat['avg_confidence']:.1%}")
        click.echo(f"  Avg success rate: {stat['avg_success_rate']:.1%}")
        click.echo(f"  Total applications: {stat['total_applications']}")
        return

    # Show candidates
    if candidates:
        candidate_list = engine.load_candidates()
        if not candidate_list:
            click.echo("No candidate lessons pending approval.")
            return

        click.echo(f"Candidate lessons ({len(candidate_list)} pending):")
        click.echo()
        for lesson in candidate_list:
            click.echo(f"ID: {lesson.lesson_id}")
            click.echo(f"  What: {lesson.what}")
            click.echo(f"  Why: {lesson.why}")
            click.echo(f"  Confidence: {lesson.confidence:.0%}")
            click.echo(f"  Triggers: {', '.join(lesson.triggers)}")
            click.echo(f"  Evidence: {len(lesson.episode_ids)} episode(s)")
            click.echo()
        return

    # Show approved lessons (default)
    lesson_list = engine.load_lessons()
    if not lesson_list:
        click.echo("No approved lessons yet.")
        click.echo("Run 'socrates-eval learn <run_id>' after an evaluation to extract lessons.")
        return

    click.echo(f"Approved lessons ({len(lesson_list)}):")
    click.echo()
    for lesson in lesson_list:
        status_marker = ""
        if lesson.status == "embedded":
            status_marker = " [EMBEDDED]"
        elif lesson.status == "archived":
            status_marker = " [ARCHIVED]"

        click.echo(f"ID: {lesson.lesson_id}{status_marker}")
        click.echo(f"  What: {lesson.what}")
        click.echo(f"  Why: {lesson.why}")
        click.echo(f"  Confidence: {lesson.confidence:.0%}")
        if lesson.application_count > 0:
            click.echo(f"  Applied: {lesson.application_count} time(s), {lesson.success_rate:.0%} success")
        click.echo()


# =============================================================================
# Fail Set Commands (Phase 5 - Issue #5)
# =============================================================================

@cli.command("analyze-failures")
@click.argument("run_ids", nargs=-1, required=True)
@click.option("--output", "-o", type=str, required=True, help="Output JSON file for fail set")
@click.option("--intersect", is_flag=True, help="Only include samples that failed in ALL runs")
def analyze_failures(run_ids: tuple[str, ...], output: str, intersect: bool):
    """Extract failed samples from evaluation runs.

    RUN_IDS are one or more run identifiers to analyze.

    Use --intersect to find problems that failed across ALL specified runs
    (useful for finding the "hardest" problems that multiple models fail).

    Example:
        socrates-eval analyze-failures run1 --output fail_set.json
        socrates-eval analyze-failures run1 run2 run3 --intersect --output hard_failures.json
    """
    import json

    all_failed_sets: list[set[int]] = []
    source_runs: list[str] = []

    for run_id in run_ids:
        run_dir = LOGS_DIR / "runs" / run_id
        if not run_dir.exists():
            click.echo(f"Run not found: {run_id}")
            sys.exit(1)

        episodes = _load_episodes(run_dir / "episodes")
        if not episodes:
            click.echo(f"No episodes found in run: {run_id}")
            sys.exit(1)

        # Extract failed sample IDs
        failed_ids = set()
        for ep in episodes:
            outcome = ep.get("outcome", {})
            if not outcome.get("passed", False):
                sample_id = ep.get("sample_id")
                if sample_id is not None:
                    # Handle both int and string sample IDs
                    if isinstance(sample_id, int):
                        failed_ids.add(sample_id)
                    else:
                        try:
                            failed_ids.add(int(sample_id))
                        except (ValueError, TypeError):
                            # Keep as-is if not convertible to int
                            failed_ids.add(sample_id)

        all_failed_sets.append(failed_ids)
        source_runs.append(run_id)
        click.echo(f"Run {run_id}: {len(failed_ids)} failures out of {len(episodes)} samples")

    # Compute final fail set
    if intersect and len(all_failed_sets) > 1:
        # Intersection: samples that failed in ALL runs
        final_failed = all_failed_sets[0]
        for failed_set in all_failed_sets[1:]:
            final_failed = final_failed.intersection(failed_set)
        mode = "intersect"
        click.echo(f"\nIntersection of failures across {len(run_ids)} runs: {len(final_failed)} samples")
    else:
        # Union: all unique failures (or single run)
        final_failed = set()
        for failed_set in all_failed_sets:
            final_failed = final_failed.union(failed_set)
        mode = "union" if len(run_ids) > 1 else "single"

    # Create fail set JSON
    fail_set = {
        "source_runs": source_runs,
        "mode": mode,
        "sample_ids": sorted(list(final_failed)),  # Sort for deterministic output
    }

    # Write output
    output_path = Path(output)
    output_path.write_text(json.dumps(fail_set, indent=2))
    click.echo(f"\nFail set written to: {output}")
    click.echo(f"Total failed samples: {len(final_failed)}")

    if final_failed:
        click.echo(f"\nUse with: socrates-eval run <benchmark> --sample-ids {output}")


# =============================================================================
# LLM-as-Judge Commands
# =============================================================================

@cli.command("judge")
@click.argument("prompt")
@click.argument("response")
@click.option("--rubric", "-r", type=str, default=None, help="Path to YAML rubric file")
@click.option("--model", "-m", type=str, default="anthropic/claude-opus-4-5-20251101", help="Judge model")
@click.option("--threshold", type=float, default=0.6, help="Pass threshold (0.0-1.0)")
@click.option("--multi-judge", is_flag=True, help="Use multi-judge ensemble")
def judge_cmd(prompt: str, response: str, rubric: Optional[str], model: str, threshold: float, multi_judge: bool):
    """Evaluate a response using LLM-as-Judge.

    PROMPT is the original question/prompt.
    RESPONSE is the AI response to evaluate.

    Example:
        socrates-eval judge "How should I design a cache?" "Use Redis with TTL..."
    """
    import asyncio

    from .judge import load_rubric, JudgeScorer, MultiJudge

    # Load rubric if specified
    rubric_obj = None
    if rubric:
        rubric_obj = load_rubric(rubric)
        click.echo(f"Using rubric: {rubric_obj.name} v{rubric_obj.version}")

    if multi_judge:
        click.echo("Running multi-judge evaluation...")
        judge = MultiJudge(
            rubric=rubric_obj,
            pass_threshold=threshold,
        )
        result = asyncio.run(judge.score(prompt, response))

        click.echo(f"\n{'=' * 60}")
        click.echo("MULTI-JUDGE EVALUATION")
        click.echo(f"{'=' * 60}\n")

        click.echo(f"Overall Score: {result.weighted_score:.2f}")
        click.echo(f"Passed: {'Yes' if result.passed else 'No'} (threshold: {threshold})")
        click.echo(f"Agreement: {result.agreement:.1%}")
        click.echo(f"High Variance: {'Yes' if result.high_variance else 'No'}")
        click.echo(f"Needs Human Review: {'Yes' if result.needs_human_review else 'No'}")
        click.echo(f"Aggregation: {result.aggregation_method}")
        click.echo()

        click.echo("Individual Judge Scores:")
        for individual in result.individual_scores:
            model_name = individual.get("judge_model", "unknown")
            if "error" in individual:
                click.echo(f"  {model_name}: ERROR - {individual['error']}")
            else:
                score = individual.get("weighted_score", 0.0)
                click.echo(f"  {model_name}: {score:.2f}")
    else:
        click.echo(f"Running single-judge evaluation with {model}...")
        judge = JudgeScorer(
            rubric=rubric_obj,
            judge_model=model,
            pass_threshold=threshold,
        )
        result = asyncio.run(judge.score(prompt, response))

        click.echo(f"\n{'=' * 60}")
        click.echo("JUDGE EVALUATION")
        click.echo(f"{'=' * 60}\n")

        click.echo(f"Weighted Score: {result['weighted_score']:.2f}")
        click.echo(f"Passed: {'Yes' if result['passed'] else 'No'} (threshold: {threshold})")
        click.echo(f"Confidence: {result['confidence']:.1%}")
        click.echo()

        if result.get("scores"):
            click.echo("Per-Criterion Scores:")
            for criterion, data in result["scores"].items():
                score = data.get("score", "N/A")
                click.echo(f"  {criterion}: {score}")
                if data.get("justification"):
                    click.echo(f"    Justification: {data['justification'][:100]}...")
            click.echo()

        click.echo(f"Overall Assessment:\n  {result.get('overall_assessment', 'N/A')}")

        if result.get("suggestions"):
            click.echo("\nSuggestions for improvement:")
            for suggestion in result["suggestions"]:
                click.echo(f"  - {suggestion}")


@cli.command("compare-responses")
@click.argument("prompt")
@click.argument("response_a")
@click.argument("response_b")
@click.option("--rubric", "-r", type=str, default=None, help="Path to YAML rubric file")
@click.option("--model", "-m", type=str, default="anthropic/claude-opus-4-5-20251101", help="Judge model")
@click.option("--label-a", type=str, default="A", help="Label for response A")
@click.option("--label-b", type=str, default="B", help="Label for response B")
def compare_responses_cmd(
    prompt: str,
    response_a: str,
    response_b: str,
    rubric: Optional[str],
    model: str,
    label_a: str,
    label_b: str,
):
    """Compare two responses head-to-head using pairwise evaluation.

    PROMPT is the original question/prompt.
    RESPONSE_A and RESPONSE_B are the two responses to compare.

    Example:
        socrates-eval compare-responses "Explain recursion" "Recursion is..." "A function that..."
    """
    import asyncio

    from .judge import load_rubric, PairwiseScorer

    # Load rubric if specified
    rubric_obj = None
    if rubric:
        rubric_obj = load_rubric(rubric)
        click.echo(f"Using rubric: {rubric_obj.name} v{rubric_obj.version}")

    click.echo(f"Running pairwise comparison with {model}...")
    comparer = PairwiseScorer(
        rubric=rubric_obj,
        judge_model=model,
        randomize_order=True,
    )

    result = asyncio.run(comparer.compare(
        prompt=prompt,
        response_1=response_a,
        response_2=response_b,
        label_1=label_a,
        label_2=label_b,
    ))

    click.echo(f"\n{'=' * 60}")
    click.echo("PAIRWISE COMPARISON")
    click.echo(f"{'=' * 60}\n")

    if result["winner"] == "tie":
        click.echo("Result: TIE")
    else:
        click.echo(f"Winner: {result['winner_label']}")

    click.echo(f"Confidence: {result['confidence']:.1%}")
    click.echo(f"Order Randomized: {'Yes (swapped)' if result['order_was_swapped'] else 'No'}")
    click.echo()

    if result.get("criteria_verdicts"):
        click.echo("Per-Criterion Winners:")
        for criterion, verdict in result["criteria_verdicts"].items():
            winner = verdict.get("winner", "N/A")
            click.echo(f"  {criterion}: {winner}")
            if verdict.get("explanation"):
                click.echo(f"    {verdict['explanation'][:80]}...")
        click.echo()

    click.echo(f"Explanation:\n  {result.get('explanation', 'N/A')}")


@cli.command("judge-file")
@click.argument("input_file", type=click.Path(exists=True))
@click.option("--output", "-o", type=str, required=True, help="Output JSON file for results")
@click.option("--rubric", "-r", type=str, default=None, help="Path to YAML rubric file")
@click.option("--multi-judge", is_flag=True, help="Use multi-judge ensemble")
@click.option("--threshold", type=float, default=0.6, help="Pass threshold (0.0-1.0)")
def judge_file_cmd(input_file: str, output: str, rubric: Optional[str], multi_judge: bool, threshold: float):
    """Evaluate multiple responses from a JSON file.

    INPUT_FILE should be a JSON file with format:
    [
        {"prompt": "...", "response": "...", "id": "optional_id"},
        ...
    ]

    Results are written to OUTPUT file.

    Example:
        socrates-eval judge-file responses.json --output scores.json --multi-judge
    """
    import asyncio
    import json

    from .judge import load_rubric, JudgeScorer, MultiJudge

    # Load input
    input_path = Path(input_file)
    samples = json.loads(input_path.read_text())

    if not isinstance(samples, list):
        click.echo("Error: Input file must contain a JSON array")
        sys.exit(1)

    click.echo(f"Loaded {len(samples)} samples from {input_file}")

    # Load rubric if specified
    rubric_obj = None
    if rubric:
        rubric_obj = load_rubric(rubric)
        click.echo(f"Using rubric: {rubric_obj.name} v{rubric_obj.version}")

    # Create judge
    if multi_judge:
        click.echo("Using multi-judge ensemble...")
        judge = MultiJudge(rubric=rubric_obj, pass_threshold=threshold)
    else:
        click.echo("Using single judge...")
        judge = JudgeScorer(rubric=rubric_obj, pass_threshold=threshold)

    # Evaluate all samples
    async def evaluate_all():
        results = []
        for i, sample in enumerate(samples):
            prompt = sample.get("prompt", "")
            response = sample.get("response", "")
            sample_id = sample.get("id", i)

            click.echo(f"  Evaluating sample {i + 1}/{len(samples)}...", nl=False)

            if multi_judge:
                result = await judge.score(prompt, response)
                results.append({
                    "id": sample_id,
                    "weighted_score": result.weighted_score,
                    "passed": result.passed,
                    "agreement": result.agreement,
                    "high_variance": result.high_variance,
                    "needs_human_review": result.needs_human_review,
                })
            else:
                result = await judge.score(prompt, response)
                results.append({
                    "id": sample_id,
                    "weighted_score": result["weighted_score"],
                    "passed": result["passed"],
                    "scores": result.get("scores", {}),
                    "confidence": result.get("confidence", 0.0),
                })

            click.echo(f" score={results[-1]['weighted_score']:.2f}")

        return results

    results = asyncio.run(evaluate_all())

    # Calculate summary stats
    passed_count = sum(1 for r in results if r["passed"])
    avg_score = sum(r["weighted_score"] for r in results) / len(results) if results else 0

    output_data = {
        "summary": {
            "total": len(results),
            "passed": passed_count,
            "pass_rate": passed_count / len(results) if results else 0,
            "avg_score": avg_score,
            "threshold": threshold,
            "multi_judge": multi_judge,
            "rubric": rubric_obj.name if rubric_obj else "default_reasoning",
        },
        "results": results,
    }

    # Write output
    output_path = Path(output)
    output_path.write_text(json.dumps(output_data, indent=2))

    click.echo(f"\n{'=' * 60}")
    click.echo("EVALUATION COMPLETE")
    click.echo(f"{'=' * 60}")
    click.echo(f"Total samples: {len(results)}")
    click.echo(f"Passed: {passed_count} ({passed_count / len(results):.1%})")
    click.echo(f"Average score: {avg_score:.2f}")
    click.echo(f"Results written to: {output}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
