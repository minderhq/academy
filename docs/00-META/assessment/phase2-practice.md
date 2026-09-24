# Phase 2: AI/ML Foundations Practice

## Hands-On Exercises

### Exercise 1: Tensor Operations with einsum

**Objective:** Master Einstein summation notation for tensor operations.

```python
import torch
import numpy as np

def einsum_basics():
    """Learn einsum notation through examples"""

    print("=== Einstein Summation (einsum) Tutorial ===\n")

    # 1. Vector dot product
    print("1. Vector Dot Product:")
    a = torch.randn(3)
    b = torch.randn(3)

    # Standard way
    dot_standard = torch.dot(a, b)

    # einsum way
    dot_einsum = torch.einsum('i,i->', a, b)

    print(f"   a: {a}")
    print(f"   b: {b}")
    print(f"   torch.dot(a, b):  {dot_standard:.4f}")
    print(f"   torch.einsum('i,i->', a, b): {dot_einsum:.4f}")

    # 2. Matrix multiplication
    print("\n2. Matrix Multiplication:")
    A = torch.randn(3, 4)
    B = torch.randn(4, 5)

    # Standard way
    matmul_standard = A @ B

    # einsum way
    matmul_einsum = torch.einsum('ij,jk->ik', A, B)

    print(f"   A shape: {A.shape}")
    print(f"   B shape: {B.shape}")
    print(f"   A @ B shape: {matmul_standard.shape}")
    print(f"   torch.einsum('ij,jk->ik', A, B) shape: {matmul_einsum.shape}")
    assert torch.allclose(matmul_standard, matmul_einsum)

    # 3. Batch matrix multiplication
    print("\n3. Batch Matrix Multiplication:")
    batch_A = torch.randn(10, 3, 4)
    batch_B = torch.randn(10, 4, 5)

    # Standard way
    batch_matmul = torch.bmm(batch_A, batch_B)

    # einsum way
    batch_einsum = torch.einsum('bij,bjk->bik', batch_A, batch_B)

    print(f"   Batch A shape: {batch_A.shape}")
    print(f"   Batch B shape: {batch_B.shape}")
    print(f"   bmm output shape: {batch_matmul.shape}")
    print(f"   einsum output shape: {batch_einsum.shape}")
    assert torch.allclose(batch_matmul, batch_einsum)

    # 4. Transpose
    print("\n4. Matrix Transpose:")
    C = torch.randn(3, 4)

    # Standard way
    transpose_standard = C.T

    # einsum way
    transpose_einsum = torch.einsum('ij->ji', C)

    print(f"   C shape: {C.shape}")
    print(f"   C.T shape: {transpose_standard.shape}")
    print(f"   einsum('ij->ji', C) shape: {transpose_einsum.shape}")

    # 5. Outer product
    print("\n5. Outer Product:")
    u = torch.randn(3)
    v = torch.randn(4)

    outer = torch.einsum('i,j->ij', u, v)
    print(f"   u shape: {u.shape}")
    print(f"   v shape: {v.shape}")
    print(f"   outer product shape: {outer.shape}")

    # 6. Element-wise operations
    print("\n6. Element-wise Multiplication:")
    D = torch.randn(3, 4)
    E = torch.randn(3, 4)

    element_mul = torch.einsum('ij,ij->ij', D, E)
    print(f"   D shape: {D.shape}")
    print(f"   E shape: {E.shape}")
    print(f"   element-wise shape: {element_mul.shape}")

    # 7. Sum along axis
    print("\n7. Sum Along Axis:")
    F = torch.randn(3, 4)

    sum_rows = torch.einsum('ij->i', F)  # Sum across columns
    sum_cols = torch.einsum('ij->j', F)  # Sum across rows
    sum_all = torch.einsum('ij->', F)     # Sum all elements

    print(f"   F shape: {F.shape}")
    print(f"   sum rows: {sum_rows.shape} -> {sum_rows}")
    print(f"   sum cols: {sum_cols.shape} -> {sum_cols}")
    print(f"   sum all: {sum_all.item():.4f}")

    # 8. Diagonal extraction
    print("\n8. Diagonal Extraction:")
    G = torch.randn(4, 4)

    diagonal = torch.einsum('ii->i', G)
    print(f"   G shape: {G.shape}")
    print(f"   diagonal: {diagonal}")

    # 9. Trace (sum of diagonal)
    print("\n9. Trace:")
    trace = torch.einsum('ii->', G)
    print(f"   trace: {trace.item():.4f}")

    # 10. Attention mechanism (complex example)
    print("\n10. Attention Mechanism with einsum:")

    batch_size = 2
    seq_len = 5
    num_heads = 4
    head_dim = 8

    Q = torch.randn(batch_size, num_heads, seq_len, head_dim)
    K = torch.randn(batch_size, num_heads, seq_len, head_dim)
    V = torch.randn(batch_size, num_heads, seq_len, head_dim)

    # Compute attention scores: Q @ K^T / sqrt(d)
    scores = torch.einsum('bhqd,bhkd->bhqk', Q, K) / (head_dim ** 0.5)

    # Apply softmax
    attn_weights = torch.softmax(scores, dim=-1)

    # Apply attention to values
    output = torch.einsum('bhqk,bhkd->bhqd', attn_weights, V)

    print(f"   Q shape: {Q.shape}")
    print(f"   K shape: {K.shape}")
    print(f"   V shape: {V.shape}")
    print(f"   scores shape: {scores.shape}")
    print(f"   output shape: {output.shape}")

    print("\n=== All einsum operations completed successfully! ===")

if __name__ == "__main__":
    einsum_basics()
```

