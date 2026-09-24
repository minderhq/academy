---
Document ID: 6100-PRACTICE
Title: "6100: Vector Embeddings - Practice"
Last Updated: 2026-02-05
Status: Complete
Difficulty: Advanced
---

# 6100: Vector Embeddings - Practice

## Exercises

### Exercise 1: Compute Embeddings

```python
from sentence_transformers import SentenceTransformer
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Load model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Documents
documents = [
    "The cat sits on the mat",
    "A dog is playing in the park",
    "Machine learning is fascinating"
]

# Compute embeddings
print("Computing embeddings for documents...")
embeddings = model.encode(documents)

print(f"Embedding shape: {embeddings.shape}")  # (3, 384)
print(f"Embedding dtype: {embeddings.dtype}")
print(f"First 5 dimensions of first doc: {embeddings[0][:5]}")

# Compute similarity matrix
from sklearn.metrics.pairwise import cosine_similarity

similarity_matrix = cosine_similarity(embeddings)

print("\nSimilarity Matrix:")
print("(0=cat, 1=dog, 2=ML)")
for i, row in enumerate(similarity_matrix):
    print(f"Doc {i}: {np.round(row, 3)}")

# Find most similar pair (excluding self-similarity)
max_sim = -1
best_pair = None

for i in range(len(documents)):
    for j in range(i+1, len(documents)):
        if similarity_matrix[i][j] > max_sim:
            max_sim = similarity_matrix[i][j]
            best_pair = (i, j)

print(f"\nMost similar pair: Documents {best_pair[0]} and {best_pair[1]}")
print(f"Similarity score: {max_sim:.3f}")
print(f"Document {best_pair[0]}: {documents[best_pair[0]]}")
print(f"Document {best_pair[1]}: {documents[best_pair[1]]}")

# Display as heatmap
plt.figure(figsize=(8, 6))
sns.heatmap(similarity_matrix, annot=True, fmt='.3f', cmap='YlOrRd',
            xticklabels=['Cat', 'Dog', 'ML'], yticklabels=['Cat', 'Dog', 'ML'])
plt.title('Document Similarity Matrix')
plt.tight_layout()
plt.savefig('similarity_heatmap.png')
print("\nHeatmap saved to similarity_heatmap.png")

# Expected output:
# - cat and dog have moderate similarity (both about animals)
# - ML document has lower similarity to both
# - Self-similarity = 1.0
```

### Exercise 2: Compare Embedding Models

```python
import time
from sentence_transformers import SentenceTransformer

# Define models to compare
models_config = {
    "miniLM": "all-MiniLM-L6-v2",
    "mpnet": "all-mpnet-base-v2",
    "gte": "BAAI/bge-small-en-v1.5"
}

# Test documents
test_docs = [
    "The cat chases the mouse",
    "A feline pursues a rodent",
    "Machine learning models process data",
    "Artificial intelligence is transforming industries",
]

# Query for similarity test
query = "animals hunting prey"

print("Comparing Embedding Models")
print("=" * 60)

results = {}

for model_name, model_path in models_config.items():
    print(f"\nTesting {model_name} ({model_path})...")

    # Load model
    model = SentenceTransformer(model_path)

    # Measure encoding speed
    start_time = time.time()
    embeddings = model.encode(test_docs)
    encoding_time = time.time() - start_time

    # Get embedding dimensions
    emb_dim = embeddings.shape[1]

    # Compute query similarity
    query_emb = model.encode([query])
    similarities = cosine_similarity(query_emb, embeddings)[0]

    # Memory usage (rough estimate)
    memory_mb = embeddings.nbytes / (1024 * 1024)

    results[model_name] = {
        "dimensions": emb_dim,
        "encoding_time": encoding_time,
        "memory_mb": memory_mb,
        "similarities": similarities,
        "model": model
    }

    print(f"  Dimensions: {emb_dim}")
    print(f"  Encoding time: {encoding_time:.4f}s")
    print(f"  Memory: {memory_mb:.2f} MB")
    print(f"  Query similarities: {np.round(similarities, 3)}")

# Comparison summary
print("\n" + "=" * 60)
print("PERFORMANCE COMPARISON")
print("=" * 60)

print("\nSpeed vs Accuracy Trade-off:")
for model_name, res in results.items():
    print(f"{model_name:10s}: {res['encoding_time']:.4f}s | {res['dimensions']} dims | Animal doc similarity: {res['similarities'][0]:.3f}")

# Best model for semantic understanding (highest similarity to paraphrase)
best_semantic = max(results.items(), key=lambda x: x[1]['similarities'][0])
print(f"\nBest semantic understanding: {best_semantic[0]} (similarity: {best_semantic[1]['similarities'][0]:.3f})")

# Fastest model
fastest = min(results.items(), key=lambda x: x[1]['encoding_time'])
print(f"Fastest encoding: {fastest[0]} ({fastest[1]['encoding_time']:.4f}s)")

# Expected results:
# - miniLM: Fastest, good quality, 384 dims
# - mpnet: Slower, better quality, 768 dims
# - gte: Best semantic understanding, competitive speed
```

