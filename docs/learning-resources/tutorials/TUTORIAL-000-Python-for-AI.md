---
Document ID: TUTORIAL-000
Title: "TUTORIAL-000: Python for AI (Complete Beginner)"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Beginner
Estimated Time: 20 hours
Prerequisites: []
Tags: ['tutorial', 'math', 'tensors']
---

# TUTORIAL-000: Python for AI (Complete Beginner)

**Difficulty:** ⭐ Beginner
**Time:** 15-20 hours (spread over 1-2 weeks)
**Prerequisites:** None! This is where you start.

> ⚠️ **Realistic Expectation:** If you're new to programming, this will take 15-20 hours to complete properly. Don't rush - solid fundamentals are crucial for success in later tutorials.

---

## Why This Tutorial?

Before you can build AI systems, you need to speak the language of AI: **Python**.

This tutorial is designed for **complete beginners** with zero programming experience. By the end, you'll have the Python skills needed for TUTORIAL-001 (Hello LLM) and beyond.

---

## What You'll Learn

### Part 1: Python Basics (2 hours)
- Variables and data types
- Operators and expressions
- Control flow (if/else, loops)
- Functions (the building blocks)

### Part 2: Data Structures (2 hours)
- Lists and tuples
- Dictionaries (crucial for AI!)
- Sets
- List comprehensions

### Part 3: Object-Oriented Programming (1 hour)
- Classes and objects
- Methods and attributes
- When to use OOP

### Part 4: Practical Skills (1 hour)
- File I/O
- Error handling
- Working with packages
- Virtual environments

### Part 5: AI-Specific Python (4-6 hours)
- NumPy basics for tensor operations
- Type hints (including advanced types)
- async/await (intro)
- **Pydantic data models** (CRITICAL for later tutorials)
- **FastAPI web framework** (CRITICAL for later tutorials)
- Working with APIs

---

## After This Tutorial

You'll be ready for:
- ✅ TUTORIAL-001: Hello LLM
- ✅ TUTORIAL-002: Docker Essentials
- ✅ TUTORIAL-003: RAG Basics
- ✅ LAB-001: Docker & LLM
- ✅ All other tutorials and labs!

---

## Part 1: Python Basics

### 1.1 What is Python?

**Python** is a programming language that:
- Easy to read and write
- Powerful and widely used
- The #1 language for AI/ML

**Why Python for AI?**
- Simple syntax → focus on logic, not syntax
- Huge ecosystem → libraries for everything
- Great community → help is everywhere

---

### 1.2 Installing Python

#### Windows:
```bash
# Download from python.org
# https://www.python.org/downloads/

# During installation:
CHECK "Add Python to PATH"
```

#### Mac:
```bash
# Install Homebrew first (if needed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python
```

#### Linux:
```bash
# Usually pre-installed
python3 --version

# If not:
sudo apt install python3  # Ubuntu/Debian
sudo yum install python3   # CentOS/RHEL
```

#### Verify Installation:
```bash
python --version
# Should show: Python 3.13.x or similar
```

---

### 1.3 Your First Python Code

#### Interactive Python Shell:
```bash
python
```

#### Try This:
```python
# Simple calculator
2 + 2
# Output: 4

# String
"Hello, World!"
# Output: 'Hello, World!'

# Combining
"Hello" + " " + "World"
# Output: 'Hello World'
```

**Exit shell:** Type `exit()` or press `Ctrl+D`

---

### 1.4 Variables and Data Types

#### What is a Variable?

A **variable** is a container for storing data.

```python
# Assigning values
name = "Alice"
age = 30
height = 1.75
is_student = True

# Print variables
print(name)
print(age)
print(height)
print(is_student)
```

**Output:**
```text
Alice
30
1.75
True
```

#### Python Data Types:

| Type | Description | Example |
|------|-------------|---------|
| `str` | Text/string | `"Hello"` |
| `int` | Integer | `42` |
| `float` | Decimal | `3.14` |
| `bool` | True/False | `True` |
| `list` | Collection | `[1, 2, 3]` |
| `dict` | Key-value | `{"key": "value"}` |

#### Type Conversion:
```python
# String to int
age_str = "30"
age_int = int(age_str)
print(age_int + 5)  # 35

# Int to string
age = 30
age_str = str(age)
print("I am " + age_str + " years old")  # I am 30 years old

# Float to int
price = 9.99
price_int = int(price)
print(price_int)  # 9 (rounds down)
```

---

### 1.5 Operators

#### Arithmetic Operators:
```python
# Basic math
x = 10
y = 3

print(x + y)   # 13 (addition)
print(x - y)   # 7  (subtraction)
print(x * y)   # 30 (multiplication)
print(x / y)   # 3.33... (division)
print(x // y)  # 3  (floor division)
print(x % y)   # 1  (remainder/modulo)
print(x ** y)  # 1000 (exponent)
```

#### Comparison Operators:
```python
x = 10
y = 5

print(x == y)  # False (equal)
print(x != y)  # True (not equal)
print(x > y)   # True (greater than)
print(x < y)   # False (less than)
print(x >= y)  # True (greater or equal)
print(x <= y)  # False (less or equal)
```

#### Logical Operators:
```python
x = True
y = False

print(x and y)  # False (both must be True)
print(x or y)   # True (at least one True)
print(not x)    # False (negation)
```

---

### 1.6 Control Flow

#### If/Else Statements:
```python
age = 18

if age >= 18:
    print("You are an adult")
elif age >= 13:
    print("You are a teenager")
else:
    print("You are a child")
```

#### Comparison in Action:
```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

print(f"Your grade: {grade}")  # Your grade: B
```

#### Logical Operators in Conditions:
```python
age = 25
has_license = True

if age >= 18 and has_license:
    print("You can drive")
else:
    print("You cannot drive")
```

---

### 1.7 Loops

#### For Loops:
```python
# Loop through a range
for i in range(5):
    print(i)
# Output: 0, 1, 2, 3, 4

# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)
# Output: apple, banana, cherry

# Loop with index
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")
# Output:
# 0: apple
# 1: banana
# 2: cherry
```

#### While Loops:
```python
count = 0
while count < 5:
    print(count)
    count += 1
# Output: 0, 1, 2, 3, 4
```

