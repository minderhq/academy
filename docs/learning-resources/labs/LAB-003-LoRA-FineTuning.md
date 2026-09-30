---
Document ID: LAB-003
Title: "LAB-003: LoRA Fine-Tuning with QLoRA"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Tags: ['lab', 'lora', 'qlora', 'finetuning', 'hands-on']
---

# LAB-003: LoRA Fine-Tuning with QLoRA

**Prerequisites:**

## Required Knowledge
- **[TUTORIAL-001: Hello LLM](../tutorials/TUTORIAL-001-Hello-LLM.md)** - LLM basics
- **[TUTORIAL-002: Docker Essentials](../tutorials/TUTORIAL-002-Docker-Essentials.md)** - Docker fundamentals
- **[LAB-001: Docker & LLM](LAB-001-Docker-LLM.md)** - Docker practice
- **[TUTORIAL-000: Python for AI](../tutorials/TUTORIAL-000-Python-for-AI.md)** - REQUIRED for training code
- **Phase 2 (Recommended):** [2100-Calculus](../../phases/phase2-foundations/2100-calculus/) - PyTorch knowledge helpful

⚠️ **Strong Python Required:** This lab involves PyTorch, training loops, and model architecture. Complete **TUTORIAL-000** and review **Phase 2** content first.

### Required Hardware
- **GPU:** NVIDIA GPU with 11GB+ VRAM (11GB-class GPU, RTX 3060 12GB, or better)
- **RAM:** 32GB+ system RAM recommended
- **Storage:** 50GB+ free space for models and checkpoints
- **CPU:** 8+ cores recommended

> **⚠️ No GPU?** This lab requires GPU for QLoRA fine-tuning. Alternatives:
> - Use Google Colab Pro (GPU runtime)
> - Use cloud GPU services (RunPod, Lambda Labs, AWS)
> - Skip to [LAB-004: ReAct Agent](LAB-004-ReAct-Agent.md) which can run CPU-only

### Required Software Setup

#### 1. CUDA Installation (Linux)
```bash
# Check NVIDIA driver
nvidia-smi

# Install CUDA 12.1 (Ubuntu/Debian)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda-toolkit-12-1

# Verify CUDA
nvcc --version
```

#### 2. Hugging Face Authentication (Required)
```bash
# Install Hugging Face CLI
uv pip install -U "huggingface_hub[cli]"

# Login (you need a Hugging Face account with access to Mistral-7B)
# Visit https://huggingface.co/settings/tokens to create a token
huggingface-cli login

# Accept model license (required for Mistral-7B)
# Visit: https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.2
# Click "Agree and access repository" then login to accept
```

> **🔑 Important:** You must accept the Mistral 7B license terms on Hugging Face before the lab. The model is gated and requires authentication.

#### 3. Python Environment
```bash
# Verify Python version (3.13+ required)
python --version  # Should be 3.13

# Create the project environment with uv
# (uv fetches the Python 3.13 interpreter itself if it is missing)
uv venv --python 3.13

# Install PyTorch with CUDA support
# (cu130 wheels bundle the CUDA runtime - a recent driver is enough)
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Verify GPU access
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

**Time:** 4 hours
**Difficulty:** ⭐⭐⭐ Advanced

---

## Lab Objectives

After completing this lab, you will be able to:
- ✅ Understand LoRA (Low-Rank Adaptation) architecture
- ✅ Prepare datasets for fine-tuning
- ✅ Fine-tune models with QLoRA (4-bit quantization)
- ✅ Evaluate fine-tuned models
- ✅ Deploy custom models with vLLM
- ✅ Compare base vs fine-tuned models

---

## Setup Instructions

```bash
# Create lab directory
mkdir ~/lab-003-lora
cd ~/lab-003-lora

# Create directory structure
mkdir -p data/datasets
mkdir -p data/checkpoints
mkdir -p models
mkdir -p scripts
```

---

## Exercise 1: LoRA Theory and Setup (30 minutes)

### Understanding LoRA Architecture

**Key Concepts:**

1. **Pre-trained Model:** Frozen weights (W)
2. **LoRA Adapters:** Small trainable matrices (A, B)
3. **Forward Pass:** `output = Wx + BAx` where B×A << W

**Why LoRA Works:**
- Pre-trained models have low "intrinsic dimension"
- Adaptations can be learned in low-rank subspace
- Reduces trainable parameters from billions to thousands

```python
# ~/lab-003-lora/scripts/understand_lora.py
import math
import torch
import torch.nn as nn

