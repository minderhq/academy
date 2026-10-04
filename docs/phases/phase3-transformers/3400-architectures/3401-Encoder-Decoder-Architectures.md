---
Document ID: 3401
Title: "3401: Encoder-Decoder Architectures"
Phase: 3
Module: 3400
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'architecture', 'encoder-decoder', 't5', 'bart']
---

# 3401: Encoder-Decoder Architectures

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Three Architecture Families](#the-three-architecture-families)
- [Cross-Attention: The Defining Mechanism](#cross-attention-the-defining-mechanism)
- [T5 (Text-to-Text Transfer Transformer)](#t5-text-to-text-transfer-transformer)
- [BART (Denoising Auto-Encoder)](#bart-denoising-auto-encoder)
- [Encoder-Decoder vs Decoder-Only Today](#encoder-decoder-vs-decoder-only-today)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Classify a model as encoder-only, decoder-only, or encoder-decoder from its attention mask alone
- Explain cross-attention and why it is the mechanism that separates encoder-decoder models from the other families
- Describe T5's text-to-text framing and span-corruption pretraining objective
- Describe BART's denoising objectives and which noise combinations train it for generation
- Argue when an encoder-decoder still beats a decoder-only model in production (and when it does not)

---

## Abstract

The original transformer was an encoder-decoder: one stack reads the input bidirectionally, another generates the output autoregressively, and cross-attention wires the second to the first. Decoder-only models (GPT, LLaMA — [3402](./3402-Decoder-Only-Models.md)) later absorbed most of the spotlight, but encoder-decoders remain the strongest fit for fixed sequence-to-sequence tasks — translation, summarization, structured transformation — at a fraction of the inference cost. This lesson builds the family taxonomy, dissects cross-attention, and studies the two canonical implementations: T5 (text-to-text, span corruption) and BART (denoising auto-encoder).

## The Three Architecture Families

```text
                 attention mask          sees             examples
---------------+----------------------+----------------+------------------
encoder-only    bidirectional           input only       BERT, RoBERTa
                (every token attends    never generates
                to every token)

decoder-only    causal                  input + own      GPT, LLaMA,
                (token i sees 0..i-1)   output so far    Mistral

encoder-        bidirectional encoder   input (enc) +    T5, BART,
decoder         + causal decoder        output (dec)     mT5, FLAN-T5
                + CROSS-attention
                (dec -> enc states)
```

```text
One sentence each

- Encoder-only:  builds REPRESENTATIONS of complete inputs
                 (classification, retrieval, reranking)
- Decoder-only:  models P(next token | prefix); generation is native,
                 understanding is a prompting convention
- Encoder-dec:   COMPRESS-then-GENERATE - the encoder produces a
                 full representation of the source, the decoder emits
                 a fresh sequence conditioned on it
```

The compression property is the architectural signature: in a decoder-only model the "understanding" of the prompt is implicit in the KV cache of the prompt tokens; in an encoder-decoder it is an explicit, fixed-size-ish intermediate that generation attends to.

## Cross-Attention: The Defining Mechanism

Every decoder layer in an encoder-decoder has THREE attention inputs, not one:

```text
Decoder layer:
  1. masked self-attention   output-so-far -> output-so-far   (causal)
  2. cross-attention         output-so-far -> ENCODER STATES   (full access)
  3. feed-forward            per-token transform

Cross-attention math (identical to self-attention, different K/V source):

  Q = H_dec @ W_Q        # queries from the decoder stream
  K = H_enc @ W_K        # keys from the ENCODER output
  V = H_enc @ W_V        # values from the ENCODER output
  head = softmax(Q @ K^T / sqrt(d_k)) @ V
```

```text
Why it matters

- The decoder can attend to ANY source position at ANY generation
  step - no causal constraint toward the input
- The encoder output is computed ONCE and reused for every output
  token (like a KV cache you cannot invalidate)
- This is why encoder-decoders translate long documents without
  the "lost in the middle" degradation that long-prompt decoder-only
  models exhibit
```

## T5 (Text-to-Text Transfer Transformer)

### The Text-to-Text Framing

T5's one big idea: every NLP task becomes **text in, text out**, and one model handles all of them by changing the prefix:

```text
Task                     Input                                    Target
-----------------------+---------------------------------------+----------------
translation           "translate English to German:            "Das Haus ist
                       The house is small"                      klein"
summarization         "summarize: <article 500 tokens>"        "<2-sentence gist>"
sentiment             "sst2 sentence: A great, fun film"       "positive"
QA                    "question: What is RLHF? context: ..."   "<answer>"
```

No task heads, no fine-tuning plumbing per task — the same `(input_ids -> labels)` interface everywhere. This framing directly shaped instruction-tuned decoder-only models (FLAN → instruction tuning → chat models).

### Pretraining: Span Corruption

```text
Replace BERT-style single-token masking with SPAN corruption:

input:   "Thank you <X> me to your party <Y> week."
target:  "<X> for inviting <Y> next"

- spans are picked with a mean length that scales with noise
  density (15% of tokens corrupted)
- the sentinel tokens <X>, <Y> are ordinary vocabulary entries
- the decoder learns to generate the missing spans as text -
  the pretraining objective IS the downstream interface
```

### Version Notes (Commonly Confused)

```text
T5 1.0 (2019)   ReLU FF, absolute-ish position via relative bias,
                pre-norm (pre-LN) in both stacks, RMSNorm-like
                layer norm WITHOUT bias
T5 1.1          NO supervised mixing in pretraining (C4 only),
                GEGLU activation in FF, d_model scaled differently;
                checkpoints t5-v1_1-{small..xxl}
FLAN-T5         T5 1.1 + instruction/multi-task fine-tuning;
                the strong zero-shot generalist people actually use
mT5/mT0         multilingual variants

NOT part of T5: sparse / routed feed-forward. That is Switch
Transformer (the MoE follow-up built on the T5 codebase).
Standard T5's FF is dense.
```

### Using T5 Today

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

tok = AutoTokenizer.from_pretrained("google/flan-t5-base")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-base")

prompt = "summarize: The transformer replaced recurrence with " \
         "attention, enabling parallel training over long sequences. " \
         "Subsequent scaling work showed predictable loss improvements " \
         "with compute, data, and parameters."

inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=1024)
out = model.generate(
    **inputs,
    max_new_tokens=64,
    num_beams=4,            # beam search is natural here: encoder states
    length_penalty=0.8,     # are fixed, so beams share one encoding pass
)
print(tok.decode(out[0], skip_special_tokens=True))
```

```text
Family sizes (params)

t5-small 60M | base 220M | large 770M | 3B | 11B
flan-t5 base 250M | large 780M | xl 3B | xxl 11B
```

## BART (Denoising Auto-Encoder)

### Design

BART keeps the transformer as-is (BERT-scale bidirectional encoder + GPT-scale causal decoder, tied through cross-attention) and puts ALL its innovation in the pretraining noise: corrupt text, train the model to restore it.

```text
Denoising objectives (any combination; final BART uses the last two)

1. token masking      random tokens -> <mask>, predict originals
2. token deletion     random tokens DELETED; model must detect positions
3. text infilling     spans (Poisson, ~3 tokens avg) -> one <mask>;
                      model must infer HOW MANY tokens are missing
4. sentence perm.     sentence order shuffled; model restores discourse
5. document rotation  random token moved to start; model finds the end

BART base:  6 enc + 6 dec layers, d=768
BART large: 12 enc + 12 dec layers, d=1024  (~400M params)
```

```text
Reading the noise design

infilling  ~= T5-style span corruption -> translation-like generative strength
deletion   forces localization of missing content
permutation trains global discourse reasoning
Rotation+infilling together = the recipe shipped in BART large
```

### Using BART

```python
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# transformers 5.x retired the "summarization" pipeline alias; the
# model is still first-class - load and generate directly
print("Loading BART large...")
tokenizer = AutoTokenizer.from_pretrained("facebook/bart-large-cnn")
model = AutoModelForSeq2SeqLM.from_pretrained("facebook/bart-large-cnn")

article = """The transformer architecture eliminated recurrence ..."""
inputs = tokenizer(article, return_tensors="pt", max_length=1024, truncation=True)
summary_ids = model.generate(**inputs, max_length=130, min_length=30, do_sample=False)
print(tokenizer.decode(summary_ids[0], skip_special_tokens=True))
```

`bart-large-cnn` remains a strong, tiny-by-2026-standards (406M) summarization baseline: no prompt engineering, deterministic output, single fixed purpose.

## Encoder-Decoder vs Decoder-Only Today

| Dimension | Encoder-decoder (T5/BART) | Decoder-only (GPT/LLaMA) |
|---|---|---|
| Bidirectional input reading | Yes (encoder) | No — causal only |
| Inference cost, fixed task | Encode once, decode short output | Full prompt in KV cache every call |
| Multi-task generality | Bounded by pretraining tasks | Open-ended; won this round |
| Prompting complexity | None — task prefix baked in | Prompt engineering required |
| Best-known scales | ~11B ceiling in practice | 100B+ frontier |
| Beam search efficiency | Cheap (shared encoding) | Beams recompute/reduplicate context |

```text
Why decoder-only won the frontier

1. Scaling behavior: every token is training signal (both input
   and output positions contribute loss); enc-dec decoders only
   train on target tokens
2. One interface for everything: chat, tools, code, RAG - no
   task prefixes to engineer
3. Ecosystem: serving, KV-cache, quantization all optimized for
   causal LMs

Where enc-dec still wins (ship it when)
- High-volume FIXED task: translation, summarization, extraction,
  normalization. A flan-t5-large beats a prompted 70B on cost
  by 2-3 orders of magnitude
- Strict latency budget with long inputs: encode once, decode 50
  tokens
- Determinism matters: no prompt drift, temperature 0, beam search
```

The modern engineering pattern is therefore **triage**: route the bulk traffic of a known task to a small encoder-decoder, and escalate the long tail to a frontier decoder-only model.

---

## Summary

The original transformer was an encoder-decoder: one stack reads the input bidirectionally, another generates the output autoregressively, and cross-attention wires the second to the first. This lesson walked the full T5/BART family anatomy - the encoder stack, the decoder stack, the cross-attention bridge, and why the split still wins for fixed sequence-to-sequence tasks like translation and summarization. The rule it leaves: decoder-only absorbed the spotlight, but when the input is known text and the output is a transformation of it, encoder-decoder remains the strongest fit.

## References

### Related Minder Academy Documents

- [3402: Decoder-Only Models (GPT, LLaMA, Mistral)](3402-Decoder-Only-Models.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)

---

## Next Steps

- Continue with: **[3402: Decoder-Only Models](./3402-Decoder-Only-Models.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