**Expected Output:**
- All operations complete without errors
- Shapes match expected dimensions
- Complex attention mechanism works correctly

**Key Concepts:**
- Repeated indices: diagonal or dot product (`i,i`)
- Unique indices: sum along dimension (`ij->i`)
- Order of letters: output shape (`ij,jk->ik`)

---

### Exercise 2: Implement Backpropagation

**Objective:** Implement automatic differentiation from scratch.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class AutogradTensor:
    """Simple automatic differentiation tensor"""

    def __init__(self, data, requires_grad=False):
        self.data = torch.tensor(data, dtype=torch.float32)
        self.grad = None
        self.requires_grad = requires_grad
        self._backward_fn = None

    def backward(self, grad_output=None):
        """Compute gradients through computational graph"""
        if not self.requires_grad:
            return

        if grad_output is None:
            grad_output = torch.ones_like(self.data)

        # Build topological order
        nodes = []
        visited = set()

        def build_graph(node):
            if node not in visited:
                visited.add(node)
                if node._backward_fn:
                    for input_node in node._backward_fn[1]:
                        build_graph(input_node)
                nodes.append(node)

        build_graph(self)

        # Backpropagate
        grad = grad_output
        for node in reversed(nodes):
            if node.grad is None:
                node.grad = torch.zeros_like(node.data)
            node.grad += grad

            if node._backward_fn:
                backward_fn, inputs = node._backward_fn
                grads = backward_fn(grad)
                grad = torch.zeros_like(grad)  # Reset for next
                for input_node, input_grad in zip(inputs, grads):
                    if input_node.requires_grad:
                        grad += input_grad

    def __add__(self, other):
        """Addition operation"""
        other = other if isinstance(other, AutogradTensor) else AutogradTensor(other)

        result = AutogradTensor(self.data + other.data)

        def backward_grad(grad):
            return grad, grad

        result._backward_fn = (backward_grad, [self, other])
        return result

    def __mul__(self, other):
        """Multiplication operation"""
        other = other if isinstance(other, AutogradTensor) else AutogradTensor(other)

        result = AutogradTensor(self.data * other.data)

        def backward_grad(grad):
            return grad * other.data, grad * self.data

        result._backward_fn = (backward_grad, [self, other])
        return result

    def __matmul__(self, other):
        """Matrix multiplication"""
        result = AutogradTensor(self.data @ other.data)

        def backward_grad(grad):
            # d(A@B)/dA = grad @ B.T
            # d(A@B)/dB = A.T @ grad
            return grad @ other.data.T, self.data.T @ grad

        result._backward_fn = (backward_grad, [self, other])
        return result

    def sum(self):
        """Sum reduction"""
        result = AutogradTensor(self.data.sum())

        def backward_grad(grad):
            return torch.ones_like(self.data) * grad

        result._backward_fn = (backward_grad, [self])
        return result

    def relu(self):
        """ReLU activation"""
        mask = self.data > 0
        result = AutogradTensor(self.data * mask.float())

        def backward_grad(grad):
            return grad * mask.float()

        result._backward_fn = (backward_grad, [self])
        return result


