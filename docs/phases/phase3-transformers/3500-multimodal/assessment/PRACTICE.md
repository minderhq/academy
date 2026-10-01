---
Document ID: 3500-PRACTICE
Title: "3500: Multimodal AI - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'practice', 'transformers', 'multimodal']
---

# 3500: Multimodal AI - Practice

## Exercises

### Exercise 1: CLIP Image-Text Encoding

```python
import torch
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import requests

# Load CLIP model
print("Loading CLIP model...")
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Prepare image and text
# Example with a URL image
url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

texts = ["a cat", "a dog", "a bird", "a car", "two cats sleeping"]

# Process inputs
inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)

# Get embeddings (transformers 5.x: get_*_features returns BaseModelOutputWithPooling -
# the projected features live in its pooler_output slot, not on the output itself)
with torch.no_grad():
    image_features = model.get_image_features(inputs.pixel_values).pooler_output
    text_features = model.get_text_features(inputs.input_ids, inputs.attention_mask).pooler_output

# Normalize features
image_features = image_features / image_features.norm(dim=-1, keepdim=True)
text_features = text_features / text_features.norm(dim=-1, keepdim=True)

# Compute similarity
similarity = (image_features @ text_features.T).squeeze()

print("\nImage-Text Similarities:")
for text, score in zip(texts, similarity.tolist()):
    print(f"  [{score:.4f}] {text}")

# Find best match
best_idx = similarity.argmax()
print(f"\nBest match: \"{texts[best_idx]}\" with score {similarity[best_idx]:.4f}")

# Expected Output:
# Highest similarity for "two cats" or "a cat"
# Lower similarity for unrelated concepts (dog, bird, car)
```

**Explanation:**
- CLIP learns joint image-text representations
- Uses contrastive learning to align vision and language
- Can compute similarity between images and text
- Zero-shot transfer capabilities

**Use Cases:**
- Image classification (via text prompts)
- Image-text retrieval
- Zero-shot classification
- Visual grounding

---

### Exercise 2: Vision Transformer (ViT)

```python
import torch
from transformers import ViTForImageClassification, ViTImageProcessor
from PIL import Image
import requests

# Load ViT model
print("Loading Vision Transformer...")
processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")
model = ViTForImageClassification.from_pretrained("google/vit-base-patch16-224")

# Load and process image
url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

inputs = processor(images=image, return_tensors="pt")

# Forward pass
with torch.no_grad():
    outputs = model(**inputs)
    logits = outputs.logits

# Get top-5 predictions
top5_idx = logits.topk(5).indices.squeeze().tolist()
top5_scores = torch.softmax(logits, dim=-1).topk(5).values.squeeze()

print(f"\nTop-5 Predictions:")
for idx, score in zip(top5_idx, top5_scores):
    label = model.config.id2label[idx]
    print(f"  [{score:.4f}] {label}")

# Expected Output:
# Top prediction should be cat-related (e.g., "tabby cat", "Egyptian cat")
# High confidence (>0.8) for correct category
```

**Explanation:**
- ViT applies transformer architecture to images
- Splits image into patches (e.g., 16x16 pixels)
- Treats patches like tokens in text models
- Achieves SOTA on many vision tasks

**Architecture:**
1. Split image into patches
2. Linear projection of patches
3. Add position embeddings
4. Pass through transformer encoder
5. Classification head on [CLS] token

---

### Exercise 3: Multimodal Fusion