class LinearWithLoRA(nn.Module):
    """Linear layer with LoRA adaptation"""

    def __init__(
        self,
        in_features: int,
        out_features: int,
        rank: int = 4,
        alpha: float = 1.0
    ):
        super().__init__()

        # Original weights (frozen)
        self.linear = nn.Linear(in_features, out_features, bias=False)
        self.linear.weight.requires_grad = False

        # LoRA parameters
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank

        # LoRA matrices (trainable)
        self.lora_A = nn.Parameter(torch.zeros(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))

        # Initialize A with Kaiming, B with zeros
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x):
        # Original: Wx
        result = self.linear(x)

        # LoRA: (BA)x scaled
        lora = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling

        return result + lora

# Compare parameter counts
def compare_params():
    """Compare base model vs LoRA"""

    in_features, out_features = 4096, 4096
    rank = 4

    # Base layer
    base_params = in_features * out_features

    # LoRA
    lora_params = (in_features * rank) + (rank * out_features)

    print(f"Base layer parameters: {base_params:,}")
    print(f"LoRA parameters: {lora_params:,}")
    print(f"Reduction: {base_params / lora_params:.1f}x")
    print(f"LoRA % of base: {lora_params / base_params * 100:.2f}%")

compare_params()
```

### ✅ Checkpoint: Exercise 1
**Verify:** Understand LoRA reduces parameters by ~1000x

---

## Exercise 2: Dataset Preparation (45 minutes)

### Task: Create and format training data

```python
# ~/lab-003-lora/scripts/prepare_dataset.py
import json

import random

class DatasetPreparer:
    """Prepare datasets for instruction fine-tuning"""

    def __init__(self, task_type: str = "instruction"):
        self.task_type = task_type

    def create_instruction_dataset(
        self,
        instructions: list[dict[str, str]],
        output_path: str
    ):
        """
        Create instruction tuning dataset

        Format:
        {
            "instruction": "...",
            "input": "...",  (optional)
            "output": "..."
        }
        """

        dataset = []
        for item in instructions:
            dataset.append({
                "instruction": item.get("instruction", ""),
                "input": item.get("input", ""),
                "output": item.get("output", "")
            })

        # Save as JSONL
        with open(output_path, 'w') as f:
            for example in dataset:
                f.write(json.dumps(example) + '\n')

        print(f"Saved {len(dataset)} examples to {output_path}")

    def create_chat_dataset(
        self,
        conversations: list[dict[str, str]],
        output_path: str
    ):
        """
        Create chat dataset

        Format:
        {
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
        """

        dataset = []
        for conv in conversations:
            dataset.append({
                "messages": conv.get("messages", [])
            })

        with open(output_path, 'w') as f:
            for example in dataset:
                f.write(json.dumps(example) + '\n')

        print(f"Saved {len(dataset)} conversations to {output_path}")

    def split_dataset(
        self,
        input_path: str,
        train_path: str,
        val_path: str,
        train_ratio: float = 0.9
    ):
        """Split dataset into train/validation"""

        # Load all examples
        examples = []
        with open(input_path, 'r') as f:
            for line in f:
                examples.append(json.loads(line))

        # Shuffle
        random.shuffle(examples)

        # Split
        split_idx = int(len(examples) * train_ratio)
        train_examples = examples[:split_idx]
        val_examples = examples[split_idx:]

        # Save
        with open(train_path, 'w') as f:
            for example in train_examples:
                f.write(json.dumps(example) + '\n')

        with open(val_path, 'w') as f:
            for example in val_examples:
                f.write(json.dumps(example) + '\n')

        print(f"Train: {len(train_examples)}, Val: {len(val_examples)}")

