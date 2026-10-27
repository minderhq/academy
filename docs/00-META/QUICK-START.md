---
Document ID: QUICK-START
Title: "QUICK START GUIDE: Get Started in 30 Minutes"
Last Updated: 2026-10-27
Status: Complete
Difficulty: Beginner
Tags: ['quickstart', 'tutorial', 'llm']
---

# QUICK START GUIDE: Get Started in 30 Minutes

**Fastest path to running your first local LLM**

---

## What You'll Achieve

In the next 30 minutes, you will:

1. ✅ Install Ollama (easiest LLM runner)
2. ✅ Run your first local AI model
3. ✅ Chat with Qwen3.5 0.8B
4. ✅ Understand the basics
5. ✅ Know where to go next

---

## Prerequisites

### Hardware Requirements
- Computer (Windows, Mac, or Linux)
- 8GB+ RAM (16GB+ recommended for a smoother experience)
- 10GB+ free disk space
- Stable internet connection (for model download)

### Software Requirements
- Basic command line knowledge
- Administrator/sudo access (for installation)

### Before You Start

**If you're new to command line:**

- Windows: Use PowerShell or Terminal
- Mac: Use Terminal (Applications → Utilities)
- Linux: Use your default terminal

**If you have limited resources:**

- 8GB RAM: Start with `qwen3.5:0.8b`; close memory-heavy apps if needed
- 16GB+ RAM: Try `qwen3.5:2b` for a more capable local model
- CPU-only: Models will run slower but work
- Limited disk: Start with one model at a time

### Need Help with Setup?

If you encounter any issues:

1. **Complete Setup Guide:** [ENVIRONMENT-SETUP.md](ENVIRONMENT-SETUP.md) - Detailed installation and troubleshooting
2. **Quick Start Troubleshooting:** [TROUBLESHOOTING-QUICKSTART.md](TROUBLESHOOTING-QUICKSTART.md) - Common issues and solutions
3. **Environment Lab:** [LAB-000-ENVIRONMENT-SETUP.md](../learning-resources/labs/LAB-000-ENVIRONMENT-SETUP.md) - Hands-on setup practice

---

**Ready? Let's continue!**

---

## Step 1: Install Ollama (5 minutes)

