# AI Engineering Curriculum Notebooks

**Interactive Jupyter notebooks for hands-on learning**

---

## 📚 Overview

This directory contains Jupyter notebooks that provide practical, hands-on experience with the concepts covered in AI Engineering Curriculum. Each notebook is designed to be interactive and runnable, allowing you to experiment with code and see results in real-time.

---

## 🚀 Quick Start

### 1. Install Required Dependencies

Choose the appropriate environment file based on the notebook topic:

```bash
# For PyTorch notebooks (NB-201, NB-202)
conda env create -f environment-pytorch.yml
conda activate ai-engineering-curriculum-pytorch

# For Transformer notebooks (NB-301, NB-302, NB-303)
conda env create -f environment-transformers.yml
conda activate ai-engineering-curriculum-transformers

# For Fine-tuning notebooks (NB-501, NB-502, NB-503)
conda env create -f environment-finetuning.yml
conda activate ai-engineering-curriculum-finetuning

# For RAG notebooks (NB-601, NB-602, NB-603)
conda env create -f environment-rag.yml
conda activate ai-engineering-curriculum-rag
```

### 2. Start Jupyter Lab

```bash
# From the notebooks directory
cd docs/notebooks
jupyter lab
```

This will open Jupyter Lab in your browser at `http://localhost:8888`

### 3. Verify Installation

Run the following in a notebook cell to verify your setup:

```python
import torch
import sys

print(f"Python: {sys.version}")
print(f"PyTorch: {torch.__version__}")
print(f"CUDA Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"GPU: {torch.cuda.get_device_name(0)}")
```

---

## 📓 Available Notebooks

### Phase 2: AI/ML Foundations

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-201: PyTorch Basics](./NB-201-PyTorch-Basics.ipynb)** | Tensors, Autograd, Neural Networks | ⭐ Beginner | 2 hours | `environment-pytorch.yml` |
| **[NB-202: Deep Learning Fundamentals](./NB-202-Deep-Learning-Fundamentals.ipynb)** | Feed-forward networks, Training loops | ⭐⭐ Intermediate | 3 hours | `environment-pytorch.yml` |
| **[NB-203: NLP for LLMs](./NB-203-NLP-For-LLMs.ipynb)** | Tokenization, Embeddings, Language Models | ⭐⭐ Intermediate | 3 hours | `environment-pytorch.yml` |
| **[NB-204: Data Loading](./NB-204-Data-Loading.ipynb)** | Datasets, Dataloaders, Preprocessing | ⭐⭐ Intermediate | 2 hours | `environment-pytorch.yml` |
| **[NB-205: Evaluation Metrics](./NB-205-Evaluation-Metrics.ipynb)** | Accuracy, Loss, Custom Metrics | ⭐⭐ Intermediate | 2 hours | `environment-pytorch.yml` |

### Phase 3: LLM Internals

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-301: Self-Attention](./NB-301-Self-Attention.ipynb)** | Self-Attention from scratch | ⭐⭐⭐ Advanced | 4 hours | `environment-transformers.yml` |
| **[NB-302: Transformer Architecture](./NB-302-Transformer-Architecture.ipynb)** | Encoder-Decoder, Multi-Head | ⭐⭐⭐ Advanced | 4 hours | `environment-transformers.yml` |
| **[NB-303: GPT Implementation](./NB-303-GPT-Implementation.ipynb)** | Build GPT from scratch | ⭐⭐⭐ Advanced | 6 hours | `environment-transformers.yml` |

### Phase 4: Quantization

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-401: Quantization](./NB-401-Quantization.ipynb)** | INT8, FP16 quantization | ⭐⭐ Intermediate | 3 hours | `environment-transformers.yml` |
| **[NB-402: GPTQ Quantization](./NB-402-GPTQ-Quantization.ipynb)** | GPTQ algorithm | ⭐⭐⭐ Advanced | 4 hours | `environment-finetuning.yml` |
| **[NB-403: KV Cache Optimization](./NB-403-KV-Cache-Optimization.ipynb)** | KV Cache, Context Window | ⭐⭐⭐ Advanced | 3 hours | `environment-transformers.yml` |

### Phase 5: Fine-Tuning

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-501: LoRA Fine-tuning](./NB-501-LoRA-Fine-tuning.ipynb)** | LoRA implementation | ⭐⭐⭐ Advanced | 4 hours | `environment-finetuning.yml` |
| **[NB-502: DPO Alignment](./NB-502-DPO-Alignment.ipynb)** | DPO training | ⭐⭐⭐ Advanced | 4 hours | `environment-finetuning.yml` |
| **[NB-503: Synthetic Data Generation](./NB-503-Synthetic-Data-Generation.ipynb)** | Generate training data | ⭐⭐⭐ Advanced | 3 hours | `environment-finetuning.yml` |

### Phase 6: RAG & Data Systems

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-601: Building RAG](./NB-601-Building-RAG.ipynb)** | Basic RAG system | ⭐⭐ Intermediate | 4 hours | `environment-rag.yml` |
| **[NB-602: Advanced RAG Techniques](./NB-602-Advanced-RAG-Techniques.ipynb)** | Hybrid search, Re-ranking | ⭐⭐⭐ Advanced | 5 hours | `environment-rag.yml` |
| **[NB-603: Vector Databases](./NB-603-Vector-Databases.ipynb)** | Qdrant, Pinecone, Weaviate | ⭐⭐ Intermediate | 3 hours | `environment-rag.yml` |

