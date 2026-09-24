# [3400]: Model Architectures

## Overview

This module covers the major Transformer architecture families: encoder-decoder (T5, BART), decoder-only (GPT, LLaMA), and encoder-only (BERT). You'll learn the trade-offs and when to use each architecture for different tasks.

---

## Module Documents

| Document | Description | Difficulty | Time |
|----------|-------------|------------|------|
| [3401: Encoder-Decoder Architectures](./3401-Encoder-Decoder-Architectures.md) | T5, BART, and sequence-to-sequence models | ⭐⭐⭐ | 4 hrs |
| [3402: Decoder-Only Models](./3402-Decoder-Only-Models.md) | GPT, LLaMA, Mistral architectures | ⭐⭐⭐ | 4 hrs |
| [3403: Model Architecture Comparison](./guides/3403-Model-Architecture-Comparison.md) | Comparative guide with benchmarks | ⭐⭐⭐ | 3 hrs |

---

## Learning Objectives

After completing this module, you will:
- ✅ Understand encoder-decoder, decoder-only, and encoder-only architectures
- ✅ Compare T5, BART, GPT, BERT, and LLaMA
- ✅ Choose the right architecture for your task
- ✅ Understand bidirectional vs causal attention
- ✅ Implement different Transformer variants

---

## Prerequisites

- **Programming:** PyTorch, attention mechanisms
- **Previous:** [3100: Attention](../3100-attention/), [3300: Decoding](../3300-decoding/)

---

## Key Concepts

### The Three Architecture Families

```
┌─────────────────────────────────────────────────────────────┐
│                    Transformer Architectures                 │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Encoder-Decoder           Decoder-Only        Encoder-Only │
│  (T5, BART)               (GPT, LLaMA)        (BERT, RoBERTa)│
│       │                        │                     │        │
│       ▼                        ▼                     ▼        │
│  ┌─────────┐              ┌─────────┐            ┌─────────┐ │
│  │ Encoder │              │ Decoder │            │ Encoder │ │
│  │Bidirect │              │ Causal  │            │Bidirect │ │
│  └────┬────┘              └────┬────┘            └────┬────┘ │
│       │                        │                     │        │
│       ▼                        ▼                     │        │
│  ┌─────────┐              ┌─────────┐               │        │
│  │ Decoder │              │ Decoder │               │        │
│  │ Causal  │              │ Causal  │               │        │
│  └────┬────┘              └────┬────┘               │        │
│       │                        │                     │        │
│       ▼                        ▼                     ▼        │
│  Seq2Seq                  Generation           Understanding│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Architecture Comparison Table

| Aspect | Encoder-Decoder | Decoder-Only | Encoder-Only |
|--------|----------------|--------------|--------------|
| **Attention Type** | Bidirectional + Causal | Causal only | Bidirectional only |
| **Output** | Generates sequence | Generates sequence | Classifies/encodes |
| **Use Case** | Translation, summarization | Text generation | Classification, search |
| **Examples** | T5, BART | GPT, LLaMA, Mistral | BERT, RoBERTa |
| **Training** | Seq2Seq | Next token prediction | Masked token prediction |
| **Inference Speed** | Slower (2x passes) | Fast | Fast (single pass) |

---

## Encoder-Decoder Architecture

### Structure

```
Input: "Translate English to German: The house is wonderful"

┌─────────────────────────────────────────────────────────────┐
│ ENCODER (Bidirectional Attention)                          │
│                                                              │
│  [The] [house] [is] [wonderful]                             │
│   ↓     ↓       ↓    ↓                                      │
│  Each token attends to ALL tokens                          │
│                                                              │
│  Output: Context vector for each token                      │
└─────────────────────────────────────────────────────────────┘
                           ↓ Cross-Attention
┌─────────────────────────────────────────────────────────────┐
│ DECODER (Causal Attention + Cross-Attention)                │
│                                                              │
│  [<SOS>] → [Das] → [Haus] → [ist] → [wunderbar]            │
│   ↓        ↓       ↓       ↓          ↓                     │
│  Causal: Attend to previous decoder tokens                  │
│  Cross:  Attend to ALL encoder outputs                      │
│                                                              │
│  Output: "Das Haus ist wunderbar"                           │
└─────────────────────────────────────────────────────────────┘
```

### Key Models

| Model | Training | Strengths | Weaknesses |
|-------|----------|-----------|------------|
| **T5** | Text-to-text | Flexible, can do any task | Slow (2x computation) |
| **BART** | Denoising autoencoder | Good for summarization | Slower than decoder-only |
| **mT5** | Multilingual T5 | 101 languages | Larger model size |

---

## Decoder-Only Architecture

### Structure

```
Input: "Once upon a time"

[Once] [upon] [a] [time] [<EOS>]
  ↓      ↓      ↓    ↓      ↓
  Each token attends to PREVIOUS tokens only
  (causal / autoregressive)

[Once] → attends to []
[upon] → attends to [Once]
  [a]  → attends to [Once, upon]
 [time] → attends to [Once, upon, a]
[<EOS>] → attends to [Once, upon, a, time]

Output: "Once upon a time, there was a..."
```

### Key Models

| Model | Params | Context | Strengths | Use Case |
|-------|--------|---------|-----------|----------|
| **GPT-3** | 175B | 2k | Zero-shot learning | General tasks |
| **LLaMA 2** | 7B-70B | 4k | Open weights, efficient | Research, production |
| **Mistral** | 7B | 8k | Fast, efficient | Edge deployment |
| **Claude** | ? | 100k+ | Large context | Long documents |

---

## Encoder-Only Architecture

### Structure

```
Input: "The [MASK] is on the table"

