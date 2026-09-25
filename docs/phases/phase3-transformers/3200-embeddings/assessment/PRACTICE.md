---
Document ID: 3200-PRACTICE
Title: "3200: Embeddings - Practice"
Last Updated: 2026-09-25
Status: Complete
Difficulty: Advanced
---

# 3200: Embeddings - Practice

## Exercises

### Exercise 1: Word2Vec Training

```python
from gensim.models import Word2Vec

# Prepare training sentences
# The corpus must contain every word the tests below query: only
# plural 'dogs'/'cats' existed before, so similarity('cat', 'dog')
# raised KeyError, and the analogy words (king/man/woman) were not
# in the vocabulary at all
sentences = [
    ['the', 'cat', 'sits', 'on', 'the', 'mat'],
    ['the', 'dog', 'is', 'a', 'loyal', 'pet'],
    ['dogs', 'are', 'loyal', 'animals'],
    ['paris', 'is', 'the', 'capital', 'of', 'france'],
    ['london', 'is', 'in', 'england'],
    ['cats', 'and', 'dogs', 'are', 'pets'],
    ['france', 'is', 'in', 'europe'],
    ['the', 'king', 'is', 'the', 'ruler', 'of', 'the', 'country'],
    ['the', 'queen', 'is', 'the', 'wife', 'of', 'the', 'king'],
    ['a', 'man', 'and', 'a', 'woman', 'walked', 'in', 'the', 'park'],
] * 100  # Repeat for better training

# Train Word2Vec model
model = Word2Vec(
    sentences=sentences,
    vector_size=100,      # Dimensionality of embeddings
    window=5,             # Context window size
    min_count=1,          # Minimum word frequency
    epochs=10,            # Training epochs
    sg=0,                 # 0=CBOW, 1=Skip-gram
    workers=4             # Parallel workers
)

# Test similarity between words
try:
    similarity = model.wv.similarity('cat', 'dog')
    print(f"Cat-Dog similarity: {similarity:.4f}")

    similarity2 = model.wv.similarity('cat', 'paris')
    print(f"Cat-Paris similarity: {similarity2:.4f}")

    similarity3 = model.wv.similarity('france', 'paris')
    print(f"France-Paris similarity: {similarity3:.4f}")
except KeyError as e:
    print(f"Word not in vocabulary: {e}")

# Test analogies
try:
    result = model.wv.most_similar(
        positive=['king', 'woman'],
        negative=['man'],
        topn=3
    )
    print("\nKing - Man + Woman:")
    for word, score in result:
        print(f"  {word}: {score:.4f}")
except KeyError as e:
    print(f"Analogy words not in vocabulary: {e}")

# Find most similar words
try:
    print("\nMost similar to 'cat':")
    similar_words = model.wv.most_similar('cat', topn=5)
    for word, score in similar_words:
        print(f"  {word}: {score:.4f}")
except KeyError as e:
    print(f"Word 'cat' not in vocabulary: {e}")

# Get embedding vector
try:
    cat_vector = model.wv['cat']
    print(f"\n'cat' embedding shape: {cat_vector.shape}")
    print(f"First 5 dimensions: {cat_vector[:5]}")
except KeyError as e:
    print(f"Word not in vocabulary: {e}")

# Save model
model.save("word2vec.model")
print("\nModel saved to 'word2vec.model'")

# Expected Output (values are NOT reproducible on this toy corpus -
# random initialization over ~10 distinct sentences makes every run
# differ; read the qualitative direction, not the numbers):
# - Cat-Dog and France-Paris similarities tend to run higher than
#   Cat-Paris (shared context vs. unrelated words)
# - The King - Man + Woman analogy prints neighbors, but at this
#   corpus size the result is illustrative, not reliable - real
#   analogy quality needs orders of magnitude more text
# - Most similar to 'cat': co-occurring words (cats/dogs, pets,
#   mat, sits) dominate
```

**Explanation:**
- Word2Vec learns word representations from context
- CBOW predicts target word from context
- Skip-gram predicts context from target word
- Analogies demonstrate captured semantic relationships

**Troubleshooting Tips:**
- Increase epochs or data if similarities are low
- Use larger vector_size (100-300) for better quality
- Ensure min_count isn't filtering out important words
- More training data = better embeddings

---

