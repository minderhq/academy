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
Download and install Docker Desktop from https://www.docker.com/products/docker-desktop

---

## Exercise 4: Python Environment
### Solution
```bash
# Create venv
python3 -m venv omega-env
source omega-env/bin/activate  # Mac/Linux
omega-env\Scripts\activate     # Windows

# Install packages
pip install torch torchvision torchaudio
pip install transformers datasets
pip install fastapi uvicorn[standard]
pip install ollama
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

**Last Updated:** 2026-02-04
**Difficulty:** ⭐ Beginner