#### Loop Control:
```python
# break - exit loop
for i in range(10):
    if i == 5:
        break
    print(i)
# Output: 0, 1, 2, 3, 4

# continue - skip to next iteration
for i in range(5):
    if i == 2:
        continue
    print(i)
# Output: 0, 1, 3, 4
```

---

### 1.8 Functions

#### What is a Function?

A **function** is a reusable block of code.

```python
# Defining a function
def greet(name):
    return f"Hello, {name}!"

# Calling a function
message = greet("Alice")
print(message)  # Hello, Alice!
```

#### Function Parameters:
```python
# Default parameter
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

print(greet("Alice"))              # Hello, Alice!
print(greet("Bob", "Hi"))         # Hi, Bob!
print(greet("Charlie", "Hey"))    # Hey, Charlie!
```

#### Multiple Return Values:
```python
def get_user_info():
    name = "Alice"
    age = 30
    city = "NYC"
    return name, age, city

# Unpacking return values
name, age, city = get_user_info()
print(name)  # Alice
print(age)   # 30
print(city)  # NYC
```

#### Lambda Functions (Anonymous):
```python
# Regular function
def add(x, y):
    return x + y

# Lambda equivalent
add_lambda = lambda x, y: x + y

print(add(5, 3))        # 8
print(add_lambda(5, 3))  # 8
```

---

## Part 2: Data Structures

### 2.1 Lists

#### Creating Lists:
```python
# Empty list
empty_list = []

# List with items
fruits = ["apple", "banana", "cherry"]

# Mixed types
mixed = [1, "hello", 3.14, True]

# List from range
numbers = list(range(5))
print(numbers)  # [0, 1, 2, 3, 4]
```

#### Accessing Elements:
```python
fruits = ["apple", "banana", "cherry"]

# Indexing (starts at 0)
print(fruits[0])   # apple
print(fruits[1])   # banana
print(fruits[-1])  # cherry (last element)

# Slicing
print(fruits[0:2])  # ['apple', 'banana']
print(fruits[1:])   # ['banana', 'cherry']
print(fruits[:2])   # ['apple', 'banana']
```

#### Modifying Lists:
```python
fruits = ["apple", "banana", "cherry"]

# Append
fruits.append("date")
print(fruits)  # ['apple', 'banana', 'cherry', 'date']

# Insert at position
fruits.insert(1, "blueberry")
print(fruits)  # ['apple', 'blueberry', 'banana', 'cherry', 'date']

# Remove
fruits.remove("banana")
print(fruits)  # ['apple', 'blueberry', 'cherry', 'date']

# Pop (remove and return)
last = fruits.pop()
print(last)    # date
print(fruits)  # ['apple', 'blueberry', 'cherry']
```

#### List Methods:
```python
numbers = [3, 1, 4, 1, 5, 9, 2, 6]

# Sort
numbers.sort()
print(numbers)  # [1, 1, 2, 3, 4, 5, 6, 9]

# Reverse
numbers.reverse()
print(numbers)  # [9, 6, 5, 4, 3, 2, 1, 1]

# Count
print(numbers.count(1))  # 2

# Index
print(numbers.index(5))  # 2
```

---

### 2.2 Tuples

#### What is a Tuple?

A **tuple** is like a list, but **immutable** (cannot be changed).

```python
# Creating tuples
coordinates = (10, 20)
rgb = (255, 128, 0)

# Accessing (same as lists)
print(coordinates[0])  # 10
print(rgb[1])          # 128

# Tuples are immutable
coordinates[0] = 5  # ERROR! Cannot modify tuple
```

#### When to Use Tuples:
```python
# Good for fixed data
DAYS_OF_WEEK = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

# Returning multiple values
def get_dimensions():
    return (1920, 1080)

width, height = get_dimensions()
print(f"Resolution: {width}x{height}")  # Resolution: 1920x1080
```

---

### 2.3 Dictionaries (CRUCIAL for AI!)

#### What is a Dictionary?

A **dictionary** stores key-value pairs. This is the most important data structure for AI!

```python
# Creating dictionaries
person = {
    "name": "Alice",
    "age": 30,
    "city": "NYC"
}

# Accessing values
print(person["name"])   # Alice
print(person["age"])    # 30

# Using .get() (safer)
print(person.get("name"))  # Alice
print(person.get("job", "Unknown"))  # Unknown (default)
```

#### Modifying Dictionaries:
```python
person = {"name": "Alice", "age": 30}

# Add/Update
person["city"] = "NYC"
print(person)  # {'name': 'Alice', 'age': 30, 'city': 'NYC'}

person["age"] = 31
print(person)  # {'name': 'Alice', 'age': 31, 'city': 'NYC'}

# Delete
del person["city"]
print(person)  # {'name': 'Alice', 'age': 31}
```

#### Dictionary Methods:
```python
person = {"name": "Alice", "age": 30, "city": "NYC"}

# Keys
print(person.keys())    # dict_keys(['name', 'age', 'city'])

# Values
print(person.values())  # dict_values(['Alice', 30, 'NYC'])

# Items
print(person.items())   # dict_items([('name', 'Alice'), ('age', 30), ('city', 'NYC')])

# Iterate
for key, value in person.items():
    print(f"{key}: {value}")
# Output:
# name: Alice
# age: 30
# city: NYC
```

#### Nested Dictionaries (Common in AI):
```python
# AI model configuration
config = {
    "model": {
        "name": "mistral-7b",
        "parameters": "7b",
        "quantization": "4-bit"
    },
    "training": {
        "epochs": 3,
        "batch_size": 32,
        "learning_rate": 0.001
    }
}

# Access nested values
model_name = config["model"]["name"]
batch_size = config["training"]["batch_size"]

print(f"Model: {model_name}, Batch: {batch_size}")
# Model: mistral-7b, Batch: 32
```

---

### 2.4 Sets

#### What is a Set?

A **set** is an unordered collection of unique elements.

```python
# Creating sets
numbers = {1, 2, 3, 4, 5}
duplicates = {1, 2, 2, 3, 3, 3}  # Automatically removes duplicates
print(duplicates)  # {1, 2, 3}

# Set operations
a = {1, 2, 3}
b = {3, 4, 5}

print(a | b)  # Union: {1, 2, 3, 4, 5}
print(a & b)  # Intersection: {3}
print(a - b)  # Difference: {1, 2}
```