# Sample instruction data
instructions = [
    {
        "instruction": "Explain what Docker is",
        "input": "",
        "output": "Docker is a platform for developing, shipping, and running applications in containers. Containers are lightweight, standalone packages that include everything needed to run an application, including the code, runtime, system tools, libraries, and settings."
    },
    {
        "instruction": "What is the difference between Docker and a VM?",
        "input": "",
        "output": "Docker containers share the host OS kernel and are more lightweight, while VMs have their own OS kernel and require more resources. Containers start in seconds, while VMs take minutes. Containers are more portable and efficient than VMs."
    },
    {
        "instruction": "Explain Kubernetes in simple terms",
        "input": "",
        "output": "Kubernetes is like a traffic cop for containers. It manages where your containers run, makes sure they stay healthy, and automatically adds or removes containers based on how much traffic you have."
    },
    {
        "instruction": "Write a Docker command to run nginx",
        "input": "",
        "output": "docker run -d -p 80:80 --name my-nginx nginx"
    },
    {
        "instruction": "How do I list running Docker containers?",
        "input": "",
        "output": "docker ps"
    },
    {
        "instruction": "What is a Docker image?",
        "input": "",
        "output": "A Docker image is a read-only template that contains a set of instructions for creating a Docker container. It includes the application code, libraries, dependencies, and runtime needed to run the application."
    },
    {
        "instruction": "Explain Kubernetes pods",
        "input": "",
        "output": "A Pod is the smallest deployable unit in Kubernetes. It contains one or more containers that share storage and network resources. Pods are ephemeral and can be created, destroyed, and recreated as needed."
    },
    {
        "instruction": "What is a Kubernetes service?",
        "input": "",
        "output": "A Kubernetes Service is an abstraction that defines a logical set of Pods and a policy to access them. Services provide stable networking endpoints, load balancing, and service discovery for Pods."
    },
    {
        "instruction": "How do I scale a Kubernetes deployment?",
        "input": "",
        "output": "kubectl scale deployment my-app --replicas=5"
    },
    {
        "instruction": "What is a Dockerfile?",
        "input": "",
        "output": "A Dockerfile is a text document that contains all the commands to assemble a Docker image. It specifies the base image, application code, dependencies, and configuration needed to build the image."
    }
]

# Create dataset
preparer = DatasetPreparer()
preparer.create_instruction_dataset(
    instructions,
    "~/lab-003-lora/data/datasets/docker_k8s_train.jsonl"
)

# Split into train/val
preparer.split_dataset(
    "~/lab-003-lora/data/datasets/docker_k8s_train.jsonl",
    "~/lab-003-lora/data/datasets/train.jsonl",
    "~/lab-003-lora/data/datasets/val.jsonl",
    train_ratio=0.8
)
```

### ✅ Checkpoint: Exercise 2
**Verify:** Dataset created with train/val split

---

## Exercise 3: QLoRA Fine-Tuning Setup (30 minutes)

### Task: Install dependencies and configure training

```bash
# Install PyTorch with CUDA support
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# Install fine-tuning libraries
uv pip install -q -U bitsandbytes  # Note: Correct spelling (not "bitsandpeed")
uv pip install -q -U transformers
uv pip install -q -U peft
uv pip install -q -U accelerate
uv pip install -q -U datasets
uv pip install -q -U trl
uv pip install -q -U wandb
```

### Create training script:

```python
# ~/lab-003-lora/scripts/train_lora.py
import os
import torch
from datasets import load_dataset
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from trl import SFTTrainer
import json

# Configuration
MODEL_NAME = "mistralai/Mistral-7B-Instruct-v0.2"
DATA_PATH = "~/lab-003-lora/data/datasets/train.jsonl"
OUTPUT_DIR = "~/lab-003-lora/data/checkpoints/mistral-7b-docker-k8s-lora"

# LoRA hyperparameters
LORA_R = 16          # Rank
LORA_ALPHA = 32      # Alpha scaling
LORA_DROPOUT = 0.05  # Dropout
TARGET_MODULES = [   # Which modules to apply LoRA
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj"
]

# Training hyperparameters
MAX_SEQ_LENGTH = 512
BATCH_SIZE = 4
GRADIENT_ACCUMULATION_STEPS = 4
NUM_EPOCHS = 3
LEARNING_RATE = 2e-4
WARMUP_STEPS = 50

def load_model_and_tokenizer():
    """Load model with 4-bit quantization"""

    # Quantization config for QLoRA
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True
    )

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True
    )

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, trust_remote_code=True)

    # Fix for models without pad token
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        tokenizer.pad_token_id = tokenizer.eos_token_id

    return model, tokenizer

def prepare_model_for_lora(model):
    """Prepare model for LoRA training"""

    # Prepare for k-bit training
    model = prepare_model_for_kbit_training(model)

    # LoRA config
    lora_config = LoraConfig(
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM"
    )

    # Apply LoRA
    model = get_peft_model(model, lora_config)

    # Print trainable parameters
    model.print_trainable_parameters()

    return model

