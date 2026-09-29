---
Document ID: 2305
Title: "2305: Framework Comparison Guide"
Phase: 2
Module: 2300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 1.5 hours
Prerequisites: See module README
Related: See module README
Tags: framework-comparison, transformers, pytorch-lightning, langchain, framework-selection
---

# 2305: Framework Comparison Guide

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Why Framework Choice Matters](#why-framework-choice-matters)
- [Comparison Criteria](#comparison-criteria)
- [Hugging Face Transformers: The Model Hub Standard](#hugging-face-transformers-the-model-hub-standard)
- [PyTorch Lightning: Structured Training](#pytorch-lightning-structured-training)
- [LangChain: LLM Application Orchestration](#langchain-llm-application-orchestration)
- [Building a Custom Framework](#building-a-custom-framework)
- [Summary Comparison Table](#summary-comparison-table)
- [Decision Guide](#decision-guide)
- [Combining Frameworks](#combining-frameworks)
- [Practical Recommendations](#practical-recommendations)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

By the end of this guide, you will be able to:

- **Choose** between Hugging Face Transformers, PyTorch Lightning, and LangChain for a concrete task, using explicit criteria instead of habit or hype.
- **Run** a minimal working example for each framework and identify what the framework is actually doing for you underneath.
- **Score** any framework (including ones not covered here) against the five comparison criteria used in this guide.
- **Wire frameworks together** — a Transformers model wrapped as a LangChain LLM — and explain why "versus" is usually the wrong frame.
- **Justify a framework decision in writing** for your own project, naming the trade-off you accepted.

## Abstract

This guide runs a minimal working example of each of the three frameworks — Hugging Face Transformers, PyTorch Lightning, and LangChain — scores all three against five explicit criteria, wires them together (a Transformers model wrapped as a LangChain LLM), and distills the results into a decision guide. They solve different problems: getting a pretrained model and tokenizer into your code in five lines, writing a training loop once and correctly, and composing LLM calls into an application — so “versus” is usually the wrong frame, and most real systems use two or three at once.

## Why Framework Choice Matters

A framework is a bundle of decisions someone else made for you: project layout, training loop structure, extension points, dependency surface. Accepting those decisions buys speed; accepting them blindly buys rework when the framework's assumptions stop matching your problem.

The three frameworks in this guide solve *different problems*, which is the first thing to internalize:

- **Hugging Face Transformers** answers: *how do I get a pretrained model and its tokenizer into my code in five lines?*
- **PyTorch Lightning** answers: *how do I write a training loop once, correctly, without hand-rolling mixed precision, checkpointing, and device management every time?*
- **LangChain** answers: *how do I compose LLM calls, retrievers, and tools into an application without gluing everything together by hand?*

None of them replaces the others. Most real systems use two or three at once.

## Comparison Criteria

Every framework below is scored against the same five criteria. When you evaluate a framework this guide does not cover, score it against these too.

| Criterion | Question it answers |
|---|---|
| **Abstraction level** | How much do you have to know about what happens underneath? Higher abstraction = faster start, harder debugging when it leaks. |
| **Ecosystem & community** | Pretrained weights, integrations, docs, Stack Overflow density. This determines how often you fight the tool vs. use it. |
| **Production readiness** | Can the thing you built in a notebook run unchanged behind an API with monitoring? |
| **Flexibility & control** | Can you override the framework when its defaults are wrong for you? |
| **Learning curve** | Time from zero to a correct, idiomatic result for a working engineer. |

Ratings use a five-star scale: more stars is more of that quality (so more stars on *learning curve* means *easier* to learn, and more stars on *abstraction level* means *more* is hidden from you).

## Hugging Face Transformers: The Model Hub Standard

Transformers is the de facto interface to the model ecosystem. Its real product is not the library — it is the [Model Hub](https://huggingface.co/docs/transformers/index) convention: any model published there is loadable with the same three calls.

**Ratings:**

| Criterion | Rating | Notes |
|---|---|---|
| Abstraction level | ★★★★☆ | `AutoModelForCausalLM.from_pretrained` hides architecture resolution, weight downloads, and device placement. |
| Ecosystem & community | ★★★★★ | Hundreds of thousands of checkpoints share one loading API; the widest integration surface in ML. |
| Production readiness | ★★★★☆ | Models are plain `torch.nn.Module`s — production-grade, but serving (batching, health checks, deployment) is on you, or on a server like vLLM/TGI. |
| Flexibility & control | ★★★★☆ | Everything is a standard PyTorch module; you can subclass, dissect, or export it. |
| Learning curve | ★★★☆☆ | The pipeline API is minutes; fine-tuning with custom data collators takes longer. |

**Minimal usage** — SmolLM2-1.7B-Instruct is an open (Apache-2.0), ungated model, so this runs with no Hugging Face login:

```python
# uv pip install transformers torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

# Ungated, Apache-2.0: a deliberate choice for teaching - no HF account needed.
MODEL_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

generator = pipeline("text-generation", model=model, tokenizer=tokenizer)
messages = [{"role": "user", "content": "Explain what an inference server does."}]
result = generator(messages, max_new_tokens=80)
print(result[0]["generated_text"][-1]["content"])
```

**Reach for Transformers when:** your starting point is a pretrained model — inference, fine-tuning, or embedding it into a larger system.

**Think twice when:** you need serving infrastructure (that is [1402: vLLM and TGI High-Concurrency Inference](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) territory) or training-loop structure (that is Lightning's job below).

## PyTorch Lightning: Structured Training

Lightning organizes your code into a `LightningModule` (the *what*: model, loss, optimization step) and hands the *how* (loop, device placement, logging, checkpointing) to the `Trainer`. The pitch is precise: your research code stops containing loop-scaffolding bugs, and the same module runs on CPU, one GPU, or a cluster by changing Trainer flags.

**Ratings:**

| Criterion | Rating | Notes |
|---|---|---|
| Abstraction level | ★★★★☆ | The epoch/batch loop, `.to(device)`, and gradient plumbing disappear; you implement named hooks like `training_step`. |
| Ecosystem & community | ★★★★☆ | Mature, well-documented, standard in research repos; smaller surface than Transformers. |
| Production readiness | ★★★★☆ | Checkpointing, logging integrations, and distributed flags are built in; the exported artifact is still a plain PyTorch module. |
| Flexibility & control | ★★★☆☆ | Escape hatches exist (`manual_optimization`, raw loops inside hooks), but deeply custom schedules fight the framework. |
| Learning curve | ★★★☆☆ | The hook model takes a day to internalize; after that, more code is *about your model* and less is about loops. |

**Complete, runnable example** — synthetic data, so nothing needs downloading:

```python
# uv pip install lightning torch
# The modern package is `lightning`; the older `pytorch_lightning` import
# still exists in legacy repos but new code should use the unified package.
import lightning as L
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset


class LitClassifier(L.LightningModule):
    """Everything about *what* to optimize; the Trainer owns *how* it runs."""

    def __init__(self, input_dim: int = 16, hidden_dim: int = 32, lr: float = 1e-3):
        super().__init__()
        self.save_hyperparameters()  # logged + restored with checkpoints
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 2),
        )
        self.loss_fn = nn.CrossEntropyLoss()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)

    def training_step(self, batch, batch_idx: int) -> torch.Tensor:
        x, y = batch
        loss = self.loss_fn(self(x), y)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx: int) -> None:
        x, y = batch
        self.log("val_loss", self.loss_fn(self(x), y), prog_bar=True)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=self.hparams.lr)


def make_loaders(n_train: int = 512, n_val: int = 128, batch_size: int = 32):
    g = torch.Generator().manual_seed(0)
    x_train = torch.randn(n_train, 16, generator=g)
    y_train = torch.randint(0, 2, (n_train,), generator=g)
    x_val = torch.randn(n_val, 16, generator=g)
    y_val = torch.randint(0, 2, (n_val,), generator=g)
    train_loader = DataLoader(TensorDataset(x_train, y_train), batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(TensorDataset(x_val, y_val), batch_size=batch_size)
    return train_loader, val_loader


if __name__ == "__main__":
    train_loader, val_loader = make_loaders()
    trainer = L.Trainer(
        max_epochs=3,
        limit_train_batches=4,   # tiny data: cap steps per epoch so the demo is seconds
        limit_val_batches=2,
        logger=False,
        enable_checkpointing=False,
    )
    trainer.fit(LitClassifier(), train_loader, val_loader)
    print("training finished - same code scales to multi-GPU via Trainer flags")
```

**Reach for Lightning when:** you are *training* models and the loop boilerplate (device placement, checkpointing, distributed) is eating your time.

**Think twice when:** you only serve pretrained models — Lightning buys you nothing at inference time.

## LangChain: LLM Application Orchestration

LangChain operates at a layer above the model: prompt templates, chat models, retrievers, vector stores, and chains composing them. For LLM applications, its value is the integration surface — every provider and vector store behind one interface — and a standard execution model.

**Ratings:**

| Criterion | Rating | Notes |
|---|---|---|
| Abstraction level | ★★★★★ | You declare components and wire them; execution, retries, and streaming plumbing are handled. |
| Ecosystem & community | ★★★★★ | The largest integration catalog in the LLM space; fast-moving, which cuts both ways. |
| Production readiness | ★★★☆☆ | Applications run in production widely, but observability and latency budgets need deliberate work (see the API design lessons in this module). |
| Flexibility & control | ★★★★☆ | Every abstraction has a custom-subclass escape hatch; you can drop to raw API calls any time. |
| Learning curve | ★★★☆☆ | Simple chains in an hour; the abstraction layers (runnables, retrievers, memory) reward a structured pass. |

**Minimal usage** — requires a local Ollama server (`ollama pull llama3.1` and `ollama pull nomic-embed-text`):

```python
# uv pip install langchain langchain-ollama langchain-community faiss-cpu
# The classic `from langchain.llms import Ollama` moved into the dedicated
# integration package: use langchain-ollama's ChatOllama / OllamaLLM, and
# call .invoke() instead of the old .run().
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings

llm = ChatOllama(model="llama3.1", temperature=0.1, base_url="http://localhost:11434")
print(llm.invoke("Name the three components of a RAG pipeline in one line.").content)

# model= is required - langchain-ollama ships no default embedding model.
embeddings = OllamaEmbeddings(model="nomic-embed-text", base_url="http://localhost:11434")

texts = [
    "Batching increases GPU utilization by grouping concurrent requests.",
    "A health check endpoint lets the load balancer drop unhealthy replicas.",
    "KV-cache reuse avoids recomputing attention for shared prompt prefixes.",
]
store = FAISS.from_texts(texts, embedding=embeddings)
hits = store.similarity_search("how do we keep the GPU busy?", k=1)
print(hits[0].page_content)
```

**Reach for LangChain when:** you are building an *application around* LLMs — RAG, agents, tool use — and want provider-agnostic composition.

**Think twice when:** your task is a single prompt-response call; a direct API client is simpler and one less dependency.

## Building a Custom Framework

Sometimes the right framework is the one you write — a thin layer of conventions over PyTorch and FastAPI. This is the path [2306: Building a Production Framework](./2306-Building-Production-Framework.md) walks in full; here is the seed it grows from.

**Ratings:**

| Criterion | Rating | Notes |
|---|---|---|
| Abstraction level | ★☆☆☆☆ | Nothing is hidden; every behavior is code you own. |
| Ecosystem & community | ★☆☆☆☆ | You are the community. Docs are whatever you write. |
| Production readiness | ★★★☆☆ | Potentially excellent — you build exactly what you need — but only if you build the operational parts (health checks, config, batching) too. |
| Flexibility & control | ★★★★★ | Total, by definition. |
| Learning curve | ★★☆☆☆ | Nothing to learn up front; everything to maintain forever. |

**The seed — a component contract:**

```python
from abc import ABC, abstractmethod


class Component(ABC):
    """Every pipeline stage accepts a dict payload and returns the dict."""

    @abstractmethod
    def handle(self, payload: dict) -> dict: ...


class Preprocessor(Component):
    def handle(self, payload: dict) -> dict:
        payload["clean"] = " ".join(str(payload["raw"]).split())
        return payload


class ModelStub(Component):
    def handle(self, payload: dict) -> dict:
        payload["prediction"] = sum(ord(c) for c in payload["clean"]) % 2
        return payload


pipeline = [Preprocessor(), ModelStub()]
out = {"raw": "  Inference   request "}
for step in pipeline:
    out = step.handle(out)
print(out["prediction"])
```

**Build custom when:** your domain logic is the product, the generic frameworks fight your shape, and you can afford to own the operational surface.

**Think twice when:** you are about to rebuild batching, config management, or registry plumbing that an existing framework already hardened — read [2306: Building a Production Framework](./2306-Building-Production-Framework.md) first and borrow its design instead of its maintenance burden.

## Summary Comparison Table

| Criterion | Transformers | Lightning | LangChain | Custom |
|---|---|---|---|---|
| Abstraction level | ★★★★☆ | ★★★★☆ | ★★★★★ | ★☆☆☆☆ |
| Ecosystem & community | ★★★★★ | ★★★★☆ | ★★★★★ | ★☆☆☆☆ |
| Production readiness | ★★★★☆ | ★★★★☆ | ★★★☆☆ | ★★★☆☆ |
| Flexibility & control | ★★★★☆ | ★★★☆☆ | ★★★★☆ | ★★★★★ |
| Learning curve (ease) | ★★★☆☆ | ★★★☆☆ | ★★★☆☆ | ★★☆☆☆ |

Read this table as *profiles, not winners*. Transformers wins on ecosystem reach; Lightning on training-loop hygiene; LangChain on application composition; custom on control. No row is uniformly best, which is why the next two sections matter more than the stars.

## Decision Guide

Answer these in order:

1. **Are you training a model, or serving an existing one?**
   - Training → Lightning structures your loop.
   - Serving a hub model → Transformers is the loading interface; pair it with a real inference server for throughput ([1402: vLLM and TGI High-Concurrency Inference](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md)).
2. **Is the LLM a component of an application (RAG, agents, tools)?**
   - Yes → LangChain composes the pieces; the model underneath is still Transformers/`ChatOllama`/whatever you choose.
   - No → a framework here is overhead; call the model directly.
3. **Is your problem shape standard (text in, text out, standard training)?**
   - Yes → use the off-the-shelf framework.
   - No → build custom, but copy the *designs* (registry, config, batching) from 2306 rather than inventing new ones.
4. **Who maintains this in twelve months?**
   - A team that knows framework X → that is a real criterion; score it deliberately.
   - Only you, long-term → prefer fewer, larger, slower-moving dependencies.

## Combining Frameworks

The frameworks compose cleanly because they operate at different layers. The most common production stack: **Lightning for training → Transformers as the model interface → LangChain for application orchestration → FastAPI for serving** (the serving layer is [2306: Building a Production Framework](./2306-Building-Production-Framework.md)).

A Transformers model wrapped as a LangChain LLM — one pipeline object shared by both worlds:

```python
# uv pip install "langchain-huggingface[full]" transformers torch
# The [full] extra pulls the local inference dependencies; without it the
# package installs but cannot run a local pipeline.
import torch
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

MODEL_ID = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

# HuggingFacePipeline wraps an actual transformers pipeline OBJECT - not a
# task string and not a model id. Build the pipeline first, then hand it in.
pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=64,
    torch_dtype=torch.float32,
)
llm = HuggingFacePipeline(pipeline=pipe)
print(llm.invoke("Summarize why KV caches matter in one sentence."))
```

What just happened: LangChain's chain machinery calls `pipe` exactly as the raw Transformers example did. The model layer never knew about the application layer — that decoupling is the point.

## Practical Recommendations

- **Default stack for a new LLM project:** Transformers + Lightning for the model/training layer, LangChain only if there is real application composition, FastAPI (per [2303: API Design for ML Systems](../2303-API-Design-for-ML.md)) at the edge.
- **Add a framework only against a named pain.** "Might need it later" is how projects accumulate a second framework's dependency surface for a feature that never ships.
- **Pin and read the integration packages.** The LLM ecosystem moves fast: `langchain-ollama` and `langchain-huggingface` are separate packages precisely so they can move at their own pace.
- **Prototype in the framework, productionize deliberately.** A notebook prototype is disposable; the API wrapper, config, and monitoring around it are the product.
- **Write the decision down.** A five-line ADR (decision, criteria, accepted trade-off) prevents the same debate from restarting every quarter.

## Summary

**Framework choice is a layered decision, not a tournament.** Transformers standardizes *access to models*, Lightning standardizes *training loops*, LangChain standardizes *LLM application composition*, and a custom framework is the control-maximal end of the same spectrum.

- Score frameworks against explicit criteria — abstraction, ecosystem, production readiness, flexibility, learning curve — so the choice is reviewable.
- The three frameworks in this guide solve different problems and compose; "Transformers *or* LangChain" is usually a category error.
- Integration packages move independently (`langchain-ollama`, `langchain-huggingface`) — pin versions and read their changelogs.
- Before building custom, steal the designs (registry, config, batching) that [2306: Building a Production Framework](./2306-Building-Production-Framework.md) implements end to end.

## References

### Related Documents

- [Phase 2: Module 2300 - Framework Engineering](../README.md)
- [2301: Framework Design Patterns](../2301-Framework-Design-Patterns.md)
- [2302: Model Serving Architectures](../2302-Model-Serving-Architectures.md)
- [2303: API Design for ML Systems](../2303-API-Design-for-ML.md)
- [2306: Building a Production Framework](./2306-Building-Production-Framework.md)

### External References

- [Transformers Documentation](https://huggingface.co/docs/transformers/index)
- [PyTorch Lightning Documentation](https://lightning.ai/docs/pytorch/stable/)
- [LangChain Overview](https://docs.langchain.com/oss/python/langchain/overview)
- [langchain-ollama on PyPI](https://pypi.org/project/langchain-ollama/)
- [langchain-huggingface on PyPI](https://pypi.org/project/langchain-huggingface/)
- [SmolLM2-1.7B-Instruct Model Card](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct)

## Next Steps

- **Next Guide:** [2306: Building a Production Framework](./2306-Building-Production-Framework.md) — build the custom framework this guide argued for, end to end.
- **Practical:** [LAB-007: Production RAG System](../../../../learning-resources/labs/LAB-007-Production-RAG.md) — a LangChain-style retrieval application in production shape.
- **Assessment:** [2300: Framework Engineering - Quiz](../assessment/QUIZ.md)

**Related:** [1402: vLLM and TGI High-Concurrency Inference](../../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) · [TUTORIAL-003: RAG Basics - Give Your LLM Knowledge](../../../../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md) · [6101: HNSW Indexing - Efficient Semantic Search at Scale](../../../phase6-rag/6100-vector/6101-HNSW-Indexing.md)

**Experiment:** [EXP_1403: TGI (Text Generation Inference) Tuning Experiments](../../../../../experiments/EXP_1403_TGI_TUNING.md) — measure what a dedicated inference server buys over naive model serving.
