---
Document ID: CHEAT-SHEET-002
Title: "CHEAT-SHEET-002: Python for AI/ML"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'math', 'pytorch']
---

# CHEAT-SHEET-002: Python for AI/ML

**Essential Python for AI/ML development**

---

## Python Basics

### Virtual Environments
```bash
# Create project environment with uv (recommended)
# (uv downloads Python 3.13 itself if it is missing)
uv venv --python 3.13

# Activate (Linux/Mac)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Deactivate
deactivate

# Recreate the exact project environment anywhere
# (manifest: pyproject.toml declares deps, uv.lock pins the graph)
uv sync --locked
```

### Package Management
```bash
# Install package
uv pip install numpy

# Install specific version
uv pip install numpy==2.4.6

# Install from GitHub
uv pip install git+https://github.com/user/repo.git

# Show package info
uv pip show numpy

# List installed packages
uv pip list

# Uninstall package
uv pip uninstall numpy

# uv manages itself - no "upgrade pip" step needed
# (plain-pip fallback: python -m pip install --upgrade pip)
```

---

## NumPy Fundamentals

### Array Operations
```python
import numpy as np

# Create arrays
a = np.array([1, 2, 3, 4, 5])
b = np.zeros((3, 3))  # 3x3 zeros
c = np.ones((2, 4))   # 2x4 ones
d = np.random.randn(3, 3)  # Random normal

# Array info
print(a.shape)  # Dimensions
print(a.dtype)  # Data type
print(a.ndim)   # Number of dimensions

# Reshaping
a = a.reshape(5, 1)  # Reshape to 5x1
a = a.flatten()      # Flatten to 1D

# Slicing
a[:3]      # First 3 elements
a[::2]     # Every 2nd element
a[::-1]    # Reverse
```

### Array Math
```python
import numpy as np

a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

# Element-wise operations
a + b      # [5, 7, 9]
a * b      # [4, 10, 18]
a ** 2     # [1, 4, 9]

# Linear algebra
np.dot(a, b)           # Dot product
np.matmul(a, b)        # Matrix multiplication
a @ b                   # Matrix multiplication (Python 3.5+)

# Statistical operations
np.mean(a)              # Mean
np.std(a)               # Standard deviation
np.sum(a)               # Sum
np.max(a)               # Maximum
np.argmax(a)            # Index of maximum

# Broadcasting
a = np.array([[1, 2, 3]])      # Shape (1, 3)
b = np.array([4, 5, 6])         # Shape (3,)
a + b                          # Shape (1, 3): [[5, 7, 9]]
```

---

## Pandas Essentials

### DataFrame Operations
```python
import pandas as pd

# Create DataFrame
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'SF']
})

# Read/Write
df = pd.read_csv('data.csv')
df.to_csv('output.csv', index=False)

# Explore data
df.head()              # First 5 rows
df.tail()              # Last 5 rows
df.info()              # DataFrame info
df.describe()          # Statistics
df.shape              # Dimensions

# Select columns
df['name']             # Single column
df[['name', 'age']]    # Multiple columns

# Filter rows
df[df['age'] > 25]     # Conditional
df.query('age > 25')   # Query string

# Group by
df.groupby('city')['age'].mean()

# Sort
df.sort_values('age', ascending=False)
```

### Data Manipulation
```python
# Add column
df['salary'] = [50000, 60000, 70000]

# Apply function
df['name_upper'] = df['name'].str.upper()

# Aggregate
df.agg({'age': 'mean', 'salary': 'sum'})

# Merge
pd.merge(df1, df2, on='id')
pd.concat([df1, df2])
```

---

## Hugging Face Transformers

### Load Models
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load model and tokenizer
model_name = "mistralai/Mistral-7B-Instruct-v0.2"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name)

# Tokenize
text = "Hello, world!"
inputs = tokenizer(text, return_tensors="pt")

