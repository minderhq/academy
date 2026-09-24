# LAB-011: Multi-Modal AI

**Vision + Language Models - Build Systems That See and Understand**

---

## 📋 Lab Overview

**Time:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐ Expert
**Prerequisites:**
- LAB-002: RAG Implementation
- LAB-004: ReAct Agent
- Understanding of Transformers (Volume 3)
- Basic computer vision concepts

**Learning Objectives:**
- Master Vision Transformer (ViT) architecture
- Implement CLIP for zero-shot image classification
- Build LLaVA-style vision-language models
- Create multi-modal agents with vision capabilities
- Implement image understanding pipelines
- Handle video analysis with LLMs
- Deploy multi-modal systems in production

---

## 🎯 What You'll Build

By the end of this lab, you will have:

1. **Image Classification with CLIP** - Zero-shot classification on any image
2. **Visual Q&A System** - Answer questions about images
3. **Multi-Modal Agent** - Agent that can see and analyze images
4. **Video Summarization** - Extract insights from video content
5. **Production Multi-Modal API** - Deployed with Docker

---

## 🏗️ Part 1: Vision Transformers (ViT) Fundamentals (90 minutes)

### Understanding ViT Architecture

Vision Transformers revolutionized computer vision by applying transformer architecture to images. Let's understand how they work.

