---
Document ID: SOLUTION-LAB-000
Title: "SOLUTION-LAB-000: Environment Setup"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-000: Environment Setup

## Overview
Complete solution for environment verification and setup.

---

## Exercise 1: OS Check
### Solution
No action needed - informational commands show your system specs.

---

## Exercise 2: Hardware Verification
### Solution
```bash
# RAM
# Windows: wmic memorychip get capacity
# Mac: sysctl hw.memsize
# Linux: free -h

# GPU
nvidia-smi

# Storage
df -h
```

---

## Exercise 3: Docker Installation
### Solution (Mac/Linux)
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Solution (Windows)
Download and install Docker Desktop from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)

---

## Exercise 4: Python Environment
### Solution
```bash
# Create the project environment with uv
# (uv downloads Python 3.13 itself if it is missing)
uv venv --python 3.13
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Install packages (uv finds the active .venv automatically)
uv pip install torch torchvision torchaudio
uv pip install transformers datasets
uv pip install fastapi uvicorn[standard]
uv pip install ollama
```

---

## Exercise 5: Ollama Setup
### Solution
```bash
# Install
curl -fsSL https://ollama.com/install.sh | sh

# Start server
ollama serve

# Pull model (another terminal)
ollama pull mistral

# Test
ollama run mistral "Hello!"
```

---

## Exercise 6: End-to-End Test
### Solution
```python
import ollama

# Test connection
response = ollama.generate(model='mistral', prompt='Write a haiku about AI:')
print(response['response'])

# Expected: A haiku about AI
```

---

**Difficulty:** ⭐ Beginner