### Exercise 2: Sentence Embeddings

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Load pre-trained sentence transformer model
# Options: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'paraphrase-MiniLM-L6-v2'
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create sentence embeddings
sentences = [
    "The cat sits on the mat.",
    "A dog is playing in the park.",
    "Paris is the capital of France.",
    "A kitten is resting on the rug.",
    "France is a country in Europe.",
    "The feline is sleeping on the carpet."
]

print("Encoding sentences...")
embeddings = model.encode(sentences)

print(f"Embedding shape: {embeddings.shape}")
print(f"Each sentence is a {embeddings.shape[1]}-dimensional vector")

# Compute similarity matrix
similarity_matrix = cosine_similarity(embeddings)

print("\nSimilarity Matrix:")
print("(Rows and columns correspond to sentences in order)")
for i, sent1 in enumerate(sentences):
    for j, sent2 in enumerate(sentences):
        if i < j:  # Only print upper triangle to avoid duplicates
            print(f"\"{sent1[:30]}...\" <-> \"{sent2[:30]}...\": {similarity_matrix[i][j]:.4f}")

# Visualize similarity matrix
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 8))
sns.heatmap(
    similarity_matrix,
    annot=True,
    fmt=".2f",
    cmap='YlOrRd',
    xticklabels=[s[:20] + "..." for s in sentences],
    yticklabels=[s[:20] + "..." for s in sentences]
)
plt.title("Sentence Similarity Matrix")
plt.xticks(rotation=45, ha='right')
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# Find most similar pairs
def find_most_similar_pairs(sentences, embeddings, top_k=3):
    """Find the top-k most similar sentence pairs."""
    similarities = cosine_similarity(embeddings)

    # Get upper triangle (excluding diagonal)
    pairs = []
    for i in range(len(sentences)):
        for j in range(i+1, len(sentences)):
            pairs.append((i, j, similarities[i][j]))

    # Sort by similarity
    pairs.sort(key=lambda x: x[2], reverse=True)

    return pairs[:top_k]

print("\nTop 3 Most Similar Pairs:")
top_pairs = find_most_similar_pairs(sentences, embeddings, top_k=3)
for i, j, sim in top_pairs:
    print(f"{sim:.4f}: \"{sentences[i]}\" <-> \"{sentences[j]}\"")

# Expected Output:
# High similarity (>0.7) between semantically similar sentences
# Low similarity (<0.3) between unrelated sentences
# Example: "cat sits on mat" ~ "kitten resting on rug" (both about cats on surfaces)
```

**Explanation:**
- Sentence transformers create fixed-size embeddings for variable-length text
- Based on BERT architecture with fine-tuning for similarity tasks
- Cosine similarity measures semantic relatedness

**Use Cases:**
- Semantic search
- Document clustering
- Duplicate detection
- Recommendation systems

---

### Exercise 3: BERT Embeddings

```python
from transformers import AutoModel, AutoTokenizer
import torch

# Load BERT model and tokenizer
model_name = "bert-base-uncased"
print(f"Loading {model_name}...")

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModel.from_pretrained(model_name)

# Ensure model is in eval mode
model.eval()

# Get embeddings for a sentence
text = "The capital of France is Paris."
print(f"\nProcessing: \"{text}\"")

# Tokenize and encode
inputs = tokenizer(
    text,
    return_tensors="pt",
    padding=True,
    truncation=True,
    max_length=512
)

print(f"Input IDs shape: {inputs['input_ids'].shape}")
print(f"Attention mask shape: {inputs['attention_mask'].shape}")

# Show tokenization
tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'][0])
print(f"\nTokens: {tokens}")

# Get embeddings
with torch.no_grad():
    outputs = model(**inputs)

# Extract different types of embeddings
last_hidden = outputs.last_hidden_state  # (batch, seq_len, hidden_size)
pooler_output = outputs.pooler_output     # (batch, hidden_size)

# Method 1: Mean pooling (average of all token embeddings)
mean_pooled = last_hidden.mean(dim=1)

# Method 2: CLS token embedding (first token)
cls_token = last_hidden[:, 0, :]

# Method 3: Max pooling
max_pooled, _ = last_hidden.max(dim=1)

print(f"\nEmbedding shapes:")
print(f"  Last hidden state: {last_hidden.shape}")
print(f"  Mean pooled: {mean_pooled.shape}")
print(f"  CLS token: {cls_token.shape}")
print(f"  Max pooled: {max_pooled.shape}")
print(f"  Pooler output: {pooler_output.shape}")

# Compare multiple sentences
sentences = [
    "The capital of France is Paris.",
    "Paris is the capital of France.",
    "The capital of Germany is Berlin.",
    "I like eating pizza."
]

