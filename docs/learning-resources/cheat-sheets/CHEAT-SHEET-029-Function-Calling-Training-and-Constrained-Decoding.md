---
Document ID: CHEAT-SHEET-029
Title: "CHEAT-SHEET-029: Function Calling Training and Constrained Decoding"
Last Updated: 2026-10-15
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'function-calling', 'constrained-decoding', 'agents', 'training']
---

# CHEAT-SHEET-029: Function Calling Training and Constrained Decoding

**Quick Reference for:** the grammar-to-mask mechanism and its per-state legal-set ladder, prompting versus constraining, the Gorilla pair-training recipe and its ~0.89 plateau, the syntax-versus-semantics 2x2, the campaign ledger with the one-time $2.3760 train bill, and the five known failure modes that keep a 1.0000-valid model from shipping wrong calls. CHEAT-SHEET-013 owns the producer side - schema-constrained structured output with Outlines and XGrammar; CHEAT-SHEET-027 owns the client and registry contract; this sheet owns the two layers underneath both - the mask that makes invalid calls structurally impossible at inference, and the pair-training that makes valid calls correct. A mask without training ships parseable garbage at 1.0000 validity and 0.3033 tool-correctness; training without a mask burns retries against a 0.0000 raw-validity floor - you need both, and this page is the operator map for both.

## Grammar to Mask: the Mechanism

A 31-token vocabulary (21 call tokens, 10 noise tokens) over a three-tool calling language `fn: TOOL { KEY : VALUE }`. A 12-state FSM accepts exactly the well-formed calls; walking the legal set along one canonical path gives per-state sizes **[1, 3, 1, 1, 1, 3, 2]** - the widest step offers 3 of 31 tokens, a 9.68% pass rate at the grammar's most generous moment. Unconstrained sampling from a format-unaware policy lands **0/2000 = 0.0000** valid calls; the same policy with FSM masking lands **2000/2000 = 1.0000**.

```text
fn:            -> [fn:]                                              1 of 31
<tool>         -> [calc, search, weather]                            3 of 31
{              -> [{]                                                1 of 31
<key>          -> [q]        (search: q / calc: x / weather: city)   1 of 31
:              -> [:]                                                1 of 31
<value>        -> ["agents", "quantization", "transformers"]         3 of 31
close          -> [",", "}"]                                         2 of 31
```

Note the toy's limitation honestly: on a two-pair grammar the XGrammar context-independent partition is empty - the acceleration that matters on production vocabularies has nothing to accelerate here. Measure the partition's effect on your real vocab, not on the toy.

## Prompting Is Not Constraining

| mode | valid_rate | tokens/request | retries/request |
|---|---|---|---|
| raw | 0.0000 | 48.00 | 3.000 |
| prompted | 0.7940 | 17.18 | 1.454 |
| masked | 1.0000 | 8.92 | 0.000 |

The format-unaware base model with four attempts and retry-budget burns 48 tokens per request and still scores 0.0000 - every attempt dead. Prompting with the format recovers 0.7940 at 1.454 retries (a 0.02 eps of token noise keeps it honest); masking recovers 1.0000 at 8.92 tokens and zero retries. prompt_gain **+0.7940**, mask_gain **+1.0000** - the mask closes the door, the prompt only asks nicely. Gorilla's hallucination numbers are the same lesson at scale: GPT-4 invents packages on **36.55%** (TorchHub), **37.16%** (TensorHub) and **78.65%** (Hugging Face) of requests - a model that sounds compliant is not constrained.

## Training the Capability: the Gorilla Recipe

Pair-training the same tiny policy - 20 pairs per epoch, 600 held-out eval queries, masked greedy serving - walks tool accuracy **0.3333 -> 0.6050 -> 0.8183 -> 0.8867 -> 0.8783 -> 0.8883 -> 0.8917** across **0..120 pairs**:

| pairs seen | tool accuracy |
|---|---|
| 0 | 0.3333 |
| 20 | 0.6050 |
| 40 | 0.8183 |
| 60 | 0.8867 |
| 80 | 0.8783 |
| 100 | 0.8883 |
| 120 | 0.8917 |

