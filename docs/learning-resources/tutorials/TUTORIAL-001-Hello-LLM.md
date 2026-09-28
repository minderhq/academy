---
Document ID: TUTORIAL-001
Title: "Tutorial 001: Hello LLM! - Your First AI Model"
Last Updated: 2026-09-28
Status: Complete
Difficulty: Intermediate
---

# Tutorial 001: Hello LLM! - Your First AI Model

**Difficulty:** ⭐ Beginner
**Time:** 30 minutes
**Prerequisites:**
- **Basic Python knowledge** (variables, functions, loops)
- **Python 3.13+ installed**

:information_source: **New to Python?** Start with **[TUTORIAL-000: Python for AI](TUTORIAL-000-Python-for-AI.md)** (15-20 hours) to learn the fundamentals.

---

## Learning Objectives

By the end of this tutorial, you will:
- ✅ Understand what an LLM is
- ✅ Run your first local LLM
- ✅ Generate text with AI
- ✅ Basic prompting skills

---

## What is an LLM?

**LLM** = **Large Language Model**

Think of it as a very smart text-completion engine:
- Trained on billions of words from the internet
- Can write stories, code, poetry, and more
- Understands context and follows instructions

### How LLMs Work (Simplified)

```text
Input: "The sky is"
          ↓
    LLM Brain
    (predicts next word)
          ↓
Output: "blue" (most likely)
       "cloudy" (less likely)
       "falling" (context dependent)
```

---

## Step 1: Install Ollama

**Ollama** is the easiest way to run LLMs locally.

### Mac/Linux:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Windows:
Download from: https://ollama.com/download

### Verify Installation:
```bash
ollama --version
```

---

## Step 2: Download Your First Model

We'll use **Mistral 7B** - a powerful, efficient model.

```bash
ollama pull mistral
```

**What's happening?**
- Downloading ~4GB model file
- This will take a few minutes depending on your internet

### Model Sizes:
- **7B** = 7 billion parameters (beginner friendly)
- **13B** = 13 billion parameters (better quality)
- **70B** = 70 billion parameters (best quality, needs more RAM)

---

## Step 3: Run Your First Chat

### Interactive Chat:
```bash
ollama run mistral
```

**Try these prompts:**
```text
1. Hello! What can you do?

2. Write a haiku about AI

3. Explain quantum computing to a 5-year-old

4. Write Python code to sort a list
```

### Exit the chat:
Type `/bye` or press `Ctrl+C`

---

## Step 4: Use as an API

Ollama also runs a local API server!

### Start the API (if not running):
```bash
ollama serve
```

### Test with curl:
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "mistral",
  "prompt": "Why is the sky blue?",
  "stream": false
}'
```

### Response:
```json
{
  "model": "mistral",
  "response": "The sky appears blue due to a phenomenon called Rayleigh scattering...",
  "done": true
}
```

---

## Step 5: Chat API (Better Format)

```bash
curl http://localhost:11434/api/chat -d '{
  "model": "mistral",
  "messages": [
    {
      "role": "user",
      "content": "What is 2 + 2?"
    }
  ],
  "stream": false
}'
```

### Response:
```json
{
  "message": {
    "role": "assistant",
    "content": "2 + 2 equals 4."
  }
}
```

---

## Step 6: Python Integration

Let's use Python to talk to the LLM!

### Install requests:
```bash
uv pip install requests
```

### Create `hello_llm.py`:
```python
import requests
import json

API_URL = "http://localhost:11434/api/chat"

def chat(message):
    """Send a message to the LLM and get a response"""

    payload = {
        "model": "mistral",
        "messages": [
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": False
    }

    response = requests.post(API_URL, json=payload)
    result = response.json()

    return result["message"]["content"]

# Test it!
if __name__ == "__main__":
    user_input = input("You: ")

    while user_input.lower() != "bye":
        response = chat(user_input)
        print(f"AI: {response}")

        user_input = input("You: ")

    print("AI: Goodbye!")
```

### Run it:
```bash
python hello_llm.py
```

---

## Step 7: Understanding Prompts

### What is a Prompt?

A **prompt** is the input you give to the LLM.

### Prompt Engineering Basics:

#### 1. Be Clear and Specific
```text
❌ Bad: "Write code"
✅ Good: "Write a Python function that sorts a list of numbers in ascending order"
```

#### 2. Provide Context
```text
❌ Bad: "What is this?"
✅ Good: "I'm learning Python. Can you explain what this code does: def foo(): return [x*2 for x in range(10)]"
```

#### 3. Use Examples (Few-Shot)
```text
❌ Bad: "Convert to uppercase"
✅ Good: """
Convert the following words to uppercase:
- "hello" → "HELLO"
- "world" → "WORLD"
- "python" →
"""
```

---

## Step 8: Advanced Prompts

### Chain of Thought:
```text
Solve this step by step:
If I have 3 apples and eat 1, then buy 5 more, how many do I have?

Let's think:
1. Start with 3 apples
2. Eat 1: 3 - 1 = 2
3. Buy 5 more: 2 + 5 = 7

Answer: 7 apples
```

### Role Playing:
```text
You are a Python expert. Explain the difference between lists and tuples
to a beginner programmer.
```

### Format Instructions:
```text
Write a JSON object with these keys:
- name (string)
- age (number)
- city (string)

Example: {"name": "John", "age": 30, "city": "NYC"}

Now create one for: "Alice, 25, London"
```

---

## Step 9: Common Issues

### Issue: "Model not found"
**Solution:** Run `ollama pull mistral` first

### Issue: "Out of memory"
**Solution:** Try a smaller model:
```bash
ollama pull phi3  # 3B model, very light
```

### Issue: "Slow response"
**Solution:** This is normal for CPU inference. GPU is much faster (we'll cover this later!)

---

## Step 10: What's Next?

You've just:
- ✅ Installed Ollama
- ✅ Run your first LLM
- ✅ Generated text with AI
- ✅ Learned prompt basics

### Continue Your Journey:

1. **[Tutorial 002: Docker Essentials](TUTORIAL-002-Docker-Essentials.md)** - Container basics for AI
2. **[Tutorial 003: RAG Basics](TUTORIAL-003-RAG-Basics.md)** - Give the model knowledge
3. **[0000-LEARNING-PATH.md](../../00-META/0000-LEARNING-PATH.md)** - Full curriculum roadmap

---

## 🎓 Knowledge Check

Test your understanding:

1. **What does LLM stand for?**
   - Large Language Model

2. **What is a prompt?**
   - The input text you give to the LLM

3. **Why is specificity important in prompts?**
   - Clear, specific prompts get better, more accurate responses

4. **What's the difference between `ollama run` and `ollama serve`?**
   - `run` = interactive chat
   - `serve` = API server

---

## 📚 Additional Resources

- **Ollama Documentation:** https://ollama.com/docs
- **Mistral AI:** https://mistral.ai
- **Prompt Engineering Guide:** https://www.promptingguide.ai

---

## Next Steps

- **[Tutorial 002: Docker Essentials](TUTORIAL-002-Docker-Essentials.md)**
