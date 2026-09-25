---
Document ID: SOLUTION-LAB-011
Title: "SOLUTION-LAB-011: Multi-Modal AI"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Expert
---

# SOLUTION-LAB-011: Multi-Modal AI

## Overview

Reference solution for the core of [LAB-011: Multi-Modal AI](../LAB-011-Multi-Modal-AI.md): CLIP retrieval and zero-shot classification, BLIP captioning, and a multi-modal RAG store that fuses text and image embeddings. Vision-language theory lives in [3501: Vision-Language Models](../../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md); the audio half of the lab in [3502: Audio Models](../../../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md).

Two API notes that will save you debugging time: CLIP's raw features are **not normalized** — every similarity below normalizes explicitly first; and modern `qdrant-client` searches through `query_points` (`search`/`query_vector` are deprecated).

---

## Exercise 1: CLIP Retrieval and Zero-Shot Classification

### Solution

```python
import torch
import torch.nn.functional as F
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class MultiModalRetriever:
    """CLIP-based image/text retrieval and zero-shot classification."""

    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)

    @torch.no_grad()
    def encode_image(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        feats = self.model.get_image_features(**inputs)       # (1, 512), unnormalized
        return F.normalize(feats, dim=-1)

    @torch.no_grad()
    def encode_text(self, text):
        inputs = self.processor(text=[text], return_tensors="pt")
        feats = self.model.get_text_features(**inputs)        # (1, 512), unnormalized
        return F.normalize(feats, dim=-1)

    def retrieve_images(self, query, image_paths, top_k=5):
        q = self.encode_text(query)                            # (1, 512)
        sims = []
        for path in image_paths:
            img = self.encode_image(path)                      # (1, 512)
            sims.append((path, (q @ img.T).item()))            # normalized -> cosine
        sims.sort(key=lambda x: x[1], reverse=True)
        return sims[:top_k]

    def zero_shot_classify(self, image, classes):
        img = self.encode_image(image)                         # (1, 512)
        inputs = self.processor(
            text=list(classes), return_tensors="pt", padding=True
        )
        with torch.no_grad():
            txt = F.normalize(
                self.model.get_text_features(**inputs), dim=-1  # (C, 512)
            )
        sims = (img @ txt.T).squeeze(0)                        # (C,)
        idx = sims.argmax().item()
        return classes[idx], sims[idx].item()
```

### Usage

```python
retriever = MultiModalRetriever()

results = retriever.retrieve_images(
    "a dog playing in the park",
    ["dog.jpg", "cat.jpg", "park.jpg", "car.jpg"],
    top_k=3,
)
for path, score in results:
    print(f"{path}: {score:.4f}")

label, score = retriever.zero_shot_classify(
    "cat.jpg", ["a photo of a dog", "a photo of a cat", "a photo of a car"]
)
print(f"Predicted: {label} ({score:.4f})")
```

### Why the normalization matters

`get_image_features` / `get_text_features` return unnormalized projections. Similarity on raw vectors is a dot product dominated by vector magnitude; with `F.normalize` on both sides, `q @ img.T` is true cosine similarity — the protocol OpenAI's reference CLIP implementation uses. Skip it and your scores are not comparable across images or class sets.

Two more details that matter for quality: zero-shot prompts work best as descriptive phrases ("a photo of a cat", not "cat"), and a production retriever encodes the corpus **once** and caches the vectors — re-encoding every image per query, as this lab version does, is for learning the mechanics only.

### Model size, correctly stated

| Checkpoint | Notes |
|---|---|
| `openai/clip-vit-base-patch32` | default here — the **small, fast** one (~150M params, 512-dim embeddings) |
| `openai/clip-vit-base-patch16` | **larger and more accurate** (16px patches = more tokens per image) — an upgrade, not a downgrade |
| `openai/clip-vit-large-patch14` | largest of the openai family, 768-dim embeddings — update `VectorParams(size=...)` below if you switch |

If a source tells you patch16 is "smaller", it has the patch-size convention backwards: smaller patches mean more patches per image.

---

## Exercise 2: Image Captioning with BLIP

### Solution

```python
import torch
from PIL import Image
from transformers import BlipForConditionalGeneration, BlipProcessor


class ImageCaptioner:
    """Generate short captions for images."""

    def __init__(self, model_name="Salesforce/blip-image-captioning-base"):
        self.processor = BlipProcessor.from_pretrained(model_name)
        self.model = BlipForConditionalGeneration.from_pretrained(
            model_name, torch_dtype=torch.bfloat16
        ).eval()

    @torch.no_grad()
    def caption(self, image_path, max_new_tokens=40):
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt").to(
            self.model.device, torch.bfloat16
        )
        out = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=3,
        )
        return self.processor.decode(out[0], skip_special_tokens=True)


captioner = ImageCaptioner()
print(captioner.caption("dog.jpg"))
```

