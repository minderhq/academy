---
Document ID: TUTORIAL-011
Title: "TUTORIAL-011: Multi-Modal AI"
Last Updated: 2026-10-08
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: [PHASE-3]
Tags: ['tutorial', 'multimodal', 'vision']
---

# TUTORIAL-011: Multi-Modal AI

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Vision-Language Models](#part-1-vision-language-models)
- [Part 2: Image Understanding](#part-2-image-understanding)
- [Part 3: Cross-Modal Retrieval](#part-3-cross-modal-retrieval)
- [Part 4: Video Understanding](#part-4-video-understanding)
- [Part 5: Audio Transcription](#part-5-audio-transcription)
- [Part 6: Multi-Modal RAG](#part-6-multi-modal-rag)
- [Exercises](#exercises)
- [Completion Checklist](#completion-checklist)
- [References](#references)
- [Next Steps](#next-steps)

---

## Abstract

This tutorial covers multi-modal AI systems that can understand and generate content across text, images, audio, and video.

**Duration:** 5 hours

**Difficulty:** ⭐⭐⭐ Advanced

**Prerequisites:** TUTORIAL-001 (Hello LLM), TUTORIAL-003 (RAG Basics)

---

## Learning Objectives

After this tutorial, you will:

- Understand multi-modal model architectures
- Use vision-language models (CLIP, BLIP)
- Build image captioning systems
- Implement video understanding
- Transcribe a video's audio track with Whisper
- Create cross-modal retrieval systems

---

## Part 1: Vision-Language Models

### Installation

```bash
uv pip install torch transformers pillow opencv-python qdrant-client torchaudio
```

Parts 1-3 need torch/transformers/pillow, Part 4 opencv-python (the
cv2 import), Part 5 torchaudio plus a system **ffmpeg** on the PATH
(the code shells out to it for audio extraction), and Part 6
qdrant-client. numpy ships with the rest of the stack.

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

# Expected Output:
# a photo of a cat: <N>.NN%
# a photo of a dog: <N>.NN%
# a photo of a bird: <N>.NN%
# a photo of a car: <N>.NN%
# (percentages depend entirely on the image; the four scores are a
#  softmax over the candidate captions, so they sum to ~100%)
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

# Expected Output:
# Caption: <BLIP caption, continuing from the "a photo of" prompt>
# Caption (unconditional): <BLIP caption, conditioned only on the image>
# (exact text depends on the image; BLIP's captioning checkpoint
#  generates lowercase text with no terminal punctuation)
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

# Expected Output:
# Q: What color is the cat?
# A: <one-to-few-word answer from BLIP-VQA>
# Q: How many animals are in the image?
# A: <short answer - counting is BLIP-VQA's weak spot, expect noise>
# (answers depend on the image; BLIP-VQA is trained to reply in a
#  handful of words)
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

# Expected Output:
# Predicted: <class> (<N>.NN%)
#   <class>: <N>.NN%
#   ... (five lines, one per candidate - a softmax over them, so
#        they sum to ~100%; which class wins depends on the image)
```

---

## Part 3: Cross-Modal Retrieval

### Image-Text Retrieval

```python
import numpy as np


# CLIPModel/CLIPProcessor/torch/PIL Image come from Part 1's import
# header (this tutorial's blocks run top-down)

class MultiModalRetriever:
    """Retrieve images using text queries or vice versa"""

    def __init__(self):
        self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

        self.image_embeddings = []
        self.text_embeddings = []
        self.images = []
        self.captions = []

    def index(self, images: list[str], captions: list[str]):
        """Index images with captions"""
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

    def search_by_text(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        """Search images by text query"""
        # Get query embedding
        inputs = self.clip_processor(text=[query], return_tensors="pt", padding=True)

        with torch.no_grad():
            outputs = self.clip_model.get_text_features(**inputs).pooler_output  # transformers 5.x: projected features live in pooler_output
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

    def search_by_image(self, image_path: str, k: int = 5) -> list[tuple[str, float]]:
        """Search captions by image"""
        image = Image.open(image_path).convert("RGB")

        inputs = self.clip_processor(images=image, return_tensors="pt")

        with torch.no_grad():
            outputs = self.clip_model.get_image_features(**inputs).pooler_output
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

# Expected Output:
# Frame 0: <caption>
# Frame 30: <caption>
# ... (one line per sampled frame - every frame_interval-th frame;
#      captions depend on the video content)
```

### Video Question Answering

```python
# cv2/numpy/PIL Image/BLIP classes come from the earlier parts
# (top-down flow); the LLM that reads the captions is new here
from transformers import AutoModelForCausalLM, AutoTokenizer

def video_qa(video_path: str, question: str):
    """Answer questions about video content"""

    # Sample frames
    cap = cv2.VideoCapture(video_path)
    # CAP_PROP_FRAME_COUNT is already a frame COUNT - multiplying it
    # by the FPS inflates it by the fps factor, pushing the sampled
    # indices past the end of the video (cap.read() then returns
    # False and frames are silently dropped)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

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
    llm = AutoModelForCausalLM.from_pretrained("gpt2")
    tokenizer = AutoTokenizer.from_pretrained("gpt2")

    prompt = f"""Video context: {context}

Question: {question}
Answer:"""

    inputs = tokenizer(prompt, return_tensors="pt")
    outputs = llm.generate(**inputs, max_new_tokens=50)
    # generate() returns the FULL prompt+continuation sequence -
    # decoding the whole thing would print the entire prompt back
    # under the "Answer:" label, so slice off the continuation only
    prompt_len = inputs["input_ids"].shape[-1]
    answer = tokenizer.decode(
        outputs[0][prompt_len:], skip_special_tokens=True
    )

    print(f"Answer: {answer}")

# Expected Output:
# Answer: <continuation generated from the caption context>
# (gpt2 is a tiny base model - expect fluent but loosely grounded
#  text; production video QA feeds frames directly to an
#  instruction-tuned vision-language model instead)
```

---

## Part 5: Audio Transcription

### Audio Transcription (Whisper)

```python
import subprocess

import torchaudio
from transformers import WhisperProcessor, WhisperForConditionalGeneration

def transcribe_audio(video_path: str):
    """
    Transcribe a video's audio track with Whisper.

    True audio-VISUAL ASR - lip-reading models like RAVEn or
    AV-HuBERT that fuse mouth-region video frames with the audio -
    is a specialized model family; the audio-only branch below is
    the piece every such system still needs.
    """

    # Extract mono 16 kHz audio - Whisper's expected input rate.
    # check=True so a missing ffmpeg or unreadable video fails
    # loudly instead of leaving torchaudio.load to fail obscurely
    audio_path = "temp_audio.wav"
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vn", "-acodec", "pcm_s16le",
        "-ar", "16000", "-ac", "1",
        audio_path
    ], check=True)

    # Load audio
    waveform, sample_rate = torchaudio.load(audio_path)

    # Transcribe
    processor = WhisperProcessor.from_pretrained("openai/whisper-base")
    model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

    inputs = processor(waveform.squeeze(), sampling_rate=sample_rate, return_tensors="pt")
    input_features = inputs.input_features

    generated_ids = model.generate(inputs=input_features)
    transcription = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

    print(f"Transcription: {transcription}")

    return transcription

# Usage
transcribe_audio("video.mp4")

# Expected Output:
# Transcription: <verbatim English transcription of the audio>
# (exact words depend on the recording; whisper-base decodes plain
#  English text and needs the 16 kHz mono wav produced above)
```

---

## Part 6: Multi-Modal RAG

### Image-Text RAG System

```python
from transformers import CLIPModel, CLIPProcessor
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# torch and PIL Image come from Part 1's import header (top-down flow)

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
        documents: list[dict],
        id_start: int = 0
    ):
        """Index multimodal documents"""
        points = []

        for i, doc in enumerate(documents):
            # Get embeddings
            if "image" in doc:
                # .convert("RGB") - grayscale/palette images would
                # otherwise hit the processor's RGB expectation
                image = Image.open(doc["image"]).convert("RGB")
                inputs = self.processor(images=image, return_tensors="pt")

                with torch.no_grad():
                    emb = self.clip.get_image_features(**inputs).pooler_output

            else:
                inputs = self.processor(text=doc["text"], return_tensors="pt")

                with torch.no_grad():
                    emb = self.clip.get_text_features(**inputs).pooler_output

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

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Search with text query"""
        inputs = self.processor(text=[query], return_tensors="pt")

        with torch.no_grad():
            query_emb = self.clip.get_text_features(**inputs).pooler_output

        # query_points replaces client.search, deprecated since
        # qdrant-client 1.10 - it returns a QueryResponse whose
        # .points hold the ScoredPoint list
        results = self.client.query_points(
            collection_name="multimodal",
            query=query_emb.squeeze().cpu().tolist(),
            limit=k
        ).points

        return results

    def search_by_image(self, image_path: str, k: int = 5) -> list[dict]:
        """Search with image query"""
        image = Image.open(image_path).convert("RGB")

        inputs = self.processor(images=image, return_tensors="pt")

        with torch.no_grad():
            query_emb = self.clip.get_image_features(**inputs).pooler_output

        results = self.client.query_points(
            collection_name="multimodal",
            query=query_emb.squeeze().cpu().tolist(),
            limit=k
        ).points

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
- [ ] Audio transcription working
- [ ] Multi-modal RAG prototype

---

## References

### Related Minder Academy Documents

- [TUTORIAL-001: Hello LLM](TUTORIAL-001-Hello-LLM.md)
- [TUTORIAL-003: RAG Basics](TUTORIAL-003-RAG-Basics.md)
- [LAB-011: Multi-Modal AI](../labs/LAB-011-Multi-Modal-AI.md)
- [3501: Vision-Language Models](../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)

---

## Next Steps

- Hands-on: **[3501: Vision-Language Models](../../phases/phase3-transformers/3500-multimodal/3501-Vision-Language-Models.md)**
- Practice: **[LAB-011: Multi-Modal AI](../labs/LAB-011-Multi-Modal-AI.md)**
