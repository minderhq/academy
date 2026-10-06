---
Document ID: 7106
Title: "7106: Function-Calling Training and Constrained Decoding - The Grammar Owns the Syntax, the Data Owns the Semantics"
Phase: 7
Module: 7100
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 4 hours
Tags: ['agents', 'function-calling', 'constrained-decoding', 'inference', 'training']
---

# 7106: Function-Calling Training and Constrained Decoding - The Grammar Owns the Syntax, the Data Owns the Semantics

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [The Grammar-to-Mask Mechanism](#the-grammar-to-mask-mechanism)
- [Prompting Is Not Constraining](#prompting-is-not-constraining)
- [Training the Call: The Gorilla Recipe](#training-the-call-the-gorilla-recipe)
- [Syntax Guarantees, Semantics Trains: The 2x2](#syntax-guarantees-semantics-trains-the-2x2)
- [The Campaign: Four Stacks, One Ledger](#the-campaign-four-stacks-one-ledger)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Compile a call grammar into a per-step token mask and show that the mask alone flips a 0.0000 valid-call rate to 1.0000 without touching a single weight
- Separate what a format prompt buys (0.7940 valid at 17.18 tokens per request) from what a mask guarantees (1.0000 at 8.92) and why no retry budget closes the gap
- Run the capability-training walk - 120 pairs lift tool accuracy from 0.3333 to a 0.89 greedy plateau set by the query vocabulary the pairs cover, not by the optimizer
- Read the syntax-by-semantics grid: the mask guarantees parseable, training supplies correct, and only the trained-plus-masked cell is deployable
- Price four serving stacks on one 2,000-request ledger and see that the training bill is one-time while the untrained stacks' failure is per-request

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)

## Abstract

[1405](../../phase1-infra/1400-llmops/1405-SGLang.md) owns the serving-side contract - the `xgrammar` backend flag and the structured-output API a consumer calls; [7201](../7200-tools/7201-Tool-Calling.md) owns the registry discipline that keeps a tool's schema honest; [7101](./7101-ReAct-Loop-System.md) owns the loop that executes whatever call arrives and its mechanical retry; [7105](./7105-Reflection-and-Self-Correction.md) owns the named in-run correction patterns. What no lesson has owned is the mechanism underneath - how a grammar becomes a per-step logit mask, why prompting for format is not constraining for format, and where the function-calling capability itself comes from - which is exactly the gap the module's own quiz admits twice: function-calling training at Q11 and constrained generation at Q16, both taught nowhere. This lesson builds both from one toy: a three-tool call language whose grammar compiles to a twelve-state FSM, a policy that serves raw, prompted, or masked, and a pair corpus that trains it. The mask alone flips 0.0000 to 1.0000 valid; the prompt alone reaches only 0.7940 and pays 1.454 retries per request to get there; training lifts greedy tool accuracy 0.3333 to 0.8917 and stops where the pair vocabulary stops; and the 2x2 grid shows the two levers are orthogonal - syntax is a decoding-time guarantee, semantics is a training-time property, and the deployable cell is their product.

## The Grammar-to-Mask Mechanism

Outlines (Willard and Louf, arXiv 2307.09702) stated the reformulation this lesson builds: any generation step under a grammar is equivalent to choosing the next token from the subset the grammar's state admits, which means the constraint can be applied by zeroing the logits of every token not in that subset - no architecture change, no fine-tune, model-agnostic. XGrammar (Dong et al., arXiv 2411.15100, MLSys 2025) made the check fast enough for production by partitioning the vocabulary into tokens whose admissibility is context-independent (precomputable once per grammar) and context-dependent (checked against a persistent stack), reporting near-zero per-token overhead and large speedups over per-step full-vocabulary checks.

The toy here is a three-tool call language: `fn:` TOOL `{` KEY `:` VALUE (`,` KEY `:` VALUE)* `}` where the key must be the tool's own argument name - `search` takes `q`, `calc` takes `x`, `weather` takes `city` - and the value must come from that key's pool. The vocabulary is 31 tokens: 21 call tokens and 10 prose tokens a base model would rather emit. Compiling the grammar gives a twelve-state FSM, and the first fence walks one call's path through it, counting the legal set at each position:

```python
import random

TOOLS = ["search", "calc", "weather"]
ARG_KEYS = {"search": "q", "calc": "x", "weather": "city"}
ARG_VALUES = {"q": ['"transformers"', '"quantization"', '"agents"'],
              "x": ['"42"', '"7"', '"3"'], "city": ['"tokyo"', '"paris"', '"ohio"']}
ALL_KEYS = sorted(set(ARG_KEYS.values()))
CALL_TOKENS = (["fn:", "{", "}", ",", ":", '"'] + TOOLS + ALL_KEYS
               + sorted({v for vals in ARG_VALUES.values() for v in vals}))
NOISE_TOKENS = ["the", "I", "maybe", "a", "is", "run", "stuff", "things", "data", "yes"]
VOCAB = []
for _t in CALL_TOKENS + NOISE_TOKENS:
    if _t not in VOCAB:
        VOCAB.append(_t)


def valid_call(tokens):
    if not tokens or tokens[0] != "fn:":
        return False
    if len(tokens) < 2 or tokens[1] not in TOOLS:
        return False
    tool = tokens[1]
    rest = tokens[2:]
    if not rest or rest[0] != "{":
        return False
    rest = rest[1:]
    if not rest or rest[-1] != "}":
        return False
    rest = rest[:-1]
    if not rest or len(rest) < 3 or rest[1] != ":":
        return False
    key, val = rest[0], rest[2]
    if key != ARG_KEYS[tool] or val not in ARG_VALUES.get(key, []):
        return False
    return len(rest) == 3 or (len(rest) == 7 and rest[3] == "," and rest[4] == ARG_KEYS[tool]
                              and rest[5] == ":" and rest[6] in ARG_VALUES[rest[4]])


def fsm_next(state, tok, tool=None):
    pos = state[0]
    if pos == 0:
        return ((1, None), tok) if tok == "fn:" else None
    if pos == 1:
        return ((2, None), tok) if tok in TOOLS else None
    if pos == 2:
        return ((3, None), tool) if tok == "{" else None
    if pos == 3:
        return ((4, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 4:
        return ((5, None), tool) if tok == ":" else None
    if pos == 5:
        return ((6, "v1"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 6:
        if tok == "}":
            return ((7, None), tool)
        if tok == ",":
            return ((8, None), tool)
        return None
    if pos == 8:
        return ((9, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 9:
        return ((10, None), tool) if tok == ":" else None
    if pos == 10:
        return ((11, "done"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 11:
        return ((7, None), tool) if tok == "}" else None
    return None


START = (0, None)
ACCEPT_POS = 7


def fsm_legal_tokens(state, tool):
    return [t for t in VOCAB if fsm_next(state, t, tool) is not None]


def fsm_explore():
    seen, frontier = set(), [(START, None)]
    while frontier:
        state, tool = frontier.pop()
        if (state, tool) in seen:
            continue
        seen.add((state, tool))
        for t in fsm_legal_tokens(state, tool):
            ns = fsm_next(state, t, tool)
            frontier.append((ns[0], ns[1] if ns[1] is not None else tool))
    return len({s[0] for s, _ in seen})


class Policy:
    def __init__(self):
        self.scores = {}
        self.mode = "raw"

    def _word_dist(self, w, last):
        sc = self.scores.get((w, last), {})
        z = sum(sc.values())
        if z == 0:
            return {t: 1.0 / len(VOCAB) for t in VOCAB}
        d = {t: (sc[t] / z) ** 1.25 if t in sc else 0.0 for t in VOCAB}
        tz = sum(d.values())
        return {t: p / tz for t, p in d.items()}

    def _dist(self, context, last):
        ds = [self._word_dist(w, last) for w in context]
        return {t: sum(d[t] for d in ds) / len(ds) for t in VOCAB}

    def sample(self, context, rng, mask=False, max_len=12):
        toks, state, tool, last = [], START, None, "<s>"
        for _ in range(max_len):
            if state[0] == ACCEPT_POS:
                return toks
            dist = self._dist(context, last)
            if mask:
                legal = ["fn:"] if state == START else fsm_legal_tokens(state, tool)
                dist = {t: dist[t] for t in legal}
                z = sum(dist.values())
                dist = ({t: 1.0 / len(legal) for t in legal} if z == 0
                        else {t: p / z for t, p in dist.items()})
            r, acc, chosen = rng.random(), 0.0, None
            for t, p in dist.items():
                acc += p
                if r <= acc:
                    chosen = t
                    break
            if chosen is None:
                chosen = list(dist)[0]
            nxt = fsm_next(state, chosen, tool)
            if nxt is None:
                state, tool = ((99, None), tool)
                toks.append(chosen)
                last = chosen
                continue
            toks.append(chosen)
            state, tool = nxt[0], (nxt[1] if nxt[1] is not None else tool)
            last = chosen
        return toks


rng = random.Random(7)
n_states = fsm_explore()
p = Policy()
N = 2000
raw_valid = sum(1 for _ in range(N) if valid_call(p.sample(["find"], rng)))
p2 = Policy()
mask_valid = sum(1 for _ in range(N) if valid_call(p2.sample(["find"], rng, mask=True)))
path = [START, (1, None), (2, None), (3, None), (4, None), (5, None), (6, "v1")]
path_sizes = [1 if st == START else len(fsm_legal_tokens(st, "search")) for st in path]
print("=== F1 grammar-to-mask mechanism")
print(f"vocab_size={len(VOCAB)} call_tokens={len(CALL_TOKENS)} noise_tokens={len(NOISE_TOKENS)}")
print(f"fsm_states={n_states} per_state_legal_sizes={path_sizes}")
print(f"unconstrained_valid={raw_valid}/{N}={raw_valid / N:.4f}")
print(f"masked_valid={mask_valid}/{N}={mask_valid / N:.4f}")
print(f"typical_allowed_step={max(path_sizes)} of {len(VOCAB)} = {max(path_sizes) / len(VOCAB):.4f}")
```

The walk's legal-set sizes read `[1, 3, 1, 1, 1, 3, 2]`: exactly one token opens a call, three tools are admissible after `fn:`, the brace and colon positions admit exactly one token each, three values are legal in the value slot, and two tokens (`}` closing the call, or `,` extending it to a second pair) close the value position. At the widest step the grammar admits 3 of 31 tokens - 0.0968 of the vocabulary; at the narrow ones it admits one. An unconstrained sampler draws all 31 tokens at every position and lands `0/2000 = 0.0000` valid calls in 2,000 twelve-token draws - not one. The same sampler masked to the FSM's legal set lands `2000/2000 = 1.0000`. Nothing about the model changed; the mask deleted the 28 tokens that could have broken the call before they could be chosen. Note what the toy honestly cannot show: in this two-pair grammar no token is admissible in every state, so XGrammar's context-independent partition is empty here - that partition is a production-vocabulary effect, where 100,000-token vocabularies are mostly tokens no state of any given grammar ever admits, and precomputing them is where the speedup lives. The mechanism - per-step legal set, zero the rest - is the same at both scales.

## Prompting Is Not Constraining

The standard first move is to paste the format into the prompt: "emit calls as fn: TOOL { KEY : VALUE }". For a base model the honest model of what that buys is shape compliance without grounding: the model now follows the call's silhouette - `fn:`, a tool slot, a braced body - but it does not know which argument name belongs to which tool, so it picks the key uniformly across all three, and it does not know the value pools, so it invents. The second fence serves the same 2,000 requests three ways through one policy: raw (no format knowledge), prompted (format silhouette followed, bindings guessed), and masked (the FSM's legal set enforced at every step, with a uniform fallback over the legal set when the policy's mass on it is zero - the fallback every production constrained-decoding stack implements):

```python
import random

TOOLS = ["search", "calc", "weather"]
ARG_KEYS = {"search": "q", "calc": "x", "weather": "city"}
ARG_VALUES = {"q": ['"transformers"', '"quantization"', '"agents"'],
              "x": ['"42"', '"7"', '"3"'], "city": ['"tokyo"', '"paris"', '"ohio"']}
ALL_KEYS = sorted(set(ARG_KEYS.values()))
CALL_TOKENS = (["fn:", "{", "}", ",", ":", '"'] + TOOLS + ALL_KEYS
               + sorted({v for vals in ARG_VALUES.values() for v in vals}))
NOISE_TOKENS = ["the", "I", "maybe", "a", "is", "run", "stuff", "things", "data", "yes"]
VOCAB = []
for _t in CALL_TOKENS + NOISE_TOKENS:
    if _t not in VOCAB:
        VOCAB.append(_t)
UNIQUE = {"search": ["find", "docs", "paper", "tutorial", "lookup", "cite", "reference", "browse"],
          "calc": ["compute", "evaluate", "sum", "square", "multiply", "divide", "sqrt", "modulo"],
          "weather": ["forecast", "temperature", "humidity", "rain", "wind", "snow", "uv", "pressure"]}
SHARED = ["today", "now", "quick", "update", "current", "local"]


def valid_call(tokens):
    if not tokens or tokens[0] != "fn:":
        return False
    if len(tokens) < 2 or tokens[1] not in TOOLS:
        return False
    tool = tokens[1]
    rest = tokens[2:]
    if not rest or rest[0] != "{":
        return False
    rest = rest[1:]
    if not rest or rest[-1] != "}":
        return False
    rest = rest[:-1]
    if not rest or len(rest) < 3 or rest[1] != ":":
        return False
    key, val = rest[0], rest[2]
    if key != ARG_KEYS[tool] or val not in ARG_VALUES.get(key, []):
        return False
    return len(rest) == 3 or (len(rest) == 7 and rest[3] == "," and rest[4] == ARG_KEYS[tool]
                              and rest[5] == ":" and rest[6] in ARG_VALUES[rest[4]])


def fsm_next(state, tok, tool=None):
    pos = state[0]
    if pos == 0:
        return ((1, None), tok) if tok == "fn:" else None
    if pos == 1:
        return ((2, None), tok) if tok in TOOLS else None
    if pos == 2:
        return ((3, None), tool) if tok == "{" else None
    if pos == 3:
        return ((4, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 4:
        return ((5, None), tool) if tok == ":" else None
    if pos == 5:
        return ((6, "v1"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 6:
        if tok == "}":
            return ((7, None), tool)
        if tok == ",":
            return ((8, None), tool)
        return None
    if pos == 8:
        return ((9, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 9:
        return ((10, None), tool) if tok == ":" else None
    if pos == 10:
        return ((11, "done"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 11:
        return ((7, None), tool) if tok == "}" else None
    return None


START = (0, None)
ACCEPT_POS = 7


def fsm_legal_tokens(state, tool):
    return [t for t in VOCAB if fsm_next(state, t, tool) is not None]


def make_query(intent, rng):
    words = []
    for _ in range(2):
        words.append(rng.choice(UNIQUE[intent]) if rng.random() < 0.60
                     else rng.choice(SHARED))
    return words


class Policy:
    def __init__(self):
        self.scores = {}
        self.mode = "raw"

    def _word_dist(self, w, last):
        sc = self.scores.get((w, last), {})
        z = sum(sc.values())
        if z == 0:
            return {t: 1.0 / len(VOCAB) for t in VOCAB}
        d = {t: (sc[t] / z) ** 1.25 if t in sc else 0.0 for t in VOCAB}
        tz = sum(d.values())
        return {t: p / tz for t, p in d.items()}

    def _dist(self, context, last):
        ds = [self._word_dist(w, last) for w in context]
        return {t: sum(d[t] for d in ds) / len(ds) for t in VOCAB}

    def sample(self, context, rng, mask=False, max_len=12):
        if self.mode == "prompted" and not mask:
            return self._sample_prompted(rng)
        toks, state, tool, last = [], START, None, "<s>"
        for _ in range(max_len):
            if state[0] == ACCEPT_POS:
                return toks
            dist = self._dist(context, last)
            if mask:
                legal = ["fn:"] if state == START else fsm_legal_tokens(state, tool)
                dist = {t: dist[t] for t in legal}
                z = sum(dist.values())
                dist = ({t: 1.0 / len(legal) for t in legal} if z == 0
                        else {t: p / z for t, p in dist.items()})
            r, acc, chosen = rng.random(), 0.0, None
            for t, p in dist.items():
                acc += p
                if r <= acc:
                    chosen = t
                    break
            if chosen is None:
                chosen = list(dist)[0]
            nxt = fsm_next(state, chosen, tool)
            if nxt is None:
                state, tool = ((99, None), tool)
                toks.append(chosen)
                last = chosen
                continue
            toks.append(chosen)
            state, tool = nxt[0], (nxt[1] if nxt[1] is not None else tool)
            last = chosen
        return toks

    def _sample_prompted(self, rng):
        eps = 0.02
        def nz(t):
            return t if rng.random() > eps else rng.choice(NOISE_TOKENS)
        tool = rng.choice(TOOLS)
        key = rng.choice(ALL_KEYS)
        val = rng.choice(ARG_VALUES[key])
        return ["fn:", nz(tool), "{", nz(key), ":", nz(val), "}"]


rng = random.Random(7)
N = 2000
results = {}
for mode in ("raw", "prompted", "masked"):
    p = Policy()
    p.mode = "prompted" if mode == "prompted" else "raw"
    ms = mode == "masked"
    valid = retry_tokens = retry_count = 0
    for _ in range(N):
        ctx = make_query("search", rng)
        toks = p.sample(ctx, rng, mask=ms)
        attempts, ok = 1, valid_call(toks)
        while not ok and attempts < 4:
            retry_tokens += len(toks)
            retry_count += 1
            toks = p.sample(ctx, rng, mask=ms)
            attempts += 1
            ok = valid_call(toks)
        if ok:
            valid += 1
        retry_tokens += len(toks)
    results[mode] = (valid / N, retry_tokens / N, retry_count / N)
print("=== F2 prompting-is-not-constraining (format-unaware base model)")
for mode, (v, tok, rc) in results.items():
    print(f"{mode}: valid_rate={v:.4f} tokens_per_request={tok:.2f} retries_per_request={rc:.3f}")
v_raw, v_pro, v_msk = results["raw"][0], results["prompted"][0], results["masked"][0]
print(f"prompt_gain={v_pro - v_raw:+.4f} mask_gain={v_msk - v_raw:+.4f}")
```

The ladder is the section's whole argument. Raw serves `0.0000` valid and burns `48.00` tokens per request - the max retry budget, four twelve-token attempts, every one of them dead. Prompted jumps to `0.7940` valid - the format instruction is doing real work, `+0.7940` of it - but it gets there by spending `1.454` retries per request and `17.18` tokens per request, and one request in five still exhausts the budget with a call that parses as shape but binds the wrong key. Masked serves `1.0000` valid at `8.92` tokens per request with `0.000` retries: the guarantee is not a better prompt, it is a different mechanism - one that cannot emit an illegal token because the illegal tokens' logits are zeroed before the sample. Gorilla (Patil et al., arXiv 2305.15334) measured what prompt-only leaves on the table at scale: base GPT-4 hallucinates - emits calls to APIs that do not exist - on `36.55%` of TorchHub, `37.16%` of TensorHub, and `78.65%` of Hugging Face queries. A prompt that enumerates valid tools is a list the model can ignore and that goes stale the day the tool list changes; the mask is recompiled from the grammar and cannot go stale. The `+1.0000` against `+0.7940` is the difference between asking and enforcing.

## Training the Call: The Gorilla Recipe

Constrained decoding guarantees the call parses; nothing about it makes the call right. The right-tool decision lives in the weights, and the corpus-level evidence is that it is trainable: Gorilla's APIBench pairs roughly 1,645 APIs (TorchHub 95, TensorHub 696, Hugging Face 925) with about ten self-instruct-generated queries each - 11,000+ pairs - and fine-tunes LLaMA-7B on them to `59.13/71.68/83.79` AST accuracy across the three hubs against GPT-4's zero-shot `38.70/19.80/18.20`, with hallucination dropping to `6.98/10.95/5.40` against the base model's `36.55/37.16/78.65`. ToolLLM (Qin et al., arXiv 2307.16789) scales the recipe to 16,464 RESTful APIs across 49 categories with an instruction-generation pipeline and a three-stage data construction, and its ToolLLaMA lands comparable to ChatGPT on their ToolEval bench. The third fence runs that recipe's shape on the toy: pair corpora arrive in batches of 20, each pair being a two-word query bound to a gold call, and after every batch the policy serves 600 held-out queries under masked greedy decoding - argmax over the legal set, the protocol every benchmark number above was produced under:

```python
import random

TOOLS = ["search", "calc", "weather"]
ARG_KEYS = {"search": "q", "calc": "x", "weather": "city"}
ARG_VALUES = {"q": ['"transformers"', '"quantization"', '"agents"'],
              "x": ['"42"', '"7"', '"3"'], "city": ['"tokyo"', '"paris"', '"ohio"']}
ALL_KEYS = sorted(set(ARG_KEYS.values()))
CALL_TOKENS = (["fn:", "{", "}", ",", ":", '"'] + TOOLS + ALL_KEYS
               + sorted({v for vals in ARG_VALUES.values() for v in vals}))
NOISE_TOKENS = ["the", "I", "maybe", "a", "is", "run", "stuff", "things", "data", "yes"]
VOCAB = []
for _t in CALL_TOKENS + NOISE_TOKENS:
    if _t not in VOCAB:
        VOCAB.append(_t)
UNIQUE = {"search": ["find", "docs", "paper", "tutorial", "lookup", "cite", "reference", "browse"],
          "calc": ["compute", "evaluate", "sum", "square", "multiply", "divide", "sqrt", "modulo"],
          "weather": ["forecast", "temperature", "humidity", "rain", "wind", "snow", "uv", "pressure"]}
SHARED = ["today", "now", "quick", "update", "current", "local"]
INTENTS = ["search", "calc", "weather"]


def valid_call(tokens):
    if not tokens or tokens[0] != "fn:":
        return False
    if len(tokens) < 2 or tokens[1] not in TOOLS:
        return False
    tool = tokens[1]
    rest = tokens[2:]
    if not rest or rest[0] != "{":
        return False
    rest = rest[1:]
    if not rest or rest[-1] != "}":
        return False
    rest = rest[:-1]
    if not rest or len(rest) < 3 or rest[1] != ":":
        return False
    key, val = rest[0], rest[2]
    if key != ARG_KEYS[tool] or val not in ARG_VALUES.get(key, []):
        return False
    return len(rest) == 3 or (len(rest) == 7 and rest[3] == "," and rest[4] == ARG_KEYS[tool]
                              and rest[5] == ":" and rest[6] in ARG_VALUES[rest[4]])


def extract_call(tokens):
    if not valid_call(tokens):
        return None
    tool = tokens[1]
    d = {tokens[3]: tokens[5]}
    if len(tokens) > 8:
        d[tokens[7]] = tokens[9]
    return (tool, d)


def fsm_next(state, tok, tool=None):
    pos = state[0]
    if pos == 0:
        return ((1, None), tok) if tok == "fn:" else None
    if pos == 1:
        return ((2, None), tok) if tok in TOOLS else None
    if pos == 2:
        return ((3, None), tool) if tok == "{" else None
    if pos == 3:
        return ((4, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 4:
        return ((5, None), tool) if tok == ":" else None
    if pos == 5:
        return ((6, "v1"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 6:
        if tok == "}":
            return ((7, None), tool)
        if tok == ",":
            return ((8, None), tool)
        return None
    if pos == 8:
        return ((9, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 9:
        return ((10, None), tool) if tok == ":" else None
    if pos == 10:
        return ((11, "done"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 11:
        return ((7, None), tool) if tok == "}" else None
    return None


START = (0, None)
ACCEPT_POS = 7


def fsm_legal_tokens(state, tool):
    return [t for t in VOCAB if fsm_next(state, t, tool) is not None]


class Policy:
    def __init__(self):
        self.scores = {}
        self.mode = "raw"

    def _word_dist(self, w, last):
        sc = self.scores.get((w, last), {})
        z = sum(sc.values())
        if z == 0:
            return {t: 1.0 / len(VOCAB) for t in VOCAB}
        d = {t: (sc[t] / z) ** 1.25 if t in sc else 0.0 for t in VOCAB}
        tz = sum(d.values())
        return {t: p / tz for t, p in d.items()}

    def _dist(self, context, last):
        ds = [self._word_dist(w, last) for w in context]
        return {t: sum(d[t] for d in ds) / len(ds) for t in VOCAB}

    def sample_greedy(self, context, max_len=12):
        toks, state, tool, last = [], START, None, "<s>"
        for _ in range(max_len):
            if state[0] == ACCEPT_POS:
                return toks
            dist = self._dist(context, last)
            legal = ["fn:"] if state == START else fsm_legal_tokens(state, tool)
            sub = {t: dist[t] for t in legal}
            z = sum(sub.values())
            chosen = (max(sub, key=lambda t: sub[t] / z) if z > 0
                      else max(legal, key=lambda t: sub[t]))
            nxt = fsm_next(state, chosen, tool)
            toks.append(chosen)
            state, tool = nxt[0], (nxt[1] if nxt[1] is not None else tool)
            last = chosen
        return toks

    def observe_query(self, context, toks):
        for w in context:
            seq = ["<s>"] + toks
            for a, b in zip(seq, seq[1:]):
                self.scores.setdefault((w, a), {})
                self.scores[(w, a)][b] = self.scores[(w, a)].get(b, 0.0) + 1.0


def make_query(intent, rng):
    words = []
    for _ in range(2):
        words.append(rng.choice(UNIQUE[intent]) if rng.random() < 0.60
                     else rng.choice(SHARED))
    return words


def make_example(intent, rng, corrupt_p=0.0):
    key = ARG_KEYS[intent]
    if rng.random() < corrupt_p:
        key = rng.choice([k for k in ALL_KEYS if k != ARG_KEYS[intent]])
    vals = ARG_VALUES[key]
    return ["fn:", intent, "{", key, ":", vals[rng.randrange(len(vals))], "}"]


rng = random.Random(7)
p = Policy()
per_epoch = 20
gold = [(it, make_query(it, rng)) for it in INTENTS for _ in range(200)]


def tool_acc(pol):
    hit = 0
    for intent, ctx in gold:
        c = extract_call(pol.sample_greedy(ctx))
        if c and c[0] == intent:
            hit += 1
    return hit / len(gold)


walk = [tool_acc(p)]
for ep in range(6):
    for _ in range(per_epoch):
        it = INTENTS[rng.randrange(3)]
        p.observe_query(make_query(it, rng), make_example(it, rng, 0.06))
    walk.append(tool_acc(p))
print("=== F3 capability-training walk (600 eval queries, masked greedy serving)")
print("pairs_seen: " + " ".join(str(i * per_epoch) for i in range(7)))
print("tool_accuracy: " + " ".join(f"{a:.4f}" for a in walk))
```

The walk climbs `0.3333 / 0.6050 / 0.8183 / 0.8867 / 0.8783 / 0.8883 / 0.8917` across `0 / 20 / 40 / 60 / 80 / 100 / 120` pairs - nearly nine-tenths of the climb lands in the first 40 pairs, then a crawl into a plateau near 0.89 that is not the optimizer running out of steam. The plateau is the query vocabulary's own ceiling: each query carries two words, and every word is drawn 60 percent from its intent's eight unique words and 40 percent from a six-word shared pool that any intent's queries may contain. A query made of two unique words pins its tool exactly once its words are covered; a query mixing a unique word with a shared word resolves only as sharply as the shared word's evidence splits across the three tools; a two-shared-word query is a coin weighted by nothing but pair frequencies. Greedy decoding reads that mixture's mode, so the walk's ceiling sits near 0.89 - the exact share of queries the pair vocabulary can disambiguate - and the walk's one down-step (0.8867 to 0.8783 at 80 pairs) is not noise: greedy evaluation is deterministic, and a handful of shared-word queries flip as their counts cross. This is Gorilla's retriever-aware result in miniature - their +12.37 percent on TorchHub and +23.46 percent on Hugging Face from making training aware of the retrieval context is the same statement at corpus scale: the ceiling is set by what the pairs cover, and no number of additional epochs moves it.

## Syntax Guarantees, Semantics Trains: The 2x2

Two levers, two questions. Does the call parse? That is the grammar's question, answered at decode time by the mask. Is it the right call? That is the data's question, answered at training time by the pairs. The fourth fence crosses them - untrained or trained policy, served raw or masked - and scores 300 queries per cell for validity, tool correctness, and end-to-end executability:

```python
import random

TOOLS = ["search", "calc", "weather"]
ARG_KEYS = {"search": "q", "calc": "x", "weather": "city"}
ARG_VALUES = {"q": ['"transformers"', '"quantization"', '"agents"'],
              "x": ['"42"', '"7"', '"3"'], "city": ['"tokyo"', '"paris"', '"ohio"']}
ALL_KEYS = sorted(set(ARG_KEYS.values()))
CALL_TOKENS = (["fn:", "{", "}", ",", ":", '"'] + TOOLS + ALL_KEYS
               + sorted({v for vals in ARG_VALUES.values() for v in vals}))
NOISE_TOKENS = ["the", "I", "maybe", "a", "is", "run", "stuff", "things", "data", "yes"]
VOCAB = []
for _t in CALL_TOKENS + NOISE_TOKENS:
    if _t not in VOCAB:
        VOCAB.append(_t)
UNIQUE = {"search": ["find", "docs", "paper", "tutorial", "lookup", "cite", "reference", "browse"],
          "calc": ["compute", "evaluate", "sum", "square", "multiply", "divide", "sqrt", "modulo"],
          "weather": ["forecast", "temperature", "humidity", "rain", "wind", "snow", "uv", "pressure"]}
SHARED = ["today", "now", "quick", "update", "current", "local"]
INTENTS = ["search", "calc", "weather"]


def valid_call(tokens):
    if not tokens or tokens[0] != "fn:":
        return False
    if len(tokens) < 2 or tokens[1] not in TOOLS:
        return False
    tool = tokens[1]
    rest = tokens[2:]
    if not rest or rest[0] != "{":
        return False
    rest = rest[1:]
    if not rest or rest[-1] != "}":
        return False
    rest = rest[:-1]
    if not rest or len(rest) < 3 or rest[1] != ":":
        return False
    key, val = rest[0], rest[2]
    if key != ARG_KEYS[tool] or val not in ARG_VALUES.get(key, []):
        return False
    return len(rest) == 3 or (len(rest) == 7 and rest[3] == "," and rest[4] == ARG_KEYS[tool]
                              and rest[5] == ":" and rest[6] in ARG_VALUES[rest[4]])


def extract_call(tokens):
    if not valid_call(tokens):
        return None
    tool = tokens[1]
    d = {tokens[3]: tokens[5]}
    if len(tokens) > 8:
        d[tokens[7]] = tokens[9]
    return (tool, d)


def fsm_next(state, tok, tool=None):
    pos = state[0]
    if pos == 0:
        return ((1, None), tok) if tok == "fn:" else None
    if pos == 1:
        return ((2, None), tok) if tok in TOOLS else None
    if pos == 2:
        return ((3, None), tool) if tok == "{" else None
    if pos == 3:
        return ((4, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 4:
        return ((5, None), tool) if tok == ":" else None
    if pos == 5:
        return ((6, "v1"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 6:
        if tok == "}":
            return ((7, None), tool)
        if tok == ",":
            return ((8, None), tool)
        return None
    if pos == 8:
        return ((9, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 9:
        return ((10, None), tool) if tok == ":" else None
    if pos == 10:
        return ((11, "done"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 11:
        return ((7, None), tool) if tok == "}" else None
    return None


START = (0, None)
ACCEPT_POS = 7


def fsm_legal_tokens(state, tool):
    return [t for t in VOCAB if fsm_next(state, t, tool) is not None]


class Policy:
    def __init__(self):
        self.scores = {}
        self.mode = "raw"

    def _word_dist(self, w, last):
        sc = self.scores.get((w, last), {})
        z = sum(sc.values())
        if z == 0:
            return {t: 1.0 / len(VOCAB) for t in VOCAB}
        d = {t: (sc[t] / z) ** 1.25 if t in sc else 0.0 for t in VOCAB}
        tz = sum(d.values())
        return {t: p / tz for t, p in d.items()}

    def _dist(self, context, last):
        ds = [self._word_dist(w, last) for w in context]
        return {t: sum(d[t] for d in ds) / len(ds) for t in VOCAB}

    def sample(self, context, rng, mask=False, max_len=12):
        toks, state, tool, last = [], START, None, "<s>"
        for _ in range(max_len):
            if state[0] == ACCEPT_POS:
                return toks
            dist = self._dist(context, last)
            if mask:
                legal = ["fn:"] if state == START else fsm_legal_tokens(state, tool)
                dist = {t: dist[t] for t in legal}
                z = sum(dist.values())
                dist = ({t: 1.0 / len(legal) for t in legal} if z == 0
                        else {t: p / z for t, p in dist.items()})
            r, acc, chosen = rng.random(), 0.0, None
            for t, p in dist.items():
                acc += p
                if r <= acc:
                    chosen = t
                    break
            if chosen is None:
                chosen = list(dist)[0]
            nxt = fsm_next(state, chosen, tool)
            if nxt is None:
                state, tool = ((99, None), tool)
                toks.append(chosen)
                last = chosen
                continue
            toks.append(chosen)
            state, tool = nxt[0], (nxt[1] if nxt[1] is not None else tool)
            last = chosen
        return toks

    def observe_query(self, context, toks):
        for w in context:
            seq = ["<s>"] + toks
            for a, b in zip(seq, seq[1:]):
                self.scores.setdefault((w, a), {})
                self.scores[(w, a)][b] = self.scores[(w, a)].get(b, 0.0) + 1.0


def make_query(intent, rng):
    words = []
    for _ in range(2):
        words.append(rng.choice(UNIQUE[intent]) if rng.random() < 0.60
                     else rng.choice(SHARED))
    return words


def make_example(intent, rng, corrupt_p=0.0):
    key = ARG_KEYS[intent]
    if rng.random() < corrupt_p:
        key = rng.choice([k for k in ALL_KEYS if k != ARG_KEYS[intent]])
    vals = ARG_VALUES[key]
    return ["fn:", intent, "{", key, ":", vals[rng.randrange(len(vals))], "}"]


def trained_policy(rng, n_pairs=120):
    p = Policy()
    for _ in range(n_pairs):
        it = INTENTS[rng.randrange(3)]
        p.observe_query(make_query(it, rng), make_example(it, rng, 0.06))
    return p


rng = random.Random(7)
trained = trained_policy(rng)
untrained = Policy()
N = 300
cells = {}
for name, pol, ms in (("untrained_raw", untrained, False),
                      ("untrained_masked", untrained, True),
                      ("trained_raw", trained, False),
                      ("trained_masked", trained, True)):
    valid = tool_ok = arg_ok = 0
    for i in range(N):
        intent = INTENTS[i % 3]
        ctx = make_query(intent, rng)
        c = extract_call(pol.sample(ctx, rng, mask=ms))
        if c:
            valid += 1
            if c[0] == intent:
                tool_ok += 1
                key = ARG_KEYS[c[0]]
                if c[1].get(key) in ARG_VALUES[key]:
                    arg_ok += 1
    cells[name] = (valid / N, tool_ok / N, arg_ok / N)
print("=== F4 syntax-vs-semantics 2x2 (300 queries, sampled serving)")
for name, (v, t, a) in cells.items():
    print(f"{name}: valid={v:.4f} tool_correct={t:.4f} end_to_end={a:.4f}")
```

Read the grid by its columns. Validity: `0.0000 / 1.0000 / 0.4733 / 1.0000` - the mask is the only thing that produces a parseable call every time, and the trained-but-raw policy loses `52.67 percent` of its calls to syntax. The raw-trained losses are not one failure but three: the six percent of training pairs carry a wrong-key contamination (the malformed pair any scraped or self-instructed corpus contains), and at rare query words that contamination is all the evidence there is - the policy's mass on the legal continuation is zero and the raw sample wanders off the grammar; elsewhere the shared-word ambiguity splits the tool slot and the wrong tool poisons the rest of the call; and sampling means every ambiguous position re-rolls. Tool correctness: `0.0000 / 0.3033 / 0.4567 / 0.7167` - the untrained-masked cell is the section's sharpest warning, `1.0000` valid and `0.3033` correct, parseable garbage sitting at chance: the mask guarantees the envelope, never the letter inside. Note the raw cells' valid and tool-correct columns nearly coincide (`0.4733` vs `0.4567`) - a survivorship artifact, since a call only gets scored for tool choice if it parsed at all. End-to-end equals tool correctness here because the grammar already forces the value pool; the deployment column is `0.0000 / 0.3033 / 0.4567 / 0.7167`, and only the trained-plus-masked cell clears a third. One protocol note the corpus's own numbers obey: Section 3's `0.8917` is greedy, this fence's `0.7167` is the same policy sampled - the gap is the shared-word ambiguity paid on every sampled request instead of resolved by argmax.

## The Campaign: Four Stacks, One Ledger

The fifth fence prices the four deployable stacks on one 2,000-request campaign at the corpus's standard $0.24 per million tokens: raw, prompted, masked, and trained-plus-masked. The training bill is priced once, at real pair sizes - 11,000 pairs at 300 tokens each for 3 epochs, the APIBench recipe's own scale - while the serving lines are priced at the toy call's 7-to-11 tokens; the two scales are named separately and the comparison the ledger argues is within the serving column:

```python
import random

TOOLS = ["search", "calc", "weather"]
ARG_KEYS = {"search": "q", "calc": "x", "weather": "city"}
ARG_VALUES = {"q": ['"transformers"', '"quantization"', '"agents"'],
              "x": ['"42"', '"7"', '"3"'], "city": ['"tokyo"', '"paris"', '"ohio"']}
ALL_KEYS = sorted(set(ARG_KEYS.values()))
CALL_TOKENS = (["fn:", "{", "}", ",", ":", '"'] + TOOLS + ALL_KEYS
               + sorted({v for vals in ARG_VALUES.values() for v in vals}))
NOISE_TOKENS = ["the", "I", "maybe", "a", "is", "run", "stuff", "things", "data", "yes"]
VOCAB = []
for _t in CALL_TOKENS + NOISE_TOKENS:
    if _t not in VOCAB:
        VOCAB.append(_t)
UNIQUE = {"search": ["find", "docs", "paper", "tutorial", "lookup", "cite", "reference", "browse"],
          "calc": ["compute", "evaluate", "sum", "square", "multiply", "divide", "sqrt", "modulo"],
          "weather": ["forecast", "temperature", "humidity", "rain", "wind", "snow", "uv", "pressure"]}
SHARED = ["today", "now", "quick", "update", "current", "local"]
INTENTS = ["search", "calc", "weather"]


def valid_call(tokens):
    if not tokens or tokens[0] != "fn:":
        return False
    if len(tokens) < 2 or tokens[1] not in TOOLS:
        return False
    tool = tokens[1]
    rest = tokens[2:]
    if not rest or rest[0] != "{":
        return False
    rest = rest[1:]
    if not rest or rest[-1] != "}":
        return False
    rest = rest[:-1]
    if not rest or len(rest) < 3 or rest[1] != ":":
        return False
    key, val = rest[0], rest[2]
    if key != ARG_KEYS[tool] or val not in ARG_VALUES.get(key, []):
        return False
    return len(rest) == 3 or (len(rest) == 7 and rest[3] == "," and rest[4] == ARG_KEYS[tool]
                              and rest[5] == ":" and rest[6] in ARG_VALUES[rest[4]])


def extract_call(tokens):
    if not valid_call(tokens):
        return None
    tool = tokens[1]
    d = {tokens[3]: tokens[5]}
    if len(tokens) > 8:
        d[tokens[7]] = tokens[9]
    return (tool, d)


def fsm_next(state, tok, tool=None):
    pos = state[0]
    if pos == 0:
        return ((1, None), tok) if tok == "fn:" else None
    if pos == 1:
        return ((2, None), tok) if tok in TOOLS else None
    if pos == 2:
        return ((3, None), tool) if tok == "{" else None
    if pos == 3:
        return ((4, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 4:
        return ((5, None), tool) if tok == ":" else None
    if pos == 5:
        return ((6, "v1"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 6:
        if tok == "}":
            return ((7, None), tool)
        if tok == ",":
            return ((8, None), tool)
        return None
    if pos == 8:
        return ((9, None), tool) if tok == ARG_KEYS[tool] else None
    if pos == 9:
        return ((10, None), tool) if tok == ":" else None
    if pos == 10:
        return ((11, "done"), tool) if tok in ARG_VALUES[ARG_KEYS[tool]] else None
    if pos == 11:
        return ((7, None), tool) if tok == "}" else None
    return None


START = (0, None)
ACCEPT_POS = 7


def fsm_legal_tokens(state, tool):
    return [t for t in VOCAB if fsm_next(state, t, tool) is not None]


class Policy:
    def __init__(self):
        self.scores = {}
        self.mode = "raw"

    def _word_dist(self, w, last):
        sc = self.scores.get((w, last), {})
        z = sum(sc.values())
        if z == 0:
            return {t: 1.0 / len(VOCAB) for t in VOCAB}
        d = {t: (sc[t] / z) ** 1.25 if t in sc else 0.0 for t in VOCAB}
        tz = sum(d.values())
        return {t: p / tz for t, p in d.items()}

    def _dist(self, context, last):
        ds = [self._word_dist(w, last) for w in context]
        return {t: sum(d[t] for d in ds) / len(ds) for t in VOCAB}

    def sample(self, context, rng, mask=False, max_len=12):
        if self.mode == "prompted" and not mask:
            return self._sample_prompted(rng)
        toks, state, tool, last = [], START, None, "<s>"
        for _ in range(max_len):
            if state[0] == ACCEPT_POS:
                return toks
            dist = self._dist(context, last)
            if mask:
                legal = ["fn:"] if state == START else fsm_legal_tokens(state, tool)
                dist = {t: dist[t] for t in legal}
                z = sum(dist.values())
                dist = ({t: 1.0 / len(legal) for t in legal} if z == 0
                        else {t: p / z for t, p in dist.items()})
            r, acc, chosen = rng.random(), 0.0, None
            for t, p in dist.items():
                acc += p
                if r <= acc:
                    chosen = t
                    break
            if chosen is None:
                chosen = list(dist)[0]
            nxt = fsm_next(state, chosen, tool)
            if nxt is None:
                state, tool = ((99, None), tool)
                toks.append(chosen)
                last = chosen
                continue
            toks.append(chosen)
            state, tool = nxt[0], (nxt[1] if nxt[1] is not None else tool)
            last = chosen
        return toks

    def _sample_prompted(self, rng):
        eps = 0.02
        def nz(t):
            return t if rng.random() > eps else rng.choice(NOISE_TOKENS)
        tool = rng.choice(TOOLS)
        key = rng.choice(ALL_KEYS)
        val = rng.choice(ARG_VALUES[key])
        return ["fn:", nz(tool), "{", nz(key), ":", nz(val), "}"]

    def observe_query(self, context, toks):
        for w in context:
            seq = ["<s>"] + toks
            for a, b in zip(seq, seq[1:]):
                self.scores.setdefault((w, a), {})
                self.scores[(w, a)][b] = self.scores[(w, a)].get(b, 0.0) + 1.0


def make_query(intent, rng):
    words = []
    for _ in range(2):
        words.append(rng.choice(UNIQUE[intent]) if rng.random() < 0.60
                     else rng.choice(SHARED))
    return words


def make_example(intent, rng, corrupt_p=0.0):
    key = ARG_KEYS[intent]
    if rng.random() < corrupt_p:
        key = rng.choice([k for k in ALL_KEYS if k != ARG_KEYS[intent]])
    vals = ARG_VALUES[key]
    return ["fn:", intent, "{", key, ":", vals[rng.randrange(len(vals))], "}"]


def trained_policy(rng, n_pairs=120):
    p = Policy()
    for _ in range(n_pairs):
        it = INTENTS[rng.randrange(3)]
        p.observe_query(make_query(it, rng), make_example(it, rng, 0.06))
    return p


rng = random.Random(7)
trained = trained_policy(rng)
base = Policy()
pro = Policy()
pro.mode = "prompted"
N = 2000
stacks = {}
for name, pol, ms, max_retries in (("raw", base, False, 4),
                                   ("prompted", pro, False, 4),
                                   ("masked", base, True, 1),
                                   ("trained_masked", trained, True, 1)):
    valid = tool_ok = e2e = toks = retries = 0
    for i in range(N):
        intent = INTENTS[i % 3]
        ctx = make_query(intent, rng)
        attempt = 1
        while True:
            out = pol.sample(ctx, rng, mask=ms)
            toks += len(out)
            c = extract_call(out)
            if c:
                valid += 1
                if c[0] == intent:
                    tool_ok += 1
                    key = ARG_KEYS[c[0]]
                    if c[1].get(key) in ARG_VALUES[key]:
                        e2e += 1
                break
            retries += 1
            if attempt >= max_retries:
                break
            attempt += 1
    stacks[name] = dict(valid=valid / N, tool_ok=tool_ok / N, e2e=e2e / N,
                        tokens=toks, retries=retries)
print("=== F5 campaign ledger (2000 requests, $0.24/Mtok)")
for name, s in stacks.items():
    cost = s["tokens"] / 1e6 * 0.24
    print(f"{name}: valid={s['valid']:.4f} tool_ok={s['tool_ok']:.4f} e2e={s['e2e']:.4f} "
          f"tokens={s['tokens']} retries={s['retries']} cost=${cost:.4f}")
train_tokens = 11000 * 300 * 3
print(f"train_bill: pairs=11000 tokens={train_tokens} "
      f"cost=${train_tokens / 1e6 * 0.24:.4f} (one-time)")
```

The ledger's rows, worst to best: raw serves `96,000` tokens for `0.0000` end-to-end - $0.0230 spent, nothing delivered, `8,000` retries all dead. Prompted delivers `0.2585` at `34,223` tokens ($0.0082) - real, and still three-quarters of requests either fail or land the wrong tool. Masked delivers `0.3375` at `17,880` tokens ($0.0043) - the cheapest untrained line on the board, and still two-thirds wrong, because Section 4's warning is an economic fact: a guarantee about syntax cannot buy correctness. Trained-plus-masked delivers `0.7225` at `14,052` tokens ($0.0034) - the best row on the board is also the cheapest, 2.1 times the next-best end-to-end rate at 21 percent fewer tokens. The one-time bill for that row prints under it: `11,000` pairs at `300` tokens for `3` epochs is `9,900,000` tokens, $2.3760 - priced at real pair sizes, against serving lines priced at toy sizes, which is why the ledger's argument is the end-to-end column and not a token break-even: the two cheapest rows differ by less than a tenth of a cent per batch of 2,000, while the untrained stacks' correctness ceiling of `0.3375` is not purchasable upward at any retry budget. That is the campaign's whole shape: the mask's cost is zero per request and buys parseability every request; the training bill is paid once and buys correctness every request after; and the stack that pays neither delivers a number no retry ladder can rescue.

## Known Failure Modes

- **Masking an untrained model and shipping it.** The untrained-masked cell is `1.0000` valid, `0.3033` correct - every call parses and a third of them are right, exactly chance. Constrained decoding is a syntax guarantee; reading its valid rate as a quality metric is the section's core trap.
- **Trusting prompt-only compliance.** `0.7940` valid feels deployable until the tool list changes: the prompt's enumeration is a snapshot that goes stale, and base-model hallucination rates (Gorilla's `36.55/37.16/78.65` percent across three hubs) are what ungrounded tool choice does at scale. The mask recompiles from the grammar; the prompt rots.
- **Reading benchmark numbers without their serving temperature.** Section 3's `0.8917` and Section 4's `0.7167` are the same policy under greedy and sampled serving. Quoting either without the protocol makes cross-paper comparisons meaningless - ToolEval-style tool accuracy and AST accuracy numbers are not in the same unit.
- **Assuming clean pair data.** The six percent wrong-key contamination in this lesson's pairs is deliberately mild; real scraped and self-instructed corpora are worse (Gorilla's self-instruct generation, ToolLLM's pipeline - both autogenerate their queries). Contamination at rare query words zeroes the evidence for the legal continuation; the mask's fallback keeps such calls parseable while the wrong binding survives into production.
- **Confusing the two scales in the ledger.** The training bill is priced at real 300-token pairs; the serving lines at the toy's 7-to-11-token calls. The ledger argues the shape (one-time correctness bill vs per-request syntax guarantee), not a token-for-token break-even.

## Summary

One toy grammar, five fences, and the two levers separate cleanly. The grammar compiles to a twelve-state FSM whose legal sets run `[1, 3, 1, 1, 1, 3, 2]` - 3 of 31 tokens at the widest step - and masking alone flips validity `0.0000` to `1.0000` at the lowest token bill (`8.92` per request). Prompting for format is the middle rung: `0.7940` valid bought with `1.454` retries per request, a mechanism that rots with the tool list and cannot stop the model inventing tools the grammar has never heard of. Training is the only lever that moves correctness: 120 pairs lift greedy tool accuracy `0.3333` to `0.8917`, plateauing where the pair vocabulary's coverage ends - shared ambiguous words set the ceiling, and more epochs do not move it. The 2x2 grid prices the levers' orthogonality: `1.0000` valid at `0.3033` correct for mask-without-training, `0.4733` valid at `0.4567` correct for training-without-mask, and `1.0000` at `0.7167` for their product - the only deployable cell. The campaign ledger closes it: the untrained stacks' failure is per-request (`0.0000` and `0.2585` end-to-end), the mask's guarantee is per-request and free, and the $2.3760 one-time training bill buys the board's best row - `0.7225` end-to-end at `14,052` tokens, cheapest and correct.

## References

- Willard, B. T., and Louf, R. "Efficient Guided Generation for Large Language Models." arXiv 2307.09702 (2023) - the FSM reformulation: grammar-constrained generation as per-step masking, model-agnostic, from regex or CFG to logit mask.
- Dong, Y., Ruan, C., Cai, Y., Lai, J., Xu, Z., Zhao, Y., and Chen, T. "XGrammar: Flexible and Efficient Structured Generation Engine for Large Language Models." arXiv 2411.15100 (2024), MLSys 2025 - the context-independent/context-dependent vocabulary partition, the persistent stack, and the near-zero-overhead production check.
- Patil, S., Zhang, T., Wang, X., and Gonzalez, J. E. "Gorilla: Large Language Model Connected with Massive APIs." arXiv 2305.15334 (2023) - APIBench's 1,645 APIs and 11,000+ self-instruct pairs, the AST accuracy and hallucination tables, and the retriever-aware training gains.
- Qin, Y., et al. "ToolLLM: Facilitating Large Language Models to Master 16,000+ Real-world APIs." arXiv 2307.16789 (2023) - the 16,464-API / 49-category corpus, the three-stage instruction construction, DFSDT, and the ToolLLaMA evaluation.

## Next Steps

- **Next Module:** [7201](../7200-tools/7201-Tool-Calling.md) owns the registry discipline that decides what the grammar compiles from - schema versioning and contract checks are the upstream of every mask this lesson builds.
- [1405](../../phase1-infra/1400-llmops/1405-SGLang.md) serves these masks: the `xgrammar` backend flag and structured-output API are the production end of Section 1's mechanism.
- [5205](../../phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md) trains the same correctness this lesson's pairs supply, but from verifiable rewards instead of demonstrations - the alignment-side answer to "where does the right call come from."
- [7105](./7105-Reflection-and-Self-Correction.md) owns what happens when a call fails anyway: the in-run detection and correction patterns that wrap this lesson's serving stack.

**Estimated Time:** 4 hours (1 hour reading, 3 hours hands-on with the fences)
