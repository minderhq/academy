# AI Engineering Curriculum Glossary

**Official Terminology Reference**

**Last Updated:** 2026-02-04
**Purpose:** Standardize terminology across all AI Engineering Curriculum documentation

---

## 📖 Usage Guidelines

### Why This Matters
Consistent terminology prevents confusion and makes learning easier. When you see a term anywhere in AI Engineering Curriculum, it means the same thing.

### How to Use
1. **Writers:** Use these exact terms in all documentation
2. **Learners:** Reference this when you encounter unfamiliar terms
3. **Contributors:** Follow these standards in new content

---

## 🤖 Core AI Concepts

| Term | Definition | Related Terms |
|------|------------|--------------|
| **LLM** | Large Language Model - AI system trained on vast text data | Foundation model, Base model |
| **Inference** | Running a trained model to generate predictions | Deployment, Serving |
| **Training** | Process of teaching a model from data | Fine-tuning, Pre-training |
| **Fine-tuning** | Adapting a pre-trained model to specific tasks | SFT, Adaptation |
| **Token** | Smallest unit of text an LLM processes | Word piece, Subword |
| **Embedding** | Numerical representation of text/data | Vector, Latent space |
| **Transformer** | Neural network architecture powering modern LLMs | Attention-based model |
| **Attention** | Mechanism allowing models to focus on relevant parts | Self-attention, Multi-head |
| **Parameters** | Weights learned during training | Weights, Model size |
| **Context Window** | Maximum input length a model can process | Input length, Sequence length |

---

## 🔧 Technical Operations

| Term | Correct Usage | Incorrect Usage |
|------|--------------|----------------|
| **LLMOps** | Large Language Model Operations (one word, capital O) | LLM Ops, LLMOps, llmops |
| **Vector Database** | Database optimized for similarity search (two words) | VectorDB, Vector DB, VectorDb |
| **ReAct** | Reasoning + Acting framework (capital R, capital A) | React, react, REACT |
| **RAG** | Retrieval-Augmented Generation (always capitalized) | rag, Rag, r.a.g. |
| **LoRA** | Low-Rank Adaptation (capital L, capital R, capital A) | lora, Lora, lora |
| **QLoRA** | Quantized LoRA (capital Q, capital L, capital R, capital A) | qlora, Qlora, q-lora |
| **DPO** | Direct Preference Optimization (always capitalized) | dpo, D.P.O. |
| **GGUF** | File format for quantized models (always uppercase) | gguf, Gguf |
| **GraphRAG** | RAG with knowledge graphs (one word, capital G, capital R) | Graph RAG, graphrag, GraphRag |

---

## 📊 Model Metrics & Characteristics

| Term | Definition | Unit |
|------|------------|------|
| **Parameters** | Number of weights in model | Billions (7B, 13B, 70B) |
| **VRAM** | Video RAM required for inference | GB (8GB, 16GB, 24GB) |
| **Quantization** | Reducing model precision | Bits (4-bit, 8-bit) |
| **Throughput** | Tokens processed per second | TPS, tokens/s |
| **Latency** | Time to first token | TTFT, milliseconds |
| **Context Length** | Maximum input + output tokens | Tokens (4K, 8K, 32K, 128K) |
| **Temperature** | Randomness in generation | Float (0.0 - 2.0) |
| **Top-P** | Nucleus sampling parameter | Float (0.0 - 1.0) |
| **Top-K** | K most likely tokens | Integer (1 - 100) |

---

## 🏗️ Architecture & Deployment

| Term | Definition | Example |
|------|------------|---------|
| **Microservices** | Small, independent services | RAG service, LLM service |
| **Orchestration** | Managing multiple services/AI agents | Kubernetes, Docker Compose |
| **Scaling** | Handling increased load | Horizontal, Vertical |
| **Load Balancing** | Distributing requests across servers | Nginx, HAProxy |
| **Canary Deployment** | Rolling out to subset of users | 10% traffic to new version |
| **Blue-Green Deployment** | Switching between identical environments | Blue (old), Green (new) |
| **A/B Testing** | Comparing two versions | Model A vs Model B |
| **CI/CD** | Continuous Integration/Deployment | GitHub Actions, GitLab CI |

