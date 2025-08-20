"""
Pytest configuration for unit tests only.
This conftest is isolated from integration test dependencies.
"""

import pytest

def pytest_configure(config):
    """Configure pytest markers for unit tests."""
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