```python
# File: vit_architecture.py
"""
Vision Transformer (ViT) Architecture Explained
===============================================

ViT divides an image into patches, treats each patch as a token,
and processes them with a standard transformer encoder.

Key Components:
1. Patch Embedding: Convert image patches to embeddings
2. Position Encoding: Add positional information
3. Transformer Encoder: Process patch embeddings
4. Classification Head: Output predictions
"""

import torch
import torch.nn as nn
from typing import Tuple
import numpy as np

class PatchEmbedding(nn.Module):
    """
    Split image into patches and embed them.

    Example:
    - Input: (B, C, H, W) = (1, 3, 224, 224)
    - Patch size: 16x16
    - Number of patches: 14x14 = 196
    - Output: (1, 196, 768)
    """

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        embed_dim: int = 768,
    ):
        super().__init__()
        self.image_size = image_size
        self.patch_size = patch_size
        self.n_patches = (image_size // patch_size) ** 2

        # Use convolution to create patch embeddings
        self.proj = nn.Conv2d(
            in_channels,
            embed_dim,
            kernel_size=patch_size,
            stride=patch_size,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, C, H, W)

        Returns:
            patches: (B, N, D)
            where N = H*W / patch_size^2
        """
        x = self.proj(x)  # (B, D, H/P, W/P)
        x = x.flatten(2)  # (B, D, N)
        x = x.transpose(1, 2)  # (B, N, D)
        return x

class MultiHeadSelfAttention(nn.Module):
    """Multi-head self-attention mechanism"""

    def __init__(self, embed_dim: int = 768, num_heads: int = 12):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        assert self.head_dim * num_heads == embed_dim

        self.qkv = nn.Linear(embed_dim, embed_dim * 3)
        self.proj = nn.Linear(embed_dim, embed_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, N, D)

        Returns:
            out: (B, N, D)
        """
        B, N, D = x.shape

        # Generate Q, K, V
        qkv = self.qkv(x).reshape(B, N, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)  # (3, B, H, N, D)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Scaled dot-product attention
        attn = (q @ k.transpose(-2, -1)) / (self.head_dim ** 0.5)
        attn = attn.softmax(dim=-1)

        out = attn @ v  # (B, H, N, D)
        out = out.transpose(1, 2).reshape(B, N, D)
        out = self.proj(out)

        return out

class TransformerBlock(nn.Module):
    """Transformer encoder block"""

    def __init__(self, embed_dim: int = 768, num_heads: int = 12, mlp_ratio: float = 4.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(embed_dim)
        self.attn = MultiHeadSelfAttention(embed_dim, num_heads)
        self.norm2 = nn.LayerNorm(embed_dim)

        mlp_hidden_dim = int(embed_dim * mlp_ratio)
        self.mlp = nn.Sequential(
            nn.Linear(embed_dim, mlp_hidden_dim),
            nn.GELU(),
            nn.Linear(mlp_hidden_dim, embed_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x

class VisionTransformer(nn.Module):
    """
    Complete Vision Transformer for image classification.

    Architecture:
    1. Patch Embedding
    2. Class Token + Position Embedding
    3. Transformer Encoder (x12)
    4. MLP Head for classification
    """

    def __init__(
        self,
        image_size: int = 224,
        patch_size: int = 16,
        in_channels: int = 3,
        num_classes: int = 1000,
        embed_dim: int = 768,
        depth: int = 12,
        num_heads: int = 12,
    ):
        super().__init__()

        # Patch embedding
        self.patch_embed = PatchEmbedding(image_size, patch_size, in_channels, embed_dim)

        # Class token (learnable)
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))

        # Position embedding
        self.pos_embed = nn.Parameter(
            torch.zeros(1, 1 + self.patch_embed.n_patches, embed_dim)
        )

        # Transformer encoder
        self.blocks = nn.ModuleList([
            TransformerBlock(embed_dim, num_heads)
            for _ in range(depth)
        ])

        # Layer norm
        self.norm = nn.LayerNorm(embed_dim)

        # Classification head
        self.head = nn.Linear(embed_dim, num_classes)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        nn.init.trunc_normal_(self.pos_embed, std=0.02)
        nn.init.trunc_normal_(self.cls_token, std=0.02)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (B, C, H, W)

        Returns:
            logits: (B, num_classes)
        """
        B = x.shape[0]

        # Patch embeddings
        x = self.patch_embed(x)  # (B, N, D)

        # Add class token
        cls_tokens = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls_tokens, x], dim=1)

        # Add position embedding
        x = x + self.pos_embed

        # Transformer encoder
        for block in self.blocks:
            x = block(x)

        # Layer norm
        x = self.norm(x)

        # Get class token output
        cls_token_final = x[:, 0]

        # Classification head
        logits = self.head(cls_token_final)

        return logits

# Demo: Load pre-trained ViT
def load_vit_model():
    """Load a pre-trained ViT model"""
    from transformers import ViTModel, ViTImageProcessor

    # Load pre-trained model
    model = ViTModel.from_pretrained("google/vit-base-patch16-224")
    processor = ViTImageProcessor.from_pretrained("google/vit-base-patch16-224")

    return model, processor

# Test ViT
if __name__ == "__main__":
    from PIL import Image
    import requests

    # Load model
    model, processor = load_vit_model()
    model.eval()

    # Load and process image
    url = "http://images.cocodataset.org/val2017/000000039769.jpg"
    image = Image.open(requests.get(url, stream=True).raw)

    inputs = processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        # Get image embeddings
        image_embeddings = outputs.last_hidden_state
        print(f"Image embeddings shape: {image_embeddings.shape}")
        print(f"CLS token: {image_embeddings[:, 0, :].shape}")
```

### Step 1.1: Implement Vision Transformer from Scratch

**Exercise:** Build a complete ViT model and test it on sample images.

```bash
# Run ViT demo
python vit_architecture.py

# Expected output:
# Image embeddings shape: torch.Size([1, 197, 768])
# CLS token: torch.Size([1, 768])
```

**Checkpoint 1:** ✅ You understand ViT architecture

---

## 🔗 Part 2: CLIP - Connecting Vision and Language (120 minutes)

### Understanding CLIP

CLIP (Contrastive Language-Image Pre-training) learns visual concepts from natural language supervision. It can perform zero-shot classification on any visual task.

