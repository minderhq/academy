---
Document ID: 5405
Title: "5405: FSDP2 and torchao - Composable Sharding and Quantized Training"
Phase: 5
Module: 5400
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['distributed', 'fsdp', 'torchao', 'training', 'quantization']
---

# 5405: FSDP2 and torchao - Composable Sharding and Quantized Training

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Sharding Ladder: DDP, FSDP1, FSDP2](#the-sharding-ladder-ddp-fsdp1-fsdp2)
- [fully_shard: Per-Parameter Sharding](#fully_shard-per-parameter-sharding)
- [Memory Economics](#memory-economics)
- [torchao: The Quantization Stack Under Training](#torchao-the-quantization-stack-under-training)
- [Float8 Training Recipes](#float8-training-recipes)
- [QAT Without Dead Gradients](#qat-without-dead-gradients)
- [The Trainer Surface: accelerate and transformers](#the-trainer-surface-accelerate-and-transformers)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Explain what FSDP2 changes over FSDP1: per-parameter `DTensor` sharding instead of flat-parameter buckets
- Call `fully_shard` on a model and read the three states a mixed-precision parameter passes through in one step
- Compute the per-rank memory ledger DDP versus FSDP pays, including the all-gather spike
- Quantize a model with `torchao`'s `quantize_` API for inference and train with its float8 recipes
- Say why fake quantization kills gradients without a straight-through estimator - and demonstrate the cure
- Wire FSDP2 through `accelerate`/`transformers` config and know what the trainer normalizes behind your back

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[5401](./5401-Data-Parallelism.md) taught DDP and classic FSDP; [5404](./5404-Distributed-Optimization.md) taught the optimizer-side tricks. This lesson is the modern stack those lessons were pointing at: **FSDP2**, PyTorch's rewrite of fully sharded data parallelism on `DTensor`, and **torchao**, the PyTorch-native quantization library that trains and serves low-bit models with plain `torch` code. The two belong in one lesson because the frontier labs run them together - torchtitan, PyTorch's reference training framework, composes `fully_shard` + torchao float8 + `torch.compile` as one pipeline. You will shard a real model on a single rank and watch the parameter's three states, run the fp8 arithmetic that shows why per-row scales exist, break and fix QAT gradients, and finish at the `accelerate` config surface every HF trainer job actually uses.

## The Sharding Ladder: DDP, FSDP1, FSDP2

Each rung of the ladder trades communication for memory:

```text
DDP      every rank holds:  full params + full grads + full optimizer state
         communicates:      gradients (bucketed, overlapped with backward)
         ceiling:           model must fit on one GPU

FSDP1    every rank holds:  1/N of flat-param BUCKETS (per wrap-unit)
         communicates:      all-gather params before each fwd/bfw use,
                            reduce-scatter grads after
         ceiling:           flat buckets fuse params; per-param control is lost;
                            code lives in torch.distributed.fsdp (FullyShardedDataParallel)

FSDP2    every rank holds:  1/N of EACH PARAMETER as a DTensor (Shard(0))
         communicates:      same all-gather/reduce-scatter protocol,
                            but per-parameter, composable, and hookable
         surface:           torch.distributed.fsdp.fully_shard - one call per module
```

Three facts make FSDP2 the generation that stuck:

1. **`DTensor` is the sharding unit, not wrapper modules.** FSDP1 replaced your submodules with `FSDP(...)` wrappers and fused their parameters into flat buffers you could not inspect per-name. FSDP2 leaves every parameter a `nn.Parameter` whose storage is a `DTensor` with a `Shard(0)` placement on the data-parallel mesh - `model.layer.weight` still points at real weights.
2. **Composition over wrapping.** `fully_shard(module)` is idempotent per module: shard the layers that deserve their own communication scope, then the container. There is no `auto_wrap_policy` DSL to learn.
3. **The rest of the modern stack assumes it.** torchao float8 training, activation checkpointing tooling, and torchtitan's recipes all target FSDP2's per-parameter view. FSDP1 remains supported but is the legacy surface.

## fully_shard: Per-Parameter Sharding

One call shards every parameter the module (transitively) owns onto the default world mesh. On one rank with the `gloo` backend - the configuration that also runs on CPU and Windows - the whole protocol is observable without a cluster:

```python
import os

os.environ.setdefault("MASTER_ADDR", "localhost")
os.environ.setdefault("MASTER_PORT", "29617")
os.environ.setdefault("RANK", "0")
os.environ.setdefault("WORLD_SIZE", "1")

import torch
import torch.nn as nn
import torch.distributed as dist
from torch.distributed.fsdp import fully_shard, MixedPrecisionPolicy

dist.init_process_group(backend="gloo")


class ToyBlock(nn.Module):
    def __init__(self, dim=32):
        super().__init__()
        self.in_proj = nn.Linear(dim, 2 * dim, bias=False)
        self.out_proj = nn.Linear(2 * dim, dim, bias=False)

    def forward(self, x):
        return self.out_proj(torch.relu(self.in_proj(x)))


model = ToyBlock()
mp = MixedPrecisionPolicy(param_dtype=torch.bfloat16, reduce_dtype=torch.float32)
fully_shard(model, mp_policy=mp)

w = model.in_proj.weight
print(f"before forward : {type(w).__name__}  local dtype {w.to_local().dtype}")

out = model(torch.randn(4, 32))
w2 = model.in_proj.weight
print(f"after forward  : {type(w2).__name__}  dtype {w2.dtype}")

loss = out.square().mean()
loss.backward()
w3 = model.in_proj.weight
print(f"after backward : {type(w3).__name__}  local dtype {w3.to_local().dtype}"
      f"  grad {type(model.in_proj.weight.grad).__name__}")
dist.destroy_process_group()
```

Run it and the parameter walks through three states in one step:

```text
before forward : DTensor   local dtype torch.float32   <- sharded fp32 master
after forward  : Parameter dtype   torch.bfloat16      <- unsharded bf16 all-gather
after backward : DTensor   local dtype torch.float32   <- re-sharded, grad is a DTensor
```

That walk **is** the memory story of sharded mixed-precision training: at rest you hold `1/N` of the fp32 master weights; for the duration of the forward you pay for a full-size bf16 copy (the all-gather); backward frees it and re-shards. `reshard_after_forward=False` keeps the unsharded copy alive between forward and backward - faster second use, worse peak memory. Under the default (`True`), each layer's copy lives only as long as its slice of the compute.

`fully_shard`'s signature shows the other levers: `mesh` (a `DeviceMesh` you build with `init_device_mesh` for FSDP + tensor-parallel hybrids), `shard_placement_fn` (exclude a parameter from sharding), `mp_policy`, `offload_policy` (CPU offload), and `ignored_params`.

## Memory Economics

The arithmetic that decides DDP versus FSDP for a 7B-parameter model at bf16:

```python
N_PARAMS = 7_000_000_000
BYTES_BF16 = 2
world = 4
replica_gb = N_PARAMS * BYTES_BF16 / 1e9
shard_gb = replica_gb / world
print(f"weights: {N_PARAMS/1e9:.0f}B params x {BYTES_BF16} B = {replica_gb:.0f} GB bf16")
print(f"DDP  per-rank (full replica): {replica_gb:.0f} GB")
print(f"FSDP per-rank (1/{world} shard): {shard_gb:.1f} GB")
print(f"all-gather spike during forward: +{shard_gb:.1f} GB unsharded copy")
```

Two corrections to the naive ledger, both learned the hard way:

- **Optimizer state multiplies the FSDP win.** Adam holds two fp32 moments per parameter; under DDP that state is replicated (`+56 GB` for 7B), under FSDP2 it is sharded with the parameters. The bigger the optimizer, the bigger FSDP's relative win - and that is before activation memory.
- **The all-gather spike scales with the shard unit.** Shard per-layer (fine-grained `fully_shard` per submodule) and the spike is one layer's worth; shard one giant container and the spike is the whole model. This is why 5401's transformer auto-wrap advice survives into FSDP2 as "call `fully_shard` per block".

## torchao: The Quantization Stack Under Training

[Phase 4](../../phase4-quantization/4100-low-bit/README.md) quantized *trained* checkpoints: GGUF, AWQ, EXL2 - artifacts for serving. **torchao** works the other side of the wall: quantization that participates in training (float8 recipes, QAT) and quantization defined as `torch` tensors (`Float8Tensor`, `Int4Tensor`) so the same `quantize_` call serves inference without leaving PyTorch. The API is one in-place function plus configs:

```python
import torch
from torchao.quantization import (
    Float8DynamicActivationFloat8WeightConfig,
    Int4WeightOnlyConfig,
    quantize_,
)
from torchao.quantization.granularity import PerTensor, PerGroup

# float8 dynamic-activation + float8-weight: the training-adjacent recipe
quantize_(model, Float8DynamicActivationFloat8WeightConfig(granularity=PerTensor()))

# int4 weight-only, group 32: the serving recipe, weights become Int4Tensor
quantize_(model, Int4WeightOnlyConfig(group_size=32))

# the same quantize_ drives QAT through QATConfig (next section)
```

`quantize_` swaps each `nn.Linear`'s weight for a quantized tensor subclass whose `__matmul__` dequantizes (or dispatches a fused kernel). Nothing else in your code changes - the model still prints, saves, and forwards like a `nn.Module`.

> **torchao is an optional package** (`pip install torchao`) - the fences in the next two sections document its API against the released library; they stop at the import in a QA environment by design.

## Float8 Training Recipes

fp8 (`e4m3` for forward tensors) halves the bytes of bf16 and is how frontier-scale pretraining squeezes throughput. Its whole difficulty is scale selection - and one poisoned scale shows why per-tensor is fragile:

```python
import torch

torch.manual_seed(0)
W = torch.randn(256, 512) * 1e-4
W[0, :] *= 2e4  # one outlier row - four orders above the healthy population

f8_max = torch.finfo(torch.float8_e4m3fn).max

scale_t = W.abs().max() / f8_max
Wt = (W / scale_t).to(torch.float8_e4m3fn).to(torch.float32) * scale_t

scale_r = W.abs().amax(dim=1, keepdim=True) / f8_max
Wr = (W / scale_r).to(torch.float8_e4m3fn).to(torch.float32) * scale_r

h = slice(1, None)  # healthy rows: the 99.6% the outlier taxes
W_h, Wt_h, Wr_h = W[h], Wt[h], Wr[h]
rt = (W_h - Wt_h).norm() / W_h.norm()
rr = (W_h - Wr_h).norm() / W_h.norm()
zt = (Wt_h == 0).float().mean()
zr = (Wr_h == 0).float().mean()
print(f"healthy-row relative err  tensorwise: {rt:.3f}  ({zt:.0%} of entries quantized to zero)")
print(f"healthy-row relative err     rowwise: {rr:.3f}  ({zr:.0%} flushed)")
```

On this run: **10.3% relative error and 14% of entries flushed to zero under tensorwise; 2.6% and 0% under rowwise.** The mechanism is visible in the arithmetic: e4m3's smallest normal is `2^-6 ≈ 0.0156`; a healthy entry of `~1e-4` divided by the outlier-inflated scale lands near `0.005` fp8-units - inside the subnormal dead zone, where values round to zero. Rowwise scales give every row its own `amax`, so the outlier's reach ends at its own row. That is why torchao's float8 recipes are named after the scale granularity:

```text
recipe              activation scale   weight scale      notes
"tensorwise"        per-tensor         per-tensor        simplest; fragile to outliers
"rowwise"           per-row            per-row           the workhorse for training
"rowwise_with_gw_hp"  per-row          per-row + gw hp   keeps grad-weight in high precision
```

And the training conversion is one call plus a filter - the module names whose dimensions are not multiples of 16 (the fp8 kernel's tile) or whose precision you want to keep (embeddings, lm_head) are excluded:

```python
import torch
import torch.nn as nn
from torchao.float8 import Float8LinearConfig, convert_to_float8_training

tiny = nn.Sequential(nn.Linear(64, 128), nn.ReLU(), nn.Linear(128, 64))


def module_filter_fn(mod: nn.Module, fqn: str) -> bool:
    if fqn.endswith("1"):  # keep the last Linear (the "lm_head" role) in bf16
        return False
    if isinstance(mod, nn.Linear):
        if mod.in_features % 16 != 0 or mod.out_features % 16 != 0:
            return False
    return True


config = Float8LinearConfig.from_recipe_name("tensorwise")
convert_to_float8_training(tiny, config=config, module_filter_fn=module_filter_fn)
tiny = torch.compile(tiny)  # 3103's compiler makes the recipe competitive
```

Under FSDP2 the composition is `fully_shard` first, float8 conversion after - the `DTensor`-sharded weights and torchao's quantized subclasses cooperate because both are `torch` tensors, not wrapper machinery.

## QAT Without Dead Gradients

[4301](../../phase4-quantization/4300-quantization-aware-training/4301-QAT-Foundations.md) taught quantization-aware training's promise: train *through* the quantizer. Its mechanism has a sharp edge that this fence makes unignorable - `round()` has zero gradient almost everywhere, so a naive fake-quantize silently kills the loss's gradient path:

```python
import torch
import torch.nn as nn

torch.manual_seed(0)
sc = torch.tensor(0.5)

leaf = nn.Parameter(torch.tensor([2.3]))
fake = (leaf / sc).round() * sc
fake.sum().backward()
print(f"plain fake-quant grad: {leaf.grad.item():.4f}  (round()'s autograd grad is 0)")

leaf2 = nn.Parameter(torch.tensor([2.3]))
ste = leaf2 + ((leaf2 / sc).round() * sc - leaf2).detach()
ste.sum().backward()
print(f"STE grad            : {leaf2.grad.item():.4f}  (round treated as identity)")
```

`0.0000` against `1.0000`. The straight-through estimator is one line: pass the rounded value forward but detach the *rounding error*, so backward sees the identity. torchao's QAT workflow packages exactly this behind a config - the modern string-step form replaces the older `prepare`/`convert` quantizer objects:

```python
import torch
from torchao.quantization import (
    Int8DynamicActivationIntxWeightConfig,
    PerGroup,
    quantize_,
)
from torchao.quantization.qat import QATConfig

base = Int8DynamicActivationIntxWeightConfig(
    weight_dtype=torch.int4,
    weight_granularity=PerGroup(32),
)
quantize_(model, QATConfig(base, step="prepare"))  # insert fake-quant (with STE)
# ... train normally here ...
quantize_(model, QATConfig(base, step="convert"))  # bake fake-quant into real kernels
```

## The Trainer Surface: accelerate and transformers

Nobody calls `init_process_group` by hand in a fine-tuning job - `accelerate` builds the process group, the mesh, and FSDP2 from `TrainingArguments`. The config contract is `fsdp_config` with `fsdp_version: 2`, and the trainer *normalizes* what you pass - the fence prints the truth over the docs:

```python
from transformers import TrainingArguments

args = TrainingArguments(
    output_dir="./out",
    fsdp="full_shard",
    fsdp_config={"fsdp_version": 2, "reshard_after_forward": True},
)
print("args.fsdp:", args.fsdp, "(normalized to bool)")
print("args.fsdp_config:", args.fsdp_config)
```

`fsdp: "full_shard"` came back as `True`, and `fsdp_version` was rewritten to `version: 2` with defaults filled in (`min_num_params: 0`, `xla: False`, ...). Under the hood `accelerate`'s `FullyShardedDataParallelPlugin` reads that dict and, for `fsdp_version: 2`, switches to `fully_shard`, takes `reshard_after_forward` as a plain `bool`, accepts `torch.distributed.fsdp.MixedPrecisionPolicy` directly in `mixed_precision_policy`, and ignores `backward_prefetch` (an FSDP1 concept). Launch with `torchrun`, not `python`:

```bash
# one process per GPU; accelerate/transformers read RANK/WORLD_SIZE from the env
torchrun --standalone --nproc-per-node=4 train.py \
    --fsdp full_shard \
    --fsdp_config '{"fsdp_version": 2, "reshard_after_forward": true}'
```

For serving the result, the checkpoint that leaves FSDP2 is a sharded state dict - [1402](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) and [1405](../../phase1-infra/1400-llmops/1405-SGLang.md) are the engines that consolidate and serve it; torchao-quantized weights ride along as plain tensors in the checkpoint.

## Known Failure Modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AttributeError: 'Parameter' object has no attribute 'to_local'` right after forward | under a `MixedPrecisionPolicy`, FSDP2 rebinds `module.weight` to the unsharded bf16 copy during forward; the DTensor returns after backward | read the attribute after `backward()`, or guard on `isinstance(w, DTensor)` |
| `DeviceMesh` warns about "no default device selected" | mesh built before any device is selected; the heuristic guesses `rank % num_devices` | select the device (`torch.cuda.set_device(rank)`) before `init_device_mesh`, or accept the warning on CPU/gloo |
| `RuntimeError: Expected to have finished reduction` / hang at first backward | one rank never entered `init_process_group` (RANK/WORLD_SIZE unset when launched with plain `python`) | launch under `torchrun`; never hand-set `RANK`/`WORLD_SIZE` in real jobs - the fence's `setdefault` is a single-rank teaching device |
| `torch.distributed` refuses gloo on a cluster expecting NCCL | CPU-only or Windows node where NCCL does not exist | `backend="gloo"` for CPU/single-rank smoke tests; NCCL for real GPU jobs |
| fp8-quantized weights degrade catastrophically | one outlier row/channel set a per-tensor scale, pushing healthy values into e4m3's subnormal dead zone | switch the recipe to `"rowwise"`; audit activations with 3103's profiling before trusting tensorwise |
| QAT loss stops decreasing - or blows up on the first step | fake quantization's `round()` has zero autograd gradient; gradients die (or explode without scaling) | use the STE form (`x + (quant(x) - x).detach()`), i.e. torchao's `QATConfig(step="prepare")`, never a hand-rolled `round()` in the loss path |
| `TrainingArguments` rejects `mixed_precision_policy` as a string | FSDP2 takes the `MixedPrecisionPolicy` object; FSDP1 took strings | pass the object under `fsdp_version: 2`, or let the trainer map strings for v1 |
| `reshape`/`view` fails on a sharded weight | `DTensor` local shard shapes differ from the global tensor | call `.full_tensor()` (gather, debugging only) or `.to_local()` (raw shard) before shape-sensitive code |
| Recompilation storm under `torch.compile` after `fully_shard` | per-rank shard shapes changed with world size; guards keyed on the old shapes | compile after sharding, with `dynamic=True` for rank-agnostic graphs - 3103's recompile tax applies per rank |

## Summary

FSDP2 rebuilt fully sharded data parallelism on `DTensor`: parameters stay inspectable, sharding becomes per-parameter and composable, and the whole protocol is visible on a single gloo rank - sharded fp32 master, unsharded bf16 all-gather, re-sharded gradient. torchao rebuilt quantization as tensors: one `quantize_` call with configs serves inference (int4 weights), trains at fp8 (recipes named for their scale granularity - and the outlier fence shows exactly why `rowwise` exists), and runs QAT with the straight-through estimator hidden behind `QATConfig`. The rule this lesson leaves: sharding and quantization are both just bookkeeping about *where precision lives* - FSDP2 moves whole parameters across ranks, torchao moves bits inside them, and neither asks you to leave plain `torch`.

## References

### Related Minder Academy Documents

- [5401: Data Parallelism](./5401-Data-Parallelism.md) - DDP and classic FSDP: the communication patterns FSDP2 reuses
- [5403: Mixed Precision](./5403-Mixed-Precision.md) - bf16/fp16 autocast; `MixedPrecisionPolicy` is its sharded cousin
- [4301: QAT Foundations](../../phase4-quantization/4300-quantization-aware-training/4301-QAT-Foundations.md) - the training-through-quantizer theory torchao operationalizes
- [3103: SDPA and torch.compile](../../phase3-transformers/3100-attention/3103-SDPA-and-torch-compile.md) - the compiler half of the torchtitan recipe
- [1402: vLLM and TGI](../../phase1-infra/1400-llmops/1402-vLLM-and-TGI.md) - serving the consolidated checkpoint
- [1405: SGLang RadixAttention Serving](../../phase1-infra/1400-llmops/1405-SGLang.md) - the serving engine for quantized artifacts

### Primary Sources

- PyTorch docs: [`fully_shard` (FSDP2)](https://docs.pytorch.org/docs/stable/distributed.fsdp.fully_shard.html) - the composable API, `MixedPrecisionPolicy`, `reshard_after_forward` semantics.
- PyTorch docs: [`DTensor`](https://docs.pytorch.org/docs/stable/distributed.tensor.html) - the `Shard(0)` placement model behind per-parameter sharding.
- torchao on PyPI (0.18.x line) and `github.com/pytorch/ao` - `quantize_`, `Float8DynamicActivationFloat8WeightConfig`, `Int4WeightOnlyConfig`, `QATConfig` step form, `convert_to_float8_training` with `from_recipe_name`.
- torchtitan (`github.com/pytorch/torchtitan`) - the reference composition of FSDP2 + torchao float8 + `torch.compile`.

---

## Next Steps

- Next Module: **[5500: Advanced Optimization](../5500-advanced-optimization/README.md)**
- Continue with: **[4302: Fake Quantization](../../phase4-quantization/4300-quantization-aware-training/4302-Fake-Quantization.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**
- Reproduce the outlier fence at your own scale: plant a single outlier row in a real `nn.Linear` weight, quantize tensorwise and rowwise, and plot the relative error against outlier magnitude - find the magnitude where tensorwise tips over.
