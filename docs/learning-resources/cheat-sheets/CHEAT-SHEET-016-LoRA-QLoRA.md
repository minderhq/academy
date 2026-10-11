---
Document ID: CHEAT-SHEET-016
Title: "CHEAT-SHEET-016: LoRA & QLoRA"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'lora', 'qlora', 'peft']
---

# CHEAT-SHEET-016: LoRA & QLoRA

## Quick Reference for LoRA

**Version:** 1.0

Parameter-efficient fine-tuning is three decisions stacked: the rank
budget, the target modules, and the base precision the adapters train
against. This sheet maps the low-rank arithmetic, the knob tables, the
QLoRA pipeline order, and the merge rules that keep deployment clean.

---

## The Low-Rank Bet

Fine-tuning updates have low intrinsic rank: freeze the base weight W
and train a down-projection A (r x in) and an up-projection B (r x out)
so W' = W + B@A scaled by alpha/r. One 4096x4096 projection carries
16,777,216 weights; at r=8 the adapter pair carries 65,536 — 256x
fewer. Initialization is load-bearing: kaiming-uniform A, zeros B, so
B@A = 0 and every adapter starts as an exact identity. Merging folds
the delta into W — and needs the `merged` flag, because without it the
forward adds the LoRA path again and emits Wx + 2*deltaW: silently
wrong outputs from a silently doubled update.

```python
D, F = 4096, 11008  # Llama-2-7B hidden / intermediate
TOTAL = 6_738_415_616
NLAYER = 32

FULL = D * D
r8 = 8 * (D + D)
print("one 4096x4096 proj: full %d vs LoRA r=8 %d -> %.0fx smaller"
      % (FULL, r8, FULL / r8))

def trainable(rank, names):
    sizes = {"q": (D, D), "k": (D, D), "v": (D, D), "o": (D, D),
             "gate": (D, F), "up": (D, F), "down": (F, D)}
    return NLAYER * sum(rank * (a + b)
                        for a, b in (sizes[n] for n in names))

for label, names in [("q+v", ["q", "v"]),
                     ("all-attn", ["q", "k", "v", "o"]),
                     ("all-linear", ["q", "k", "v", "o", "gate", "up", "down"])]:
    p = trainable(8, names)
    print("LoRA %-10s r=8: %10d trainable (%.4f%%)" % (label, p, 100 * p / TOTAL))
p16 = trainable(16, ["q", "k", "v", "o"])
print("QLoRA all-attn r=16: %d trainable (%.4f%%)" % (p16, 100 * p16 / TOTAL))

alpha, rank = 16, 8
print("scaling alpha/r:", alpha / rank)

adapter = 0.02 + 0.02 + 0.03
print("7B LoRA fp16 ~%.1f GB (24GB-class) | QLoRA NF4 ~%.1f GB (8GB-class)"
      % (14.0 + 2.0 + adapter, 3.5 + 2.0 + adapter))
```

---

## The Three Knobs

**Rank** — the capacity ladder: r=2-4 for style, r=8-16 the default
band, r=32-64 for heavy domain shift, diminishing returns past 64.
Start at r=8 and raise only when underfitting. **Alpha** — the scale
alpha/r: alpha = r gives 1.0, alpha = 2r gives 2.0 (r=8, alpha=16 is
the canonical pairing). **Targets** — the budget ladder on Llama-2-7B:

| Target modules | Trainable @ r=8 | Typical use |
| --- | --- | --- |
| q_proj + v_proj | 4.19M (0.06%) | instruction tuning |
| all attention (q,k,v,o) | 8.39M (0.12%) | style transfer |
| + FFN (gate,up,down) | ~20M (0.30%) | domain adaptation |

Two convention traps. `target_modules = "all-linear"` must be the
STRING: the list `["all-linear"]` matches no module name and silently
wraps nothing. Dropout sits on the LoRA path's INPUT (the PEFT
convention, `lora_dropout=0.05-0.1`); 0.0 for style transfer.
Variants: DoRA (`use_dora=True`) normalizes the COMBINED weight per
output channel and perturbs direction only; AdaLoRA shifts rank budget
by importance (`AdaLoraConfig(init_r, tfinal, deltaT)` runs the
trimming schedule itself).

---

## QLoRA: The 4-Bit Base

Same adapters, quantized base. Three innovations: NF4 (4-bit
NormalFloat tuned to the normal weight distribution), double
quantization (quantize the quantization constants; 0.37 bits/param —
~3 GB per 65B), and paged optimizers (optimizer state pages through
CPU RAM on CUDA unified memory). The 7B bill: fp16 base ~16.1 GB needs
a 24GB-class card; NF4 base ~5.6 GB fits an 8GB-class card. The paper's
headline is a 65B on one 48 GB GPU.

Pipeline order: `BitsAndBytesConfig(load_in_4bit, nf4, bf16 compute,
double quant)` -> `AutoModelForCausalLM.from_pretrained` ->
`prepare_model_for_kbit_training` -> `LoraConfig` -> `get_peft_model`.
QLoRA defaults run one step richer than LoRA: r=16 on all attention
(16.8M = 0.25%), lr 2e-4 (the 4-bit base needs the stronger signal;
1e-4 underfits, 5e-4 destabilizes), cosine schedule with 3% warmup,
`optim="paged_adamw_32bit"` — a TrainingArguments STRING, not a custom
class (the Paged* classes are paged by construction). Keep
`bf16=True` matching `bnb_4bit_compute_dtype`: bf16 compute inside
fp16 AMP with a grad scaler is a contradiction. Gradient checkpointing
saves ~50% of activation memory for ~20% time.

---

## Merge on the 16-Bit Base

`merge_and_unload()` is not supported on a 4-bit bitsandbytes model —
and the adapter was trained against dequantized weights anyway. Load
the FP16 base, attach the adapter, merge, save, then re-quantize the
merged model for inference. Converters never apply adapters: merge
BEFORE quantizing to GGUF/exl2.

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| NaN loss early | lr too hot for the 4-bit base | halve lr (2e-4 -> 1e-4), check data |
| OOM mid-run | activations dominate the budget | batch 2 + accumulation 8 + gradient checkpointing |
| Loss plateaus high | rank too low for the shift | raise r (16 -> 32); alpha with it |
| Adapter has ~0 trainable params | `target_modules=["all-linear"]` list form matches nothing | use the string `"all-linear"` or real module names |
| merge_and_unload() crashes | 4-bit bnb base does not support merge | merge on the FP16 base, then re-quantize |
| Outputs subtly wrong after merge | merged flag missing: forward adds delta twice | set merged (or use PEFT's own merge path) |

---

**Quick Reference for:**

- [Module 5101: LoRA Logic](../../phases/phase5-finetuning/5100-peft/5101-LoRA-Logic.md)
- [Module 5102: QLoRA Pipelines](../../phases/phase5-finetuning/5100-peft/5102-QLoRA-Pipelines.md)
- [Module 5103: Adapters](../../phases/phase5-finetuning/5100-peft/5103-Adapters.md)
- [CHEAT-SHEET-010: Alignment Methods](./CHEAT-SHEET-010-Alignment-Methods.md)