```python
# File: clip_model.py
"""
CLIP: Contrastive Language-Image Pre-training
=============================================

CLIP Architecture:
1. Image Encoder (Vision Transformer)
2. Text Encoder (Transformer)
3. Contrastive Learning Objective

Key Innovation: Learn joint vision-language representations
by matching images to their captions.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from transformers import CLIPProcessor, CLIPModel
from PIL import Image
import numpy as np

class CLIPWrapper:
    """
    Wrapper for OpenAI's CLIP model with enhanced functionality.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32"):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)
        self.model.eval()

    def encode_image(self, image: Image.Image) -> torch.Tensor:
        """Encode image to embedding vector"""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            image_features = self.model.get_image_features(**inputs)
        return image_features

    def encode_text(self, text: str) -> torch.Tensor:
        """Encode text to embedding vector"""
        inputs = self.processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        with torch.no_grad():
            text_features = self.model.get_text_features(**inputs)
        return text_features

    def zero_shot_classification(
        self,
        image: Image.Image,
        class_labels: list,
        template: str = "a photo of a {}"
    ) -> dict:
        """
        Perform zero-shot image classification.

        Args:
            image: PIL Image
            class_labels: List of possible class names
            template: Prompt template for class names

        Returns:
            Dictionary with probabilities for each class
        """
        # Format class labels with template
        text_inputs = [template.format(label) for label in class_labels]

        # Process inputs
        inputs = self.processor(
            text=text_inputs,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # Get features
        with torch.no_grad():
            image_features = self.model.get_image_features(inputs["pixel_values"])
            text_features = self.model.get_text_features(inputs["input_ids"], inputs["attention_mask"])

        # Calculate similarity
        similarity = (image_features @ text_features.T).squeeze(0)
        probs = F.softmax(similarity, dim=-1)

        # Return results
        results = {
            label: float(prob)
            for label, prob in zip(class_labels, probs)
        }
        results = dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

        return results

    def image_text_retrieval(
        self,
        query_image: Image.Image,
        candidate_texts: list,
        top_k: int = 5
    ) -> list:
        """
        Retrieve most relevant texts for given image.

        Args:
            query_image: Image to search with
            candidate_texts: List of candidate text descriptions
            top_k: Number of top results to return

        Returns:
            List of (text, score) tuples
        """
        # Encode image
        image_features = self.encode_image(query_image)

        # Encode all texts
        text_features_list = []
        for text in candidate_texts:
            features = self.encode_text(text)
            text_features_list.append(features)

        text_features = torch.cat(text_features_list, dim=0)

        # Calculate similarities
        similarities = F.cosine_similarity(image_features, text_features, dim=-1)

        # Get top-k
        top_indices = similarities.topk(min(top_k, len(candidate_texts))).indices

        results = [
            (candidate_texts[i], float(similarities[i]))
            for i in top_indices
        ]

        return results

    def text_image_retrieval(
        self,
        query_text: str,
        candidate_images: list,
        top_k: int = 5
    ) -> list:
        """
        Retrieve most relevant images for given text.

        Args:
            query_text: Text query
            candidate_images: List of PIL Images
            top_k: Number of top results to return

        Returns:
            List of (image_index, score) tuples
        """
        # Encode text
        text_features = self.encode_text(query_text)

        # Encode all images
        image_features_list = []
        for image in candidate_images:
            features = self.encode_image(image)
            image_features_list.append(features)

        image_features = torch.cat(image_features_list, dim=0)

        # Calculate similarities
        similarities = F.cosine_similarity(text_features, image_features, dim=-1)

        # Get top-k
        top_indices = similarities.topk(min(top_k, len(candidate_images))).indices

        results = [
            (int(i), float(similarities[i]))
            for i in top_indices
        ]

        return results

class MultiLabelClassifier:
    """
    Multi-label image classification using CLIP.
    Can detect multiple objects/concepts in a single image.
    """

    def __init__(self, clip_model: CLIPWrapper):
        self.clip = clip_model

    def classify(
        self,
        image: Image.Image,
        concepts: list,
        threshold: float = 0.2,
        template: str = "{}"
    ) -> dict:
        """
        Classify image with multiple possible labels.

        Args:
            image: PIL Image
            concepts: List of possible concepts/labels
            threshold: Minimum probability threshold
            template: Prompt template

        Returns:
            Dictionary of detected concepts with scores
        """
        # Format concepts
        text_inputs = [template.format(concept) for concept in concepts]

        # Process
        inputs = self.clip.processor(
            text=text_inputs,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.clip.device)

        with torch.no_grad():
            image_features = self.clip.model.get_image_features(**inputs)
            text_features = self.clip.model.get_text_features(
                inputs["input_ids"],
                inputs["attention_mask"]
            )

        # Calculate similarities
        similarities = (image_features @ text_features.T).squeeze(0)
        probs = F.softmax(similarities, dim=-1)

        # Filter by threshold
        results = {
            concept: float(prob)
            for concept, prob in zip(concepts, probs)
            if prob >= threshold
        }

        return dict(sorted(results.items(), key=lambda x: x[1], reverse=True))

# Demo usage
if __name__ == "__main__":
    import requests

    # Initialize CLIP
    clip = CLIPWrapper()

    # Demo 1: Zero-shot classification
    print("=== Zero-Shot Classification ===")
    url = "https://images.unsplash.com/photo-1474511320723-9a56873571b7"
    image = Image.open(requests.get(url, stream=True).raw)

    classes = ["cat", "dog", "bird", "car", "tree", "person", "beach"]
    results = clip.zero_shot_classification(image, classes)

    print("Classification results:")
    for label, prob in list(results.items())[:3]:
        print(f"  {label}: {prob:.3f}")

    # Demo 2: Multi-label classification
    print("\n=== Multi-Label Classification ===")
    detector = MultiLabelClassifier(clip)

    concepts = [
        "animal", "cat", "dog", "fur", "whiskers",
        "eyes", "ears", "nose", "outdoor", "indoor"
    ]
    results = detector.classify(image, concepts, threshold=0.15)

    print("Detected concepts:")
    for concept, score in list(results.items())[:5]:
        print(f"  {concept}: {score:.3f}")

    # Demo 3: Image-text retrieval
    print("\n=== Image-Text Retrieval ===")
    texts = [
        "A cute cat sitting on grass",
        "A dog playing in park",
        "A bird flying in sky",
        "A car on the road",
        "A person reading book"
    ]

    results = clip.image_text_retrieval(image, texts, top_k=2)
    print("Top matching texts:")
    for text, score in results:
        print(f"  [{score:.3f}] {text}")
```

