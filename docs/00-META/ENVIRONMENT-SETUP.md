---
Document ID: ENVIRONMENT-SETUP
Title: "Environment Setup Guide"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# Environment Setup Guide

**Last Updated:** 2026-09-27
**Reading Time:** 15 minutes
**Difficulty:** ⭐ Beginner

---

## Overview

This guide helps you set up a complete AI development environment for PROJECT-OMEGA. Whether you're working on Windows, Mac, or Linux, we'll get you ready to run local LLMs, fine-tune models, and deploy AI systems.

---

## 🖥️ Hardware Requirements

### Minimum Specifications (For Learning)

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 4 cores | 8+ cores | x86_64 or ARM64 |
| **RAM** | 16GB | 32GB+ | More RAM = better model performance |
| **Storage** | 100GB SSD | 500GB+ NVMe SSD | Models take significant space |
| **GPU** | None (CPU mode) | 8GB+ VRAM | NVIDIA RTX 3060+ recommended |
| **Network** | Stable internet | 100Mbps+ | For model downloads |

### Check Your Hardware

**Windows:**
```powershell
# System Information
systeminfo | findstr /C:"Total Physical Memory"

# GPU Information (if NVIDIA)
nvidia-smi

# Storage Check
wmic diskdrive get size,model
```

**Mac/Linux:**
```bash
# System Information
system_profiler SPHardwareDataType  # Mac
lscpu                              # Linux

# GPU Information
nvidia-smi                          # If NVIDIA

# Storage Check
df -h
```

---

## 📦 Software Installation

### Step 1: Operating System Preparation

#### Windows
1. **Enable WSL2** (Recommended for AI development)
```powershell
wsl --install
```

2. **Install Windows Terminal** (from Microsoft Store)

3. **Enable Virtualization** in BIOS:
   - Intel: Intel VT-x
   - AMD: AMD-V

#### macOS
1. **Update macOS** to latest version
2. **Install Xcode Command Line Tools:**
```bash
xcode-select --install
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y build-essential curl wget git
```

---

### Step 2: Docker Installation

Docker is essential for containerized AI applications.

#### Windows
1. Download **Docker Desktop** from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Run installer with WSL2 backend enabled
3. Restart computer
4. Verify installation:
```powershell
docker --version
docker run hello-world
```

#### macOS
1. Download **Docker Desktop for Mac** (Apple Silicon or Intel)
2. Install and start Docker
3. Verify:
```bash
docker --version
docker run hello-world
```

#### Linux
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Verify
docker --version
```

---

### Step 3: Python Environment (uv)

> **Tooling standard (2026):** this curriculum uses [uv](https://docs.astral.sh/uv/)
> as its package manager. uv resolves and installs packages 10-100x faster
> than pip (parallel downloads + a global cache) and manages Python versions,
> virtual environments, and project dependencies in one tool. Everywhere else
> in the corpus, a `pip install X` you encounter maps 1:1 to `uv pip install X`.
>
> Two deliberate exceptions: inside conda workflows,
> `pip install` into the active environment remains the standard; and in
> uv-first blocks that already show `uv pip install` as the recommended
> form, a labeled plain-pip fallback (QUICK-START's `# plain pip works too`)
> may stay so first-run readers succeed on any setup. Dockerfiles used to be
> a third exception, but every Dockerfile in the corpus now follows LAB-001's
> official uv image pattern (uv binary copied from the uv image, then
> `RUN uv pip install --system`); TUTORIAL-002 keeps one deliberately bad
> Dockerfile that uses plain pip as a labeled anti-example.

#### Install uv

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Verify:
```bash
uv --version
```

> **Prefer pip?** uv is a drop-in replacement, but a system Python 3.13+ with
> `python -m venv` and plain `pip` still works for every lesson. On Windows,
> install Python from [python.org](https://www.python.org/downloads/) (check
> "Add Python to PATH"); on macOS use `brew install python@3.13`; on Linux
> `sudo apt install -y python3.13 python3-pip python3-venv`.

#### Create the Project Environment