#### Removing Duplicates from List:
```python
# Using set to remove duplicates
numbers = [1, 2, 2, 3, 3, 3, 4, 5]
unique = list(set(numbers))
print(unique)  # [1, 2, 3, 4, 5]
```

---

### 2.5 List Comprehensions

#### Basic List Comprehension:
```python
# Traditional way
squares = []
for i in range(5):
    squares.append(i ** 2)
print(squares)  # [0, 1, 4, 9, 16]

# List comprehension
squares = [i ** 2 for i in range(5)]
print(squares)  # [0, 1, 4, 9, 16]
```

#### With Conditions:
```python
# Even numbers only
evens = [x for x in range(10) if x % 2 == 0]
print(evens)  # [0, 2, 4, 6, 8]

# String manipulation
names = ["alice", "bob", "charlie"]
capitalized = [name.capitalize() for name in names]
print(capitalized)  # ['Alice', 'Bob', 'Charlie']
```

#### Nested Comprehension:
```python
# Matrix flattening
matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
flattened = [num for row in matrix for num in row]
print(flattened)  # [1, 2, 3, 4, 5, 6, 7, 8, 9]
```

---

## Part 3: Object-Oriented Programming

### 3.1 Classes and Objects

#### What is a Class?

A **class** is a blueprint for creating objects. An **object** is an instance of a class.

```python
# Defining a class
class Dog:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def bark(self):
        return f"{self.name} says Woof!"

    def describe(self):
        return f"{self.name} is {self.age} years old"

# Creating objects
dog1 = Dog("Buddy", 3)
dog2 = Dog("Max", 5)

print(dog1.bark())       # Buddy says Woof!
print(dog2.describe())   # Max is 5 years old
```

#### Class vs Instance Attributes:
```python
class Dog:
    species = "Canis familiaris"  # Class attribute (shared)

    def __init__(self, name, age):
        self.name = name  # Instance attribute (unique)
        self.age = age

dog1 = Dog("Buddy", 3)
dog2 = Dog("Max", 5)

print(dog1.species)  # Canis familiaris
print(dog2.species)  # Canis familiaris (same)
print(dog1.name)     # Buddy
print(dog2.name)     # Max (different)
```

---

### 3.2 Inheritance

#### Base and Derived Classes:
```python
# Base class
class Animal:
    def __init__(self, name):
        self.name = name

    def speak(self):
        raise NotImplementedError("Subclass must implement")

# Derived class
class Dog(Animal):
    def speak(self):
        return f"{self.name} says Woof!"

class Cat(Animal):
    def speak(self):
        return f"{self.name} says Meow!"

# Using derived classes
dog = Dog("Buddy")
cat = Cat("Whiskers")

print(dog.speak())  # Buddy says Woof!
print(cat.speak())  # Whiskers says Meow!
```

---

### 3.3 When to Use OOP

#### Good Use Cases:
```python
# API client (good for OOP)
class LLMClient:
    def __init__(self, api_url, model):
        self.api_url = api_url
        self.model = model

    def chat(self, message):
        # API call logic
        return f"Response from {self.model}"

    def stream(self, message):
        # Streaming logic
        return f"Streaming from {self.model}"

# Using the client
client = LLMClient("http://localhost:11434", "mistral")
print(client.chat("Hello"))  # Response from mistral
```

#### When NOT to Use OOP:
```python
# Simple functions are better for simple tasks

# BAD: Unnecessary OOP
class Calculator:
    def add(self, a, b):
        return a + b

# GOOD: Simple function
def add(a, b):
    return a + b
```

---

## Part 4: Practical Skills

### 4.1 File I/O

#### Reading Files:
```python
# Read entire file
with open("file.txt", "r") as f:
    content = f.read()
    print(content)

# Read line by line
with open("file.txt", "r") as f:
    for line in f:
        print(line.strip())

# Read into list
with open("file.txt", "r") as f:
    lines = f.readlines()
    print(lines)
```

#### Writing Files:
```python
# Write text
with open("output.txt", "w", encoding="utf-8") as f:
    f.write("Hello, World!\n")
    f.write("This is a new line.")

# Append to file
with open("output.txt", "a", encoding="utf-8") as f:
    f.write("\nThis is appended.")
```

#### JSON Files (Important for AI):
```python
import json

# Write JSON
data = {
    "name": "Alice",
    "age": 30,
    "city": "NYC"
}

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# Read JSON
with open("data.json", "r") as f:
    loaded = json.load(f)
    print(loaded)  # {'name': 'Alice', 'age': 30, 'city': 'NYC'}
```

---

### 4.2 Error Handling

#### Try/Except:
```python
# Basic error handling
try:
    result = 10 / 0
except ZeroDivisionError:
    print("Cannot divide by zero!")

# Multiple exceptions
try:
    number = int("not a number")
except ValueError:
    print("Invalid number!")
except Exception as e:
    print(f"Error: {e}")

# Finally block
try:
    f = open("file.txt", "r")
    content = f.read()
except FileNotFoundError:
    print("File not found!")
finally:
    print("Cleanup code here")
```

#### Raising Exceptions:
```python
def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

try:
    result = divide(10, 0)
except ValueError as e:
    print(f"Error: {e}")  # Error: Cannot divide by zero
```

---

### 4.3 Working with Packages

#### Installing Packages:
```bash
# Using uv (the 2026 curriculum standard - 10-100x faster than pip)
uv pip install requests
uv pip install numpy
uv pip install pandas

# Multiple packages
uv pip install requests numpy pandas

# From a project's lockfile (the standard share format - see 4.4)
uv sync --locked
```

> Every `pip install X` you see online maps 1:1 to `uv pip install X`.

#### Importing Modules:
```python
# Import module
import math
print(math.sqrt(16))  # 4.0

# Import specific function
from math import sqrt
print(sqrt(16))  # 4.0

# Import with alias
import numpy as np
arr = np.array([1, 2, 3])
print(arr)  # [1 2 3]

# Import all (not recommended)
from math import *
print(sqrt(16))  # 4.0
```

#### Creating Your Own Module:
```python
# mymodule.py
def greet(name):
    return f"Hello, {name}!"

PI = 3.14159

# main.py
import mymodule

print(mymodule.greet("Alice"))  # Hello, Alice!
print(mymodule.PI)              # 3.14159
```