### Step 2.1: Build Visual Q&A System

```python
# File: visual_qa.py
"""
Visual Question Answering with CLIP + LLM
==========================================

Combines CLIP's vision understanding with LLM's reasoning.
"""

import torch
from PIL import Image
import requests
from transformers import BlipProcessor, BlipForQuestionAnswering

class VisualQASystem:
    """
    Visual Question Answering system using BLIP model.
    """

    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = BlipProcessor.from_pretrained("Salesforce/blip-vqa-base")
        self.model = BlipForQuestionAnswering.from_pretrained("Salesforce/blip-vqa-base").to(self.device)
        self.model.eval()

    def answer_question(self, image: Image.Image, question: str) -> str:
        """
        Answer a question about the image.

        Args:
            image: PIL Image
            question: Question about the image

        Returns:
            Answer text
        """
        # Prepare inputs
        inputs = self.processor(image, question, return_tensors="pt").to(self.device)

        # Generate answer
        with torch.no_grad():
            outputs = self.model.generate(**inputs, max_length=20)

        # Decode answer
        answer = self.processor.decode(outputs[0], skip_special_tokens=True)
        return answer

    def batch_answer(
        self,
        image: Image.Image,
        questions: list
    ) -> dict:
        """Answer multiple questions about the same image"""
        answers = {}
        for question in questions:
            answers[question] = self.answer_question(image, question)
        return answers

# Demo
if __name__ == "__main__":
    vqa = VisualQASystem()

    # Load image
    url = "https://images.unsplash.com/photo-1474511320723-9a56873571b7"
    image = Image.open(requests.get(url, stream=True).raw)

    # Ask questions
    questions = [
        "What animal is in the image?",
        "What color is the animal?",
        "What is the animal doing?",
        "Where is the animal?",
        "How many animals are there?"
    ]

    print("Visual Q&A:")
    for question in questions:
        answer = vqa.answer_question(image, question)
        print(f"  Q: {question}")
        print(f"  A: {answer}\n")
```

