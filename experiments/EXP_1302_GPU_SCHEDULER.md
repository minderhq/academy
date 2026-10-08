---
Document ID: EXP_1302
Title: "EXP_1302_GPU_SCHEDULER: GPU Scheduler Configuration"
Last Updated: 2026-10-07
Status: Complete
Difficulty: Intermediate
---

# EXP_1302_GPU_SCHEDULER: GPU Scheduler Configuration

## Experiment Information
- **Infrastructure Used:** Kubernetes cluster with a GPU worker node
- **Model:** Llama-3.1-8B running in K3s pod
- **Framework:** vLLM with tensor-parallel-size=1

## Experiment Setup
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: llama-inference
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:v0.30.0
    resources:
      limits:
        nvidia.com/gpu: 1
        memory: "10Gi"
```

## Measurements

### Memory Utilization
```bash
nvidia-smi dmon:

# gpu    sm    mem    enc    dec    jpg    jpeg    frm
# Idx    %      %      %      %      %      %      %      %
  0     95     82      0      0      0      0      0      0

GPU: Any NVIDIA GPU with 11GB+ VRAM
Model: Llama-3.1-8B @ 4-bit quantization
Weights: ~4.5 GB
KV Cache: ~0.6 GB @ 4096 context (GQA)
Activations: ~1 GB
Total: ~6.1 GB (fits with room to spare)
```

### Throughput
```text
vLLM @ 4-bit, context=2048:
  Tokens/sec: ~85-95
  Batch Size: 1
  Temperature: 0.7
```

## Configuration Tuning

### GPU Memory Fraction
```python
gpu_memory_utilization=0.9  # Default
# Tested: 0.7, 0.8, 0.9, 0.95

# Results:
# 0.7:  Can't use 4096 context
# 0.8: Works, ~70 tokens/sec
# 0.9: Sweet spot, ~90 tokens/sec
# 0.95: OOM errors with longer sequences
```

### Batch Size Optimization
```text
| Batch | Tokens/sec | VRAM Usage |
|-------|------------|------------|
| 1     | 90         | 8.2 GB     |
| 2     | 150        | 9.1 GB     |
| 4     | 200        | 10.5 GB    |
| 8     | OOM        | -          |

Optimal batch size: 4 for an 11GB-class GPU
```

## Lessons Learned
- 7B model @ 4-bit fits comfortably
- 13B model would need GPU memory optimization
- Batch size 4 gives best throughput

## Next Steps
- [ ] Test with 13B model
- [ ] Enable Flash Attention 2
- [ ] Benchmark with EXL2 quantization

## Related Files
- [1302-GPU-Scheduler.md](../docs/phases/phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)
- [1402-vLLM-and-TGI.md](../docs/phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