---

### 4.4 Virtual Environments

#### Why Virtual Environments?

Virtual environments isolate project dependencies.

#### uv (Recommended):
```bash
# Create a project environment (uv downloads Python 3.13 if missing)
uv venv --python 3.13

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install packages (uv finds .venv automatically)
uv pip install requests

# Deactivate
deactivate
```

#### venv (Built-in fallback):
```bash
# Create virtual environment
python -m venv myenv

# Activate (Windows)
myenv\Scripts\activate

# Activate (Mac/Linux)
source myenv/bin/activate

# Install packages (uv pip works in any active venv, built-in included)
uv pip install requests

# Deactivate
deactivate
```

#### Project workflow (reproducibility):

For anything you share or deploy, the project manifest is the modern
standard - `pyproject.toml` declares dependencies, `uv.lock` pins the
exact graph, and one command recreates it anywhere.

```bash
# Create the project manifest
uv init --bare --python 3.13 .

# Add dependencies - writes pyproject.toml and uv.lock
uv add requests numpy pandas

# Recreate the exact locked environment anywhere
uv sync --locked
```

### 4.5 Code Quality: Lint and Format Your Code

Writing code that runs is step one. Code that stays clean and consistent is what makes projects maintainable — and it matters from your very first script, not just in team settings.

The 2026 standard is [ruff](https://docs.astral.sh/ruff/) — one Rust-fast tool that lints (finds bugs and style problems) and formats (makes spacing, quotes and line length consistent). You do not even install it: `uvx` runs it in an ephemeral, cached environment.

```bash
# Check your code for errors, unused imports and style issues
uvx ruff check .

# Auto-fix what ruff can fix safely, then format every file
uvx ruff check --fix .
uvx ruff format .
```

What ruff catches for you:
- **Bugs:** unused variables and imports, undefined names, f-string mistakes
- **Style:** inconsistent quotes, spacing and import order (no more bikeshedding)
- **Modernization:** old idioms that have cleaner Python 3.13 replacements

**Make it a habit:** run `uvx ruff check .` after every exercise in this tutorial — catching an unused import yourself is how the habit sticks. The full tooling setup lives in [Environment Setup](../../00-META/ENVIRONMENT-SETUP.md).

---

## Part 5: AI-Specific Python

### 5.1 NumPy for AI (CRITICAL for Phase 2!)

#### Why NumPy is Essential

**NumPy** is the foundation of all AI/ML in Python. PyTorch tensors are built on NumPy concepts.

> ⚠️ **IMPORTANT:** If you skip NumPy, you will STRUGGLE in Phase 2 (tensors, gradients, backprop).
> Spend extra time here - it pays off!

#### Installation:
```bash
uv pip install numpy
```

---

#### 5.1.1 Creating Arrays (Tensors)

```python
import numpy as np

# From list
arr = np.array([1, 2, 3, 4, 5])
print(arr)           # [1 2 3 4 5]
print(arr.shape)     # (5,) - 1D tensor (vector)
print(arr.dtype)     # int64

# Specific data types (CRITICAL for AI!)
float_arr = np.array([1, 2, 3], dtype=np.float32)
print(float_arr.dtype)  # float32

# Zeros and ones
zeros = np.zeros(5)        # [0. 0. 0. 0. 0.]
ones = np.ones((3, 3))     # 3x3 matrix of ones
full = np.full((2, 4), 7)  # 2x4 matrix filled with 7s

# Range (like Python's range)
range_arr = np.arange(0, 10, 2)  # [0 2 4 6 8]

# Linearly spaced numbers (useful for learning rates!)
linspace = np.linspace(0, 1, 5)   # [0.   0.25 0.5  0.75 1.  ]

# Identity matrix (CRITICAL for attention mechanisms!)
identity = np.eye(3)
print(identity)
# [[1. 0. 0.]
#  [0. 1. 0.]
#  [0. 0. 1.]]

# Random arrays (CRITICAL for weight initialization!)
np.random.seed(42)  # Reproducibility!
random_uniform = np.random.rand(3, 2)    # Uniform [0, 1)
random_normal = np.random.randn(3, 2)    # Normal distribution
random_int = np.random.randint(0, 10, (3, 3))  # Random integers
```

---

#### 5.1.2 Array Shapes and Reshaping (CRITICAL!)

```python
import numpy as np

# Understanding shape
scalar = np.array(5)
print(scalar.shape)     # () - 0D tensor (scalar)

vector = np.array([1, 2, 3])
print(vector.shape)     # (3,) - 1D tensor

matrix = np.array([[1, 2], [3, 4]])
print(matrix.shape)     # (2, 2) - 2D tensor

tensor3d = np.array([[[1, 2], [3, 4]], [[5, 6], [7, 8]]])
print(tensor3d.shape)   # (2, 2, 2) - 3D tensor

# Batch of images example (common in AI!)
batch_images = np.random.randn(32, 3, 224, 224)
print(batch_images.shape)  # (32, 3, 224, 224)
# Meaning: 32 images, 3 channels (RGB), 224x224 pixels

# Reshaping (CRITICAL for neural networks!)
arr = np.arange(12)
print(arr)              # [ 0  1  2  3  4  5  6  7  8  9 10 11]

reshaped = arr.reshape(3, 4)
print(reshaped)
# [[ 0  1  2  3]
#  [ 4  5  6  7]
#  [ 8  9 10 11]]

# Flattening (for output layers!)
matrix = np.array([[1, 2], [3, 4]])
flat = matrix.flatten()  # or matrix.ravel()
print(flat)  # [1 2 3 4]

# Adding/removing dimensions
arr = np.array([1, 2, 3])
print(arr.shape)        # (3,)

# Add dimension (for batch processing!)
batch = arr[np.newaxis, :]
print(batch.shape)      # (1, 3)

# Squeeze (remove single dimensions)
squeezed = np.squeeze(batch)
print(squeezed.shape)   # (3,)
```

---

#### 5.1.3 Indexing and Slicing (CRITICAL!)

```python
import numpy as np

arr = np.array([10, 20, 30, 40, 50])

# Basic indexing
print(arr[0])      # 10
print(arr[-1])     # 50 (last element)

# Slicing
print(arr[1:4])    # [20 30 40]
print(arr[:3])     # [10 20 30]
print(arr[2:])     # [30 40 50]
print(arr[::2])    # [10 30 50] (every 2nd element)

# 2D array slicing
matrix = np.array([
    [1, 2, 3, 4],
    [5, 6, 7, 8],
    [9, 10, 11, 12]
])

# Single element
print(matrix[0, 0])   # 1
print(matrix[1, 2])   # 7

# Row/column slicing
print(matrix[0, :])   # [1 2 3 4] (first row)
print(matrix[:, 0])   # [1 5 9] (first column)

# Sub-matrix (CRITICAL for attention heads!)
print(matrix[0:2, 1:3])
# [[2 3]
#  [6 7]]

# Boolean indexing (CRITICAL for filtering!)
arr = np.array([1, 2, 3, 4, 5])
mask = arr > 3
print(mask)           # [False False False  True  True]
print(arr[mask])      # [4 5]

# Fancy indexing
arr = np.array([10, 20, 30, 40, 50])
indices = [0, 2, 4]
print(arr[indices])   # [10 30 50]
```

---

#### 5.1.4 Broadcasting (CRITICAL for operations!)

```python
import numpy as np

# Same shape operations
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])
print(a + b)  # [5 7 9]

# Broadcasting: scalar with array
a = np.array([1, 2, 3])
print(a * 5)  # [5 10 15]

# Broadcasting: different shapes
a = np.array([[1, 2, 3], [4, 5, 6]])  # (2, 3)
b = np.array([10, 20, 30])            # (3,)
print(a + b)
# [[11 22 33]
#  [14 25 36]]
# b is "stretched" to match a's shape!

# Broadcasting rules (memorize!)
# 1. Align shapes on the RIGHT
# 2. Dimensions must match OR one must be 1
# 3. Result shape is the maximum

# Example: (3, 4) + (4,) = (3, 4)
# Example: (3, 1) + (1, 4) = (3, 4)
# Example: (2, 3, 4) + (1, 4) = (2, 3, 4)

# Practical example: adding bias to neural network layer
activations = np.random.randn(10, 50)  # 10 samples, 50 neurons
bias = np.random.randn(50)             # 50 biases
output = activations + bias            # Broadcasting! (10, 50)
print(output.shape)  # (10, 50)
```

---

#### 5.1.5 Linear Algebra Operations (CRITICAL for Phase 2!)

```python
import numpy as np

# Matrix multiplication (THE most important operation!)
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

# Method 1: np.dot()
result1 = np.dot(A, B)

# Method 2: @ operator (preferred!)
result2 = A @ B

print(result2)
# [[19 22]
#  [43 50]]

# Element-wise multiplication (different!)
print(A * B)
# [[ 5 12]
#  [21 32]]

# Transpose (CRITICAL for attention!)
A = np.array([[1, 2], [3, 4]])
print(A.T)
# [[1 3]
#  [2 4]]

# Matrix norms (for regularization!)
A = np.array([[1, 2], [3, 4]])
print(np.linalg.norm(A))      # Frobenius norm
print(np.linalg.norm(A, ord=2))  # Spectral norm

# Solving linear systems (for optimization!)
A = np.array([[3, 1], [1, 2]])
b = np.array([9, 8])
x = np.linalg.solve(A, b)
print(x)  # [2. 3.] (3x1 + 1x3 = 9, 1x2 + 2x3 = 8)

# Eigenvalues and eigenvectors (for PCA, understanding matrices!)
A = np.array([[4, -2], [1, 1]])
eigenvalues, eigenvectors = np.linalg.eig(A)
print(eigenvalues)   # [3. 2.]
print(eigenvectors)
# [[0.894 0.707]
#  [0.447 0.707]]

# SVD (CRITICAL for understanding transformers!)
A = np.array([[1, 2], [3, 4], [5, 6]])
U, S, Vt = np.linalg.svd(A)
print(U.shape)  # (3, 3)
print(S.shape)  # (2,) - singular values
print(Vt.shape) # (2, 2)
```

---

#### 5.1.6 Statistical Operations (CRITICAL for normalization!)

```python
import numpy as np

arr = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

# Basic statistics
print(arr.mean())     # 5.5 (average)
print(arr.sum())      # 55 (total)
print(arr.std())      # 2.87 (standard deviation)
print(arr.var())      # 8.25 (variance)
print(arr.min())      # 1
print(arr.max())      # 10
print(np.median(arr)) # 5.5

# Percentiles (for anomaly detection!)
print(np.percentile(arr, 25))  # 3.25 (Q1)
print(np.percentile(arr, 50))  # 5.5 (Q2 = median)
print(np.percentile(arr, 75))  # 7.75 (Q3)

# Axis operations (CRITICAL for batch processing!)
matrix = np.array([
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
])

# Mean along rows (axis=0)
print(matrix.mean(axis=0))  # [4. 5. 6.] (column means)

# Mean along columns (axis=1)
print(matrix.mean(axis=1))  # [2. 5. 8.] (row means)

# Cumulative operations
arr = np.array([1, 2, 3, 4])
print(np.cumsum(arr))  # [ 1  3  6 10] (cumulative sum)
print(np.cumprod(arr)) # [ 1  2  6 24] (cumulative product)
```

---

#### 5.1.7 Practical AI Examples

```python
import numpy as np

# Example 1: Softmax function (CRITICAL for transformers!)
def softmax(x):
    """Convert logits to probabilities."""
    exp_x = np.exp(x - np.max(x))  # Numerical stability
    return exp_x / exp_x.sum()

logits = np.array([2.0, 1.0, 0.1])
probs = softmax(logits)
print(probs)  # [0.659 0.242 0.098]
print(probs.sum())  # 1.0 (probabilities sum to 1)

# Example 2: Batch softmax
batch_logits = np.array([
    [2.0, 1.0, 0.1],
    [1.0, 3.0, 0.5],
    [0.5, 0.5, 2.0]
])
exp_logits = np.exp(batch_logits - batch_logits.max(axis=1, keepdims=True))
batch_probs = exp_logits / exp_logits.sum(axis=1, keepdims=True)
print(batch_probs.shape)  # (3, 3)

# Example 3: ReLU activation
def relu(x):
    """Rectified Linear Unit: max(0, x)."""
    return np.maximum(0, x)

x = np.array([-1, 0, 1, 2])
print(relu(x))  # [0 0 1 2]

# Example 4: Normalization (CRITICAL for training stability!)
def normalize(x):
    """Normalize to zero mean, unit variance."""
    return (x - x.mean()) / x.std()

data = np.array([1, 2, 3, 4, 5])
normalized = normalize(data)
print(normalized.mean())  # ~0
print(normalized.std())   # ~1

# Example 5: Attention mechanism (simplified!)
def simple_attention(query, key, value):
    """
    Simplified scaled dot-product attention.

    Args:
        query: (seq_len, d_k)
        key: (seq_len, d_k)
        value: (seq_len, d_v)

    Returns:
        context: (seq_len, d_v)
    """
    # Scaled dot-product
    scores = query @ key.T / np.sqrt(query.shape[-1])
    # Softmax
    weights = softmax(scores)
    # Weighted sum
    context = weights @ value
    return context

seq_len, d_k, d_v = 5, 4, 4
Q = np.random.randn(seq_len, d_k)
K = np.random.randn(seq_len, d_k)
V = np.random.randn(seq_len, d_v)

output = simple_attention(Q, K, V)
print(output.shape)  # (5, 4)
```

---

#### 5.1.8 Performance Tips

```python
import numpy as np

# ALWAYS use vectorized operations (not loops!)
arr = np.array([1, 2, 3, 4, 5])

# BAD: Python loop
result_slow = []
for x in arr:
    result_slow.append(x * 2)

# GOOD: Vectorized
result_fast = arr * 2

# Vectorized is 100x+ faster!

# Memory views (no copying)
arr = np.array([1, 2, 3, 4, 5])
view = arr[1:4]       # View (no copy)
copy = arr[1:4].copy()  # Copy

view[0] = 999
print(arr)  # [  1 999   3   4   5] (original modified!)

# In-place operations (save memory!)
arr = np.array([1.0, 2.0, 3.0])
arr *= 2     # In-place (no new array)
arr = arr * 2  # NOT in-place (creates new array)
```

---

#### Summary: NumPy Checklist

Before moving to Phase 2, ensure you understand:

- [ ] Creating arrays with different shapes and dtypes
- [ ] Reshaping and flattening tensors
- [ ] Indexing and slicing (including boolean indexing)
- [ ] Broadcasting rules
- [ ] Matrix multiplication (@ operator)
- [ ] Linear algebra operations (transpose, SVD, eigenvalues)
- [ ] Statistical operations along axes
- [ ] Implementing softmax, ReLU, normalization
- [ ] Understanding attention mechanism with NumPy

> 🚨 **If you're unsure about any of these, REVIEW again!**
> Phase 2 assumes 100% fluency with these concepts.

---

### 5.2 Type Hints

#### What are Type Hints?

**Type hints** specify expected types for variables and function parameters.

#### Basic Type Hints:
```python
# Variable annotations
name: str = "Alice"
age: int = 30
height: float = 1.75
is_student: bool = True

# Function annotations
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    return a + b

# Usage
message = greet("Bob")  # OK
result = add(5, 3)      # OK
```

#### Complex Types:
```python

# List type
def process_numbers(numbers: list[int]) -> list[int]:
    return [x * 2 for x in numbers]

# Dict type
def get_config() -> dict[str, str]:
    return {"model": "mistral", "api": "localhost"}

# Optional type
def find_user(user_id: int) -> str | None:
    if user_id == 1:
        return "Alice"
    return None

# Union type
def process(value: int | str) -> str:
    return str(value)
```

#### Why Type Hints?
```python
# Better code documentation
def train_model(
    epochs: int,
    batch_size: int,
    learning_rate: float,
    use_gpu: bool = True
) -> float:
    """Train a model and return accuracy.

    Args:
        epochs: Number of training epochs
        batch_size: Batch size for training
        learning_rate: Learning rate for optimizer
        use_gpu: Whether to use GPU acceleration

    Returns:
        Final accuracy score
    """
    # Implementation here
    return 0.95
```

---

### 5.3 Async/Await (Introduction)

#### What is Async?

**Async** allows concurrent code execution without blocking.

#### Basic Async:
```python
import asyncio

# Async function
async def greet(name: str) -> str:
    await asyncio.sleep(1)  # Simulate I/O
    return f"Hello, {name}!"

# Running async
async def main():
    result = await greet("Alice")
    print(result)

# Run async code
asyncio.run(main())
```

#### Concurrent Tasks:
```python
import asyncio

async def fetch_data(url: str) -> str:
    await asyncio.sleep(1)  # Simulate network delay
    return f"Data from {url}"

async def main():
    # Run concurrently
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    for result in results:
        print(result)

asyncio.run(main())
```

---

### 5.4 Pydantic Data Models (CRITICAL for TUTORIAL-003)

#### What is Pydantic?

**Pydantic** is a data validation library that uses Python type annotations. It's ESSENTIAL for modern AI/ML APIs.

#### Why Pydantic?

TUTORIAL-003 and beyond use Pydantic extensively:
```python
from pydantic import BaseModel

class Query(BaseModel):
    text: str
    use_rag: bool = True
    top_k: int = 3
```

**Without Pydantic knowledge, you will get STUCK in TUTORIAL-003!**

#### Installation:
```bash
uv pip install pydantic
```

#### Basic Pydantic Models

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    """Simple user model"""
    name: str
    age: int
    email: str

# Create user
user = User(name="Alice", age=30, email="alice@example.com")
print(user)
# Output: name='Alice' age=30 email='alice@example.com'

# Access fields
print(user.name)   # Alice
print(user.age)    # 30
```

#### Field Validation

```python
from pydantic import BaseModel, Field, EmailStr

class User(BaseModel):
    """User with validation"""
    name: str = Field(..., min_length=1, max_length=50)
    age: int = Field(..., ge=0, le=120)  # ge=greater/equal, le=less/equal
    email: EmailStr  # Email validation
    bio: str | None = None  # Optional field

# Valid user
user = User(name="Bob", age=25, email="bob@example.com")
print(user)

# Invalid user (will raise error)
try:
    invalid_user = User(name="", age=150, email="bad-email")
except Exception as e:
    print(f"Validation error: {e}")
```

#### Nested Models

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str
    country: str

class Person(BaseModel):
    name: str
    age: int
    addresses: list[Address]  # List of nested models

# Create person with addresses
person = Person(
    name="Alice",
    age=30,
    addresses=[
        Address(street="123 Main St", city="NYC", country="USA"),
        Address(street="456 Park Ave", city="NYC", country="USA")
    ]
)
print(person)
```

#### Default Values and Required Fields

```python
from pydantic import BaseModel

class Query(BaseModel):
    """Query model for RAG"""
    text: str  # Required field
    use_rag: bool = True  # Default value
    top_k: int = 5  # Default value
    min_score: float | None = None  # Optional

# Create query
query = Query(text="What is AI?")
print(query)
# Output: text='What is AI?' use_rag=True top_k=5 min_score=None

# With overrides
query2 = Query(text="What is ML?", use_rag=False, top_k=10)
print(query2)
```

#### Pydantic with JSON

```python
import json
from pydantic import BaseModel

class Config(BaseModel):
    model_name: str
    parameters: str
    quantization: str
    epochs: int = 3

# From JSON string
json_str = '{"model_name": "mistral", "parameters": "7b", "quantization": "4-bit"}'
config = Config.parse_raw(json_str)
print(config)

# From JSON file
# config.json contains: {"model_name": "mistral", ...}
with open("config.json", "r") as f:
    config = Config.parse_raw(f.read())
print(config)
```

---

### 5.5 FastAPI Web Framework (CRITICAL for TUTORIAL-003)

#### What is FastAPI?

**FastAPI** is a modern, fast web framework for building APIs with Python. It's the standard for AI/ML services.

#### Why FastAPI?

TUTORIAL-003 uses FastAPI extensively:
```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/query")
def query(query: Query):
    return {"result": "..."}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

**Without FastAPI knowledge, you will get STUCK in TUTORIAL-003!**

#### Installation:
```bash
uv pip install fastapi uvicorn
```

#### Basic FastAPI App

```python
from fastapi import FastAPI

app = FastAPI(title="My API")

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id, "name": f"Item {item_id}"}
```

#### Path Parameters and Query Parameters

```python
from fastapi import FastAPI


