"""Tests for eval/preflight.py - Environment validation."""

import pytest
from unittest.mock import patch, MagicMock


class TestPreflightChecks:
    """Tests for preflight environment validation."""

    def test_check_python_version(self):
        """Should validate Python version is 3.11+."""
        from eval.preflight import check_python_version

        result = check_python_version()
        assert result.ok is True
        assert "3.1" in result.version  # 3.11 or 3.12

    def test_check_inspect_installed(self):
        """Should detect if inspect-ai is installed."""
        from eval.preflight import check_inspect_installed
        import sys

        # Mock successful import
        with patch.dict(sys.modules, {"inspect_ai": MagicMock(__version__="0.3.150")}):
            result = check_inspect_installed()
            assert result.ok is True
            assert result.version == "0.3.150"

        # Mock import failure (ensure it's not in sys.modules)
        with patch.dict(sys.modules):
            if "inspect_ai" in sys.modules:
                del sys.modules["inspect_ai"]
            
            # We also need to make sure the import actually fails. 
            # Since we can't easily force an ImportError on a specific module via patch.dict alone 
            # if it's not there, we can patch builtins.__import__ but that's messy.
            # A simpler way for the failure case if we trust the environment might not have it
            # is just to assume if we remove it from sys.modules it might trigger reload, 
            # but simpler is to use a side_effect on a patch if the function used a helper.
            # But the function uses a raw `import`.
            
            # Let's try to patch `builtins.__import__` to raise ImportError for inspect_ai
            import builtins
            original_import = builtins.__import__
            
            def mock_import(name, *args, **kwargs):
                if name == "inspect_ai":
                    raise ImportError("No module named 'inspect_ai'")
                return original_import(name, *args, **kwargs)
                
            with patch("builtins.__import__", side_effect=mock_import):
                result = check_inspect_installed()
                assert result.ok is False


    @patch("subprocess.run")
    def test_check_docker_available(self, mock_run):
        """Should detect Docker availability."""
        from eval.preflight import check_docker_available

        # Mock Docker available
        mock_run.return_value = MagicMock(returncode=0)
        result = check_docker_available()
        assert result.ok is True

        # Mock Docker not available
        mock_run.return_value = MagicMock(returncode=1)
        result = check_docker_available()
        assert result.ok is False

    @patch("subprocess.run")
    def test_check_docker_not_found(self, mock_run):
        """Should handle Docker not installed."""
        from eval.preflight import check_docker_available

        mock_run.side_effect = FileNotFoundError()
        result = check_docker_available()
        assert result.ok is False
        assert "not installed" in result.message.lower()

    def test_run_all_checks(self, monkeypatch):
        """Should run all preflight checks and return summary."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        from eval.preflight import run_preflight

        result = run_preflight()

        assert "python" in result.checks
        assert "inspect" in result.checks
        assert "docker" in result.checks
        assert "api_keys" in result.checks

    def test_available_benchmarks(self, monkeypatch):
        """Should list benchmarks available given current environment."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")

        from eval.preflight import get_available_benchmarks

        with patch("eval.preflight.check_docker_available") as mock_docker:
            # Without Docker
            mock_docker.return_value = MagicMock(ok=False)
            available = get_available_benchmarks()
            assert "gsm8k" in available
            assert "swe_bench" not in available

            # With Docker
            mock_docker.return_value = MagicMock(ok=True)
            available = get_available_benchmarks()
            assert "gsm8k" in available
            assert "swe_bench" in available
