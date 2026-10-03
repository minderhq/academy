---
Document ID: TUTORIAL-007
Title: "TUTORIAL-007: LoRA Basics"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Intermediate
Estimated Time: 1 hour
Prerequisites: [TUTORIAL-001]
Tags: ['tutorial', 'lora', 'finetuning', 'peft']
---

# TUTORIAL-007: LoRA Basics

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why LoRA: The Numbers, Honestly](#why-lora-the-numbers-honestly)
- [How LoRA Works](#how-lora-works)
- [A LoRA Layer From Scratch](#a-lora-layer-from-scratch)
- [Using PEFT](#using-peft)
- [Training with TRL](#training-with-trl)
- [Inference: Adapters and Merging](#inference-adapters-and-merging)
- [QLoRA: Fine-Tuning on Consumer GPUs](#qlora-fine-tuning-on-consumer-gpus)
- [Managing Multiple Adapters](#managing-multiple-adapters)
- [Hyperparameters](#hyperparameters)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)
- [References](#references)

---

## Learning Objectives

After completing this tutorial, you will be able to:

- Explain the low-rank hypothesis behind LoRA and what initializing B to zero buys you
- Implement a LoRA linear layer from scratch with the paper's matrix orientation and the α/r scaling
- Fine-tune a causal LM with PEFT + TRL using the current API (SFTConfig, processing_class)
- Set up QLoRA correctly — NF4, double quantization, `prepare_model_for_kbit_training`, gradient checkpointing — and know why each piece is there
- Choose rank, alpha, and target modules deliberately, and debug the standard failure modes (OOM, slow training, "loss went down but the model got worse")

---

## Abstract

LoRA (Low-Rank Adaptation) fine-tunes a model by learning a low-rank *update* to selected weight matrices while the original weights stay frozen — a few million trainable parameters instead of billions, saved as megabyte-scale adapter files instead of full checkpoints. This tutorial builds the mechanism from scratch (correct matrix shapes, zero-init, α/r scaling), then does the same job with the production stack: PEFT's `LoraConfig`, TRL's `SFTTrainer`, and QLoRA for consumer GPUs. For the theory behind why low-rank updates work, see [5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md); for a guided hands-on lab, [LAB-003](../labs/LAB-003-LoRA-FineTuning.md).

## Why LoRA: The Numbers, Honestly

Full fine-tuning of a 7B model is not memory-hard, it is memory-*impossible* on one consumer card — and the gap is mostly optimizer state, not weights:

```text
Memory to TRAIN a 7B model (AdamW, mixed precision)

Full fine-tune
  weights (bf16)        ~14 GB
  gradients (bf16)      ~14 GB
  optimizer states      ~28 GB   (AdamW keeps 2 fp32 moments)
  + activations                  -> 60-80 GB: multi-GPU territory

LoRA (frozen bf16 base)
  weights (bf16, frozen) ~14 GB   no grads, no optimizer state
  adapters + their optim  ~0.1 GB
  + activations                    -> ~18-20 GB: one 24 GB card

QLoRA (frozen NF4 base)
  weights (4-bit)        ~3.5-4 GB
  adapters + optim + acts           -> ~8-12 GB: laptop-class

Storage per task
  full checkpoint       ~14 GB
  LoRA adapter          ~20-100 MB
```

The adapter storage number is what changes your workflow: one base model on disk, many task adapters beside it.

## How LoRA Works

Fine-tuned weight updates are approximately low-rank — the empirical observation behind LoRA is that the *change* ΔW during adaptation has far fewer effective degrees of freedom than d². LoRA makes that assumption structural: it constrains the update to rank r from the start.

```text
Forward pass

  h = W0 @ x + (alpha / r) * B @ A @ x
            \_______ ΔW _______/

  W0 [d, d]   pretrained, FROZEN
  A  [r, d]   down-projection, r << d, random (Gaussian) init
  B  [d, r]   up-projection,   initialized to ZERO
  alpha       scaling constant, typically 2x rank

At initialization B = 0, so ΔW = 0: training starts from the
pretrained model EXACTLY. Gradients still flow through A and B
(because B@A@x is differentiable in both), so training can move
off the frozen point immediately.
```

```text
Parameter count, per adapted matrix (d = 4096, r = 16)

  full update W:        4096 x 4096 = 16,777,216 params

  LoRA:
      A [16, 4096]   65,536 params
      B [4096, 16]   65,536 params
      B @ A [4096, 4096]      131,072 params total

  131,072 / 16,777,216 = 0.78% per matrix

  Llama-2-7B scale (r=16, q+v, 32 layers):
    131,072 x 2 (q+v) x 32 layers = 8,388,608 trainable
    = ~0.12% of the 6.74B base model
```

## A LoRA Layer From Scratch

```python
import torch
import torch.nn as nn

class LoRALinear(nn.Module):
    """LoRA (Hu et al., 2021) on top of a frozen linear layer.
    A: down-projection [r, in], random init.
    B: up-projection [out, r], ZERO init (so training starts
    exactly at the pretrained function)."""

    def __init__(self, in_features, out_features,
                 rank=16, alpha=32):
        super().__init__()
        self.linear = nn.Linear(in_features, out_features,
                                bias=False)
        self.linear.weight.requires_grad = False  # frozen base

        self.lora_A = nn.Parameter(
            torch.randn(rank, in_features) * 0.01)
        self.lora_B = nn.Parameter(
            torch.zeros(out_features, rank))

        self.scaling = alpha / rank   # the real LoRA scale

    def forward(self, x):
        # frozen path + learned low-rank path
        return self.linear(x) + \
            (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
```

```text
Three details people get wrong
1. Orientation: A is [r, d] (down), B is [d, r] (up),
   DeltaW = B @ A. Swapping them still "runs" but the init
   story and the paper's shapes no longer line up
2. scaling = alpha / r, not 1/r: alpha is the knob that keeps
   adapter strength stable when you change rank
3. B starts at ZERO, A does not. Init both random and the
   model starts perturbed; init both zero and the gradient
   through A is zero - training goes nowhere
```

## Using PEFT

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model

model_name = "meta-llama/Llama-2-7b-hf"
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    dtype=torch.float16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

lora_config = LoraConfig(
    r=16,                                  # rank
    lora_alpha=32,                         # scaling: alpha / r
    target_modules=["q_proj", "v_proj"],   # attention only
    lora_dropout=0.05,
    bias="none",                           # never train biases
    task_type="CAUSAL_LM",
)

model = get_peft_model(model, lora_config)
model.print_trainable_parameters()
# Llama-2-7B, r=16, q+v: 8,388,608 trainable params
# = ~0.12% of the 6.74B base model
```

```text
How the trainable count is computed (do this yourself once):
  per adapted matrix: r*in + out*r = 16*4096 + 4096*16
                     = 131,072
  q and v are two matrices per layer:
    131,072 x 2 = 262,144 per layer
  x 32 transformer layers = 8,388,608 trainable params
  8,388,608 / 6,738,415,616 = 0.1245% - the number peft
  prints. Scale by YOUR hidden size, layer count, and
  target-module count.
```

The honest way to know is to run `print_trainable_parameters()` and read its output rather than copy numbers from a tutorial. Typical percentages on a 7B base: ~0.1% attention-only, up to ~1% with all-linear.

## Training with TRL

```python
from datasets import load_dataset
from transformers import TrainingArguments
from trl import SFTConfig, SFTTrainer

dataset = load_dataset("databricks/databricks-dolly-15k")

def format_prompt(sample):
    return {
        "text": (
            "### Instruction:\n"
            f"{sample['instruction']}\n\n"
            "### Response:\n"
            f"{sample['response']}"
        )
    }

# ONE split, one seed - do not call train_test_split twice
split = dataset["train"].train_test_split(test_size=0.1, seed=42)
train_data = split["train"].map(format_prompt)
eval_data = split["test"].map(format_prompt)

training_args = SFTConfig(
    output_dir="./lora-output",
    learning_rate=2e-4,                 # 10-100x full-FT lr
    per_device_train_batch_size=4,
    gradient_accumulation_steps=4,      # effective batch 16
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=10,
    save_steps=100,
    bf16=True,                          # Ampere+; fp16 on older
    max_grad_norm=0.3,
    warmup_ratio=0.03,
    lr_scheduler_type="cosine",
    max_length=512,                     # TRL sequences cap
    dataset_text_field="text",
    eval_strategy="steps",
    eval_steps=100,
)

trainer = SFTTrainer(
    model=model,
    train_dataset=train_data,
    eval_dataset=eval_data,
    args=training_args,
    processing_class=tokenizer,         # current TRL API
)

trainer.train()

# saves the ADAPTER only - megabytes, not gigabytes
trainer.save_model("./lora-adapters")
```

```text
Reading the hyperparameters
- lr 2e-4: LoRA's small trainable set tolerates (and wants)
  much higher lr than full fine-tuning (1e-5..5e-5)
- bf16 over fp16 on Ampere and later: same speed, wider
  dynamic range, fewer overflow surprises
- eval during training is not optional: "loss went down but
  the model got worse" is the #1 LoRA bug report, and it is
  invisible without an eval split
```

## Inference: Adapters and Merging

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    dtype=torch.float16,
    device_map="auto",
)
model = PeftModel.from_pretrained(base_model, "./lora-adapters")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")

prompt = "### Instruction:\nExplain quantum computing\n\n### Response:\n"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

outputs = model.generate(
    **inputs,
    max_new_tokens=256,
    do_sample=True,        # REQUIRED for temperature/top_p
    temperature=0.7,
    top_p=0.9,
)
# strip the prompt from the output
response = tokenizer.decode(
    outputs[0][inputs["input_ids"].shape[1]:],
    skip_special_tokens=True,
)
print(response)
```

```text
Sampling caveat that generates bug reports: with
do_sample=False (the default), temperature and top_p are
IGNORED and generation is greedy - the parameters pass
silently without changing behavior.

Deploying merged (no PEFT at inference time):

    merged = model.merge_and_unload()      # W0 + alpha/r * BA
    merged.save_pretrained("./merged-model")

Merging costs the multi-adapter workflow (one full checkpoint
per task) but removes the PEFT dependency and the adapter
compose overhead at serving time.
```

## QLoRA: Fine-Tuning on Consumer GPUs

QLoRA (Dettmers et al., 2023) freezes the base model in 4-bit NF4 and trains LoRA adapters on top — a 7B model fits in under 10 GB. Two glue pieces are load-bearing and usually missing from quickstarts:

```python
import torch
from transformers import (AutoModelForCausalLM,
                          BitsAndBytesConfig)
from peft import (LoraConfig, get_peft_model,
                  prepare_model_for_kbit_training)

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",              # NormalFloat4
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,         # quantize the scales
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-2-7b-hf",
    quantization_config=bnb_config,
    device_map="auto",
)

# 1. casts norms/embeddings to fp32 for stability and
# 2. enables gradients on inputs (required with checkpointing)
model = prepare_model_for_kbit_training(model)

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    # all attention + MLP projections - QLoRA can afford more
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                    "gate_proj", "up_proj", "down_proj"],
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM",
)
model = get_peft_model(model, lora_config)
model.config.use_cache = False   # incompatible with checkpointing
```

```python
# in TrainingArguments / SFTConfig:
#     gradient_checkpointing=True
```

```text
Why each piece exists
- nf4: quantization grid matched to the normal-ish weight
  distribution - closer to fp16 than uniform int4 at 4 bits
- double quant: quantizes the quantization constants, ~0.4
  bits/param saved, no measurable quality cost
- prepare_model_for_kbit_training: frozen-quantized weights
  break the usual gradient flow assumptions; this helper
  fixes numerics (fp32 norms) and wires input gradients
- use_cache=False: the KV cache conflicts with activation
  checkpointing; leave it off during training
Full pipeline details: [5102: QLoRA Pipelines]
(../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
```

## Managing Multiple Adapters

One base model, many task adapters — the workflow LoRA exists to enable:

```python
from peft import PeftModel

model = PeftModel.from_pretrained(
    base_model, "adapters/code", adapter_name="code")
model.load_adapter("adapters/chat", adapter_name="chat")

model.set_adapter("code")       # route through the code adapter
model.set_adapter("chat")       # ... now the chat adapter

# combine adapters into a new one (a real merge, not a switch)
model.add_weighted_adapter(
    adapters=["code", "chat"],
    weights=[0.5, 0.5],
    adapter_name="combo",
)
model.set_adapter("combo")
```

```text
generate() takes TOKENS, not text - every call goes through
the tokenizer:

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    model.generate(**inputs, ...)

adapters are ~50-100 MB each: hot-swap per request in serving,
or merge a weighted combination offline for a fixed blend.
```

## Hyperparameters

| Parameter | Typical Values | Effect |
|-----------|----------------|--------|
| **r (rank)** | 8–64 | Capacity of the update; more rank = more params |
| **alpha** | ~1–2× r | Output scale (α/r); keep α fixed while sweeping r |
| **dropout** | 0.05–0.1 | Regularization on the adapter path |
| **target_modules** | q/v → all-linear | Where adapters go; the biggest quality lever |
| **lr** | 1e-4 – 3e-4 | 10–100× full fine-tuning rates |

```text
Choosing rank, honestly
- r=8-16: style, formatting, small instruction sets - most
  fine-tuning jobs live here
- r=32-64: domain adaptation with real terminology shifts,
  larger datasets
- beyond ~r=64 rarely pays on a 7B model - if capacity is the
  bottleneck, widen target_modules (all-linear) before raising
  rank past 64
- hold alpha/r constant across rank sweeps or your comparisons
  measure scale, not capacity
```

## Troubleshooting

```text
CUDA out of memory
  per_device_train_batch_size=1, raise
  gradient_accumulation_steps to compensate ->
  gradient_checkpointing=True -> switch base to QLoRA (NF4)
  (in that order; each step costs speed)

Slow training
  attn_implementation="flash_attention_2" in from_pretrained
  (requires the flash-attn package - it is a build, not a pip
  one-liner) -> TRL packing for short sequences -> fewer
  target modules if VRAM thrashing is the cause

Loss went down, model got WORSE
  overfitting: 3 epochs on 1-15k samples is already a lot;
  check eval loss, add/raise lora_dropout, cut epochs
  formatting drift: the model learned the template, not the
  task - verify the prompt format matches inference EXACTLY
  lr too high: 2e-4 is a starting point, not a law; halve it
  and re-run before blaming the method

Loss barely moves
  adapters on too few modules (q+v only is the floor, not the
  default) -> raise rank for genuinely hard tasks -> check
  that the BASE actually requires grad where expected
  (print_trainable_parameters)
```

## Best Practices

```text
1. QLoRA (NF4 + double quant + prepare_model_for_kbit_training)
   is the default starting point on any card under 24 GB
2. B zero-init, A random-init, scaling alpha/r: the three
   correctness details of every LoRA implementation
3. attention-only (q/v) first; add MLP projections only when
   eval says the model is underfitting - all-linear is the
   ceiling, not the default
4. Keep an eval split and watch it: LoRA overfits fast, and
   train loss hides it
5. lr 1e-4..3e-4, cosine schedule, warmup ~3%: the stable
   recipe; sweep nothing until this converges cleanly
6. Save adapters per task, merge only the one you deploy -
   merged checkpoints are per-task 14 GB commitments
7. Match the inference prompt template to the training
   template byte-for-byte; template drift is the most common
   "the adapter does not work" cause
```

---

## References

### Related PROJECT-OMEGA Documents

- [5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
- [5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
- [5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)
- [LAB-003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)

---

## Next Steps

- Hands-on: **[LAB-003: LoRA Fine-Tuning](../labs/LAB-003-LoRA-FineTuning.md)**
- Theory: **[5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)**
- Advanced: **[5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)** → **[5201: DPO Theory](../../phases/phase5-finetuning/5200-alignment/5201-DPO-Theory.md)**
