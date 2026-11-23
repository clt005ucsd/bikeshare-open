"""Pytest fixtures shared across tests."""
import pytest

from src.ingest import load_raw


@pytest.fixture(scope="module")
def raw():
    """Load the raw bike-sharing data once per test session."""
    return load_raw()
