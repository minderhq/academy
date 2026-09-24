---
Document ID: TUTORIAL-011
Title: "TUTORIAL-011: Multi-Modal AI"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Intermediate
---

# TUTORIAL-011: Multi-Modal AI

## Overview

This tutorial covers multi-modal AI systems that can understand and generate content across text, images, audio, and video.

**Duration:** 5 hours
**Difficulty:** Advanced
**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-003 (RAG Basics)

---

## Learning Objectives

After this tutorial, you will:
- Understand multi-modal model architectures
- Use vision-language models (CLIP, BLIP)
- Build image captioning systems
- Implement video understanding
- Create cross-modal retrieval systems

---

## Part 1: Vision-Language Models

### CLIP (Contrastive Language-Image Pre-training)

```python
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

def clip_demo():
    """Zero-shot image classification with CLIP"""

    # Load model
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    # Load image
    image = Image.open("path/to/image.jpg")

    # Define candidate classes
    text_inputs = [
        "a photo of a cat",
        "a photo of a dog",
        "a photo of a bird",
        "a photo of a car"
    ]

    # Process inputs
    inputs = processor(
        text=text_inputs,
        images=image,
        return_tensors="pt",
        padding=True
    )

    # Forward pass
    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image  # Image-text similarity
    probs = logits_per_image.softmax(dim=1).squeeze()

    # Print results
    for text, prob in zip(text_inputs, probs):
        print(f"{text}: {prob:.2%}")

# Usage
clip_demo()
```

### BLIP (Bootstrapped Language-Image Pre-training)

```python
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image

def image_captioning(image_path: str):
    """Generate image captions with BLIP"""

    # Load model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    # Load image
    image = Image.open(image_path).convert("RGB")

    # Conditional captioning
    inputs = processor(image, text="a photo of", return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    print(f"Caption: {caption}")

    # Unconditional captioning
    inputs = processor(image, return_tensors="pt")
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)

    print(f"Caption (unconditional): {caption}")

# Usage
image_captioning("path/to/image.jpg")
```

---

## Part 2: Image Understanding

### Visual Question Answering

```python
from transformers import BlipForQuestionAnswering

def visual_qa(image_path: str, question: str):
    """Answer questions about images"""

    # Load model
    processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
    model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base")

    # Load image
    image = Image.open(image_path).convert("RGB")

    # Process inputs
    inputs = processor(image, text=question, return_tensors="pt")

    # Generate answer
    out = model.generate(**inputs)
    answer = processor.decode(out[0], skip_special_tokens=True)

    print(f"Q: {question}")
    print(f"A: {answer}")

# Usage
visual_qa("image.jpg", "What color is the cat?")
visual_qa("image.jpg", "How many animals are in the image?")
```

### Image Classification with CLIP

```python
def zero_shot_classification(image_path: str, classes: list):
    """Classify image without training data"""

    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

    image = Image.open(image_path)
    text_inputs = [f"a photo of {cls}" for cls in classes]

    inputs = processor(
        text=text_inputs,
        images=image,
        return_tensors="pt",
        padding=True
    )

    outputs = model(**inputs)
    logits_per_image = outputs.logits_per_image
    probs = logits_per_image.softmax(dim=1).squeeze()

    # Get top prediction
    top_idx = probs.argmax()
    print(f"Predicted: {classes[top_idx]} ({probs[top_idx]:.2%})")

    # Show all probabilities
    for cls, prob in zip(classes, probs):
        print(f"  {cls}: {prob:.2%}")

# Usage
zero_shot_classification(
    "image.jpg",
    ["cat", "dog", "bird", "fish", "reptile"]
)
```

---

## Part 3: Cross-Modal Retrieval

### Image-Text Retrieval

