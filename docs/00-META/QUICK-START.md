# QUICK START GUIDE: Get Started in 30 Minutes

**Fastest path to running your first local LLM**

---

## ⚡ What You'll Achieve

In the next 30 minutes, you will:
1. ✅ Install Ollama (easiest LLM runner)
2. ✅ Run your first local AI model
3. ✅ Chat with Mistral 7B
4. ✅ Understand the basics
5. ✅ Know where to go next

---

## 🎯 Prerequisites

### Hardware Requirements
- Computer (Windows, Mac, or Linux)
- 8GB+ RAM (16GB+ recommended)
- 10GB+ free disk space
- Stable internet connection (for model download)

### Software Requirements
- Basic command line knowledge
- Administrator/sudo access (for installation)

### ⚠️ Before You Start

**If you're new to command line:**
- Windows: Use PowerShell or Terminal
- Mac: Use Terminal (Applications → Utilities)
- Linux: Use your default terminal

**If you have limited resources:**
- 8GB RAM: Use `mistral:7b` or `phi3`
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

## 📥 Step 1: Install Ollama (5 minutes)

### Windows
1. Download: https://ollama.com/download
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

### ✅ Verify Installation
```bash
ollama --version
```

Expected output: `ollama version is 0.1.x` or similar

---

## 🤖 Step 2: Download a Model (10 minutes)

Ollama makes it incredibly easy:

```bash
# Pull Mistral 7B (recommended for beginners)
ollama pull mistral

# This downloads ~4GB - may take a few minutes
```

### What's Happening?
- Mistral 7B is a powerful open-source LLM
- 4 billion parameters (small but capable)
- Requires ~8GB RAM to run
- Perfect for learning and experimentation

### Other Options (for later)
```bash
ollama pull llama2          # Meta's Llama 2
ollama pull codellama       # Coding assistant
ollama pull phi3            # Small & fast
```

### ⚠️ Troubleshooting Model Download

**Download stuck or very slow?**
```bash
# Check your internet connection
ping google.com

# Try again (Ollama resumes automatically)
ollama pull mistral
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
ollama pull phi3            # Only ~2GB
ollama pull mistral:7b      # Explicit 7B version
```

**Verify model downloaded successfully:**
```bash
ollama list
# Should show: mistral    latest    <size>
```

---

## 💬 Step 3: Chat with Your AI (10 minutes)

### Simple Chat
```bash
ollama run mistral
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

## 🐍 Step 4: Use with Python (5 minutes)

### Install the Ollama Python library
```bash
pip install ollama
```

### Create Your First AI Script

```python
# my_first_ai.py
import ollama

# Simple chat
response = ollama.chat(model='mistral', messages=[
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

### 🎉 Congratulations!
You just built your first AI application!

---

## 🚀 Step 5: Build Something Cool (Optional)

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
            model='mistral',
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

## 📚 What You Just Learned

| Concept | What It Means |
|---------|---------------|
| **LLM** | Large Language Model - AI that understands and generates text |
| **Mistral 7B** | A specific model with 7 billion parameters |
| **Ollama** | Tool to run LLMs locally on your computer |
| **API** | Application Programming Interface - how code talks to AI |

---

## 🎯 Next Steps

You're now ready for the full learning journey!

### Immediate Next Steps (Recommended Order)

1. **[Tutorial 001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)** (30 min)
   - Deeper dive into Ollama
   - More model features
   - Prompt engineering basics

2. **[Tutorial 002: Docker Essentials](../learning-resources/tutorials/TUTORIAL-002-Docker-Essentials.md)** (45 min)
   - Containerize your AI
   - Run multiple models
   - Production basics

3. **[LAB 001: Docker & LLM](../learning-resources/labs/LAB-001-Docker-LLM.md)** (2 hours)
   - Hands-on practice
   - Build an AI API server
   - Add chat interface

### After These Tutorials

4. **[Tutorial 003: RAG Basics](../learning-resources/tutorials/TUTORIAL-003-RAG-Basics.md)** (1 hour)
   - Add your own knowledge
   - Build a smart assistant

5. **[LAB 002: RAG Implementation](../learning-resources/labs/LAB-002-RAG-Implementation.md)** (3 hours)
   - Deploy vector database
   - Create knowledge base
   - Build RAG pipeline

6. **[LAB 003: LoRA Fine-Tuning](../learning-resources/labs/LAB-003-LoRA-FineTuning.md)** (4 hours)
   - Customize models
   - Train on your data
   - Deploy custom models

---

## 🛠️ Common Issues

### Issue: "Command not found: ollama"

**Solution:**
- Make sure Ollama is installed
- Restart your terminal
- On Windows, use PowerShell or Command Prompt

### Issue: "Not enough memory"

**Solution:**
- Close other applications
- Try a smaller model: `ollama pull phi3`
- Add more RAM to your computer

### Issue: "Model download is slow"

**Solution:**
- Be patient, models are large (4GB+)
- Try a different network
- Use a download manager if needed

### Issue: "Python import error"

**Solution:**
```bash
# Make sure pip is installed
python -m pip install --upgrade pip

# Install ollama package
pip install ollama

# If using Python 3 specifically
python3 -m pip install ollama
```

---

## 💡 Tips for Success

1. **Start Small** - Don't try to build everything at once
2. **Experiment** - Try different prompts and models
3. **Read Error Messages** - They often tell you what's wrong
4. **Ask Questions** - Join communities (links below)
5. **Have Fun!** - Learning AI should be enjoyable

---

## 🌐 Resources

### Official Documentation
- **Ollama:** https://ollama.com/docs
- **Mistral AI:** https://mistral.ai/news/
- **Hugging Face:** https://huggingface.co/docs

### Communities
- **Ollama Discord:** https://discord.gg/ollama
- **r/LocalLLaMA:** https://reddit.com/r/LocalLLaMA
- **Hugging Face Forums:** https://discuss.huggingface.co

### In AI Engineering Curriculum
- **[Progress Tracker](PROGRESS-TRACKER.md)** - Track your learning
- **[Troubleshooting](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)** - Get help
- **[Cheat Sheets](../learning-resources/cheat-sheets/)** - Quick reference

---

## 🎓 You're On Your Way!

You just completed your first step into the world of local AI!

**What you can do now:**
- ✅ Run AI models on your computer
- ✅ Chat with Mistral 7B
- ✅ Build basic AI scripts
- ✅ Understand the fundamentals

**What's next:**
- 📚 Complete the tutorials
- 🧪 Do the hands-on labs
- 🏆 Build the capstone project
- 🌟 Become an AI infrastructure expert

---

## 📊 Learning Path Overview

```text
Start Here (You are here)
    │
    ├─► Quick Start (30 min) ✅ DONE
    │
    ├─► Tutorial 001: Hello LLM (30 min)
    │
    ├─► Tutorial 002: Docker Essentials (45 min)
    │
    ├─► Tutorial 003: RAG Basics (60 min)
    │
    ├─► LAB 001: Docker & LLM (2 hours)
    │
    ├─► LAB 002: RAG Implementation (3 hours)
    │
    ├─► LAB 003: LoRA Fine-Tuning (4 hours)
    │
    ├─► LAB 004: ReAct Agent (4 hours)
    │
    └─► PROJECT 001: AI Assistant (20+ hours)
```

---

**🎉 Congratulations on starting your AI journey!**

**Next:** [Tutorial 001: Hello LLM](../learning-resources/tutorials/TUTORIAL-001-Hello-LLM.md)

**Questions?** Check [Troubleshooting](../learning-resources/troubleshooting/TROUBLESHOOTING-Common-Issues.md)

---

*Last Updated: 2026-02-04*
