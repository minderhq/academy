---
Document ID: SOLUTION-LAB-011
Title: "SOLUTION-LAB-011: Multi-Modal AI"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
---

# SOLUTION-LAB-011: Multi-Modal AI

## Overview
Complete solution for multi-modal AI (text + image) using CLIP and custom architectures.

---

## Problem Statement

Build a system that can:
1. Encode images and text into shared embedding space
2. Retrieve images based on text queries
3. Generate text descriptions for images
4. Perform zero-shot classification

---

## Part 1: CLIP-based Retrieval

### Image-Text Retrieval System

```python
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import torch
import numpy as np

class MultiModalRetriever:
    """Process and retrieve using CLIP."""

    def __init__(self, model_name="openai/clip-vit-base-patch32"):
        self.model = CLIPModel.from_pretrained(model_name)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def encode_image(self, image_path):
        """Encode image to vector."""
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        with torch.no_grad():
            return self.model.get_image_features(**inputs)

    def encode_text(self, text):
        """Encode text to vector."""
        inputs = self.processor(text=[text], return_tensors="pt")
        with torch.no_grad():
            return self.model.get_text_features(**inputs)

    def retrieve_images(self, query, image_paths, top_k=5):
        """Find most similar images."""
        query_features = self.encode_text("")

        similarities = []
        for img_path in image_paths:
            img_features = self.encode_image(img_path)
            sim = torch.cosine_similarity(query_features, img_features)
            similarities.append((img_path, sim.item()))

        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]

    def zero_shot_classify(self, image, classes):
        """Classify image into classes."""
        image_features = self.encode_image(image)
        text_inputs = self.processor(text=classes, return_tensors="pt", padding=True)
        text_features = self.model.get_text_features(**text_inputs)

        similarities = (image_features @ text_features.T).squeeze()
        pred_idx = similarities.argmax().item()
        return classes[pred_idx], similarities[pred_idx].item()
```

### Usage Example

```python
# Initialize
retriever = MultiModalRetriever()

# Image search
query = "a dog playing in the park"
results = retriever.retrieve_images(query, image_paths, top_k=5)

for path, score in results:
    print(f"{path}: {score:.4f}")

# Zero-shot classification
image = Image.open("cat.jpg")
classes = ["a dog", "a cat", "a bird", "a car"]
label, confidence = retriever.zero_shot_classify(image, classes)
print(f"Predicted: {label} ({confidence:.4f})")
```

---

## Part 2: Image Captioning with BLIP

```python
from transformers import BlipProcessor, BlipForConditionalGeneration

class ImageCaptioner:
    """Generate text descriptions for images."""

    def __init__(self):
        self.processor = BlipProcessor.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.model = BlipForConditionalGeneration.from_pretrained(
            "Salesforce/blip-image-captioning-base"
        )
        self.model.eval()

    def caption(self, image_path, max_length=50):
        """Generate caption for image."""
        image = Image.open(image_path).convert("RGB")
        inputs = self.processor(image, return_tensors="pt")

        with torch.no_grad():
            out = self.model.generate(
                **inputs,
                max_length=max_length,
                num_beams=5,
                early_stopping=True
            )

        caption = self.processor.decode(out[0], skip_special_tokens=True)
        return caption

# Usage
captioner = ImageCaptioner()
caption = captioner.caption("dog.jpg")
print(f"Caption: {caption}")
```

---

## Part 3: Multi-Modal RAG

### Image + Text RAG System

```python
import qdrant_client as qc
from qdrant_client.models import Distance, VectorParams, PointStruct

class MultiModalRAG:
    """RAG system that handles both text and images."""

    def __init__(self):
        self.client = qc.QdrantClient(url="http://localhost:6333")
        self.clip = MultiModalRetriever()

        # Create collection
        self.client.recreate_collection(
            collection_name="multimodal_docs",
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )

    def add_document(self, text, image_path, metadata=None):
        """Add document with text and image."""
        # Encode both
        text_vec = self.clip.encode_text(text)
        image_vec = self.clip.encode_image(image_path)

        # Combine (average)
        combined = (text_vec + image_vec) / 2

        # Store
        self.client.upsert(
            collection_name="multimodal_docs",
            points=[PointStruct(
                id=hash(text + image_path),
                vector=combined.cpu().squeeze().tolist(),
                payload={**metadata, "text": text, "image": image_path}
            )]
        )

    def search(self, query, image=None, top_k=5):
        """Search with query text and optional image."""
        query_vec = self.clip.encode_text(query)

        if image:
            image_vec = self.clip.encode_image(image)
            combined = (query_vec + image_vec) / 2
        else:
            combined = query_vec

        results = self.client.search(
            collection_name="multimodal_docs",
            query_vector=combined.cpu().squeeze().tolist(),
            limit=top_k
        )

        return [
            {"text": r.payload["text"], "image": r.payload["image"], "score": r.score}
            for r in results
        ]
```

---

## Part 4: Advanced Multi-Modal Pipeline

```python
class MultiModalPipeline:
    """Complete multi-modal processing pipeline."""

    def __init__(self):
        self.retriever = MultiModalRetriever()
        self.captioner = ImageCaptioner()
        self.rag = MultiModalRAG()

    def process_query(self, text_query, image=None):
        """Process multi-modal query."""

        # Step 1: Retrieve relevant documents
        docs = self.rag.search(text_query, image, top_k=3)

        # Step 2: Generate context
        context = "\n".join([d["text"] for d in docs])

        # Step 3: If image provided, caption it
        if image:
            caption = self.captioner.caption(image)
            context += f"\n[Image Content: {caption}]"

        return {
            "query": text_query,
            "context": context,
            "sources": docs
        }

    def answer_question(self, question, image=None):
        """Answer question with multi-modal context."""

        # Get context
        result = self.process_query(question, image)

        # Generate answer (can use LLM here)
        prompt = f"""
        Context: {result['context']}

        Question: {question}

        Answer:
        """

        # Send to LLM (your preferred model)
        # answer = llm.generate(prompt)

        return {
            "answer": prompt,  # Replace with actual LLM call
            "sources": result["sources"]
        }
```

---

## Common Issues

### Issue: CLIP model too large

**Solution:**
```python
# Use smaller model
model_name = "openai/clip-vit-base-patch16"  # Smaller

# Or quantize
from transformers import BitsAndBytesConfig
quantization = BitsAndBytesConfig(load_in_8bit=True)
```

### Issue: Poor image quality

**Solution:**
```python
# Preprocess image
from torchvision import transforms

preprocess = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225])
])
```

---

## Complete Example

```python
# Setup
pipeline = MultiModalPipeline()

# Add documents
pipeline.rag.add_document(
    "This document covers ML basics",
    "ml_basics.jpg",
    {"category": "tutorial", "date": "2024-01-01"}
)

# Query with text only
result = pipeline.answer_question("What is machine learning?")

# Query with text + image
result = pipeline.answer_question(
    "What does this image show?",
    image="query_image.jpg"
)

print(result["answer"])
print(f"Sources: {[s['text'] for s in result['sources']]}")
```

---

**Last Updated:** 2026-02-05
**Difficulty:** ⭐⭐⭐⭐
**Estimated Time:** 3-4 hours

**Related:** [Phase 3: Multi-modal](../../../phases/phase3-transformers/3500-multimodal/README.md)