```bash
# Create project directory
mkdir -p ~/project-omega
cd ~/project-omega

# Create a virtual environment with Python 3.13
# (uv downloads the interpreter itself if it is missing)
uv venv --python 3.13

# Activate — optional: uv finds .venv automatically when run
# inside the project directory
source .venv/bin/activate    # Mac/Linux
.venv\Scripts\activate       # Windows
```

#### uv Project Workflow (pyproject.toml + uv.lock)

The `uv pip` interface above is the pip-compatible layer. For real
projects, uv's own workflow is the 2026 standard: dependencies are
declared in `pyproject.toml` and pinned by a `uv.lock` lockfile, so
every machine resolves the exact same versions.

```bash
# Start a project (creates pyproject.toml + .venv automatically)
uv init --python 3.13

# Declare a dependency (writes it to pyproject.toml and updates
# uv.lock in one step)
uv add fastapi uvicorn

# Install exactly what uv.lock pins (run this after cloning)
uv sync

# Run project commands inside the managed environment
# (no activate needed - uv picks up .venv by itself)
uv run uvicorn main:app --reload
```

How the two layers relate:
- `uv pip install -r requirements.txt` — imperative, like pip;
  fine for labs and Dockerfiles
- `uv add` / `uv sync` + `uv.lock` — declarative and reproducible
  across machines and CI; the standard for anything you own
- Migrating an existing `requirements.txt`: `uv add -r
  requirements.txt` imports it into `pyproject.toml` in one step

#### Code Quality Tooling (ruff, zero-install via uvx)