The 0.8867 -> 0.8783 dip is not noise - greedy decoding is deterministic; it is the model re-balancing after the 6%-wrong-key corruption baked into the recipe (`corrupt_p=0.06` - real scraped pairs are dirtier). The ~0.89 plateau is the query-vocabulary ceiling: 60% of eval words are unique per intent (an 8-word pool) and 40% are shared (a 6-word pool), so past 80 pairs the data cannot disambiguate further. Gorilla's real numbers: APIBench holds **1,645 APIs** (TorchHub 95, TensorHub 696, Hugging Face 925), **11,000+ pairs**; LLaMA-7B fine-tuned on them reaches **59.13 / 71.68 / 83.79 AST** against GPT-4 zero-shot's **38.70 / 19.80 / 18.20**, with hallucination dropping to **6.98 / 10.95 / 5.40** - and a retriever-aware stack adds **+12.37% / +23.46%**. ToolLLM scales the corpus to **16,464 APIs across 49 categories**, where ToolLLaMA matches ChatGPT.

## Syntax vs Semantics: the 2x2

| cell | valid | tool_correct | end_to_end |
|---|---|---|---|
| untrained_raw | 0.0000 | 0.0000 | 0.0000 |
| untrained_masked | 1.0000 | 0.3033 | 0.3033 |
| trained_raw | 0.4733 | 0.4567 | 0.4567 |
| trained_masked | 1.0000 | 0.7167 | 0.7167 |

```text
                  valid   tool_correct   end_to_end
untrained_raw     0.0000  0.0000         0.0000
untrained_masked  1.0000  0.3033         0.3033
trained_raw       0.4733  0.4567         0.4567
trained_masked    1.0000  0.7167         0.7167
```

The sharpest warning in this sheet is the untrained_masked row: **1.0000 valid, 0.3033 tool-correct** - a masked untrained model is a garbage factory with a spotless QA certificate. The grammar forces the value pool, so once the tool is right the argument is right too and end_to_end equals tool_correct in every trained cell. trained_raw loses 52.67% of its syntax (0.4733 valid) and drags correctness down with it. Protocol note: F3's 0.8917 is *greedy*, F4's 0.7167 is *sampled* - the same policy, so read benchmark numbers at the serving temperature they were measured at, or not at all.

## The Campaign Ledger and the Train Bill

2000 requests, $0.24/Mtok:

| stack | e2e | tokens | retries | cost |
|---|---|---|---|---|
| raw | 0.0000 | 96,000 | 8,000 | $0.0230 |
| prompted | 0.2585 | 34,223 | 3,295 | $0.0082 |
| masked | 0.3375 | 17,880 | 0 | $0.0043 |
| trained_masked | 0.7225 | 14,052 | 0 | $0.0034 |

The trained+masked stack is simultaneously the best and the cheapest: **2.1x** the next-best end-to-end on 21% fewer tokens. Raw's 8,000 retries are all dead attempts - money spent buying nothing, the only stack where the cost column is pure waste. The mask-only ceiling (0.3375) cannot be bought past with retries - correctness lives in the data, not the retry budget. And the training bill: 11,000 pairs x 300 tokens x 3 epochs = **9.9M tokens = $2.3760, one-time**. The one-time charge that buys every subsequent request its 2.1x.

## Known Failure Modes

| failure | lesson |
|---|---|
| Ship mask + untrained model | 1.0000 valid / 0.3033 correct - parseable is not correct |
| Trust prompt-only compliance | 0.7940 rots as the tool list evolves; the format war is lost at inference, not in the system prompt |
| Read benchmarks at the wrong temperature | 0.8917 greedy vs 0.7167 sampled - same policy, different serving; record the protocol |
| Assume clean pair data | 6% wrong-key corruption already leaves a visible dent; scraped pairs need validation |
| Mix the ledger's two scales | the toy call is 7-11 tokens, the pair is 300 - price training at pair-scale, campaigns at call-scale |

## References