**Checkpoint 2:** ✅ CLIP and Visual Q&A working

---

## 🤖 Part 3: Multi-Modal Agent (120 minutes)

### Building a Vision-Enabled Agent

Now we'll create an agent that can see, understand, and reason about visual content.

```python
# File: multimodal_agent.py
"""
Multi-Modal Agent with Vision Capabilities
===========================================

Agent that can:
- See and analyze images
- Answer questions about visual content
- Extract information from images
- Describe scenes and objects
"""

import torch
from PIL import Image
import base64
import io
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

@dataclass
class ImageInput:
    """Image input for the agent"""
    image: Image.Image
    metadata: Optional[Dict[str, Any]] = None

class VisionAgent:
    """
    Autonomous agent with vision capabilities.
    Combines CLIP, VQA, and LLM for visual understanding.
    """

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        vqa_model: str = "Salesforce/blip-vqa-base"
    ):
        from .clip_model import CLIPWrapper
        from .visual_qa import VisualQASystem

        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Initialize models
        self.clip = CLIPWrapper(model_name)
        self.vqa = VisualQASystem()

        # Agent state
        self.conversation_history = []
        self.image_memory = {}

    def see(self, image: Image.Image, name: str = None) -> str:
        """
        Process and remember an image.

        Args:
            image: PIL Image
            name: Optional name to remember the image

        Returns:
            Description of what was seen
        """
        # Generate image description
        description = self._describe_image(image)

        # Store in memory
        image_id = name or f"image_{len(self.image_memory)}"
        self.image_memory[image_id] = {
            "image": image,
            "description": description,
            "embeddings": self.clip.encode_image(image)
        }

        return f"I see: {description}"

    def _describe_image(self, image: Image.Image) -> str:
        """Generate a description of the image"""
        # Use VQA to gather information
        questions = [
            "What is in this image?",
            "What is the main subject?",
            "What is the background?",
            "What colors are present?"
        ]

        description_parts = []
        for question in questions:
            answer = self.vqa.answer_question(image, question)
            description_parts.append(answer)

        # Combine into description
        description = ". ".join(description_parts)
        return description

    def ask_about_image(
        self,
        question: str,
        image_name: str = None
    ) -> str:
        """
        Ask a question about a seen image.

        Args:
            question: Question about the image
            image_name: Name of image to ask about (if None, uses most recent)

        Returns:
            Answer to the question
        """
        # Get image
        if image_name is None:
            image_name = list(self.image_memory.keys())[-1]

        if image_name not in self.image_memory:
            return f"I don't remember an image named '{image_name}'"

        image_data = self.image_memory[image_name]
        image = image_data["image"]

        # Use VQA to answer
        answer = self.vqa.answer_question(image, question)

        # Add context from memory
        context = f" (from {image_name})"

        return answer + context

    def search_images(
        self,
        query: str,
        top_k: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Search memory for images matching query.

        Args:
            query: Text description to search for
            top_k: Number of results to return

        Returns:
            List of matching images with scores
        """
        if not self.image_memory:
            return []

        # Encode query
        query_embedding = self.clip.encode_text(query)

        # Calculate similarities
        results = []
        for image_id, data in self.image_memory.items():
            image_embedding = data["embeddings"]
            similarity = torch.cosine_similarity(
                query_embedding,
                image_embedding,
                dim=-1
            ).item()

            results.append({
                "name": image_id,
                "score": similarity,
                "description": data["description"]
            })

        # Sort and return top-k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def compare_images(
        self,
        image_name1: str,
        image_name2: str
    ) -> str:
        """
        Compare two seen images.

        Args:
            image_name1: First image name
            image_name2: Second image name

        Returns:
            Comparison description
        """
        if image_name1 not in self.image_memory:
            return f"I don't remember '{image_name1}'"
        if image_name2 not in self.image_memory:
            return f"I don't remember '{image_name2}'"

        data1 = self.image_memory[image_name1]
        data2 = self.image_memory[image_name2]

        # Calculate similarity
        similarity = torch.cosine_similarity(
            data1["embeddings"],
            data2["embeddings"],
            dim=-1
        ).item()

        # Generate comparison
        if similarity > 0.9:
            similarity_desc = "very similar"
        elif similarity > 0.7:
            similarity_desc = "somewhat similar"
        elif similarity > 0.5:
            similarity_desc = "different but related"
        else:
            similarity_desc = "very different"

        comparison = f"""
        Comparing {image_name1} and {image_name2}:
        - Similarity: {similarity:.2%} ({similarity_desc})
        - {image_name1}: {data1['description']}
        - {image_name2}: {data2['description']}
        """

        return comparison.strip()

    def chat(
        self,
        message: str,
        image: Image.Image = None
    ) -> str:
        """
        Interactive chat with the agent.

        Args:
            message: User message
            image: Optional image to show

        Returns:
            Agent response
        """
        # If image provided, process it first
        if image is not None:
            see_result = self.see(image)
            self.conversation_history.append(("system", see_result))

        # Analyze intent
        message_lower = message.lower()

        # Check for questions
        if "?" in message:
            # Extract image name if specified
            words = message.split()
            image_name = None
            for word in words:
                if word in self.image_memory:
                    image_name = word
                    break

            if image_name:
                return self.ask_about_image(message, image_name)
            elif self.image_memory:
                return self.ask_about_image(message)
            else:
                return "I haven't seen any images yet. Show me an image first!"

        # Check for search
        if any(word in message_lower for word in ["search", "find", "look for"]):
            query = message.replace("search", "").replace("find", "").replace("look for", "").strip()
            results = self.search_images(query)

            if not results:
                return "No matching images found in memory."

            response = f"Found {len(results)} matching image(s):\n"
            for i, result in enumerate(results, 1):
                response += f"{i}. {result['name']} (score: {result['score']:.2%})\n"
                response += f"   {result['description']}\n"
            return response.strip()

        # Check for comparison
        if "compare" in message_lower:
            words = message.split()
            image_names = [w for w in words if w in self.image_memory]
            if len(image_names) >= 2:
                return self.compare_images(image_names[0], image_names[1])
            else:
                return "Please specify two images to compare"

        # Default: general conversation
        return "I can help you analyze images. Try asking questions about images I've seen, searching for images, or comparing images!"

# Demo
if __name__ == "__main__":
    import requests

    # Create agent
    agent = VisionAgent()

    # Show images
    print("=== Showing Images ===")
    url1 = "https://images.unsplash.com/photo-1474511320723-9a56873571b7"
    image1 = Image.open(requests.get(url1, stream=True).raw)
    print(agent.see(image1, "cat"))

    url2 = "https://images.unsplash.com/photo-1583511655857-d19b40a7a54e"
    image2 = Image.open(requests.get(url2, stream=True).raw)
    print(agent.see(image2, "dog"))

    # Ask questions
    print("\n=== Asking Questions ===")
    print(agent.chat("What color is the cat?"))
    print(agent.chat("What is the dog doing?"))

    # Search
    print("\n=== Search ===")
    print(agent.chat("Search for animal"))

    # Compare
    print("\n=== Compare ===")
    print(agent.chat("Compare cat and dog"))
```

