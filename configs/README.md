---
Document ID: CONFIGS-README
Title: "Configuration Templates"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
---

# Configuration Templates

Reference deployment configuration for the PROJECT-OMEGA course. Everything
here is hardware-agnostic: it runs on any Docker-capable Linux host — a home
server, a workstation, a NAS with Container Manager, or a cloud VM.

## Contents

| Path | Purpose |
|------|---------|
| `docker-compose.yml` | Minimal self-hosted LLM stack: vLLM (GPU inference) + Qdrant (vector database), with Ollama as a commented alternative |
| `.env.example` | Environment template for the compose file — copy to `.env` and edit |
| `performance-testing/k6/load-test.js` | Load tests for the inference API (latency, TTFT, throughput) |

## Requirements

- Docker Engine 24+ with the Compose plugin
- Optional: an NVIDIA GPU with 8GB+ VRAM and the
  [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
  for vLLM. Without a GPU, use the commented Ollama service or point your
  application at any OpenAI-compatible remote endpoint.

## Quick Start

```bash
cd configs
cp .env.example .env    # edit MODEL / HF_TOKEN as needed
docker compose up -d

# Verify
curl http://localhost:8000/v1/models        # vLLM
curl http://localhost:6333/collections      # Qdrant
```

## Model Sizing

Pick a model that fits your VRAM (AWQ 4-bit quantized sizes shown):

| Model class | VRAM needed | Example cards |
|-------------|-------------|---------------|
| 7B–8B AWQ | ~6–7 GB | 8GB+ consumer GPU |
| 13–14B AWQ | ~10–12 GB | 12GB+ consumer GPU |
| 32B AWQ | ~22–24 GB | 24GB GPU |
| 70B AWQ | ~40+ GB | multi-GPU or 48GB+ |

Tune `MAX_MODEL_LEN` in `.env` down if you hit out-of-memory errors — KV cache
shares the same VRAM pool as the weights.

## Load Testing

```bash
k6 run -e BASE_URL=http://localhost:8000 performance-testing/k6/load-test.js
```

Reports request latency, time-to-first-token (TTFT), and token throughput
against the OpenAI-compatible `/v1/chat/completions` endpoint.

## Related Course Material

- [1404: vLLM Production Deployment](../docs/phases/phase1-infra/1400-llmops/guides/1404-vLLM-Production-Deployment.md)
- [1405: TGI Deployment Guide](../docs/phases/phase1-infra/1400-llmops/guides/1405-TGI-Deployment-Guide.md)
- [1501: Monitoring and Observability](../docs/phases/phase1-infra/1500-monitoring/1501-Monitoring-and-Observability.md)
- [6303: Neo4j Deployment Guide](../docs/phases/phase6-rag/6300-context/guides/6303-Neo4j-Deployment-Guide.md)
- [6403: Qdrant Production Deployment](../docs/phases/phase6-rag/6400-vector-databases/guides/6403-Qdrant-Production-Deployment.md)

## Security Notes

- Never commit your `.env`; the compose file reads secrets from it.
- The stack binds to localhost by default. For LAN exposure, put a reverse
  proxy with TLS in front (see Phase 1's LLMOps module) and change all
  default credentials.