def test_autograd():
    """Test custom autograd implementation"""

    print("=== Testing Custom Autograd ===\n")

    # Test 1: Simple function: f(x) = x^2
    print("Test 1: f(x) = x^2, df/dx = 2x")
    x = AutogradTensor([2.0, 3.0, 4.0], requires_grad=True)
    y = x * x
    y.backward()
    print(f"   x: {x.data}")
    print(f"   y: {y.data}")
    print(f"   dx: {x.grad}")  # Should be [4, 6, 8]
    assert torch.allclose(x.grad, torch.tensor([4.0, 6.0, 8.0]))
    print("   ✅ PASS\n")

    # Test 2: f(x) = x^2 + 2x + 1
    print("Test 2: f(x) = x^2 + 2x + 1, df/dx = 2x + 2")
    x = AutogradTensor([2.0], requires_grad=True)
    y = x * x + AutogradTensor(2.0) * x + AutogradTensor(1.0)
    y.backward()
    print(f"   x: {x.data}")
    print(f"   y: {y.data}")
    print(f"   dx: {x.grad}")  # Should be 6
    assert torch.allclose(x.grad, torch.tensor([6.0]))
    print("   ✅ PASS\n")

    # Test 3: Matrix multiplication
    print("Test 3: Matrix multiplication")
    A = AutogradTensor([[1.0, 2.0], [3.0, 4.0]], requires_grad=True)
    B = AutogradTensor([[5.0, 6.0], [7.0, 8.0]], requires_grad=True)
    C = A @ B
    loss = C.sum()
    loss.backward()

    print(f"   A:\n{A.data}")
    print(f"   B:\n{B.data}")
    print(f"   C:\n{C.data}")
    print(f"   dA:\n{A.grad}")
    print(f"   dB:\n{B.grad}")

    # Verify gradients
    expected_dA = B.data.T
    expected_dB = A.data.T
    assert torch.allclose(A.grad, expected_dA)
    assert torch.allclose(B.grad, expected_dB)
    print("   ✅ PASS\n")

    # Test 4: ReLU activation
    print("Test 4: ReLU activation")
    x = AutogradTensor([-2.0, -1.0, 0.0, 1.0, 2.0], requires_grad=True)
    y = x.relu()
    loss = y.sum()
    loss.backward()

    print(f"   x: {x.data}")
    print(f"   y: {y.data}")
    print(f"   dx: {x.grad}")  # Should be [0, 0, 0, 1, 1]
    expected_grad = torch.tensor([0.0, 0.0, 0.0, 1.0, 1.0])
    assert torch.allclose(x.grad, expected_grad)
    print("   ✅ PASS\n")

    # Test 5: Computational graph
    print("Test 5: Complex computational graph")
    x = AutogradTensor([2.0], requires_grad=True)
    y = AutogradTensor([3.0], requires_grad=True)

    # f(x,y) = (x + y) * (x - y)
    z = (x + y) * (x - y)
    z.backward()

    # df/dx = (x - y) + (x + y) = 2x = 4
    # df/dy = (x - y) - (x + y) = -2y = -6
    print(f"   x: {x.data}, dx: {x.grad}")  # Should be 4
    print(f"   y: {y.data}, dy: {y.grad}")  # Should be -6
    assert torch.allclose(x.grad, torch.tensor([4.0]))
    assert torch.allclose(y.grad, torch.tensor([-6.0]))
    print("   ✅ PASS\n")

    print("=== All Autograd Tests Passed! ===")

if __name__ == "__main__":
    test_autograd()