print("\n\nProcessing multiple sentences:")
inputs = tokenizer(
    sentences,
    return_tensors="pt",
    padding=True,
    truncation=True,
    max_length=512
)

with torch.no_grad():
    outputs = model(**inputs)
    # Masked mean pooling: the batch is padded, so a plain mean over
    # dim=1 would dilute short sentences with PAD-token outputs.
    # Weight each token by the attention mask before averaging
    mask = inputs['attention_mask'].unsqueeze(-1).float()
    embeddings = (outputs.last_hidden_state * mask).sum(dim=1) / mask.sum(dim=1)

# Compute similarities
similarities = cosine_similarity(embeddings.numpy())

print("\nSimilarity Matrix:")
for i, s1 in enumerate(sentences):
    for j, s2 in enumerate(sentences):
        if i < j:
            print(f"  [{similarities[i][j]:.3f}] \"{s1[:30]}\" <-> \"{s2[:30]}\"")

# Expected Output:
# High similarity (>0.8) between sentences with same meaning (regardless of order)
# Lower similarity between semantically different sentences
```

**Explanation:**
- BERT provides contextualized word embeddings
- Each token's embedding depends on entire context
- Multiple pooling strategies for sentence-level representation

**Pooling Strategies:**
1. **CLS token**: Special first token, trained for classification
2. **Mean pooling**: Average of all token embeddings
3. **Max pooling**: Maximum value across each dimension

---

### Exercise 4: Embedding Visualization

```python
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import numpy as np

# Use embeddings from Exercise 2 or 3
# Here we'll use sentence embeddings
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('all-MiniLM-L6-v2')

sentences = [
    # Animals
    "cat", "dog", "bird", "fish", "horse",
    # Foods
    "pizza", "burger", "salad", "pasta", "soup",
    # Locations
    "Paris", "London", "Tokyo", "Berlin", "Rome",
    # Technology
    "computer", "phone", "internet", "software", "hardware",
    # Emotions
    "happy", "sad", "angry", "excited", "calm"
]

# Create embeddings
embeddings = model.encode(sentences)
print(f"Original embedding shape: {embeddings.shape}")

# Method 1: PCA (faster, linear)
print("\nPerforming PCA...")
pca_embeddings = PCA(n_components=2).fit_transform(embeddings)
print(f"PCA reduced shape: {pca_embeddings.shape}")

# Method 2: t-SNE (slower, non-linear, better visualization)
print("Performing t-SNE...")
tsne_embeddings = TSNE(
    n_components=2,
    perplexity=5,  # Lower for small datasets
    random_state=42,
    max_iter=1000  # renamed from n_iter in scikit-learn 1.5
).fit_transform(embeddings)
print(f"t-SNE reduced shape: {tsne_embeddings.shape}")

# Create color labels
colors = ['red'] * 5 + ['blue'] * 5 + ['green'] * 5 + ['orange'] * 5 + ['purple'] * 5
labels = ['Animals'] * 5 + ['Foods'] * 5 + ['Locations'] * 5 + ['Technology'] * 5 + ['Emotions'] * 5

# Plot PCA
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# PCA plot
for category in set(labels):
    mask = [l == category for l in labels]
    ax1.scatter(
        pca_embeddings[mask, 0],
        pca_embeddings[mask, 1],
        label=category,
        alpha=0.7,
        s=100
    )

# Add labels
for i, word in enumerate(sentences):
    ax1.annotate(word, (pca_embeddings[i, 0], pca_embeddings[i, 1]),
                 fontsize=8, ha='center', va='center')

ax1.set_title("PCA Visualization of Embeddings")
ax1.set_xlabel("PC1")
ax1.set_ylabel("PC2")
ax1.legend()
ax1.grid(True, alpha=0.3)

# t-SNE plot
for category in set(labels):
    mask = [l == category for l in labels]
    ax2.scatter(
        tsne_embeddings[mask, 0],
        tsne_embeddings[mask, 1],
        label=category,
        alpha=0.7,
        s=100
    )

for i, word in enumerate(sentences):
    ax2.annotate(word, (tsne_embeddings[i, 0], tsne_embeddings[i, 1]),
                 fontsize=8, ha='center', va='center')

ax2.set_title("t-SNE Visualization of Embeddings")
ax2.set_xlabel("Dimension 1")
ax2.set_ylabel("Dimension 2")
ax2.legend()
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

# 3D visualization
fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111, projection='3d')

