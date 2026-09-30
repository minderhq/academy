---
Document ID: CP-001
Title: "CP-001: RAG vs Fine-Tuning vs Agents - Decision Guide"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['comparison', 'rag', 'finetuning', 'agents']
---

# CP-001: RAG vs Fine-Tuning vs Agents - Decision Guide

## Overview

This comparison guide helps you decide when to use RAG, Fine-Tuning, or Agents for your AI application. Each approach has different strengths, use cases, and implementation requirements.

---

## Quick Decision Matrix

| Scenario | Best Approach | Why |
|----------|--------------|-----|
| **Answer questions from private documents** | RAG | Needs access to specific, updatable information |
| **Teach model domain-specific vocabulary** | Fine-Tuning | Requires learning new language patterns |
| **Automate multi-step workflows** | Agents | Needs reasoning and tool use |
| **Reduce hallucinations** | RAG | Grounds responses in retrieved facts |
| **Improve response format/style** | Fine-Tuning | Trains model on desired output patterns |
| **Integrate with external APIs** | Agents | Can call functions and process results |
| **Keep information current** | RAG | Update docs, not model |
| **Handle complex user requests** | Agents | Can break down and plan multi-step tasks |

---

## Detailed Comparison

### 1. Retrieval-Augmented Generation (RAG)

#### What It Does

```text
User Question
    ↓
Search Documents → Find Relevant Chunks
    ↓
Combine Question + Chunks → Generate Answer
    ↓
Answer with Source Citations
```

#### When to Use RAG

✅ **Use RAG when:**

- You have documents/policies/manuals that need to be queried
- Information changes frequently (weekly, daily)
- You need source citations (legal, medical, financial)
- Accuracy is more important than creativity
- You have limited training data (100-10,000 documents)
- You want quick implementation (days, not weeks)
- Budget is limited (no GPU training costs)

❌ **Don't use RAG when:**

- Questions are about general knowledge (use pure LLM)
- You need specific output format (consider fine-tuning)
- Documents are very small (<50 pages)
- You want model to "learn" patterns, not retrieve facts

#### Real-World Examples

**Example 1: Company Knowledge Base**
```python
# Scenario: 50,000 internal documents
# Update frequency: Daily
# Requirement: Must cite sources

query = "What's our vacation policy for new hires?"

# RAG finds:
# - HR Policy 2024, section 3.2
# - Employee handbook, page 15
# - Onboarding guide, vacation section

# Response cites specific documents
```

**Example 2: Legal Research**
```python
# Scenario: 10,000 contracts
# Update frequency: Weekly
# Requirement: Must be accurate and citable

query = "Find Force Majeure clauses covering pandemics"

# RAG retrieves and cites:
# - Contract #1234, clause 12.3
# - Contract #5678, clause 8.1
# - Precedent case from 2023
```

