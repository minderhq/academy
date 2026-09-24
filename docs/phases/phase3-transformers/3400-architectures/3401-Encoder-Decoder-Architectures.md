---
Document ID: 3401
Title: Encoder-Decoder Architectures
Phase: 3
Module: 3400
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'architecture', 'encoder-decoder', 'gpt', 'llama']
---

# 3401: Encoder-Decoder Architectures

## Abstract
Encoder-decoder architectures use separate components for processing input and generating output, enabling sequence-to-sequence tasks like translation and summarization.

## Architecture Comparison

### Encoder-Decoder (T5, BART)
```text
Input → [Encoder] → Context → [Decoder] → Output

Encoder: Processes input into fixed-length representation
Decoder: Generates output from encoded context
```

### Decoder-Only (GPT, LLaMA)
```text
Input → [Decoder] → Output

Single model: Causal mask on entire sequence
Autoregressive generation only
```

## T5 (Text-to-Text Transfer Transformer)

### Architecture
```python
class T5Block(nn.Module):
    """
    T5 block: Same encoder and decoder
    """
    def __init__(self, d_model=512, d_ff=2048, heads=8):
        super().__init__()

        # Self-attention
        self.self_attn = MultiHeadAttention(d_model, heads)
        self.norm1 = nn.LayerNorm(d_model)

        # Feed-forward (with relative position bias)
        self.ff = SparseFeedForward(d_model, d_ff)
        self.norm2 = nn.LayerNorm(d_model)

    def forward(self, x, encoder_output=None, mask=None):
        # Self-attention
        attn_out = self.self_attn(x, mask=mask)
        x = self.norm1(x + attn_out)

        # Feed-forward
        ff_out = self.ff(x)
        x = self.norm2(x + ff_out)

        return x

# T5 uses:
# - Relative position bias (no embeddings)
# - Sparse feed-forward (only 1/8 active)
# - Layer normalization before attention (pre-norm)
# - GeGLU activation
```

### T5 Pre-training Tasks
```python
# T5 is trained on multiple tasks:
t5_tasks = {
    "span_corruption": "Mask and predict random spans",
    "masked_lm": "Predict masked tokens (BERT-style)",
    "prefix_lm": "Predict given prefix (GPT-style)",
    "bilingual": "Translation pairs",
    "switch": "Natural language inference",
    "classification": "Text classification",
}
```

## BART (Denoising Auto-Encoder)

### Architecture
```python
class BARTModel(nn.Module):
    """
    BART: Denoising autoencoder for seq2seq
    """
    def __init__(self):
        super().__init__()

        # BIDIRECTIONAL encoder
        self.encoder = TransformerEncoder(
            num_layers=12,
            heads=16,
            d_model=1024
        )

        # AUTOREGRESSIVE decoder (like GPT)
        self.decoder = TransformerDecoder(
            num_layers=12,
            heads=16,
            d_model=1024
        )

    def forward(self, input_ids, decoder_input_ids):
        # Encode input (bidirectional)
        encoder_out = self.encoder(input_ids)

        # Decode (autoregressive)
        outputs = self.decoder(
            decoder_input_ids,
            encoder_output=encoder_out
        )

        return outputs
```

### BART Denoising Objectives
```python
bart_pretraining = [
    "Token Masking": "Random tokens replaced with <mask>",
    "Token Deletion": "Random tokens deleted",
    "Text Infilling": "Span of N tokens masked",
    "Sentence Permutation": "Sentence order shuffled",
    "Span Rotation": "Document spans rotated",
]

# BART Large = 12 layers, 16 heads, 1024 d_model
# Used for: Summarization, Translation, QA
```

## Comparison

| Architecture | Encoder | Decoder | Best For |
|-------------|---------|---------|----------|
| T5 | Pre-norm | Pre-norm | NLP tasks, Seq2Seq |
| BART | Pre-norm | Pre-norm | Summarization, Translation |
| GPT | - | Pre-norm | Generation only |
| BERT | Pre-norm | - | Encoding only |

---

## Next Steps

- Continue with: **[3402: Decoder-Only Models](./3402-Decoder-Only-Models.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

**Related:**
- [3402: Decoder-Only Models](./3402-Decoder-Only-Models.md)
- [3101: Self-Attention](../3100-attention/3101-Self-Attention-DeepDive.md)
