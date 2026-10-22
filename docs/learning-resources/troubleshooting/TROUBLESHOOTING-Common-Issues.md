---
Document ID: TROUBLESHOOTING-Common-Issues
Title: "TROUBLESHOOTING: Common Issues & Solutions"
Last Updated: 2026-10-22
Status: Complete
Difficulty: Intermediate
Tags: ['troubleshooting', 'docker', 'llm']
---

# TROUBLESHOOTING: Common Issues & Solutions

**Solutions to the most common problems encountered during learning**

---

## Docker Issues

### Issue: Container won't start

**Symptoms:**
```text
Error: Cannot connect to the Docker daemon
docker: Error response from daemon: ...
```

**Solutions:**

1. **Check if Docker is running:**
```bash
# Linux/Mac
sudo systemctl status docker

# Windows
# Check Docker Desktop is running
```

2. **Restart Docker daemon:**
```bash
sudo systemctl restart docker
```

3. **Check if port is already in use:**
```bash
# Linux/Mac
netstat -tulpn | grep ${PORT}
lsof -i :${PORT}

# Windows
netstat -ano | findstr ${PORT}
```

**Solution:** Change the port mapping or stop the conflicting service.

---

### Issue: Out of Memory (OOM)

**Symptoms:**
```text
ERROR: for <container> Cannot start service ...
OCI runtime create failed: container_linux.go:370: starting container process caused: process_linux.go:459: container init caused "write /proc/self/attr/keycreate: invalid argument"
```

**Solutions:**

1. **Increase Docker memory limit (Docker Desktop):**
    - Settings → Resources → Memory → Increase to 8GB+

2. **Check container memory usage:**
```bash
docker stats
```

3. **Limit container memory:**
```bash
docker run -m 512m myapp
```

---

### Issue: GPU not accessible in container

**Symptoms:**
```bash
Error: could not select device driver
nvidia-smi not found
```

**Solutions:**

1. **Install NVIDIA Container Toolkit:**
```bash
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed "s#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#" | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

2. **Test GPU container:**
```bash
docker run --rm --gpus all nvidia/cuda:13.0.2-base-ubuntu24.04 nvidia-smi
```

3. **Check GPU availability on host:**
```bash
nvidia-smi
```

- **[Docker Commands](../cheat-sheets/CHEAT-SHEET-001-Docker.md)** - Containers, images, volumes and networking in one page.
- **[Virtualization and GPU Passthrough - the Hypervisor RAM Ledger, the Passthrough Gate Chain, and the Multi-GPU Scaling Wall](../cheat-sheets/CHEAT-SHEET-055-Virtualization-and-GPU-Passthrough.md)** - The hypervisor RAM ledger, the IOMMU group verdict, the passthrough gate chain, the Thunderbolt tunnel bill, the kernel module ledger, the multi-GPU scaling wall, and the NCCL peer wall.

---

## LLM Issues

### Issue: Model download fails

**Symptoms:**
```text
Error: failed to load model
Connection timeout during download
```

**Solutions:**

1. **Check internet connection and proxy settings:**
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

2. **Use mirror for Hugging Face models:**
```python
import os
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from transformers import AutoModel
model = AutoModel.from_pretrained("model-name")
```

3. **Download model manually:**
```bash
# Install git-lfs
git lfs install

