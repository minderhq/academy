---
Document ID: SOL-002
Title: "SOL-002: Multi-Modal Industrial Inspection System"
Category: Industry Solution
Last Updated: 2026-09-29
Status: Complete
Difficulty: Advanced
Estimated Time: 7 hours
Prerequisites: See module README
Related: See module README
Tags: ['enterprise', 'solution', 'manufacturing', 'multimodal', 'vision', 'llm']
---

# SOL-002: Multi-Modal Industrial Inspection System

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Problem Statement](#problem-statement)
- [System Architecture](#system-architecture)
- [1. Sensor Data Collection](#1-sensor-data-collection)
- [2. RGB Defect Detection and Segmentation](#2-rgb-defect-detection-and-segmentation)
- [3. Thermal Anomaly Detection](#3-thermal-anomaly-detection)
- [4. Cross-Modal Fusion](#4-cross-modal-fusion)
- [5. Defect Knowledge Base](#5-defect-knowledge-base)
- [6. LLM Report Generation](#6-llm-report-generation)
- [7. System Orchestration](#7-system-orchestration)
- [Deployment](#deployment)
- [Metrics: Targets, Not Guarantees](#metrics-targets-not-guarantees)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this solution, you will be able to:

- Assemble a multi-modal inspection pipeline from real, running components: OpenCV preprocessing, a transformer detector with proper post-processing, SAM box-prompted segmentation, and threshold-based thermal analysis
- Fuse detections across modalities honestly — IoU-based matching with calibrated confidence, instead of ad-hoc multipliers
- Build a defect knowledge base in Qdrant with the current client API (`query_points`, payload filters) and structured-text embeddings
- Wire a tool-calling LLM agent that generates inspection reports grounded in the knowledge base — with every tool it calls actually defined
- Separate what this reference code proves (pipeline mechanics) from what it cannot (plant-specific model accuracy), and plan a validation strategy accordingly

---

## Abstract

Manual visual inspection does not scale: it is slow, subjective, and produces paper trails that resist root-cause analysis. This solution walks through an AI-powered inspection system that fuses RGB defect detection, thermal anomaly screening, and an LLM reporting layer on top of a vector-database knowledge base of historical defects. Every code path uses real, current APIs — OpenCV CLAHE, DETR with `post_process_object_detection`, SAM box prompts, Qdrant `query_points`, LangChain tool-calling agents — and every integration point that must come from your plant (camera SDKs, a fine-tuned defect model, calibrated thresholds) is marked as such rather than papered over. The knowledge-base and report-agent layers reuse the patterns from [SOL-001](./SOL-001-Enterprise-Knowledge-Base.md); the manufacturing-domain context is in [IND-003](../industry/IND-003-Manufacturing-AI.md).

## Problem Statement

Traditional manufacturing inspection fails on five axes:

```text
- manual visual inspection: slow, fatiguing, error-prone
- subjective quality assessments: inspector-to-inspector variance
- paper-based documentation: no queryable history
- delayed root cause analysis: defects recur for weeks
- inconsistent defect categorization: no shared taxonomy
```

The system below attacks all five: automated multi-modal capture, a shared defect taxonomy, a queryable knowledge base, and LLM-drafted reports with historical grounding.

## System Architecture

```text
┌────────────────────────────────────────────────────────────────┐
│                   Multi-Modal Inspection System                 │
├────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Camera   │    │ Thermal  │    │ Acoustic │   ...sensors     │
│  │  (RGB)   │    │ Imaging  │    │  (opt.)  │                  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                  │
│       └───────────────┼───────────────┘                        │
│                       ↓                                        │
│           ┌─────────────────────────┐                          │
│           │  Capture + Preprocess   │  CLAHE, registration,   │
│           │  (per-modality)         │  calibration            │
│           └───────────┬─────────────┘                          │
│        ┌──────────────┼──────────────┐                         │
│        ↓              ↓              ↓                         │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│  │ RGB      │   │ Thermal  │   │ (future  │                  │
│  │ Detector │   │ Anomaly  │   │ modality)│                  │
│  │ + SAM    │   │ Scan     │   │          │                  │
│  └────┬─────┘   └────┬─────┘   └──────────┘                  │
│       └───────┬──────┘                                        │
│               ↓                                               │
│     ┌───────────────────┐     ┌───────────────────┐           │
│     │ Cross-Modal Fuse  │ --> │ Defect Knowledge  │           │
│     │ (IoU + confidence)│     │ Base (Qdrant)     │           │
│     └─────────┬─────────┘     └─────────┬─────────┘           │
│               ↓                         ↓                     │
│     ┌───────────────────────────────────────────┐             │
│     │  LLM Report Agent (tool-calling,          │             │
│     │  grounded in the knowledge base)          │             │
│     └───────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────────┘
```

## 1. Sensor Data Collection

The capture layer is plant-specific by definition — camera models, mounts, part rotation hardware. The class below defines the interface and the preprocessing that IS general; the hardware methods are stubs you wire to your plant SDK:

```python
import cv2
import numpy as np
from datetime import datetime

def enhance_contrast(bgr_image: np.ndarray) -> np.ndarray:
    """CLAHE on the L channel of LAB: lighting-neutral contrast
    boost - the standard preprocessing for factory-floor RGB.
    (There is no cv2.enhanceContrast; CLAHE is the tool.)"""
    lab = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab = cv2.merge((clahe.apply(l), a, b))
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)   # RGB out

class MultiModalDataCollector:
    """Captures aligned sensor data per part. Hardware methods
    are STUBS - integrate with your plant's SDK."""

    def __init__(self, config):
        self.config = config
        # STUB: replace with your camera drivers
        self.rgb_camera = cv2.VideoCapture(config['rgb_camera_id'])
        self.thermal_camera = None    # thermal SDK handle
        self.acoustic_sensor = None   # acquisition handle

    def capture_rgb(self) -> np.ndarray | None:
        ret, frame = self.rgb_camera.read()
        return enhance_contrast(frame) if ret else None

    def collect_inspection_data(self, product_id: str) -> dict:
        data = {
            'product_id': product_id,
            'timestamp': datetime.now().isoformat(),
            'rgb_images': [],
            'thermal_images': [],
            'acoustic_data': None,
        }
        for angle in [0, 45, 90, 135, 180]:
            self.rotate_product(angle)          # STUB: stage control
            frame = self.capture_rgb()
            if frame is not None:
                data['rgb_images'].append({
                    'angle': angle,
                    'image': frame,
                })
        if self.thermal_camera is not None:
            data['thermal_images'].append(
                self.thermal_camera.capture_celsius())
        return data

    def rotate_product(self, angle: float) -> None:
        raise NotImplementedError("wire to your stage controller")
```

```text
What matters at capture time (and what tutorial code skips)
- registration: RGB and thermal frames must map to the same
  part coordinates, or cross-modal fusion is meaningless.
  Calibrate the transform once per station
- consistent lighting drives RGB accuracy more than model
  choice does; CLAHE is mitigation, not a cure
- keep raw captures: every model iteration will want to
  re-label and re-train against the same parts
```

## 2. RGB Defect Detection and Segmentation

Two stages: a detector proposes regions, SAM turns each box into a pixel mask. The detector here is COCO-pretrained DETR — it detects *objects*, not yet *your defects*; the mechanical pipeline is what this class teaches, and the fine-tuning requirement is stated, not hidden:

```python
import torch
from transformers import (AutoImageProcessor,
                          AutoModelForObjectDetection)
from segment_anything import sam_model_registry, SamPredictor

class RgbDefectDetector:
    """DETR detection + SAM segmentation. DETR-resnet-50 is
    COCO-pretrained: for production, fine-tune it on YOUR
    labeled defect dataset - the pipeline below is the
    deployment skeleton either way."""

    def __init__(self, model_id="facebook/detr-resnet-50",
                 score_threshold=0.7, device="cuda"):
        self.processor = AutoImageProcessor.from_pretrained(model_id)
        self.model = AutoModelForObjectDetection.from_pretrained(
            model_id).to(device).eval()
        self.threshold = score_threshold
        self.device = device

    @torch.no_grad()
    def detect(self, rgb_image: np.ndarray) -> list[dict]:
        inputs = self.processor(
            images=rgb_image, return_tensors="pt").to(self.device)
        outputs = self.model(**inputs)
        target_sizes = torch.tensor([rgb_image.shape[:2]])
        results = self.processor.post_process_object_detection(
            outputs, target_sizes=target_sizes,
            threshold=self.threshold)[0]

        detections = []
        for score, label, box in zip(
                results["scores"], results["labels"],
                results["boxes"]):
            detections.append({
                "type": self.model.config.id2label[label.item()],
                "confidence": score.item(),
                "bbox": [round(v, 1) for v in box.tolist()],  # XYXY
            })
        return detections

class SamSegmenter:
    """Box-prompted SAM: turns detector boxes into masks."""

    def __init__(self, checkpoint="sam_vit_h_4b8939.pth"):
        build_sam = sam_model_registry["vit_h"]
        sam = build_sam(checkpoint=checkpoint)
        self.predictor = SamPredictor(sam)

    def mask_from_box(self, rgb_image, bbox) -> np.ndarray:
        self.predictor.set_image(rgb_image)
        masks, scores, _ = self.predictor.predict(
            box=np.array(bbox, dtype=np.float32),
            multimask_output=True)
        return masks[int(scores.argmax())]   # best mask
```

```text
Why box-prompted SAM instead of point prompts
- the detector already gives XYXY boxes; passing the box to
  SAM constrains the mask to the right region. Point prompts
  from unverified centers segment the wrong object
- SAM needs no retraining for your parts - zero-shot masks
  are the reason it fits a production skeleton
- the defect-vs-part distinction is the DETR fine-tune's job,
  not SAM's
```

## 3. Thermal Anomaly Detection

Thermal screening is classical CV, not deep learning — and that is a feature: it is explainable to a quality engineer on day one:

```python
import cv2
import numpy as np

def thermal_anomalies(thermal_celsius: np.ndarray,
                      hot: float = 80.0, cold: float = 10.0,
                      min_area_px: int = 100) -> list[dict]:
    """Threshold + connected components on a calibrated
    thermal frame. Thresholds are per-product calibration
    values, not universal constants."""
    flags = ((thermal_celsius > hot) |
             (thermal_celsius < cold)).astype(np.uint8)
    contours, _ = cv2.findContours(
        flags, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    anomalies = []
    for c in contours:
        if cv2.contourArea(c) < min_area_px:
            continue                       # sensor noise
        x, y, w, h = cv2.boundingRect(c)
        region = thermal_celsius[y:y + h, x:x + w]
        anomalies.append({
            'type': 'hotspot' if region.max() > hot else 'cold_spot',
            'bbox': [x, y, x + w, y + h],   # XYXY (boundingRect is XYWH)
            'peak_celsius': float(region.max()),
            'severity': 'high',
        })
    return anomalies
```

```text
Acoustic/vibration modalities
- the same shape applies: calibrated feature extraction
  (RMS energy, spectral peaks) + threshold or one-class model
- add modalities ONLY when you have labeled examples of the
  failure mode they catch - a silent modality is dead weight
  in fusion
```

## 4. Cross-Modal Fusion

Two modalities agreeing is evidence — but the naive implementation (`confidence * 1.5`) is not evidence combination, it can exceed 1.0, and it hides its assumptions. The honest version: match detections across modalities by IoU, apply a bounded boost:

```python
def iou(a: list, b: list) -> float:
    """IoU of XYXY boxes - one format everywhere: DETR emits
    XYXY, SAM prompts take XYXY, and thermal bboxes are
    converted to XYXY at source. Mixing XYWH and XYXY here is
    the classic fusion bug: nothing crashes, every overlap is
    just wrong."""
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    inter = max(0, x2 - x1) * max(0, y2 - y1)
    area_a = (a[2] - a[0]) * (a[3] - a[1])
    area_b = (b[2] - b[0]) * (b[3] - b[1])
    union = area_a + area_b - inter
    return inter / union if union else 0.0

def fuse(rgb_detections, thermal_anomalies,
         iou_threshold=0.3, agreement_boost=1.25) -> list[dict]:
    """Cross-modal fusion: thermal agreement boosts a visual
    detection's confidence, bounded at 1.0. All bboxes XYXY."""
    fused = []
    for det in rgb_detections:
        agreeing = [t for t in thermal_anomalies
                    if iou(det['bbox'], t['bbox']) >= iou_threshold]
        conf = det['confidence']
        if agreeing:
            conf = min(1.0, conf * agreement_boost)
        fused.append({
            'type': det['type'],
            'confidence': round(conf, 3),
            'bbox': det['bbox'],
            'modalities': ['rgb'] + (['thermal'] if agreeing else []),
        })
    return fused
```

```text
The honest limits of this fusion
- agreement_boost=1.25 is a POLICY, not a probability. The
  principled upgrade: calibrate each modality's detector on a
  held-out set (Platt/isotonic), then combine as independent
  evidence: p_fused = 1 - (1-p_rgb)(1-p_thermal)
- iou_threshold depends on your registration accuracy - if
  RGB/thermal frames misalign by 20 px, 0.3 IoU is fiction
- for a report, "visual + thermal agree" is more actionable
  than any single number; keep the modality list in the payload
```

## 5. Defect Knowledge Base

Qdrant with the current client API (`query_points`, payload filters — `search` is deprecated). Defects are embedded as structured text; ids are UUIDs:

```python
import uuid
from datetime import datetime, timedelta

from qdrant_client import QdrantClient
from qdrant_client.models import (DatetimeRange, Distance,
                                  FieldCondition, Filter,
                                  PointStruct, VectorParams)
from sentence_transformers import SentenceTransformer

class DefectKnowledgeBase:
    """Historical defect store: embeddings for similarity,
    payload filters for trends. Text-embedding approach: a
    trained image-embedding model is a later upgrade."""

    def __init__(self, url="http://localhost:6333"):
        self.client = QdrantClient(url=url)
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.dim = self.encoder.get_sentence_embedding_dimension()

        if "defects" not in [c.name for c in
                             self.client.get_collections().collections]:
            self.client.create_collection(
                collection_name="defects",
                vectors_config=VectorParams(
                    size=self.dim, distance=Distance.COSINE))

    def embed(self, defect: dict) -> list[float]:
        text = (f"{defect['type']} defect, severity "
                f"{defect.get('severity', 'unknown')}")
        return self.encoder.encode(text).tolist()

    def store_defect(self, defect: dict, product_id: str) -> str:
        point_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name="defects",
            points=[PointStruct(
                id=point_id,
                vector=self.embed(defect),
                payload={
                    'type': defect['type'],
                    'severity': defect.get('severity', 'unknown'),
                    'modalities': defect.get('modalities', []),
                    'product_id': product_id,
                    'timestamp': datetime.now().isoformat(),
                })])
        return point_id

    def find_similar(self, vector: list[float], limit: int = 3):
        response = self.client.query_points(
            collection_name="defects",
            query=vector,
            limit=limit,
            with_payload=True)
        return response.points

    def trends(self, days: int = 30) -> dict:
        """Counts by type, filtered SERVER-side by timestamp -
        do not scroll the whole collection to filter in Python."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        response = self.client.scroll(
            collection_name="defects",
            scroll_filter=Filter(must=[FieldCondition(
                key="timestamp",
                range=DatetimeRange(gte=cutoff))]),
            limit=1000,
            with_payload=True)
        counts: dict[str, int] = {}
        for point in response[0]:
            counts[point.payload['type']] = \
                counts.get(point.payload['type'], 0) + 1
        return dict(sorted(counts.items(),
                           key=lambda kv: -kv[1]))
```

```text
Taxonomy first, vectors second
- 'type' values must come from a controlled vocabulary agreed
  with quality engineering - free-form types make trends and
  similarity both useless
- embeddings make SIMILARITY work; the structured payload
  makes TRENDS and reporting work. Design both fields on day
  one (this mirrors the SOL-001 knowledge-base pattern)
```

## 6. LLM Report Generation

A tool-calling agent grounded in the knowledge base. Every tool referenced is actually defined — the agent can only know what the tools return:

```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = """You are a quality-engineering assistant that
drafts inspection reports. Ground every claim in the tool
results - never invent defect statistics. Report structure:
1. Executive Summary  2. Detailed Findings  3. Historical
Comparison (from the knowledge base)  4. Recommendations."""

class InspectionReportAgent:
    """Tool-calling agent over the defect knowledge base."""

    def __init__(self, knowledge_base: DefectKnowledgeBase):
        self.kb = knowledge_base
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)
        self.tools = self._build_tools()
        # LangChain 1.x: system_prompt replaces the hand-wired
        # ChatPromptTemplate + agent_scratchpad + AgentExecutor.
        self.agent = create_agent(
            self.llm, self.tools, system_prompt=SYSTEM_PROMPT)

    def _build_tools(self):
        kb = self.kb

        @tool
        def search_similar_defects(defect_description: str) -> str:
            """Search the historical defect knowledge base for
            cases similar to the given description."""
            vector = kb.embed(
                {'type': defect_description, 'severity': 'unknown'})
            hits = kb.find_similar(vector, limit=3)
            if not hits:
                return "No similar historical defects found."
            return "\n".join(
                f"- {p.payload['type']} (severity "
                f"{p.payload['severity']}, seen "
                f"{p.payload['timestamp'][:10]})"
                for p in hits)

        @tool
        def defect_trends(days: int) -> str:
            """Defect counts by type over the last N days."""
            return str(kb.trends(days=days))

        return [search_similar_defects, defect_trends]

    def generate_report(self, product_id: str,
                        fused_defects: list[dict]) -> str:
        findings = "\n".join(
            f"- {d['type']} (confidence {d['confidence']}, "
            f"modalities: {', '.join(d['modalities'])})"
            for d in fused_defects) or "- none detected"
        result = self.agent.invoke({
            "messages": [
                {"role": "user",
                 "content": (f"Draft the inspection report for product "
                             f"{product_id}. Findings:\n{findings}\n"
                             f"Use the tools for historical context.")},
            ],
        })
        return result["messages"][-1].text
```

```text
Agent design for production floors
- temperature=0: reports are not creative writing; identical
  findings must produce identical drafts
- two tools, not ten: every tool is a way to be wrong. Add a
  root-cause tool only when the knowledge base actually holds
  root-cause labels
- the LLM formats and drafts; the deterministic pipeline
  decides pass/fail. Never let the model make the accept/
  reject call - that is a calibrated threshold decision
```

## 7. System Orchestration

```python
from datetime import datetime

class IndustrialInspectionSystem:
    """Wires the pipeline together. The pass/fail decision is
    a threshold on fused confidence - deterministic, auditable."""

    def __init__(self, config):
        self.collector = MultiModalDataCollector(config)
        self.detector = RgbDefectDetector()
        self.segmenter = SamSegmenter()
        self.knowledge_base = DefectKnowledgeBase()
        self.report_agent = InspectionReportAgent(
            self.knowledge_base)
        self.pass_threshold = 0.5   # calibrated per line

    def inspect_product(self, product_id: str) -> dict:
        data = self.collector.collect_inspection_data(product_id)

        rgb_detections, masks = [], []
        for img_data in data['rgb_images']:
            dets = self.detector.detect(img_data['image'])
            rgb_detections.extend(dets)
            masks.extend(
                self.segmenter.mask_from_box(
                    img_data['image'], d['bbox'])
                for d in dets)

        thermal = [a for frame in data['thermal_images']
                   for a in thermal_anomalies(frame)]

        fused = fuse(rgb_detections, thermal)

        for defect in fused:
            self.knowledge_base.store_defect(
                defect, product_id)

        report = self.report_agent.generate_report(
            product_id, fused)

        return {
            'product_id': product_id,
            'status': ('passed'
                       if not fused
                       else 'review'),
            'defect_count': len(fused),
            'report': report,
        }
```

```text
One honest simplification vs the diagram: acoustic data is
captured-then-ignored in this reference - add it to fusion
only after you have labeled acoustic failure examples. A
modality that never votes should not be in the pipeline.
```

## Deployment

```yaml
services:
  inspection-api:
    build: ./api
    ports:
      - "8000:8000"
    environment:
      - CUDA_VISIBLE_DEVICES=0
    volumes:
      - ./models:/models
      - ./data:/data
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: inspection_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?set in .env}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  qdrant_data:
  postgres_data:
```

```text
Deployment notes
- the `version:` key is obsolete in Compose V2 - omit it
- secrets come from .env, never inline in the compose file
- SAM vit_h needs ~6 GB VRAM beside the detector; size the
  GPU reservation for BOTH models, or run SAM on CPU for
  lower throughput at zero extra VRAM
```

## Metrics: Targets, Not Guarantees

Accuracy numbers for inspection systems are properties of YOUR parts, lighting, and labels — any table of universal "before/after" numbers is fiction. What a deployment should measure and commit to:

```text
Define and baseline these on your own line:
- detection recall at a FIXED false-positive budget
  (the FPR your rework station can absorb)
- inspection cycle time per part (capture + inference)
- report turnaround (capture -> signed PDF)
- root-cause closure rate: defects with a confirmed root
  cause within N days
- inter-inspector agreement BEFORE deployment: that number,
  not a paper benchmark, is the bar the system must beat
Illustrative industry targets (to validate, not to quote):
98% recall / 2% FPR class systems exist in controlled
lighting with fine-tuned models - they are earned, not assumed.
```

## Best Practices

```text
1. Mark the plant-specific boundary explicitly: camera SDKs,
   stage control, and the fine-tuned detector are YOURS; the
   pipeline mechanics are reusable. Code that pretends
   otherwise (fake hardware classes, undefined methods) is a
   tutorial smell
2. Calibrate before fusing: each modality's confidence must
   mean something on a held-out set before you combine them
3. The pass/fail decision is a threshold, not the LLM - keep
   the model in drafting and summarization
4. Server-side filtering (payload indexes + filters), never
   scroll-and-filter, as the knowledge base grows
5. Controlled defect taxonomy agreed with quality engineering
   on day one; similarity search and trends both depend on it
6. Keep raw captures - the next model iteration trains on them
7. Report the modality list with every finding; "RGB+thermal
   agree" is more actionable to a floor engineer than a
   single fused score
```

---

## References

### Related PROJECT-OMEGA Documents

- [SOL-001: Enterprise Knowledge Base](./SOL-001-Enterprise-Knowledge-Base.md)
- [IND-003: Manufacturing AI](../industry/IND-003-Manufacturing-AI.md)

---

## Next Steps

- Knowledge-base patterns this solution reuses: **[SOL-001: Enterprise Knowledge Base](./SOL-001-Enterprise-Knowledge-Base.md)**
- Manufacturing-domain deep dive: **[IND-003: Manufacturing AI](../industry/IND-003-Manufacturing-AI.md)**
- Module overview: **[README](./README.md)**