```

**Key Concepts:**
- Computational graph building
- Chain rule application
- Gradient accumulation
- Operation differentiation rules

---

### Exercise 3: Implement Neural Network Layer

**Objective:** Build custom neural network layer from scratch.

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class CustomLinear(nn.Module):
    """Custom linear layer implementation"""

    def __init__(self, in_features, out_features, bias=True):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features

        # Initialize parameters
        self.weight = nn.Parameter(torch.randn(out_features, in_features) * 0.01)
        if bias:
            self.bias = nn.Parameter(torch.zeros(out_features))
        else:
            self.register_buffer('bias', None)

    def forward(self, input):
        """Forward pass: y = xW^T + b"""
        # Input: (N, in_features)
        # Weight: (out_features, in_features)
        # Output: (N, out_features)

        output = torch.matmul(input, self.weight.t())
        if self.bias is not None:
            output += self.bias

        return output

    def extra_repr(self):
        """String representation"""
        return 'in_features={}, out_features={}, bias={}'.format(
            self.in_features, self.out_features, self.bias is not None
        )


class CustomReLU(nn.Module):
    """Custom ReLU activation"""

    def forward(self, x):
        return torch.clamp(x, min=0)


class CustomMLP(nn.Module):
    """Multi-layer perceptron from scratch"""

    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()

        # Define layers
        self.fc1 = CustomLinear(input_dim, hidden_dim)
        self.fc2 = CustomLinear(hidden_dim, hidden_dim)
        self.fc3 = CustomLinear(hidden_dim, output_dim)

        self.activation = CustomReLU()
        self.dropout = nn.Dropout(0.1)

    def forward(self, x):
        """Forward pass with custom layers"""

        # Layer 1
        x = self.fc1(x)
        x = self.activation(x)
        x = self.dropout(x)

        # Layer 2
        x = self.fc2(x)
        x = self.activation(x)
        x = self.dropout(x)

        # Layer 3 (output)
        x = self.fc3(x)

        return x


def test_custom_layers():
    """Test custom layer implementations"""

    print("=== Testing Custom Neural Network Layers ===\n")

    # Test CustomLinear
    print("Test 1: Custom Linear Layer")
    linear = CustomLinear(in_features=4, out_features=3)
    x = torch.randn(2, 4)
    output = linear(x)
    print(f"   Input shape: {x.shape}")
    print(f"   Output shape: {output.shape}")
    print(f"   Layer: {linear.extra_repr()}")
    assert output.shape == (2, 3)
    print("   ✅ PASS\n")

    # Test CustomMLP
    print("Test 2: Custom MLP")
    mlp = CustomMLP(input_dim=10, hidden_dim=20, output_dim=5)
    x = torch.randn(8, 10)  # Batch of 8
    output = mlp(x)
    print(f"   Input shape: {x.shape}")
    print(f"   Output shape: {output.shape}")
    assert output.shape == (8, 5)
    print("   ✅ PASS\n")

    # Test training loop
    print("Test 3: Training Loop with Custom MLP")

    # Generate random data
    X = torch.randn(100, 10)
    y = torch.randint(0, 5, (100,))

    model = CustomMLP(10, 20, 5)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    losses = []
    for epoch in range(100):
        # Forward pass
        outputs = model(X)
        loss = criterion(outputs, y)

        # Backward pass
        optimizer.zero_grad()
        loss.backward()

        # Update weights
        optimizer.step()

        losses.append(loss.item())

    print(f"   Initial loss: {losses[0]:.4f}")
    print(f"   Final loss: {losses[-1]:.4f}")
    print(f"   Loss reduction: {losses[0] - losses[-1]:.4f}")

    # Check that loss decreased
    assert losses[-1] < losses[0]
    print("   ✅ PASS\n")

    # Test gradient flow
    print("Test 4: Gradient Flow Check")
    model = CustomMLP(10, 20, 5)
    X = torch.randn(1, 10)
    output = model(X)
    loss = output.sum()
    loss.backward()

    # Check gradients exist
    assert model.fc1.weight.grad is not None
    assert model.fc2.weight.grad is not None
    assert model.fc3.weight.grad is not None

    print(f"   fc1.grad norm: {model.fc1.weight.grad.norm():.4f}")
    print(f"   fc2.grad norm: {model.fc2.weight.grad.norm():.4f}")
    print(f"   fc3.grad norm: {model.fc3.weight.grad.norm():.4f}")
    print("   ✅ PASS\n")

    print("=== All Custom Layer Tests Passed! ===")

if __name__ == "__main__":
    test_custom_layers()
```

---

### Exercise 4: CUDA Kernel Basics

**Objective:** Write and execute simple CUDA kernels.

```python
import torch
import torch.nn.functional as F

def simple_cuda_kernel():
    """Implement and test simple CUDA kernel"""

    print("=== Simple CUDA Kernel Tutorial ===\n")

    # Check CUDA availability
    if not torch.cuda.is_available():
        print("❌ CUDA not available. Skipping CUDA exercises.")
        return

    device = torch.device('cuda')
    print(f"✅ CUDA available. Device: {torch.cuda.get_device_name(0)}\n")

    # Exercise 1: Element-wise addition kernel
    print("Exercise 1: Vector Addition on GPU")

    size = 1000000
    a = torch.randn(size, device=device)
    b = torch.randn(size, device=device)

    # PyTorch native (uses CUDA kernels under the hood)
    c = a + b

    print(f"   Vector size: {size:,}")
    print(f"   Result: {c[:5]}... (showing first 5)")
    print(f"   Mean: {c.mean():.4f}")
    print("   ✅ PASS\n")

    # Exercise 2: Matrix multiplication
    print("Exercise 2: Matrix Multiplication on GPU")

    M, N, K = 1024, 1024, 1024
    A = torch.randn(M, K, device=device)
    B = torch.randn(K, N, device=device)

    # Warmup
    C = A @ B

    # Benchmark
    torch.cuda.synchronize()
    start = torch.cuda.Event(enable_timing=True)
    end = torch.cuda.Event(enable_timing=True)

    start.record()
    for _ in range(100):
        C = A @ B
    end.record()

    torch.cuda.synchronize()
    elapsed = start.elapsed_time(end)

    gflops = (2 * M * N * K) / (elapsed / 100 / 1e9)  # 2 MNK for matmul

    print(f"   Matrix sizes: {M}x{K} @ {K}x{N}")
    print(f"   Time for 100 iterations: {elapsed:.2f} ms")
    print(f"   Performance: {gflops:.2f} GFLOPS")
    print("   ✅ PASS\n")

    # Exercise 3: Memory management
    print("Exercise 3: GPU Memory Management")

    print(f"   Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    print(f"   Cached: {torch.cuda.memory_reserved() / 1e9:.2f} GB")

    # Clear cache
    torch.cuda.empty_cache()
    print(f"   After empty_cache - Allocated: {torch.cuda.memory_allocated() / 1e9:.2f} GB")
    print("   ✅ PASS\n")

    # Exercise 4: Multiple GPU operations
    print("Exercise 4: Parallel Operations")

    # Create multiple tensors
    tensors = [torch.randn(1000, 1000, device=device) for _ in range(5)]

    # Perform operations
    results = []
    for tensor in tensors:
        result = tensor @ tensor.T
        results.append(result.sum())

    total = sum(results)
    print(f"   Result: {total:.4f}")
    print("   ✅ PASS\n")

    print("=== All CUDA Exercises Completed! ===")

if __name__ == "__main__":
    simple_cuda_kernel()
```

