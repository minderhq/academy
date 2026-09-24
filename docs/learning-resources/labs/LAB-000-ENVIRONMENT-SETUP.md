# LAB-000: Environment Setup

**Duration:** 45-60 minutes
**Difficulty:** ⭐ Beginner
**Prerequisites:** None

---

## 🎯 Lab Objectives

After completing this lab, you will:
- ✅ Have a working AI development environment
- ✅ Understand how to verify each component
- ✅ Know how to troubleshoot common issues
- ✅ Be ready to start TUTORIAL-001 and LAB-001

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Computer with 8GB+ RAM (16GB+ recommended)
- [ ] 100GB+ free disk space
- [ ] Administrator/sudo access
- [ ] Stable internet connection
- [ ] Basic command line familiarity

**Don't have these?** Review [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md) first.

---

## 🚀 Lab Steps

### Step 1: Operating System Check (5 minutes)

**Check your OS and version:**

**Windows:**
```powershell
# Check Windows version
systeminfo | findstr /C:"OS Name"

# Check if WSL2 is installed
wsl --list --verbose
```

**Mac:**
```bash
# Check macOS version
sw_vers

# Check architecture (Intel vs Apple Silicon)
uname -m
```

**Linux:**
```bash
# Check distribution
cat /etc/os-release

# Check kernel version
uname -r
```

**✅ Verification:**
- [ ] OS version recorded
- [ ] Architecture noted (x86_64 vs ARM64)
- [ ] WSL2 installed (Windows)

---

### Step 2: Hardware Verification (5 minutes)

**Check RAM:**

**Windows:**
```powershell
# Check total RAM
systeminfo | findstr /C:"Total Physical Memory"
```

**Mac/Linux:**
```bash
# Check RAM
# Mac: About This Mac → Memory
# Linux:
free -h
```

**Check Storage:**

**Windows:**
```powershell
# Check disk space
wmic logicaldisk get size,freespace,caption
```

**Mac/Linux:**
```bash
# Check disk space
df -h
```

**Check GPU (if available):**

```bash
# NVIDIA GPU
nvidia-smi

# If command not found, you may not have NVIDIA drivers
# CPU-only mode works but is slower
```

**✅ Verification:**
- [ ] RAM meets minimum (16GB+ ideal)
- [ ] 100GB+ free storage
- [ ] GPU detected (if available)

---

### Step 3: Docker Installation & Verification (15 minutes)

**Install Docker:**