pca_3d = PCA(n_components=3).fit_transform(embeddings)

for category in set(labels):
    mask = [l == category for l in labels]
    ax.scatter(
        pca_3d[mask, 0],
        pca_3d[mask, 1],
        pca_3d[mask, 2],
        label=category,
        alpha=0.7,
        s=100
    )

ax.set_title("3D PCA Visualization")
ax.set_xlabel("PC1")
ax.set_ylabel("PC2")
ax.set_zlabel("PC3")
ax.legend()
plt.show()

print("\nInterpretation:")
print("- Similar words cluster together")
print("- Different categories should be separated")
print("- t-SNE often shows better separation than PCA")

# Expected Output:
# Original embedding shape: (25, 384)
# PCA reduced shape: (25, 2)
# t-SNE reduced shape: (25, 2)
# - Two side-by-side scatter plots (PCA and t-SNE), each point
#   annotated with its word, plus a 3D PCA figure
# - Same-category words (animals, foods, ...) form loose clusters
```

**Explanation:**
- Dimensionality reduction visualizes high-dimensional embeddings
- PCA: linear, faster, preserves global structure
- t-SNE: non-linear, slower, preserves local neighborhoods
- Clusters reveal semantic relationships

---

### Exercise 5: Similarity Search

```python
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def find_most_similar(query, documents, embedder, top_k=3):
    """
    Find most similar documents to query using cosine similarity.

    Args:
        query: Search query string
        documents: List of document strings
        embedder: SentenceTransformer model
        top_k: Number of results to return

    Returns:
        List of (document, score) tuples sorted by similarity
    """
    # Embed query and documents
    query_embedding = embedder.encode([query])
    doc_embeddings = embedder.encode(documents)

    # Compute cosine similarities
    similarities = cosine_similarity(query_embedding, doc_embeddings)[0]

    # Get top-k indices
    top_indices = similarities.argsort()[-top_k:][::-1]

    # Return results with scores
    results = [
        {
            'document': documents[i],
            'score': similarities[i],
            'index': i
        }
        for i in top_indices
    ]

    return results

# Alternative implementation with caching for efficiency
class SemanticSearchEngine:
    """Efficient semantic search with pre-computed embeddings."""

    def __init__(self, embedder_model='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(embedder_model)
        self.documents = []
        self.embeddings = None

    def index_documents(self, documents):
        """Pre-compute embeddings for all documents."""
        self.documents = documents
        self.embeddings = self.model.encode(documents)
        print(f"Indexed {len(documents)} documents")

    def search(self, query, top_k=5):
        """Search indexed documents."""
        if self.embeddings is None:
            raise ValueError("No documents indexed. Call index_documents() first.")

        query_embedding = self.model.encode([query])
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]

        top_indices = similarities.argsort()[-top_k:][::-1]

        results = [
            {
                'document': self.documents[i],
                'score': similarities[i],
                'rank': rank + 1
            }
            for rank, i in enumerate(top_indices)
        ]

        return results

# Test the search engine
print("Creating document corpus...")
documents = [
    "Machine learning is a subset of artificial intelligence.",
    "Deep learning uses neural networks with multiple layers.",
    "Paris is the capital and largest city of France.",
    "Python is a high-level programming language.",
    "Natural language processing deals with text and speech.",
    "Computer vision enables machines to interpret visual information.",
    "Reinforcement learning trains agents through reward systems.",
    "The Eiffel Tower is a famous landmark in Paris.",
    "JavaScript is commonly used for web development.",
    "Transformers are neural network architectures for sequence modeling.",
    "France is located in Western Europe.",
    "Supervised learning uses labeled data for training.",
]

# Initialize search engine
search_engine = SemanticSearchEngine()
search_engine.index_documents(documents)

# Test queries
test_queries = [
    "AI and neural networks",
    "Paris France",
    "programming languages",
    "deep learning models"
]

print("\n" + "="*60)
print("SEMANTIC SEARCH RESULTS")
print("="*60)

for query in test_queries:
    print(f"\nQuery: \"{query}\"")
    print("-" * 60)
    results = search_engine.search(query, top_k=3)

    for result in results:
        print(f"{result['rank']}. [{result['score']:.4f}] {result['document']}")

