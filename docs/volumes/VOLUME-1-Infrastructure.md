---
Document ID: VOLUME-1
Title: "Volume 1: Infrastructure Fundamentals"
Last Updated: 2026-02-04
Status: Complete
Difficulty: Intermediate
---

# Volume 1: Infrastructure Fundamentals

**"Building the Foundation"** - Set up your AI lab and run your first local LLMs.

---

## 📚 Volume Overview

**Difficulty:** ⭐ Beginner
**Time:** 2-3 weeks (part-time)
**Prerequisites:** Basic computer literacy, 8GB+ RAM

### What You'll Learn

After completing this volume, you will be able to:
- ✅ Run LLMs locally on your computer
- ✅ Containerize applications with Docker
- ✅ Build basic AI applications
- ✅ Understand network topology for AI systems
- ✅ Deploy services with Docker Compose

### Why This Volume Matters

Before diving into model internals, fine-tuning, or RAG, you need a solid foundation. This volume gets you:
- **Running models locally** - No API costs, full privacy
- **Containerized deployments** - Reproducible, portable AI applications
- **Network understanding** - Essential for distributed AI systems
- **Production basics** - Ready for scaling later

---

## 🗺️ Learning Path

### Week 1: Quick Start & Docker Fundamentals

#### Day 1-2: Quick Start (30 min - 2 hours)
**Start here if you're new to AI**

1. **[QUICK-START.md](../00-META/QUICK-START.md)** (30 minutes)
   - Install Ollama
   - Run Mistral 7B
   - First Python AI script

2. **[CHEAT-SHEET-002-Python-AI.md](../learning-resources/cheat-sheets/CHEAT-SHEET-002-Python-AI.md)** (reference)
   - Python essentials for AI
   - NumPy, PyTorch basics
   - API integration patterns

#### Day 3-5: Docker Essentials
**Containerize your first AI application**

1. **[TUTORIAL-002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)** (90 min)
   - Docker concepts
   - Container basics
   - Docker Compose

2. **[CHEAT-SHEET-001-Docker.md](../learning-resources/cheat-sheets/CHEAT-SHEET-001-Docker.md)** (reference)
   - Common Docker commands
   - Troubleshooting tips

3. **[LAB-001: Docker & LLM](../learning-resources/labs/LAB-001-Docker-LLM.md)** (3 hours)
   - Deploy Ollama with Docker
   - Build containerized AI service
   - Practice: Complete all 5 exercises

**Checkpoint:** You have a running Dockerized LLM service

---

### Week 2: Local LLMs & Hello LLM

#### Day 1-3: Understanding Local LLMs
**Learn how LLMs work on your hardware**

1. **[TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)** (60 min)
   - What are LLMs?
   - How they work
   - Your first conversation

2. **[1401: Ollama Enterprise](../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)** (45 min)
   - Running localized model APIs
   - Model management
   - API server setup

#### Day 4-5: Network & Hardware (Optional)
**For those building HomeLab infrastructure**

1. **[1101: Internet Uplink & Modem Configuration](../phases/phase1-infra/1100-network/1101-Fiber-GPON-Modem.md)**
   - Understanding your internet connection
   - Signal path optimization
   - Bridge mode configuration

2. **[1102: Star Topology Core](../phases/phase1-infra/1100-network/1102-Star-Topology-Core.md)**
   - Multi-gigabit network design
   - Switch configuration
   - Traffic management

3. **[1103: Jumbo Frames and MTU](../phases/phase1-infra/1100-network/1103-Jumbo-Frames-and-MTU.md)**
   - MTU 9000 optimization
   - Throughput improvement

**Checkpoint:** You understand network topology for AI systems

---

### Week 3: Advanced Infrastructure (Optional)

#### For HomeLab enthusiasts and production deployment

#### Day 1-2: Virtualization & GPU Passthrough
1. **[1201: Proxmox Hypervisor SOP](../phases/phase1-infra/1200-virtualization/1201-Proxmox-Hypervisor-SOP.md)**
   - Core pinning
   - RAM balloons
   - ZFS configurations

2. **[1202: GPU Passthrough (IOMMU/VFIO)](../phases/phase1-infra/1200-virtualization/1202-TB3-UT3G-Passthrough.md)**
   - IOMMU/VFIO GPU passthrough
   - eGPU configuration

3. **[1203: Nvidia Kernel Module](../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)**
   - DKMS setup
   - Driver stability

4. **[1204: Multi-GPU Setup](../phases/phase1-infra/1200-virtualization/1204-Multi-GPU-Setup.md)**
   - Multi-GPU configuration
   - Load balancing

#### Day 3-5: Kubernetes & Container Orchestration
1. **[1301: K3s Architecture](../phases/phase1-infra/1300-kubernetes/1301-K3s-Master-Worker-Arch.md)**
   - K3s cluster setup
   - Master-worker architecture
   - Service orchestration

2. **[1302: GPU Scheduler](../phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)**
   - GPU allocation in K8s
   - Resource management