`max_new_tokens` (not `max_length`) caps generated length independently of any prompt tokens. Expect short, generic captions from the base checkpoint — that is its honest ceiling. When captions must *answer questions about* an image, that is a vision-language-model job ([3501](../../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)), not a captioner upgrade.

---

## Exercise 3: Multi-Modal RAG

### Solution

```python
import uuid

import torch
import torch.nn.functional as F
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams


class MultiModalRAG:
    """Store and search documents by fused text+image embeddings."""

    NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "multimodal-rag-lab")

    def __init__(self, url="http://localhost:6333", retriever=None):
        self.client = QdrantClient(url=url)
        self.retriever = retriever or MultiModalRetriever()
        if not self.client.collection_exists("multimodal_docs"):
            self.client.create_collection(
                collection_name="multimodal_docs",
                vectors_config=VectorParams(size=512, distance=Distance.COSINE),
            )

    def _fuse(self, text_vec, image_vec):
        fused = (text_vec + image_vec) / 2.0
        return F.normalize(fused, dim=-1)

    def add_document(self, doc_id, text, image_path, metadata=None):
        vec = self._fuse(
            self.retriever.encode_text(text),
            self.retriever.encode_image(image_path),
        )
        self.client.upsert(
            collection_name="multimodal_docs",
            points=[PointStruct(
                id=str(uuid.uuid5(self.NAMESPACE, doc_id)),  # stable across runs
                vector=vec.squeeze(0).tolist(),
                payload={"text": text, "image": image_path, **(metadata or {})},
            )],
        )

    def search(self, query, top_k=5):
        q = self.retriever.encode_text(query)
        res = self.client.query_points(
            collection_name="multimodal_docs",
            query=q.squeeze(0).tolist(),
            limit=top_k,
        )
        return [
            {"text": p.payload["text"], "image": p.payload["image"], "score": p.score}
            for p in res.points
        ]
```

### Three deliberate choices, explained

```text
1. uuid5 over built-in hash(): Python's hash() for strings is salted
   per process (PYTHONHASHSEED) - the same document gets a different
   ID every run, so re-ingesting duplicates points instead of
   updating them. uuid5 is deterministic for the same input.
2. collection_exists + create_collection over recreate_collection:
   recreate deletes everything first - correct only for throwaway
   demo data. The guarded create is idempotent and preserves the index.
3. Average fusion (text+image)/2 is the simplest fusion that works
   and is re-normalized before storing. Real systems often keep both
   vectors separately and fuse at query time; that upgrade is left
   as an exercise extension.
```

The vector size (512) must match the CLIP checkpoint — switch to a ViT-L checkpoint and `VectorParams` needs `size=768`, or every upsert fails with a dimension mismatch.

---

## Common Issues

### "CLIP model too large"

The default (`clip-vit-base-patch32`) already **is** the small one. Your options, in order: run it on CPU (B/32 inference is fast enough for lab work), quantize the loader with `quantization_config=BitsAndBytesConfig(load_in_8bit=True)`, or accept the B/16 upgrade — which costs more memory and buys accuracy.

### Shape errors on similarity computation

`torch.cosine_similarity` on `(1, 512)` tensors works but reads awkwardly in loops. With normalized features, plain matrix products are cleaner: query `(1, d)` against corpus `(N, d)` is `q @ corpus.T` → `(1, N)`. If you see `RuntimeError: 1D tensors expected`, a feature vector lost its batch dimension — check for a stray `.squeeze()` before the matmul.

### Processor warnings on batched text

Encoding a list of prompts without padding produces ragged tensors. Pass `padding=True` (and `truncation=True` for long inputs) whenever `text=` receives more than one string — the zero-shot classifier above already does.

---

## References

### Related curriculum documents

- [LAB-011: Multi-Modal AI](../LAB-011-Multi-Modal-AI.md)
- [3501: Vision-Language Models](../../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)
- [3502: Audio Models](../../../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md)
- [Phase 3: Transformers](../../../phases/phase3-transformers/README.md)

### External

- [CLIP paper: Learning Transferable Visual Models From Natural Language Supervision](https://arxiv.org/abs/2103.00020)
- [BLIP paper: Bootstrapping Language-Image Pre-training](https://arxiv.org/abs/2201.12086)
- [Qdrant client: query_points API](https://api.qdrant.tech/api-reference/search/query-points)

---

## Next Steps

- Extend the store with per-modality vectors and query-time fusion
- Move from captions to questions: [3501: Vision-Language Models](../../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)
- Complete the audio half: [3502: Audio Models](../../../phases/phase3-transformers/3500-multimodal/3502-Audio-Models.md) and [LAB-012: Audio AI](../LAB-012-Audio-AI.md)