---

## 🔒 Security & Safety

| Term | Definition | Related |
|------|------------|---------|
| **Prompt Injection** | Adversarial prompts to bypass controls | Jailbreak, DAN |
| **PII** | Personally Identifiable Information | Personal data, Sensitive data |
| **Redaction** | Removing sensitive information | Masking, Sanitization |
| **Differential Privacy** | Privacy-preserving technique | DP, ε-delta |
| **Adversarial Attack** | Inputs designed to fool models | FGSM, PGD |
| **Robustness** | Model resistance to attacks | Adversarial training |

---

## 🧪 Experimentation & Testing

| Term | Definition | Usage |
|------|------------|-------|
| **Baseline** | Reference model for comparison | GPT-4, Claude |
| **Benchmark** | Standardized test suite | MMLU, HellaSwag, GSM8K |
| **Ablation Study** | Removing components to test necessity | "Without attention" |
| **Hyperparameter** | Configuration setting not learned during training | Learning rate, Batch size |
| **Epoch** | One full pass through training data | 1 epoch, 10 epochs |
| **Batch Size** | Samples processed before updating weights | 32, 64, 128 |
| **Learning Rate** | Step size for optimization | 1e-4, 1e-5 |
| **Gradient Descent** | Optimization algorithm | SGD, Adam, AdamW |

---

## 📁 File & Module Naming

### Phase Numbers (4-digit format)
```text
✅ CORRECT: 3100-attention, 6100-vector, 7100-architecture
❌ INCORRECT: 3100, 31xx, attention-3100
```

### Module Naming (kebab-case)
```text
✅ CORRECT: model-drift-detection, prompt-injection-defense
❌ INCORRECT: ModelDriftDetection, model_drift_detection
```

### File Names (Title-Case with hyphens)
```text
✅ CORRECT: 3101-Self-Attention-DeepDive.md
❌ INCORRECT: 3101_self_attention.md, self-attention-3101.md
```

### Guide Files (explicit "guide" suffix)
```text
✅ CORRECT: 5104-LoRA-Implementation-Guide.md
❌ INCORRECT: 5104-LoRA-Implementation.md, LoRA-guide.md
```

---

## 🎯 Learning Phases

### Phase Names (consistent usage)
```text
Phase 1: [1000] Infrastructure Fabric
Phase 2: [2000] Cognitive Science & Frameworks
Phase 3: [3000] Transformer Physics & LLM Internals
Phase 4: [4000] Quantization & Compression
Phase 5: [5000] Model Adaptation: Fine-Tuning & Alignment
Phase 6: [6000] Data Nexus: RAG & Memory
Phase 7: [7000] Agentic Cognition & Autonomy
```

### Volume Names (consistent usage)
```text
Volume 1: Infrastructure Fundamentals
Volume 2: AI/ML Foundations
Volume 3: LLM Internals & Architecture
Volume 4: Quantization & Optimization
Volume 5: Model Adaptation
Volume 6: Data Nexus: RAG & Memory
Volume 7: Production Mastery
```

---

## 🔢 Numbering Conventions

### Module Numbers (4-digit format)
```text
[3100] Attention Architectures
[3200] Embedding Latent Spaces
[3300] The Decoding Block
[3400] Model Architectures
```

### Document Numbers (4-digit + sequential)
```text
3101, 3102, 3103... (sequential within module)
5101, 5102, 5103, 5104... (allow gaps for guides)
```

### Experiment Numbers (EXP_XXXX_...)
```text
EXP_1101_GPON.md
EXP_3101_SELF_ATTENTION.md
EXP_6501_MLOPS_PIPELINE.md
```

---

