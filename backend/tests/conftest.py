"""Test configuration."""
import pytest


@pytest.fixture(scope="session")
def test_pdf_path():
    """Provide path to test PDF file."""
    # This would point to a test PDF file in the tests directory
    return None


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