app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int, q: str | None = None):
    """
    user_id: Path parameter (required) - /users/123
    q: Query parameter (optional) - /users/123?q=search
    """
    return {"user_id": user_id, "query": q}

# Examples:
# GET /users/123 → {"user_id": 123, "query": null}
# GET /users/123?q=search → {"user_id": 123, "query": "search"}
```

#### Request Body (Pydantic Models)

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class UserRequest(BaseModel):
    name: str
    age: int
    email: str

@app.post("/users")
def create_user(user: UserRequest):
    """
    Request body:
    {
        "name": "Alice",
        "age": 30,
        "email": "alice@example.com"
    }
    """
    return {
        "message": "User created",
        "user": user
    }
```

#### Combining Pydantic + FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field


app = FastAPI(title="RAG API")

class Document(BaseModel):
    text: str = Field(..., min_length=1)
    metadata: dict | None = None

class QueryRequest(BaseModel):
    question: str
    use_rag: bool = True
    top_k: int = Field(default=5, ge=1, le=10)

@app.post("/query")
def query_rag(request: QueryRequest):
    """Query RAG system"""
    return {
        "question": request.question,
        "use_rag": request.use_rag,
        "top_k": request.top_k,
        "answer": "This is where RAG happens"
    }

@app.post("/documents")
def add_document(doc: Document):
    """Add document to knowledge base"""
    return {
        "message": "Document added",
        "doc_id": 123
    }