3. **[1303: Storage Classes](../phases/phase1-infra/1300-kubernetes/1303-Storage-Classes.md)**
   - Dynamic provisioning
   - NFS integration

**Checkpoint:** You can deploy AI services to Kubernetes

---

## 🎯 Volume 1 Capstone: Project 001

### Build Your First AI Assistant

**[PROJECT-001: AI Assistant](../learning-resources/projects/PROJECT-001-AI-Assistant.md)** (4-6 hours)

**What You'll Build:**
- Complete AI assistant with memory
- Dockerized deployment
- API endpoints
- Web interface

**Skills Demonstrated:**
- Docker containerization ✅
- Ollama API integration ✅
- FastAPI development ✅
- Basic conversation memory ✅

**Requirements:**
- Complete TUTORIAL-001
- Complete LAB-001
- Understand Docker Compose

---

## 📋 Volume 1 Checklist

Use this checklist to track your progress:

### Core Content (Required)
- [ ] **QUICK-START.md** - Run your first LLM (30 min)
- [ ] **TUTORIAL-002: Docker Essentials** (90 min)
- [ ] **CHEAT-SHEET-001: Docker** (reference)
- [ ] **CHEAT-SHEET-002: Python AI** (reference)
- [ ] **LAB-001: Docker & LLM** (3 hours)
- [ ] **TUTORIAL-001: Hello LLM** (60 min)
- [ ] **1401: Ollama Enterprise** (45 min)
- [ ] **PROJECT-001: AI Assistant** (4-6 hours)

**Total Core Time:** ~12-15 hours

### Advanced Content (Optional)
- [ ] **1101: Internet Uplink & Modem Configuration**
- [ ] **1102: Star Topology Core**
- [ ] **1103: Jumbo Frames and MTU**
- [ ] **1201: Proxmox Hypervisor SOP**
- [ ] **1202: TB3 Passthrough**
- [ ] **1203: Nvidia Kernel Module**
- [ ] **1204: Multi-GPU Setup**
- [ ] **1301: K3s Architecture**
- [ ] **1302: GPU Scheduler**
- [ ] **1303: Storage Classes**

---

## 🔗 Cross-References

### Topics Covered in Volume 1 That Connect Later:

**Docker & Containers:**
- Volume 2: Docker for ML experiments
- Volume 4: Docker for inference engines
- Volume 7: Production Docker Compose

**Ollama & Local Models:**
- Volume 3: Understanding model internals
- Volume 4: Quantization for larger models
- Volume 5: Fine-tuning local models

**Network & Infrastructure:**
- Volume 6: Distributed RAG systems
- Volume 7: Production deployment

**Kubernetes:**
- Volume 4: vLLM on K3s
- Volume 7: Production orchestration

---

## 📊 Volume 1 Statistics

| Metric | Value |
|--------|-------|
| **Core Documents** | 8 files |
| **Optional Documents** | 10 files |
| **Tutorials** | 2 (TUTORIAL-001, TUTORIAL-002) |
| **Labs** | 1 (LAB-001) |
| **Cheat Sheets** | 2 (Docker, Python AI) |
| **Projects** | 1 (PROJECT-001) |
| **Estimated Time** | 12-15 hours (core) |
| **Difficulty** | ⭐ Beginner |

---

## 🆘 Troubleshooting

### Common Issues in Volume 1

**Problem:** Docker won't start
- **Solution:** Check [CHEAT-SHEET-001-Docker.md](../learning-resources/cheat-sheets/CHEAT-SHEET-001-Docker.md) for troubleshooting

**Problem:** Ollama slow on CPU
- **Solution:** Use smaller models (phi, gemma:2b) - see TUTORIAL-001

**Problem:** GPU not detected
- **Solution:** Check [1203: Nvidia Kernel Module](../phases/phase1-infra/1200-virtualization/1203-Nvidia-Kernel-Module.md)

For more help, see **[TROUBLESHOOTING-Common-Issues.md](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)**

---

## 🎓 After Volume 1

### You're Ready For:

**Volume 2: AI/ML Foundations** - Deep dive into the math and theory
**OR**

**Volume 3: LLM Internals** - Skip directly to understanding how transformers work

### Skills You've Gained:

```python
# You can now:
✅ Run LLMs locally
✅ Containerize applications
✅ Build AI services with APIs
✅ Deploy with Docker Compose
✅ Understand network topology
✅ Set up production infrastructure
```

---

## 🚀 Next Steps

1. **Track your progress** in [PROGRESS-TRACKER.md](../00-META/PROGRESS-TRACKER.md)
2. **Continue to Volume 2** for math and theory foundations
3. **OR skip to Volume 3** for transformer internals
4. **Review the [VOLUME-GUIDE.md](../00-META/VOLUME-GUIDE.md)** for alternative learning paths

---

**Volume 1 Status:** 🟢 Complete
**Maintainer:** AI Engineering Curriculum Team
