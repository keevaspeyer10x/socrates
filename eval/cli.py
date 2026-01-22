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
@click.option("--model", default="anthropic/claude-sonnet-4-20250514", help="Model for evaluation")
@click.option("--samples", type=int, default=None, help="Limit number of samples")
def run(benchmark: str, solver: str, model: str, samples: Optional[int]):
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

    click.echo(f"Starting evaluation: {benchmark}")
    click.echo(f"  Solver: {solver}")
    click.echo(f"  Model: {model}")
    click.echo(f"  Samples: {samples or 'all'}")
    click.echo(f"  Run ID: {run_id}")
    click.echo()

    # Update state
    state = EvalState.load(STATE_FILE)
    state.start_run(run_id, benchmark, solver, samples or 0)
    state.save(STATE_FILE)

    # Run evaluation
    try:
        _run_evaluation(benchmark, solver, model, samples, run_id)
    except Exception as e:
        click.echo(f"Error: {e}")
        state.phase = "IDLE"
        state.save(STATE_FILE)
        sys.exit(1)

    # Update state
    state.finish_run()
    state.save(STATE_FILE)

    click.echo()
    click.echo(f"Evaluation complete. View results with: socrates-eval results {run_id}")


def _run_evaluation(benchmark: str, solver: str, model: str, samples: Optional[int], run_id: str):
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

    # Run Inspect evaluation
    click.echo("Running Inspect evaluation...")
    results = inspect_eval(
        task,
        model=model,
        limit=samples,
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
    benchmark = benchmark.lower().replace("-", "_")

    if benchmark == "gsm8k":
        from inspect_evals.gsm8k import gsm8k
        return gsm8k(fewshot=0)
    elif benchmark == "mmlu":
        from inspect_evals.mmlu import mmlu
        return mmlu()
    elif benchmark in ("swe_bench", "swe_bench_verified"):
        from inspect_evals.swe_bench import swe_bench
        return swe_bench()
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


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