#### Implementation Template

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# Setup
vectorstore = QdrantVectorStore.from_documents(
    documents=your_documents,
    embedding=OpenAIEmbeddings(),
    url="localhost:6333",
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# Create RAG chain - LangChain 1.x composes LCEL steps instead of
# the legacy RetrievalQA wrapper.
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the question using only the context. Cite sources."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])

def format_docs(docs):
    return "\n\n".join(
        f"[{d.metadata.get('source', '?')}]\n{d.page_content}" for d in docs
    )

rag_chain = (
    RunnableParallel(
        context=retriever | format_docs,
        question=RunnablePassthrough(),
    )
    | prompt
    | llm
    | StrOutputParser()
)

# Query
question = "your question"
answer = rag_chain.invoke({"question": question})
sources = [d.metadata["source"] for d in retriever.invoke(question)]
```

#### Cost Comparison

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| Embeddings (OpenAI) | $0.10 per 1M tokens | ~$10/month for 100M tokens |
| Vector DB (Qdrant self-hosted) | $0 | Your HomeLab hardware |
| LLM API (GPT-3.5) | $0.50 per 1M tokens | ~$20/month for moderate use |
| **Total** | **~$30/month** | Or self-host for $0 |

---

### 2. Fine-Tuning

#### What It Does

```text
Base Model (GPT/Llama)
    +
Training Data (Your examples)
    ↓
Fine-Tuned Model
(Learns your patterns, vocabulary, style)
```

#### When to Use Fine-Tuning

✅ **Use Fine-Tuning when:**

- Model needs domain-specific vocabulary (medical, legal, code)
- You need specific response format/style
- You have 1,000+ high-quality training examples
- Information is relatively stable (doesn't change daily)
- You want consistent, branded responses
- You're willing to invest time and resources
- You have GPU resources (or budget for training)

❌ **Don't Fine-Tune when:**

- You need up-to-date information (use RAG)
- You have limited training data (<100 examples)
- Information changes frequently
- You need source citations
- Quick implementation is critical

#### Real-World Examples

**Example 1: Medical Diagnosis Assistant**
```text
# Scenario: Medical terminology and reasoning
# Training data: 10,000 doctor-patient conversations
# Vocabulary: Highly specialized (rare diseases, drugs)

# Before fine-tuning:
User: "Patient has dyspnea and edema"
Model: "Let me search for breathing and swelling..."

# After fine-tuning:
User: "Patient has dyspnea and edema"
Model: "Consider congestive heart failure. Check BNP levels,
        chest X-ray, and review patient history for hypertension."
```

**Example 2: Code Generation**
```text
# Scenario: Company-specific coding patterns
# Training data: 50,000 internal code examples
# Style: Highly specific (naming, structure, patterns)

# Before fine-tuning:
Model writes: `def calculate(x, y): return x + y`

# After fine-tuning (learns company patterns):
Model writes:
```
```python
def calculate_summands(
    first_param: float,
    second_param: float
) -> float:
    """Calculate the sum of two numeric parameters.

    Args:
        first_param: The first summand
        second_param: The second summand

    Returns:
        The calculated sum
    """
    return first_param + second_param
```

#### Implementation Template

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer

# Load base model
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    load_in_4bit=True
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

# Configure LoRA (efficient fine-tuning)
lora_config = LoraConfig(
    r=16,  # Rank
    lora_alpha=32,
    target_modules=["q_proj", "v_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM"
)

# Apply LoRA
model = get_peft_model(model, lora_config)

# Training configuration
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=4,
    gradient_accumulation_steps=2,
    learning_rate=2e-4,
    fp16=True,
    logging_steps=10,
)

# Train
trainer = SFTTrainer(
    model=model,
    train_dataset=your_dataset,
    dataset_text_field="text",
    tokenizer=tokenizer,
    args=training_args,
)

trainer.train()
```

#### Cost Comparison

| Component | Cost | Notes |
|-----------|------|-------|
| GPU Training (11GB-class GPU, 3 epochs) | $0 (your hardware) | ~24-48 hours training time |
| Base Model (Llama 2 7B) | $0 | Open source |
| Electricity | ~$5-10 | Per training run |
| **Total** | **~$5-10** | One-time cost |

---

### 3. AI Agents

#### What They Do

```text
User Request
    ↓
Agent Thinks: "What do I need to do?"
    ↓
Agent Plans: [Step 1, Step 2, Step 3]
    ↓
Agent Executes: Uses tools for each step
    ↓
Agent Observes: Results from each tool
    ↓
Agent Thinks Again: "What next?"
    ↓
... (ReAct loop) ...
    ↓
Final Answer
```

#### When to Use Agents

✅ **Use Agents when:**

- Tasks require multiple steps/decisions
- Need to integrate with external APIs
- Tasks involve reasoning and planning
- Need to handle uncertain situations
- Want autonomous problem-solving
- Have reliable tools/functions available
- Can tolerate some unpredictability

❌ **Don't use Agents when:**

- Task is simple, single-step (use function)
- Workflow is fixed (use traditional automation)
- Need complete predictability
- Tools are unreliable
- Cost must be minimized (agents use more tokens)

#### Real-World Examples

**Example 1: DevOps Incident Management**
```text
# Scenario: Server alerts need investigation and resolution
# Complexity: Multiple steps, different tools needed
# Decision: Which action to take?

Alert: "API server returning 500 errors"

Agent Process:
1. Check pod status → "Pod is CrashLoopBackOff"
2. Get pod logs → "OutOfMemoryError"
3. Check memory usage → "Using 110% of limit"
4. Scale deployment → "Increased memory limit"
5. Restart pod → "Pod now healthy"
6. Verify → "API responding normally"

Result: Autonomous incident resolution
```

**Example 2: Travel Planning Agent**
```text
# Scenario: Plan a complex trip
# Complexity: Multiple bookings, constraints, preferences

User: "Plan a week in Japan in March, budget $3000,
       interested in temples and food, prefer Ryokans"

Agent Process:
1. Search destinations → Tokyo, Kyoto, Osaka
2. Search accommodations → Find Ryokans in Kyoto
3. Check availability → March 15-22 available
4. Get flight prices → $800 round trip
5. Calculate budget → $2200 remaining
6. Search activities → Temples, food tours within budget
7. Create itinerary → Day-by-day plan
8. Present options → 3 itinerary options

Result: Comprehensive travel plan
```

#### Implementation Template

```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# Define tools - @tool replaces the legacy Tool(name=, func=) constructor
@tool
def search(query: str) -> str:
    """Search for information."""
    return search_function(query)

@tool
def calculator(expression: str) -> str:
    """Perform calculations."""
    return calculator_function(expression)

@tool
def database(query: str) -> str:
    """Query the database."""
    return database_function(query)

# Create agent
llm = ChatOpenAI(model="gpt-4")
agent = create_agent(
    llm,
    [search, calculator, database],
    system_prompt="You are a helpful assistant with tool access.",
)

# Run
result = agent.invoke({
    "messages": [
        {"role": "user",
         "content": "Find the top 3 products by sales and calculate total revenue"}
    ]
})
print(result["messages"][-1].text)
```

#### Cost Comparison

| Component | Monthly Cost | Notes |
|-----------|--------------|-------|
| LLM API (GPT-4) | $0.03-0.12 per 1K tokens | Higher due to reasoning loops |
| Average tokens per task | 5,000-15,000 | Depends on complexity |
| Cost per task | $0.15-1.80 | Varies widely |
| API calls (tools) | Varies | Depends on external APIs |
| **Total** | **$50-500/month** | For 100-500 agent tasks |

---

## Combining Approaches

### RAG + Fine-Tuning

**Best of both:** Grounded in your documents + speaks your language

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

# Fine-tune for domain vocabulary
fine_tuned_model = load_finetuned_model("legal-llama-7b")

# Use RAG for factual retrieval - LangChain 1.x composes LCEL steps
# instead of the legacy RetrievalQA wrapper (langchain_classic only)
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer using only the provided context."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
rag_chain = (
    {"context": vectorstore.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | fine_tuned_model
    | StrOutputParser()
)

# Result: Accurate + understands legal terminology
```

**Use case:** Legal assistant that cites case law AND writes in legal style

### RAG + Agents

**Dynamic retrieval:** Agent decides what to search for

```python
from langchain_core.tools import tool
# Agent with RAG tools
@tool
def search_docs(query: str) -> str:
    """Search internal documents."""
    return rag_search(query)

@tool
def search_web(query: str) -> str:
    """Search the web."""
    return web_search(query)

@tool
def query_db(query: str) -> str:
    """Query the database."""
    return database_query(query)

tools = [search_docs, search_web, query_db]

agent = create_agent(tools=tools)

# Agent intelligently chooses which tool to use
```

**Use case:** Research assistant that searches multiple sources

### Agents + Fine-Tuning

**Specialized agents:** Domain-expert agents

```python
# Fine-tuned models for different domains
medical_agent = Agent(model="medical-llama-7b")
legal_agent = Agent(model="legal-llama-7b")
code_agent = Agent(model="code-llama-7b")

# Router sends to appropriate agent
```

**Use case:** Multi-domain assistant (medical, legal, general)

### All Three: RAG + Agents + Fine-Tuning

**Maximum capability:**

```python
from langchain_core.tools import tool
# Fine-tuned model
model = load_finetuned_model("domain-specific-7b")

# RAG for grounding
@tool
def search_docs(query: str) -> str:
    """Search internal documents."""
    return rag_search(query)

# Other tools
@tool
def api_call(query: str) -> str:
    """Call an external API."""
    return call_api(query)

@tool
def calculator(expression: str) -> str:
    """Perform calculations."""
    return calculator_function(expression)

# Agent orchestrates everything
agent = Agent(
    model=model,
    tools=[search_docs, api_call, calculator]
)
```

**Use case:** Enterprise knowledge assistant with domain expertise

---

## Decision Tree

```text
START: What do you need?

├─ Need to query documents/policies?
│  └─ YES → Use RAG
│
├─ Need specific format/style/vocabulary?
│  └─ YES → Use Fine-Tuning
│
├─ Need to integrate with APIs/tools?
│  └─ YES → Use Agents
│
├─ Need accurate, sourced information?
│  └─ YES → Use RAG
│
├─ Need multi-step reasoning/planning?
│  └─ YES → Use Agents
│
├─ Need model to "learn" patterns?
│  └─ YES → Use Fine-Tuning
│
└─ Multiple needs?
   └─ YES → Combine approaches
```

---

## Cost-Benefit Summary

| Approach | Implementation Time | Cost | Accuracy | Flexibility | Best For |
|----------|-------------------|------|----------|-------------|----------|
| **Pure LLM** | Immediate | Low | Medium | Low | General tasks |
| **RAG** | Days | Low | High | Medium | Document Q&A |
| **Fine-Tuning** | Weeks | Medium | Medium | Low | Domain style |
| **Agents** | Weeks | High | Medium | High | Complex tasks |
| **RAG + Fine-Tuning** | Weeks | Medium | High | Medium | Domain Q&A |
| **RAG + Agents** | Weeks | High | High | High | Dynamic research |
| **All Combined** | Months | High | Very High | Very High | Enterprise systems |

---

## Quick Reference

### RAG Quick Start

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

# 1. Index documents
# langchain_qdrant: QdrantVectorStore replaced the old Qdrant class
vectorstore = QdrantVectorStore.from_documents(
    docs, OpenAIEmbeddings(), url="http://localhost:6333"
)

# 2. Create chain - LangChain 1.x composes LCEL steps instead of
# the legacy RetrievalQA wrapper
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_messages([
    ("system", "Answer the question using only the context. Cite sources."),
    ("human", "Context:\n{context}\n\nQuestion: {question}"),
])
rag_chain = (
    {"context": vectorstore.as_retriever(), "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 3. Query
answer = rag_chain.invoke({"question": "your question"})
```

### Fine-Tuning Quick Start

```python
# 1. Prepare data
dataset = load_dataset("your_data.jsonl")

# 2. Configure LoRA
lora_config = LoraConfig(r=16, lora_alpha=32, target_modules=["q_proj"])

# 3. Train
trainer = SFTTrainer(model, train_dataset=dataset, args=training_args)
trainer.train()
```

### Agents Quick Start

```python
from langchain_core.tools import tool
# 1. Define tools
@tool
def your_tool(your_arg: str) -> str:
    """Describe what this tool does."""
    return your_func(your_arg)

tools = [your_tool]

# 2. Create agent
agent = create_agent(llm, tools)

# 3. Execute
result = agent.invoke({"messages": [{"role": "user", "content": "your task"}]})
```

---

**Comparison ID:** CP-001
**Related:** [UC-002: RAG Applications](../use-cases/UC-002-RAG-Applications.md), [UC-003: Agent Applications](../use-cases/UC-003-Agent-Applications.md), [5101: LoRA Logic](../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
## Next Steps

- **[CP-002: Vector DB Comparison](./CP-002-Vector-Database-Comparison.md)**