---

## Bonus: Build Simple Transformer Block

```python
class TransformerBlock(nn.Module):
    """Complete transformer block from scratch"""

    def __init__(self, embed_dim, num_heads, ff_dim, dropout=0.1):
        super().__init__()

        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.head_dim = embed_dim // num_heads

        # Multi-head attention components
        self.qkv = nn.Linear(embed_dim, 3 * embed_dim)
        self.out = nn.Linear(embed_dim, embed_dim)

        # Feed-forward network
        self.ff1 = nn.Linear(embed_dim, ff_dim)
        self.ff2 = nn.Linear(ff_dim, embed_dim)

        # Normalization layers
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

        # Dropout
        self.dropout = nn.Dropout(dropout)
        self.activation = nn.GELU()

    def forward(self, x, mask=None):
        batch_size, seq_len, _ = x.shape

        # Self-attention with residual
        residual = x
        x = self.norm1(x)

        # QKV projection
        qkv = self.qkv(x).reshape(batch_size, seq_len, 3, self.num_heads, self.head_dim)
        qkv = qkv.permute(2, 0, 3, 1, 4)
        q, k, v = qkv[0], qkv[1], qkv[2]

        # Scaled dot-product attention
        scale = self.head_dim ** -0.5
        attn = (q @ k.transpose(-2, -1)) * scale

        if mask is not None:
            attn = attn.masked_fill(mask == 0, float('-inf'))

        attn = F.softmax(attn, dim=-1)
        attn = self.dropout(attn)

        # Attention output
        out = attn @ v
        out = out.transpose(1, 2).reshape(batch_size, seq_len, self.embed_dim)
        out = self.out(out)

        x = residual + self.dropout(out)

        # Feed-forward with residual
        residual = x
        x = self.norm2(x)
        x = self.ff1(x)
        x = self.activation(x)
        x = self.ff2(x)
        x = residual + self.dropout(x)

        return x


def test_transformer_block():
    """Test transformer block implementation"""

    print("=== Testing Transformer Block ===\n")

    # Create transformer block
    block = TransformerBlock(
        embed_dim=64,
        num_heads=4,
        ff_dim=256,
        dropout=0.1
    )

    # Test input
    batch_size = 2
    seq_len = 10
    x = torch.randn(batch_size, seq_len, 64)

    # Create causal mask
    mask = torch.tril(torch.ones(seq_len, seq_len))

    # Forward pass
    output = block(x, mask)

    print(f"Input shape: {x.shape}")
    print(f"Output shape: {output.shape}")
    print(f"Parameters: {sum(p.numel() for p in block.parameters()):,}")

    # Test training
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(block.parameters(), lr=0.001)

    target = torch.randn_like(output)
    loss = criterion(output, target)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

    print(f"Loss: {loss.item():.4f}")
    print("✅ Transformer block working!\n")

if __name__ == "__main__":
    test_transformer_block()
```

---

## Completion Checklist

- [ ] Tensor operations with einsum mastered
- [ ] Backpropagation implemented from scratch
- [ ] Custom neural network layers built
- [ ] Training loop implemented
- [ ] CUDA kernels understood
- [ ] Transformer block constructed
- [ ] Gradient flow verified
- [ ] Memory optimization techniques learned

---

**Last Updated:** 2026-02-05