# Generate
outputs = model.generate(**inputs, max_new_tokens=50)

# Decode
response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)
```

### Pipeline API
```python
from transformers import pipeline

# Text generation
generator = pipeline("text-generation", model="gpt2")
result = generator("Once upon a time", max_length=50)

# Sentiment analysis
classifier = pipeline("sentiment-analysis")
result = classifier("I love Docker!")

# Question answering
qa = pipeline("question-answering")
result = qa(context="Docker is a container platform", question="What is Docker?")

# Feature extraction
fe = pipeline("feature-extraction")
result = fe("Some text to embed")
```

---

## PyTorch Basics

### Tensors
```python
import torch

# Create tensors
x = torch.tensor([1, 2, 3])
y = torch.zeros(2, 3)
z = torch.randn(3, 3)

# Move to GPU
x = x.to('cuda')
y = y.to('cuda')

# Tensor info
print(x.shape)    # Dimensions
print(x.dtype)    # Data type
print(x.device)   # CPU or CUDA

# Operations
x + y
x * y
x @ y              # Matrix multiplication
x.mean()
x.sum()
```

### Neural Network
```python
import torch.nn as nn
import torch.nn.functional as F

# Define model
class SimpleNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(784, 128)
        self.fc2 = nn.Linear(128, 10)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        return x

# Use model
model = SimpleNet()
output = model(torch.randn(1, 784))
```

### Training Loop
```python
import torch.optim as optim

# Setup
model = SimpleNet()
criterion = nn.CrossEntropyLoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training
model.train()
for epoch in range(10):
    for batch_x, batch_y in dataloader:
        # Forward
        optimizer.zero_grad()
        output = model(batch_x)
        loss = criterion(output, batch_y)

        # Backward
        loss.backward()
        optimizer.step()

# Evaluation
model.eval()
with torch.no_grad():
    for batch_x, batch_y in dataloader:
        output = model(batch_x)
        # Compute metrics
```

---

## Python AI Best Practices

### Type Hints
```python


def process_data(
    data: list[dict[str, str | int]],
    threshold: float | None = None
) -> dict[str, float]:
    """Process data with type hints"""
    if threshold is None:
        threshold = 0.5

    result = {}
    for item in data:
        key = item.get('key', '')
        value = item.get('value', 0)
        result[key] = value * threshold

    return result
```

### Error Handling
```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_divide(a: float, b: float) -> float:
    """Safely divide two numbers"""
    try:
        result = a / b
        logger.info(f"Division successful: {result}")
        return result
    except ZeroDivisionError:
        logger.error("Cannot divide by zero")
        raise ValueError("b cannot be zero")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise
```

### Context Managers
```python
from contextlib import contextmanager

@contextmanager
def timer(name: str):
    """Context manager for timing"""
    import time
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"{name} took {elapsed:.2f}s")

# Use
with timer("Training"):
    model.train(data)
```

---

## Performance Tips

### List Comprehensions
```python
# Slow
result = []
for i in range(1000):
    result.append(i * 2)

# Fast
result = [i * 2 for i in range(1000)]

# With condition
result = [i * 2 for i in range(1000) if i % 2 == 0]
```

### Vectorization
```python
import numpy as np

# Slow
result = []
for i in range(1000):
    result.append(i ** 2)

# Fast
arr = np.arange(1000)
result = arr ** 2
```

### Memory Efficiency
```python
# Use generators for large datasets
def large_dataset():
    for i in range(1000000):
        yield i * 2

# Process lazily
for value in large_dataset():
    process(value)
```

---

## Debugging

### Print vs Logging
```python
import logging

# Bad: print everywhere
print(f"Processing {data}")

# Good: use logging
logging.info(f"Processing {data}")
logging.debug(f"Detailed info: {data}")
logging.error(f"Error occurred: {e}")
```

### Assertions
```python
def divide(a: float, b: float) -> float:
    assert b != 0, "Divisor cannot be zero"
    return a / b
