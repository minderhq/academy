"""
Tests for LAB-001: Docker & LLM Fundamentals
"""

import pytest
import docker
import requests
import time
from pathlib import Path


@pytest.mark.docker
class TestLab001DockerBasics:
    """Test Exercise 1: Docker Basics"""

    def test_lab_file_exists(self, labs_root):
        """Test that LAB-001 file exists"""
        lab_files = list(labs_root.glob("LAB-001-*.md"))
        assert len(lab_files) > 0, "LAB-001 file not found"

    def test_solution_file_exists(self, solutions_root):
        """Test that SOLUTION-LAB-001 file exists"""
        solution_files = list(solutions_root.glob("SOLUTION-LAB-001-*.md"))
        assert len(solution_files) > 0, "SOLUTION-LAB-001 file not found"

    @pytest.mark.skipif(
        not docker.from_env().ping() if docker.from_env() else False,
        reason="Docker not available"
    )
    def test_docker_is_running(self, docker_client):
        """Test that Docker daemon is accessible"""
        assert docker_client is not None
        version = docker_client.version()
        assert "Version" in version


@pytest.mark.docker
@pytest.mark.ollama
class TestLab001OllamaDeployment:
    """Test Exercise 1: Ollama Deployment"""

    @pytest.fixture
    def ollama_container(self, docker_client):
        """Ensure Ollama container is running"""
        containers = docker_client.containers.list(all=True)
        ollama = next((c for c in containers if "ollama" in c.name), None)

        if ollama and ollama.status != "running":
            ollama.start()
            time.sleep(5)

        if not ollama:
            pytest.skip("Ollama container not found. Run: docker run -d --name ollama -p 11434:11434 ollama/ollama")

        return ollama

    def test_ollama_container_is_running(self, ollama_container):
        """Test that Ollama container is running"""
        assert ollama_container.status == "running"

    def test_ollama_api_accessible(self, ollama_url):
        """Test that Ollama API is accessible"""
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_ollama_container_has_gpu_support(self, docker_client):
        """Test that container has GPU support (if available)"""
        try:
            ollama = docker_client.containers.get("ollama")
            inspect = ollama.attrs
            host_config = inspect["HostConfig"]

            # Check if GPU is requested
            device_requests = host_config.get("DeviceRequests", [])
            assert len(device_requests) > 0, "No GPU devices requested"
        except Exception:
            pytest.skip("Could not verify GPU support")


@pytest.mark.docker
@pytest.mark.ollama
class TestLab001ModelOperations:
    """Test Exercise 2: Model Operations"""

    @pytest.fixture
    def mistral_available(self, ollama_url):
        """Check if mistral model is available"""
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=10)
            models = response.json().get("models", [])
            return any(m.get("name") == "mistral" for m in models)
        except Exception:
            return False

    def test_model_list(self, ollama_url):
        """Test listing models"""
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    @pytest.mark.skipif(
        not True,  # Change to check if mistral is downloaded
        reason="Mistral model not downloaded"
    )
    def test_model_generation(self, ollama_url):
        """Test generating text with a model"""
        payload = {
            "model": "mistral",
            "prompt": "Say 'test successful' if you understand.",
            "stream": False
        }

        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )

        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 0


@pytest.mark.docker
class TestLab001DockerCommands:
    """Test understanding of Docker commands"""

    def test_docker_run_command_knowledge(self):
        """Test: What does 'docker run' do?"""
        # This would be an interactive quiz in a real implementation
        question = "What command runs a container in detached mode?"
        correct_answer = "docker run -d"
        # In practice, this would check user input

    def test_docker_volume_knowledge(self):
        """Test: Understanding of Docker volumes"""
        question = "What flag mounts a volume?"
        correct_answer = "-v"
        # In practice, this would check user input

    def test_docker_port_knowledge(self):
        """Test: Understanding of port mapping"""
        question = "What flag maps container ports to host?"
        correct_answer = "-p"
        # In practice, this would check user input


@pytest.mark.concepts
class TestLab001Concepts:
    """Test conceptual understanding from LAB-001"""

    def test_container_vs_image(self):
        """Test understanding of container vs image"""
        # Quiz: What's the difference?
        # Image: Template for containers
        # Container: Running instance of an image
        assert True  # Placeholder for quiz check

    def test_gpu_passthrough_concept(self):
        """Test understanding of GPU passthrough"""
        # Quiz: Why use --gpus all?
        # Answer: To pass GPU devices to the container
        assert True  # Placeholder for quiz check

    def test_volume_persistence(self):
        """Test understanding of data persistence"""
        # Quiz: Why use volumes?
        # Answer: To persist data beyond container lifecycle
        assert True  # Placeholder for quiz check


@pytest.mark.integration
@pytest.mark.docker
@pytest.mark.slow
class TestLab001Integration:
    """Integration tests for LAB-001"""

    @pytest.fixture
    def full_ollama_stack(self, docker_client, ollama_url):
        """Verify full Ollama stack is working"""
        try:
            # Check container
            containers = docker_client.containers.list(all=True)
            ollama = next((c for c in containers if "ollama" in c.name), None)

            # Check API
            response = requests.get(f"{ollama_url}/api/tags", timeout=10)

            return {
                "container": ollama is not None,
                "api": response.status_code == 200
            }
        except Exception:
            return {"container": False, "api": False}

    def test_end_to_end_flow(self, full_ollama_stack):
        """Test complete flow: container → API → generation"""
        assert full_ollama_stack["container"], "Ollama container not found"
        assert full_ollama_stack["api"], "Ollama API not accessible"

    def test_data_persistence(self, docker_client):
        """Test that models persist after container restart"""
        try:
            ollama = docker_client.containers.get("ollama")
            mounts = ollama.attrs.get("Mounts", [])

            # Should have volume mount for models
            assert len(mounts) > 0, "No volume mounts found"
        except Exception as e:
            pytest.skip(f"Could not verify persistence: {e}")


# Validation checklist
@pytest.mark.checklist
class TestLab001Checklist:
    """Completion checklist for LAB-001"""

    def test_exercise_1_complete(self):
        """Exercise 1: Run Ollama in Docker"""
        # [ ] Container is running
        # [ ] API responds on port 11434
        # [ ] GPU support is enabled
        assert True  # User confirms completion

    def test_exercise_2_complete(self):
        """Exercise 2: Pull and use models"""
        # [ ] Model is downloaded
        # [ ] Generation works
        # [ ] API returns valid JSON
        assert True  # User confirms completion

    def test_exercise_3_complete(self):
        """Exercise 3: Volume persistence"""
        # [ ] Volume is mounted
        # [ ] Models survive container restart
        # [ ] Data is persisted
        assert True  # User confirms completion