# Clone model repo
git clone https://huggingface.co/model-name
```

---

### Issue: CUDA out of memory

**Symptoms:**
```text
RuntimeError: CUDA out of memory. Tried to allocate XYZ MiB
```

**Solutions:**

1. **Reduce batch size:**
```python
batch_size = 1  # Reduce from larger value
```

2. **Enable gradient checkpointing:**
```python
model.gradient_checkpointing_enable()
```

3. **Use 4-bit quantization:**
```python
from transformers import AutoModelForCausalLM
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.float16
)

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    quantization_config=bnb_config
)
```

4. **Reduce sequence length:**
```python
max_length = 512  # Reduce from 2048 or 4096
```

5. **Clear CUDA cache:**
```python
import torch
torch.cuda.empty_cache()
```

---

### Issue: Slow inference

**Symptoms:**

- Model takes >10 seconds per token
- GPU utilization is low

**Solutions:**

1. **Use vLLM or TGI instead of raw PyTorch:**
```bash
vllm serve model-name --gpu-memory-utilization 0.9
```

2. **Enable Flash Attention:**
```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    attn_implementation="flash_attention_2"
)
```

3. **Batch requests:**
```python
# Process multiple prompts at once
outputs = model.batch_generate(prompts)
```

4. **Use CPU offloading for large models:**
```python
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    device_map="auto",
    offload_folder="offload"
)
```

- **[Local Inference with llama.cpp & Ollama](../cheat-sheets/CHEAT-SHEET-009-Local-Inference.md)** - GGUF downloads, llama.cpp build/serve flags, Ollama run and Modelfile customization, and offload tuning for local machines.
- **[Quantization Formats & Methods](../cheat-sheets/CHEAT-SHEET-015-Quantization-Formats-Methods.md)** - The bpw block arithmetic behind Q4_0/Q4_K, the three GGUF families, and the EXL2/AWQ/GPTQ GPU-only map.
- **[vLLM Serving & Inference](../cheat-sheets/CHEAT-SHEET-007-vLLM-Serving.md)** - Serving, quantization, parallelism and tuning flags for the vLLM inference server.
- **[Flash Attention](../cheat-sheets/CHEAT-SHEET-020-Flash-Attention.md)** - The memory-hierarchy argument, the online-softmax block update, the FA1-FA2-FA3 ladder, the three enablement paths, and the when-not rules.

---

## RAG Issues

### Issue: Poor retrieval quality

**Symptoms:**

- Retrieved documents not relevant to query
- Answers are generic or unhelpful

**Solutions:**

1. **Improve chunking strategy:**
```python
# Use smaller chunks with overlap
chunker = DocumentChunker(
    chunk_size=256,  # Smaller chunks
    chunk_overlap=50,
    method="recursive"  # Try "semantic" instead
)
```

2. **Try different embedding models:**
```python
# Better quality models
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-mpnet-base-v2')  # Better but slower
model = SentenceTransformer('all-MiniLM-L6-v2')   # Faster but simpler
```

3. **Add re-ranking:**
```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder('ms-marco-MiniLM-L-6-v2')
reranked = reranker.rank(query, results, top_k=5)
```

4. **Use hybrid search (keyword + semantic):**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import QueryRequest

# Combine BM25 and vector search
results = qdrant.query_batch_points(
    collection_name="docs",
    requests=[
        QueryRequest(
            query=vector,
            limit=10,
            with_payload=True
        )
    ]
)
```

---

### Issue: Qdrant connection fails

**Symptoms:**
```text
ConnectionError: Failed to connect to Qdrant
urllib3.exceptions.MaxRetryError
```

**Solutions:**

1. **Check if Qdrant is running:**
```bash
curl http://localhost:6333/
```

2. **Check Docker logs:**
```bash
docker logs qdrant
```

3. **Verify port is not blocked by firewall:**
```bash
# Linux
sudo ufw allow 6333/tcp

# Check if port is listening
netstat -tulpn | grep 6333
```

4. **Check Qdrant health:**
```bash
curl http://localhost:6333/health
```

- **[Retrieval Strategies - the Two-Channel Fusion, the Rerank Funnel, and the Diversity Dial](../cheat-sheets/CHEAT-SHEET-047-Retrieval-Strategies.md)** - BM25 and the dense channel, RRF and the alpha dial joining them, the cross-encoder rerank funnel, the MMR diversity dial, and the provenance boost.
- **[RAG Systems](../cheat-sheets/CHEAT-SHEET-005-RAG-Systems.md)** - Chunking, embedding, retrieval and generation parameters at a glance.
- **[Semantic Vectors - the HNSW Ledger, the Recall Dial, and the Truncation Contract](../cheat-sheets/CHEAT-SHEET-048-Semantic-Vectors.md)** - What the vector is, how cosine and dot measure closeness, the HNSW walk with its ef dial, the MRL truncation contract, and the anisotropy trap.
- **[Vector Databases - the RAM Ledger, the Quantile Trap, and the Rescore Ladder](../cheat-sheets/CHEAT-SHEET-053-Vector-Databases.md)** - The RAM ledger arithmetic, the distance trio, the SQ quantile trap, binary and product quantization floors, the oversample x rescore ladder, and the snapshot RPO bill.

---

## Fine-Tuning Issues

### Issue: Training loss not decreasing

**Symptoms:**