# Advanced: Add threshold filtering
def search_with_threshold(search_engine, query, threshold=0.4, max_results=10):
    """Search with similarity threshold."""
    query_embedding = search_engine.model.encode([query])
    similarities = cosine_similarity(query_embedding, search_engine.embeddings)[0]

    # Filter by threshold
    valid_indices = np.where(similarities >= threshold)[0]

    # Sort by similarity
    sorted_indices = valid_indices[similarities[valid_indices].args()[::-1]]

    results = [
        {
            'document': search_engine.documents[i],
            'score': similarities[i],
            'index': i
        }
        for i in sorted_indices[:max_results]
    ]

    return results

print("\n\n" + "="*60)
print("THRESHOLD-BASED SEARCH (threshold=0.5)")
print("="*60)

query = "artificial intelligence"
results = search_with_threshold(search_engine, query, threshold=0.5)

print(f"\nQuery: \"{query}\"")
if results:
    for result in results:
        print(f"[{result['score']:.4f}] {result['document']}")
else:
    print("No documents met the similarity threshold.")

# Expected Output:
# Query "AI and neural networks" returns documents about ML, deep learning, neural networks
# Query "Paris France" returns documents about Paris, France, Eiffel Tower
# Query "programming languages" returns documents about Python, JavaScript
# High similarity scores (>0.6) indicate strong semantic match
```

**Explanation:**
- Semantic search finds meaning-based matches, not keyword matches
- Pre-computing embeddings enables fast querying
- Cosine similarity measures semantic relatedness
- Threshold filtering ensures quality results

**Performance Tips:**
- Pre-compute embeddings for static document sets
- Use approximate nearest neighbor (ANN) for large datasets
- Consider FAISS or Milvus for production systems

---

## Bonus: Embedding Comparison

```python
def compare_embedding_methods():
    """Compare different embedding approaches."""

    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer, AutoModel
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt

    # Sample sentences
    sentences = [
        "The cat sat on the mat.",
        "A kitten rested on the rug.",
        "Dogs are loyal pets.",
        "Canines are faithful companions.",
        "Paris is in France.",
        "The French capital is Paris."
    ]

    # Method 1: Sentence Transformer (fine-tuned for similarity)
    st_model = SentenceTransformer('all-MiniLM-L6-v2')
    st_embeddings = st_model.encode(sentences)

    # Method 2: BERT mean pooling
    bert_tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
    bert_model = AutoModel.from_pretrained('bert-base-uncased')

    bert_embeddings = []
    for sent in sentences:
        inputs = bert_tokenizer(sent, return_tensors='pt', truncation=True, padding=True)
        with torch.no_grad():
            outputs = bert_model(**inputs)
        emb = outputs.last_hidden_state.mean(dim=1).numpy()
        bert_embeddings.append(emb[0])
    bert_embeddings = np.array(bert_embeddings)

    # Compute similarity matrices
    st_sim = cosine_similarity(st_embeddings)
    bert_sim = cosine_similarity(bert_embeddings)

    print("Sentence Transformer Similarities:")
    print(st_sim.round(3))
    print("\nBERT Mean Pooling Similarities:")
    print(bert_sim.round(3))

    # Visualize comparison
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    sns.heatmap(st_sim, ax=axes[0], annot=True, fmt='.2f', cmap='YlOrRd',
                xticklabels=[s[:20]+'...' for s in sentences],
                yticklabels=[s[:20]+'...' for s in sentences])
    axes[0].set_title('Sentence Transformer')

    sns.heatmap(bert_sim, ax=axes[1], annot=True, fmt='.2f', cmap='YlOrRd',
                xticklabels=[s[:20]+'...' for s in sentences],
                yticklabels=[s[:20]+'...' for s in sentences])
    axes[1].set_title('BERT Mean Pooling')

    plt.tight_layout()
    plt.show()

    print("\nObservation:")
    print("- Sentence Transformer generally shows higher contrast")
    print("- Better tuned for semantic similarity tasks")
    print("- BERT embeddings more general-purpose")

# Run comparison
compare_embedding_methods()

# Expected Output:
# - Two 6x6 similarity matrices printed to the console (exact
#   values vary by model version), then two side-by-side heatmaps
# - Sentence Transformer matrix: similar pairs near 0.6-0.8,
#   unrelated pairs near 0.0-0.2 - higher contrast than BERT
```

**Key Takeaways:**

1. **Word2Vec**: Fast word-level embeddings, good for simple tasks
2. **Sentence Transformers**: State-of-the-art for sentence similarity
3. **BERT**: Contextual embeddings, good for many NLP tasks
4. **Visualization**: Essential for understanding embedding quality
5. **Search**: Semantic search beats keyword search for meaning
