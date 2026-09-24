# AI Engineering Curriculum Lab Testing Framework

**Automated testing for hands-on lab validation**

---

## Overview

This testing framework provides automated validation for lab completion. Each lab has corresponding tests to verify:

1. **Code correctness** - Does the solution work as expected?
2. **Concept understanding** - Are key concepts demonstrated?
3. **Best practices** - Is code following recommended patterns?

---

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-asyncio requests docker
```

### Run All Tests

```bash
# Run all lab tests
pytest tests/ -v

# Run specific lab tests
pytest tests/test_lab_001.py -v

# Run with coverage
pytest tests/ --cov=.

# Run in parallel (faster)
pytest tests/ -n auto
```

---

## Test Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Shared fixtures
├── test_lab_001.py             # LAB-001: Docker & LLM tests
├── test_lab_002.py             # LAB-002: RAG Implementation tests
├── test_lab_003.py             # LAB-003: LoRA Fine-tuning tests
├── test_lab_004.py             # LAB-004: ReAct Agent tests
├── test_lab_005.py             # LAB-005: GraphRAG tests
└── ...
```

---

## Test Template

```python
"""Tests for LAB-XXX: Lab Name"""

import pytest
from pathlib import Path


class TestLabXXX:
    """Test suite for LAB-XXX"""

    @pytest.fixture
    def lab_dir(self):
        """Path to lab directory"""
        return Path(__file__).parent.parent / "docs/learning-resources/labs"

    def test_exercise_1_solution_exists(self, lab_dir):
        """Test that Exercise 1 solution file exists"""
        solution_file = lab_dir / "solutions/SOLUTION-LAB-XXX.md"
        assert solution_file.exists()

    def test_exercise_1_code_runs(self, lab_dir):
        """Test that Exercise 1 code can execute"""
        # Implementation depends on lab type
        pass

    def test_exercise_2_concept_check(self, lab_dir):
        """Test understanding of key concepts"""
        # Quiz-style questions
        assert True  # Replace with actual test
```

---

## Test Categories

### 1. Code Execution Tests

Verify that provided code snippets work:

```python
def test_docker_container_runs(self):
    """Test that Docker container starts successfully"""
    import docker
    client = docker.from_env()
    containers = client.containers.list()
    assert any(c.name == "ollama" for c in containers)
```

### 2. API Response Tests

Verify API endpoints work correctly:

```python
def test_ollama_api_response(self):
    """Test Ollama API returns valid response"""
    import requests
    response = requests.post("http://localhost:11434/api/generate", json={
        "model": "mistral",
        "prompt": "Test",
        "stream": False
    })
    assert response.status_code == 200
    assert "response" in response.json()
```

### 3. Concept Understanding Tests

Quiz-style questions to verify understanding:

```python
def test_concept_docker_containers(self):
    """Test understanding of Docker containers"""
    # Multiple choice question
    question = "What is a Docker container?"
    options = {
        "a": "A virtual machine",
        "b": "An isolated application environment",
        "c": "A physical server"
    }
    correct_answer = "b"
    # Test implementation would check user's answer
```

---

## Validation Checklist

Before marking a lab as complete, verify:

### Infrastructure Labs (001-003)
- [ ] Docker containers run successfully
- [ ] Services are accessible on expected ports
- [ ] GPU passthrough works (if applicable)
- [ ] Data persistence works

### AI/ML Labs (004-006)
- [ ] Model loads without errors
- [ ] Inference produces expected output
- [ ] Performance meets minimum requirements
- [ ] Memory usage is within limits

### Advanced Labs (007+)
- [ ] Multi-service integration works
- [ ] Error handling is robust
- [ ] Monitoring data is collected
- [ ] System can handle load

---

## Continuous Integration

### GitHub Actions Example

```yaml
name: Lab Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pytest pytest-asyncio requests docker
      - name: Run tests
        run: pytest tests/ -v
```

---

## Troubleshooting

### Test Failures

1. **Docker not available**
   - Ensure Docker is running: `docker ps`
   - Check permissions: Add user to docker group

2. **Port conflicts**
   - Kill conflicting processes
   - Change ports in test setup

3. **Model download issues**
   - Check internet connection
   - Pre-download models for CI

---

## Contributing

When adding new labs:

1. Create `test_lab_XXX.py` in tests/
2. Add at least 3 test cases
3. Include positive and negative tests
4. Document any prerequisites
5. Update this README

---

**Status:** ✅ Framework Ready
**Last Updated:** 2026-02-05
**Maintainer:** AI Engineering Curriculum Team
