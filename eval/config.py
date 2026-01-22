"""API key management and benchmark requirements."""

import os
from pathlib import Path
from typing import Optional


def mask_api_key(key: Optional[str]) -> str:
    """Mask API key for safe logging, showing only last 4 characters."""
    if not key:
        return "not set"
    if len(key) <= 4:
        return "..." + key
    return "..." + key[-4:]


class APIKeyManager:
    """Manages API keys for multi-model evaluation."""

    # Map provider prefixes to environment variable names
    PROVIDER_KEYS = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "x-ai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }

    def __init__(self, env_file: Optional[Path] = None):
        """Initialize with optional .env file path."""
        self._env_file = env_file or Path(".env")
        self._load_dotenv()

    def _load_dotenv(self):
        """Load .env file if present (don't override existing env vars)."""
        if not self._env_file.exists():
            return

        for line in self._env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip("\"'")

            # Don't override existing environment variables
            if key not in os.environ:
                os.environ[key] = value

    def _get_provider(self, model: str) -> str:
        """Extract provider from model string (e.g., 'anthropic/claude-3')."""
        if "/" in model:
            return model.split("/")[0]
        # Default to anthropic for unqualified model names
        return "anthropic"

    def get_key(self, provider: str) -> Optional[str]:
        """Get API key for a provider."""
        env_var = self.PROVIDER_KEYS.get(provider)
        if not env_var:
            return None
        return os.environ.get(env_var)

    def validate_for_models(self, models: list[str]) -> dict[str, bool]:
        """Check which models have valid keys configured."""
        results = {}
        for model in models:
            provider = self._get_provider(model)
            results[model] = self.get_key(provider) is not None
        return results

    def get_missing_keys(self, models: list[str]) -> list[str]:
        """Return list of models missing API keys."""
        validation = self.validate_for_models(models)
        return [model for model, has_key in validation.items() if not has_key]


class BenchmarkRequirements:
    """Defines requirements for each benchmark."""

    # Benchmarks that require Docker for sandboxed execution
    DOCKER_REQUIRED = {
        "swe_bench",
        "swe_bench_verified",
        "swe_bench_verified_mini",
        "gaia",
        "gaia_l1",
        "gaia_l2",
        "gaia_l3",
        "cybench",
        "terminal_bench",
    }

    # Benchmarks that work without Docker
    NO_DOCKER = {
        "gsm8k",
        "mmlu",
        "humaneval",
        "arc",
        "hellaswag",
        "truthfulqa",
        "winogrande",
    }

    @classmethod
    def requires_docker(cls, benchmark: str) -> bool:
        """Check if a benchmark requires Docker."""
        # Normalize benchmark name
        normalized = benchmark.lower().replace("-", "_")
        return normalized in cls.DOCKER_REQUIRED

    @classmethod
    def all_benchmarks(cls) -> set[str]:
        """Return all known benchmarks."""
        return cls.DOCKER_REQUIRED | cls.NO_DOCKER
