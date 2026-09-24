# Environment Setup Guide

**Last Updated:** 2026-02-04
**Reading Time:** 15 minutes
**Difficulty:** ⭐ Beginner

---

## Overview

This guide helps you set up a complete AI development environment for AI Engineering Curriculum. Whether you're working on Windows, Mac, or Linux, we'll get you ready to run local LLMs, fine-tune models, and deploy AI systems.

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

### Step 3: Python Environment

#### Install Python 3.10+

**Windows:**
1. Download from [python.org](https://www.python.org/downloads/)
2. Check "Add Python to PATH"
3. Verify:
```powershell
python --version
```

**macOS:**
```bash
# Using Homebrew (recommended)
brew install python@3.11
```

**Linux:**
```bash
sudo apt install -y python3.11 python3-pip python3-venv
```

#### Create Virtual Environment

```bash
# Create project directory
mkdir -p ~/ai-engineering-curriculum
cd ~/ai-engineering-curriculum

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
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
pip install torch torchvision torchaudio
pip install transformers
pip install datasets
pip install accelerate

# RAG and vector databases
pip install chromadb qdrant-client
pip install langchain
pip install sentence-transformers

# Fine-tuning
pip install peft
pip install bitsandbytes
pip install trl

# Utilities
pip install jupyter
pip install pandas numpy matplotlib
pip install requests tqdm
```

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
# Should be 3.10 or higher
```

2. **Use pyenv (Mac/Linux):**
```bash
# Install pyenv
brew install pyenv  # Mac
curl https://pyenv.run | bash  # Linux

# Install Python 3.11
pyenv install 3.11.7
pyenv local 3.11.7
```

3. **Windows - Use Python Launcher:**
```powershell
py -3.11 -m pip install package-name
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
- [ ] Python 3.10+: `python --version`
- [ ] Virtual environment active: `which python`
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
- [RAM Requirements for LLMs](https://ollama.com/blog/run-llama-3-locally)

### Software Resources
- [Docker Documentation](https://docs.docker.com/)
- [Ollama Documentation](https://ollama.com/docs)
- [PyTorch Installation](https://pytorch.org/get-started/locally/)

### Troubleshooting
- [Common Docker Issues](https://docs.docker.com/engine/troubleshooting/)
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

---

**Last Updated:** 2026-02-04
**Contributors:** AI Engineering Curriculum Team