### Windows
1. Download: [https://ollama.com/download](https://ollama.com/download)
2. Run the installer
3. Open PowerShell or Command Prompt

### Mac
```bash
brew install ollama
```

### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Verify Installation
```bash
ollama --version
```

The command prints the installed Ollama version. The exact format changes between releases.

---

## Step 2: Download a Model (10 minutes)

Ollama makes it incredibly easy:

```bash
# Pull the small Qwen3.5 0.8B model for a low-memory first run
ollama pull qwen3.5:0.8b

# The model download is about 1.2 GB; leave extra disk space for runtime use.
```

### What's Happening?
- Qwen3.5 is an open-weight multimodal model family; this guide starts with its 0.8B variant
- Ollama currently lists the 0.8B download at about 1.2-1.3 GB; runtime memory also depends on context length and other running apps
- With more memory, `qwen3.5:2b` is a larger option; its listed download is about 2.7-3.1 GB
- Model sizes and available tags can change; check the [Qwen3.5 model page](https://ollama.com/library/qwen3.5) before downloading

### Other Options (for later)
```bash
ollama pull mistral:7b      # Mistral 7B, needs more memory
ollama pull llama3.2:3b     # Meta's Llama 3.2
```

### Troubleshooting Model Download

**Download stuck or very slow?**
```bash
# Check your internet connection
ping google.com

# Try again (Ollama resumes automatically)
ollama pull qwen3.5:0.8b
```

**"Connection refused" error?**
```bash
# Check if Ollama is running
# Windows: Check Task Manager for "ollama app"
# Mac/Linux: ps aux | grep ollama

# Start Ollama if not running
# Windows: Click Ollama app or run: ollama serve
# Mac/Linux: ollama serve &
```

**"Out of memory" error?**
```bash
# Your system might not have enough RAM
# Try a smaller model:
ollama pull qwen3.5:0.8b   # Use the smallest option in this guide
```

**Verify model downloaded successfully:**
```bash
ollama list
# Should show: qwen3.5:0.8b and its downloaded size
```

---

## Step 3: Chat with Your AI (10 minutes)

### Simple Chat
```bash
ollama run qwen3.5:0.8b
```

Type your message and press Enter!

**Try these:**
```text
Hello! What can you do?
Explain quantum computing like I'm five
Write a Python function to check if a number is prime
```

**To exit:** Type `/bye` or press Ctrl+D

---

## Step 4: Use with Python (5 minutes)

### Install the Ollama Python library
```bash
# uv (fast, recommended - see ENVIRONMENT-SETUP.md)
uv pip install ollama

# plain pip works too
pip install ollama
```

### Create Your First AI Script

```python
# my_first_ai.py
import ollama

# Simple chat
response = ollama.chat(model='qwen3.5:0.8b', messages=[
    {
        'role': 'user',
        'content': 'Why is the sky blue?'
    }
])

print(response['message']['content'])
```

### Run It
```bash
python my_first_ai.py
```

### Congratulations!
You just built your first AI application!

---

## Step 5: Build Something Cool (Optional)

### AI Assistant with Memory

```python
# ai_assistant.py
import ollama

class AIAssistant:
    def __init__(self, name="AI"):
        self.name = name
        self.history = []

    def chat(self, user_message):
        # Add user message to history
        self.history.append({
            'role': 'user',
            'content': user_message
        })

        # Get response from AI
        response = ollama.chat(
            model='qwen3.5:0.8b',
            messages=self.history
        )

        ai_message = response['message']['content']

        # Add AI response to history
        self.history.append({
            'role': 'assistant',
            'content': ai_message
        })

        return ai_message

# Use the assistant
assistant = AIAssistant()

print("🤖 AI Assistant (type 'quit' to exit)")
print("="*50)

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ['quit', 'exit', 'bye']:
        print(f"{assistant.name}: Goodbye!")
        break

    response = assistant.chat(user_input)
    print(f"{assistant.name}: {response}")
```

### Run It
```bash
python ai_assistant.py
```

---

## What You Just Learned

| Concept | What It Means |
|---------|---------------|
| **LLM** | Large Language Model - AI that understands and generates text |
| **Qwen3.5 0.8B** | The small text-and-image model variant used in this guide |
| **Ollama** | Tool to run LLMs locally on your computer |
| **API** | Application Programming Interface - how code talks to AI |

---

## Next Steps

You're now ready for the full learning journey!

### Immediate Next Steps (Recommended Order)

1. **[TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)** (30 min)
    - Deeper dive into Ollama
    - More model features
    - Prompt engineering basics

2. **[TUTORIAL-002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)** (45 min)
    - Containerize your AI
    - Run multiple models
    - Production basics

3. **[LAB-001: Docker & LLM](../learning-resources/labs/LAB-001-Docker-LLM.md)** (2 hours)
    - Hands-on practice
    - Build an AI API server
    - Add chat interface

### After These Tutorials

4. **[TUTORIAL-003: RAG Basics](../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)** (1 hour)
    - Add your own knowledge
    - Build a smart assistant

5. **[LAB-002: RAG Implementation](../learning-resources/labs/LAB-002-RAG-Implementation.md)** (4 hours)
    - Deploy vector database
    - Create knowledge base
    - Build RAG pipeline

6. **[LAB-003: LoRA Fine-Tuning](../learning-resources/labs/LAB-003-LoRA-FineTuning.md)** (4 hours)
    - Customize models
    - Train on your data
    - Deploy custom models

---

## Common Issues

### Issue: "Command not found: ollama"

**Solution:**

- Make sure Ollama is installed
- Restart your terminal
- On Windows, use PowerShell or Command Prompt

### Issue: "Not enough memory"

**Solution:**

- Close other applications
- Try the smallest model in this guide: `ollama pull qwen3.5:0.8b`
- Add more RAM to your computer

### Issue: "Model download is slow"

**Solution:**

- Allow time for the model download; this guide's model is about 1.2 GB
- Try a different network
- Use a download manager if needed

### Issue: "Python import error"

**Solution:**
```bash
# Recommended: install into the project venv with uv
# (run from the directory that holds .venv)
uv pip install ollama

# Plain pip fallback
python -m pip install --upgrade pip
pip install ollama
```

---

## Tips for Success

1. **Start Small** - Don't try to build everything at once
2. **Experiment** - Try different prompts and models
3. **Read Error Messages** - They often tell you what's wrong
4. **Ask Questions** - Join communities (links below)
5. **Have Fun!** - Learning AI should be enjoyable

---

## Resources

### Official Documentation
- **Ollama:** [https://docs.ollama.com](https://docs.ollama.com)
- **Mistral AI:** [https://mistral.ai/news/](https://mistral.ai/news/)
- **Hugging Face:** [https://huggingface.co/docs](https://huggingface.co/docs)

### Communities
- **Ollama Discord:** [Join the Ollama community](https://discord.com/invite/ollama)
- **r/LocalLLaMA:** [https://www.reddit.com/r/LocalLLaMA/](https://www.reddit.com/r/LocalLLaMA/)
- **Hugging Face Forums:** [https://discuss.huggingface.co](https://discuss.huggingface.co)

### In Minder Academy
- **[Progress Tracker](PROGRESS-TRACKER.md)** - Track your learning
- **[Troubleshooting](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)** - Get help
- **[Cheat Sheets](MASTER-INDEX.md)** - Quick reference (see the Cheat Sheets section)

---

## You're On Your Way!

You just completed your first step into the world of local AI!

**What you can do now:**

- ✅ Run AI models on your computer
- ✅ Chat with Qwen3.5 0.8B
- ✅ Build basic AI scripts
- ✅ Understand the fundamentals

**What's next:**

- 📚 Complete the tutorials
- 🧪 Do the hands-on labs
- 🏆 Build the capstone project
- 🌟 Become an AI infrastructure expert

---

## Learning Path Overview

```text
Start Here (You are here)
    │
    ├─► Quick Start (30 min) ✅ DONE
    │
    ├─► TUTORIAL-001: Hello LLM (30 min)
    │
    ├─► TUTORIAL-002: Docker Essentials (45 min)
    │
    ├─► TUTORIAL-003: RAG Basics (60 min)
    │
    ├─► LAB-001: Docker & LLM (2 hours)
    │
    ├─► LAB-002: RAG Implementation (4 hours)
    │
    ├─► LAB-003: LoRA Fine-Tuning (4 hours)
    │
    ├─► LAB-004: ReAct Agent (4 hours)
    │
    └─► PROJECT-001: AI Assistant (20+ hours)
```

---

**🎉 Congratulations on starting your AI journey!**

## Your First Tutorial

- **[TUTORIAL-001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)**

**Questions?** Check [Troubleshooting](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)