**Checkpoint 3:** ✅ Multi-modal agent working

---

## 🎬 Part 4: Video Analysis (90 minutes)

### Processing Videos with Multi-Modal AI

```python
# File: video_analysis.py
"""
Video Analysis with Multi-Modal AI
===================================

Extract insights from video content using:
- Frame sampling
- CLIP embeddings
- Temporal understanding
"""

import torch
from PIL import Image
import cv2
import numpy as np
from typing import List, Dict, Tuple
import tempfile
import os

class VideoAnalyzer:
    """
    Analyze video content using multi-modal AI.
    """

    def __init__(self):
        from .clip_model import CLIPWrapper

        self.clip = CLIPWrapper()
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def extract_frames(
        self,
        video_path: str,
        num_frames: int = 10,
        method: str = "uniform"
    ) -> List[Image.Image]:
        """
        Extract frames from video.

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            method: 'uniform', 'key', or 'first'

        Returns:
            List of PIL Images
        """
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        frames = []

        if method == "uniform":
            # Extract evenly distributed frames
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
        elif method == "first":
            # Extract first N frames
            frame_indices = range(min(num_frames, total_frames))
        else:  # key
            # Use scene detection (simplified: uniform sampling)
            frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                pil_image = Image.fromarray(frame_rgb)
                frames.append(pil_image)

        cap.release()
        return frames

    def analyze_video(
        self,
        video_path: str,
        actions: List[str] = None,
        scenes: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze video content.

        Args:
            video_path: Path to video
            actions: List of actions to detect
            scenes: List of scene types to detect

        Returns:
            Analysis results
        """
        if actions is None:
            actions = ["person walking", "person running", "car driving", "people talking"]
        if scenes is None:
            scenes = ["indoor", "outdoor", "street", "office", "home", "nature"]

        # Extract frames
        frames = self.extract_frames(video_path, num_frames=16)
        print(f"Extracted {len(frames)} frames")

        # Analyze each frame
        frame_analyses = []
        for i, frame in enumerate(frames):
            # Detect actions
            action_probs = self.clip.zero_shot_classification(frame, actions)
            top_action = max(action_probs, key=action_probs.get)

            # Detect scene
            scene_probs = self.clip.zero_shot_classification(frame, scenes)
            top_scene = max(scene_probs, key=scene_probs.get)

            frame_analyses.append({
                "frame": i,
                "action": top_action,
                "action_confidence": action_probs[top_action],
                "scene": top_scene,
                "scene_confidence": scene_probs[top_scene]
            })

        # Summarize video
        summary = self._summarize_video(frame_analyses, len(frames))

        return {
            "summary": summary,
            "frames": frame_analyses
        }

    def _summarize_video(self, frame_analyses: List[Dict], total_frames: int) -> str:
        """Generate text summary of video"""
        # Most common actions
        actions = [f["action"] for f in frame_analyses]
        from collections import Counter
        action_counts = Counter(actions)

        # Most common scenes
        scenes = [f["scene"] for f in frame_analyses]
        scene_counts = Counter(scenes)

        summary = f"""
        Video Summary:
        - Total frames analyzed: {total_frames}
        - Primary action: {action_counts.most_common(1)[0][0]}
        - Primary scene: {scene_counts.most_common(1)[0][0]}

        Action distribution:
        """

        for action, count in action_counts.most_common(3):
            summary += f"  - {action}: {count/total_frames:.1%}\n"

        summary += "\nScene distribution:\n"
        for scene, count in scene_counts.most_common(3):
            summary += f"  - {scene}: {count/total_frames:.1%}\n"

        return summary.strip()

    def generate_video_caption(
        self,
        video_path: str,
        max_frames: int = 8
    ) -> str:
        """
        Generate a caption for the video.

        Args:
            video_path: Path to video
            max_frames: Maximum frames to analyze

        Returns:
            Video caption
        """
        # Extract frames
        frames = self.extract_frames(video_path, num_frames=max_frames)

        # Generate descriptions for each frame
        from .visual_qa import VisualQASystem
        vqa = VisualQASystem()

        descriptions = []
        for i, frame in enumerate(frames):
            desc = vqa.answer_question(frame, "What is happening in this image?")
            descriptions.append(desc)

        # Combine into coherent caption
        if len(descriptions) == 1:
            return descriptions[0]

        # Simple concatenation (could use LLM to refine)
        caption = " ".join(descriptions)
        return caption

    def search_video(
        self,
        video_path: str,
        query: str,
        top_k: int = 3
    ) -> List[Dict]:
        """
        Search for frames matching text query in video.

        Args:
            video_path: Path to video
            query: Text query
            top_k: Number of results

        Returns:
            Matching frames with scores
        """
        # Extract frames
        frames = self.extract_frames(video_path, num_frames=30)

        # Search with CLIP
        results = []
        for i, frame in enumerate(frames):
            # Encode frame
            frame_embedding = self.clip.encode_image(frame)

            # Encode query
            query_embedding = self.clip.encode_text(query)

            # Calculate similarity
            similarity = torch.cosine_similarity(
                frame_embedding,
                query_embedding,
                dim=-1
            ).item()

            results.append({
                "frame": i,
                "similarity": similarity,
                "image": frame
            })

        # Sort and return top-k
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

# Demo
if __name__ == "__main__":
    analyzer = VideoAnalyzer()

    # Note: Replace with actual video path
    # results = analyzer.analyze_video("sample.mp4")
    # print(results["summary"])

    print("Video analyzer ready. Provide a video file to analyze.")
```

