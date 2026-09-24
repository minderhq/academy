---
Document ID: 6302
Title: CAG - Context Augmented Generation and Long Context Architectures
Phase: 6
Module: 6300
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'graphrag', 'neo4j', 'knowledge-graphs']
---

# 6302: CAG - Context Augmented Generation and Long Context Architectures

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [RAG vs CAG](#rag-vs-cag)
- [Long Context Models](#long-context-models)
- [Context Management](#context-management)
- [Implementation Examples](#implementation-examples)
- [Context Optimization](#context-optimization)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare RAG vs CAG
- Explain Long Context Models
- Explain Context Management
- Apply Implementation Examples
- Explain Context Optimization

---

## Abstract
CAG (Context Augmented Generation) uses the model's large context window as a temporary database, retrieving and inserting relevant information directly into the context rather than using RAG.

## RAG vs CAG

### Traditional RAG
```text
RAG (Retrieval-Augmented Generation):
  Query → Retrieve chunks → Insert into prompt → Generate
  - External vector database
  - Limited context (few chunks)
  - Retrieval happens each query
  - Good for: Large knowledge bases, dynamic data
```

### CAG (Context Augmented Generation)
```text
CAG (Context Augmented Generation):
  Pre-load entire relevant doc into context → Query → Generate
  - No external retrieval at inference
  - Uses 128k+ context window
  - Documents loaded once, reused
  - Good for: Document QA, code analysis, specific domains
```

### Comparison
```text
| Aspect         | RAG                  | CAG                      |
|----------------|----------------------|--------------------------|
| Context window | 4k-8k tokens         | 32k-128k tokens          |
| Latency        | Higher (retrieve)    | Lower (pre-loaded)       |
| Knowledge       | External DB          | In-context               |
| Use case        | Large corpus         | Specific documents       |
| Accuracy        | Retrieval dependent  | Context-length dependent |
```

## Long Context Models

### Models with Extended Context
```python
# Models supporting long context
long_context_models = {
    "Claude 2": {
        "context": "100k tokens",
        "architecture": "Attention with efficient cache",
        "use_case": "Book-length analysis"
    },
    "Claude 2.1/3": {
        "context": "200k tokens",
        "architecture": "Improved attention",
        "use_case": "Enterprise document analysis"
    },
    "GPT-4-Turbo": {
        "context": "128k tokens",
        "architecture": "GQA + attention optimizations",
        "use_case": "Code repository analysis"
    },
    "GPT-4-32k": {
        "context": "32k tokens",
        "architecture": "Standard attention",
        "use_case": "Meeting transcripts"
    },
    "Llama-2-Long": {
        "context": "32k+ tokens",
        "architecture": "Trained with longer sequences",
        "use_case": "Open-source long context"
    },
    "Mistral-7B": {
        "context": "32k tokens (with YaRN)",
        "architecture": "YaRN position interpolation",
        "use_case": "Local deployment"
    },
}
```

### Context Window Strategies
```python
# Strategy 1: Full document in context
def full_document_cag(document, query, model):
    """
    Load entire document into context
    """
    prompt = f"""
    Document:
    {document}

    Question: {query}

    Answer:
    """

    response = model.generate(prompt, max_tokens=512)
    return response

# Strategy 2: Chunked with overlap (for very long docs)
def chunked_cag(document, query, model, chunk_size=8000, overlap=200):
    """
    Process very long document in chunks
    """
    chunks = []
    start = 0

    while start < len(document):
        end = start + chunk_size
        chunk = document[start:end]
        chunks.append(chunk)
        start = end - overlap  # Overlap

    # Process each chunk
    answers = []
    for chunk in chunks:
        prompt = f"""
        Context: {chunk}

        Question: {query}

        Answer based on context:
        """
        answer = model.generate(prompt, max_tokens=256)
        answers.append(answer)

    # Combine answers
    combined_prompt = f"""
    Question: {query}

    Potential answers from different document sections:
    {chr(10).join(f'{i+1}. {ans}' for i, ans in enumerate(answers))}

    Synthesize a final answer:
    """

    final_answer = model.generate(combined_prompt, max_tokens=512)
    return final_answer
```

## Context Management

### Efficient Context Loading
```python
class ContextManager:
    """
    Manage long context for CAG
    """
    def __init__(self, model, max_context=100000):
        self.model = model
        self.max_context = max_context
        self.context = ""
        self.context_tokens = 0

    def add_document(self, document, priority="low"):
        """
        Add document to context
        Priority determines removal order when full
        """
        document_tokens = len(document.split())  # Rough estimate

        if self.context_tokens + document_tokens > self.max_context:
            # Remove old documents based on priority
            self._make_room(document_tokens, priority)

        # Add new document
        self.context += f"\n\n{document}"
        self.context_tokens += document_tokens

    def _make_room(self, needed_tokens, priority):
        """
        Remove old documents to make room
        """
        # Simple strategy: remove from start
        # Could be more sophisticated (LRU, importance)
        tokens_to_remove = needed_tokens + 1000  # Buffer

        # Remove from start
        while tokens_to_remove > 0:
            removed = self.context[:tokens_to_remove]
            self.context = self.context[tokens_to_remove:]
            tokens_to_remove = 0

        self.context_tokens -= needed_tokens

    def query(self, question):
        """
        Answer question using current context
        """
        prompt = f"""
        Context:
        {self.context}

        Question: {question}

        Answer based on the context above:
        """

        return self.model.generate(prompt)
```

### Dynamic Context Pruning
```python
def dynamic_context_pruning(context, query, model, keep_ratio=0.5):
    """
    Dynamically prune context based on query relevance

    Approach: Score each chunk by relevance to query, keep top K
    """
    # Split context into chunks
    chunks = split_context(context, chunk_size=500)

    # Score relevance
    scorer = CrossEncoderReranker()
    scored_chunks = scorer.rerank(query, chunks, top_k=len(chunks))

    # Keep top K
    keep = int(len(scored_chunks) * keep_ratio)
    pruned_context = "\n\n".join(scored_chunks[:keep])

    # Generate answer
    prompt = f"""
    Relevant Context:
    {pruned_context}

    Question: {query}

    Answer:
    """

    return model.generate(prompt)
```

## Implementation Examples

### Document QA System
```python
class DocumentQA:
    """
    Question answering over single long document
    """
    def __init__(self, model, max_tokens=100000):
        self.model = model
        self.max_tokens = max_tokens
        self.document = ""
        self.chunks = []

    def load_document(self, document_path):
        """
        Load and prepare document
        """
        with open(document_path, 'r') as f:
            self.document = f.read()

        # Create overlapping chunks
        self.chunks = self._create_chunks(
            self.document,
            chunk_size=8000,
            overlap=1000
        )

    def _create_chunks(self, text, chunk_size, overlap):
        """
        Create overlapping chunks
        """
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap

        return chunks

    def answer(self, question, method="full"):
        """
        Answer question about document
        """
        if method == "full":
            return self._answer_full_context(question)
        elif method == "chunked":
            return self._answer_chunked(question)

    def _answer_full_context(self, question):
        """
        Use entire document (if fits in context)
        """
        prompt = f"""
        Document:
        {self.document}

        Based on the document above, answer the following question:
        {question}

        Answer:
        """

        return self.model.generate(prompt)

    def _answer_chunked(self, question):
        """
        For very long docs: chunk, search, then answer
        """
        # Find relevant chunks
        relevant_chunks = self._find_relevant_chunks(question, top_k=5)

        # Combine into context
        context = "\n\n".join(relevant_chunks)

        prompt = f"""
        Relevant excerpts from document:
        {context}

        Question: {question}

        Answer based on the excerpts:
        """

        return self.model.generate(prompt)

    def _find_relevant_chunks(self, query, top_k=5):
        """
        Find most relevant chunks using BM25 or semantic search
        """
        # Simple keyword search (could use semantic)
        scored = []

        for i, chunk in enumerate(self.chunks):
            score = sum(word in chunk.lower() for word in query.lower().split())
            scored.append((i, score, chunk))

        # Sort and return top k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for _, _, chunk in scored[:top_k]]
```

### Code Analysis System
```python
class CodeAnalyzer:
    """
    Analyze entire code repository using CAG
    """
    def __init__(self, model):
        self.model = model
        self.repository = {}

    def load_repository(self, repo_path):
        """
        Load all files from repository
        """
        for root, dirs, files in os.walk(repo_path):
            # Skip common directories
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__']]

            for file in files:
                file_path = os.path.join(root, file)

                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        self.repository[file_path] = content
                except:
                    pass  # Binary files

    def analyze_codebase(self, question):
        """
        Answer question about entire codebase
        """
        # Build context from all files
        context_parts = []

        for file_path, content in self.repository.items():
            context_parts.append(f"""
File: {file_path}
```python
{content}
```
""")

        # Combine (may need to truncate for very large repos)
        full_context = "\n\n".join(context_parts)

        # Truncate if needed
        if len(full_context) > self.model.max_tokens:
            # Could implement smarter truncation
            full_context = full_context[:self.model.max_tokens - 1000]

        prompt = f"""
    Codebase:
    {full_context}

    Question: {question}

    Answer based on the code:
    """

        return self.model.generate(prompt)
```python

## Context Optimization

### Lost in the Middle Phenomenon
```python
"""
Models struggle with information in the middle of long context

Solution: Important information at start or end
"""

def optimize_context_order(context_chunks, query, important_chunks):
    """
    Reorder context to optimize for "lost in the middle"

    Strategy:
    - Important chunks at start and end
    - Less important in middle
    """
    # Identify important chunks (could use retrieval)
    # ...

    # Reorder
    # Start: Top 20% important
    # Middle: Remaining 60%
    # End: Top 20% important

    # This reduces "lost in the middle" effect
    pass
```

### Context Compression
```python
def compress_context(context, target_length=50000):
    """
    Compress context while preserving information
    """
    # Method 1: Extractive summarization
    # Select most important sentences

    # Method 2: Abstractive summarization
    # Generate summary of sections

    # Method 3: Hierarchical compression
    # Summarize chunks, then summarize summaries

    # Implementation depends on use case
    pass
```


---

## References

### Related ai-engineering-curriculum Documents

- [6301: Neo4j and Knowledge Graphs for Multi-Hop Reasoning](6301-Neo4j-and-Knowledge-Graphs.md)

---

## Next Steps

- Continue with: **[../6400-vector-databases/6401-Qdrant-Setup.md](./../6400-vector-databases/6401-Qdrant-Setup.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---
---

**Related Documents:**
- [4201: Context Window](../../phase4-quantization/4200-KV-Cache/4201-Context-Window-Physics.md)
- [6301: Neo4j GraphRAG](./6301-Neo4j-and-Knowledge-Graphs.md)
- [6202: Re-ranking](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)

**Experiment Template:** `experiments/EXP_6302_CAG.md"