For linting and formatting, the 2026 standard is [ruff](https://docs.astral.sh/ruff/) — one Rust-fast tool that replaces the old flake8 + black + isort stack. You do not even need to install it: `uvx` runs a tool in an ephemeral, cached environment.

```bash
# Lint and format the project - no install step at all
uvx ruff check .
uvx ruff format .

# Use it daily? Install it once into an isolated tool environment
uv tool install ruff
```

---

### Step 4: Ollama Installation

Ollama simplifies running local LLMs.

#### Windows (WSL2)
```bash
# Install in WSL2
curl -fsSL https://ollama.com/install.sh | sh
```

#### macOS
```bash
# Download installer from ollama.com
# OR use Homebrew
brew install ollama
```

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

#### Start Ollama & Test
```bash
# Start Ollama server
ollama serve

# In another terminal, pull a model
ollama pull mistral

# Test chat
ollama run mistral "Hello, can you help me learn AI?"
```

---

### Step 5: Essential Python Packages

```bash
# Core AI/ML packages
uv pip install torch torchvision torchaudio
uv pip install transformers
uv pip install datasets
uv pip install accelerate

# RAG and vector databases
uv pip install chromadb qdrant-client
uv pip install langchain
uv pip install sentence-transformers

# Fine-tuning
uv pip install peft
uv pip install bitsandbytes
uv pip install trl

# Utilities
uv pip install jupyter
uv pip install pandas numpy matplotlib
uv pip install requests tqdm
```

> NVIDIA GPU on Linux? Torch needs the CUDA wheel index:
> `uv pip install torch --index-url https://download.pytorch.org/whl/cu130`.
> `uv pip install` accepts every `pip install` flag, so any package
> instructions elsewhere in the curriculum work unchanged.

---

## 🔧 Troubleshooting

### Issue 1: Ollama Download Fails

**Symptoms:**
- Download hangs at 0%
- "Connection refused" error
- Very slow download speed

**Solutions:**

1. **Check Network Connection:**
```bash
# Test internet
ping google.com

# Check DNS
nslookup ollama.com
```

2. **Use Alternative Mirror:**
```bash
# Set environment variable
export OLLAMA_HOST=https://ollama.com
```

3. **Manual Download:**
```bash
# Download model manually
wget https://ollama.com/download/mistral

# Place in Ollama models directory
# ~/.ollama/models/ on Linux/Mac
# %USERPROFILE%\.ollama\models\ on Windows
```

---

### Issue 2: Docker "Permission Denied"

**Linux only:**
```bash
# Fix permission issue
sudo usermod -aG docker $USER

# Log out and log back in
# OR run without sudo (temporary)
sudo chmod 666 /var/run/docker.sock
```

---

### Issue 3: CUDA Out of Memory (GPU)

**Symptoms:**
- "CUDA out of memory" error
- Model fails to load

**Solutions:**

1. **Check GPU Memory:**
```bash
nvidia-smi
```

2. **Use Smaller Model:**
```bash
# Try 7B instead of 13B/70B
ollama pull mistral:7b
```

3. **Offload to CPU:**
```python
import torch
# Force CPU
device = "cpu"
model.to(device)
```

---

### Issue 4: Python Version Conflicts

**Symptoms:**
- "Module not found" errors
- Version incompatibility

**Solutions:**

1. **Check Python Version:**
```bash
python --version
# Should be 3.13 or higher
```

2. **Use uv (recommended) or pyenv:**
```bash
# uv manages interpreter versions too - simplest path
uv python install 3.13
uv venv --python 3.13

# pyenv alternative (Mac/Linux)
brew install pyenv  # Mac
curl https://pyenv.run | bash  # Linux

# Install Python 3.13
pyenv install 3.13
pyenv local 3.13
```

3. **Windows - Use Python Launcher with uv:**
```powershell
py -3.13 --version
uv pip install --python 3.13 package-name
```

---

### Issue 5: WSL2 Issues on Windows

**Symptoms:**
- WSL won't start
- Network issues between WSL and Windows

**Solutions:**

1. **Update WSL:**
```powershell
wsl --update
```

2. **Restart WSL:**
```powershell
wsl --shutdown
wsl
```

3. **Check Network Bridge:**
```powershell
# In PowerShell (admin)
New-NetFirewallRule -DisplayName "WSL" -Direction Inbound -InterfaceAlias "vEthernet (WSL)" -Action Allow
```

---

## ✅ Verification Checklist

Before starting tutorials, verify:

### Hardware Verification
- [ ] RAM meets minimum (16GB+)
- [ ] Storage space available (100GB+)
- [ ] GPU detected (if available) with `nvidia-smi`

### Software Verification
- [ ] Docker running: `docker ps`
- [ ] uv installed: `uv --version`
- [ ] Virtual environment active: `which python` (or `.venv` exists in the project)
- [ ] Ollama running: `ollama list`
- [ ] Model downloaded: `ollama pull mistral`

### Functionality Verification
- [ ] Can run Docker container: `docker run hello-world`
- [ ] Can import PyTorch: `python -c "import torch"`
- [ ] Can chat with model: `ollama run mistral "test"`
- [ ] Can create notebook: `jupyter notebook`

---

## 🎯 Next Steps

Once your environment is set up:

1. **Start with Quick Start:** [QUICK-START.md](QUICK-START.md)
2. **Complete LAB-000:** [LAB-000-ENVIRONMENT-SETUP.md](../learning-resources/labs/LAB-000-ENVIRONMENT-SETUP.md)
3. **Progress to TUTORIAL-001:** [TUTORIAL-001-Hello-LLM.md](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)

---

## 📚 Additional Resources

### Hardware Guides
- [GPU Comparison](https://www.tomshardware.com/best-gpus)
- [Ollama Model Library (model sizes)](https://ollama.com/library)

### Software Resources
- [Docker Documentation](https://docs.docker.com/)
- [Ollama Documentation](https://docs.ollama.com)
- [PyTorch Installation](https://pytorch.org/get-started/locally/)

### Troubleshooting
- [Common Docker Issues](https://docs.docker.com/engine/daemon/troubleshoot/)
- [WSL2 Troubleshooting](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)

---

## 💡 Tips for Success

1. **Start Small:** Begin with 7B models, not 70B
2. **Use Virtual Environments:** Avoid package conflicts
3. **Monitor Resources:** Use `htop` or `nvidia-smi`
4. **Backup Models:** Don't re-download large models
5. **Document Setup:** Note your working configuration

---

**Still having issues?** Check [TROUBLESHOOTING-QUICKSTART.md](TROUBLESHOOTING-QUICKSTART.md) for common Quick Start problems.