### Phase 7: Agentic Systems

| Notebook | Topic | Difficulty | Time | Environment |
|----------|-------|------------|------|-------------|
| **[NB-701: Agentic System](./NB-701-Agentic-System.ipynb)** | ReAct Agent | ⭐⭐⭐ Advanced | 5 hours | `environment-rag.yml` |
| **[NB-702: Agent Memory Systems](./NB-702-Agent-Memory-Systems.ipynb)** | Memory management | ⭐⭐⭐ Advanced | 4 hours | `environment-rag.yml` |
| **[NB-703: Agent Security](./NB-703-Agent-Security.ipynb)** | Security best practices | ⭐⭐⭐ Advanced | 3 hours | `environment-rag.yml` |

---

## 💻 Hardware Requirements

### Minimum Requirements
- **CPU:** 4+ cores
- **RAM:** 16GB
- **Storage:** 50GB free space
- **GPU:** Not required for basic notebooks

### Recommended Requirements
- **CPU:** 8+ cores
- **RAM:** 32GB+
- **Storage:** 200GB+ SSD
- **GPU:** NVIDIA GPU with 8GB+ VRAM (for GPU acceleration)

### GPU Requirements by Notebook
| Notebook | GPU Required | VRAM Needed |
|----------|--------------|-------------|
| NB-201 to NB-205 | Optional | 4GB+ |
| NB-301 to NB-303 | Optional | 8GB+ |
| NB-401 to NB-403 | Optional | 8GB+ |
| NB-501 | **Required** | 12GB+ |
| NB-502 | **Required** | 12GB+ |
| NB-503 | **Required** | 12GB+ |
| NB-601 to NB-603 | Optional | 8GB+ |
| NB-701 to NB-703 | Optional | 8GB+ |

---

## 🔧 Troubleshooting

### Common Issues

#### Issue: CUDA Out of Memory
**Solution:** Reduce batch size or use CPU instead
```python
# Use CPU
device = "cpu"

# Or reduce batch size
batch_size = 8  # Reduce from 32
```

#### Issue: Module Not Found
**Solution:** Ensure correct environment is activated
```bash
# Check active environment
conda info --envs

# Install missing package
pip install missing-package
```

#### Issue: Notebook Won't Open
**Solution:** Check Jupyter Lab version
```bash
# Update Jupyter Lab
uv pip install --upgrade jupyterlab
```

#### Issue: Slow Performance
**Solution:** Enable GPU acceleration
```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)
```

---

## 📖 How to Use Notebooks

### About TODO Comments

> **📝 Educational Design Note:**
>
> Many notebooks contain `# TODO:` comments followed by working code. These are **NOT** incomplete tasks - they are **educational prompts** designed to:
>
> 1. **Invite exploration** - Run the code and observe what happens
> 2. **Encourage experimentation** - Modify parameters and see the results
> 3. **Guide learning** - The code demonstrates the concept being taught
> 4. **Provide reference** - Use as a template for your own experiments
>
> **Example:**
> ```python
> # TODO: Create tensors
> x = torch.tensor([1, 2, 3, 4])  # ✅ This code works! Run it!
> ```
>
> The `# TODO:` marks **what you should learn** from this cell, not what you need to implement.

### Best Practices

1. **Read the documentation first** - Review the corresponding module documentation before running the notebook

2. **Run cells in order** - Notebooks are designed to be run sequentially from top to bottom

3. **Experiment freely** - Modify parameters, try different inputs, and observe results

4. **Save your work** - Notebooks auto-save, but create copies before major experiments

5. **Use GPU when available** - GPU acceleration significantly speeds up training

6. **Ask questions** - If something doesn't make sense, review the documentation or ask in community forums

### Learning Path

**Beginner Path:**
1. Start with NB-201 (PyTorch Basics)
2. Move to NB-202 (Deep Learning Fundamentals)
3. Try NB-203 (NLP for LLMs)
4. Complete NB-204 (Data Loading) and NB-205 (Evaluation Metrics)

**Intermediate Path:**
1. Begin with NB-301 (Self-Attention)
2. Move to NB-302 (Transformer Architecture)
3. Try NB-401 (Quantization)
4. Complete NB-601 (Building RAG)

**Advanced Path:**
1. Start with NB-303 (GPT Implementation)
2. Move to NB-501 (LoRA Fine-tuning)
3. Try NB-502 (DPO Alignment)
4. Complete NB-701 (Agentic System)

---

## 🔄 Keeping Notebooks Updated

Notebooks are regularly updated with:
- Bug fixes
- Performance improvements
- New examples
- Updated dependencies

**Update Procedure:**
```bash
# Pull latest changes
git pull origin main

# Update environment
conda env update -f environment-[name].yml
```

---

## 🤝 Contributing

Found an issue with a notebook? Contributions welcome!

1. Test the notebook thoroughly
2. Document the issue clearly
3. Suggest improvements
4. Submit a pull request if you have a fix

---

## 📞 Getting Help

- **Documentation:** See corresponding module documentation
- **Troubleshooting:** Check TROUBLESHOOTING-Common-Issues.md
- **Community:** Ask in forums or discussion boards
- **Issues:** Report bugs via GitHub issues

---

**Last Updated:** 2026-02-08
**Total Notebooks:** 22
**Difficulty Levels:** Beginner (5), Intermediate (8), Advanced (9)