def load_dataset(file_path):
    """Load custom dataset"""

    data = []
    with open(file_path, 'r') as f:
        for line in f:
            data.append(json.loads(line))

    # Format for training
    formatted_data = []
    for item in data:
        instruction = item.get('instruction', '')
        input_text = item.get('input', '')
        output = item.get('output', '')

        # Create prompt
        if input_text:
            prompt = f"""### Instruction:
{instruction}

### Input:
{input_text}

### Response:
{output}"""
        else:
            prompt = f"""### Instruction:
{instruction}

### Response:
{output}"""

        formatted_data.append({"text": prompt})

    return formatted_data

def train():
    """Main training function"""

    print("Loading model and tokenizer...")
    model, tokenizer = load_model_and_tokenizer()

    print("Preparing model for LoRA...")
    model = prepare_model_for_lora(model)

    print("Loading dataset...")
    dataset = load_dataset(DATA_PATH)

    print(f"Dataset size: {len(dataset)}")

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        learning_rate=LEARNING_RATE,
        warmup_steps=WARMUP_STEPS,
        logging_steps=10,
        save_steps=100,
        eval_steps=100,
        save_total_limit=2,
        fp16=True,
        optim="paged_adamw_32bit",
        weight_decay=0.001,
        lr_scheduler_type="cosine",
        report_to="none",  # Set to "wandb" if using Weights & Biases
        save_strategy="steps",
        evaluation_strategy="steps",
        load_best_model_at_end=True,
    )

    # Create trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=MAX_SEQ_LENGTH,
        packing=False,
    )

    print("Starting training...")
    trainer.train()

    print("Saving model...")
    trainer.save_model()
    tokenizer.save_pretrained(OUTPUT_DIR)

    print(f"Model saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    train()
```

### Create the project manifest (pyproject.toml + uv.lock):

```bash
cd ~/lab-003-lora

# uv-native dependency management: pyproject.toml holds the constraints,
# uv.lock pins the exact resolved versions. uv init --bare creates only
# the manifest; uv add records each constraint, writes the lockfile and
# installs into the project venv in one step (replaces uv pip install -r).
# Constraints with >= are quoted so the shell never sees a redirection.
uv init --bare --python 3.13 .
uv add "torch>=2.12.0" "transformers>=5.10.2" "peft>=0.19.1" "bitsandbytes>=0.50.2" "accelerate>=1.13.0" "datasets>=5.0.0" "trl>=1.14.0" "scipy>=1.17.1" "sentencepiece>=0.2.1" "protobuf>=7.35.0" "wandb>=0.30.0"
```

### ✅ Checkpoint: Exercise 3
**Verify:** All dependencies installed, script ready

---

## Exercise 4: Run Fine-Tuning (60 minutes)

### Task: Fine-tune Mistral 7B on Docker/K8s dataset

```bash
# Start training
cd ~/lab-003-lora
python scripts/train_lora.py
```

### Monitor training:

```bash
# In another terminal, monitor GPU usage
watch -n 1 nvidia-smi
```

### Expected output:

```text
Loading model and tokenizer...
Preparing model for LoRA...
trainable params: 6,553,600 || all params: 7,242,739,712 || trainable%: 0.0905
Loading dataset...
Dataset size: 8
Starting training...
{'loss': 2.1234, 'grad_norm': 1.234, 'learning_rate': 0.00019, 'epoch': 0.12}
{'loss': 1.8765, 'grad_norm': 0.987, 'learning_rate': 0.00018, 'epoch': 0.25}
...
```

### Training tips:

1. **VRAM Management:**
   - Use `MAX_SEQ_LENGTH=512` for 11GB VRAM
   - Reduce `BATCH_SIZE` if OOM
   - Increase `GRADIENT_ACCUMULATION_STEPS` to maintain effective batch size

2. **Speed:**
   - QLoRA on an 11GB-class GPU: ~1-2 samples/sec
   - 10 samples × 3 epochs ≈ 15-30 seconds
   - Real datasets (1000+ samples): several hours

3. **Monitoring:**
   - Loss should decrease steadily
   - Watch for gradient explosions (grad_norm > 10)
   - Check for overfitting on small datasets

### ✅ Checkpoint: Exercise 4
**Verify:** Training completes, model checkpoint saved

---

## Exercise 5: Evaluate Fine-Tuned Model (30 minutes)

### Task: Compare base vs fine-tuned model

```python
# ~/lab-003-lora/scripts/evaluate_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def load_base_model():
    """Load base Mistral model"""

    model_name = "mistralai/Mistral-7B-Instruct-v0.2"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    return model, tokenizer

def load_finetuned_model(base_model_path, lora_path):
    """Load fine-tuned model with LoRA adapters"""

    # Load base model
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    # Load LoRA adapters
    model = PeftModel.from_pretrained(model, lora_path)

    return model, tokenizer

def generate_response(model, tokenizer, prompt, max_tokens=256):
    """Generate response from model"""

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    outputs = model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        temperature=0.7,
        do_sample=True,
        top_p=0.9,
        pad_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(outputs[0], skip_special_tokens=True)

    # Extract only the generated part
    if prompt in response:
        response = response.replace(prompt, "").strip()

    return response

def compare_models():
    """Compare base vs fine-tuned model"""

    test_questions = [
        "What is Docker?",
        "How do I run a Docker container?",
        "Explain Kubernetes pods",
        "Write a Docker command to list containers",
        "What is the difference between Docker and VMs?"
    ]

    print("="*60)
    print("Loading models...")
    print("="*60)

    # Load models
    base_model, base_tokenizer = load_base_model()
    ft_model, ft_tokenizer = load_finetuned_model(
        "mistralai/Mistral-7B-Instruct-v0.2",
        "~/lab-003-lora/data/checkpoints/mistral-7b-docker-k8s-lora"
    )

    # Compare
    for question in test_questions:
        print(f"\n{'='*60}")
        print(f"Question: {question}")
        print(f"{'='*60}\n")

        prompt = f"[INST] {question} [/INST]"

        # Base model
        print("Base Model:")
        base_response = generate_response(base_model, base_tokenizer, prompt)
        print(base_response[:200] + "..." if len(base_response) > 200 else base_response)

        print("\n" + "-"*60 + "\n")

        # Fine-tuned model
        print("Fine-tuned Model:")
        ft_response = generate_response(ft_model, ft_tokenizer, prompt)
        print(ft_response[:200] + "..." if len(ft_response) > 200 else ft_response)

        print("\n")

if __name__ == "__main__":
    compare_models()
```

### Run evaluation:

```bash
python ~/lab-003-lora/scripts/evaluate_model.py
```

### ✅ Checkpoint: Exercise 5
**Verify:** Fine-tuned model shows domain-specific improvements

---

## Exercise 6: Merge and Export (30 minutes)

### Task: Merge LoRA weights into base model

```python
# ~/lab-003-lora/scripts/merge_model.py
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

def merge_and_export(
    base_model_path: str,
    lora_path: str,
    output_path: str
):
    """Merge LoRA weights into base model and export"""

    print("Loading base model...")
    tokenizer = AutoTokenizer.from_pretrained(base_model_path)
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print("Loading LoRA adapters...")
    model = PeftModel.from_pretrained(base_model, lora_path)

    print("Merging weights...")
    merged_model = model.merge_and_unload()

    print("Saving merged model...")
    merged_model.save_pretrained(output_path, safe_serialization=True)
    tokenizer.save_pretrained(output_path)

    print(f"Merged model saved to {output_path}")

if __name__ == "__main__":
    merge_and_export(
        base_model_path="mistralai/Mistral-7B-Instruct-v0.2",
        lora_path="~/lab-003-lora/data/checkpoints/mistral-7b-docker-k8s-lora",
        output_path="~/lab-003-lora/models/mistral-7b-docker-k8s-merged"
    )
```

### Convert to GGUF for CPU inference:

```bash
# Install llama.cpp
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make

# Convert to GGUF
./convert-hf-to-gguf.py ~/lab-003-lora/models/mistral-7b-docker-k8s-merged \
  --outfile ~/lab-003-lora/models/mistral-7b-docker-k8s.gguf \
  --outtype q4_k_m

# Quantize to 4-bit
./quantize ~/lab-003-lora/models/mistral-7b-docker-k8s.gguf \
  ~/lab-003-lora/models/mistral-7b-docker-k8s-Q4_K_M.gguf \
  Q4_K_M
```

### ✅ Checkpoint: Exercise 6
**Verify:** Merged model and GGUF files created

---

## Exercise 7: Deploy with vLLM (15 minutes)

### Task: Deploy fine-tuned model with vLLM

```bash
# Create docker-compose.yml
cat > ~/lab-003-lora/docker-compose.yml << 'EOF'

services:
  vllm-ft:
    image: vllm/vllm-openai:v0.6.6.post1  # ⚠️ PIN SPECIFIC VERSION in production!
    container_name: vllm-finetuned
    ports:
      - "8002:8000"
    volumes:
      - ./models:/models
    command: >
      --model /models/mistral-7b-docker-k8s-merged
      --gpu-memory-utilization 0.9
      --max-model-len 2048
      --port 8000
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
EOF

# Deploy
cd ~/lab-003-lora
docker-compose up -d

# Test
curl http://localhost:8002/v1/models
```

### Test the API:

```bash
# Generate with fine-tuned model
curl http://localhost:8002/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/mistral-7b-docker-k8s-merged",
    "prompt": "What is Docker?\n\n",
    "max_tokens": 256
  }'
