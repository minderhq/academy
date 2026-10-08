---
Document ID: PREREQUISITES-001
Title: "PROJECT-001: Prerequisites & Setup Guide"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Intermediate
Tags: ['prerequisites', 'project', 'setup']
---

# PROJECT-001: Prerequisites & Setup Guide

**For:** [PROJECT-001: Build Your AI Assistant](./PROJECT-001-AI-Assistant.md)

**Estimated Setup Time:** 2-3 hours

**Difficulty:** ⭐⭐ Intermediate

---

## Overview

PROJECT-001 is a comprehensive AI assistant combining RAG, ReAct agents, and tool calling. This guide ensures you have everything needed before starting.

---

## Project Overview

**What You'll Build:**

- RAG-powered knowledge base assistant
- ReAct agent with tool calling
- Vector database (Qdrant)
- LLM integration (Ollama)
- REST API with FastAPI
- Docker deployment

**Estimated Duration:** 15-25 hours

**Team Size:** 1-2 developers

---

## Prerequisites Checklist

### Technical Knowledge

**Required:**

- [ ] Intermediate Python (classes, async, type hints)
- [ ] Basic Docker knowledge (containers, compose)
- [ ] REST API concepts (endpoints, JSON)
- [ ] Git basics (clone, commit, push)

**Helpful but Not Required:**

- [ ] FastAPI experience
- [ ] Vector database concepts
- [ ] LLM integration patterns

### Hardware Requirements

**Minimum:**

- CPU: 4 cores
- RAM: 16GB
- Storage: 50GB SSD
- Network: Stable internet

**Recommended:**

- CPU: 8+ cores
- RAM: 32GB
- Storage: 100GB NVMe SSD
- GPU: 8GB+ VRAM (optional)

---

## Software Requirements

### Essential Software

1. **Docker & Docker Compose**
2. **Python 3.13+**
3. **Ollama**
4. **Git**

### Verify Installation

```bash
docker --version
docker compose version
python --version
ollama --version
git --version
```

---

## Infrastructure Components

### Databases

**Qdrant (Vector Database):**

- Port: 6333
- Memory: 1-2GB

**PostgreSQL (Optional):**

- Port: 5432
- Memory: 512MB

### LLM Server

**Ollama:**

- Port: 11434
- Memory: 4-8GB

---

## Pre-Project Learning

**Before starting PROJECT-001, complete:**

1. [TUTORIAL-003: RAG Basics](../tutorials/TUTORIAL-003-RAG-Basics.md) (2 hours)
2. [LAB-002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md) (3 hours)
3. [LAB-004: ReAct Agent](../labs/LAB-004-ReAct-Agent.md) (4 hours)

---

## Setup Verification Checklist

Before starting PROJECT-001:

### Infrastructure
- [ ] Docker installed and running
- [ ] Ollama installed with model

### Services
- [ ] Qdrant accessible
- [ ] Ollama responding

### Knowledge
- [ ] Completed RAG tutorial
- [ ] Completed RAG lab
- [ ] Completed ReAct lab

---

## Ready to Start?

**All checks passed?** Start building: [PROJECT-001: Build Your AI Assistant](./PROJECT-001-AI-Assistant.md)

**Need help?** Check:

- [ENVIRONMENT-SETUP.md](../../00-META/ENVIRONMENT-SETUP.md)
- [LAB-000: Environment Setup](../labs/LAB-000-ENVIRONMENT-SETUP.md)

---

**Setup Duration:** 2-3 hours

**Completed:** [ ] Yes / [ ] No

**Date:** _____________
