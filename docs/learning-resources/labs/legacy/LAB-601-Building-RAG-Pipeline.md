# LAB-601: Building a RAG Pipeline

## Overview
Build a complete Retrieval Augmented Generation system from scratch.

## Prerequisites
- LAB-201 completed
- Understanding of embeddings (6100)
- Vector database basics (6400)

## Setup

```bash
pip install torch transformers sentence-transformers qdrant-client fastapi
```

## Exercise 1: Create Embeddings

```python
from sentence_transformers import SentenceTransformer

# TODO: Load embedding model
embedder = SentenceTransformer('all-MiniLM-L6-v2')

# Sample documents
documents = [
    "Paris is the capital of France.",
    "London is the capital of the United Kingdom.",
    "Berlin is the capital of Germany.",
    "Madrid is the capital of Spain.",
    "Rome is the capital of Italy.",
]

# TODO: Create embeddings
embeddings = embedder.encode(documents)

print(f"Document count: {len(documents)}")
print(f"Embedding shape: {embeddings.shape}")  # [5, 384]
print(f"Embedding dim: {embeddings.shape[1]}")
```

## Exercise 2: Setup Vector Database

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# TODO: Initialize Qdrant
client = QdrantClient(url="http://localhost:6333")

# TODO: Create collection
collection_name = "rag_demo"

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
)

# TODO: Insert documents
points = [
    PointStruct(
        id=i,
        vector=embeddings[i].tolist(),
        payload={"text": documents[i]}
    )
    for i in range(len(documents))
]

client.upsert(
    collection_name=collection_name,
    points=points
)

print(f"Inserted {len(points)} points")
```

## Exercise 3: Retrieve Relevant Documents

```python
def retrieve(query, top_k=3):
    """
    Retrieve relevant documents for query.

    Args:
        query: Query string
        top_k: Number of results

    Returns:
        List of (document, score) tuples
    """
    # TODO: Embed query
    query_embedding = embedder.encode(query)

    # TODO: Search in Qdrant
    results = client.search(
        collection_name=collection_name,
        query_vector=query_embedding.tolist(),
        limit=top_k
    )

    # Extract documents and scores
    retrieved = [
        (result.payload["text"], result.score)
        for result in results
    ]

    return retrieved

# Test
query = "What is the capital of France?"
results = retrieve(query)

print(f"\nQuery: {query}")
print("Retrieved documents:")
for doc, score in results:
    print(f"  [{score:.3f}] {doc}")
```

## Exercise 4: Generate with Context

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# TODO: Load generation model
gen_model_name = "gpt2"  # or "meta-llama/Llama-2-7b-hf"
gen_model = AutoModelForCausalLM.from_pretrained(gen_model_name)
gen_tokenizer = AutoTokenizer.from_pretrained(gen_model_name)
gen_tokenizer.pad_token = gen_tokenizer.eos_token

def generate_with_context(query, context):
    """
    Generate response using retrieved context.

    Args:
        query: User query
        context: Retrieved documents

    Returns:
        Generated response
    """
    # TODO: Create prompt with context
    context_str = "\n".join([f"- {doc}" for doc, _ in context])
    prompt = f"""Context:
{context_str}

Question: {query}

Answer:"""

    # TODO: Generate
    inputs = gen_tokenizer(prompt, return_tensors="pt")
    outputs = gen_model.generate(
        **inputs,
        max_new_tokens=50,
        temperature=0.7
    )

    response = gen_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return response

# Test
query = "What is the capital of France?"
context = [doc for doc, _ in retrieve(query)]

response = generate_with_context(query, context)
print(f"\nQuery: {query}")
print(f"Response: {response}")
```

## Exercise 5: Complete RAG Pipeline

```python
class RAGPipeline:
    def __init__(self, collection_name, embedder_model, gen_model_name):
        # TODO: Initialize components
        self.embedder = SentenceTransformer(embedder_model)
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = collection_name

        self.gen_model = AutoModelForCausalLM.from_pretrained(gen_model_name)
        self.gen_tokenizer = AutoTokenizer.from_pretrained(gen_model_name)
        self.gen_tokenizer.pad_token = self.gen_tokenizer.eos_token

    def retrieve(self, query, top_k=3):
        """Retrieve relevant documents."""
        query_embedding = self.embedder.encode(query)
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k
        )
        return [result.payload["text"] for result in results]

    def generate(self, query, context):
        """Generate response with context."""
        context_str = "\n".join([f"- {doc}" for doc in context])
        prompt = f"Context:\n{context_str}\n\nQuestion: {query}\n\nAnswer:"

        inputs = self.gen_tokenizer(prompt, return_tensors="pt")
        outputs = self.gen_model.generate(
            **inputs,
            max_new_tokens=100,
            temperature=0.7
        )

        return self.gen_tokenizer.decode(outputs[0], skip_special_tokens=True)

    def query(self, question, top_k=3):
        """Complete RAG query."""
        # Retrieve
        context = self.retrieve(question, top_k=top_k)

        # Generate
        response = self.generate(question, context)

        return {
            "question": question,
            "context": context,
            "answer": response
        }

# TODO: Test pipeline
rag = RAGPipeline(
    collection_name="rag_demo",
    embedder_model="all-MiniLM-L6-v2",
    gen_model_name="gpt2"
)

result = rag.query("What is the capital of Germany?")
print(f"\nQuestion: {result['question']}")
print(f"Context: {result['context']}")
print(f"Answer: {result['answer']}")
```

## Exercise 6: Add Document

```python
def add_document(text):
    """Add a new document to the RAG system."""
    # TODO: Embed
    embedding = embedder.encode(text)

    # TODO: Get next ID
    collection_info = client.get_collection(collection_name)
    next_id = collection_info.points_count + 1

    # TODO: Insert
    point = PointStruct(
        id=next_id,
        vector=embedding.tolist(),
        payload={"text": text}
    )

    client.upsert(
        collection_name=collection_name,
        points=[point]
    )

    print(f"Added document with ID: {next_id}")

# Test
add_document("Amsterdam is the capital of the Netherlands.")
result = rag.query("What is the capital of the Netherlands?")
print(f"\nNew question answer: {result['answer']}")
```

## Expected Outputs

1. Exercise 1: Embeddings [5, 384]
2. Exercise 2: 5 points inserted
3. Exercise 3: Retrieved documents with scores
4. Exercise 4: Context-aware generation
5. Exercise 5: Complete pipeline working
6. Exercise 6: New document retrievable

## Troubleshooting

**Issue:** Qdrant connection error
```python
# Solution: Ensure Qdrant is running
# docker run -p 6333:6333 qdrant/qdrant
```

**Issue:** Poor retrieval
```python
# Solution: Try different embedding model
embedder = SentenceTransformer('all-mpnet-base-v2')
```

**Issue:** Generation ignores context
```python
# Solution: Improve prompt formatting
prompt = f"Using ONLY this context:\n{context_str}\n\nAnswer: {query}"
```

## Extensions

1. Add re-ranking
2. Implement hybrid search (vector + keyword)
3. Add citation sources
4. Handle multi-turn conversations
5. Add streaming responses

## Time Estimate: 4-5 hours

---

**Last Updated:** 2026-02-04