```

### ✅ Checkpoint: Exercise 7
**Verify:** Fine-tuned model serving via vLLM

---

## Final Challenge: Build Custom Chatbot (30 minutes)

### Task: Create chatbot with your fine-tuned model

```python
# ~/lab-003-lora/chatbot.py
import requests

class FineTunedChatbot:
    """Chatbot using fine-tuned model"""

    def __init__(self, api_url: str = "http://localhost:8002"):
        self.api_url = api_url
        self.conversation_history = []

    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.conversation_history.append({
            "role": role,
            "content": content
        })

    def format_prompt(self, user_message: str) -> str:
        """Format prompt for model"""

        prompt = ""

        # Add conversation history
        for msg in self.conversation_history:
            if msg["role"] == "user":
                prompt += f"[INST] {msg['content']} [/INST] "
            else:
                prompt += f"{msg['content']} </s>"

        # Add current message
        prompt += f"[INST] {user_message} [/INST]"

        return prompt

    def chat(self, user_message: str) -> str:
        """Chat with the model"""

        # Format prompt
        prompt = self.format_prompt(user_message)

        # Call API
        response = requests.post(
            f"{self.api_url}/v1/completions",
            json={
                "model": "/models/mistral-7b-docker-k8s-merged",
                "prompt": prompt,
                "max_tokens": 512,
                "temperature": 0.7,
                "top_p": 0.9
            },
            timeout=120
        )

        result = response.json()
        assistant_message = result["choices"][0]["text"].strip()

        # Update history
        self.add_message("user", user_message)
        self.add_message("assistant", assistant_message)

        return assistant_message

    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