- Loss stays flat or increases
- Model doesn't learn

**Solutions:**

1. **Check learning rate:**
```python
# Try different learning rates
learning_rate = 2e-4  # Common starting point
learning_rate = 1e-4  # Lower if unstable
learning_rate = 5e-4  # Higher if too slow
```

2. **Increase dataset size:**
- 10-100 samples for testing
- 1000+ samples for real fine-tuning

3. **Check data quality:**
```python
# Remove duplicates
data = list(set(data))

# Filter too short samples
data = [d for d in data if len(d['text']) > 100]

# Balance classes
from collections import Counter
print(Counter([d['label'] for d in data]))
```

4. **Reduce batch size if memory constrained:**
```python
per_device_train_batch_size = 1
gradient_accumulation_steps = 8  # Effective batch = 1 * 8 = 8
```

---

### Issue: LoRA adapters not loading

**Symptoms:**
```text
ValueError: Cannot load PeftModel
KeyError: 'base_model.model.model.layers'
```

**Solutions:**

1. **Check base model compatibility:**
```python
# Must use same base model as during training
base_model = "Qwen/Qwen3-8B"
```

2. **Verify PEFT version:**
```bash
uv pip show peft
# Should be >= 0.7.0
uv pip install --upgrade peft
```

3. **Load adapter explicitly:**
```python
from transformers import AutoModelForCausalLM
from peft import PeftModel

model = AutoModelForCausalLM.from_pretrained(base_model)
model = PeftModel.from_pretrained(model, adapter_path)
```

- **[Advanced Optimization - the Optimizer Memory Ledger, the Schedule Arc, and the Failure Toolbox](../cheat-sheets/CHEAT-SHEET-046-Advanced-Optimization.md)** - The optimizer memory ledger, Adam's scale-free first step, the warmup-decay schedule arc, the failure toolbox, SAM's flat-minima search, and the LR range test.
- **[LoRA & QLoRA](../cheat-sheets/CHEAT-SHEET-016-LoRA-QLoRA.md)** - The low-rank arithmetic and the three knobs, the QLoRA 4-bit pipeline, and the merge-on-FP16 rule.

---

## Python Environment Issues

### Issue: Import errors

**Symptoms:**
```text
ModuleNotFoundError: No module named 'transformers'
ImportError: cannot import name 'AutoModel'
```

**Solutions:**

1. **Check Python version:**
```bash
python --version
# Should be 3.8+ for most ML libraries
```

2. **Install in correct environment:**
```bash
# Create the project environment with uv
uv venv --python 3.13
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows

# Install from the project manifest (pyproject.toml + uv.lock)
uv sync --locked
```

3. **Verify installation:**
```bash
uv pip list | grep transformers
```

4. **Check import path:**
```python
import sys
print(sys.path)

# Add custom path if needed
sys.path.append('/path/to/module')
```

---

### Issue: Version conflicts

**Symptoms:**
```text
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
TypeError: __init__() got an unexpected keyword argument
```

**Solutions:**

1. **Reinstall with uv's resolver:**
```bash
uv pip install --reinstall package-name
```

2. **Create fresh environment:**
```bash
# Recreate the exact environment from the project lock
rm -rf .venv && uv sync --locked
```

3. **Pin exact versions:**
```toml
# pyproject.toml - exact pins recorded by uv add
dependencies = [
    "transformers==5.10.2",
    "torch==2.12.0",
    "peft==0.19.1",
]
```

4. **Use conda for better dependency management:**
```bash
conda create -n ml-env python=3.13
conda activate ml-env
conda install pytorch torchvision torchaudio pytorch-cuda=12.1 -c pytorch -c nvidia
pip install transformers
```

- **[Python for AI/ML](../cheat-sheets/CHEAT-SHEET-002-Python-AI.md)** - The Python idioms, libraries and snippets used across the curriculum.

---

## Network Issues

### Issue: Proxy blocking downloads

**Symptoms:**
```text
SSLError: HTTPSConnectionPool
ProxyError: Unable to connect to proxy
```

**Solutions:**

1. **Set environment variables:**
```bash
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
export NO_PROXY=localhost,127.0.0.1
```

2. **Set the proxy per command** (uv and pip both honor the variables above):
```bash
HTTPS_PROXY=http://proxy.example.com:8080 uv pip install package-name
```

