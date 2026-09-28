---
Document ID: 3500-MULTIMODAL-README
Title: "[3500]: Multimodal Models"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Beginner
---

# [3500]: Multimodal Models

## Overview

This module covers vision-language models (CLIP, BLIP, LLaVA) and audio models (Whisper, AudioLM). You'll learn how Transformers extend beyond text to process images, audio, and video, enabling applications like image captioning, visual question answering, and speech recognition.

---

## Module Documents

| Document | Description | Time | Difficulty |
|----------|-------------|------|------------|
| [3501: Vision-Language Models](./3501-Vision-Language-Models.md) | CLIP, BLIP, LLaVA, multimodal RAG | 5 hrs | Advanced |
| [3502: Audio Models](./3502-Audio-Models.md) | Whisper, AudioLM, voice assistants | 5 hrs | Advanced |

---

## Learning Objectives

After completing this module, you will:
- Understand vision-language model architectures
- Implement CLIP-style contrastive learning
- Build multimodal RAG systems
- Understand audio Transformers (Whisper, AudioLM)
- Apply multimodal models to real-world tasks

---

## Prerequisites

- **Vision:** Convolutional neural networks basics
- **Audio:** Signal processing basics (MFCC, spectrograms)
- **Previous:** [3100: Attention](../3100-attention/), [3400: Architectures](../3400-architectures/)

