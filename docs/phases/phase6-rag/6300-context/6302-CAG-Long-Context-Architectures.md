---
Document ID: 6302
Title: CAG - Context Augmented Generation and Long Context Architectures
Phase: 6
Module: 6300
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['rag', 'context', 'cag', 'long-context']
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

- Compare RAG vs CAG trade-offs — per-query retrieval over a vector database vs pre-loading the corpus into the window, and name the regime (small, stable corpus; document/code QA) where CAG wins
- Size a long-context model from the 2026 table — Gemini 3 (2M), GPT-5.x (~1M in / 128k out), Claude 1M, Qwen3 256k native → 1M with YaRN, Llama 4 Scout 10M paper-spec — and separate advertised ceilings from reliable working length
- Chunk long documents with overlap — run the `chunk_size`/`overlap` sliding window and justify the `overlap < chunk_size` guard that keeps `start` advancing
- Run an evicting context manager — `ContextManager.add_document`/`_make_room` evicts lowest-priority-then-oldest documents when the token budget is exceeded, with a truthful token ledger
- Prune context by query relevance — `split_context` into windows, score chunks (`keyword_score` fallback or the 6202 cross-encoder), keep the top `keep_ratio`, and restore reading order
- Defeat lost-in-the-middle and compress — `optimize_context_order` parks important chunks at the start and end, and `compress_context` extractively keeps high-information sentences within a budget

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
| Context window | Prompt budget (few chunks) | 128k-2M+ tokens    |
| Latency        | Higher (retrieve)    | Lower (pre-loaded)       |
| Knowledge       | External DB          | In-context               |
| Use case        | Large corpus         | Specific documents       |
| Accuracy        | Retrieval dependent  | Context-length dependent |
```

## Long Context Models

### Models with Extended Context
```python
# Flagship context windows as of 2026-09. Advertised maxima are ceilings,
# not working memory — quality degrades well before the limit on most
# models (lost-in-the-middle, below), so budget 100-200k as the reliable zone
long_context_models = {
    "Gemini 3": {
        "context": "2M tokens",
        "architecture": "Sparse attention + implicit caching",
        "use_case": "Largest usable frontier context"
    },
    "GPT-5.x": {
        "context": "~1M input / 128k output",
        "architecture": "GQA + attention optimizations",
        "use_case": "Code repository analysis"
    },
    "Claude (Sonnet 4.6 / Opus 4.7)": {
        "context": "1M tokens (200k standard)",
        "architecture": "Efficient attention + prompt caching",
        "use_case": "Book-length and agentic analysis"
    },
    "Qwen3": {
        "context": "256k native, 1M with YaRN",
        "architecture": "YaRN position interpolation",
        "use_case": "Open-weight long context"
    },
    "Llama 4 Scout": {
        "context": "10M tokens (paper spec)",
        "architecture": "MoE + iRoPE, early-fusion multimodal",
        "use_case": "Massive single documents; degrades at extremes"
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
    # `start = end - overlap` advances by chunk_size - overlap per step;
    # overlap >= chunk_size would never advance start and stall the loop
    if overlap >= chunk_size:
        raise ValueError("overlap must be < chunk_size")
    chunks = []
    start = 0

    while start < len(document):
        end = start + chunk_size
        chunk = document[start:end]
        chunks.append(chunk)
        if end >= len(document):
            break
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
    def __init__(self, model, max_context=100000, headroom=1000):
        self.model = model
        self.max_context = max_context   # token budget (word-count estimate)
        self.headroom = headroom        # buffer kept free when evicting
        self.documents = []             # (priority, seq, text, tokens)
        self._seq = 0                   # insertion order

    def add_document(self, document, priority="low"):
        """
        Add document to context. When the budget is exceeded,
        low-priority (then oldest) documents are evicted first.
        """
        document_tokens = len(document.split())  # word count ≈ token estimate

        if self.context_tokens + document_tokens > self.max_context:
            self._make_room(document_tokens)

        self.documents.append((priority, self._seq, document, document_tokens))
        self._seq += 1

    @property
    def context_tokens(self):
        # Ledger is derived from what is actually stored — never drifts
        return sum(doc[3] for doc in self.documents)

    @property
    def context(self):
        return "\n\n".join(doc[2] for doc in self.documents)

    def _make_room(self, needed_tokens):
        """
        Evict lowest-priority, then oldest, documents until the new
        document fits with headroom. Returns the tokens actually freed.
        """
        rank = {"low": 0, "high": 1}
        candidates = sorted(self.documents, key=lambda d: (rank[d[0]], d[1]))

        freed = 0
        evict = []
        for doc in candidates:
            if freed >= needed_tokens + self.headroom:
                break
            freed += doc[3]
            evict.append(doc)

        for doc in evict:
            self.documents.remove(doc)  # (priority, seq) unique → safe
        return freed

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
def split_context(context, chunk_size=500):
    """
    Split context into fixed-size character windows. Production pipelines
    split on paragraph/sentence boundaries instead so windows don't cut
    sentences in half.
    """
    return [context[i:i + chunk_size]
            for i in range(0, len(context), chunk_size)]


def keyword_score(query, chunk):
    """
    Fallback scorer: fraction of query words present in the chunk.
    Production: swap in a cross-encoder — CrossEncoderReranker in
    6202-Re-ranking — wrapped as score_fn(query, chunk) -> float.
    """
    q_words = set(query.lower().split())
    if not q_words:
        return 0.0
    return len(q_words & set(chunk.lower().split())) / len(q_words)


def dynamic_context_pruning(context, query, model, keep_ratio=0.5,
                            chunk_size=500, score_fn=keyword_score):
    """
    Dynamically prune context based on query relevance

    Approach: Score each chunk by relevance to query, keep the top
    keep_ratio of chunks, and restore the original reading order
    (shuffled context reads as noise to the model)
    """
    chunks = split_context(context, chunk_size=chunk_size)

    # Score relevance — rank chunk positions by score
    ranked = sorted(range(len(chunks)),
                    key=lambda i: score_fn(query, chunks[i]),
                    reverse=True)

    # Keep top K
    keep = max(1, int(len(chunks) * keep_ratio))
    kept = sorted(ranked[:keep])
    pruned_context = "\n\n".join(chunks[i] for i in kept)

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
        Create overlapping chunks (same overlap < chunk_size guard as
        chunked_cag above — otherwise start never advances)
        """
        if overlap >= chunk_size:
            raise ValueError("overlap must be < chunk_size")
        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            if end >= len(text):
                break
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
        Find most relevant chunks using keyword overlap
        """
        # Token-set matching: whole words only. A substring test like
        # `word in chunk` would count "the" inside "theory"
        query_words = set(query.lower().split())
        scored = []

        for i, chunk in enumerate(self.chunks):
            chunk_words = set(chunk.lower().split())
            score = len(query_words & chunk_words)
            scored.append((i, score, chunk))

        # Sort and return top k
        scored.sort(key=lambda x: x[1], reverse=True)
        return [chunk for _, _, chunk in scored[:top_k]]
```

### Code Analysis System
````python
import os

class CodeAnalyzer:
    """
    Analyze entire code repository using CAG
    """
    def __init__(self, model, max_context_chars=600000):
        self.model = model
        # Model clients expose their window in tokens via their own config,
        # not a .max_tokens attribute — budget in characters here
        # (~4 chars/token → 600k chars ≈ 150k tokens)
        self.max_context_chars = max_context_chars
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
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        self.repository[file_path] = content
                except (OSError, UnicodeDecodeError):
                    pass  # Unreadable or binary files

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

        # Truncate if needed (smarter option: per-file relevance ranking)
        if len(full_context) > self.max_context_chars:
            full_context = full_context[:self.max_context_chars]

        prompt = f"""
    Codebase:
    {full_context}

    Question: {question}

    Answer based on the code:
    """

        return self.model.generate(prompt)
````

## Context Optimization

### Lost in the Middle Phenomenon
```python
"""
Models struggle with information in the middle of long context

Solution: Important information at start or end
"""

def optimize_context_order(context_chunks, important_indices):
    """
    Reorder context to mitigate "lost in the middle" (Liu et al. 2023):
    recall is strongest at the start and end of the window, weakest in
    the middle.

    important_indices: positions (into context_chunks) of the chunks most
    relevant to the query — identify them with the retrieval scorer of
    your pipeline. The first half goes to the front, the second half to
    the back; remaining chunks fill the middle.
    """
    important = [context_chunks[i] for i in sorted(important_indices)]
    rest = [c for i, c in enumerate(context_chunks)
            if i not in set(important_indices)]

    half = len(important) // 2
    return important[:half] + rest + important[half:]
```

### Context Compression
```python
def compress_context(context, target_length=50000):
    """
    Extractive compression: keep the highest-information sentences until
    the target character budget is reached.

    Informativeness ≈ mean in-document word frequency per sentence (the
    Luhn-style extractive heuristic) — no model call needed. Abstractive
    or hierarchical variants swap this ranker for a summarizer.
    """
    sentences = [s.strip() for s in context.split(".") if s.strip()]
    if not sentences:
        return ""

    word_freq = {}
    for s in sentences:
        for w in s.lower().split():
            word_freq[w] = word_freq.get(w, 0) + 1

    def informativeness(i):
        words = sentences[i].lower().split()
        return sum(word_freq[w] for w in words) / max(len(words), 1)

    # Rank sentence POSITIONS (duplicated sentences stay distinct), keep
    # the best until the budget is reached
    ranked = sorted(range(len(sentences)), key=informativeness, reverse=True)
    kept_idx, budget = [], 0
    for i in ranked:
        if budget + len(sentences[i]) > target_length:
            break
        kept_idx.append(i)
        budget += len(sentences[i])

    if not kept_idx:  # every sentence exceeds the budget: top one, trimmed
        return sentences[ranked[0]][:target_length]

    # Restore the original reading order (positions are unique — no dupes)
    return ". ".join(sentences[i] for i in sorted(kept_idx)) + "."
```


---

## References

### Related ai-engineering-curriculum Documents

- [6301: Neo4j and Knowledge Graphs for Multi-Hop Reasoning](6301-Neo4j-and-Knowledge-Graphs.md)
- [4201: Context Window](../../phase4-quantization/4200-kv-cache/4201-Context-Window-Physics.md)
- [6202: Re-ranking](../6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md)

---

## Next Steps

- Continue with: **[6401: Qdrant Setup](./../6400-vector-databases/6401-Qdrant-Setup.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Experiment: **[EXP_6302: CAG](../../../../experiments/EXP_6302_CAG.md)**
