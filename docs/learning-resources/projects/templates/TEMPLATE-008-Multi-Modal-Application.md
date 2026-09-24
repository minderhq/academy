# PROJECT TEMPLATE: Multi-Modal Application

Build applications with vision + language models.

## Project Structure

```text
multimodal-app/
├── README.md
├── requirements.txt
├── config/
│   ├── models_config.yaml
│   └── app_config.yaml
├── src/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── clip.py          # CLIP model
│   │   ├── blip.py          # Image captioning
│   │   ├── llava.py         # LLaVA model
│   │   └── whisper.py       # Speech-to-text
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── image.py         # Image processing
│   │   ├── audio.py         # Audio processing
│   │   └── video.py         # Video processing
│   ├── embeddings/
│   │   ├── __init__.py
│   │   ├── image_embedder.py
│   │   └── text_embedder.py
│   ├── retrieval/
│   │   ├── __init__.py
│   │   └── image_search.py
│   ├── generation/
│   │   ├── __init__.py
│   │   ├── captioning.py
│   │   └── vqa.py           # Visual Q&A
│   └── api.py               # FastAPI endpoints
├── data/
│   ├── images/
│   ├── audio/
│   └── videos/
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── styles.css
└── tests/
    └── test_multimodal.py
```

## Features

- Image-text retrieval
- Image captioning
- Visual question answering
- Speech recognition
- Cross-modal search

## Quick Start

### Image-Text Retrieval

```python
from src.models.clip import CLIPModel
from src.retrieval.image_search import ImageSearch

model = CLIPModel("openai/clip-vit-base-patch32")
search = ImageSearch(model, image_database="data/images")

# Text to image
results = search.search("a dog playing in the park", top_k=5)

# Image to text
results = search.search_by_image("query_image.jpg", top_k=5)
```

### Image Captioning

```python
from src.models.blip import BLIPCaptioner

captioner = BLIPCaptioner("Salesforce/blip-image-captioning-base")
caption = captioner.generate("image.jpg")
print(f"Caption: {caption}")
```

### Visual Q&A

```python
from src.models.llava import LLaVAModel

vqa = LLaVAModel("llava-hf/llava-1.5-7b-hf")

answer = vqa.answer(
    image="image.jpg",
    question="What color is the cat?"
)
print(f"Answer: {answer}")
```

### Speech Recognition

```python
from src.models.whisper import WhisperModel

whisper = WhisperModel("openai/whisper-base")

text = whisper.transcribe("audio.wav")
print(f"Transcript: {text}")
```

## API Endpoints

```bash
# Image captioning
curl -X POST "http://localhost:8000/caption" \
  -F "image=@image.jpg"

# Visual Q&A
curl -X POST "http://localhost:8000/vqa" \
  -F "image=@image.jpg" \
  -F "question=What is in this image?"

# Image search
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "sunset on the beach"}'
```

## Processing Pipeline

```python
from src.processors.image import ImageProcessor
from src.processors.audio import AudioProcessor

# Image preprocessing
img_processor = ImageProcessor()
processed = img_processor.preprocess(
    "image.jpg",
    resize=(224, 224),
    normalize=True
)

# Audio preprocessing
audio_processor = AudioProcessor()
processed = audio_processor.preprocess(
    "audio.wav",
    sample_rate=16000,
    duration=30
)
```

## Multi-Modal RAG

```python
from src.generation.multimodal_rag import MultiModalRAG

rag = MultiModalRAG(
    image_encoder="clip",
    text_encoder="sentence-transformer",
    generator="llava"
)

response = rag.query(
    text_query="show me animals",
    image_database="data/animals/"
)
```

---

**Difficulty:** Advanced
**Estimated Time:** 10-15 hours
**Skills:** Multi-modal models, Computer vision, Audio processing
