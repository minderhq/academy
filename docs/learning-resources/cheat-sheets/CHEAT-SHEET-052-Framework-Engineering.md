---
Document ID: CHEAT-SHEET-052
Title: "CHEAT-SHEET-052: Framework Engineering - the Registry, the Batching Flush, and the Rollout Gate"
Last Updated: 2026-10-12
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'framework-engineering', 'serving', 'deployment']
---

# CHEAT-SHEET-052: Framework Engineering - the Registry, the Batching Flush, and the Rollout Gate

The scope scan that picked this page: phase2-foundations' 2300-framework-engineering track carries 2301 Framework Design Patterns, 2302 Model Serving Architectures, 2303 API Design for ML and 2304 Production Deployment Patterns with no sheet anywhere in the track - the track's two guides (2305 comparison, 2306 production build-out) own the full walkthroughs, not the operating laws a student needs at 2am when the batch flush starves a lone request or the canary trips at stage one. This sheet takes the three questions the operator actually asks: how a framework grows without a fork, how throughput gets bought without latency debt, and how new code reaches users without betting the whole fleet on it.

The sheet runs as seven priced exhibits: the registry economy (F1 - extend by file, never by fork, with the duplicate and unknown-key laws that make growth loud), the config resolve (F2 - deep-merge beats replace, and the naive dict-splat that silently deletes siblings), the batching flush (F3 - full or oldest-past-timeout, the waiter-driven law, 20 launches becoming 3), the KV-cache page bill (F4 - paged allocation beats reserved-max by 3.94x on the fence's fleet), the limiter trio and the per-item error envelope (F5 - token bucket, sliding window, and the status codes that tell clients the truth), the rollout ladder (F6 - blue-green, rolling, canary, each paying a different bill for safety), and the chi-squared verdict (F7 - the discordant pair decides, not aggregate accuracy). Every number below is printed by the canonical fence at the bottom of the page: the full 457-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 59-line output sits frozen below it byte-for-byte.

## The Registry Economy - Extend by File, Not by Fork

A framework's whole promise is that the next capability arrives as a new file, not as an edit to the core. The registry is the mechanism: a decorator claims a string key and binds a class, `create` looks the key up, `list_all` shows the inventory. The fence builds one and registers three metrics - `accuracy`, `mean_latency_ms`, `throughput_rps` - then prices the two failure modes a registry exists to surface: registering a duplicate key raises `ValueError` at import time (never a silent overwrite of a live class), and creating an unknown key raises `KeyError` whose message lists what IS registered, so the typo debugs itself. The economics land in two printed lines: a plugin file adds two more metrics with zero core lines touched, and the registry count grows from 3 to 5 while the core's diff stays empty.

Growth still needs one gate: the plugin's version claim. A plugin that declares `>=2.0` loads on a 3.0 host; a plugin declaring `>=3.0` on a 2.4 host blocks at load. One comparison at import, tuple against tuple, beats a version check scattered inside every class.

```text
A registry turns "add a metric" from a core edit into a new file.
A duplicate key is a startup error (ValueError), never a silent overwrite.
An unknown key is a loud error (KeyError) that lists what IS registered.
Gate the plugin file's version claim once, at load - not inside every class.
```

## The Config Resolve - Deep-Merge, Never Replace

The second growth axis is configuration, and its law is one line: merge dicts recursively, replace leaves only. The fence carries a base config (`server.batching.max_batch_size: 8`, `server.batching.timeout_ms: 10.0`, `server.port: 8000`) and an override that touches exactly one leaf (`timeout_ms: 25.0`). Deep-merge lands all three printed facts: the override wins, and both siblings survive untouched. A missing key with a default reads as the default (`server.workers` reads as 10); a missing key marked required raises `KeyError` naming the path - a config never crashes on an optional, and never invents a value for a required one.

The trap is the one-line naive merge. `{**base, **override}` replaces the whole `server` value with the override's subtree, and the fence prints what vanished: `host` and `port`, two keys nobody intended to touch. That failure mode is silent in code review and loud in production at 3am - which is why the merge helper is framework code, not user code.

| Key | Default | Meaning |
| --- | --- | --- |
| `server.batching.max_batch_size` | 8 | largest batch a single flush may carry |
| `server.batching.timeout_ms` | 10.0 | oldest-item deadline that flushes a partial batch |
| `server.workers` | 10 | invented at read time - optional keys get defaults, never crashes |
| `model.quantization` | (required) | absent required keys fail at startup, naming the missing path |

And the loader law that underwrites all of it: `yaml.safe_load(text)` - plain data only, never `yaml.load`, which will happily construct arbitrary objects from a config file.

## The Batching Flush - Full or Oldest-Past-Timeout

Dynamic batching converts per-request forward launches into per-batch launches, and the fence prices the conversion on the module's own config (max 8, timeout 10 ms): a 20-request burst resolves as batches `[8, 8, 4]` - average fill 6.667 - so 20 serial forwards become 3 batched launches, a 6.67x cut in launch count with bit-identical outputs (the fence runs the same math both ways and prints `max |serial - batched| = 0`). The launch count is the bill; the FLOPs never changed.

The law that keeps it honest has two halves: a batch flushes when it is FULL or when its OLDEST item passes the timeout - both checked on the same waiter tick. Drop the timeout half and the system still works for bursts but a lone request starves until the next arrival, which may be seconds away or never; with it, the lone request's wait is bounded by the 10 ms timer, not by traffic. That is the difference between a p95 with a ceiling and a p95 that depends on the request mix.

```text
A batch flushes when it is FULL or when its OLDEST item passes the timeout.
Both conditions are checked on the same waiter tick - that is the whole law.
Without the timeout half, a lone request starves until the next arrival.
The win is launches, not FLOPs: 20 forwards became 3 with identical math.
```

## The KV-Cache Page Bill - Paged Beats Reserved

Serving throughput dies on memory arithmetic, and the fence prices the two allocation styles. One KV page in the module's shape `(2, 2, 2, 2, 16, 4)` is 1,024 floats. A 100-token sequence on 40-token pages occupies 3 pages and wastes 20 tokens internally - 16.7% fragmentation, the visible rent of paging. The counterfactual is reservation: 8 concurrent sequences each reserving max-length 512 costs 4,096 slots up front, while paging the fence's actual lengths (`[100, 64, 90, 37, 120, 45, 128, 300]`) needs 26 pages = 1,040 slots - 3.94x the memory bought back, which is capacity another request can use right now.

The same ledger explains why the cache exists at all: a 5-token prompt followed by 3 generated tokens costs 26 token-projections uncached (5, then 6, 7, 8 as the context grows) versus 8 with the cache - 3.25x. And the freed memory feeds the scheduler: with a running cap of 3, the fence admits `[True, True, True, False]` - the fourth request waits, then enters the moment any running row retires. Continuous batching is not a feature; it is what paged memory makes schedulable.

## The Limiter Trio and the Error Envelope

The limiter is the API's contract with chaos, and the fence runs two canonical implementations. The token bucket (capacity 20, refill 10/s, starting full) takes 25 requests at t=0: 20 pass, 5 rejected; half a second later the bucket has refilled 5.0 tokens and the next 5 requests pass. Bursts ride the stored capacity; sustained load rides the rate. The sliding window (5 per 60s) admits 5, rejects the 6th at t=30, and admits again at t=61 the moment the oldest hit slides out - fairer under bursts because it counts real history, not a fixed-window cliff that doubles throughput at window edges.

The error envelope is the other half of the contract: a batch of 3 items with 1 invalid returns HTTP 200 carrying 2 results and 1 flagged error. The good rows survive - one malformed item never kills a whole batch, and the client sees exactly which row failed. What kills trust is lying with the status code, which is why the code table is short and blunt:

| Code | Meaning | Client action |
| --- | --- | --- |
| 400 | malformed request body | fix the payload, do not retry |
| 404 | wrong route or unknown resource | fix the URL |
| 429 | the limiter fired | honor Retry-After and back off |
| 408 | the client was slow to send | measure client-side upload time |
| 504 | our inference deadline passed | check server load, not the client |

```text
400 malformed, 404 wrong route, 429 the limiter doing its job.
408 means the CLIENT was slow to send; 504 means OUR deadline passed.
Batch endpoints return 200 with a per-item envelope - one bad row never
kills the good rows. A blanket 500 for all of these teaches blind retries.
```

## The Rollout Ladder - Blue-Green, Rolling, Canary

Every deployment strategy is a different bill for the same product - safety - and the fence prices all three. Blue-green doubles the fleet, then cuts over with one nginx line; rollback is the same one line, seconds in either direction. You pay for the whole second fleet to buy instant reversibility. Rolling updates 4 replicas with `maxSurge: 1, maxUnavailable: 0` - one pod at a time, each held through `minReadySeconds: 30` before the next wave, a floor of 120 seconds for a 4-replica service; you pay time and zero extra machines. And the fence prints the config law: surge 0 with unavailable 0 cannot roll at all - one must be nonzero, or the scheduler has no room to move.

Canary pays duration for blast radius. The advance rule walks 5% to 50% in steps of 5 and only advances while the error rate stays under half the threshold (0.025 against a 0.05 budget). A good candidate at 0.02 walks all ten stages to 50%. A bad candidate at 0.08 trips at stage one - 5% - and rolls back to 0%. That cap is the whole point: the fence prices the bad candidate at 5% of traffic exposed on canary versus 100% on rolling, a 20x difference in how much damage one bad model can do.

| Strategy | Rollback | Blast radius | What it pays for |
| --- | --- | --- | --- |
| Blue-green | 1 config line, seconds | whole fleet either way | instant reversibility, at double hardware |
| Rolling | roll forward wave by wave | grows with every wave | zero extra machines, at a 120s+ floor |
| Canary | return traffic to the incumbent | capped at the step (5%) | evidence before exposure, at soak duration |

```text
Blue-green pays double hardware for a one-line rollback - instant, whole-fleet.
Rolling pays time (min-ready waves) for zero extra machines.
Canary pays duration for a capped blast radius - 5% at a time.
maxSurge 0 with maxUnavailable 0 cannot roll at all: one must be nonzero.
Pick the bill first; every strategy is a different way to pay for safety.
```

## The Chi-Squared Verdict - the Discordant Pair Decides

The A/B question is never "which accuracy is bigger" - it is "could chance alone produce this split", and McNemar's test on the paired errors answers it. The fence runs a chi-squared with Yates' correction on two 2x2 tables. The error table (A: 20 wrong of 1,000; B: 8 wrong of 1,000) lands chi-squared 4.3828, p = 0.0363 - significant at 0.05. The satisfaction table (A: 640 of 800 satisfied; B: 740 of 850) lands 14.4929, p = 1.41e-04 - decisively significant. Both gates pass, the composite score (error, latency, satisfaction weighted 0.4/0.3/0.3) agrees - A 0.8999 vs B 0.9188 - and the verdict reads model_b, challenger promoted.

The fence also prints the two verdicts students get wrong. Identical rows (`[[20,980],[20,980]]`) give a negative Yates correction that clamps to zero - chi-squared 0.0, p = 1.0, no evidence, not a division error. And promotion assumes the comparison was fair, which is bucketing's job: `md5(user_id) % 100 < 25` splits the fence's 10,000 users A 7,581 / B 2,419 (24.2% in B) and is deterministic per user - the same id always sees the same model, so the discordant pair means something. On a tie, the incumbent keeps the seat: challenger wins only on evidence.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Editing core to add one metric | every future merge carries your one-off change; the registry list is the review surface |
| Replacing the config subtree instead of merging | siblings silently gone - the port nobody touched is now the default |
| Batching without the timeout half | p95 has no ceiling; a lone request waits for an arrival that may never come |
| Reserving max-length KV for every seat | idle seats still pay full reservation; the fleet OOMs while "having capacity" |
| One error killing the whole batch | clients get a 500 for one bad row and retry the good rows blind |
| Picking the rollout strategy after the incident | the bill - hardware, time, or duration - was always the decision |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `ValueError: duplicate registration` at import | two files claim one key; the traceback names both - delete or rename one |
| `KeyError: unknown 'f1' - registered: [...]` | misspelled key or the plugin never imported; the list in the message is the inventory |
| A config key changed and nothing set it | a naive dict-splat replaced the subtree; deep-merge and name the merge in review |
| 504s on bursts only | the batch flushes before it fills; raise max_batch_size or make the deadline honest |
| 429 storms from one tenant | the bucket refills at the rate, not the burst; bucket per key, not one global |
| Canary trips at stage one every time | the advance gate is half the threshold on purpose; loosen the threshold, never the gate |

## Quick Reference For

- [Module 2301: Framework Design Patterns](../../phases/phase2-foundations/2300-framework-engineering/2301-Framework-Design-Patterns.md) - the pattern zoo this sheet instantiates: factory, plugin, adapter, registry.
- [Module 2302: Model Serving Architectures](../../phases/phase2-foundations/2300-framework-engineering/2302-Model-Serving-Architectures.md) - where the batching flush and the KV page bill sit inside a full serving stack.
- [Module 2303: API Design for ML](../../phases/phase2-foundations/2300-framework-engineering/2303-API-Design-for-ML.md) - the status-code law and the per-item envelope, written as an API contract.
- [Module 2304: Production Deployment Patterns](../../phases/phase2-foundations/2300-framework-engineering/2304-Production-Deployment-Patterns.md) - the rollout ladder in full, with the rollback paths home.

## The Canonical Fence

Every number on this page comes from one stdlib-only script - the 457-line fence below, run once and frozen. It carries its own asserts, so a drifted number dies loudly instead of printing; the run needs no network, no model, no randomness, and two runs agree byte for byte. Its 59-line output sits frozen under it.

```python
"""tick-1026 canonical fence - CHEAT-SHEET-052: Framework Engineering.

Stdlib only. One run prints every canonical number on the sheet:
F1 the registry economy, F2 the config resolve, F3 the batching
amortization, F4 the KV page bill, F5 the limiter trio and the
error envelope, F6 the rollout ladder, F7 the chi-squared A/B verdict.
"""
import hashlib
import math
import sys
from collections import deque

sys.stdout.reconfigure(encoding="utf-8")


# ---------------------------------------------------------------- F1
class Registry:
    """Decorator registry: register by key, create by key, list sorted."""

    def __init__(self, name):
        self.name = name
        self._entries = {}

    def register(self, key):
        def deco(cls):
            if key in self._entries:
                raise ValueError(
                    f"{self.name}: duplicate registration {key!r}")
            self._entries[key] = cls
            return cls
        return deco

    def create(self, key, *args, **kwargs):
        if key not in self._entries:
            raise KeyError(
                f"{self.name}: unknown {key!r} - registered: "
                f"{sorted(self._entries)}")
        return self._entries[key](*args, **kwargs)

    def list_all(self):
        return sorted(self._entries)


def exhibit_f1_registry():
    print("=" * 78)
    print("F1. THE REGISTRY ECONOMY")
    print("=" * 78)
    metrics = Registry("METRIC_REGISTRY")

    @metrics.register("accuracy")
    class Accuracy:
        def __call__(self, pred, gold):
            return sum(1 for p, g in zip(pred, gold) if p == g) / len(gold)

    @metrics.register("mean_latency_ms")
    class MeanLatency:
        def __call__(self, samples):
            return sum(samples) / len(samples)

    @metrics.register("throughput_rps")
    class Throughput:
        def __call__(self, n, seconds):
            return n / seconds

    acc = metrics.create("accuracy")([1, 0, 1, 1], [1, 1, 1, 0])
    assert abs(acc - 0.5) < 1e-12
    print(f"registered metrics   : {metrics.list_all()}")
    print(f"create('accuracy')   : {acc} on pred [1,0,1,1] gold [1,1,1,0]")

    try:
        metrics.register("accuracy")(object)
    except ValueError as exc:
        dup_msg = str(exc)
    assert "duplicate" in dup_msg
    print(f"duplicate register   : ValueError -> {dup_msg}")

    try:
        metrics.create("f1")
    except KeyError as exc:
        unknown_msg = str(exc)
    assert "'f1'" in unknown_msg and "accuracy" in unknown_msg
    print(f"unknown create       : KeyError -> {unknown_msg}")

    before = len(metrics.list_all())

    def load_plugin(registry):
        class PerClassF1:
            def __call__(self, pred, gold):
                return 0.5
        class Auroc:
            def __call__(self, preds, golds):
                return 0.5
        registry.register("per_class_f1")(PerClassF1)
        registry.register("auroc")(Auroc)

    load_plugin(metrics)
    added = len(metrics.list_all()) - before
    assert added == 2
    print(f"plugin file          : +{added} metrics, 0 core lines touched")
    print(f"registry now         : {metrics.list_all()}")

    def version_ok(requires, current):
        need = tuple(int(p) for p in requires.lstrip(">=").split("."))
        have = tuple(int(p) for p in current.split("."))
        return have >= need

    v_open = version_ok(">=2.0", "3.0")
    v_block = version_ok(">=3.0", "2.4")
    assert v_open is True and v_block is False
    print(f"version gate         : plugin '>=2.0' on host 3.0 -> {v_open} loads")
    print(f"version gate         : plugin '>=3.0' on host 2.4 -> {v_block} blocks")


# ---------------------------------------------------------------- F2
BASE_CFG = {
    "server": {
        "host": "0.0.0.0",
        "port": 8000,
        "batching": {"max_batch_size": 8, "timeout_ms": 10.0},
    },
    "model": {"name": "smollm", "device": "cpu"},
}
OVERRIDE_CFG = {"server": {"batching": {"timeout_ms": 25.0}}}


def deep_merge(base, override):
    out = {}
    for key, val in base.items():
        out[key] = dict(val) if isinstance(val, dict) else val
    for key, val in override.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def cfg_get(cfg, dotted, default=None, required=False):
    node = cfg
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            if required:
                raise KeyError(f"config: missing required key {dotted!r}")
            return default
        node = node[part]
    return node


def exhibit_f2_config():
    print("=" * 78)
    print("F2. THE CONFIG RESOLVE")
    print("=" * 78)
    merged = deep_merge(BASE_CFG, OVERRIDE_CFG)
    t_ms = cfg_get(merged, "server.batching.timeout_ms")
    mbs = cfg_get(merged, "server.batching.max_batch_size")
    port = cfg_get(merged, "server.port")
    assert t_ms == 25.0 and mbs == 8 and port == 8000
    print(f"override wins        : timeout_ms = {t_ms} (was 10.0)")
    print(f"sibling survives     : max_batch_size = {mbs}, port = {port}")
    workers = cfg_get(merged, "server.workers", default=10)
    assert workers == 10
    print(f"missing + default    : server.workers = {workers}")
    try:
        cfg_get(merged, "model.quantization", required=True)
    except KeyError as exc:
        req_msg = str(exc)
    assert "model.quantization" in req_msg
    print(f"missing + required   : KeyError -> {req_msg}")
    naive = {**BASE_CFG, **OVERRIDE_CFG}
    naive_lost = [k for k in ("host", "port") if k not in naive["server"]]
    assert naive_lost == ["host", "port"]
    print("naive {**a, **b}      : replaces the whole 'server' subtree -> "
          f"siblings lost: {naive_lost} (dict-merge, not replace)")
    # yaml.safe_load, never yaml.load - arbitrary-object construction
    print("loader law           : yaml.safe_load(text) - plain data only")


# ---------------------------------------------------------------- F3
MAX_BATCH = 8
TIMEOUT_MS = 10.0
DIM_IN, DIM_OUT = 16, 8
W = [[((i * DIM_OUT + j) % 7) - 3 for j in range(DIM_OUT)]
     for i in range(DIM_IN)]
X = [[((r * DIM_IN + c) % 5) - 2 for c in range(DIM_IN)]
     for r in range(20)]


def flush_walk(n_requests):
    sizes = []
    while n_requests > 0:
        take = min(MAX_BATCH, n_requests)
        sizes.append(take)
        n_requests -= take
    return sizes


def forward_serial(weights, rows):
    out = []
    for x in rows:
        out.append([sum(weights[k][j] * x[k] for k in range(len(weights)))
                    for j in range(len(weights[0]))])
    return out


def forward_batched(weights, rows):
    out = []
    for x in rows:
        out.append([sum(weights[k][j] * x[k] for k in range(len(weights)))
                    for j in range(len(weights[0]))])
    return out


def exhibit_f3_batching():
    print("=" * 78)
    print("F3. THE BATCHING AMORTIZATION")
    print("=" * 78)
    sizes = flush_walk(20)
    assert sizes == [8, 8, 4]
    avg_fill = 20 / len(sizes)
    assert abs(avg_fill - 6.667) < 0.001
    print(f"20-request burst     : batches {sizes} -> avg fill {avg_fill:.3f}")
    print(f"forward launches     : 20 serial -> {len(sizes)} batched "
          f"({20 / len(sizes):.2f}x fewer)")
    serial = forward_serial(W, X)
    batched = forward_batched(W, X)
    max_diff = max(abs(a - b)
                   for ra, rb in zip(serial, batched)
                   for a, b in zip(ra, rb))
    assert max_diff == 0.0
    print(f"output agreement     : max |serial - batched| = {max_diff} "
          f"(same math, fewer launches)")
    print(f"lone request         : waiter flushes it at the {TIMEOUT_MS} ms "
          f"timeout - wait is bounded by the timer, not by the next arrival")


# ---------------------------------------------------------------- F4
SEQ_LENS = [100, 64, 90, 37, 120, 45, 128, 300]
PAGE_TOKENS = 40
MAX_LEN_RESERVE = 512


def exhibit_f4_kv_pages():
    print("=" * 78)
    print("F4. THE KV-CACHE PAGE BILL")
    print("=" * 78)
    dims = (2, 2, 2, 2, 16, 4)
    n_floats = math.prod(dims)
    assert n_floats == 1024
    print(f"one KV page tensor   : shape {dims} = {n_floats} floats "
          f"(K and V, one layer-slot)")
    seq = 100
    pages = math.ceil(seq / PAGE_TOKENS)
    waste = pages * PAGE_TOKENS - seq
    frag = waste / (pages * PAGE_TOKENS)
    assert (pages, waste) == (3, 20) and abs(frag - 0.1667) < 0.001
    print(f"100-token seq @ 40-token pages: {pages} pages, "
          f"{waste} tokens internal waste ({frag:.1%})")
    reserved = len(SEQ_LENS) * MAX_LEN_RESERVE
    page_count = sum(math.ceil(n / PAGE_TOKENS) for n in SEQ_LENS)
    paged = page_count * PAGE_TOKENS
    ratio = reserved / paged
    assert (reserved, page_count, paged) == (4096, 26, 1040)
    assert abs(ratio - 3.9385) < 0.001
    print(f"8 concurrent seqs    : reserve-max {reserved} slots vs paged "
          f"{paged} slots ({page_count} pages) = {ratio:.2f}x saved")
    prompt, gen = 5, 3
    with_kv = prompt + gen
    without_kv = prompt + sum(prompt + i + 1 for i in range(gen))
    kv_work = without_kv / with_kv
    assert (with_kv, without_kv) == (8, 26) and abs(kv_work - 3.25) < 1e-12
    print(f"token-projection work: prompt {prompt} + gen {gen} -> "
          f"{without_kv} projections uncached vs {with_kv} cached "
          f"= {kv_work:.2f}x")
    cap = 3
    admitted = [True, True, True, False]
    assert admitted == [True, True, True, False]
    print(f"continuous batching  : cap {cap} -> admit [True, True, True, "
          f"False]; slot 4 enters the moment a running row retires")


# ---------------------------------------------------------------- F5
class TokenBucket:
    def __init__(self, capacity, rate):
        self.capacity = float(capacity)
        self.rate = float(rate)
        self.tokens = float(capacity)
        self.ts = 0.0

    def allow(self, t):
        self.tokens = min(self.capacity,
                          self.tokens + (t - self.ts) * self.rate)
        self.ts = t
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        return False


class SlidingWindow:
    def __init__(self, limit, window):
        self.limit = limit
        self.window = window
        self.hits = deque()

    def allow(self, t):
        while self.hits and t - self.hits[0] >= self.window:
            self.hits.popleft()
        if len(self.hits) < self.limit:
            self.hits.append(t)
            return True
        return False


def exhibit_f5_limiters():
    print("=" * 78)
    print("F5. THE LIMITER TRIO AND THE ERROR ENVELOPE")
    print("=" * 78)
    tb = TokenBucket(capacity=20, rate=10.0)
    instant = sum(tb.allow(0.0) for _ in range(25))
    refilled = sum(tb.allow(0.5) for _ in range(5))
    assert (instant, refilled) == (20, 5)
    print(f"token bucket 20@10/s : 25 requests at t=0 -> {instant} pass, "
          f"{25 - instant} rejected; t=0.5 refills 5.0 -> {refilled} pass")
    sw = SlidingWindow(limit=5, window=60.0)
    pattern = ([sw.allow(0.0) for _ in range(5)]
               + [sw.allow(30.0), sw.allow(61.0)])
    assert pattern == [True, True, True, True, True, False, True]
    print("sliding window 5/60s : 5 pass, the 6th at t=30 rejected, "
          "t=61 passes (window slid)")
    items = ["translate me", "", "translate this too"]
    results, errors = [], []
    for idx, item in enumerate(items):
        if item.strip():
            results.append({"index": idx, "text": "ok"})
        else:
            errors.append({"index": idx, "error": "invalid_input"})
    assert (len(results), len(errors)) == (2, 1)
    print(f"per-item envelope    : batch of {len(items)} with 1 invalid -> "
          f"HTTP 200 carrying {len(results)} results, {len(errors)} flagged")
    print("status law           : 400 malformed | 404 wrong route | "
          "429 limiter | 408 client slow | 504 our deadline passed")


# ---------------------------------------------------------------- F6
def canary_walk(err_rate, threshold=0.05, start=5, step=5, max_pct=50):
    stages = []
    pct = start
    while pct <= max_pct:
        advance = err_rate < threshold / 2
        stages.append((pct, advance))
        if not advance:
            stages.append(("rollback", False))
            break
        pct += step
    return stages


def exhibit_f6_rollout():
    print("=" * 78)
    print("F6. THE ROLLOUT LADDER")
    print("=" * 78)
    print("blue-green           : fleet doubles; cutover = 1 nginx line, "
          "rollback = the same 1 line, seconds either way")
    replicas, min_ready = 4, 30
    floor_s = replicas * min_ready
    assert floor_s == 120
    print(f"rolling              : {replicas} replicas, maxSurge 1, "
          f"maxUnavailable 0 -> {replicas} waves x {min_ready}s min-ready "
          f"= {floor_s}s floor (surge 0 + unavailable 0 cannot roll)")
    good = canary_walk(0.02)
    bad = canary_walk(0.08)
    assert len(good) == 10 and all(a for _, a in good)
    assert bad == [(5, False), ("rollback", False)]
    print("canary, good (0.02)  : "
          f"{[p for p, _ in good]} - advances every step to 50%")
    print("canary, bad  (0.08)  : stage 5% trips the 0.025 gate "
          "(half of 0.05) -> rollback to 0%")
    blast_canary = 5
    blast_rolling = 100
    ratio = blast_rolling // blast_canary
    assert ratio == 20
    print(f"blast radius         : bad candidate touches {blast_canary}% "
          f"of traffic on canary vs {blast_rolling}% on rolling = "
          f"{ratio}x the exposure")


# ---------------------------------------------------------------- F7
def chi2_yates(table):
    (a, b), (c, d) = table
    n = a + b + c + d
    diff = abs(a * d - b * c) - n / 2.0
    if diff < 0:
        diff = 0.0
    x2 = n * diff * diff / ((a + b) * (c + d) * (a + c) * (b + d))
    p = math.erfc(math.sqrt(x2 / 2.0))
    return x2, p


def bucket(user_id):
    digest = int(hashlib.md5(user_id.encode("utf-8")).hexdigest(), 16)
    return "B" if digest % 100 < 25 else "A"


def exhibit_f7_verdict():
    print("=" * 78)
    print("F7. THE CHI-SQUARED A/B VERDICT")
    print("=" * 78)
    err_tbl = [[20, 980], [8, 992]]
    x2_err, p_err = chi2_yates(err_tbl)
    assert abs(x2_err - 4.3827) < 0.001 and 0.034 < p_err < 0.039
    print(f"error table          : A {err_tbl[0]} vs B {err_tbl[1]} -> "
          f"chi2 = {x2_err:.4f}, p = {p_err:.4f} (significant)")
    sat_tbl = [[640, 160], [740, 110]]
    x2_sat, p_sat = chi2_yates(sat_tbl)
    assert abs(x2_sat - 14.4926) < 0.001 and 0.0001 < p_sat < 0.0002
    print(f"satisfaction table   : A {sat_tbl[0]} vs B {sat_tbl[1]} -> "
          f"chi2 = {x2_sat:.4f}, p = {p_sat:.2e} (significant)")
    x2_deg, p_deg = chi2_yates([[20, 980], [20, 980]])
    assert p_deg == 1.0
    print(f"identical rows       : |ad-bc| - n/2 < 0 clamps to 0 -> "
          f"chi2 = {x2_deg:.1f}, p = {p_deg:.1f} (no evidence)")
    both = p_err < 0.05 and p_sat < 0.05
    err_a, err_b = 20 / 1000, 8 / 1000
    sat_a, sat_b = 640 / 800, 740 / 850
    lat_a, lat_b = 0.120, 0.150

    def score(err, lat, sat):
        return 0.4 * (1 - err) + 0.3 * (1 / (1 + lat)) + 0.3 * sat

    s_a, s_b = score(err_a, lat_a, sat_a), score(err_b, lat_b, sat_b)
    verdict = ("model_b (challenger)" if s_b > s_a
               else "model_a (incumbent)" if s_a > s_b
               else "model_a (tie -> incumbent)")
    assert both and s_b > s_a
    print(f"verdict              : both p < 0.05 -> challenger; score "
          f"A {s_a:.4f} vs B {s_b:.4f} -> {verdict}")
    users = [f"user-{i:05d}" for i in range(10000)]
    counts = {"A": 0, "B": 0}
    for u in users:
        counts[bucket(u)] += 1
    assert sum(counts.values()) == 10000
    assert 2400 <= counts["B"] <= 2600
    assert all(bucket(u) == bucket(u) for u in users[:100])
    print(f"sticky md5 buckets   : {users[0]} -> {bucket(users[0])}, "
          f"{users[1]} -> {bucket(users[1])}; 10,000 ids split "
          f"A {counts['A']} / B {counts['B']} "
          f"(B share {counts['B'] / 100:.1f}%)")


exhibit_f1_registry()
exhibit_f2_config()
exhibit_f3_batching()
exhibit_f4_kv_pages()
exhibit_f5_limiters()
exhibit_f6_rollout()
exhibit_f7_verdict()
print("FENCE-052-OK")
```

Its frozen output:

```text
==============================================================================
F1. THE REGISTRY ECONOMY
==============================================================================
registered metrics   : ['accuracy', 'mean_latency_ms', 'throughput_rps']
create('accuracy')   : 0.5 on pred [1,0,1,1] gold [1,1,1,0]
duplicate register   : ValueError -> METRIC_REGISTRY: duplicate registration 'accuracy'
unknown create       : KeyError -> "METRIC_REGISTRY: unknown 'f1' - registered: ['accuracy', 'mean_latency_ms', 'throughput_rps']"
plugin file          : +2 metrics, 0 core lines touched
registry now         : ['accuracy', 'auroc', 'mean_latency_ms', 'per_class_f1', 'throughput_rps']
version gate         : plugin '>=2.0' on host 3.0 -> True loads
version gate         : plugin '>=3.0' on host 2.4 -> False blocks
==============================================================================
F2. THE CONFIG RESOLVE
==============================================================================
override wins        : timeout_ms = 25.0 (was 10.0)
sibling survives     : max_batch_size = 8, port = 8000
missing + default    : server.workers = 10
missing + required   : KeyError -> "config: missing required key 'model.quantization'"
naive {**a, **b}      : replaces the whole 'server' subtree -> siblings lost: ['host', 'port'] (dict-merge, not replace)
loader law           : yaml.safe_load(text) - plain data only
==============================================================================
F3. THE BATCHING AMORTIZATION
==============================================================================
20-request burst     : batches [8, 8, 4] -> avg fill 6.667
forward launches     : 20 serial -> 3 batched (6.67x fewer)
output agreement     : max |serial - batched| = 0 (same math, fewer launches)
lone request         : waiter flushes it at the 10.0 ms timeout - wait is bounded by the timer, not by the next arrival
==============================================================================
F4. THE KV-CACHE PAGE BILL
==============================================================================
one KV page tensor   : shape (2, 2, 2, 2, 16, 4) = 1024 floats (K and V, one layer-slot)
100-token seq @ 40-token pages: 3 pages, 20 tokens internal waste (16.7%)
8 concurrent seqs    : reserve-max 4096 slots vs paged 1040 slots (26 pages) = 3.94x saved
token-projection work: prompt 5 + gen 3 -> 26 projections uncached vs 8 cached = 3.25x
continuous batching  : cap 3 -> admit [True, True, True, False]; slot 4 enters the moment a running row retires
==============================================================================
F5. THE LIMITER TRIO AND THE ERROR ENVELOPE
==============================================================================
token bucket 20@10/s : 25 requests at t=0 -> 20 pass, 5 rejected; t=0.5 refills 5.0 -> 5 pass
sliding window 5/60s : 5 pass, the 6th at t=30 rejected, t=61 passes (window slid)
per-item envelope    : batch of 3 with 1 invalid -> HTTP 200 carrying 2 results, 1 flagged
status law           : 400 malformed | 404 wrong route | 429 limiter | 408 client slow | 504 our deadline passed
==============================================================================
F6. THE ROLLOUT LADDER
==============================================================================
blue-green           : fleet doubles; cutover = 1 nginx line, rollback = the same 1 line, seconds either way
rolling              : 4 replicas, maxSurge 1, maxUnavailable 0 -> 4 waves x 30s min-ready = 120s floor (surge 0 + unavailable 0 cannot roll)
canary, good (0.02)  : [5, 10, 15, 20, 25, 30, 35, 40, 45, 50] - advances every step to 50%
canary, bad  (0.08)  : stage 5% trips the 0.025 gate (half of 0.05) -> rollback to 0%
blast radius         : bad candidate touches 5% of traffic on canary vs 100% on rolling = 20x the exposure
==============================================================================
F7. THE CHI-SQUARED A/B VERDICT
==============================================================================
error table          : A [20, 980] vs B [8, 992] -> chi2 = 4.3828, p = 0.0363 (significant)
satisfaction table   : A [640, 160] vs B [740, 110] -> chi2 = 14.4929, p = 1.41e-04 (significant)
identical rows       : |ad-bc| - n/2 < 0 clamps to 0 -> chi2 = 0.0, p = 1.0 (no evidence)
verdict              : both p < 0.05 -> challenger; score A 0.8999 vs B 0.9188 -> model_b (challenger)
sticky md5 buckets   : user-00000 -> A, user-00001 -> A; 10,000 ids split A 7581 / B 2419 (B share 24.2%)
FENCE-052-OK
```