```python
import numpy as np
from typing import List, Tuple

class MultiModalRetriever:
    """Retrieve images using text queries or vice versa"""

    def __init__(self):
        from sentence_transformers import SentenceTransformer
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        self.image_embeddings = []
        self.text_embeddings = []
        self.images = []
        self.captions = []

    def index(self, images: List[str], captions: List[str]):
        """Index images with captions"""
        from PIL import Image

        for img_path, caption in zip(images, captions):
            image = Image.open(img_path).convert("RGB")

            # Get embeddings
            inputs = self.clip_processor(
                text=[caption],
                images=image,
                return_tensors="pt",
                padding=True
            )

            with torch.no_grad():
                outputs = self.clip_model(**inputs)
                image_emb = outputs.image_embeds
                text_emb = outputs.text_embeds

            self.image_embeddings.append(image_emb.cpu())
            self.text_embeddings.append(text_emb.cpu())
            self.images.append(image)
            self.captions.append(caption)

    def search_by_text(self, query: str, k: int = 5) -> List[Tuple[str, float]]:
        """Search images by text query"""
        # Get query embedding
        inputs = self.clip_processor(text=[query], return_tensors="pt", padding=True)

        with torch.no_grad():
            outputs = self.clip_model.get_text_features(**inputs)
            query_emb = outputs.cpu()

        # Calculate similarities
        similarities = []
        for img_emb in self.image_embeddings:
            sim = torch.nn.functional.cosine_similarity(
                query_emb, img_emb, dim=-1
            ).item()
            similarities.append(sim)

        # Get top-k
        indices = np.argsort(similarities)[::-1][:k]

        return [(self.captions[i], similarities[i]) for i in indices]

    def search_by_image(self, image_path: str, k: int = 5) -> List[Tuple[str, float]]:
        """Search captions by image"""
        image = Image.open(image_path).convert("RGB")

        inputs = self.clip_processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = self.clip_model.get_image_features(**inputs)
            query_emb = outputs.cpu()

        # Calculate similarities
        similarities = []
        for text_emb in self.text_embeddings:
            sim = torch.nn.functional.cosine_similarity(
                query_emb, text_emb, dim=-1
            ).item()
            similarities.append(sim)

        indices = np.argsort(similarities)[::-1][:k]

        return [(self.captions[i], similarities[i]) for i in indices]
```

---

## Part 4: Video Understanding

### Video Frame Analysis

```python
import cv2
import torch
from PIL import Image

def analyze_video(video_path: str, frame_interval: int = 30):
    """Extract and analyze video frames"""

    # Open video
    cap = cv2.VideoCapture(video_path)

    # Load models
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    frame_count = 0
    captions = []

    while cap.isOpened():
        ret, frame = cap.read()

        if not ret:
            break

        # Process every nth frame
        if frame_count % frame_interval == 0:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)

            # Generate caption
            inputs = processor(image, return_tensors="pt")
            out = model.generate(**inputs)
            caption = processor.decode(out[0], skip_special_tokens=True)

            captions.append({
                "frame": frame_count,
                "timestamp": frame_count / cap.get(cv2.CAP_PROP_FPS),
                "caption": caption
            })

            print(f"Frame {frame_count}: {caption}")

        frame_count += 1

    cap.release()
    return captions

# Usage
captions = analyze_video("video.mp4", frame_interval=30)
```

### Video Question Answering

```python
def video_qa(video_path: str, question: str):
    """Answer questions about video content"""

    # Sample frames
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FPS) * cap.get(cv2.CAP_PROP_FRAME_COUNT))

    # Get representative frames
    frame_indices = np.linspace(0, total_frames - 1, 8).astype(int)

    frames = []
    for idx in frame_indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(frame_rgb))

    cap.release()

    # Generate captions for each frame
    processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

    frame_captions = []
    for frame in frames:
        inputs = processor(frame, return_tensors="pt")
        out = model.generate(**inputs)
        caption = processor.decode(out[0], skip_special_tokens=True)
        frame_captions.append(caption)

    # Combine captions and answer question
    context = " ".join(frame_captions)

    # Use LLM to answer
    from transformers import AutoModelForCausalLM, AutoTokenizer

    llm = AutoModelForCausalLM.from_pretrained("gpt2")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")

    prompt = f"""Video context: {context}

Question: {question}
Answer:"""

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = llm.generate(**inputs, max_new_tokens=50)
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)

    print(f"Answer: {answer}")
```