**Checkpoint 4:** ✅ Video analysis working

---

## 🐳 Part 5: Production Deployment (90 minutes)

### Dockerizing Multi-Modal System

```dockerfile
# File: Dockerfile.multimodal
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-multimodal.txt .
RUN pip install --no-cache-dir -r requirements-multimodal.txt

# Copy application
COPY multimodal_api.py .
COPY models/ ./models/

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["uvicorn", "multimodal_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

```python
# File: multimodal_api.py
"""
Production Multi-Modal API
===========================
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from PIL import Image
import io
import torch

from multimodal_agent import VisionAgent

app = FastAPI(title="Multi-Modal AI API")

# Initialize agent
agent = VisionAgent()

class QuestionRequest(BaseModel):
    question: str
    image_name: str = None

class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/see")
async def see_image(file: UploadFile = File(...), name: str = None):
    """Process and remember an image"""
    try:
        # Read image
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))

        # Process with agent
        result = agent.see(image, name)

        return {
            "status": "success",
            "result": result,
            "image_name": name or f"image_{len(agent.image_memory)}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
async def ask_question(request: QuestionRequest):
    """Ask a question about a seen image"""
    try:
        answer = agent.ask_about_image(request.question, request.image_name)
        return {
            "status": "success",
            "answer": answer
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_images(request: SearchRequest):
    """Search for images in memory"""
    try:
        results = agent.search_images(request.query, request.top_k)
        return {
            "status": "success",
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/images")
async def list_images():
    """List all seen images"""
    return {
        "images": list(agent.image_memory.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```yaml
# File: docker-compose.multimodal.yml
version: '3.8'

services:
  multimodal-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    volumes:
      - ./models:/models
    restart: unless-stopped
```

**Checkpoint 5:** ✅ Production deployment ready

---

## ✅ Lab Completion Checklist

- [ ] Part 1: Vision Transformer implementation
- [ ] Part 2: CLIP zero-shot classification
- [ ] Part 3: Visual Q&A system
- [ ] Part 4: Multi-modal agent
- [ ] Part 5: Video analysis
- [ ] Part 6: Production API deployment

---

## 🎓 Summary

In this lab, you learned:

1. **Vision Transformers** - How transformers work for images
2. **CLIP** - Zero-shot image classification and retrieval
3. **Visual Q&A** - Answering questions about images
4. **Multi-Modal Agents** - Agents that can see and reason
5. **Video Analysis** - Extracting insights from videos
6. **Production Deployment** - Dockerizing multi-modal systems

---

## 🚀 Next Steps

1. **LAB-012: Audio AI** - Add speech capabilities
2. **LAB-013: Advanced Function Calling** - Enhance agent tools
3. Build a complete multi-modal assistant

---

**Last Updated:** 2026-02-04
**Lab:** 011 - Multi-Modal AI
**Time Estimate:** 6-8 hours
**Difficulty:** ⭐⭐⭐⭐ Expert