```python
import torch
import torch.nn as nn

class MultimodalFusion(nn.Module):
    """Fusion module for combining text and image features."""

    def __init__(self, text_dim=768, image_dim=512, hidden_dim=512, num_classes=10):
        super().__init__()

        # Projection layers to common dimension
        self.text_proj = nn.Sequential(
            nn.Linear(text_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        self.image_proj = nn.Sequential(
            nn.Linear(image_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # Fusion strategies
        # 1. Concatenation-based fusion
        self.concat_fusion = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1)
        )

        # 2. Gated fusion
        self.gate = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.Sigmoid()
        )

        # Output head
        self.output = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim // 2, num_classes)
        )

    def forward(self, text_features, image_features, fusion_type='concat'):
        """
        Args:
            text_features: (batch, text_dim)
            image_features: (batch, image_dim)
            fusion_type: 'concat', 'gate', or 'add'

        Returns:
            (batch, num_classes)
        """
        # Project to common dimension
        text_proj = self.text_proj(text_features)
        image_proj = self.image_proj(image_features)

        # Fusion
        if fusion_type == 'concat':
            # Concatenate and project
            combined = torch.cat([text_proj, image_proj], dim=-1)
            fused = self.concat_fusion(combined)

        elif fusion_type == 'gate':
            # Gated fusion
            combined = torch.cat([text_proj, image_proj], dim=-1)
            gate_weights = self.gate(combined)
            fused = gate_weights * text_proj + (1 - gate_weights) * image_proj

        elif fusion_type == 'add':
            # Simple addition
            fused = text_proj + image_proj

        else:
            raise ValueError(f"Unknown fusion type: {fusion_type}")

        # Output
        logits = self.output(fused)
        return logits

# Test the fusion module
print("Testing Multimodal Fusion")
print("="*60)

fusion_model = MultimodalFusion(
    text_dim=768,
    image_dim=512,
    hidden_dim=512,
    num_classes=10
)

# Dummy features
batch_size = 4
text_features = torch.randn(batch_size, 768)
image_features = torch.randn(batch_size, 512)

# Test different fusion strategies
for fusion_type in ['concat', 'gate', 'add']:
    logits = fusion_model(text_features, image_features, fusion_type=fusion_type)
    print(f"{fusion_type.upper()} fusion output shape: {logits.shape}")

# Expected Output:
# CONCAT fusion output shape: torch.Size([4, 10])
# GATE fusion output shape: torch.Size([4, 10])
# ADD fusion output shape: torch.Size([4, 10])
```

**Explanation:**
- Multimodal fusion combines features from different modalities
- Common strategies: concatenation, gating, attention
- Critical for tasks requiring multiple input types

**Fusion Strategies:**
1. **Concatenation**: Simple, preserves all information
2. **Gated**: Learns modality importance
3. **Attention**: Cross-modal attention
4. **Tensor Fusion**: Captures interactions

---

### Exercise 4: Image Captioning with BLIP

```python
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
import requests

# Load BLIP model
print("Loading BLIP model for image captioning...")
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")

# Load image
url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

# Conditional captioning (with prompt)
inputs = processor(image, text="a photo of", return_tensors="pt")

with torch.no_grad():
    outputs = model.generate(**inputs, max_length=20)

conditional_caption = processor.decode(outputs[0], skip_special_tokens=True)
print(f"\nConditional caption: \"{conditional_caption}\"")

# Unconditional captioning
inputs = processor(image, return_tensors="pt")

with torch.no_grad():
    outputs = model.generate(**inputs, max_length=20)

unconditional_caption = processor.decode(outputs[0], skip_special_tokens=True)
print(f"Unconditional caption: \"{unconditional_caption}\"")

# Expected Output:
# Descriptive caption about cats (e.g., "two cats sleeping on a pink blanket")
# Conditional version follows the prompt format
```

**Explanation:**
- BLIP unifies vision-language understanding and generation
- Uses bootstrapping for noisy data filtering
- State-of-the-art image captioning
- Can also do VQA and visual reasoning

---

### Exercise 5: Visual Question Answering

```python
import torch
from transformers import ViltProcessor, ViltForQuestionAnswering
from PIL import Image
import requests

# Load VQA model
print("Loading ViLT model for VQA...")
processor = ViltProcessor.from_pretrained("dandelin/vilt-b32-finetuned-vqa")
model = ViltForQuestionAnswering.from_pretrained("dandelin/vilt-b32-finetuned-vqa")

# Load image
url = "http://images.cocodataset.org/val2017/000000039769.jpg"
image = Image.open(requests.get(url, stream=True).raw)

# Test questions
questions = [
    "What is in this image?",
    "How many cats are there?",
    "What color is the blanket?",
    "Are the cats awake?",
    "What animal is shown?"
]

print("\nVisual Question Answering Results:")
print("="*60)

for question in questions:
    # Prepare inputs
    encoding = processor(image, question, return_tensors="pt")

    # Forward pass
    with torch.no_grad():
        outputs = model(**encoding)
        logits = outputs.logits

    # Get prediction
    predicted_idx = logits.argmax(-1).item()
    answer = model.config.id2label[predicted_idx]

    print(f"Q: {question}")
    print(f"A: {answer}\n")

# Expected Output:
# Accurate answers about the image content
# "cat" or "cats" for animal questions
# "two" for count
# "no" for awake question
```

**Explanation:**
- VQA requires understanding both image and question
- ViLT uses late fusion of vision and language
- Trained on VQA v2 dataset
- Applications in accessibility, education, robotics