- Willard & Louf, *Efficient Guided Generation for Large Language Models* (Outlines), arXiv:2307.09702
- Dong et al., *XGrammar: Flexible and Efficient Structured Generation Engine* (MLSys 2025), arXiv:2411.15100
- Patil et al., *Gorilla: An LLM Connected with Massive APIs* (APIBench), arXiv:2305.15334
- Qin et al., *ToolLLM: Facilitating Large Language Models to Master 16000+ Real-world APIs*, arXiv:2307.16789

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Perfect validity, ~chance tool-correctness | mask shipped over an untrained policy | pair-train before shipping the mask (0.3033 -> 0.7167) |
| Validity decays as tools are added | prompt-only format discipline | move the format into the grammar; the prompt is not a constraint |
| Benchmark number unreproducible in prod | serving-temperature mismatch (greedy vs sampled) | pin and publish the decoding protocol with every score |
| Trained model stuck below ~0.9 | query-vocabulary ceiling (60/40 unique/shared) | widen the intent vocabulary; more pairs cannot fix a ceiling |
| Training cost quoted absurdly high | two-scale ledger confusion | 9.9M training tokens at pair scale is $2.3760 one-time, not per-campaign |
| Mask accelerates nothing | context-independent partition empty on the toy grammar | measure the partition on the production vocabulary |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7106: Function-Calling Training and Constrained Decoding](../../phases/phase7-agentic/7100-architecture/7106-Function-Calling-Training-and-Constrained-Decoding.md) | this sheet's source module - the full mechanism and recipe |
| [Module 1405: SGLang](../../phases/phase1-infra/1400-llmops/1405-SGLang.md) | the serving-side contract - xgrammar backend flag |
| [Module 5205: GRPO-RLVR](../../phases/phase5-finetuning/5200-alignment/5205-GRPO-RLVR.md) | the alignment-side training - verifiable rewards beyond pairs |
| [CHEAT-SHEET-013: Structured Output and Function Calling](CHEAT-SHEET-013-Structured-Output-Function-Calling.md) | the producer side - Outlines / XGrammar 2x2 |

