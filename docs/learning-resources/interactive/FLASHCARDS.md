---
Document ID: FLASHCARDS
Title: "Minder Academy: Interactive Learning Components"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['flashcards', 'llm', 'practice']
---

# Minder Academy: Interactive Learning Components

Interactive elements to enhance the learning experience.

## Flashcards

Use flashcards for quick recall of key concepts.

### Phase 1: Infrastructure
```yaml
CARD-1100-001:
  front: "What is the purpose of VLAN tagging?"
  back: "VLAN tagging allows multiple virtual networks to share a single physical network cable by adding a tag to each frame that identifies which VLAN it belongs to."
  tags: [network, vlan, tagging]

CARD-1100-002:
  front: "What is the difference between GPON and EPON?"
  back: "GPON (Gigabit Passive Optical Network) uses ATM/GEM framing and supports 2.5 Gbps downstream. EPON (Ethernet Passive Optical Network) uses standard Ethernet frames and supports 1.25 Gbps symmetric."
  tags: [network, fiber, gpon, epon]
```

### Phase 3: Transformers
```yaml
CARD-3100-001:
  front: "What is self-attention?"
  back: "Self-attention is a mechanism that allows each token in a sequence to attend to all other tokens, computing a weighted sum of their representations to capture contextual relationships."
  tags: [attention, transformers]

CARD-3100-002:
  front: "What are Q, K, V in attention?"
  back: "Query (Q): What the current token is looking for. Key (K): What other tokens offer. Value (V): The actual information content. Attention(Q,K,V) = softmax(QK^T/√d_k)V"
  tags: [attention, qkv, transformers]
```

## Quizzes

Interactive quizzes for self-assessment.

### Quick Quiz Format
```markdown
## Quiz: Transformer Architecture

**Question 1:** What is the purpose of positional encoding?

A) [ ] To add memory to the network
B) [ ] To provide position information since self-attention is permutation invariant
C) [ ] To increase model capacity
D) [ ] To regularize the model

**Answer:** B

**Explanation:** Self-attention processes all tokens in parallel and doesn't inherently know about position. Positional encodings add position information using sine/cosine functions or learned embeddings.

---

**Question 2:** What is the main difference between BERT and GPT?

A) [ ] BERT uses CNN, GPT uses RNN
B) [ ] BERT is encoder-only, GPT is decoder-only
C) [ ] BERT is for images, GPT is for text
D) [ ] No difference

**Answer:** B

**Explanation:** BERT uses only the encoder stack (bidirectional attention), while GPT uses only the decoder stack (causal/masked attention).
```

## Code Challenges

Hands-on coding exercises.

### Challenge Levels
```yaml
CHALLENGE-201-001:
  title: "Build a ReLU Activation"
  difficulty: "Beginner"
  time_estimate: "15 minutes"
  description: "Implement the ReLU activation function from scratch"
  starter_code: |
    def relu(x):
        # TODO: Implement ReLU
        # ReLU(x) = max(0, x)
        pass
  tests:
    - assert relu(-5) == 0
    - assert relu(5) == 5
    - assert relu(0) == 0
  hints:
    - "Use the max() function"
    - "Remember: ReLU returns 0 for negative values"

CHALLENGE-301-001:
  title: "Implement Scaled Dot-Product Attention"
  difficulty: "Intermediate"
  time_estimate: "45 minutes"
  description: "Implement the attention mechanism from 'Attention Is All You Need'"
  starter_code: |
    import torch
    import torch.nn.functional as F

    def scaled_dot_product_attention(query, key, value, mask=None):
        # TODO: Compute attention scores
        # 1. Compute Q @ K^T
        # 2. Scale by 1/√d_k
        # 3. Apply mask if provided
        # 4. Apply softmax
        # 5. Multiply by values
        pass
  tests:
    - "Check output shape matches value shape"
    - "Verify attention weights sum to 1"
  hints:
    - "Use torch.matmul for matrix multiplication"
    - "Divide by sqrt(d_k) where d_k is the last dimension of Q"
    - "Use F.softmax for the softmax operation"
```

## Visual Diagrams

Interactive SVG diagrams.

### Attention Visualization
```html
<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
  <text x="300" y="30" text-anchor="middle" font-size="20">Self-Attention Mechanism</text>

  <!-- Query, Key, Value boxes -->
  <rect x="50" y="80" width="120" height="60" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="110" y="115" text-anchor="middle">Query (Q)</text>

  <rect x="240" y="80" width="120" height="60" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="300" y="115" text-anchor="middle">Key (K)</text>

  <rect x="430" y="80" width="120" height="60" fill="#e3f2fd" stroke="#1976d2" stroke-width="2"/>
  <text x="490" y="115" text-anchor="middle">Value (V)</text>

  <!-- Operation labels -->
  <text x="300" y="200" text-anchor="middle" font-size="14">MatMul(Q, K^T)</text>
  <text x="300" y="250" text-anchor="middle" font-size="14">Scale by 1/√d_k</text>
  <text x="300" y="300" text-anchor="middle" font-size="14">Softmax</text>

  <!-- Arrows -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
      <polygon points="0 0, 10 3, 0 6" fill="#1976d2"/>
    </marker>
  </defs>

  <line x1="170" y1="110" x2="220" y2="170" stroke="#1976d2" stroke-width="2" marker-end="url(#arrowhead)"/>
  <line x1="360" y1="110" x2="320" y2="170" stroke="#1976d2" stroke-width="2" marker-end="url(#arrowhead)"/>
  <line x1="490" y1="140" x2="490" y2="320" stroke="#1976d2" stroke-width="2" marker-end="url(#arrowhead)"/>
  <line x1="300" y1="320" x2="430" y2="350" stroke="#1976d2" stroke-width="2" marker-end="url(#arrowhead)"/>

  <!-- Output -->
  <rect x="200" y="350" width="200" height="40" fill="#c8e6c9" stroke="#388e3c" stroke-width="2"/>
  <text x="300" y="375" text-anchor="middle">Attention Output</text>
</svg>
```