```

#### Testing Your API (TestClient)

You don't need to run a server to test endpoints — `TestClient` (built on `httpx`) calls the app in-process:

```python
from fastapi.testclient import TestClient

client = TestClient(app)  # the RAG API above — no server process needed

# Smoke-test the endpoints
resp = client.post("/query", json={"question": "What is RAG?"})
assert resp.status_code == 200
assert resp.json()["top_k"] == 5  # default applied

resp = client.post("/query", json={"question": "What is RAG?", "top_k": 99})
assert resp.status_code == 422  # le=10 constraint enforced

resp = client.post("/documents", json={"text": ""})
assert resp.status_code == 422  # min_length=1 constraint enforced

print("All API smoke tests passed")
```

#### Running FastAPI

```python
# Save as main.py
import uvicorn

# Run the server
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

```bash
# Run from terminal
uvicorn main:app --reload

# Access the API
# http://localhost:8000/docs (interactive API documentation)
```

---

### 5.6 Working with APIs

#### Making HTTP Requests:
```python
import requests

# GET request
response = requests.get("https://api.github.com/users/octocat")
print(response.status_code)  # 200
print(response.json())        # JSON data

# POST request
data = {"message": "Hello, API!"}
response = requests.post("https://httpbin.org/post", json=data)
print(response.json())
```