Refer to [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md#step-2-docker-installation) for your OS.

**Verify Installation:**

```bash
# Check Docker version
docker --version

# Check Docker is running
docker ps

# Run test container
docker run hello-world
```

**Expected Output:**
```text
Hello from Docker!
This message shows that your installation appears to be working correctly.
```

**⚠️ Troubleshooting:**

**"Permission denied" (Linux only):**
```bash
sudo usermod -aG docker $USER
# Log out and log back in
```

**"Docker daemon not running":**
```bash
# Start Docker Desktop (Windows/Mac)
# OR start Docker service (Linux)
sudo systemctl start docker
```

**✅ Verification:**
- [ ] Docker version displayed
- [ ] `docker ps` works without error
- [ ] `hello-world` container ran successfully

---

### Step 4: Python Environment Setup (10 minutes)

**Check Python Version:**

```bash
python --version
# OR
python3 --version

# Should be 3.10 or higher
```

**Create Virtual Environment:**

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
```

**Verify Activation:**

```bash
# You should see (venv) in your prompt
which python
# Should show: ~/ai-engineering-curriculum/venv/bin/python
```

**Install Essential Packages:**

```bash
# Upgrade pip
pip install --upgrade pip

# Install core packages
pip install torch transformers
pip install datasets accelerate
pip install jupyter pandas numpy
```

**Test Installation:**

```bash
python -c "import torch; print(f'PyTorch {torch.__version__}')"
python -c "import transformers; print('Transformers installed')"
```

**✅ Verification:**
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Virtual environment activated
- [ ] PyTorch and Transformers installed

---

### Step 5: Ollama Installation & Test (10 minutes)

**Install Ollama:**

Refer to [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md#step-4-ollama-installation) for your OS.

**Start Ollama:**

**Windows:** Click Ollama app or run: `ollama serve`
**Mac/Linux:** `ollama serve &`

**Pull a Model:**

```bash
# Open new terminal (keep ollama serve running)

# Pull a small model for testing
ollama pull phi3
# OR
ollama pull mistral:7b
```

**Test Chat:**

```bash
ollama run phi3 "Hello! What is 2+2?"
```

**Expected Response:**
```text
The answer is 4.
```

**⚠️ Troubleshooting:**

**"Connection refused":**
- Make sure `ollama serve` is running
- Check firewall settings

**Download stuck:**
- Check internet connection
- Try again (Ollama resumes automatically)

**"Out of memory":**
- Use smaller model: `ollama pull phi3`
- Close other applications

**✅ Verification:**
- [ ] Ollama installed
- [ ] Ollama server running
- [ ] Model downloaded
- [ ] Chat responds correctly

---

### Step 6: End-to-End Test (5 minutes)

**Create Test Script:**

```bash
cd ~/ai-engineering-curriculum
cat > test_env.py << 'EOF'
import ollama
import torch
print("✅ Ollama imported")
print(f"✅ PyTorch {torch.__version__}")

# Test Ollama
response = ollama.generate(model='phi3', prompt='Say hello')
print(f"✅ LLM Response: {response['response'][:50]}...")

print("\n🎉 Environment setup complete!")
EOF
```

**Run Test:**

```bash
python test_env.py
```

**Expected Output:**
```text
✅ Ollama imported
✅ PyTorch 2.x.x
✅ LLM Response: Hello!...
🎉 Environment setup complete!
```

**✅ Verification:**
- [ ] Test script runs without errors
- [ ] All imports successful
- [ ] LLM generates response

---

## 📊 Lab Completion Checklist

### Infrastructure
- [ ] OS verified and compatible
- [ ] Hardware meets minimum requirements
- [ ] Storage sufficient for models

### Software
- [ ] Docker installed and running
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Essential packages installed

### AI Components
- [ ] Ollama installed
- [ ] Ollama server running
- [ ] At least one model downloaded
- [ ] LLM responds to prompts

### Verification
- [ ] Test script runs successfully
- [ ] All components verified
- [ ] Troubleshooting understood

---

## 🎯 Success Criteria

You have successfully completed this lab if:

1. ✅ You can run `docker ps` without errors
2. ✅ You can activate Python virtual environment
3. ✅ You can import PyTorch and Transformers
4. ✅ You can chat with an LLM via Ollama
5. ✅ You understand how to troubleshoot common issues

---

## 🚀 Next Steps

With your environment ready:

1. **Complete TUTORIAL-001:** [TUTORIAL-001-Hello-LLM.md](../tutorials/TUTORIAL-001-Hello-LLM.md)
2. **Progress to LAB-001:** [LAB-001-Docker-LLM.md](./LAB-001-Docker-LLM.md)
3. **Track Progress:** [PROGRESS-TRACKER.md](../../00-META/PROGRESS-TRACKER.md)

---

## 💡 Tips for Success

1. **Document Your Setup:**
   ```bash
   # Save your configuration
   python --version > ~/ai-engineering-curriculum/setup-info.txt
   docker --version >> ~/ai-engineering-curriculum/setup-info.txt
   ollama --version >> ~/ai-engineering-curriculum/setup-info.txt
   ```

2. **Create Startup Script:**
   ```bash
   # Start everything quickly
   #!/bin/bash
   cd ~/ai-engineering-curriculum
   source venv/bin/activate  # Mac/Linux
   # venv\Scripts\activate   # Windows
   ollama serve &
   ```

3. **Monitor Resources:**
   ```bash
   # Check GPU usage
   watch -n 1 nvidia-smi

   # Check RAM/CPU
   htop  # Mac/Linux
   # Task Manager  # Windows
   ```

---

## ❓ Common Questions

**Q: Can I use CPU-only?**
A: Yes! LLMs will run slower but work fine for learning.

**Q: Do I need all components?**
A: For LAB-000: Yes. For tutorials: Minimum is Ollama + Python.

**Q: Can I skip Docker?**
A: For LAB-001: No. For later labs: Depends on requirements.

**Q: How much disk space for models?**
A: 7B model ~4GB, 13B ~8GB, 70B ~40GB. Start with 7B.

---

**Still having issues?** Check [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md) or [TROUBLESHOOTING-QUICKSTART.md](../../00-META/TROUBLESHOOTING-QUICKSTART.md)

---

**Lab Duration:** 45-60 minutes
**Completed:** [ ] Yes / [ ] No
**Date:** _____________

**Next Lab:** [LAB-001: Docker & LLM](./LAB-001-Docker-LLM.md)