## Interactive Notebooks

Guided notebook exercises.

### Notebook Template
````markdown
# Interactive Notebook: Self-Attention

## Learning Objectives
After completing this notebook, you will:
- Understand the attention mechanism
- Implement scaled dot-product attention
- Visualize attention weights

---

## Exercise 1: Compute Attention Scores

**Your Task:** Complete the function below to compute attention scores.

```python
import torch
def compute_attention_scores(Q, K):
    """
    Compute attention scores from Q and K.

    Args:
        Q: Query tensor of shape (batch_size, seq_len, d_k)
        K: Key tensor of shape (batch_size, seq_len, d_k)

    Returns:
        scores: Attention scores of shape (batch_size, seq_len, seq_len)
    """
    # TODO: Compute Q @ K^T
    scores = torch.matmul(Q, K.transpose(-2, -1))

    # TODO: Scale by sqrt(d_k)
    d_k = Q.size(-1)
    scores = scores / torch.sqrt(torch.tensor(d_k, dtype=torch.float32))

    return scores
```
````

**Test Your Code:**
```python
import torch
Q = torch.randn(2, 5, 8)
K = torch.randn(2, 5, 8)
scores = compute_attention_scores(Q, K)
print(f"Scores shape: {scores.shape}")
# Expected: torch.Size([2, 5, 5])
```

✅ **Check:** Does your output shape match the expected shape?

---

## Exercise 2: Visualize Attention

**Your Task:** Create a heatmap of attention weights.

```python
import torch.nn.functional as F
import torch
import matplotlib.pyplot as plt

def visualize_attention(attention_weights, tokens):
    """
    Visualize attention weights as a heatmap.

    Args:
        attention_weights: (seq_len, seq_len) tensor
        tokens: list of tokens
    """
    plt.figure(figsize=(10, 8))

    # TODO: Create heatmap
    plt.imshow(attention_weights, cmap='Blues')

    # TODO: Add labels
    plt.xticks(range(len(tokens)), tokens, rotation=90)
    plt.yticks(range(len(tokens)), tokens)

    plt.colorbar()
    plt.show()

# Test
tokens = ["The", "cat", "sat", "on", "mat"]
attn_weights = F.softmax(torch.randn(5, 5), dim=-1)
visualize_attention(attn_weights, tokens)
```

🎨 **Challenge:** Try different colormaps (viridis, plasma, inferno)

## Comparison Tables

Interactive comparison of methods/models.

```markdown
## Quantization Methods Comparison

| Method | Bits | Size Reduction | Speed | Quality Loss | Use Case |
|--------|------|----------------|-------|--------------|----------|
| **Dynamic** | 8 | 2x | ⚡⚡⚡ | Minimal | Quick testing |
| **PTQ** | 4 | 4x | ⚡⚡ | Small | Production |
| **GPTQ** | 4 | 4x | ⚡⚡ | Minimal | Large models |
| **AWQ** | 4 | 4x | ⚡⚡⚡ | Minimal | Fast inference |
| **NF4** | 4 | 4x | ⚡⚡ | Minimal | Normal Float |

### Click to expand details
<details>
<summary>Dynamic Quantization</summary>
Applied during model runtime. No calibration data needed. Best for quick testing.
</details>

<details>
<summary>GPTQ</summary>
Requires calibration data. Best for large models (>7B parameters). Preserves accuracy well.
</details>
```

## Progress Trackers

Track your learning progress.

```yaml
PROGRESS_TRACKER:
  user_id: "learner_001"
  start_date: "2026-02-04"

  phase_1_infrastructure:
    status: "in_progress"
    completed_modules:
      - "1100-network"
      - "1200-virtualization"
    current_module: "1300-kubernetes"
    quiz_scores:
      "1100-network": 85
      "1200-virtualization": 92
    labs_completed:
      - "LAB-000: Environment Setup"
      - "LAB-001: Docker & LLM Fundamentals"

  phase_2_foundations:
    status: "not_started"

  phase_3_transformers:
    status: "not_started"
```

## Coding Exercises with Feedback

Immediate feedback on code submissions.

```python
# Exercise: Implement LoRA layer

def check_lora_implementation(lora_layer):
    """Provide feedback on LoRA implementation."""

    feedback = {
        "errors": [],
        "warnings": [],
        "suggestions": []
    }

    # Check for low-rank matrices
    if not hasattr(lora_layer, 'lora_A') or not hasattr(lora_layer, 'lora_B'):
        feedback["errors"].append(
            "❌ Missing lora_A or lora_B matrices. "
            "LoRA requires two low-rank matrices."
        )
    else:
        feedback["suggestions"].append(
            "✅ LoRA matrices found"
        )

    # Check for scaling factor
    if not hasattr(lora_layer, 'scaling'):
        feedback["warnings"].append(
            "⚠️ No scaling factor found. "
            "Consider adding scaling = alpha / rank"
        )

    return feedback

# Usage
feedback = check_lora_implementation(my_lora_layer)
for msg in feedback["errors"] + feedback["warnings"] + feedback["suggestions"]:
    print(msg)
```

## Animated Concepts

GIF animations for complex topics.

### Topics to animate:
1. **Forward Pass vs Backward Pass**
2. **Gradient Descent Optimization**
3. **Attention Flow**
4. **Tokenization Process**
5. **KV Cache Operation**

---


**Note:** These components are designed to be integrated into the learning platform or used as standalone study aids.