#### Ollama API Example (Preview for TUTORIAL-001):
```python
import requests

API_URL = "http://localhost:11434/api/chat"

def chat(message: str, model: str = "mistral") -> str:
    """Send a message to Ollama and get a response."""

    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": message}
        ],
        "stream": False
    }

    response = requests.post(API_URL, json=payload)
    result = response.json()

    return result["message"]["content"]

# Usage
response = chat("What is AI?")
print(response)
```

---

## Practice Exercises

### Exercise 1: Calculator (30 minutes)

Create a calculator function that can add, subtract, multiply, and divide.

```python
def calculator(a: float, b: float, operation: str) -> float:
    """Perform a calculation.

    Args:
        a: First number
        b: Second number
        operation: One of 'add', 'subtract', 'multiply', 'divide'

    Returns:
        Result of the calculation
    """
    # Your code here
    pass

# Test
print(calculator(10, 5, "add"))       # 15.0
print(calculator(10, 5, "subtract"))  # 5.0
print(calculator(10, 5, "multiply"))  # 50.0
print(calculator(10, 5, "divide"))    # 2.0
```

**Solution:**

```python
def calculator(a: float, b: float, operation: str) -> float:
    operations = {
        "add": lambda x, y: x + y,
        "subtract": lambda x, y: x - y,
        "multiply": lambda x, y: x * y,
        "divide": lambda x, y: x / y if y != 0 else "Error: Division by zero"
    }

    if operation not in operations:
        raise ValueError(f"Unknown operation: {operation}")

    return operations[operation](a, b)
```

---