---

## Part 5: Audio-Visual Models

### Audio-Visual Speech Recognition

```python
from transformers import AutoProcessor, AutoModelForCTC
import torchaudio

def audio_visual_asr(video_path: str):
    """
    Combine audio and visual for speech recognition
    (Requires specialized model like RAVEn)
    """

    # Extract audio from video
    import subprocess

    audio_path = "temp_audio.wav"
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path
    ])

    # Load audio
    waveform, sample_rate = torchaudio.load(audio_path)

    # Transcribe
    from transformers import WhisperProcessor, WhisperForConditionalGeneration

    processor = WhisperProcessor.from_pretrained("openai/whisper-base")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

    inputs = processor(waveform.squeeze(), sampling_rate=sample_rate, return_tensors="pt")
    input_features = inputs.input_features

    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    print(f"Transcription: {transcription}")

    return transcription
```

---

## Part 6: Multi-Modal RAG

### Image-Text RAG System

```python
from transformers import CLIPModel, CLIPProcessor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class MultiModalRAG:
    """RAG system that handles both images and text"""

    def __init__(self):
        # Load CLIP
        self.clip = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        # Initialize Qdrant
        self.client = QdrantClient(location=":memory:")
        self.client.create_collection(
            collection_name="multimodal",
            vectors_config=VectorParams(size=512, distance=Distance.COSINE)
        )

    def index_documents(
        self,
        documents: List[dict],
        id_start: int = 0
    ):
        """Index multimodal documents"""
        points = []

        for i, doc in enumerate(documents):
            # Get embeddings
            if "image" in doc:
                from PIL import Image
                image = Image.open(doc["image"])
                inputs = self.processor(images=image, return_tensors="pt")

                with torch.no_grad():
                    emb = self.clip.get_image_features(**inputs)

            else:
                inputs = self.processor(text=doc["text"], return_tensors="pt")

                with torch.no_grad():
                    emb = self.clip.get_text_features(**inputs)

            points.append(
                PointStruct(
                    id=id_start + i,
                    vector=emb.squeeze().cpu().tolist(),
                    payload=doc
                )
            )

        self.client.upsert(
            collection_name="multimodal",
            points=points
        )

    def search(self, query: str, k: int = 5) -> List[dict]:
        """Search with text query"""
        inputs = self.processor(text=[query], return_tensors="pt")

        with torch.no_grad():
            query_emb = self.clip.get_text_features(**inputs)

        results = self.client.search(
            collection_name="multimodal",
            query_vector=query_emb.squeeze().cpu().tolist(),
            limit=k
        )

        return results

    def search_by_image(self, image_path: str, k: int = 5) -> List[dict]:
        """Search with image query"""
        from PIL import Image
        image = Image.open(image_path)

        inputs = self.processor(images=image, return_tensors="pt")

        with torch.no_grad():
            query_emb = self.clip.get_image_features(**inputs)

        results = self.client.search(
            collection_name="multimodal",
            query_vector=query_emb.squeeze().cpu().tolist(),
            limit=k
        )

        return results
```

---

## Exercises

1. **Zero-shot classify** custom images with CLIP
2. **Build image captioning** system
3. **Create cross-modal retrieval** for your documents
4. **Analyze video** and extract key moments
5. **Build multi-modal RAG** for your use case

---

## Completion Checklist

- [ ] CLIP zero-shot classification working
- [ ] Image captioning implemented
- [ ] Cross-modal retrieval built
- [ ] Video analysis completed
- [ ] Multi-modal RAG prototype

---

**Next Steps:** LAB-011: Multi-Modal AI or EXP_3501: Multi-Modal RAG