See [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

---

## Key Concepts

### What is Multimodal AI?

```text
┌─────────────────────────────────────────────────────────────┐
│                      Multimodal Models                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input Modality          Processing        Output Modality   │
│  ─────────────          ─────────         ────────────────  │
│                                                              │
│  Text                    │                                   │
│  Image         →    Transformer    →    Text / Image / Audio│
│  Audio                   │                                   │
│  Video                   │                                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Multimodal Architecture Families

| Architecture | Description | Examples | Use Case |
|--------------|-------------|----------|----------|
| **Encoder-Encoder** | Separate encoders, fusion layer | CLIP, BLIP | Image-text retrieval |
| **Encoder-Decoder** | Cross-modal attention | LLaVA, Flamingo | VQA, captioning |
| **Unified** | Single modality-agnostic encoder | GATO, Flamingo | General multimodal |
| **Projection** | Map to shared embedding space | CLIP | Zero-shot transfer |

---

## Vision-Language Models

### CLIP: Contrastive Language-Image Pre-training

**Core Idea:** Learn visual concepts from natural language supervision

```text
Training: (Image, Text) pairs with contrastive loss

┌──────────────────┐              ┌──────────────────┐
│   Image Encoder  │              │   Text Encoder   │
│   (Vision        │              │   (Text          │
│    Transformer)  │              │    Transformer)  │
└────────┬─────────┘              └────────┬─────────┘
         │                                 │
         │  Shared Embedding Space (512D)  │
         │                                 │
         └─────────────┬───────────────────┘
                       │
                       ▼
              Contrastive Loss
              (Maximize similarity for
               matching pairs, minimize
               for non-matching)
```

**Key Formula:**
```text
L = -log(exp(sim(z_i, z_j) / τ) / Σ exp(sim(z_i, z_k) / τ))

Where:
- z_i: Image embedding
- z_j: Text embedding (positive pair)
- z_k: All text embeddings
- τ: Temperature parameter
- sim: Cosine similarity
```

### LLaVA: Large Language and Vision Assistant

**Architecture:** Connect vision encoder to LLM via projection layer

```text
Image Input
    ↓
CLIP ViT-L/14 (Vision Encoder)
    ↓
Linear Projection (to LLM token space)
    ↓
LLM (Vicuna, LLaMA)
    ↓
Text Output

Example:
User: <image> What is in this image?
LLaMA: The image shows a cat sitting on a windowsill...
```

### Multimodal RAG

**Idea:** Extend text RAG with visual documents

```text
Query: "What did the Q4 earnings report say about revenue?"

┌─────────────────────────────────────────────────────────────┐
│                    Multimodal RAG Pipeline                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. PDF Pages                                              │
│     ├── Text chunks → Text embeddings                       │
│     └── Images     → CLIP embeddings                        │
│                                                              │
│  2. Vector Store                                            │
│     ├── Text vectors (Qdrant)                               │
│     └── Image vectors (Qdrant)                              │
│                                                              │
│  3. Retrieval                                               │
│     ├── Relevant text chunks                                │
│     └── Relevant images/tables/charts                       │
│                                                              │
│  4. Generation (Vision-Language LLM)                        │
│     ├── Text context                                        │
│     ├── Images (base64)                                     │
│     └── Answer: "According to Q4 report, revenue..."       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Audio Models

### Whisper: Automatic Speech Recognition

**Architecture:** Encoder-decoder Transformer

```text
Audio Input (16kHz)
    ↓
Log-Mel Spectrogram (80 channels)
    ↓
Audio Transformer Encoder (bidirectional)
    ↓
Transformer Decoder (autoregressive)
    ↓
Text Output (with timestamps)
```

**Key Features:**
- **680k hours** of weakly supervised training data
- **Robust** to accents, background noise, technical language
- **Multilingual** (99 languages)
- **Timestamps** for word-level alignment

### AudioLM: Audio Generation

**Approach:** Language modeling approach to audio

```text
Audio Input
    ↓
Semantic Tokens (from w2v-BERT encoder)
    ↓
Transformer (predicts next semantic token)
    ↓
Coarse Acoustic Model (predicts acoustic tokens)
    ↓
Fine Acoustic Model (predicts actual audio samples)
    ↓
Generated Audio
```

---

## Implementation Examples

### CLIP-style Contrastive Learning

```python
import numpy as np
class ContrastiveLearning(nn.Module):
    """
    CLIP-style contrastive learning for image-text pairs.
    """
    def __init__(self, image_encoder, text_encoder, embed_dim=512):
        super().__init__()
        self.image_encoder = image_encoder
        self.text_encoder = text_encoder
        self.embed_dim = embed_dim

        # Projection layers
        self.image_proj = nn.Linear(image_encoder.output_dim, embed_dim)
        self.text_proj = nn.Linear(text_encoder.output_dim, embed_dim)

        # Learnable temperature parameter
        self.logit_scale = nn.Parameter(torch.ones(1) * np.log(1 / 0.07))

    def forward(self, images, texts):
        """
        Args:
            images: (batch, 3, H, W)
            texts: (batch, seq_len)

        Returns:
            loss: Contrastive loss
        """
        # Encode images and texts
        image_features = self.image_encoder(images)
        text_features = self.text_encoder(texts)

        # Project to shared space
        image_embeds = self.image_proj(image_features)
        text_embeds = self.text_proj(text_features)

        # Normalize
        image_embeds = F.normalize(image_embeds, dim=-1)
        text_embeds = F.normalize(text_embeds, dim=-1)

        # Cosine similarity
        logits = (image_embeds @ text_embeds.T) * self.logit_scale.exp()

        # Labels: diagonal elements (matching pairs)
        batch_size = images.size(0)
        labels = torch.arange(batch_size, device=images.device)

        # Loss (symmetric)
        loss_i = F.cross_entropy(logits, labels)
        loss_t = F.cross_entropy(logits.T, labels)
        loss = (loss_i + loss_t) / 2

        return loss
```

### Multimodal RAG Query

```python
def multimodal_rag_query(query: str, vector_store, vision_llm):
    """
    Perform multimodal RAG query.
    """
    # 1. Retrieve relevant text chunks
    text_results = vector_store.search(
        query,
        modality="text",
        top_k=5
    )

    # 2. Retrieve relevant images
    image_results = vector_store.search(
        query,
        modality="image",
        top_k=3
    )

    # 3. Prepare multimodal context
    context = {
        "text": "\n\n".join([r.content for r in text_results]),
        "images": [encode_base64(r.image) for r in image_results]
    }

    # 4. Generate response with vision-language LLM
    prompt = f"""
    Query: {query}

    Context:
    {context['text']}

    Images: <image_tags_here>

    Based on the text and images above, answer the query.
    """

    response = vision_llm.generate(
        prompt=prompt,
        images=context["images"]
    )

    return response
```

---

## Related Experiments

| Experiment | Description |
|------------|-------------|
| [EXP_3501: Multimodal RAG](../../../../experiments/EXP_3501_MULTIMODAL_RAG.md) | Build multimodal RAG system |
| [LAB-011: Multi-Modal AI](../../../learning-resources/labs/LAB-011-Multi-Modal-AI.md) | Vision + language hands-on |
| [LAB-012: Audio AI](../../../learning-resources/labs/LAB-012-Audio-AI.md) | Speech recognition and synthesis |

---

## Assessment

- **Quiz:** [assessment/QUIZ.md](assessment/QUIZ.md) - Test your multimodal knowledge
- **Practice:** [assessment/PRACTICE.md](assessment/PRACTICE.md) - Build multimodal applications

---

## See Also

- **Previous Module:** [3400: Model Architectures](../3400-architectures/)
- **Related:** [6200: RAG 2.0](../../phase6-rag/6200-retrieval/) - For multimodal RAG
- **Related:** [7500: AI Security](../../phase7-agentic/7500-security/) - Multimodal threats
- **Phase Overview:** [Phase 3 README](../README.md)

---

## Common Issues

| Issue | Solution |
|-------|----------|
| **Vision encoder too slow** | Use smaller ViT or ResNet backbone |
| **Poor image-text alignment** | Increase training data or use better loss weighting |
| **Audio model hallucinations** | Add language model decoding or ensemble voting |

---

## Quick Reference

### Model Selection by Task

| Task | Recommended Model | Reason |
|------|-------------------|--------|
| Zero-shot classification | CLIP | No training needed |
| Image captioning | BLIP-2, LLaVA | Good image understanding |
| Visual QA | LLaVA, Flamingo | Strong reasoning |
| Speech recognition | Whisper | Robust, multilingual |
| Voice cloning | Vall-E, AudioLM | High quality |
| Multimodal RAG | CLIP + LLaMA | Simple, effective |

### Modalities and Their Representations

| Modality | Raw Input | Preprocessing | Encoder |
|----------|-----------|---------------|---------|
| **Image** | RGB pixels | Resize, normalize | ViT, CNN |
| **Audio** | Waveform | Mel-spectrogram | Audio Transformer |
| **Video** | Frame sequence | Per-frame encoding | Video ViT |
| **3D** | Point cloud | Voxelization | Point Transformer |

---

## Applications

### Vision-Language Applications

1. **Image Search** → Find images by description
2. **Visual QA** → Answer questions about images
3. **Image Captioning** → Generate descriptions
4. **OCR + Understanding** → Read and understand documents
5. **Multimodal RAG** → Query PDFs with images/charts

### Audio Applications

1. **Speech Recognition** → Transcribe audio
2. **Voice Assistants** → Natural voice interaction
3. **Audio Search** → Find similar audio
4. **Music Generation** → Create music
5. **Voice Cloning** → Synthesize specific voices

---

**Module Difficulty:** Advanced
**Estimated Time:** 10 hours total