## 💬 Common Acronyms

| Acronym | Full Term | Context |
|---------|-----------|---------|
| **API** | Application Programming Interface | Software integration |
| **CLI** | Command Line Interface | Terminal usage |
| **CPU** | Central Processing Unit | Main processor |
| **GPU** | Graphics Processing Unit | Accelerator |
| **TPU** | Tensor Processing Unit | Google accelerator |
| **RAM** | Random Access Memory | System memory |
| **SSD** | Solid State Drive | Storage |
| **NVMe** | Non-Volatile Memory Express | Fast storage |
| **HTTP** | Hypertext Transfer Protocol | Web communication |
| **REST** | Representational State Transfer | API style |
| **JSON** | JavaScript Object Notation | Data format |
| **YAML** | YAML Ain't Markup Language | Config format |

---

## 🌐 AI Companies & Models

| Company | Notable Models | Abbreviation |
|---------|---------------|--------------|
| **Meta** | LLaMA 2, LLaMA 3 | - |
| **Mistral AI** | Mistral 7B, Mixtral 8x7B | - |
| **Google** | Gemini, PaLM, BERT | - |
| **OpenAI** | GPT-3.5, GPT-4, GPT-4o | - |
| **Anthropic** | Claude 3, Claude 3.5 | - |
| **Cohere** | Command R, R+ | - |
| **01.AI** | Yi-34B, Yi-6B | - |

---

## 📝 Usage Examples

### In Documentation
```markdown
✅ CORRECT:
"The LLMOps pipeline uses a Vector Database for RAG implementation.
ReAct agents perform tool calling to complete tasks."

❌ INCORRECT:
"The LLM Ops pipeline uses a VectorDB for RAG.
React agents perform tool-calling to complete tasks."
```

### In Code Comments
```python
✅ CORRECT:
# Implement LoRA fine-tuning with QLoRA quantization
# Store embeddings in Vector Database for RAG

❌ INCORRECT:
# Implement lora fine-tuning with qlora
# Store embeddings in vectorDB for rag
```

### In File Names
```text
✅ CORRECT:
docs/phases/phase3-transformers/3100-attention/3101-Self-Attention-DeepDive.md

❌ INCORRECT:
docs/phases/phase3/attention/Self-Attention.md
docs/transformers/3101-self-attention.md
```

---

## 🔄 Term Evolution

### Deprecated Terms (Don't Use)
| Old Term | New Term | Reason |
|----------|----------|--------|
| "Language Model" | "LLM" or "Foundation Model" | More specific |
| "Fine-tune" | "Fine-tuning" (noun) | Consistency |
| "Inference Engine" | "Inference Server" | Clarity |
| "Prompt Engineer" | "Prompt Engineering" | Consistency |

### Emerging Terms (Use with Definition)
- **Agentic AI** - AI systems that can plan and act autonomously
- **Multimodal** - Models handling multiple data types (text, image, audio)
- **Federated Learning** - Distributed training without centralizing data
- **Constitutional AI** - AI with built-in ethical constraints

---

## 📚 Additional Resources

### External Glossaries
- [Google AI Glossary](https://ai.google/static/education/glossary/)
- [NVIDIA AI Glossary](https://www.nvidia.com/en-us/glossary/)
- [OpenAI Glossary](https://platform.openai.com/docs/guides/gpt-best-practices)

### Style Guides
- [Google Developer Documentation Style Guide](https://developers.google.com/tech-writing)
- [Microsoft Writing Style Guide](https://docs.microsoft.com/en-us/style-guide/)

---

## 🤝 Contributing

Found an inconsistency? Suggest changes by:
1. Checking if term is listed here
2. Proposing standardized usage
3. Updating all affected documentation
4. Updating this glossary

---

**Last Updated:** 2026-02-04
**Version:** 1.0
**Maintained By:** AI Engineering Curriculum Documentation Team

---

**Quick Reference:** Use Ctrl+F to find terms quickly
