---
Document ID: IND-003
Title: "IND-003: Manufacturing AI Applications"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['industry', 'manufacturing', 'llm']
---

# IND-003: Manufacturing AI Applications

## Table of Contents

- [Overview](#overview)
- [The Manufacturing AI Landscape](#the-manufacturing-ai-landscape)
- [1. Predictive Maintenance](#1-predictive-maintenance)
- [2. Computer Vision Quality Control](#2-computer-vision-quality-control)
- [3. Production Scheduling with RL](#3-production-scheduling-with-rl)
- [4. Supply Chain RAG Agent](#4-supply-chain-rag-agent)
- [5. Digital Twin Monitoring](#5-digital-twin-monitoring)
- [End-to-End Orchestration](#end-to-end-orchestration)
- [Key Technologies](#key-technologies)
- [Best Practices](#best-practices)
- [References](#references)

---

## Overview

Manufacturing is the industry where AI pays back fastest — the data is machine-generated (no consent issues), the failure modes are physical and repeatable, and the cost of a miss is measured in scrap and downtime rather than lawsuits. This survey walks the four application families that dominate real deployments: predictive maintenance on windowed sensor signals, computer-vision quality control, scheduling/optimization, and LLM-assisted decision support over historical episodes, plus the digital-twin pattern that ties monitoring together. Each section is a runnable skeleton with its provenance stated honestly — which model detects what, which thresholds are policy, and which parts must come from your plant. The multi-modal inspection pipeline this survey summarizes is built out in full in [SOL-002](../enterprise-solutions/SOL-002-Industry-Solution.md); the RAG and agent foundations live in [6100: Vector Databases](../phases/phase6-rag/6100-vector/README.md) and [7100: Agent Architecture](../phases/phase7-agentic/7100-architecture/README.md).

## The Manufacturing AI Landscape

```text
Where the wins actually are (in order of typical ROI)

1. Predictive maintenance    sensor time-series -> failure risk
                             - the most mature family; labeled
                               failure history is the bottleneck
2. Vision quality control    camera frames -> defect detection
                             - biggest labor saving; the model
                               is the easy part, the labeling
                               and lighting are the project
3. Scheduling/optimization   orders + machine state -> schedules
                             - solvers (CP-SAT) usually beat RL
                               here; see section 3 for when RL
                               is actually justified
4. LLM decision support      logs + episodes -> reports, advice
                             - newest family; the LLM drafts and
                               summarizes, deterministic systems
                               keep the accept/reject decisions

Cross-cutting truth: every family is gated by DATA ENGINEERING
(labeled history, calibrated sensors, controlled taxonomies),
not by model choice. Plan accordingly.
```

---

## 1. Predictive Maintenance

Failure classification over windowed sensor signals. Three details decide whether this works: feature extraction on the right time scale, the scaler fitted on TRAINING data only (refitting on prediction data is silent data leakage), and class weighting — failures are rare by definition:

```python
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

class PredictiveMaintenance:
    """Failure classifier over windowed sensor signals.
    Rows = fixed-length windows (e.g. 10 s of vibration)."""

    def __init__(self, sample_rate=1000):
        self.model = RandomForestClassifier(
            n_estimators=200, class_weight="balanced")
        self.scaler = StandardScaler()
        self.fs = sample_rate

    def _window_features(self, vib: np.ndarray,
                         temperature: float) -> dict:
        spectrum = np.abs(np.fft.rfft(vib))
        freqs = np.fft.rfftfreq(len(vib), d=1.0 / self.fs)
        return {
            'vibration_rms': float(np.sqrt(np.mean(vib ** 2))),
            'vibration_peak': float(np.max(np.abs(vib))),
            'dominant_freq': float(freqs[spectrum.argmax()]),
            'spectral_energy': float(np.sum(spectrum)),
            'temperature': temperature,
        }

    def build_features(self, windows: pd.DataFrame) -> pd.DataFrame:
        rows = [self._window_features(row.vibration, row.temperature)
                for row in windows.itertuples()]
        feats = pd.DataFrame(rows)
        feats['temp_trend'] = feats['temperature'].diff().fillna(0.0)
        return feats

    def train(self, windows: pd.DataFrame, labels: np.ndarray):
        X = self.scaler.fit_transform(     # fit HERE, once
            self.build_features(windows))
        self.model.fit(X, labels)

    def failure_probability(self, windows: pd.DataFrame) -> float:
        X = self.scaler.transform(         # transform ONLY
            self.build_features(windows))
        return float(self.model.predict_proba(X)[:, 1].max())

    def assess(self, windows, critical=0.7, warning=0.4):
        p = self.failure_probability(windows)
        if p > critical:
            return 'CRITICAL: schedule maintenance now', p
        if p > warning:
            return 'WARNING: monitor closely, plan maintenance', p
        return 'NORMAL: no action needed', p
```

```text
Details that matter (and where quickstarts go wrong)
- fft().argmax() returns a BIN INDEX, not a frequency - convert
  with rfftfreq(len(x), 1/fs) or your "dominant frequency" is
  a meaningless integer
- scaler.fit_transform in the PREDICTION path refits the scaler
  on today's data: the training distribution silently drifts.
  Fit once at train time, transform at inference
- class_weight="balanced": a line that fails 2% of the time
  trains a classifier that predicts "healthy" forever unless
  you weight the minority class
- the critical/warning thresholds are POLICY agreed with
  maintenance planning, not statistics - tune them with the
  team that owns the downtime cost
```

The natural-language report on top — on-prem, as factory networks usually require. (`pipeline("text-generation", model="gpt-4")` does not work: GPT-4 is not a Hugging Face model; via `transformers` you can only load open-weight checkpoints):

```python
from langchain_ollama import ChatOllama

def maintenance_report(llm, equipment_id, metrics, assessment) -> str:
    """Grounded report: the model sees exactly the numbers the
    pipeline measured, and is told to use only those."""
    prompt = f"""Draft a maintenance report.
Equipment: {equipment_id}
Vibration RMS: {metrics['vibration_rms']:.2f} mm/s
Dominant frequency: {metrics['dominant_freq']:.0f} Hz
Temperature: {metrics['temperature']:.1f} C
Assessment: {assessment}

Sections: 1. Condition summary 2. Risk assessment
3. Recommended actions 4. Timeline. Use ONLY the data above."""
    return llm.invoke(prompt).content

llm = ChatOllama(model="llama3.1", temperature=0)   # on-prem
```

## 2. Computer Vision Quality Control

A Faster R-CNN candidate detector with honest provenance: the shipped weights are COCO-pretrained, so they detect *COCO objects* — a production defect detector is this exact plumbing after fine-tuning on YOUR labeled defect images:

```python
import cv2
import torch
from torchvision.models.detection import (
    FasterRCNN_ResNet50_FPN_Weights, fasterrcnn_resnet50_fpn)

class QualityInspection:
    """Object detection -> pass/fail. Weights are COCO-
    pretrained; the defect_classes map is valid only AFTER
    fine-tuning on labeled defect images."""

    def __init__(self, score_threshold=0.7):
        self.weights = FasterRCNN_ResNet50_FPN_Weights.DEFAULT
        self.model = fasterrcnn_resnet50_fpn(
            weights=self.weights).eval()
        self.threshold = score_threshold
        self.defect_classes = {          # post-fine-tune labels
            1: 'scratch', 2: 'dent', 3: 'crack',
            4: 'color_variation', 5: 'misalignment',
        }

    def inspect(self, bgr) -> dict:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        tensor = torch.from_numpy(rgb).permute(2, 0, 1).float() / 255.0
        # GeneralizedRCNNTransform normalizes internally - do NOT
        # add manual mean/std on top (double normalization)
        with torch.no_grad():
            preds = self.model([tensor])[0]

        keep = preds['scores'] > self.threshold
        defects = []
        for label, score, box in zip(
                preds['labels'][keep], preds['scores'][keep],
                preds['boxes'][keep]):
            name = (self.defect_classes.get(label.item())
                    or self.weights.meta['categories'][label.item()])
            defects.append({
                'type': name,
                'confidence': round(score.item(), 3),
                'bbox': box.tolist(),          # XYXY
            })
        return {'passed': len(defects) == 0, 'defects': defects}
```

```text
What the fine-tuned production version changes
- the dataset: a few thousand labeled frames per defect class,
  balanced across lighting/position variants - this is 90% of
  the project
- the label map: your taxonomy (the dict above), replacing
  COCO's 80 categories
- the threshold: chosen on a validation set at the FALSE-
  POSITIVE rate your rework station can absorb - recall at a
  fixed FPR, not accuracy, is the number that matters
Deep dive with segmentation, thermal fusion, and a knowledge
base: [SOL-002](../enterprise-solutions/SOL-002-Industry-Solution.md)
```

## 3. Production Scheduling with RL

Honest framing first: for deterministic scheduling with explicit constraints (changeovers, due dates, capacity), a constraint solver — Google OR-Tools CP-SAT — is almost always the better first tool. RL earns its complexity when the objective or the process dynamics are hard to encode as constraints. The skeleton below shows the RL shape correctly:

```python
import gymnasium as gym
import numpy as np
from stable_baselines3 import PPO

class LineSchedulingEnv(gym.Env):
    """Simplified scheduling env: each step assigns the next
    job to a machine; terminal reward = -makespan. Skeleton -
    a real line adds changeover times, due dates, and
    stochastic breakdowns in step()."""

    def __init__(self, num_machines=10, num_jobs=50):
        super().__init__()
        self.num_machines = num_machines
        self.num_jobs = num_jobs
        self.observation_space = gym.spaces.Box(
            low=0, high=1e6,
            shape=(num_machines + num_jobs,), dtype=np.float32)
        self.action_space = gym.spaces.Discrete(num_machines)

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.queue = np.random.uniform(1, 10, self.num_jobs)
        self.machine_free = np.zeros(self.num_machines)
        return self._obs(), {}

    def step(self, action):
        job = self.queue[0] if len(self.queue) else 0.0
        self.machine_free[action] += job
        self.queue = self.queue[1:]
        done = len(self.queue) == 0
        reward = -float(self.machine_free.max()) if done else 0.0
        return self._obs(), reward, done, False, {}

    def _obs(self):
        padded = np.zeros(self.num_jobs)
        padded[:len(self.queue)] = self.queue
        return np.concatenate(
            [self.machine_free, padded]).astype(np.float32)

env = LineSchedulingEnv()
model = PPO("MlpPolicy", env, verbose=0)
model.learn(total_timesteps=100_000)

# roll out a schedule
obs, _ = env.reset()
done = False
while not done:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, done, _, _ = env.step(int(action))
```

```text
Decision guide
- explicit constraints, known durations -> CP-SAT (OR-Tools):
  optimal or provably-good in seconds, explainable
- stochastic process, soft objectives, simulator available ->
  RL: PPO over a faithful env, evaluated on the simulator
  against the CURRENT scheduler before anyone trusts it
- never schedule the live line directly from an RL policy -
  schedule into a planning buffer and let existing MES logic
  remain the actuator
```

## 4. Supply Chain RAG Agent

Decision support grounded in historical episodes: embeddings retrieve similar past situations, an on-prem LLM synthesizes. Modern Qdrant API (`query_points` — `search` is deprecated) and the current LangChain-Ollama integration:

```python
import uuid

from langchain_ollama import ChatOllama
from qdrant_client import QdrantClient
from qdrant_client.models import (Distance, PointStruct,
                                  VectorParams)
from sentence_transformers import SentenceTransformer

class SupplyChainAgent:
    """RAG over supply-chain episodes + on-prem synthesis."""

    def __init__(self, url="http://localhost:6333"):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.llm = ChatOllama(model="llama3.1", temperature=0)
        self.client = QdrantClient(url=url)
        if "supply_episodes" not in [
                c.name for c in
                self.client.get_collections().collections]:
            self.client.create_collection(
                collection_name="supply_episodes",
                vectors_config=VectorParams(
                    size=384, distance=Distance.COSINE))

    def remember_episode(self, description: str,
                         resolution: str) -> None:
        vec = self.encoder.encode(description).tolist()
        self.client.upsert(
            collection_name="supply_episodes",
            points=[PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload={'description': description,
                         'resolution': resolution})])

    def similar_episodes(self, situation: str, limit: int = 3):
        vec = self.encoder.encode(situation).tolist()
        points = self.client.query_points(
            collection_name="supply_episodes",
            query=vec, limit=limit, with_payload=True).points
        return "\n".join(
            f"- {p.payload['description']} "
            f"-> {p.payload['resolution']}"
            for p in points)

    def advise(self, situation: str) -> str:
        context = self.similar_episodes(situation)
        prompt = f"""Current situation:
{situation}

Similar historical episodes and how they were resolved:
{context}

Give: 1. Risk assessment 2. Recommended mitigation
3. What to monitor. Ground every point in the episodes above;
say so explicitly when the history does not cover this case."""
        return self.llm.invoke(prompt).content
```

```text
Two rules that keep supply-chain RAG honest
- temperature=0 and the "ground in the episodes" instruction:
  inventory and lead-time advice must be traceable to history,
  not invented
- the retrieval corpus needs CURATION - one bad resolution in
  the episode store teaches the LLM to recommend it forever.
  Review before ingestion (same pattern as SOL-001)
```

## 5. Digital Twin Monitoring

The lightweight, honest version of "digital twin": an ML surrogate trained on historical sensor→outcome pairs, monitored by comparing its predictions against reality. (Enterprise digital twins are full simulation engines — Siemens, AnyLogic; the surrogate below is the AI-team-sized pattern that detects *drift*, which is its actual job):

```python
import numpy as np
from sklearn.neural_network import MLPRegressor

class DigitalTwin:
    """Surrogate of one line: sensor features in,
    (throughput, quality, downtime) out."""

    def __init__(self):
        self.model = MLPRegressor(hidden_layer_sizes=(128, 64, 32),
                                  max_iter=1000)
        self.feature_cols = ['temperature', 'pressure',
                             'vibration_rms', 'line_speed']

    def train(self, sensor_df, outcomes_df):
        X = sensor_df[self.feature_cols].values
        y = outcomes_df[['throughput', 'quality',
                         'downtime']].values
        self.model.fit(X, y)

    def simulate(self, scenario: dict) -> dict:
        x = np.array([[scenario[c] for c in self.feature_cols]])
        throughput, quality, downtime = self.model.predict(x)[0]
        return {'throughput': float(throughput),
                'quality': float(quality),
                'downtime': float(downtime)}

    def deviation_alarm(self, live: dict, threshold=3.0) -> dict:
        """Compare twin prediction against actual outcome.
        Persistent deviation = sensor drift, model drift, or a
        real process change - all three deserve a human."""
        pred = self.simulate(live)
        devs = {k: abs(pred[k] - live[f'actual_{k}'])
                for k in pred}
        worst = max(devs, key=devs.get)
        return {'status': 'alarm' if devs[worst] > threshold
                else 'normal',
                'worst_deviation': worst,
                'deviation': round(devs[worst], 2)}
```

```text
What this twin is and is not
- IS: a drift detector - "the line is behaving differently
  than the model of the line expects"
- IS NOT: a physics simulator; do not quote its predictions as
  ground truth for capacity planning
- threshold is in OUTCOME units (units/hour, % quality), which
  is why plant engineers can actually set it
```

## End-to-End Orchestration

One monitoring cycle wiring the pieces above. The structural rule of the whole document is visible here: every decision is a deterministic threshold; the LLM only writes the prose:

```python
import time
from datetime import datetime, timezone

class SmartFactoryMonitor:
    """One cycle: assess + inspect + alarm, then an LLM report."""

    def __init__(self, maintenance, inspection, twin, llm):
        self.maintenance = maintenance
        self.inspection = inspection
        self.twin = twin
        self.llm = llm

    def run_cycle(self, sensor_windows, latest_image_bgr,
                  live_metrics) -> dict:
        assessment, prob = self.maintenance.assess(sensor_windows)
        inspection = self.inspection.inspect(latest_image_bgr)
        alarm = self.twin.deviation_alarm(live_metrics)
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'maintenance': assessment,
            'failure_probability': round(prob, 3),
            'inspection': inspection,
            'twin': alarm,
        }

    def report(self, cycle: dict) -> str:
        prompt = f"""Draft a shift status report from this data:
{cycle}

Sections: 1. Executive summary 2. Critical issues
3. Recommendations. Use ONLY the data above."""
        return self.llm.invoke(prompt).content

# plant-provided inputs (sensor SDK, camera, paging):
#   sensor_windows(), grab_frame(), live_metrics(), send_alert()
monitor = SmartFactoryMonitor(
    maintenance, quality_inspection, twin, llm)

while True:
    cycle = monitor.run_cycle(
        sensor_windows(), grab_frame(), live_metrics())
    critical = (cycle['maintenance'].startswith('CRITICAL')
                or cycle['twin']['status'] == 'alarm')
    if critical:
        send_alert(monitor.report(cycle))
    time.sleep(60)
```

```text
Read the wiring, not the loop
- every branch (CRITICAL, alarm) is a threshold a plant
  engineer can audit and retune
- the LLM is called ONLY when something needs saying - and its
  output goes to a human channel, never to an actuator
- the plant hooks (sensor_windows, grab_frame, live_metrics,
  send_alert) are the integration surface: everything above
  them is portable, everything below is yours
```

## Key Technologies

| Technology | Use Case |
|------------|----------|
| **Time-series ML** | Predictive maintenance (section 1) |
| **Computer vision** | Quality inspection (section 2) |
| **Solvers / RL** | Scheduling — CP-SAT first, RL when stochastic (section 3) |
| **RAG + on-prem LLM** | Supply-chain decision support (section 4) |
| **ML surrogate** | Digital-twin drift monitoring (section 5) |
| **Edge inference** | Line-side latency; quantized models (Phase 4) |

## Best Practices

```text
1. Start with predictive maintenance - the data already exists
   in historians; the labeled failure history is the real
   project. Budget for labeling before modeling
2. Vision: the model is the easy part. Lighting, fixturing,
   and a labeled defect taxonomy are the project. Recall at a
   fixed FPR is the acceptance metric
3. Scheduling: CP-SAT before RL. RL only with a faithful
   simulator, and never wired directly to the live line
4. LLMs draft and summarize; deterministic thresholds decide.
   No actuator ever reads an LLM's output
5. On-prem first: factory networks are air-gapped more often
   than not - ChatOllama-class local serving is the default
   assumption, cloud APIs the exception
6. Ground every generated report in measured numbers, and
   instruct the model to say when history does not cover a case
7. Validate on YOUR line: inter-inspector agreement and
   baseline downtime are the bars to beat - not paper
   benchmarks (same honest-metrics rule as SOL-002)
```

---

## References

### Related PROJECT-OMEGA Documents

- [SOL-002: Multi-Modal Industrial Inspection System](../enterprise-solutions/SOL-002-Industry-Solution.md)
- [SOL-001: Enterprise Knowledge Base](../enterprise-solutions/SOL-001-Enterprise-Knowledge-Base.md)
- [IND-001: Healthcare AI Applications](./IND-001-Healthcare-AI-Applications.md)
- [IND-002: Finance AI Applications](./IND-002-Finance-AI-Applications.md)

---

## Next Steps

- Full inspection pipeline (vision + fusion + knowledge base + report agent): **[SOL-002: Multi-Modal Industrial Inspection System](../enterprise-solutions/SOL-002-Industry-Solution.md)**
- RAG foundations: **[6100: Vector Databases](../phases/phase6-rag/6100-vector/README.md)**
- Agent architecture: **[7100: Agent Architecture](../phases/phase7-agentic/7100-architecture/README.md)**
- Sibling surveys: **[IND-001: Healthcare](./IND-001-Healthcare-AI-Applications.md)** · **[IND-002: Finance](./IND-002-Finance-AI-Applications.md)**
