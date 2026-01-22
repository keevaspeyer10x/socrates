"""Tests for eval/config.py - API key management."""

import os
import pytest
from pathlib import Path


class TestAPIKeyManager:
    """Tests for API key loading and validation."""

    def test_load_key_from_env(self, monkeypatch):
        """API key should be loaded from environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test123")

        from eval.config import APIKeyManager
        manager = APIKeyManager()

        assert manager.get_key("anthropic") == "sk-ant-test123"

    def test_missing_key_returns_none(self, monkeypatch):
        """Missing API key should return None, not raise."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        from eval.config import APIKeyManager
        # Use non-existent SOPS file to avoid loading from minds config
        manager = APIKeyManager(sops_file=Path("/nonexistent/secrets.yaml"))

        assert manager.get_key("anthropic") is None

    def test_mask_key_for_logging(self):
        """API key should be masked for safe logging."""
        from eval.config import mask_api_key

        assert mask_api_key("sk-ant-api03-abcdefghijk") == "...hijk"
        assert mask_api_key("short") == "...hort"
        assert mask_api_key(None) == "not set"
        assert mask_api_key("") == "not set"

    def test_validate_required_keys(self, monkeypatch):
        """Should return dict of model -> bool for key availability."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from eval.config import APIKeyManager
        # Use non-existent SOPS file to avoid loading from minds config
        manager = APIKeyManager(sops_file=Path("/nonexistent/secrets.yaml"))

        result = manager.validate_for_models([
            "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o"
        ])

        assert result["anthropic/claude-sonnet-4-20250514"] is True
        assert result["openai/gpt-4o"] is False

    def test_get_missing_keys(self, monkeypatch):
        """Should return list of missing API keys."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        from eval.config import APIKeyManager
        # Use non-existent SOPS file to avoid loading from minds config
        manager = APIKeyManager(sops_file=Path("/nonexistent/secrets.yaml"))

        missing = manager.get_missing_keys([
            "anthropic/claude-sonnet-4-20250514",
            "openai/gpt-4o"
        ])

        assert "openai/gpt-4o" in missing
        assert "anthropic/claude-sonnet-4-20250514" not in missing


class TestBenchmarkRequirements:
    """Tests for benchmark requirement mapping."""

    def test_swe_bench_requires_docker(self):
        """SWE-bench should require Docker."""
        from eval.config import BenchmarkRequirements

        assert BenchmarkRequirements.requires_docker("swe_bench")
        assert BenchmarkRequirements.requires_docker("swe_bench_verified")

    def test_gsm8k_no_docker(self):
        """GSM8K should not require Docker."""
        from eval.config import BenchmarkRequirements

        assert not BenchmarkRequirements.requires_docker("gsm8k")
        assert not BenchmarkRequirements.requires_docker("mmlu")

    def test_humaneval_no_docker(self):
        """HumanEval should not require Docker (for fast iteration)."""
        from eval.config import BenchmarkRequirements

        assert not BenchmarkRequirements.requires_docker("humaneval")
        assert not BenchmarkRequirements.requires_docker("humaneval_fast")

    def test_mbpp_no_docker(self):
        """MBPP should not require Docker."""
        from eval.config import BenchmarkRequirements

        assert not BenchmarkRequirements.requires_docker("mbpp")

    def test_bigcodebench_requires_docker(self):
        """BigCodeBench should require Docker (for Python library dependencies)."""
        from eval.config import BenchmarkRequirements

        assert BenchmarkRequirements.requires_docker("bigcodebench")
        assert BenchmarkRequirements.requires_docker("bigcodebench_hard")
