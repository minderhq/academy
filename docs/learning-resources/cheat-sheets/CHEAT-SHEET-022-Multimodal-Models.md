---
Document ID: CHEAT-SHEET-022
Title: "CHEAT-SHEET-022: Multimodal Models"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'multimodal', 'vision-language', 'clip', 'transformers']
---

# CHEAT-SHEET-022: Multimodal Models

**Quick Reference for:** the two-generation split, CLIP's contrastive objective, the encoder→projector→LLM recipe and its token math, the LLaVA discipline, the two multimodal-RAG architectures, the audio spectrogram/codec-token split, Whisper's prompt-token controls, and the voice-pipeline latency budget.

**Version:** 1.0

## The Two-Generation Split

Vision-language models come in two generations, and every workload picks one of them. **CLIP** (generation one) aligns images and text in a single embedding space with a contrastive objective — it powers retrieval, zero-shot classification, and multimodal RAG. **LLaVA and its descendants** (generation two) feed visual features into a language model as tokens, making images first-class citizens of the chat interface. The rule the curriculum leaves: **CLIP is the index, LLaVA is the conversation — pick by whether the task is finding or explaining.**

## CLIP: The Contrastive Index

CLIP trains two encoders — an image ViT and a text transformer — on N image-text pairs. A batch of N pairs becomes **2N encodings**, both branches are **L2-normalized**, and the N×N score matrix (cosine similarities × a learned temperature) is trained with **symmetric cross-entropy over rows AND columns**: each image must pick its text, each text must pick its image.

- Zero-shot transfer: `"a photo of a {label}"` prompts turn ANY label set into a classifier without training. Prompt ensembling (averaging over templates) measurably lifts accuracy — the original paper's trick.
- Embeddings are comparable ACROSS modalities: an image query and a text query land in the same space — this is what multimodal RAG runs on.
- The temperature is learned (`logit_scale`): coarse gradients early, sharp softmax late.
- Weaknesses to quote: fine-grained distinctions, counting, text-in-image, inherited web-data bias.
- Wiring discipline: `logits_per_image` **already applies the temperature** — do not rescale again.

## The VLM Recipe: Encoder → Projector → LLM

Every mainstream open VLM (LLaVA, Qwen-VL, InternVL) is assembled from three parts: a **ViT vision encoder** (ViT-L/14 at 336px) turns patches into features, a **projector** (an MLP) aligns vision dims to LLM embedding dims, and the **LLM decoder** consumes the visual tokens inserted into the sequence in place of the `<image>` placeholder.

**The token math you must be able to do:** one image costs `tokens = (resolution / patch_size)^2` before pooling. 336px / 14px patch = 24×24 grid = **576 tokens per image**; 448px = 32×32 = **1024**. A 2×2 projector pooling merge (common) divides by 4: 576 → **144**. Budget rule: images eat context like ~100-500 words each — ten screenshots on an 8k-token context IS a context-window problem.

| Adapter family | Mechanism | Trade-off |
|---|---|---|
| Token insertion (LLaVA) | visual features become tokens in the sequence | simple, unified KV cache, dominates today |
| Cross-attention (Flamingo) | frozen LLM, gated attention layers read vision | fewer tokens, but a second pathway to maintain |
| Unified early-fusion (Chameleon) | one tokenizer for pixels and text | elegant, expensive training |

## The Arithmetic

```python
from math import exp, sqrt

# --- VLM token math: one image = (resolution / patch_size)^2 tokens ---
def image_tokens(resolution, patch=14, pool=1):
    return (resolution // patch) ** 2 // pool

# --- CLIP scoring: L2-normalize both branches, dot product = cosine ---
def cosine(a, b):
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb)

def softmax(xs):
    m = max(xs)
    es = [exp(x - m) for x in xs]
    tot = sum(es)
    return [e / tot for e in es]

# --- audio: Whisper's fixed window in mel frames; codec token bill ---
def mel_frames(seconds, hop_ms=10):
    return seconds * 1000 // hop_ms

n = 32
print("CLIP batch: N=%d pairs -> %d encodings -> %dx%d score matrix"
      % (n, 2 * n, n, n))
print("image 336px/14 =", image_tokens(336), "tokens; +2x2 pool =",
      image_tokens(336, pool=4))
print("image 448px/14 =", image_tokens(448), "tokens")
match = cosine([1, 0, 1], [1, 1, 0])
other = cosine([1, 0, 1], [0, 1, 0])
print("CLIP cosine match=%.4f other=%.4f" % (match, other))
probs = softmax([3.0, 0.5, -1.0])
print("zero-shot probs", " ".join("%.2f" % p for p in probs))
print("Whisper 30s window =", mel_frames(30), "mel frames @10ms hop")
print("codec 75 tok/s -> 1 min audio =", 75 * 60, "tokens")
```

The run confirms the whole bill: `CLIP batch: N=32 pairs -> 64 encodings -> 32x32 score matrix` (N pairs bill 2N encodings and an N×N matrix). `image 336px/14 = 576 tokens; +2x2 pool = 144` and `image 448px/14 = 1024 tokens` — the token math above, exactly. `CLIP cosine match=0.5000 other=0.0000` — L2-normalize both branches and the dot product is the cosine similarity; the matching pair scores above zero while the mismatch lands at zero. `zero-shot probs 0.91 0.07 0.02` — a softmax over per-label scores IS the zero-shot classifier. `Whisper 30s window = 3000 mel frames @10ms hop` — Whisper's fixed window. `codec 75 tok/s -> 1 min audio = 4500 tokens` — one minute of audio is ~4.5k codec tokens, an order of magnitude above the text it transcribes.

