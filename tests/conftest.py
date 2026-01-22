"""Pytest configuration and shared fixtures."""

import os
import sys
import pytest
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Clean environment for each test."""
    # Remove any existing API keys to ensure tests are isolated
    for key in ["ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GOOGLE_API_KEY"]:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def temp_state_file(tmp_path):
    """Create a temporary state file path."""
    return tmp_path / ".eval_state.json"


@pytest.fixture
def sample_episode_data():
    """Sample episode data for testing."""
    return {
        "sample_id": "test_001",
        "context": {
            "input": "What is 2+2?",
            "target": "4"
        },
        "traces": [
            {"type": "model", "content": "Let me calculate..."},
            {"type": "tool", "function": "calculator", "result": "4"}
        ],
        "action": {
            "output": "The answer is 4",
            "tool_calls_count": 1
        },
        "outcome": {
            "passed": True,
            "score": 1.0,
            "failure_mode": None
        },
        "cost": {
            "input_tokens": 100,
            "output_tokens": 50,
            "usd": 0.001
        }
    }
