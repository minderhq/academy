---
Document ID: CHEAT-SHEET-008
Title: "CHEAT-SHEET-008: Reasoning Models & Test-Time Compute"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'reasoning', 'inference', 'serving']
---

# CHEAT-SHEET-008: Reasoning Models & Test-Time Compute

## Quick Reference for Reasoning-Model Inference

**Version:** 1.0

Reasoning models emit a chain-of-thought trace before the final answer. That
trace is a separate output channel (`reasoning_content`) distinct from the
answer (`content`), it consumes context and latency, and it is controlled
through budget knobs - effort levels, thinking budgets, or soft switches.

---

## Serving an Open Reasoning Model

```bash
# DeepSeek-R1-style checkpoints: the reasoning parser routes the
# <think>...</think> trace into reasoning_content
vllm serve deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
  --reasoning-parser deepseek_r1 \
  --max-model-len 16384
```

```bash
# Qwen3 checkpoints: same parser family
vllm serve Qwen/Qwen3-8B \
  --reasoning-parser qwen3 \
  --max-model-len 16384
```

```bash
# Or with Docker (no local install needed)
docker run --gpus all -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  vllm/vllm-openai:latest \
  --model deepseek-ai/DeepSeek-R1-Distill-Qwen-7B \
  --reasoning-parser deepseek_r1
```

---

## The Two-Channel Output

```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The answer is 42.",
      "reasoning_content": "First I restate the problem, then..."
    }
  }],
  "usage": {
    "completion_tokens": 512,
    "completion_tokens_details": {"reasoning_tokens": 480}
  }
}
```

- `content` - what you show the user.
- `reasoning_content` - the trace; log it, never concatenate it into chat
  history as a user-visible turn.
- `reasoning_tokens` - billed and context-consuming; monitor it per request.

---

## Reasoning Effort (Hosted Reasoning Endpoints)

```python
from openai import OpenAI

client = OpenAI()
resp = client.chat.completions.create(
    model="o4-mini",
    reasoning_effort="low",          # low | medium | high
    max_completion_tokens=4096,      # covers trace + answer
    messages=[{"role": "user", "content": "Prove that sqrt(2) is irrational."}],
)
print(resp.choices[0].message.content)
```

- `reasoning_effort` trades trace length against latency and cost.
- Reasoning endpoints reject custom sampling on many models: drop
  `temperature` / `top_p` rather than debugging 400s.
- `max_completion_tokens` replaces `max_tokens` on these endpoints - the
  trace and the answer share this ceiling.

---

## Extended Thinking (Anthropic-Style Budget)

```python
resp = client.messages.create(
    model="claude-sonnet-5-5",
    max_tokens=16000,                # must exceed budget_tokens
    thinking={
        "type": "enabled",
        "budget_tokens": 10000,      # ceiling for the trace
    },
    messages=[{"role": "user", "content": "Design a rate limiter."}],
)
```

- `budget_tokens` caps the thinking phase; `max_tokens` caps the whole turn
  and must be strictly larger than the budget.
- Thinking tokens are billed as output tokens and cannot be turned into a
  cache hit mid-trace.

---

## Qwen3 Soft Switches

```bash
# Inline switches ride inside the user turn:
#   "How many R's in strawberry? /no_think"   -> skips the trace
#   "Solve this IMO problem. /think"          -> forces the trace
```

```python
# Or at the template level (chat-template kwarg):
resp = client.chat.completions.create(
    model="qwen3",
    messages=[{"role": "user", "content": "Classify this ticket."}],
    extra_body={"chat_template_kwargs": {"enable_thinking": False}},
)
```

---

## Self-Consistency (Test-Time Compute You Control)

```python
from collections import Counter

from vllm import LLM, SamplingParams

llm = LLM(model="Qwen/Qwen3-8B")
params = SamplingParams(temperature=0.7, n=1)
answers = []
for _ in range(8):
    out = llm.generate(["Solve step by step: 17 * 23."], params)
    answers.append(out[0].outputs[0].text.strip())   # the final line
winner, votes = Counter(answers).most_common(1)[0]
print(winner, votes)
```

- Sampling wider (larger `n`) is the cheapest accuracy lever once the trace
  is exhausted.
- Track pass@1 vs pass@n on your own eval set before paying for wider
  sampling in production.

---

## Cost & Latency Knobs

| Knob | Effect | Typical |
| --- | --- | --- |
| `reasoning_effort` | trace length per request | low for routing, high for proofs |
| `budget_tokens` | hard ceiling on the trace | 2k-16k |
| `max_completion_tokens` | trace + answer ceiling | budget + 1k-2k |
| `n` (self-consistency) | accuracy per extra sample | 4-16 on hard tasks |
| model routing | skip the trace on easy turns | classifier or heuristics |

---

## Troubleshooting

```bash
# Empty "content", answer missing
#   -> the whole completion was spent thinking: raise
#      max_completion_tokens or lower the budget/effort

# Request dies with context-length error
#   -> thinking tokens consume max_model_len too: budget
#      context = trace + answer + prompt

# Raw <think>...</think> appears inside "content"
#   -> the reasoning parser was not set at serve time, or the
#      chat template does not match the checkpoint; restart
#      with --reasoning-parser and verify /v1/models

# 400 on every request with temperature set
#   -> the reasoning endpoint pins sampling: remove
#      temperature / top_p from the payload

# p99 latency exploded after enabling reasoning
#   -> route easy queries to a non-reasoning model, cap
#      effort/budget, and alert on reasoning_tokens p95
```

---

**Quick Reference for:**

- [Module 1402: vLLM & TGI High-Concurrency Inference](../../phases/phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)
- [Module 3304: Decoding & Sampling Strategies](../../phases/phase3-transformers/3300-decoding/3304-Decoding-Sampling-Strategies.md)
- [Module 5205: GRPO & RLVR](../../phases/phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md)
- [CHEAT-SHEET-007: vLLM Serving & Inference](./CHEAT-SHEET-007-vLLM-Serving.md)