---

### Exercise 6: Audio-Text Processing (Whisper)

```python
from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch

# Load Whisper model
print("Loading Whisper model...")
processor = WhisperProcessor.from_pretrained("openai/whisper-base")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-base")

# Load audio (using dummy audio for demonstration)
# In practice, load from file: audio, sr = torchaudio.load("audio.wav")
sampling_rate = 16000

# Simulate audio tensor (1 second of audio at 16kHz)
dummy_audio = torch.randn(sampling_rate)

# Process audio
inputs = processor(dummy_audio, return_tensors="pt", sampling_rate=sampling_rate)

# Generate transcription
with torch.no_grad():
    predicted_ids = model.generate(**inputs)

transcription = processor.decode(predicted_ids[0], skip_special_tokens=True)
print(f"\nTranscription: {transcription}")

# Expected Output:
# With real audio: accurate transcription
# With dummy audio: gibberish (expected)
```

**Explanation:**
- Whisper is a robust speech recognition model
- Trained on 680k hours of multilingual data
- Handles multiple languages and translation
- Strong performance on diverse accents

---

### Exercise 7: Cross-Modal Retrieval System

```python
import torch

class CrossModalRetrieval:
    """Retrieve images given text queries or vice versa."""

    def __init__(self, model, processor):
        self.model = model
        self.processor = processor
        self.image_features_cache = []
        self.text_features_cache = []

    def encode_images(self, images):
        """Encode multiple images to features."""
        features = []
        for img in images:
            inputs = self.processor(images=img, return_tensors="pt")
            with torch.no_grad():
                feat = self.model.get_image_features(**inputs)
            feat = feat / feat.norm(dim=-1, keepdim=True)
            features.append(feat)
        return torch.cat(features, dim=0)

    def encode_texts(self, texts):
        """Encode multiple texts to features."""
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        with torch.no_grad():
            features = self.model.get_text_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features

    def retrieve_images(self, query_text, image_features, top_k=5):
        """Retrieve top-k images for a text query."""
        query_feat = self.encode_texts([query_text])
        similarities = (query_feat @ image_features.T).squeeze()
        top_indices = similarities.argsort(descending=True)[:top_k]
        return top_indices, similarities[top_indices]

    def retrieve_texts(self, query_image, text_features, top_k=5):
        """Retrieve top-k texts for an image query."""
        query_feat = self.encode_images([query_image])
        similarities = (query_feat @ text_features.T).squeeze()
        top_indices = similarities.argsort(descending=True)[:top_k]
        return top_indices, similarities[top_indices]

# Example usage
print("Cross-Modal Retrieval System")
print("="*60)

# Sample texts
texts = [
    "a cat sleeping on a blanket",
    "a dog playing in the park",
    "a bird flying in the sky",
    "two cats resting together",
    "a car driving on the road"
]

print("\nSample texts:")
for i, text in enumerate(texts):
    print(f"{i+1}. {text}")

print("\n\nTo test retrieval:")
print("1. Load a set of images")
print("2. Encode all images using encode_images()")
print("3. Query with text using retrieve_images()")
print("4. Get top-k most similar images")

# Expected Output:
# The 5 sample texts, then the 4 usage steps
# (no retrieval runs here - the encode/retrieve methods follow
# the same flow as Exercise 1: normalize, matmul, top-k)
```

---

## Summary: Multimodal AI Applications

```text
APPLICATIONS → MODELS:

Image Classification:
  → CLIP (zero-shot), ViT (supervised)

Image Captioning:
  → BLIP, BLIP-2, GIT

Visual Question Answering:
  → ViLT, BLIP, OFA

Text-to-Image Generation:
  → Stable Diffusion, DALL-E

Image-Text Retrieval:
  → CLIP, ALIGN

Audio/Speech:
  → Whisper, Wav2Vec2

Video Understanding:
  → VideoCLIP, VideoMAE

KEY PRINCIPLES:

1. Joint Embedding Spaces
   - Align different modalities in shared space
   - Enable cross-modal similarity computation

2. Fusion Strategies
   - Early fusion: combine raw inputs
   - Late fusion: combine processed features
   - Hybrid: multi-stage fusion

3. Pre-training Objectives
   - Contrastive learning (CLIP)
   - Masked modeling (MAE)
   - Generative modeling (BLIP)

4. Zero-Shot Transfer
   - Leverage language for vision tasks
   - Natural language prompts
   - No task-specific training needed
```
