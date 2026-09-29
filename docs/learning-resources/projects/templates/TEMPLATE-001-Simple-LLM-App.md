---
Document ID: TEMPLATE-001-Simple-LLM-App
Title: "PROJECT TEMPLATE: Simple LLM App"
Last Updated: 2026-09-29
Status: Complete
Difficulty: Beginner
---

# PROJECT TEMPLATE: Simple LLM App

A simple template for building applications with LLMs.

## Project Structure

```text
simple-llm-app/
├── README.md
├── pyproject.toml
├── uv.lock
├── config.yaml
├── src/
│   ├── __init__.py
│   ├── model.py          # Model loading and setup
│   ├── generator.py      # Text generation
│   └── api.py            # FastAPI endpoints
├── tests/
│   └── test_model.py
└── notebooks/
    └── exploration.ipynb
```

## Features

- Model loading with HuggingFace
- Text generation interface
- REST API with FastAPI
- Configuration management
- Unit tests

## Quick Start

1. Sync dependencies:
```bash
# The template ships pyproject.toml + uv.lock - one command
# creates the project venv with the exact locked dependency graph.
uv sync
```

2. Run the API:
```bash
uvicorn src.api:app --reload
```

3. Generate text:
```bash
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, world!", "max_tokens": 50}'
```

## Configuration

Edit `config.yaml` to customize:
- Model name/path
- Generation parameters
- API settings
- Logging options

## Next Steps

- Add authentication
- Implement rate limiting
- Add monitoring
- Deploy to production

---

**Difficulty:** Beginner
**Estimated Time:** 2-4 hours
**Skills:** Python, FastAPI, Transformers
