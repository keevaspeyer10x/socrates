"""Environment validation and preflight checks."""

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional

from .config import APIKeyManager, BenchmarkRequirements, mask_api_key


@dataclass
class CheckResult:
    """Result of a single preflight check."""
    ok: bool
    message: str
    version: Optional[str] = None


@dataclass
class PreflightResult:
    """Result of all preflight checks."""
    checks: dict[str, CheckResult]
    ready_benchmarks: list[str]
    blocked_benchmarks: list[str]

    @property
    def all_ok(self) -> bool:
        """True if all critical checks passed."""
        critical = ["python", "inspect"]
        return all(self.checks.get(c, CheckResult(False, "")).ok for c in critical)


def check_python_version() -> CheckResult:
    """Check Python version is 3.11+."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 11)
    message = f"Python {version}" if ok else f"Python {version} (requires 3.11+)"
    return CheckResult(ok=ok, message=message, version=version)


def check_inspect_installed() -> CheckResult:
    """Check if inspect-ai is installed."""
    try:
        import inspect_ai
        version = getattr(inspect_ai, "__version__", "unknown")
        return CheckResult(ok=True, message=f"inspect-ai {version}", version=version)
    except ImportError:
        return CheckResult(ok=False, message="inspect-ai not installed", version=None)


def check_docker_available() -> CheckResult:
    """Check if Docker daemon is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=15  # Increased for WSL/Docker Desktop
        )
        if result.returncode == 0:
            return CheckResult(ok=True, message="Docker available")
        return CheckResult(ok=False, message="Docker not running")
    except FileNotFoundError:
        return CheckResult(ok=False, message="Docker not installed")
    except subprocess.TimeoutExpired:
        return CheckResult(ok=False, message="Docker timeout")
    except Exception as e:
        return CheckResult(ok=False, message=f"Docker check failed: {e}")


def check_api_keys(models: Optional[list[str]] = None) -> CheckResult:
    """Check API key configuration."""
    manager = APIKeyManager()

    if models is None:
        # Check common providers
        models = [
            "anthropic/claude-sonnet",
            "openai/gpt-4o",
            "google/gemini",
        ]

    validation = manager.validate_for_models(models)
    configured = [m for m, ok in validation.items() if ok]
    missing = [m for m, ok in validation.items() if not ok]

    if not missing:
        return CheckResult(
            ok=True,
            message=f"All keys configured ({len(configured)} providers)"
        )
    elif configured:
        return CheckResult(
            ok=True,  # Partial is OK
            message=f"{len(configured)} configured, {len(missing)} missing"
        )
    else:
        return CheckResult(
            ok=False,
            message="No API keys configured"
        )


def run_preflight(models: Optional[list[str]] = None) -> PreflightResult:
    """Run all preflight checks."""
    checks = {
        "python": check_python_version(),
        "inspect": check_inspect_installed(),
        "docker": check_docker_available(),
        "api_keys": check_api_keys(models),
    }

    # Determine available benchmarks
    docker_ok = checks["docker"].ok
    ready = []
    blocked = []

    for benchmark in BenchmarkRequirements.all_benchmarks():
        if BenchmarkRequirements.requires_docker(benchmark):
            if docker_ok:
                ready.append(benchmark)
            else:
                blocked.append(benchmark)
        else:
            ready.append(benchmark)

    return PreflightResult(
        checks=checks,
        ready_benchmarks=sorted(ready),
        blocked_benchmarks=sorted(blocked),
    )


def get_available_benchmarks() -> list[str]:
    """Get list of benchmarks available in current environment."""
    result = run_preflight()
    return result.ready_benchmarks


def format_preflight_report(result: PreflightResult) -> str:
    """Format preflight results as human-readable report."""
    lines = [
        "Socrates Evaluation Framework - Preflight Check",
        "=" * 48,
        "",
    ]

    # Check results
    for name, check in result.checks.items():
        status = "✓" if check.ok else "✗"
        lines.append(f"{name:12} {status} {check.message}")

    lines.append("")

    # Available benchmarks
    if result.ready_benchmarks:
        lines.append(f"Ready for: {', '.join(result.ready_benchmarks[:5])}")
        if len(result.ready_benchmarks) > 5:
            lines.append(f"           +{len(result.ready_benchmarks) - 5} more")

    if result.blocked_benchmarks:
        lines.append(f"Blocked:   {', '.join(result.blocked_benchmarks[:3])} (requires Docker)")

    return "\n".join(lines)
