---
Document ID: CHEAT-SHEET-009
Title: "CHEAT-SHEET-009: Local Inference with llama.cpp & Ollama"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Beginner
Tags: ['cheatsheet', 'llamacpp', 'ollama', 'quantization']
---

# CHEAT-SHEET-009: Local Inference with llama.cpp & Ollama

## Quick Reference for Local LLM Serving

**Version:** 1.0

Two stacks dominate local inference: **llama.cpp** (a C++ runtime that runs
GGUF-quantized models on CPU, GPU or both) and **Ollama** (a model-manager
wrapped around llama.cpp with a registry and a REST API). This sheet maps
the everyday commands for both.

---

## Install

### llama.cpp

```bash
# macOS (Homebrew)
brew install llama.cpp

# From source with CUDA (Linux/Windows)
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON
cmake --build build --config Release -j
```

### Ollama

```bash
# macOS / Linux one-liner
curl -fsSL https://ollama.com/install.sh | sh

# Verify
ollama --version
```

---

## Getting a GGUF Model

```bash
# Pull a quantized checkpoint from Hugging Face
huggingface-cli download bartowski/Llama-3.2-3B-Instruct-GGUF \
  --include "*Q4_K_M*" --local-dir ./models
```

```bash
# Or let Ollama manage the download and the cache
ollama pull llama3.2:3b
ollama list
```

Quant-type rule of thumb: `Q4_K_M` is the default quality/size sweet spot,
`Q8_0` is near-lossless, `IQ4_XS`/`IQ2` families trade quality for the
smallest footprint (see module 4101 for the physics).

---

## llama.cpp: CLI and Server

```bash
# Single prompt
llama-cli -m ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -ngl 99 \              # offload all layers to GPU (0 = pure CPU)
  -c 8192 \              # context size
  -t 8 \                 # CPU threads for the remaining work
  -p "Explain KV cache in one paragraph."
```

```bash
# OpenAI-compatible local server
llama-server -m ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf \
  -ngl 99 -c 8192 --port 8080
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "local", "messages": [{"role": "user", "content": "hi"}]}'
```

---

## Ollama: Run, Serve, Customize

```bash
ollama run llama3.2:3b "Summarize attention."
ollama serve                             # REST API on :11434
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:3b", "prompt": "hi", "stream": false}'
```

```dockerfile
# Modelfile: pin a system prompt and sampling defaults
FROM llama3.2:3b
SYSTEM "You are a precise teaching assistant."
PARAMETER temperature 0.2
PARAMETER num_ctx 8192
```

```bash
ollama create tutor -f Modelfile
ollama run tutor "Define perplexity."
```

---

## Performance Knobs

| Knob | llama.cpp | Ollama |
| --- | --- | --- |
| GPU offload | `-ngl N` | `num_gpu` param |
| Context size | `-c` | `num_ctx` |
| CPU threads | `-t` | `num_thread` |
| Batch/ubatch | `-b` / `-ub` | `num_batch` |

```bash
# Measure before tuning: tokens/sec, prompt eval rate
llama-bench -m ./models/Llama-3.2-3B-Instruct-Q4_K_M.gguf -ngl 99
```

---

## Troubleshooting

```bash
# Out of memory on load
#   -> drop -ngl until it fits (offload fewer layers), or move to a
#      smaller quant (Q4_K_M -> IQ4_XS -> IQ3)

# Tokens/sec collapses after a while
#   -> context cache thrash: raise -c or trim the conversation;
#      check --no-mmap / --mlock for swap behavior

# Model downloads but refuses to load
#   -> GGUF version mismatch: update llama.cpp/Ollama; one repo,
#      one runtime version, verify with `ollama logs`

# Ollama pulls a 7B when you asked for 3B
#   -> tag syntax: `llama3.2:3b` not `llama3.2` (default tag is
#      the largest variant)

# CUDA build works but GPU idle
#   -> llama.cpp built without -DGGML_CUDA=ON: rebuild and confirm
#      the log prints the CUDA device at startup
```

---

**Quick Reference for:**

- [Module 1401: Ollama Enterprise](../../phases/phase1-infra/1400-llmops/1401-Ollama-Enterprise.md)
- [Module 1402: vLLM & TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [Module 4101: GGUF Physics](../../phases/phase4-quantization/4100-low-bit/4101-GGUF-Physics.md)
- [CHEAT-SHEET-007: vLLM Serving & Inference](./CHEAT-SHEET-007-vLLM-Serving.md)