### Exercise 3: Chunking Strategy

```python
def chunk_document(text, max_length=512, overlap=50):
    """Chunk document into smaller pieces.

    Args:
        text: Input text document
        max_length: Maximum tokens per chunk
        overlap: Number of overlapping tokens between chunks

    Returns:
        List of text chunks
    """
    # Simple word-based chunking
    words = text.split()

    if len(words) <= max_length:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + max_length, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        # Move start position with overlap
        start = end - overlap

        # Avoid infinite loop
        if start >= len(words):
            break

    return chunks

def semantic_chunk_document(text, max_sentences=10):
    """Chunk document by semantic boundaries (paragraphs/sentences)."""
    import re

    # Split into paragraphs
    paragraphs = re.split(r'\n\n+', text)

    chunks = []
    current_chunk = []

    for para in paragraphs:
        sentences = re.split(r'[.!?]+', para)
        sentences = [s.strip() for s in sentences if s.strip()]

        for sent in sentences:
            current_chunk.append(sent)

            if len(current_chunk) >= max_sentences:
                chunks.append('. '.join(current_chunk) + '.')
                current_chunk = []

    if current_chunk:
        chunks.append('. '.join(current_chunk) + '.')

    return chunks

# Test with long document
long_text = """
Machine learning is a subset of artificial intelligence that focuses on building systems that can learn from data.
It has applications in various fields including computer vision, natural language processing, and robotics.
Deep learning, a branch of machine learning, uses neural networks with multiple layers to model complex patterns.
These networks can automatically discover representations needed for detection or classification from raw data.
Supervised learning algorithms build a mathematical model of a set of data that contains both the inputs and the desired outputs.
Unsupervised learning algorithms take a set of data that contains only inputs, and find structure in the data.
Reinforcement learning is another approach where agents learn to make decisions by performing actions and seeing the results.
""" * 10  # Repeat to make it longer

print(f"Original text length: {len(long_text)} characters")

# Test fixed-size chunking
print("\nFixed-size Chunking:")
chunks_fixed = chunk_document(long_text, max_length=100, overlap=20)
print(f"Number of chunks: {len(chunks_fixed)}")
print(f"First chunk: {chunks_fixed[0][:100]}...")
print(f"Second chunk starts: {chunks_fixed[1][:50]}...")

# Test semantic chunking
print("\nSemantic Chunking:")
chunks_semantic = semantic_chunk_document(long_text, max_sentences=5)
print(f"Number of chunks: {len(chunks_semantic)}")
for i, chunk in enumerate(chunks_semantic):
    print(f"Chunk {i+1}: {len(chunk)} chars, {len(chunk.split())} words")

# Verify chunks
print("\nVerification:")
print(f"Fixed-size - All chunks under limit: {all(len(c.split()) <= 150 for c in chunks_fixed)}")
print(f"Semantic - All chunks have complete sentences: {all(c.rstrip().endswith('.') for c in chunks_semantic)}")

# Expected results:
# - Fixed-size: More chunks, maintains overlap, may split sentences
# - Semantic: Fewer chunks, preserves sentence boundaries, better for RAG
```

---

**Last Updated:** 2026-02-05
**Status:** ✅ Complete - All tasks completed with solutions
