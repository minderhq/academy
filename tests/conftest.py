"""
Shared fixtures and configuration for PROJECT-OMEGA lab tests
"""

import pytest
import os
from pathlib import Path
import time
import docker
import requests


# Base paths
PROJECT_ROOT = Path(__file__).parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"
LABS_ROOT = DOCS_ROOT / "learning-resources" / "labs"
SOLUTIONS_ROOT = LABS_ROOT / "solutions"


@pytest.fixture(scope="session")
def project_root():
    """PROJECT-OMEGA root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def labs_root():
    """Labs directory"""
    return LABS_ROOT


@pytest.fixture(scope="session")
def solutions_root():
    """Solutions directory"""
    return SOLUTIONS_ROOT


@pytest.fixture(scope="session")
def docker_client():
    """Docker client for container tests"""
    try:
        client = docker.from_env()
        # Verify Docker is accessible
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"Docker not available: {e}")


@pytest.fixture(scope="session")
def ollama_url():
    """Ollama API URL (configurable via environment)"""
    return os.getenv("OLLAMA_URL", "http://localhost:11434")


@pytest.fixture(scope="session")
def ollama_available(ollama_url):
    """Check if Ollama is available"""
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception:
        return False


@pytest.fixture(scope="session")
def wait_for_service():
    """Helper to wait for service to be ready"""
    def _wait(url, timeout=30, interval=1):
        """Wait for service at URL to respond"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(interval)
        return False
    return _wait


@pytest.fixture
def lab_file(labs_root):
    """Get path to a specific lab file"""
    def _get_lab(lab_number):
        lab_file = labs_root / f"LAB-{lab_number:03d}-*.md"
        matches = list(labs_root.glob(f"LAB-{lab_number:03d}-*.md"))
        return matches[0] if matches else None
    return _get_lab


@pytest.fixture
def solution_file(solutions_root):
    """Get path to a specific solution file"""
    def _get_solution(lab_number):
        matches = list(solutions_root.glob(f"SOLUTION-LAB-{lab_number:03d}-*.md"))
        return matches[0] if matches else None
    return _get_solution


# Test configuration markers
def pytest_configure(config):
    """Configure custom pytest markers"""
    config.addinivalue_line(
        "markers", "docker: tests requiring Docker"
    )
    config.addinivalue_line(
        "markers", "gpu: tests requiring GPU support"
    )
    config.addinivalue_line(
        "markers", "ollama: tests requiring Ollama"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take a long time to run"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests"
    )


@pytest.fixture
def skip_if_no_docker(docker_client):
    """Skip test if Docker is not available"""
    if docker_client is None:
        pytest.skip("Docker not available")


@pytest.fixture
def skip_if_no_ollama(ollama_available):
    """Skip test if Ollama is not available"""
    if not ollama_available:
        pytest.skip("Ollama not available")
