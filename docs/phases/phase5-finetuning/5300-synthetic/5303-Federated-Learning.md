---
Document ID: 5303
Title: "5303: Federated Learning"
Phase: 5
Module: 5300
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['federated-learning', 'privacy', 'differential-privacy', 'distributed', 'finetuning']
---

# 5303: Federated Learning

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why Federated Learning](#why-federated-learning)
- [Federated Averaging](#federated-averaging)
- [The Non-IID Reality](#the-non-iid-reality)
- [Privacy: What FedAvg Does Not Give You](#privacy-what-fedavg-does-not-give-you)
- [Federated LLM Fine-Tuning](#federated-llm-fine-tuning)
- [Orchestration with Flower](#orchestration-with-flower)
- [Production Checklist](#production-checklist)
- [Summary](#summary)
- [References](#references)
- [Related Resources](#related-resources)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Trace one FedAvg round end-to-end: selection, local epochs, sample-weighted aggregation
- Diagnose non-IID client drift and name the standard mitigations (FedProx, fewer local steps)
- Explain why a raw gradient update leaks training data (gradient inversion) and which two mechanisms close the gap
- Run DP-SGD with Opacus and distinguish central from local differential privacy
- Size a federated LLM fine-tuning loop around LoRA-adapter exchange instead of full-model shipping

---

## Abstract

Federated learning trains a shared model across many data holders without the data ever leaving them: each participant trains locally, and only model updates travel. The canonical algorithm is FedAvg (McMahan et al., 2017); the two hard problems wrapped around it are statistical heterogeneity (client data is not IID) and privacy (naive updates leak raw training data, so real deployments add differential privacy and secure aggregation). This lesson builds FedAvg from a correct minimal implementation outward, then covers the production stack: the Flower framework, DP-SGD via Opacus, secure aggregation, and the LoRA-adapter pattern that makes federated **LLM** fine-tuning practical.

## Why Federated Learning

The constraint is simple: the data cannot move.

```text
Reasons data stays put
- Regulation: GDPR, HIPAA, KVKK - user data may not leave its
  origin (device, hospital, bank)
- Bandwidth: raw data dwarfs model updates (an hour of audio
  vs a few MB of weights)
- Ownership: partners collaborate but will not pool datasets
- Risk: a central data lake is a single breach target
```

```text
Two settings - everything downstream depends on which one you are in

                 cross-device                  cross-silo
scale        10^4 - 10^9 devices         2 - 100 organizations
reliability  devices offline most of     data centers, high uptime
             the time; high dropout
identity     anonymous, untrusted        known, contractually bound
data         tiny per device, NON-IID    large per silo, still non-IID
examples     phone keyboards, wearables  hospitals, banks, telecoms
framework    FedAvg + heavy dropout      FedAvg + DP (contracts help)
tolerance
```

## Federated Averaging

### The Algorithm

```text
One round of FedAvg (McMahan et al., 2017)

server:   select fraction C of available clients
          broadcast current global weights w_t to the selected
client k: load w_t
          run E local epochs of SGD on its OWN data
          send back weights w_k and its sample count n_k
server:   aggregate   w_{t+1} = sum_k (n_k / N) * w_k
          (N = total samples across participants)

Roles are swapped vs 5401/5402: there, ONE dataset was sharded
across replicas of identical hardware. Here, the data never
centralizes and the hardware is wildly heterogeneous.
```

The aggregation is a sample-weighted average — clients with more data move the global model more. Note the communication economics: what dominates wall-clock time is the **round trip**, not the compute, which is why the standard knobs are `E` (local epochs) and `C` (participation fraction).

### A Correct Minimal Implementation

```python
import torch

def fedavg(global_model: torch.nn.Module,
           updates: list[dict]) -> None:
    """updates: [{"state_dict": sd, "num_samples": n}, ...]

    Weighted average of floating tensors; integer buffers
    (e.g. BatchNorm num_batches_tracked) are carried as-is -
    averaging them silently converts them to float.
    """
    total = sum(u["num_samples"] for u in updates)
    averaged = {}
    for key, first in updates[0]["state_dict"].items():
        if first.dtype.is_floating_point:
            averaged[key] = sum(
                u["state_dict"][key] * (u["num_samples"] / total)
                for u in updates
            )
        else:
            averaged[key] = first.clone()
    global_model.load_state_dict(averaged)
```

```text
Footguns this 15-line function encodes
1. weight by n_k, NOT by 1/len(updates) - unweighted FedAvg
   lets one giant client dominate or dilute, depending on sign
2. never average integer buffers - see the comment above
3. updates must all come from the SAME architecture at the SAME
   global round; a straggler returning weights from round t-1
   corrupts the average (version-tag every exchange)
```

## The Non-IID Reality

The founding assumption of SGD — batches drawn from one distribution — does not hold. A keyboard model trained on one user's typing drifts toward that user; averaging drifted models converges slower and oscillates.

```text
Why naive FedAvg degrades under non-IID data

client k runs E epochs on ONLY its own distribution
  -> its weights move toward the local optimum (client drift)
  -> the global average bounces between local optima
  -> more local epochs E = MORE drift, not faster progress
     (E is a dial between "IID-fast" and "heterogeneous-stuck")
```

```text
Mitigations, in the order you should try them

1. FedProx (Li et al., 2020)   add a proximal term to the local
   objective: loss + (mu/2) * ||w - w_global||^2   - penalizes
   drifting far from the global weights. mu ~ 0.01-0.1; one-line
   change in the local loss
2. Fewer local epochs          E=1 with more rounds often beats
   E=5 with fewer, at equal communication
3. SCAFFOLD (Karimireddy et    control variates correct the
   al., 2020)                  drift explicitly; strong but doubles
                               state kept per client
4. Server momentum / FedAvgM   average THEN apply momentum server-
                               side; cheap and often effective
```

There is also a **systems** axis: devices drop out mid-round. Production rounds are deadline-based — the server aggregates whatever returns in time, and the sample-weighting does the rest. Design every metric (accuracy, epsilon, convergence) to tolerate 10-30% dropout.

## Privacy: What FedAvg Does Not Give You

Federated learning hides the raw data but **not** the gradients. This is the most common misconception in the field, so it gets its own section.

### Gradient Inversion

```text
Zhu et al., "Deep Leakage from Gradients" (NeurIPS 2019)

Given one client's gradient update + the model architecture,
an attacker OPTIMIZES a dummy input until its gradient matches
the received one. Result: reconstructed training examples that
are visually recognizable - faces, tokens, documents.

Batch size 1 = near-perfect reconstruction. Larger batches and
more rounds of accumulation blur it, but leakage persists.
Plain FedAvg is therefore a bandwidth optimization, NOT a
privacy mechanism.
```

Two mechanisms close the gap, and real deployments use **both**:

### Differential Privacy: DP-SGD Done Right

DP-SGD (Abadi et al., 2016) makes one client's contribution provably bounded:

```text
The correct algorithm - three steps, each load-bearing

1. PER-SAMPLE gradients: compute g_i for every example i in the
   batch separately (not the batch mean)
2. Clip EACH g_i to L2 norm C -> bounds any individual's influence
   (the sensitivity of the sum is now exactly C)
3. Noise the SUM: add N(0, sigma^2 * C^2 * I), divide by B

Privacy budget: (epsilon, delta) is accumulated over ALL rounds
by a moments accountant. epsilon is a spent budget, like a
quota - every round costs some.
```

```text
Common WRONG implementation (seen in many blog posts and naive
drafts): clip the BATCH-MEAN gradient with clip_grad_norm_,
then add ad-hoc noise per tensor.

Why it fails
- clipping the batch mean bounds nothing about any individual
  example, so there is no sensitivity bound to calibrate against
- "sigma = sensitivity / epsilon" is not a DP mechanism; the
  Gaussian mechanism needs sigma from the accountant, not from
  epsilon directly
- without an accountant, epsilon is untracked fiction
```

With Opacus, the correct version is a three-line retrofit:

```python
import torch
from opacus import PrivacyEngine

model = build_model()
optimizer = torch.optim.SGD(model.parameters(), lr=0.05)
train_loader = ...  # ordinary DataLoader

privacy_engine = PrivacyEngine()
model, optimizer, train_loader = privacy_engine.make_private_with_epsilon(
    module=model,
    optimizer=optimizer,
    data_loader=train_loader,
    epochs=E,
    target_epsilon=8.0,     # total budget across all epochs
    target_delta=1e-5,
    max_grad_norm=1.0,      # C: per-sample clip bound
)

# training loop is UNCHANGED - Opacus swaps in per-sample grads,
# clipping, and noise under the hood
for x, y in train_loader:
    optimizer.zero_grad()
    torch.nn.functional.cross_entropy(model(x), y).backward()
    optimizer.step()

privacy_engine.get_epsilon(delta=1e-5)   # budget actually spent
```

### Central vs Local DP, and Secure Aggregation

```text
Where the noise is added decides the trust model

LOCAL DP   client noises its OWN update before sending
           - no trust in the server needed at all
           - utility cost is severe for small per-device batches

CENTRAL DP updates sent raw (under encryption), the server adds
           calibrated noise to the AGGREGATE only
           - far better utility
           - requires the server to never see a raw individual
             update -> only works combined with...

SECURE AGGREGATION (Bonawitz et al., 2017)
           clients exchange pairwise masks that CANCEL in the sum
           server learns sum_k (masked_w_k) = sum_k w_k + noise,
           and nothing about any single w_k
           - dropout-tolerant via secret sharing of the masks

Production recipe for cross-device: SecAgg + central DP.
Cross-silo with contracts: SecAgg still recommended; DP budget
agreed per data-use agreement.
```

PII handling before training even starts is a separate, complementary layer — see [7502: PII Redaction](../../phase7-agentic/7500-security/7502-PII-Redaction.md).

## Federated LLM Fine-Tuning

Shipping a 7B model's full weights to every round-trip client is not an option. The parameter-efficient pattern makes it one:

```text
FedLoRA round structure

server  -> clients   frozen base model id + current LoRA adapters
                     (a rank-16 adapter on a 7B model: ~20-40 MB,
                     vs ~14 GB for full weights)
clients -> local     load base (optionally 4-bit, lesson 5102),
                     fine-tune ONLY adapter params on local data
clients -> server    adapters + sample counts, never the base
server  -> aggregate sample-weighted average OF THE ADAPTERS
                     (they live at the same addresses in every
                     client - averaging is well-defined)

+ 100x less communication per client per round
+ base model stays centrally versioned; updates are tiny deltas
- heterogeneous client hardware: quantize the base for low-RAM
  devices, keep adapter dtype identical everywhere or the average
  breaks
```

```text
Honest state of the field
- cross-silo FedLoRA: works, used (healthcare, finance consortia)
- cross-device LLM personalization: active research; adapter drift
  under non-IID user data is the open problem - apply the non-IID
  mitigations above to the ADAPTER weights
- DP noise on adapters behaves like DP on any small parameter
  group; budgets are typically more forgiving than full-model DP
```

## Orchestration with Flower

Hand-rolled servers are fine for learning and wrong for production. [Flower](https://flower.ai) (`uv pip install flwr`) is the de-facto framework: it owns selection, dropout handling, serialization, and strategy plugins. The client is a thin subclass:

```python
import flwr as fl
import torch

class FlowerClient(fl.client.NumPyClient):
    def __init__(self, net, train_loader, epochs):
        self.net = net
        self.train_loader = train_loader
        self.epochs = epochs

    def get_parameters(self, config):
        return [v.cpu().numpy() for v in self.net.state_dict().values()]

    def set_parameters(self, parameters):
        params_dict = zip(self.net.state_dict().keys(), parameters)
        state = {k: torch.tensor(v) for k, v in params_dict}
        self.net.load_state_dict(state)

    def fit(self, parameters, config):
        self.set_parameters(parameters)          # load global weights
        train(self.net, self.train_loader, epochs=self.epochs)
        return self.get_parameters(config={}), len(self.train_loader.dataset), {}

    def evaluate(self, parameters, config):
        self.set_parameters(parameters)
        loss, accuracy = test(self.net, self.val_loader)
        return loss, len(self.val_loader.dataset), {"accuracy": accuracy}
```

The server side is a strategy object — FedAvg with its knobs:

```python
strategy = fl.server.strategy.FedAvg(
    fraction_fit=0.3,          # C: 30% of available clients per round
    min_fit_clients=30,
    min_available_clients=100, # wait until this many are online
    fraction_evaluate=0.1,
)
# run via `flwr run` with a ServerApp(config=ServerConfig(num_rounds=100),
# strategy=strategy) - `flwr new` scaffolds the full app layout
```

```text
What the framework buys you over a hand-rolled loop
- client dropouts handled mid-round (weights and masks restored)
- strategy abstraction: swap FedAvg -> FedProx/QFedAvg by config
- simulation mode: run 1000 virtual clients on one GPU for
  experiments before any real deployment
- serialization + versioning of every exchange
```

## Production Checklist

```text
Design
- decide cross-device vs cross-silo FIRST - it changes every choice below
- non-IID audit: per-client data volume and label distribution,
  before the first round; stratify client selection on it
- pick E as small as convergence allows (start E=1) and C by the
  dropout profile, not by optimism

Privacy
- budget epsilon over the WHOLE training lifetime, then divide
  across rounds; re-training burns it again
- SecAgg everywhere; DP noise scale chosen by the accountant,
  never hand-set
- threat-model the server explicitly (honest-but-curious? colluding?)

Operations
- version-tag every broadcast; reject stale updates at the server
- monitor per-round: participation rate, returned-sample skew,
  delta-norm between global weights (drift alarm)
- federated evaluation has no central test set: mix per-client
  held-out metrics with a small fixed server-side probe set
- rollback = broadcast an older version tag; the update path is
  already there, use it
```

---

## Summary

Federated learning trains a shared model across many data holders without the data ever leaving them: participants train locally, only model updates travel, and FedAvg averages the rounds. This lesson faced the two hard problems head-on - statistical heterogeneity, where non-IID client data bends the average, and the privacy illusion, since FedAvg alone leaks and DP noise plus secure aggregation are separate layers. It then covered federated LLM fine-tuning, Flower orchestration, and the production checklist. The rule it leaves: federation is an architecture decision about data residency first and an ML decision second.

## References

### Related Minder Academy Documents

- [5301: Knowledge Distillation](5301-Knowledge-Distillation.md)
- [5302: Distributed Training Orchestration](5302-Distributed-Training.md)
- [5102: QLoRA Pipelines](../5100-peft/5102-QLoRA-Pipelines.md)

---

## Next Steps

- Continue with: **[5401: Data Parallelism](../5400-distributed-training/5401-Data-Parallelism.md)**
- Assessment: **[assessment/QUIZ.md](./assessment/QUIZ.md)**

---

## Related Resources

- **Related:** [7502: PII Redaction](../../phase7-agentic/7500-security/7502-PII-Redaction.md)
- **Experiment:** [EXP_5303: Federated Learning](../../../../experiments/EXP_5303_FEDERATED_LEARNING.md)