[The] [MASK] [is] [on] [the] [table]
  ↓      ↓     ↓    ↓     ↓      ↓
  All tokens attend to ALL tokens
  (bidirectional masking)

Output: "cat" (predict masked token)
```

### Key Models

| Model | Training | Strengths | Use Case |
|-------|----------|-----------|----------|
| **BERT** | Masked LM | Deep understanding | Classification, search |
| **RoBERTa** | Improved BERT training | Better performance | NLU tasks |
| **ALBERT** | Parameter sharing | Efficient | Resource-constrained |

---

## When to Use Each Architecture

### Decision Tree

```
Task: ?
│
├─ Text Generation → Decoder-Only (GPT, LLaMA)
│
├─ Sequence-to-Sequence → Encoder-Decoder (T5, BART)
│  │
│  ├─ Translation → T5, mT5
│  ├─ Summarization → BART, T5
│  └─ Question Answering → T5
│
└─ Understanding/Classification → Encoder-Only (BERT)
   │
   ├─ Sentiment Analysis → BERT
   ├─ Named Entity Recognition → BERT
   └─ Semantic Search → BERT, RoBERTa
```

---

## Implementation Example

### Decoder-Only Block (LLaMA-style)

```python
class DecoderBlock(nn.Module):
    """
    LLaMA-style decoder block with:
    - RMSNorm pre-normalization
    - SwiGLU activation
    - Rotary positional embeddings
    - Grouped-query attention (optional)
    """
    def __init__(self, d_model=4096, n_heads=32, d_ff=11008):
        super().__init__()

        # Pre-normalization
        self.norm1 = RMSNorm(d_model)
        self.norm2 = RMSNorm(d_model)

        # Causal self-attention
        self.attn = CausalSelfAttention(
            d_model=d_model,
            n_heads=n_heads,
        )

        # Feed-forward with SwiGLU
        self.ffn = SwiGLU(d_model, d_ff)

    def forward(self, x, freqs_cis):
        """
        Args:
            x: (batch, seq_len, d_model)
            freqs_cis: Precomputed RoPE frequencies

        Returns:
            output: (batch, seq_len, d_model)
        """
        # Pre-norm architecture
        # Residual connection around attention
        x = x + self.attn(self.norm1(x), freqs_cis)

        # Residual connection around FFN
        x = x + self.ffn(self.norm2(x))

        return x
```

### Encoder-Decoder Block (T5-style)

```python
class EncoderDecoderBlock(nn.Module):
    """
    T5-style encoder-decoder block.
    """
    def __init__(self, d_model=512, n_heads=8, d_ff=2048):
        super().__init__()

        # Encoder
        self.encoder_norm1 = LayerNorm(d_model)
        self.encoder_norm2 = LayerNorm(d_model)
        self.encoder_attn = SelfAttention(d_model, n_heads)
        self.encoder_ffn = FeedForward(d_model, d_ff)

        # Decoder
        self.decoder_norm1 = LayerNorm(d_model)
        self.decoder_norm2 = LayerNorm(d_model)
        self.decoder_norm3 = LayerNorm(d_model)
        self.decoder_attn = CausalSelfAttention(d_model, n_heads)
        self.cross_attn = CrossAttention(d_model, n_heads)
        self.decoder_ffn = FeedForward(d_model, d_ff)

    def forward(self, encoder_input, decoder_input):
        # Encoder
        encoder_output = encoder_input
        encoder_output = encoder_output + self.encoder_attn(
            self.encoder_norm1(encoder_output)
        )
        encoder_output = encoder_output + self.encoder_ffn(
            self.encoder_norm2(encoder_output)
        )

        # Decoder
        decoder_output = decoder_input
        decoder_output = decoder_output + self.decoder_attn(
            self.decoder_norm1(decoder_output)
        )
        decoder_output = decoder_output + self.cross_attn(
            self.decoder_norm2(decoder_output),
            encoder_output
        )
        decoder_output = decoder_output + self.decoder_ffn(
            self.decoder_norm3(decoder_output)
        )

        return encoder_output, decoder_output
```

---

## Related Experiments

| Experiment | Description |
|------------|-------------|
| [EXP_3401: Encoder-Decoder](../../../../experiments/EXP_3401_ENCODER_DECODER.md) | Build T5 from scratch |

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your architecture knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Implement Transformer variants

---

## See Also

- **Previous Module:** [3300: The Decoding Block](../3300-decoding/)
- **Next Module:** [3500: Multimodal Models](../3500-multimodal/) - Vision and audio
- **Guide:** [3403: Architecture Comparison](./guides/3403-Model-Architecture-Comparison.md)
- **Phase Overview:** [Phase 3 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Encoder-decoder too slow** | Use decoder-only for generation |
| **Poor translation quality** | Use larger encoder-decoder model |
| **Catastrophic forgetting** | Use encoder-only for fine-tuning |

---

## Quick Reference

### Model Selection by Task

| Task | Best Architecture | Specific Model |
|------|-------------------|----------------|
| Chatbots | Decoder-only | LLaMA, Mistral |
| Translation | Encoder-decoder | T5, mT5 |
| Summarization | Both | BART (enc-dec), GPT (dec-only) |
| Classification | Encoder-only | BERT, RoBERTa |
| Code generation | Decoder-only | CodeLlama, StarCoder |
| RAG | Decoder-only | LLaMA with retrieval |

---

**Status:** ✅ Complete
**Last Updated:** 2026-02-05
**Module Difficulty:** ⭐⭐⭐ Intermediate
**Estimated Time:** 11 hours total