### Exercise 2: Todo List Manager (45 minutes)

Create a todo list manager using dictionaries.

```python
class TodoManager:
    def __init__(self):
        self.todos = {}

    def add(self, title: str, description: str = "") -> int:
        """Add a new todo item."""
        # Your code here
        pass

    def complete(self, todo_id: int) -> bool:
        """Mark a todo as complete."""
        # Your code here
        pass

    def list(self) -> list:
        """List all todos."""
        # Your code here
        pass

# Test
manager = TodoManager()
manager.add("Learn Python", "Complete TUTORIAL-000")
manager.add("Build AI App")
manager.complete(1)
print(manager.list())
```

**Solution:**

```python
class TodoManager:
    def __init__(self):
        self.todos = {}
        self.next_id = 1

    def add(self, title: str, description: str = "") -> int:
        todo_id = self.next_id
        self.todos[todo_id] = {
            "title": title,
            "description": description,
            "completed": False
        }
        self.next_id += 1
        return todo_id

    def complete(self, todo_id: int) -> bool:
        if todo_id in self.todos:
            self.todos[todo_id]["completed"] = True
            return True
        return False

    def list(self) -> list:
        return [
            {"id": id, **todo}
            for id, todo in self.todos.items()
        ]
```

---

### Exercise 3: JSON Config Loader (30 minutes)

Create a function to load and validate AI model configuration.

```python
import json
from typing import Any

def load_config(config_path: str) -> dict[str, Any]:
    """Load and validate AI model configuration.

    Required keys:
        - model.name: str
        - model.parameters: str
        - training.epochs: int
        - training.batch_size: int

    Args:
        config_path: Path to config JSON file

    Returns:
        Validated configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    # Your code here
    pass

# Test
config = load_config("config.json")
print(config)
```

**Solution:**

```python
def load_config(config_path: str) -> dict[str, Any]:
    with open(config_path, "r") as f:
        config = json.load(f)

    # Validate required keys
    required_keys = [
        ("model", "name"),
        ("model", "parameters"),
        ("training", "epochs"),
        ("training", "batch_size")
    ]

    for key_path in required_keys:
        current = config
        for key in key_path:
            if key not in current:
                raise ValueError(f"Missing required key: {'.'.join(key_path)}")
            current = current[key]

    return config
```

---

## Completion Checklist

```text
[ ] Part 1: Python Basics (2 hours)
    [ ] 1.1 What is Python?
    [ ] 1.2 Installing Python
    [ ] 1.3 Your First Code
    [ ] 1.4 Variables and Types
    [ ] 1.5 Operators
    [ ] 1.6 Control Flow
    [ ] 1.7 Loops
    [ ] 1.8 Functions

[ ] Part 2: Data Structures (2 hours)
    [ ] 2.1 Lists
    [ ] 2.2 Tuples
    [ ] 2.3 Dictionaries
    [ ] 2.4 Sets
    [ ] 2.5 List Comprehensions

[ ] Part 3: OOP (1 hour)
    [ ] 3.1 Classes and Objects
    [ ] 3.2 Inheritance
    [ ] 3.3 When to Use OOP

[ ] Part 4: Practical Skills (1 hour)
    [ ] 4.1 File I/O
    [ ] 4.2 Error Handling
    [ ] 4.3 Packages
    [ ] 4.4 Virtual Environments
    [ ] 4.5 Code Quality (ruff)

[ ] Part 5: AI-Specific Python (4-6 hours)
    [ ] 5.1 NumPy Basics
    [ ] 5.2 Type Hints
    [ ] 5.3 Async/Await
    [ ] 5.4 Pydantic Data Models (CRITICAL)
    [ ] 5.5 FastAPI Web Framework (CRITICAL)
    [ ] 5.6 Working with APIs

[ ] Exercises
    [ ] Exercise 1: Calculator
    [ ] Exercise 2: Todo Manager
    [ ] Exercise 3: JSON Config Loader
```

---

## What's Next?

Congratulations! You now have the Python skills needed for AI development!

### Continue Your Journey:

1. **[TUTORIAL-001: Hello LLM](TUTORIAL-001-Hello-LLM.md)** - Build your first AI application
2. **[TUTORIAL-002: Docker Essentials](TUTORIAL-002-Docker-Essentials.md)** - Container fundamentals
3. **[TUTORIAL-003: RAG Basics](TUTORIAL-003-RAG-Basics.md)** - Give your LLM knowledge
4. **[LAB-001: Docker & LLM](../labs/LAB-001-Docker-LLM.md)** - Hands-on practice

### Recommended Learning Path:

```text
TUTORIAL-000: Python for AI (YOU ARE HERE)
         ↓
TUTORIAL-001: Hello LLM (Build your first AI app)
         ↓
TUTORIAL-002: Docker Essentials (Container fundamentals)
         ↓
TUTORIAL-003: RAG Basics (Knowledge augmentation)
         ↓
LAB-001: Docker & LLM (Hands-on practice)
         ↓
PROJECT-001: AI Assistant (Complete project)
```

---

## Additional Resources

### Free Python Tutorials:
- **Python.org Tutorial**: [https://docs.python.org/3/tutorial/](https://docs.python.org/3/tutorial/)
- **W3Schools Python**: [https://www.w3schools.com/python/](https://www.w3schools.com/python/)
- **Real Python**: [https://realpython.com/](https://realpython.com/)

### Interactive Learning:
- **Codecademy Python**: [https://www.codecademy.com/learn/learn-python-3](https://www.codecademy.com/learn/learn-python-3)
- **Edabit Python Challenges**: [https://edabit.com/challenges/python3](https://edabit.com/challenges/python3)

### Books:
- **Python Crash Course** by Eric Matthes
- **Automate the Boring Stuff** by Al Sweigart
- **Fluent Python** by Luciano Ramalho (Advanced)

---

**Time Estimate:** 20 hours
**Difficulty:** ⭐ Beginner
**Prerequisites:** None

> ℹ️ **Time Estimate:** This tutorial has been significantly expanded to include NumPy, Pydantic, and FastAPI fundamentals. Plan for 15-20 hours of focused learning, ideally spread over 1-2 weeks for proper retention.

**Ready to build AI?** Start with [TUTORIAL-001: Hello LLM](TUTORIAL-001-Hello-LLM.md) 🚀