```

### Type Checking
```python
# Install mypy
# uv pip install mypy

# Run type checker
# mypy script.py

# Use type: ignore sparingly
result = complex_function(data)  # type: ignore
```

### Lint and Format
```python
# Lint with ruff (zero-install: uvx runs it without project changes)
# uvx ruff check .

# Auto-fix safe issues
# uvx ruff check --fix .

# Format like black, at Rust speed
# uvx ruff format .

# Habit: lint + format before every commit
```

---

## Common Libraries

### HTTP Requests
```python
import requests

# GET
response = requests.get('https://api.example.com/data', timeout=30)
data = response.json()

# POST
response = requests.post(
    'https://api.example.com/data',
    json={'key': 'value'},
    headers={'Authorization': 'Bearer token'}, timeout=30
)
```

### File Operations
```python
# Read file
with open('file.txt', 'r') as f:
    content = f.read()

# Write file
with open('output.txt', 'w', encoding="utf-8") as f:
    f.write('Hello, World!')

# Read lines
with open('file.txt', 'r') as f:
    lines = f.readlines()

# JSON
import json
data = json.load(open('data.json'))
json.dump(data, open('output.json', 'w', encoding="utf-8"))
```

---

## Testing

### Unit Tests
```python
import unittest

class TestMath(unittest.TestCase):
    def test_addition(self):
        self.assertEqual(1 + 1, 2)

    def test_division(self):
        self.assertEqual(10 / 2, 5)

if __name__ == '__main__':
    unittest.main()
```

### Pytest
```python
# uv pip install pytest

def test_addition():
    assert 1 + 1 == 2

def test_division():
    assert 10 / 2 == 5

# Run
# pytest test_file.py
```

---

## AI-Specific Patterns

### Model Inference
```python
import torch

def predict(model, input_data):
    """Make prediction with proper resource management"""
    model.eval()
    with torch.no_grad():
        input_tensor = torch.tensor(input_data)
        output = model(input_tensor)
        return output.numpy()
```

### Batch Processing
```python
from tqdm import tqdm

def process_in_batches(data, batch_size=32):
    """Process data in batches"""
    results = []
    for i in tqdm(range(0, len(data), batch_size)):
        batch = data[i:i+batch_size]
        result = model.process(batch)
        results.append(result)
    return results
```

---

## Python Idioms for AI

### Data Loading
```python
from dataclasses import dataclass

@dataclass
class TrainingConfig:
    batch_size: int = 32
    learning_rate: float = 0.001
    epochs: int = 10

def load_config(path: str) -> TrainingConfig:
    """Load config from JSON"""
    import json
    with open(path) as f:
        data = json.load(f)
    return TrainingConfig(**data)
```

### Progress Bars
```python
from tqdm import trange

for i in trange(1000, desc="Processing"):
    # Do work
    pass
```

### Configuration Files
```python
# config.py
MODEL_CONFIG = {
    'name': 'mistral',
    'max_tokens': 2048,
    'temperature': 0.7
}

# Usage
from config import MODEL_CONFIG
print(MODEL_CONFIG['name'])
```

---

## Quick Links

- **[TUTORIAL-001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - Your first LLM with Python
- **[2101: Tensor Algebra](../../phases/phase2-foundations/2100-calculus/2101-Tensor-Algebra.md)** - Math foundations
- **[2201: PyTorch Graphs](../../phases/phase2-foundations/2200-frameworks/2201-PyTorch-Computational-Graphs.md)** - PyTorch internals
- **[LAB-001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - FastAPI LLM server
- **[LAB-002: RAG Implementation](../labs/LAB-002-RAG-Implementation.md)** - RAG with Python
- **[LAB-003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)** - Fine-tuning with Python

---

## Next Steps

- **[CHEAT-SHEET-003: Git & Version Control](CHEAT-SHEET-003-Git.md)**