3. **Use Hugging Face mirror:**
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

---

### Issue: Git clone fails

**Symptoms:**
```text
fatal: unable to access 'https://github.com/.../'
Failed to connect to github.com
```

**Solutions:**

1. **Use SSH instead of HTTPS:**
```bash
git clone git@github.com:user/repo.git
```

2. **Configure Git proxy:**
```bash
git config --global http.proxy http://proxy.example.com:8080
git config --global https.proxy http://proxy.example.com:8080
```

3. **Use mirror sites:**
```bash
# Gitee mirror for Chinese users
git clone https://gitee.com/mirrors/repo.git
```

---

## Storage Issues

### Issue: Disk space full

**Symptoms:**
```text
No space left on device
ERROR: write error
```

**Solutions:**

1. **Check disk usage:**
```bash
df -h
du -sh ~/* | sort -h
```

2. **Clean Docker:**
```bash
# Remove unused images
docker image prune -a

# Remove unused containers
docker container prune

# Remove unused volumes
docker volume prune

# Remove everything unused
docker system prune -a --volumes
```

3. **Clean package cache (uv):**
```bash
uv cache clean
```

4. **Clean model cache:**
```bash
# Hugging Face cache
rm -rf ~/.cache/huggingface

# Ollama models
rm -rf ~/.ollama/models
```

- **[Linux Commands for AI/ML](../cheat-sheets/CHEAT-SHEET-004-Linux.md)** - Shell commands, permissions and process management on the lab machines.

---

## Performance Issues

### Issue: High GPU memory usage

**Symptoms:**

- nvidia-smi shows high memory usage
- Other applications can't use GPU

**Solutions:**

1. **Reduce model size:**
```python
# Use smaller model
model_name = "mistralai/Mistral-7B"  # Instead of 70B
```

2. **Enable quantization:**
```python
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)
```

3. **Limit memory fraction:**
```python
import torch
torch.cuda.set_per_process_memory_fraction(0.7)
```

4. **Kill zombie processes:**
```bash
# Find processes using GPU
nvidia-smi

# Kill specific process
kill -9 ${PID}
```

- **[Quantization Formats & Methods](../cheat-sheets/CHEAT-SHEET-015-Quantization-Formats-Methods.md)** - The bpw block arithmetic behind Q4_0/Q4_K, the three GGUF families, and the EXL2/AWQ/GPTQ GPU-only map.

---

## Monitoring Issues

### Issue: Grafana dashboards not loading

**Symptoms:**

- Dashboard shows "No data"
- Panel errors

**Solutions:**

1. **Check Prometheus is running:**
```bash
curl http://localhost:9090/-/healthy
```

2. **Verify datasource configuration:**
```bash
# Check Grafana datasources
curl http://localhost:3000/api/datasources
```

3. **Check Prometheus targets:**
```bash
curl http://localhost:9090/api/v1/targets
```

4. **Restart Grafana:**
```bash
docker restart grafana
```

- **[LLM Observability](../cheat-sheets/CHEAT-SHEET-033-LLM-Observability.md)** - The four LLM-specific metric families and their alert thresholds, the timing trio with its decode-rate trap, the hallucination ladder, and the nearest-rank percentile rule.

---

## Emergency Commands

### Force stop all containers:
```bash
docker kill $(docker ps -aq)
```

### Remove all containers:
```bash
docker rm -f $(docker ps -aq)
```

### Factory reset Docker:
```bash
# ⚠️ WARNING: Deletes all data!
docker system prune -a --volumes -f
```

### Reboot machine (last resort):
```bash
sudo reboot
```

---

## Getting Help

If you're still stuck:

1. **Check logs:**
```bash
docker logs ${CONTAINER_NAME}
journalctl -u docker
```

2. **Search error messages:**
    - Google the exact error
    - Check Stack Overflow
    - GitHub Issues

3. **Ask in communities:**
    - Discord servers
    - Reddit (r/LocalLLaMA, r/MachineLearning)
    - Hugging Face Forums

---

## Quick Links

- **[TUTORIAL-001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - Getting started
- **[TUTORIAL-002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker basics
- **[LAB-001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Troubleshooting in practice
- **[1501: Monitoring and Observability](../../phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)** - Debug with observability

---

**Need more help?** Check the specific documentation for the service you're using.
