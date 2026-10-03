---
Document ID: 3501
Title: "3501: Vision-Language Models"
Phase: 3
Module: 3500
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['transformers', 'multimodal', 'vision-language', 'clip', 'vlm']
---

# 3501: Vision-Language Models

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [CLIP: Contrastive Language-Image Pre-training](#clip-contrastive-language-image-pre-training)
- [The VLM Recipe: Vision Encoder + Projector + LLM](#the-vlm-recipe-vision-encoder--projector--llm)
- [LLaVA in Practice](#llava-in-practice)
- [Multimodal RAG](#multimodal-rag)
- [Production Considerations](#production-considerations)
- [Summary](#summary)
- [References](#references)
- [Related Resources](#related-resources)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain CLIP's contrastive objective and compute zero-shot classifications with a real CLIP checkpoint
- Calculate how many tokens an image costs inside a VLM context from resolution and patch size
- Describe the vision-encoder → projector → LLM recipe shared by LLaVA-class models
- Choose between caption-then-index and shared-embedding retrieval for a multimodal RAG system
- Budget image preprocessing, tokenization, and batching in a production VLM service

---

## Abstract

Vision-language models come in two generations. The first — CLIP — aligns images and text in a single embedding space with a contrastive objective, and still powers retrieval, zero-shot classification, and multimodal RAG. The second — LLaVA and its descendants — feeds visual features into a language model as tokens, making images first-class citizens of the chat interface. This lesson covers both: CLIP's math and real usage, the projector recipe that every modern VLM shares, working LLaVA inference code, and the two retrieval architectures for multimodal RAG.

## CLIP: Contrastive Language-Image Pre-training

### The Contrastive Objective

CLIP trains two encoders — an image ViT (or ResNet) and a text transformer — to place matching pairs close together in one shared space:

```text
Batch of N image-text pairs -> 2N encodings -> L2-normalize

              t1     t2     t3    ...    tN
        i1  [ 1.0    .02    .01         .03 ]
        i2  [ .01    1.0    .02         .01 ]     * exp(logit_scale)
  S   =  i3  [ .02    .01    1.0         .02 ]       (learned temperature)
        ...                                       diagonal = matches
        iN  [ .03    .01    .02         1.0 ]

Loss = symmetric cross-entropy over rows AND columns:
       each image must pick its text, each text must pick its image
```

```text
Consequences of the design
- Zero-shot transfer: "a photo of a {label}" prompts turn ANY
  label set into a classifier without training
- Embeddings are comparable ACROSS modalities: image query and
  text query land in the same space (multimodal RAG, below)
- The temperature is learned: early training uses coarse gradients,
  later training sharpens the softmax
- Weaknesses: fine-grained distinctions, counting, text-in-image,
  and inherited web-data bias
```

### Real Usage: Zero-Shot Classification

```python
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

class_names = ["screenshot of a dashboard", "photograph of a person",
               "product photo on white background", "document scan"]

@torch.no_grad()
def classify(image: Image.Image) -> dict:
    # prompt ensembling: averaging over templates measurably lifts
    # accuracy vs a single template (the original paper's trick)
    prompts = [f"a {c}" for c in class_names]

    inputs = processor(text=prompts, images=image,
                       return_tensors="pt", padding=True)
    outputs = model(**inputs)

    # normalized dot products == cosine similarities
    probs = outputs.logits_per_image.softmax(dim=-1)[0]

    return {c: p.item() for c, p in zip(class_names, probs)}

scores = classify(Image.open("upload.jpg"))
best = max(scores, key=scores.get)
```

Two implementation details that matter: both branches are L2-normalized before the dot product (so the score is cosine similarity), and `logits_per_image` already applies the temperature — do not rescale again.

## The VLM Recipe: Vision Encoder + Projector + LLM

Every mainstream open VLM (LLaVA, Qwen-VL, InternVL, ...) is assembled from three parts:

```text
image                        text
  |                            |
ViT vision encoder        tokenizer
  |  (ViT-L/14, 336px)        |
  |  patches -> features      v
  |                        LLM decoder  <----+
projector (MLP)               ^             |
  |  aligns vision dims       |             |
  |  to LLM embedding dims    |             |
  +-------> [visual tokens inserted into the
            sequence in place of <image>]
```

### The Token Math You Must Be Able to Do

```text
How many context tokens does ONE image cost?

tokens = (resolution / patch_size)^2      (before any pooling)

336px / 14px patch  = 24 x 24 grid  = 576 tokens per image
448px / 14px        = 32 x 32 grid  = 1024 tokens per image
+ projector pooling (2x2 merge, common) divides by 4:
  576 -> 144 tokens

Budget rule: images eat context like ~100-500 words each.
Ten screenshots on a 8k-token context IS a context-window problem.
```

```text
Adapter families (how vision reaches the LLM)

token insertion   visual features become tokens in the sequence
                  (LLaVA). Simple, unified KV cache, dominates today
cross-attention   frozen LLM, gated attention layers read vision
                  (Flamingo). Fewer tokens, but a second pathway
                  to maintain
unified early-fusion  one tokenizer for pixels and text
                  (Chameleon-class). Elegant; expensive training
```

## LLaVA in Practice

```python
import torch
from PIL import Image
from transformers import LlavaForConditionalGeneration, AutoProcessor

model_id = "llava-hf/llava-1.5-7b-hf"
model = LlavaForConditionalGeneration.from_pretrained(
    model_id, dtype=torch.float16, device_map="auto")
processor = AutoProcessor.from_pretrained(model_id)

image = Image.open("whiteboard.jpg")

# single <image> placeholder marks where visual tokens are injected
prompt = "USER: <image>\nSummarize the action items on this whiteboard. ASSISTANT:"

inputs = processor(text=prompt, images=image, return_tensors="pt").to(model.device)

with torch.no_grad():
    out = model.generate(
        **inputs,
        max_new_tokens=256,
        do_sample=False,          # deterministic for extraction tasks
    )

reply = processor.decode(out[0], skip_special_tokens=True)
print(reply.split("ASSISTANT:")[-1].strip())
```

```text
What to check when outputs disappoint
1. The <image> placeholder is EXACTLY once, before the question
2. Resolution: small text in screenshots needs the 336px+ variants
   or a cropping/tile pipeline - CLIP-pretrained ViTs miss fine text
3. do_sample=False for extraction; sampling only for creative captions
4. Multiple images: check the model actually supports multi-image
   prompts - llava-1.5 is single-image per turn
```

## Multimodal RAG

Two architectures exist; pick by how much meaning lives in pixels versus text.

### Architecture A: Caption-Then-Index (Simple, Robust)

```text
images -> VLM captions (batch, offline) -> caption text -> text embeddings
                                                          -> vector DB
query  -> text embedding ------------------------------> same space

+ reuses the ENTIRE text-RAG stack (6101-6401), hybrid search, rerankers
- captions lose fine detail: charts, exact numbers, layout
```

### Architecture B: Shared-Embedding Retrieval (CLIP-Space)

```text
images -> CLIP image embeddings  --+
                                   +-> vector DB (one collection)
query  -> CLIP text embedding   --+

+ retrieves by visual similarity even when uncaptionable
  (logos, diagrams, product shots)
- CLIP space is coarse: weak at text-in-image and counts
- generator still needs the IMAGE itself -> return image refs
  and inject via a VLM, not captions alone
```

```python
import torch
from transformers import CLIPModel, CLIPProcessor
from qdrant_client import QdrantClient, models   # setup: lesson 6401

clip = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
proc = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
client = QdrantClient(url="http://localhost:6333")

@torch.no_grad()
def embed_image(image) -> list[float]:
    inputs = processor(images=image, return_tensors="pt")
    feats = clip.get_image_features(**inputs).pooler_output  # transformers 5.x: projected features live in pooler_output
    return torch.nn.functional.normalize(feats, dim=-1)[0].tolist()

@torch.no_grad()
def embed_text(query: str) -> list[float]:
    inputs = processor(text=[query], return_tensors="pt", padding=True)
    feats = clip.get_text_features(**inputs).pooler_output
    return torch.nn.functional.normalize(feats, dim=-1)[0].tolist()

# index
client.upsert("image_library", points=[
    models.PointStruct(id=img_id, vector=embed_image(img),
                       payload={"path": path, "caption": caption})
    for img_id, img, path, caption in indexed_images
])

# retrieve
hits = client.query_points("image_library", query=embed_text("org chart slide"),
                           limit=5).points
```

```text
Production pattern: BOTH, side by side
- one Qdrant collection for caption text vectors (dense meaning)
- one for CLIP vectors (visual similarity)
- retrieve from both, merge + dedupe, hand images to a VLM for
  the final answer. Hybrid-search theory: 6201.
```

## Production Considerations

```text
1. Preprocessing correctness
   - EXIF rotation: apply or images arrive sideways
   - resize with aspect preservation, letterbox if needed;
     blind square crops destroy charts and documents
   - RGB conversion (PNG alpha, CMYK JPEGs crash naive loaders)

2. Token budgeting
   - enforce per-request image count AND pixel budget
   - downscale server-side: the model resizes internally anyway;
     better you control the loss

3. Throughput
   - the ViT encoder batch separately from LLM decode; image
     encoding is compute-bound and batchable, decode is not
   - fp16/bf16 for the ViT halves memory at no measurable loss

4. Cost triage (mirrors 3401's lesson)
   - "is this image a photo of X?"       -> CLIP, near-free
   - "transcribe this document"          -> VLM or dedicated OCR
   - "reason about this screenshot"      -> full VLM
   Route before you pay for the LLM.

5. Safety
   - image inputs bypass text filters; run a CLIP-based NSFW /
     logo / PII gate BEFORE the VLM sees the bytes
```

---

## Summary

Vision-language models come in two generations: CLIP aligns images and text in one embedding space with a contrastive objective, and LLaVA-style models feed visual features into a language model as tokens, making images first-class citizens of the chat interface. This lesson walked the contrastive pre-training recipe, the projection layer that bridges a vision encoder to an LLM, and the retrieval, zero-shot classification, and multimodal RAG workloads each generation owns. The rule it leaves: CLIP is the index, LLaVA is the conversation - pick by whether the task is finding or explaining.

## References

### Related PROJECT-OMEGA Documents

- [3502: Audio Models](3502-Audio-Models.md)
- [6401: Qdrant Setup Guide](../../phase6-rag/6400-vector-databases/6401-Qdrant-Setup.md)

---

## Next Steps

- Continue with: **[3502: Audio Models](./3502-Audio-Models.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Related Resources

- **Related:** [6201: Hybrid Search](../../phase6-rag/6200-retrieval/6201-Hybrid-Search.md)
- **Experiment:** [EXP_3501: Multimodal RAG](../../../../experiments/EXP_3501_MULTIMODAL_RAG.md)
