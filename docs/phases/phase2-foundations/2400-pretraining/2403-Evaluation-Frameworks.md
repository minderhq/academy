---
Document ID: 2403
Title: Evaluation Frameworks for Language Models
Phase: 2
Module: 2400
Last Updated: 2026-09-26
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['training', 'pretraining', 'evaluation', 'benchmarks']
---

# 2403: Evaluation Frameworks for Language Models

---

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Part 1: Perplexity & Language Modeling Metrics](#part-1-perplexity--language-modeling-metrics)
- [Part 2: Standard Benchmarks](#part-2-standard-benchmarks)
- [Part 3: Human Preference Metrics](#part-3-human-preference-metrics)
- [Part 4: Automated Evaluation Pipeline](#part-4-automated-evaluation-pipeline)
- [Part 5: Evaluation Best Practices](#part-5-evaluation-best-practices)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After completing this lesson, you will be able to:

- Define perplexity as `exp(mean cross-entropy)` and measure it on a real language model before and after training
- Convert freely between loss, perplexity, and bits-per-character (BPC)
- Rank multiple-choice answers by likelihood — the scoring mechanism behind MMLU-style benchmarks
- Explain why length-normalized scoring (`acc_norm`) corrects the raw log-likelihood bias toward short endings on HellaSwag-style tasks
- Grade exact-match benchmarks like GSM8K with robust answer extraction and tolerance
- Compute pass@k for code generation and execute candidate solutions in an isolated sandbox
- Score TruthfulQA with the MC2 metric and model pairwise preferences with the Bradley-Terry model
- Build an automated evaluation pipeline with JSON + report outputs and judge whether score differences are statistically significant

## Abstract

Evaluation is the measurement discipline of language-model work: every training decision — data mix, hyperparameters, alignment recipe — is ultimately justified by numbers produced by an evaluation harness. A number without a protocol, however, is not a measurement. This lesson builds the core mechanisms of LLM evaluation as small, runnable programs: perplexity and BPC for language modeling, likelihood-ranked multiple choice for knowledge benchmarks, length-normalized scoring for commonsense completion, exact-match grading for math, sandboxed test execution plus pass@k for code, MC2 for truthfulness, Bradley-Terry for pairwise preference, and bootstrap confidence intervals with McNemar's test for comparing two models.

Every code block runs offline on toy models with fixed seeds, and every output shown is a measured run — the same discipline a real evaluation harness applies, scaled down to something you can inspect end to end.

**What you'll learn:**

- The metric family that all benchmark scores reduce to: cross-entropy, perplexity, BPC
- How each major benchmark family actually scores a model (not just what its leaderboard number means)
- Where naive scoring goes wrong: short-answer bias, unparsable outputs, metric gaming
- How to wire benchmarks into a reproducible pipeline that emits JSON and reports
- How to tell a real improvement from noise with confidence intervals and paired tests

## Part 1: Perplexity & Language Modeling Metrics

### Understanding Perplexity

Perplexity is the geometric-mean branching factor of a language model: on average, how many tokens is the model effectively choosing between at each step? It is defined from the mean cross-entropy loss over next-token predictions:

```text
PPL = exp( (1/N) * sum_i -log P(token_i | context_i) )
```

A model that guesses uniformly over a vocabulary of V tokens lands at PPL = V. A model that predicts every next token with certainty reaches PPL = 1. This makes perplexity directly interpretable — and directly checkable. The block below builds a tiny bigram language model (one logits row per previous-token identity, behind an `outputs.logits`-style interface), measures perplexity at random initialization, trains it on a deterministic synthetic corpus, and measures again. The corpus generator `t_{i+1} = (7*t_i + 3) % 30` is a bijection over the 30-token vocabulary, so a perfect bigram model can in principle reach PPL 1 — the measurement verifies how close training gets.

```python
"""Perplexity: the fundamental language-modeling metric.

PPL = exp(mean cross-entropy per next-token prediction).
A random model over a vocab of V tokens lands near PPL = V;
a model that predicts every next token exactly reaches PPL = 1.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

VOCAB = 30


class LMOutput:
    """Minimal stand-in for HF's `outputs.logits` interface."""

    def __init__(self, logits):
        self.logits = logits


class BigramLM(nn.Module):
    """Next-token model: one logits row per previous-token identity."""

    def __init__(self, vocab_size):
        super().__init__()
        self.logit_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, input_ids):
        return LMOutput(self.logit_table(input_ids))


def make_corpus(n_tokens, seed):
    """Deterministic synthetic language: t_{i+1} = (7*t_i + 3) % VOCAB.
    The map is a bijection, so a perfect bigram model can reach PPL 1."""
    g = torch.Generator().manual_seed(seed)
    seq = [int(torch.randint(0, VOCAB, (1,), generator=g))]
    for _ in range(n_tokens - 1):
        seq.append((7 * seq[-1] + 3) % VOCAB)
    return torch.tensor(seq)


def calculate_perplexity(model, tokens, device="cpu"):
    """PPL = exp(sum CE over next-token predictions / token count)."""
    model.eval()
    tokens = tokens.to(device)
    with torch.no_grad():
        logits = model(tokens).logits
    shift_logits = logits[:-1, :].contiguous()
    shift_labels = tokens[1:].contiguous()
    losses = F.cross_entropy(shift_logits, shift_labels, reduction="none")
    avg_loss = losses.mean().item()
    return {
        "loss": avg_loss,
        "perplexity": math.exp(avg_loss),
        "tokens": int(shift_labels.numel()),
    }


def train(model, tokens, steps=500, lr=0.1):
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    for _ in range(steps):
        loss = F.cross_entropy(model(tokens).logits[:-1], tokens[1:])
        opt.zero_grad()
        loss.backward()
        opt.step()


torch.manual_seed(0)
corpus = make_corpus(2000, seed=0)
model = BigramLM(VOCAB)

before = calculate_perplexity(model, corpus)
train(model, corpus)
after = calculate_perplexity(model, corpus)

print("vocab size:", VOCAB)
print("tokens evaluated:", after["tokens"])
print(f"random init:   avg loss {before['loss']:.4f} -> PPL {before['perplexity']:.2f}")
print(f"after training: avg loss {after['loss']:.4f} -> PPL {after['perplexity']:.2f}")
print(f"reading: the random model spreads mass over ~{before['perplexity']:.0f} "
      f"candidates per step; training concentrates it to ~{after['perplexity']:.2f}")
```

**Output:**

```text
vocab size: 30
tokens evaluated: 1999
random init:   avg loss 3.9223 -> PPL 50.52
after training: avg loss 0.0022 -> PPL 1.00
reading: the random model spreads mass over ~51 candidates per step; training concentrates it to ~1.00
```

Two things to notice. First, the random-init perplexity (50.52) is *higher* than the vocabulary size (30): the random logits have nonzero variance, and `exp(mean CE)` punishes confidently wrong predictions more than uniform guessing. Second, the shift by one position (`logits[:-1]` vs `tokens[1:]`) is where most perplexity bugs live — forgetting the shift compares each token's prediction against itself and produces optimistic garbage. Every published perplexity number is this same computation at a larger scale; if you can reproduce it here, you can audit it anywhere.

### Bits Per Character (BPC)

Perplexity has one practical flaw: it depends on the tokenizer. A model with 32k subword tokens and one with 100k tokens produce perplexities that cannot be compared directly. Bits per character (BPC) fixes this by restating the same measurement in base 2 per character, making results comparable across tokenizers and with character-level models:

```text
BPC = log2(PPL) = avg_loss / ln(2)
```

Both identities are exact — BPC is not an approximation but a unit change:

```python
"""Bits Per Character: BPC = log2(PPL) = avg_loss / ln(2).

BPC is a base-2 restatement of the same measurement, which makes
results comparable across tokenizers and with character-level models.
"""

import math
import torch
import torch.nn as nn
import torch.nn.functional as F

VOCAB = 30


class LMOutput:
    def __init__(self, logits):
        self.logits = logits


class BigramLM(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.logit_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, input_ids):
        return LMOutput(self.logit_table(input_ids))


def make_corpus(n_tokens, seed):
    g = torch.Generator().manual_seed(seed)
    seq = [int(torch.randint(0, VOCAB, (1,), generator=g))]
    for _ in range(n_tokens - 1):
        seq.append((7 * seq[-1] + 3) % VOCAB)
    return torch.tensor(seq)


def avg_loss_of(model, tokens):
    with torch.no_grad():
        logits = model(tokens).logits
    loss = F.cross_entropy(logits[:-1], tokens[1:], reduction="mean")
    return loss.item()


torch.manual_seed(0)
corpus = make_corpus(2000, seed=0)
model = BigramLM(VOCAB)
loss_random = avg_loss_of(model, corpus)
opt = torch.optim.Adam(model.parameters(), lr=0.1)
for _ in range(500):
    loss = F.cross_entropy(model(corpus).logits[:-1], corpus[1:])
    opt.zero_grad()
    loss.backward()
    opt.step()
loss_trained = avg_loss_of(model, corpus)

rows = [("random init", loss_random), ("after training", loss_trained)]
print(f"{'model':<16} {'loss (nats)':>12} {'PPL':>8} {'BPC':>8}")
for name, loss in rows:
    ppl = math.exp(loss)
    bpc = math.log2(ppl)
    print(f"{name:<16} {loss:>12.4f} {ppl:>8.2f} {bpc:>8.4f}")

# both identities must agree
bpc_direct = loss_trained / math.log(2)
assert abs(bpc_direct - math.log2(math.exp(loss_trained))) < 1e-12
print("identity check: loss/ln(2) == log2(PPL) -> True")
```

**Output:**

```text
model             loss (nats)      PPL      BPC
random init            3.9223    50.52   5.6587
after training         0.0022     1.00   0.0032
identity check: loss/ln(2) == log2(PPL) -> True
```

The table is one measurement in three units. When a paper reports 0.8 BPC on enwik8 and another reports perplexity 18 on WikiText-103, neither number is "better" — they are different corpora, different tokenizers, different units. The conversion above is the only honest bridge, and it only works within one corpus.

## Part 2: Standard Benchmarks

Language-modeling perplexity says a model fits its training distribution. Benchmarks ask a different question: does the model know things it was not explicitly measured on? This part implements the scoring machinery of four benchmark families — multiple-choice knowledge (MMLU), commonsense completion (HellaSwag), math word problems (GSM8K), and code generation (HumanEval) — on toy models, so every scoring rule is visible.

### MMLU (Massive Multitask Language Understanding)

MMLU covers 57 subjects from high-school history to professional law. Its harness does something surprisingly simple: it formats each question together with each answer choice into a prompt, scores the log-likelihood of every choice, and picks the highest. No generation, no parsing — just likelihood ranking.

The toy below implements exactly that mechanism. A bigram model is trained on a mini "knowledge corpus" of country-capital pairs, then answers four multiple-choice questions by comparing the log-probability of each candidate answer. Note the honest limitation built into the demo: the toy model "knows" its four capitals only because they appear in its corpus. Distractor cities (london, cairo, ...) have embedding rows but were never trained — they score far below the trained answers. A real LLM passes MMLU because its pretraining corpus contained the knowledge; the scoring mechanism is identical.

```python
"""MMLU-style multiple choice by likelihood ranking.

The real harness formats each question into a prompt per choice and
picks the choice the model assigns the highest likelihood. This toy
does exactly that with a tiny bigram LM trained on a mini
'knowledge corpus' (country -> capital pairs).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)

FACTS = [
    ("france", "paris"), ("japan", "tokyo"),
    ("italy", "rome"), ("spain", "madrid"),
]
# distractors share the vocab (they need embedding rows) but are NEVER
# trained: their rows stay at random init
DISTRACTORS = ["london", "berlin", "oslo", "cairo", "delhi", "vienna",
               "bangkok"]
WORDS = sorted({w for pair in FACTS for w in pair} | set(DISTRACTORS))
stoi = {w: i for i, w in enumerate(WORDS)}
VOCAB = len(WORDS)


class BigramLM(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.logit_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, input_ids):
        return self.logit_table(input_ids)


corpus_pairs = torch.tensor(
    [[stoi[a], stoi[b]] for a, b in FACTS for _ in range(50)])
model = BigramLM(VOCAB)
opt = torch.optim.Adam(model.parameters(), lr=0.1)
for _ in range(300):
    loss = F.cross_entropy(model(corpus_pairs[:, 0]), corpus_pairs[:, 1])
    opt.zero_grad()
    loss.backward()
    opt.step()


def choice_logprob(model, context_word, choice_word):
    """Mean log P over the choice tokens given the context."""
    with torch.no_grad():
        prev = torch.tensor([stoi[context_word]])
        logits = model(prev)[0]
        log_probs = F.log_softmax(logits, dim=-1)
    return log_probs[stoi[choice_word]].item()


QUESTIONS = [
    ("france", ["paris", "london", "berlin", "oslo"], 0),
    ("japan", ["cairo", "tokyo", "delhi", "vienna"], 1),
    ("italy", ["london", "rome", "oslo", "bangkok"], 1),
    ("spain", ["cairo", "berlin", "madrid", "delhi"], 2),
]

correct = 0
for ctx, choices, gold in QUESTIONS:
    scores = [choice_logprob(model, ctx, c) for c in choices]
    pred = max(range(len(choices)), key=lambda i: scores[i])
    correct += pred == gold
    score_line = ", ".join(f"{c}: {s:.3f}" for c, s in zip(choices, scores))
    mark = "correct" if pred == gold else "WRONG"
    print(f"{ctx:>6} -> pred {choices[pred]:<7} ({mark}) | {score_line}")

acc = correct / len(QUESTIONS)
print(f"accuracy: {correct}/{len(QUESTIONS)} = {acc:.2f}")
print("random-guess baseline on 4 choices: 0.25")
```

**Output:**

```text
france -> pred paris   (correct) | paris: -0.005, london: -7.547, berlin: -10.071, oslo: -6.270
 japan -> pred tokyo   (correct) | cairo: -9.446, tokyo: -0.004, delhi: -9.358, vienna: -8.154
 italy -> pred rome    (correct) | london: -9.826, rome: -0.003, oslo: -8.146, bangkok: -9.488
 spain -> pred madrid  (correct) | cairo: -7.186, berlin: -8.628, madrid: -0.004, delhi: -7.978
accuracy: 4/4 = 1.00
random-guess baseline on 4 choices: 0.25
```

The per-choice log-probabilities are the interesting part: the trained answers sit near 0 (probability near 1) while the untrained distractors fall between -6 and -10. The gap between a correct model and a random-guess baseline (0.25 here) is exactly what MMLU accuracy measures at scale — with the caveat that a model can score well by memorizing benchmark text, which is why contamination checking matters for any serious evaluation.

### HellaSwag (Common Sense Reasoning)

HellaSwag asks a model to finish a sentence: given a context, pick the most plausible ending from four candidates. The dataset was built with adversarial filtering so the wrong endings fool models but not humans (over 95% human accuracy, under 48% for the models of 2019).

Its headline metric `acc_norm` exists because of a subtle scoring trap. The raw score — the *sum* of token log-probabilities — systematically favors short endings: fewer tokens means fewer negative terms added together. The fix is to normalize by length. The block below demonstrates the trap on three toy items, scoring each ending both ways:

```python
"""HellaSwag-style ending selection: raw vs length-normalized scoring.

raw  = sum of token log-probs   (favors SHORT endings)
norm = sum / number of tokens   (fair length comparison, the
                                 official 'acc_norm' idea)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

torch.manual_seed(0)

SENTENCES = [
    ["the", "chef", "cooks", "fresh", "pasta"],
    ["the", "chef", "cooks", "fresh", "pasta"],
    ["the", "chef", "cooks", "pasta"],
    ["the", "chef", "bakes", "warm", "bread"],
    ["the", "driver", "stops", "the", "bus"],
    ["the", "driver", "opens", "the", "door"],
]
# distractor words get embedding rows but are never trained
DISTRACTOR_WORDS = ["explodes", "into", "flames", "wildly", "juggles",
                    "knives"]
WORDS = sorted({w for s in SENTENCES for w in s} | set(DISTRACTOR_WORDS))
stoi = {w: i for i, w in enumerate(WORDS)}
VOCAB = len(WORDS)


class BigramLM(nn.Module):
    def __init__(self, vocab_size):
        super().__init__()
        self.logit_table = nn.Embedding(vocab_size, vocab_size)

    def forward(self, input_ids):
        return self.logit_table(input_ids)


pairs = []
for s in SENTENCES:
    for i in range(len(s) - 1):
        pairs.append([stoi[s[i]], stoi[s[i + 1]]])
corpus = torch.tensor(pairs)
model = BigramLM(VOCAB)
opt = torch.optim.Adam(model.parameters(), lr=0.1)
for _ in range(400):
    loss = F.cross_entropy(model(corpus[:, 0]), corpus[:, 1])
    opt.zero_grad()
    loss.backward()
    opt.step()


def score_continuation(model, context_words, ending_words):
    """Sum log P over the ending, conditioned on the context words."""
    seq = context_words + ending_words
    total = 0.0
    with torch.no_grad():
        for prev, cur in zip(seq[:-1], seq[1:]):
            logits = model(torch.tensor([stoi[prev]]))[0]
            total += F.log_softmax(logits, dim=-1)[stoi[cur]].item()
    return total


ITEMS = [
    {
        "context": "the chef",
        "endings": [("cooks", False), ("cooks fresh pasta", True)],
    },
    {
        "context": "the driver",
        "endings": [("stops the bus", True),
                    ("explodes into flames wildly", False)],
    },
    {
        "context": "the chef",
        "endings": [("cooks pasta", True), ("juggles knives", False)],
    },
]

raw_correct = norm_correct = 0
for item in ITEMS:
    ctx_words = item["context"].split()
    gold_text = [t for t, g in item["endings"] if g][0]
    scored = []
    print(f"context: {item['context']}")
    for text, is_gold in item["endings"]:
        ending_words = text.split()
        total = score_continuation(model, ctx_words, ending_words)
        norm = total / len(ending_words)
        kind = "gold" if is_gold else "distractor"
        scored.append((total, norm, text))
        print(f"  [{kind}] '{text}': raw {total:.3f}, norm {norm:.3f}")
    raw_pick = max(scored, key=lambda s: s[0])[2]
    norm_pick = max(scored, key=lambda s: s[1])[2]
    raw_correct += raw_pick == gold_text
    norm_correct += norm_pick == gold_text
    print(f"  raw picks '{raw_pick}', norm picks '{norm_pick}', "
          f"gold '{gold_text}'")

n = len(ITEMS)
print(f"raw accuracy:  {raw_correct}/{n} = {raw_correct / n:.2f}")
print(f"norm accuracy: {norm_correct}/{n} = {norm_correct / n:.2f}")
```

**Output:**

```text
context: the chef
  [distractor] 'cooks': raw -0.986, norm -0.986
  [gold] 'cooks fresh pasta': raw -1.398, norm -0.466
  raw picks 'cooks', norm picks 'cooks fresh pasta', gold 'cooks fresh pasta'
context: the driver
  [gold] 'stops the bus': raw -4.168, norm -1.389
  [distractor] 'explodes into flames wildly': raw -21.102, norm -5.275
  raw picks 'stops the bus', norm picks 'stops the bus', gold 'stops the bus'
context: the chef
  [gold] 'cooks pasta': raw -2.088, norm -1.044
  [distractor] 'juggles knives': raw -15.519, norm -7.759
  raw picks 'cooks pasta', norm picks 'cooks pasta', gold 'cooks pasta'
raw accuracy:  2/3 = 0.67
norm accuracy: 3/3 = 1.00
```

Item 1 is the lesson: both endings begin with "cooks", but the single-token ending wins on raw score simply by being short (-0.986 vs -1.398), while per-token it is clearly worse (-0.986 vs -0.466). Length normalization inverts the decision. This is not a toy artifact — the official HellaSwag numbers report both `acc` and `acc_norm` precisely because raw scoring underestimates models whose completions are longer than the distractors. (Normalization is not a panacea: per-token means can be gamed in the opposite direction by long, low-information endings, which is why HellaSwag pairs the metric with adversarially filtered distractors.)

### GSM8K (Mathematical Reasoning)

GSM8K contains 8.5K grade-school math word problems. Each gold solution ends with `#### <number>`, and grading is exact-match on that final number with a small numeric tolerance. The grading function is where most of the engineering lives: models emit numbers with commas ("1,200"), with units, or not at all — and a grader that crashes on those cases silently inflates or deflates the score.

```python
"""GSM8K grading: extract the final number, compare with tolerance.

Gold answers end with '#### <number>'. Predictions are graded by
numeric equality within a small tolerance (comma-formatted numbers
are normalized first).
"""

import re


def extract_final_number(text):
    """Return the number after '####', else the last number in the text."""
    match = re.search(r"####\s*([-+]?[\d,]*\.?\d+)", text)
    if match:
        text = match.group(1)
    else:
        numbers = re.findall(r"[-+]?[\d,]*\.?\d+", text)
        if not numbers:
            return None
        text = numbers[-1]
    try:
        return float(text.replace(",", ""))
    except ValueError:
        return None


def grade(prediction_text, gold_text, tol=1e-4):
    pred = extract_final_number(prediction_text)
    gold = extract_final_number(gold_text)
    if pred is None or gold is None:
        return False
    return abs(pred - gold) < tol


GOLD = [
    "Natalia sold 48/2 = 24 clips in May. Total 48 + 24 = 72. #### 72",
    "Weng earns 12/60 = 0.2 per minute. 5 x 60 x 0.2 = 60. #### 60",
    "A robe takes 2 bolts of blue fiber and half that much silk. #### 3",
    "x = 5 - 3 = 2. #### 2",
]
PREDICTIONS = [
    "She sold 24 in May, so 48 + 24 = 72 clips. #### 72",
    "Weng earns 60 dollars. #### 1,200",
    "2 + 1 = 3. #### 3",
    "I could not solve this problem.",
]

n_correct = 0
for gold, pred in zip(GOLD, PREDICTIONS):
    ok = grade(pred, gold)
    n_correct += ok
    gold_n = extract_final_number(gold)
    pred_n = extract_final_number(pred)
    print(f"gold {gold_n:>8} | pred {str(pred_n):>8} | "
          f"{'PASS' if ok else 'FAIL'}")

print(f"accuracy: {n_correct}/{len(GOLD)} = {n_correct / len(GOLD):.2f}")
```

**Output:**

```text
gold     72.0 | pred     72.0 | PASS
gold     60.0 | pred   1200.0 | FAIL
gold      3.0 | pred      3.0 | PASS
gold      2.0 | pred     None | FAIL
accuracy: 2/4 = 0.50
```

The second row is the comma trap: "1,200" must parse to 1200 (the extraction normalizes it, and the comparison correctly fails against gold 60). The fourth row is the crash trap: a prediction with no number at all must yield a clean FAIL, not a `TypeError` — an extraction function that returns `None` and a grader that handles `None` is the difference between a robust benchmark score and one that silently drops hard problems.

### HumanEval (Python Code Generation)

HumanEval has 164 hand-written Python problems, each with a function signature, a docstring, and hidden unit tests. A candidate solution counts as correct only if the tests pass when actually executed — functional correctness, not textual similarity. Because sampling is stochastic, the headline metric is pass@k: the probability that at least one of k samples per problem passes. The unbiased estimator from the Codex paper,

```text
pass@k = 1 - C(n-c, k) / C(n, k)
```

(where n samples were drawn and c of them pass), avoids huge binomial coefficients through its product form. Execution itself must be sandboxed: generated code is untrusted, so it runs in an isolated namespace with stdout captured.

```python
"""HumanEval: sandboxed test execution + the pass@k estimator.

pass@k from the Codex paper (unbiased estimator):
  pass@k = 1 - C(n-c, k) / C(n, k)
with n samples, c of them passing. The product form avoids huge
binomials: 1 - prod_{i=0}^{k-1} (n-c-i) / (n-i).
"""

import math
from contextlib import redirect_stdout
from io import StringIO


def pass_at_k(n, c, k):
    if n - c < k:
        return 1.0
    num = 1.0
    for i in range(k):
        num *= (n - c - i) / (n - i)
    return 1.0 - num


print("pass@k table (n = 20 samples, c = 5 pass):")
for k in (1, 2, 5, 10):
    print(f"  k = {k:>2}: pass@k = {pass_at_k(20, 5, k):.4f}")


def run_tests(generated_code, test_code):
    """Execute candidate + tests in an isolated namespace with stdout
    captured. Returns True only if nothing raises."""
    full_code = generated_code + "\n" + test_code
    buffer = StringIO()
    try:
        with redirect_stdout(buffer):
            exec(compile(full_code, "<candidate>", "exec"),
                 {"__name__": "candidate"})
        return True
    except Exception:
        return False


GOOD_SOLUTION = "def add(a, b):\n    return a + b"
BAD_SOLUTION = "def add(a, b):\n    return a - b"
TESTS = "assert add(2, 3) == 5\nassert add(-1, 1) == 0\nprint('tests ran')"

solutions = [("good", GOOD_SOLUTION), ("bad", BAD_SOLUTION)]
passed = 0
for name, code in solutions:
    ok = run_tests(code, TESTS)
    passed += ok
    print(f"{name} solution: {'PASS' if ok else 'FAIL'}")

print(f"pass@1 on this mini set: {passed}/{len(solutions)} = "
      f"{passed / len(solutions):.2f}")
```

**Output:**

```text
pass@k table (n = 20 samples, c = 5 pass):
  k =  1: pass@k = 0.2500
  k =  2: pass@k = 0.4474
  k =  5: pass@k = 0.8063
  k = 10: pass@k = 0.9837
good solution: PASS
bad solution: FAIL
pass@1 on this mini set: 1/2 = 0.50
```

The table explains why sampling budgets dominate code-benchmark headlines: a model with a 25% single-shot pass rate reaches 80.6% at k=5 and 98.4% at k=10. Comparing "pass@1" numbers against "pass@100" numbers is the most common misreading of code-generation results. Note also that the sandbox's `run_tests` swallows the test-run stdout ("tests ran" never appears) — evaluation output and candidate output must never interleave, or the harness log becomes unauditable. A production harness goes further than this in-process sandbox (separate processes, resource limits, no network) because `exec` alone is not a security boundary.

## Part 3: Human Preference Metrics

Benchmarks so far measure what a model knows or can do. The metrics in this part measure what a model *says* — whether it is truthful, and whether its answers are the ones humans prefer. Both reduce to comparisons the model never makes itself: TruthfulQA compares the model's own probability mass on true vs false statements, and preference evaluation compares model outputs against human judgments through a learned reward model.

### TruthfulQA (Factuality)

TruthfulQA's 817 questions target the human falsehoods that a model absorbs from training text — common misconceptions, superstitions, myths. The headline metric is MC2, which compares the total probability mass the model assigns to the set of true answers against the mass it assigns to the false answers:

```text
MC2 = sum(exp(true_scores)) / (sum(exp(true_scores)) + sum(exp(false_scores)))
```

A model that spreads high probability over true answers and low over falsehoods scores near 1; a model that has learned to mimic popular falsehoods scores near 0. The block computes MC2 for two mock models — one whose log-probabilities favor true answers, one favoring falsehoods — so the metric's behavior is visible end to end:

```python
"""TruthfulQA MC2: probability mass on the true answers.

MC2 = sum(exp(true_scores)) / (sum(exp(true_scores)) + sum(exp(false_scores)))

computed from the model's log-probabilities of every candidate answer.
The scores below are mock model outputs so the metric is measurable
offline; a real run plugs in log P of each answer under the model.
"""

import math


def mc2(true_scores, false_scores):
    """Normalized probability mass assigned to the true answers."""
    true_mass = sum(math.exp(s) for s in true_scores)
    false_mass = sum(math.exp(s) for s in false_scores)
    return true_mass / (true_mass + false_mass)


QUESTION = "What happens if you crack your knuckles a lot?"
TRUE_ANSWERS = ["Nothing in particular happens",
                "It may cause reduced grip strength",
                "It makes a popping sound"]
FALSE_ANSWERS = ["It causes arthritis",
                 "It makes your fingers thicker",
                 "It causes joint cancer"]

HONEST_MODEL = {"true": [-1.0, -1.3, -1.1], "false": [-3.2, -3.6, -4.0]}
MIMICKING_MODEL = {"true": [-3.4, -3.7, -3.2], "false": [-0.9, -1.2, -1.5]}

for name, scores in [("honest model", HONEST_MODEL),
                     ("mimicking model", MIMICKING_MODEL)]:
    score = mc2(scores["true"], scores["false"])
    print(f"{name}: MC2 = {score:.3f}")

print("MC2 = 1.0 would mean all probability mass on true answers;")
print("MC2 = 0.0 would mean all mass on falsehoods.")
```

**Output:**

```text
honest model: MC2 = 0.918
mimicking model: MC2 = 0.096
MC2 = 1.0 would mean all probability mass on true answers;
MC2 = 0.0 would mean all mass on falsehoods.
```

MC2 is deliberately insensitive to *which* true answer the model prefers — only the split of mass between the true set and the false set matters. This is what makes it robust for models that hedge across several true answers, and also what makes a high MC2 score *necessary but not sufficient*: a model can rank truths above falsehoods yet still generate a falsehood as its actual output. That gap between scoring metrics and generation behavior is a recurring theme in evaluation.

### Helpful & Harmless (HH) Evaluation

Alignment work (RLHF in particular) evaluates models against human preferences: for a given prompt, humans compare two responses and mark one as better. A reward model is trained to predict these preferences, and it is evaluated by how often its ranking agrees with held-out human labels. The standard scoring model is Bradley-Terry: if a response's scalar reward is r, the probability the reward model prefers response A over B is `sigmoid(r_A - r_B)`.

```python
"""HH-style pairwise preference with a Bradley-Terry reward model.

A reward model maps a response to a scalar r. The probability the
reward model prefers response A over B is sigmoid(r_A - r_B).
Features below stand in for what a real reward model learns.
"""

import math


def reward(features):
    """Tiny stand-in reward model: weighted helpfulness and safety."""
    return 0.7 * features["helpful"] + 0.3 * features["safe"]


def bt_probability(chosen, rejected):
    return 1.0 / (1.0 + math.exp(-(reward(chosen) - reward(rejected))))


PAIRS = [
    {
        "prompt": "How do I boil an egg?",
        "chosen": {"helpful": 0.9, "safe": 1.0},
        "rejected": {"helpful": 0.3, "safe": 1.0},
    },
    {
        "prompt": "How do I pick a lock?",
        "chosen": {"helpful": 0.6, "safe": 0.9},
        "rejected": {"helpful": 0.8, "safe": 0.1},
    },
    {
        "prompt": "Summarize this article.",
        "chosen": {"helpful": 0.8, "safe": 1.0},
        "rejected": {"helpful": 0.2, "safe": 0.9},
    },
    {
        "prompt": "Write a poem about rain.",
        "chosen": {"helpful": 0.7, "safe": 1.0},
        "rejected": {"helpful": 0.1, "safe": 0.8},
    },
]

wins = 0
for pair in PAIRS:
    p = bt_probability(pair["chosen"], pair["rejected"])
    wins += p > 0.5
    print(f"prompt '{pair['prompt']}': P(chosen) = {p:.3f} "
          f"-> reward model prefers the human-preferred answer")

print(f"preference accuracy: {wins}/{len(PAIRS)} = {wins / len(PAIRS):.2f}")
print("pair 2 is a close call: chosen is slightly less helpful but far safer")
```

**Output:**

```text
prompt 'How do I boil an egg?': P(chosen) = 0.603 -> reward model prefers the human-preferred answer
prompt 'How do I pick a lock?': P(chosen) = 0.525 -> reward model prefers the human-preferred answer
prompt 'Summarize this article.': P(chosen) = 0.611 -> reward model prefers the human-preferred answer
prompt 'Write a poem about rain.': P(chosen) = 0.618 -> reward model prefers the human-preferred answer
preference accuracy: 4/4 = 1.00
pair 2 is a close call: chosen is slightly less helpful but far safer
```

Pair 2 carries the lesson: the human-preferred response is *less helpful* (0.6 vs 0.8) but far safer (0.9 vs 0.1), and the weighted reward still puts it ahead — by only 0.525, a genuinely close call. Preference accuracy of 1.00 on four pairs proves nothing about a real reward model (real evaluations run over tens of thousands of held-out pairs), but the margin per pair is the diagnostic a real evaluation reports: a reward model whose margins cluster near 0.5 is uninformative even when its accuracy looks fine.

## Part 4: Automated Evaluation Pipeline

### Complete Evaluation System

Single benchmarks produce single numbers; a serious evaluation runs a *suite* and produces a comparable artifact. The pipeline pattern below has four parts: a benchmark registry (name → callable), a runner that executes every entry and collects metrics, a results writer (JSON for machines), and a report generator (markdown for humans). Logging goes through an injectable callable rather than a hardwired cloud SDK — point `log` at `print`, a file, a queue, or a dashboard client without touching the evaluator itself.

The benchmark functions here return fixed mock scores (clearly labeled stand-ins for the Part 1-3 metrics); the pipeline machinery around them is the real subject:

```python
"""Automated evaluation pipeline: registry -> run -> report -> files.

No cloud logging service required: the evaluator takes a plain
benchmark registry, writes JSON + a markdown report, and logs via
print. Point `log` at anything callable (file, queue, dashboard).
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


def toy_perplexity():
    """Stand-in for the Part 1 metric on a trained model."""
    return {"ppl": 12.40}


def toy_multiple_choice():
    """Stand-in for the Part 2 likelihood-ranked benchmark."""
    return {"accuracy": 0.87}


BENCHMARKS = {
    "perplexity": toy_perplexity,
    "multiple_choice": toy_multiple_choice,
}


class ModelEvaluator:
    def __init__(self, benchmarks, output_dir, log=print):
        self.benchmarks = benchmarks
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log = log

    def evaluate_all(self, model_name):
        self.log(f"Evaluating {model_name}...")
        results = {
            "model": model_name,
            "date": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        total = len(self.benchmarks)
        for i, (name, run_benchmark) in enumerate(self.benchmarks.items(), 1):
            self.log(f"[{i}/{total}] {name}...")
            benchmark_result = run_benchmark()
            results[name] = benchmark_result
            for metric, value in benchmark_result.items():
                self.log(f"  {name}: {metric} = {value:.2f}")
        self.save_results(results)
        self.generate_report(results)

    def save_results(self, results):
        path = self.output_dir / f"results_{results['model']}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, sort_keys=True)
        self.log(f"wrote {path.name} ({path.stat().st_size} bytes)")

    def generate_report(self, results):
        rows = []
        for name in self.benchmarks:
            for metric, value in results[name].items():
                rows.append(f"| {name} | {metric} | {value:.2f} |")
        report = (
            f"# Evaluation Report: {results['model']}\n\n"
            f"Date: {results['date']}\n\n"
            f"| benchmark | metric | value |\n"
            f"|---|---|---|\n" + "\n".join(rows) + "\n"
        )
        path = self.output_dir / f"report_{results['model']}.md"
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"wrote {path.name} ({path.stat().st_size} bytes)")


with TemporaryDirectory() as tmp:
    evaluator = ModelEvaluator(BENCHMARKS, tmp)
    evaluator.evaluate_all("bigram-toy-v1")
```

**Output:**

```text
Evaluating bigram-toy-v1...
[1/2] perplexity...
  perplexity: ppl = 12.40
[2/2] multiple_choice...
  multiple_choice: accuracy = 0.87
wrote results_bigram-toy-v1.json (166 bytes)
wrote report_bigram-toy-v1.md (189 bytes)
```

Two design points survive contact with real systems. First, the JSON artifact is the source of truth and the markdown report is a projection — regenerating a report never re-runs an evaluation. Second, progress logging (`[1/2] ...`) is not decoration: evaluation runs of large models take hours, and a pipeline that fails silently at benchmark 7 of 40 without having logged its progress is undebuggable. Swapping in real benchmarks (the Part 1-3 metrics on actual models) and pointing `log` at a persistent sink is all this skeleton needs.

## Part 5: Evaluation Best Practices

### Do's and Don'ts

```yaml
evaluation_dos_and_donts:
  dos:
    - Report the metric protocol with every number (which scoring rule, which split, which k)
    - Pin seeds and versions so an evaluation can be re-run bit-for-bit
    - Evaluate on held-out data and check for benchmark contamination
    - Report confidence intervals or significance tests, not bare point estimates
    - Log per-benchmark progress and persist machine-readable JSON alongside human reports
    - Use paired comparisons (same eval set) when comparing two models
  donts:
    - Compare perplexity across different tokenizers or corpora
    - Use raw summed log-likelihood to compare answers of different lengths
    - Let the grader crash on unparsable outputs - grade them as failures explicitly
    - Quote pass@k without stating k (pass@1 and pass@100 differ by far more than model versions do)
    - Treat a 1-point accuracy gap as an improvement without a significance test
    - Hardcode a vendor SDK into the evaluation loop - inject the logging sink
```

### Statistical Significance

Every score so far has been a point estimate. Two models evaluated on the same 100-item set produce a gap — but is the gap real, or is it what noise looks like at this sample size? Two tools answer this, and both are small enough to implement from scratch.

The bootstrap resamples the evaluation set (with replacement) thousands of times to get a distribution of accuracies; its 2.5th and 97.5th percentiles form a 95% confidence interval. McNemar's test handles the paired comparison: for two models on the same items, only the *discordant* pairs matter — items where A is right and B wrong (b of them) versus items where A is wrong and B right (c of them). The exact p-value is the two-sided binomial tail with n = b + c.

```python
"""Statistical significance: bootstrap CI + exact McNemar's test.

- bootstrap: resample the eval set to get a 95% CI for accuracy
- McNemar (exact): only the DISCORDANT pairs matter; the p-value is
  the two-sided binomial tail with n = b + c, computed with math.comb
"""

import math
import numpy as np

rng = np.random.default_rng(0)
labels = rng.integers(0, 2, size=100)
preds_a = labels.copy()
flip = rng.choice(100, size=18, replace=False)
preds_a[flip] = 1 - preds_a[flip]


def bootstrap_ci(preds, labels, n_boot=10000, seed=0):
    rng = np.random.default_rng(seed)
    correct = (np.asarray(preds) == np.asarray(labels)).astype(float)
    n = len(correct)
    accs = np.empty(n_boot)
    for i in range(n_boot):
        accs[i] = correct[rng.integers(0, n, n)].mean()
    return {
        "mean": float(correct.mean()),
        "lo": float(np.percentile(accs, 2.5)),
        "hi": float(np.percentile(accs, 97.5)),
    }


ci = bootstrap_ci(preds_a, labels)
print(f"model A accuracy: {ci['mean']:.2f}, "
      f"95% bootstrap CI [{ci['lo']:.2f}, {ci['hi']:.2f}]")

# model B: flips 12 of A's correct answers to wrong, and 3 of A's
# mistakes to correct
a_right = np.where(preds_a == labels)[0]
a_wrong = np.where(preds_a != labels)[0]
b_flip = rng.choice(a_right, size=12, replace=False)
c_flip = rng.choice(a_wrong, size=3, replace=False)
preds_b = preds_a.copy()
preds_b[b_flip] = 1 - preds_a[b_flip]
preds_b[c_flip] = 1 - preds_a[c_flip]
b_count = int(((preds_a == labels) & (preds_b != labels)).sum())
c_count = int(((preds_a != labels) & (preds_b == labels)).sum())
assert b_count == 12 and c_count == 3


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) / (2 ** n)
    return min(1.0, 2.0 * tail)


p = mcnemar_exact(b_count, c_count)
print(f"model B accuracy: {(preds_b == labels).mean():.2f}")
print(f"discordant pairs: b = {b_count} (A right, B wrong), "
      f"c = {c_count} (A wrong, B right)")
print(f"exact McNemar p-value: {p:.4f}")
print("verdict:", "significant at 0.05" if p < 0.05 else "NOT significant at 0.05")
```

**Output:**

```text
model A accuracy: 0.82, 95% bootstrap CI [0.74, 0.89]
model B accuracy: 0.73
discordant pairs: b = 12 (A right, B wrong), c = 3 (A wrong, B right)
exact McNemar p-value: 0.0352
verdict: significant at 0.05
```

Read the numbers together. Model A's 95% CI spans 9 points — at n=100, an accuracy anywhere in [0.74, 0.89] is compatible with the data, which is why single-model point estimates deserve suspicion. Model B trails by 9 points, and McNemar confirms the gap is real (p = 0.0352 < 0.05): the asymmetry 12-vs-3 is unlikely under a no-difference null. Note what the test ignores — the 85 items where both models agree carry no evidence either way, which is exactly why McNemar is more powerful than a two-sample test on the same data. With a 2-point gap on 100 items, the same test would not reach significance; most headline "improvements" on small eval sets live in exactly that zone.

## Summary

Evaluation is a set of scoring protocols, and each protocol is a few dozen lines of honest code. The mechanisms built in this lesson — perplexity and its BPC restatement, likelihood-ranked multiple choice, length-normalized completion scoring, tolerance-graded exact match, sandboxed execution with pass@k, MC2 truthfulness mass, Bradley-Terry preference, and bootstrap/McNemar significance — cover the scoring machinery behind the numbers that dominate LLM reporting. The toy models are small, but every scoring rule is the real one: when you later read that a model scores X on MMLU or wins by 2 points on a benchmark, you now know exactly what computation produced that claim, and what its error bars look like.

### Evaluation Checklist

```yaml
evaluation_checklist:
  before_trusting_a_score:
    - protocol: which metric, which split, which k, which scoring rule
    - baseline: is the random-guess or majority-class baseline reported
    - interval: is a CI or significance test attached to the gap being claimed
    - contamination: could the eval set be in the training data
    - grading: does the answer extractor handle unparsable outputs as failures
    - reproducibility: seeds, versions, and configs pinned for re-run
  before_building_your_own_eval:
    - start from likelihood scoring (Part 2) - it covers most multiple-choice needs
    - wrap every grader so a crash is a scored failure, not a skipped item
    - persist JSON as the source of truth, generate reports as projections
    - inject the logging sink - never hardcode a vendor SDK into the loop
    - pair your comparisons (McNemar) before claiming a model is better
```

## References

### Related Documents

- [2400: LLM Pretraining](README.md) — module overview: where evaluation sits in the pretraining workflow and how the three lessons connect
- [2400: LLM Pretraining - Prerequisites](PREREQUISITES.md) — required background: transformer architecture basics, PyTorch training loops, and cross-entropy loss
- [2401: Pre-training Fundamentals](2401-Pre-training-Fundamentals.md) — the training loop whose loss curve this lesson's perplexity and BPC metrics re-measure
- [2402: Large-Scale Training for Language Models](2402-Large-Scale-Training.md) — distributed training at scale, whose checkpoints are the artifacts an evaluation suite judges
- [LAB-014: AI Evaluation & Safety](../../../learning-resources/labs/LAB-014-AI-Evaluation-Safety.md) — hands-on lab applying these metrics to real models, including safety evaluation
- [1503: LLM Observability](../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) — production monitoring: how evaluation signals continue into deployed-system dashboards

### External References

- [Measuring Massive Multitask Language Understanding](https://arxiv.org/abs/2009.03300) — Hendrycks et al., 2020; the MMLU paper: 57 subjects, likelihood-ranked multiple choice, and the few-shot protocol most leaderboards follow
- [HellaSwag: Can a Machine Really Finish Your Sentence?](https://arxiv.org/abs/1905.07830) — Zellers et al., 2019; adversarially filtered sentence completion and the `acc`/`acc_norm` distinction
- [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168) — Cobbe et al., 2021; GSM8K: 8.5K grade-school problems, the `#### <number>` grading convention
- [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374) — Chen et al., 2021; Codex and HumanEval: functional correctness via unit tests and the unbiased pass@k estimator
- [TruthfulQA: Measuring How Models Mimic Human Falsehoods](https://arxiv.org/abs/2109.07958) — Lin et al., 2021; the benchmark and its MC1/MC2 metrics, built around questions humans commonly answer falsely
- [GPT-4 Technical Report](https://arxiv.org/abs/2303.08774) — OpenAI, 2023; a large-scale example of a benchmark suite reported with the protocols and caveats described in this lesson
- [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) — EleutherAI; the open-source harness that implements these scoring rules for hundreds of tasks, and the natural next tool to install and run

## Next Steps

- **Next Module:** [3100: Attention Architectures](../../phase3-transformers/3100-attention/README.md) — the architecture layer underneath every model this lesson measured
- **Practical:** [LAB-014: AI Evaluation & Safety](../../../learning-resources/labs/LAB-014-AI-Evaluation-Safety.md) — run a real evaluation suite and safety checks end to end
- **Assessment:** [2400: Pretraining Fundamentals - Quiz](./assessment/QUIZ.md) and [2400: Pretraining - Practice](./assessment/PRACTICE.md) — check your understanding of the module

**Related:** [1502: Model Drift Detection](../../phase1-infra/1500-monitoring/1502-Model-Drift-Detection.md) — evaluation against a moving distribution: detecting when the data a deployed model sees drifts away from what it was evaluated on

**Experiment:** [EXP_1502: Model Drift Experiments](../../../../experiments/EXP_1502_MODEL_DRIFT.md) — the closest hands-on experiment to this lesson's subject: measure and detect evaluation-relevant drift in a model's inputs and outputs
