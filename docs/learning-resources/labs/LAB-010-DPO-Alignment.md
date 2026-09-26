---
Document ID: LAB-010
Title: "LAB-010: DPO Alignment"
Last Updated: 2026-09-27
Status: Complete
Difficulty: Advanced
Estimated Time: 5-6 hours
Tags: ['dpo', 'alignment', 'rlhf', 'preference-learning', 'hands-on']
---

# LAB 010: DPO Alignment

**Align language models with human preferences using Direct Preference Optimization**

**Prerequisites:**
- [LAB 003: LoRA Fine-Tuning](LAB-003-LoRA-FineTuning.md) - adapter-based efficient fine-tuning
- [5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md) - the math behind the loss
- [5202: Alignment Orchestration](../../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md)
- [VOLUME-3: LLM Internals](../../volumes/VOLUME-3-LLM-Internals.md) - log-probabilities and KL divergence
- [VOLUME-5: Model Adaptation](../../volumes/VOLUME-5-Model-Adaptation.md)

---

## Table of Contents

- [Lab Overview](#lab-overview)
- [Part 1: Setup (30 minutes)](#part-1-setup-30-minutes)
- [Part 2: Preference Data (90 minutes)](#part-2-preference-data-90-minutes)
- [Part 3: DPO Training (120 minutes)](#part-3-dpo-training-120-minutes)
- [Part 4: Evaluate Alignment (60 minutes)](#part-4-evaluate-alignment-60-minutes)
- [Part 5: Analyze Results (30 minutes)](#part-5-analyze-results-30-minutes)
- [Completion Checklist](#completion-checklist)
- [Key Learnings](#key-learnings)
- [You're Now Ready For](#youre-now-ready-for)

---

## Lab Overview

### What is DPO?

**DPO (Direct Preference Optimization)** is a method for aligning language models with human preferences without training a separate reward model. It's simpler and more stable than traditional RLHF (PPO).

**Key advantages:**
- No reward model needed
- More stable training
- Simpler implementation
- Better sample efficiency

### DPO vs RLHF

```text
Traditional RLHF:
Data -> Train Reward Model -> PPO with Reward Model -> Aligned Model
(Complex, unstable, many hyperparameters)

DPO:
Data -> Direct Preference Optimization -> Aligned Model
(Simple, stable, fewer hyperparameters)
```

### What You Will Do

After completing this lab, you will be able to:
- Understand what the DPO objective optimizes and why it replaces the reward-model + RL pipeline
- Create and validate preference datasets from model outputs
- Compute the DPO loss, its implicit rewards, and reward accuracy from raw log-probabilities
- Train a model with DPO alignment using TRL and LoRA on a single GPU
- Read beta as the KL anchor and measure its effect on policy drift

---

## Part 1: Setup (30 minutes)

### Step 1.1: Install Dependencies

```bash
# Create virtual environment
python -m venv dpo-env
source dpo-env/bin/activate  # On Windows: dpo-env\Scripts\activate

# Core training stack
pip install torch transformers trl peft datasets

# Experiment tracking is optional - every step in this lab runs without it
pip install wandb
```

### Step 1.2: Verify and Get a Base Model

```bash
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
python -c "import trl; print(f'TRL: {trl.__version__}')"

# hf is the current Hugging Face CLI (huggingface-cli is the legacy name)
pip install huggingface_hub
hf auth login  # only needed for gated models

# We'll use a smaller model for this lab. Good options:
#   microsoft/Phi-3-mini-4k-instruct (~8 GB in fp16)
#   meta-llama/Llama-3.2-3B-Instruct (gated)
#   mistralai/Mistral-7B-Instruct-v0.3 (~15 GB in fp16)
#
# Training downloads the model automatically. To pre-download:
# hf download microsoft/Phi-3-mini-4k-instruct --local-dir ./models/phi-3
```

---

## Part 2: Preference Data (90 minutes)

### Understanding Preference Data

DPO requires paired examples for the same prompt:
- **Chosen:** Better response
- **Rejected:** Worse response

```text
Example:
Prompt: "What's the capital of France?"
Chosen: "The capital of France is Paris, known for the Eiffel Tower."
Rejected: "Paris."
```

### Step 2.1: Generate Candidate Responses

```text
# sketch - generate_candidates.py (needs a 3-8B instruct model + GPU-hours)
"""
Generate multiple candidate responses for a DPO dataset.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import json

model_name = "microsoft/Phi-3-mini-4k-instruct"  # or your preferred model

tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Sample prompts - replace with your domain data
prompts = [
    "Explain quantum computing in simple terms.",
    "What are the benefits of regular exercise?",
    "How does photosynthesis work?",
    "Write a short poem about nature.",
    "Explain the difference between Python and JavaScript.",
]

def generate_response(prompt, temperature=0.8, max_new_tokens=256):
    """Generate a response from the model via its chat template."""
    messages = [{"role": "user", "content": prompt}]
    inputs = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)

candidates = []
for prompt in prompts:
    print(f"Generating responses for: {prompt[:50]}...")

    # Three responses at three temperatures give ranking diversity
    responses = []
    for i in range(3):
        response = generate_response(prompt, temperature=0.7 + i * 0.1)
        responses.append(response)
        print(f"  Response {i+1}: {response[:100]}...")

    candidates.append({"prompt": prompt, "responses": responses})

with open("candidates.json", "w") as f:
    json.dump(candidates, f, indent=2)

# len(responses), not len(prompts) - each group holds 3 responses
print(f"\nGenerated {len(candidates)} prompt groups with {len(responses)} responses each")
```

Two details matter for pair quality: an instruct model generates far better candidates when fed through its **chat template** (raw-prompt completion drifts off-format), and varying the temperature between candidates gives the ranker real diversity to choose from.

### Step 2.2: Rank and Create Pairs

```text
# sketch - create_pairs.py (interactive; AI ranking needs an OpenAI API key)
"""
Rank responses and create preference pairs.
"""

import json

def manual_ranking(candidates):
    """
    Manually rank responses to create high-quality pairs
    (recommended for learning).
    """
    pairs = []

    for item in candidates:
        prompt = item["prompt"]
        responses = item["responses"]

        print(f"\n{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"{'='*60}")

        for i, resp in enumerate(responses):
            print(f"\n[{i+1}] {resp}")

        print("\nRank the responses (best to worst, e.g., '2 1 3'):")
        ranking = input("> ").strip()

        try:
            ranked_indices = [int(x) - 1 for x in ranking.split()]
            if len(ranked_indices) < 2:
                print("Need at least 2 rankings, skipping...")
                continue

            best_idx = ranked_indices[0]
            for worse_idx in ranked_indices[1:]:
                pairs.append({
                    "prompt": prompt,
                    "chosen": responses[best_idx],
                    "rejected": responses[worse_idx],
                })

        except (ValueError, IndexError):
            print("Invalid ranking, skipping...")
            continue

    return pairs

def ai_ranking(candidates, judge_model_name="gpt-4o"):
    """
    Use an AI model to rank responses.
    Uses the openai >= 1.0 client API (ChatCompletion.create was removed).
    """
    from openai import OpenAI

    client = OpenAI()  # reads OPENAI_API_KEY from the environment
    pairs = []

    for item in candidates:
        prompt = item["prompt"]
        responses = item["responses"]

        rank_prompt = f"""
        Rank the following responses to this prompt from best to worst.
        Consider: accuracy, clarity, completeness, and helpfulness.

        Prompt: {prompt}

        Responses:
        {chr(10).join([f'{i+1}. {resp}' for i, resp in enumerate(responses)])}

        Respond only with the ranking numbers (e.g., '2 1 3'):
        """

        response = client.chat.completions.create(
            model=judge_model_name,
            messages=[{"role": "user", "content": rank_prompt}],
            max_tokens=50,
        )
        ranking_str = response.choices[0].message.content.strip()

        try:
            ranked_indices = [int(x) - 1 for x in ranking_str.split()]
            if len(ranked_indices) >= 2:
                best_idx = ranked_indices[0]
                for worse_idx in ranked_indices[1:]:
                    pairs.append({
                        "prompt": prompt,
                        "chosen": responses[best_idx],
                        "rejected": responses[worse_idx],
                    })
        except (ValueError, IndexError):
            continue

    return pairs

with open("candidates.json", "r") as f:
    candidates = json.load(f)

print("Creating preference pairs...")
print("Choose method:")
print("1. Manual ranking (recommended for learning)")
print("2. AI-assisted ranking")

choice = input("> ").strip()
pairs = manual_ranking(candidates) if choice == "1" else ai_ranking(candidates)

with open("preference_pairs.json", "w") as f:
    json.dump(pairs, f, indent=2)

print(f"\nCreated {len(pairs)} preference pairs")
print(f"Saved to preference_pairs.json")
```

### Step 2.3: Load a Standard Preference Dataset (Optional)

```text
# sketch - load_standard_dataset.py (needs HF account / dataset terms accepted)
"""
Load a standard preference dataset.
"""

from datasets import load_dataset

# Option 1: HH-RLHF (Anthropic's Helpful-Harmless dataset)
# GATED: you must accept the dataset terms on the Hugging Face page first.
hh_dataset = load_dataset("Anthropic/hh-rlhf", "harmless-base")
print(hh_dataset)

# Option 2: OpenAssistant (oasst1)
# Also GATED - and it stores full conversation TREES, not ready-made
# chosen/rejected pairs; you traverse the message tree to extract pairs.
oa_dataset = load_dataset("OpenAssistant/oasst1")
print(oa_dataset)

# Option 3: Stanford Human Preferences (SHP)
# Public (no approval). Pairs come from Reddit score deltas.
shp_dataset = load_dataset("stanfordnlp/SHP")
print(shp_dataset)
```

Building preference pairs properly (including from oasst1's conversation trees) is a full topic of its own - see [5204: Preference Dataset Creation](../../phases/phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md).

For this lab we use a tiny hand-written set so every step runs end to end. Before any DPO run, validate the pairs - bad pairs (identical chosen/rejected, empty fields, duplicates) actively hurt alignment. This checker runs standalone:

```python
SAMPLE_PAIRS = [
    {
        "prompt": "What is the capital of France?",
        "chosen": "The capital of France is Paris. It's known for landmarks like the Eiffel Tower and the Louvre Museum.",
        "rejected": "Paris.",
    },
    {
        "prompt": "Explain gravity.",
        "chosen": "Gravity is a fundamental force that attracts objects with mass toward each other. On Earth, it gives weight to physical objects.",
        "rejected": "Gravity makes things fall down.",
    },
    {
        "prompt": "How do I bake a cake?",
        "chosen": "To bake a cake: 1) Preheat oven to 350F, 2) Mix flour, sugar, baking powder, 3) Add eggs, milk, butter, 4) Pour into pan, 5) Bake 30-35 minutes.",
        "rejected": "Just put ingredients in oven.",
    },
    {   # deliberately broken, to show the validator catching it
        "prompt": "How do I bake a cake?",
        "chosen": "Just put ingredients in oven.",
        "rejected": "Just put ingredients in oven.",
    },
]

FIELDS = {"prompt", "chosen", "rejected"}

def validate(pairs):
    problems = []
    seen = set()
    for i, pair in enumerate(pairs):
        if set(pair) != FIELDS:
            problems.append((i, "wrong schema"))
            continue
        if not all(isinstance(v, str) and v.strip() for v in pair.values()):
            problems.append((i, "empty field"))
            continue
        if pair["chosen"] == pair["rejected"]:
            problems.append((i, "chosen == rejected"))
            continue
        if len(pair["chosen"]) <= len(pair["rejected"]):
            problems.append((i, "chosen not longer than rejected"))
        key = (pair["prompt"], pair["chosen"])
        if key in seen:
            problems.append((i, "duplicate of an earlier pair"))
        seen.add(key)
    return problems

problems = validate(SAMPLE_PAIRS)
bad = {i for i, _ in problems}
for i in range(len(SAMPLE_PAIRS)):
    if i in bad:
        continue
    print("pair %d: ok" % i)
for i, why in problems:
    print("pair %d: %s" % (i, why))
kept = len(SAMPLE_PAIRS) - len(bad)
print("kept %d of %d pairs" % (kept, len(SAMPLE_PAIRS)))
```

**Output:**

```text
pair 0: ok
pair 1: ok
pair 2: ok
pair 3: chosen == rejected
kept 3 of 4 pairs
```

---

## Part 3: DPO Training (120 minutes)

### The DPO Loss, Mechanically

DPO rewrites preference learning as a classification problem on **log-probability margins**. For each pair, define the implicit reward of a response as its log-probability under the policy relative to a frozen reference model (the SFT starting checkpoint):

```text
r(x, y)  =  beta * [ log pi(y|x) - log pi_ref(y|x) ]

L_DPO    =  -log sigmoid( r(chosen) - r(rejected) )
```

Minimizing the loss pushes the policy to raise chosen responses and lower rejected responses **relative to the reference** - the beta term anchors how far the policy may drift. You don't need a trained reward model because the loss *is* the reward model's Bradley-Terry objective, with the implicit reward substituted in.

This block implements exactly that objective on a tiny scorer and trains on one pair - runnable on CPU in under a second:

```python
import torch
import torch.nn.functional as F

torch.manual_seed(42)

VOCAB = 8
chosen_ids = torch.tensor([[1, 3, 5, 2, 4, 6]])
rejected_ids = torch.tensor([[1, 3, 4, 2, 6, 5]])

# The policy's next-token logits; a frozen copy serves as the reference.
W = (torch.randn(VOCAB, VOCAB) * 0.5).requires_grad_(True)
W_ref = W.detach().clone()
BETA = 0.1
LR = 5.0

def seq_logprob(W, ids):
    # Context-free scorer (token t's row scores the next token) keeps the
    # demo tiny; real DPO computes these log-probs with the full LM.
    logits = W[ids[:, :-1]]                       # [B, L-1, VOCAB]
    logp = torch.log_softmax(logits, dim=-1)
    picked = logp.gather(-1, ids[:, 1:].unsqueeze(-1)).squeeze(-1)
    return picked.sum(dim=-1)                     # [B]

optimizer = torch.optim.SGD([W], lr=LR)
for step in range(6):
    with torch.no_grad():
        ref_c = seq_logprob(W_ref, chosen_ids)
        ref_r = seq_logprob(W_ref, rejected_ids)
    pol_c = seq_logprob(W, chosen_ids)
    pol_r = seq_logprob(W, rejected_ids)
    margin = BETA * ((pol_c - ref_c) - (pol_r - ref_r))
    loss = -F.logsigmoid(margin).mean()
    acc = (margin > 0).float().mean()
    if step in (0, 1, 2, 5):
        print("step %d  loss %.4f  reward_acc %.0f  margin %+.4f"
              % (step, loss.item(), acc.item(), margin.item()))
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

**Output:**

```text
step 0  loss 0.6931  reward_acc 0  margin +0.0000
step 1  loss 0.6013  reward_acc 1  margin +0.1929
step 2  loss 0.5262  reward_acc 1  margin +0.3674
step 5  loss 0.3713  reward_acc 1  margin +0.7992
```

Read the first line: loss 0.6931 is exactly ln(2) - with a zero margin, DPO's loss is a coin flip. One SGD step later the margin is positive and `reward_acc` flips to 1: the policy now ranks chosen above rejected *relative to the reference*, which is all DPO asks for.

### Step 3.1: Train with TRL's DPOTrainer

```text
# sketch - dpo_training.py (needs trl + a 3-8B model + GPU-hours)
"""
Train model with DPO alignment.
"""

import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from trl import DPOConfig, DPOTrainer
from datasets import Dataset

# Load preference pairs (validated in Part 2)
with open("preference_pairs.json", "r") as f:
    preference_data = json.load(f)

def format_for_dpo(preference_data):
    """Format preference data for DPO trainer"""
    return {
        "prompt": [item["prompt"] for item in preference_data],
        "chosen": [item["chosen"] for item in preference_data],
        "rejected": [item["rejected"] for item in preference_data],
    }

dataset_dict = format_for_dpo(preference_data)
train_dataset = Dataset.from_dict(dataset_dict)

# Split into train/validation
splits = train_dataset.train_test_split(test_size=0.2)
train_data = splits["train"]
eval_data = splits["test"]

print(f"Training samples: {len(train_data)}")
print(f"Validation samples: {len(eval_data)}")

# Load base model
model_name = "microsoft/Phi-3-mini-4k-instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name)
tokenizer.pad_token = tokenizer.eos_token

model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

# Apply LoRA for efficient training
from peft import LoraConfig, get_peft_model

peft_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# Configure DPO training. DPOConfig extends TrainingArguments and is
# also where the DPO-specific fields live (beta, label_smoothing,
# loss_type, max_length) - the trainer itself takes none of them.
training_args = DPOConfig(
    output_dir="./dpo_output",
    num_train_epochs=3,
    per_device_train_batch_size=2,  # Adjust based on GPU memory
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=4,
    learning_rate=1e-5,
    warmup_ratio=0.1,
    logging_steps=10,
    save_steps=50,
    eval_steps=50,
    fp16=True,
    gradient_checkpointing=True,
    report_to="none",  # or "wandb"/"tensorboard" if installed and logged in
    run_name="dpo-alignment-lab",
    # DPO-specific:
    beta=0.1,  # KL-anchor strength: HIGHER = more conservative,
               # i.e. the policy stays closer to the SFT reference
    label_smoothing=0.0,  # No label smoothing
    loss_type="sigmoid",  # Loss type
    max_length=512,  # max_prompt_length was removed from TRL -
                     # truncate prompt/completion in data prep
)

# Create DPO trainer
# ref_model=None + LoRA: the frozen base model under the adapter
# serves as the reference - no second model in VRAM.
dpo_trainer = DPOTrainer(
    model=model,
    ref_model=None,
    args=training_args,
    train_dataset=train_data,
    eval_dataset=eval_data,
    processing_class=tokenizer,
)

print("\nStarting DPO training...")
print(f"Beta (KL anchor): {training_args.beta} | max_length: {training_args.max_length}")

dpo_trainer.train()

dpo_trainer.save_model("./dpo_final_model")
tokenizer.save_pretrained("./dpo_final_model")

print("\nTraining complete!")
print(f"Model saved to ./dpo_final_model")
```

### Step 3.2: Monitor Training

You don't need a separate monitoring script: with `report_to` set, `DPOTrainer` logs the curves itself. The three that matter are `train/loss` (should fall from ln(2) toward 0), `train/rewards/accuracies` (should climb well above 0.5 - this is the reward accuracy from the block above), and `train/rewards/margins` (chosen-minus-rejected implicit reward gap, should widen). If `accuracies` saturates at 1.0 within the first epoch while `margins` explodes, the policy is memorizing the pairs rather than generalizing - lower the learning rate or raise beta.

---

## Part 4: Evaluate Alignment (60 minutes)

### Step 4.1: Compare Before/After

```text
# sketch - evaluate_alignment.py (loads two 3-8B models + GPU;
#          ~16 GB fp16 total - close other GPU workloads first)
"""
Compare base model vs DPO-aligned model.
"""

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

base_model_name = "microsoft/Phi-3-mini-4k-instruct"
aligned_model_name = "./dpo_final_model"

base_tokenizer = AutoTokenizer.from_pretrained(base_model_name)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

aligned_tokenizer = AutoTokenizer.from_pretrained(aligned_model_name)
aligned_model = AutoModelForCausalLM.from_pretrained(
    aligned_model_name,
    torch_dtype=torch.float16,
    device_map="auto",
)

test_prompts = [
    "What's the capital of France?",
    "Explain quantum computing.",
    "How do I make a cake?",
    "Write a poem about AI.",
    "What causes climate change?",
]

def generate_response(model, tokenizer, prompt, max_new_tokens=256):
    """Generate response from model"""
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.7,
            do_sample=True,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,
        )

    return tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:],
                            skip_special_tokens=True)

print("="*80)
print("COMPARISON: Base Model vs DPO-Aligned Model")
print("="*80)

for prompt in test_prompts:
    print(f"\n{'='*80}")
    print(f"PROMPT: {prompt}")
    print(f"{'='*80}\n")

    print(f"BASE MODEL:\n{generate_response(base_model, base_tokenizer, prompt)}\n")
    print(f"DPO-ALIGNED:\n{generate_response(aligned_model, aligned_tokenizer, prompt)}\n")

    print("-" * 80)
    preference = input("Which is better? (1=base, 2=aligned, ==tie, s=skip): ").strip()

    if preference == "1":
        print("Preference: Base model")
    elif preference == "2":
        print("Preference: DPO-aligned")
    elif preference == "=":
        print("Preference: Tie")
    else:
        print("Skipped")
```

### Step 4.2: Automated Evaluation

The scoring model choice matters. A **relevance cross-encoder** (like `cross-encoder/ms-marco-MiniLM-L-6-v2`) scores query-document fit, not response quality - using it as a "reward model" measures the wrong thing. Use a model trained on human preference pairs instead. Also: cross-encoder outputs are **unbounded logits**, often near zero or negative - report the absolute delta, never a percentage change over a raw score.

```text
# sketch - auto_evaluate.py (needs sentence-transformers + GPU;
#          base/aligned models come from Step 4.1's scope or reload them)
"""
Automated evaluation of alignment with a preference-trained reward model.
"""

import torch
from sentence_transformers import CrossEncoder

# A cross-encoder TRAINED on human preference pairs - not a relevance
# scorer like ms-marco-MiniLM. First run downloads ~700 MB.
reward_model = CrossEncoder("OpenAssistant/reward-model-deberta-v3-large-v2",
                            max_length=512,
                            device="cuda" if torch.cuda.is_available() else "cpu")

def score_response(prompt, response):
    """Score a (prompt, response) pair with the reward model."""
    with torch.no_grad():
        scores = reward_model.predict([[prompt, response]])
    return float(scores[0])

def evaluate_model(model, tokenizer, test_data):
    """Generate and score one response per test prompt."""
    scores = []
    for item in test_data:
        inputs = tokenizer(item["prompt"], return_tensors="pt").to(model.device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=128,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
            )
        response = tokenizer.decode(outputs[0][inputs['input_ids'].shape[1]:],
                                    skip_special_tokens=True)
        scores.append(score_response(item["prompt"], response))
    return sum(scores) / len(scores) if scores else 0.0

# test_data, base_model/tokenizer and aligned_model/tokenizer
# come from Step 4.1.
base_score = evaluate_model(base_model, base_tokenizer, test_data)
aligned_score = evaluate_model(aligned_model, aligned_tokenizer, test_data)

print(f"Base score:    {base_score:+.3f}")
print(f"Aligned score: {aligned_score:+.3f}")
print(f"Delta:         {aligned_score - base_score:+.3f}  "
      f"(raw logits: compare deltas, not percentages)")
```

Treat this as a sanity check, not a verdict: one reward model's logits correlate with preference quality but don't replace the human comparison in Step 4.1.

---

## Part 5: Analyze Results (30 minutes)

### Step 5.1: Summarize the Run

After training, report the summary numbers in a consistent shape so runs are comparable:

**Example summary from a small real run - the numbers are illustrative, yours will differ:**

```text
DPO Training Results:
  Training Steps: 500
  Final Loss: 0.800
  Final Reward Accuracy: 87.0%
  Training Time: 2.5 hours
  Human Preference Rate: 73.0%
```

`Human Preference Rate` is the fraction of Step 4.1 comparisons a human awarded to the aligned model - the only metric here that directly measures alignment.

### Step 5.2: Read Beta as the KL Anchor

Beta controls the strength of the pull toward the reference model:
- Lower beta (0.01-0.05): weaker anchor, larger drift from the reference - aggressive, less stable
- Higher beta (0.5-1.0): stronger anchor, stays close to the reference - conservative, may barely move the model
- beta = 0.1 is the common default and a good starting point

The block below makes that trade-off measurable. It reruns Part 3's pair at different betas with the learning rate scaled as `0.5/beta`, so every beta exerts the same optimization pressure on the log-prob scale - whatever differs between rows is the anchor itself, not optimizer speed:

```python
import torch
import torch.nn.functional as F

VOCAB = 8
chosen_ids = torch.tensor([[1, 3, 5, 2, 4, 6]])
rejected_ids = torch.tensor([[1, 3, 4, 2, 6, 5]])

def seq_logprob(W, ids):
    logits = W[ids[:, :-1]]
    logp = torch.log_softmax(logits, dim=-1)
    picked = logp.gather(-1, ids[:, 1:].unsqueeze(-1)).squeeze(-1)
    return picked.sum(dim=-1)

def run_dpo(beta, steps=40):
    torch.manual_seed(42)
    W = (torch.randn(VOCAB, VOCAB) * 0.5).requires_grad_(True)
    W_ref = W.detach().clone()
    # lr scales as 1/beta so every beta exerts the same pressure on the
    # log-prob scale; whatever differs between rows is the anchor itself.
    opt = torch.optim.SGD([W], lr=0.5 / beta)
    for _ in range(steps):
        with torch.no_grad():
            ref_c = seq_logprob(W_ref, chosen_ids)
            ref_r = seq_logprob(W_ref, rejected_ids)
        pol_c = seq_logprob(W, chosen_ids)
        pol_r = seq_logprob(W, rejected_ids)
        margin = beta * ((pol_c - ref_c) - (pol_r - ref_r))
        loss = -F.logsigmoid(margin).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        ref_c = seq_logprob(W_ref, chosen_ids)
        ref_r = seq_logprob(W_ref, rejected_ids)
        pol_c = seq_logprob(W, chosen_ids)
        pol_r = seq_logprob(W, rejected_ids)
    margin = beta * ((pol_c - ref_c) - (pol_r - ref_r))
    drift = (pol_c - ref_c).abs() + (pol_r - ref_r).abs()
    return -F.logsigmoid(margin).mean().item(), \
        (margin > 0).float().mean().item(), drift.item()

for beta in (0.01, 0.05, 0.1, 0.5, 1.0):
    loss, acc, drift = run_dpo(beta)
    print("beta=%4.2f  loss %.4f  reward_acc %.0f  logprob drift %8.3f"
          % (beta, loss, acc, drift))
```

**Output:**

```text
beta=0.01  loss 0.4289  reward_acc 1  logprob drift   62.450
beta=0.05  loss 0.1398  reward_acc 1  logprob drift   37.930
beta=0.10  loss 0.0701  reward_acc 1  logprob drift   26.220
beta=0.50  loss 0.0128  reward_acc 1  logprob drift    8.700
beta=1.00  loss 0.0062  reward_acc 1  logprob drift    5.078
```

Read the two ends. At beta = 0.01 the policy moved **62 log-prob nats** away from the reference and *still* hasn't separated the pair confidently (loss 0.43); at beta = 1.0 it moved 5 nats and the pair is cleanly separated (loss 0.006). The weak anchor pays more drift for less signal. On real models the same pattern appears as KL blow-up: the low-beta run that drifts farthest is also the one that starts losing fluency - which is why 0.1 is the default.

---

## Completion Checklist

Use this checklist to track your progress:

### Setup
- [ ] Environment configured
- [ ] Dependencies installed
- [ ] Base model downloaded

### Data Preparation
- [ ] Candidates generated
- [ ] Preference pairs created and validated
- [ ] Dataset formatted for DPO

### Training
- [ ] DPO trainer configured
- [ ] Training completed (3 epochs)
- [ ] Model saved

### Evaluation
- [ ] Base model vs aligned comparison
- [ ] Automated evaluation completed
- [ ] Human evaluation completed

### Analysis
- [ ] Training metrics analyzed
- [ ] Results documented
- [ ] Key learnings recorded

---

## Key Learnings

### What DPO Does

1. **Directly optimizes** for human preferences
2. **No reward model** needed - the implicit reward does the job
3. **Simpler** than RLHF/PPO
4. **More stable** training

### Common Issues

**Issue 1: Training is unstable**
- Solution: Reduce learning rate or increase beta

**Issue 2: Model overfits to training data**
- Solution: Add regularization, reduce training epochs

**Issue 3: Aligned model is too conservative**
- Solution: Reduce beta value

**Issue 4: No improvement over baseline**
- Solution: Check preference data quality (run the Part 2 validator), increase training data

### Best Practices

1. **Start with high-quality preference data**
2. **Use beta=0.1** as starting point
3. **Monitor reward accuracy** during training
4. **Use small learning rate** (1e-5 to 5e-5)
5. **Validate with human evaluation** - reward-model deltas support but don't replace it

---

## You're Now Ready For

- **[5203: RLHF]** - the reward-model + PPO pipeline DPO replaced, and when it still wins ([5203-RLHF.md](../../phases/phase5-finetuning/5200-alignment/5203-RLHF.md))
- **[5202: Alignment Orchestration]** - combining SFT, DPO, and RLAIF into full alignment pipelines ([5202-Alignment-Orchestration.md](../../phases/phase5-finetuning/5200-alignment/5202-Alignment-Orchestration.md))
- **[LAB 007: Production RAG]** - a different axis of model quality: grounding ([LAB-007-Production-RAG.md](LAB-007-Production-RAG.md))

Further reading:
- [DPO Paper: Direct Preference Optimization](https://arxiv.org/abs/2305.18290)
- [TRL DPOTrainer Documentation](https://huggingface.co/docs/trl/main/en/dpo_trainer)
- **[5201: DPO Theory]** - the full derivation of the loss you optimized in Part 3 ([5201-DPO-Theory.md](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md))