```python
"""CHEAT-SHEET-029 fence: function-calling training + constrained decoding.

Merged from module 7106's five fences; each section re-seeds Random(7) so the
canonical numbers match the module's own run verbatim.
"""
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
        return ((1, None), None) if tok == "fn:" else None
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


# --- F1 grammar-to-mask mechanism
rng1 = random.Random(7)
n_states = fsm_explore()
p_raw = Policy()
p_msk = Policy()
N1 = 2000
raw_valid = sum(1 for _ in range(N1) if valid_call(p_raw.sample(["find"], rng1)))
mask_valid = sum(1 for _ in range(N1) if valid_call(p_msk.sample(["find"], rng1, mask=True)))
path = [START, (1, None), (2, None), (3, None), (4, None), (5, None), (6, "v1")]
path_sizes = [1 if st == START else len(fsm_legal_tokens(st, "search")) for st in path]
print("=== F1 grammar-to-mask mechanism")
print(f"vocab_size={len(VOCAB)} call_tokens={len(CALL_TOKENS)} noise_tokens={len(NOISE_TOKENS)}")
print(f"fsm_states={n_states} per_state_legal_sizes={path_sizes}")
print(f"unconstrained_valid={raw_valid}/{N1}={raw_valid / N1:.4f}")
print(f"masked_valid={mask_valid}/{N1}={mask_valid / N1:.4f}")
print(f"typical_allowed_step={max(path_sizes)} of {len(VOCAB)} = {max(path_sizes) / len(VOCAB):.4f}")

# --- F2 prompting-is-not-constraining
rng2 = random.Random(7)
N2 = 2000
results = {}
for mode in ("raw", "prompted", "masked"):
    p = Policy()
    p.mode = "prompted" if mode == "prompted" else "raw"
    ms = mode == "masked"
    valid = retry_tokens = retry_count = 0
    for _ in range(N2):
        ctx = make_query("search", rng2)
        toks = p.sample(ctx, rng2, mask=ms)
        attempts, ok = 1, valid_call(toks)
        while not ok and attempts < 4:
            retry_tokens += len(toks)
            retry_count += 1
            toks = p.sample(ctx, rng2, mask=ms)
            attempts += 1
            ok = valid_call(toks)
        if ok:
            valid += 1
        retry_tokens += len(toks)
    results[mode] = (valid / N2, retry_tokens / N2, retry_count / N2)
print("=== F2 prompting-is-not-constraining (format-unaware base model)")
for mode, (v, tok, rc) in results.items():
    print(f"{mode}: valid_rate={v:.4f} tokens_per_request={tok:.2f} retries_per_request={rc:.3f}")
v_raw, v_pro, v_msk = results["raw"][0], results["prompted"][0], results["masked"][0]
print(f"prompt_gain={v_pro - v_raw:+.4f} mask_gain={v_msk - v_raw:+.4f}")

# --- F3 capability-training walk
rng3 = random.Random(7)
p3 = Policy()
per_epoch = 20
gold = [(it, make_query(it, rng3)) for it in INTENTS for _ in range(200)]


def tool_acc(pol):
    hit = 0
    for intent, ctx in gold:
        c = extract_call(pol.sample_greedy(ctx))
        if c and c[0] == intent:
            hit += 1
    return hit / len(gold)


walk = [tool_acc(p3)]
for ep in range(6):
    for _ in range(per_epoch):
        it = INTENTS[rng3.randrange(3)]
        p3.observe_query(make_query(it, rng3), make_example(it, rng3, 0.06))
    walk.append(tool_acc(p3))
print("=== F3 capability-training walk (600 eval queries, masked greedy serving)")
print("pairs_seen: " + " ".join(str(i * per_epoch) for i in range(7)))
print("tool_accuracy: " + " ".join(f"{a:.4f}" for a in walk))

# --- F4 syntax-vs-semantics 2x2
rng4 = random.Random(7)
trained4 = trained_policy(rng4)
untrained4 = Policy()
N4 = 300
cells = {}
for name, pol, ms in (("untrained_raw", untrained4, False),
                      ("untrained_masked", untrained4, True),
                      ("trained_raw", trained4, False),
                      ("trained_masked", trained4, True)):
    valid = tool_ok = arg_ok = 0
    for i in range(N4):
        intent = INTENTS[i % 3]
        ctx = make_query(intent, rng4)
        c = extract_call(pol.sample(ctx, rng4, mask=ms))
        if c:
            valid += 1
            if c[0] == intent:
                tool_ok += 1
                key = ARG_KEYS[c[0]]
                if c[1].get(key) in ARG_VALUES[key]:
                    arg_ok += 1
    cells[name] = (valid / N4, tool_ok / N4, arg_ok / N4)
print("=== F4 syntax-vs-semantics 2x2 (300 queries, sampled serving)")
for name, (v, t, a) in cells.items():
    print(f"{name}: valid={v:.4f} tool_correct={t:.4f} end_to_end={a:.4f}")

# --- F5 campaign ledger
rng5 = random.Random(7)
trained5 = trained_policy(rng5)
base5 = Policy()
pro5 = Policy()
pro5.mode = "prompted"
N5 = 2000
stacks = {}
for name, pol, ms, max_retries in (("raw", base5, False, 4),
                                   ("prompted", pro5, False, 4),
                                   ("masked", base5, True, 1),
                                   ("trained_masked", trained5, True, 1)):
    valid = tool_ok = e2e = toks = retries = 0
    for i in range(N5):
        intent = INTENTS[i % 3]
        ctx = make_query(intent, rng5)
        attempt = 1
        while True:
            out = pol.sample(ctx, rng5, mask=ms)
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
    stacks[name] = dict(valid=valid / N5, tool_ok=tool_ok / N5, e2e=e2e / N5,
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

```text
=== F1 grammar-to-mask mechanism
vocab_size=31 call_tokens=21 noise_tokens=10
fsm_states=12 per_state_legal_sizes=[1, 3, 1, 1, 1, 3, 2]
unconstrained_valid=0/2000=0.0000
masked_valid=2000/2000=1.0000
typical_allowed_step=3 of 31 = 0.0968
=== F2 prompting-is-not-constraining (format-unaware base model)
raw: valid_rate=0.0000 tokens_per_request=48.00 retries_per_request=3.000
prompted: valid_rate=0.7940 tokens_per_request=17.18 retries_per_request=1.454
masked: valid_rate=1.0000 tokens_per_request=8.92 retries_per_request=0.000
prompt_gain=+0.7940 mask_gain=+1.0000
=== F3 capability-training walk (600 eval queries, masked greedy serving)
pairs_seen: 0 20 40 60 80 100 120
tool_accuracy: 0.3333 0.6050 0.8183 0.8867 0.8783 0.8883 0.8917
=== F4 syntax-vs-semantics 2x2 (300 queries, sampled serving)
untrained_raw: valid=0.0000 tool_correct=0.0000 end_to_end=0.0000
untrained_masked: valid=1.0000 tool_correct=0.3033 end_to_end=0.3033
trained_raw: valid=0.4733 tool_correct=0.4567 end_to_end=0.4567
trained_masked: valid=1.0000 tool_correct=0.7167 end_to_end=0.7167
=== F5 campaign ledger (2000 requests, $0.24/Mtok)
raw: valid=0.0000 tool_ok=0.0000 e2e=0.0000 tokens=96000 retries=8000 cost=$0.0230
prompted: valid=0.7970 tool_ok=0.2585 e2e=0.2585 tokens=34223 retries=3295 cost=$0.0082
masked: valid=1.0000 tool_ok=0.3375 e2e=0.3375 tokens=17880 retries=0 cost=$0.0043
trained_masked: valid=1.0000 tool_ok=0.7225 e2e=0.7225 tokens=14052 retries=0 cost=$0.0034
train_bill: pairs=11000 tokens=9900000 cost=$2.3760 (one-time)
```