def main():
    """Interactive chat loop"""

    bot = FineTunedChatbot()

    print("🤖 Fine-Tuned Docker/K8s Chatbot")
    print("="*60)
    print("Ask me anything about Docker or Kubernetes!")
    print("(type 'quit' to exit, 'clear' to clear history)")
    print("="*60)

    while True:
        user_input = input("\nYou: ").strip()

        if user_input.lower() == 'quit':
            print("Goodbye!")
            break

        if user_input.lower() == 'clear':
            bot.clear_history()
            print("History cleared!")
            continue

        if not user_input:
            continue

        response = bot.chat(user_input)
        print(f"\nAI: {response}")

if __name__ == "__main__":
    main()
```

### Run your chatbot:

```bash
python ~/lab-003-lora/chatbot.py
```

### Test questions:
- "What is Docker?"
- "How do I run nginx in Docker?"
- "Explain Kubernetes services"
- "Write a command to scale a deployment"
- "What's the difference between pods and deployments?"

### ✅ Final Checkpoint
**Test:** Your fine-tuned chatbot answers domain questions accurately

---

## 🎓 Lab Completion Checklist

```text
[ ] Exercise 1: LoRA Theory and Setup
[ ] Exercise 2: Dataset Preparation
[ ] Exercise 3: QLoRA Fine-Tuning Setup
[ ] Exercise 4: Run Fine-Tuning
[ ] Exercise 5: Evaluate Fine-Tuned Model
[ ] Exercise 6: Merge and Export
[ ] Exercise 7: Deploy with vLLM
[ ] Final Challenge: Build Custom Chatbot
```

---

## 📚 Post-Lab Reading

- **[5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)** - Deep dive into LoRA
- **[5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)** - 4-bit fine-tuning
- **[5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)** - Preference optimization

---

## 🏆 Lab Badge

**Earned:** LoRA Fine-Tuning Badge 🏅

Next: **[LAB-004: ReAct Agent](LAB-004-ReAct-Agent.md)**