## LLaVA Discipline

1. The `<image>` placeholder is **exactly once, before the question**.
2. Resolution: small text in screenshots needs the **336px+ variants** or a cropping/tile pipeline — CLIP-pretrained ViTs miss fine text.
3. `do_sample=False` for extraction; sampling only for creative captions.
4. Multi-image: check the model actually supports multi-image prompts — llava-1.5 is **single-image per turn**.

## Multimodal RAG

Two architectures exist; pick by how much meaning lives in pixels versus text.

| Architecture | How it retrieves | Strength / cost |
|---|---|---|
| Caption-then-index | VLM captions images offline, indexes caption text | reuses the ENTIRE text-RAG stack; captions lose fine detail (charts, exact numbers, layout) |
| Shared-embedding (CLIP-space) | image and text embeddings in one vector collection | retrieves by visual similarity even when uncaptionable (logos, diagrams); CLIP space is coarse |

The production pattern is **BOTH, side by side**: one collection of caption text vectors (dense meaning), one of CLIP vectors (visual similarity); retrieve from both, merge + dedupe, and hand the images themselves to a VLM for the final answer — the generator needs the IMAGE, not captions alone.

## Audio: Spectrograms for Perception, Tokens for Generation

Two representations, two model families. **Mel-spectrograms** (80 mel bins, log scale, ~25ms frames over 16 kHz audio) are dense, differentiable, and time-aligned — **encoder** models consume them (Whisper, wav2vec2, HuBERT) for perception: ASR, speaker ID, emotion. **Neural-codec tokens** (~75 tokens/s, multiple codebook streams) compress audio into discrete sequences — **decoder** models generate them for TTS and music, where the whole autoregressive toolbox (sampling, temperature, beam search) applies. The rule: **perception wants spectrograms, generation wants tokens.**

Whisper is an encoder-decoder transformer trained on **680k hours**: log-mel input over a padded **30-second window (3000 mel frames @ 10 ms hop)**, convolutional downsampler + transformer encoder, and a 50k-BPE autoregressive decoder whose **prompt tokens choose everything** — `<|startoftranscript|><|en|><|transcribe|><|notimestamps|>` selects language, task (transcribe vs translate-to-English), and timestamp granularity. No separate models per language or per task. 30% of training windows are padded silence the model learns to predict nothing on — this suppresses (mostly) the classic hallucinate-when-silent ASR failure.

| Deployment | What it is | When |
|---|---|---|
| openai-whisper | reference implementation | quality/behavior baseline; slowest; PyTorch dep tree |
| faster-whisper | CTranslate2 re-implementation, int8, VAD built in | ~4x faster; the default for servers |
| whisper.cpp | quantized GGML weights, zero Python | CPU-only edge boxes (pairs with GGUF thinking) |
| hosted API | zero ops | data residency and per-audio-minute cost are the trade |

Serving discipline: **pin the language** (detection misfires on short clips), let `vad_filter=True` skip silence (cuts hallucinations AND time), hash-key-cache identical uploads, and remember **diarization is a SEPARATE model** (pyannote) — Whisper gives what, not who. Generation stacks layer **semantic tokens** (content) → **acoustic tokens** (timbre/prosody, EnCodec/SoundStream) → **vocoder** (waveform): modern speech generation is a language-model problem over codec tokens, so sampling failure modes (loops, drift) transfer too.

## The Voice Pipeline Budget

mic → VAD (~10ms) → Whisper (300-800ms) → LLM (TTFT) → TTS (first audio). Targets: **VAD < 50ms, first audio < 300ms, < 1s perceived response.** Whisper pays the 30s window cost unless you stream with partials; stream the LLM reply **INTO the TTS sentence by sentence** instead of waiting for full text; design **barge-in** (user interrupts) early — it reshapes the pipeline.

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| flat / wrong classification probs | `logits_per_image` rescaled a second time | the temperature is already applied — softmax and stop |
| ten screenshots overflow an 8k context | 576 (or 1024) tokens per image is real | enforce a per-request image count AND pixel budget; downscale server-side |
| LLaVA answers about the wrong image | `<image>` placeholder missing, doubled, or after the question | exactly once, before the question |
| small text in screenshots unreadable | sub-336px input starves the ViT | 336px+ variants or a cropping/tile pipeline |
| Whisper hallucinates text on silence | silence-padding training suppresses "mostly" | `vad_filter=True` + pin the language |
| transcript has no speaker turns | diarization expected from Whisper | run a separate diarization model (pyannote) |

## Quick Reference For

- [Module 3501: Vision-Language Models](../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)
- [Module 3502: Audio Models](../../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md)
- [Module 6401: Qdrant Setup](../../phases/phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)
- [CHEAT-SHEET-021: RoPE Positional Encoding](./CHEAT-SHEET-021-RoPE-Positional-Encoding.md)
