---
Document ID: 7405
Title: "7405: Key-Value Memory and Checkpoint Stores"
Phase: 7
Module: 7400
Last Updated: 2026-10-07
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'memory', 'checkpoint', 'infrastructure']
---

# 7405: Key-Value Memory and Checkpoint Stores

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Address Space: Exact Keys versus Semantic Recall](#the-address-space-exact-keys-versus-semantic-recall)
- [TTL Is a Lease: Expiration Mechanics](#ttl-is-a-lease-expiration-mechanics)
- [The Budget: Eviction Policies and Who Pays](#the-budget-eviction-policies-and-who-pays)
- [The Checkpoint Store: Agent State as a KV Contract](#the-checkpoint-store-agent-state-as-a-kv-contract)
- [The Ledger: One Fleet, Four Memory Bills](#the-ledger-one-fleet-four-memory-bills)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

After reading this lesson, you will be able to:

- Read the address-space split: when the key is known, an exact-key lookup returns the object verbatim at O(1) while the same query through similarity search hands back the wrong document entirely - and when no key exists, only the search can answer
- State the two expiration mechanisms (passive on access, active by sampling) and show what each leaves behind: a 58.4% dead-but-lingering resident population under passive-only, an 18.3% residual at the active cycle's own 25% design point
- Explain why an overwrite without an expiry option silently clears the lease - 50 of 50 session keys immortal in the fence - and why the guarded form keeps all 50 on a schedule
- Predict who pays a maxmemory budget per policy: under a TTL'd workload the burden concentrates on exactly the persistent keys (51 evictions, all 51 checkpoints), while the volatile-only policies shield them (1,040 evictions, 0 checkpoints) and degrade to noeviction once no TTL keys remain
- Price one 50,000-session day four ways and read the knobs off the ledger: lease length is the resume budget, the active cycle buys the memory bound, refresh-on-read shields the threads that get read

**Estimated Time:** 3 hours (1 hour reading, 2 hours hands-on with the fences)

## Abstract

The 7400 assessment names one hole in this curriculum and this lesson closes it. Key-value memory as a dedicated store type is taught nowhere - Question 4's correct answer is "direct lookup by key," and it leans on [7403](7403-Vector-Memory.md)'s taxonomy storage-shape column alone, because no lesson owns the engine that lookup runs on. The boundary is real: [7401](7401-Long-term-Memory.md) owns the tier list, [7403](7403-Vector-Memory.md) owns semantic recall over embeddings, [7404](7404-Reflective-Memory-and-Context-Paging.md) owns the mechanisms that move bytes between tiers - what ranks, what consolidates, what pages. What no lesson has owned is the store underneath the exact-key half of that architecture: how O(1) addressing differs from similarity search as an address space, how the TTL lease actually expires, what an eviction policy does when a memory budget binds, and what it means to persist an agent's run state as a checkpoint store.

Five fences carry it. The address-space fence puts one agent's memory on both readers: the exact key `session:42:cart` returns `['sku-1', 'sku-7']` at 84.5 verbatim, while the same "latest cart state" query through a similarity ranking hands back `doc:101:summary` - a refund policy - with no cart key ranking anywhere; the flip case shows the refund question, where no key exists, answered only by the search. The TTL fence walks 3,000 writes through 600 minutes: passive-only expiration leaves 396 of 678 resident keys dead-but-lingering (58.4%), the active cycle reaps it to 63 of 344 (18.3%, its own design point) over 693 sampling passes, and the overwrite bug makes 50 of 50 session keys immortal where the guarded form keeps 50 of 50 on a schedule. The eviction fence runs three policies against one maxmemory budget: noeviction rejects 287 writes, allkeys-lru evicts 51 keys - every one a checkpoint - and volatile-lru evicts 1,040 keys - none of them checkpoints - while the degradation probe shows volatile-lru accepting 0 of 50 writes once the budget fills with persistent keys. The checkpoint fence builds the store [7404](7404-Reflective-Memory-and-Context-Paging.md)'s paging lands in: a 30-step run is 30 keys and 2,740 B with full history against 1 key and 92 B shallow, time travel to step 18 is served or gone forever, and a 60-minute TTL with polls to t+120 minutes deletes the resume state unless refresh-on-read is on. The campaign fence prices one 50,000-session day four ways: no lease grows 1.14 GB/day and OOMs a 16 GB box on day 14.0, passive-only leaks 31.93 GB by day 30 while still failing 3 of 4 late resumes, the active cycle holds 1.14 GB flat, and a 7-day lease with refresh-on-read caps at 12.59 GB with every resume answered.

## The Address Space: Exact Keys versus Semantic Recall

[7403](7403-Vector-Memory.md) built the vector store and the similarity search over it. This lesson owns the other reader. A key-value store is an address space: every value lives at exactly one key, and the read is a hash lookup, not a comparison. The read does not score candidates, does not normalize, does not approximate - it either lands on the object or misses. That is what Question 4's answer means: direct lookup by key.

The property that matters is not the O(1) cost. It is that the two readers answer different questions over the same bytes. When the address is known - the code wrote the cart under `session:42:cart` three turns ago - the exact read is the only correct reader: it returns the object itself, byte for byte. The similarity ranking is not a slower version of the same thing; run the same query through one and watch it fail:

```python
# One agent's memory namespaces: exact-key addressable vs semantic addressable
import math
from collections import Counter

docs = {
    "doc:101:summary": "Refund policy: full refund within 30 days of purchase.",
    "doc:102:summary": "Shipping policy: free shipping over $50, 3-5 business days.",
    "doc:103:summary": "Warranty: 12 months on hardware, 6 months on accessories.",
    "doc:104:summary": "Escalation policy: billing disputes route to tier-2 finance.",
}
session = {
    "session:42:cart": {"items": ["sku-1", "sku-7"], "total": 84.50},
    "session:42:step:19": {"action": "recommend", "result": "sku-9 shown"},
    "session:42:step:20": {"action": "add_to_cart", "result": "sku-9 added"},
}
kv = dict(docs)
kv.update(session)

# Case A: exact key exists -> direct lookup is the ONLY correct reader
got = kv.get("session:42:cart")
exact_is_identity = got == {"items": ["sku-1", "sku-7"], "total": 84.50}

# crude ANN: bag-of-words cosine over doc text
def toks(s):
    return Counter(s.lower().split())

def cos(a, b):
    A, B = toks(a), toks(b)
    inter = set(A) & set(B)
    num = sum(A[t] * B[t] for t in inter)
    na = math.sqrt(sum(v * v for v in A.values()))
    nb = math.sqrt(sum(v * v for v in B.values()))
    return num / (na * nb) if na and nb else 0.0

q = "latest cart state of the session"
ranked = sorted(docs.items(), key=lambda kv_: cos(kv_[1], q), reverse=True)
ann_top = ranked[0][0]

q2 = "what is the refund policy"
ranked2 = sorted(docs.items(), key=lambda kv_: cos(kv_[1], q2), reverse=True)
ann_top2 = ranked2[0][0]
exact_q2 = kv.get("session:refund")  # no such key exists

print("exact hit verbatim:", exact_is_identity,
      "| cart =", got["items"], got["total"])
print("ANN top-1 for 'latest cart state':", ann_top,
      "| any cart key in ANN ranking:", any("cart" in k for k, _ in ranked))
print("ANN top-1 for 'refund policy':", ann_top2,
      "| exact-key refund lookup:", exact_q2)
print("split: address known -> exact key wins (O(1), verbatim);"
      " address unknown -> semantic search wins (top-1 doc:101)")
```

The run: the exact read is verbatim - the cart dict comes back whole, `['sku-1', 'sku-7']` at 84.5, the same object the write put there. The similarity ranking over the same corpus for the same intent hands back `doc:101:summary` - a refund policy - and no cart key appears anywhere in its ranking, because a cart dict has no text to embed. The two flips decide the design. Asked "what is the refund policy," there is no `session:refund` key to read (the exact lookup returns `None`) and the ranking serves `doc:101:summary` at the top - the search is the only reader that can answer. The rule is an address-space rule, not a performance rule: **address known, GET; address unknown, search**. An agent that routes state reads through similarity search because "the vector store is already there" will one day serve a refund policy for a shopping cart and have no test that catches it, because the error is a wrong object, not a slow one.

This is the boundary with [7403](7403-Vector-Memory.md): that lesson owns the semantic half - embeddings, the write/read paths, the lifecycle. This lesson owns the exact-key half and the engine semantics under it. A production memory architecture is both, namespace-separated: `session:42:cart` is an address, "what is the refund policy" is a query, and the code should know which one it is holding.

## TTL Is a Lease: Expiration Mechanics

The second engine semantic is the TTL - and the honest mental model is a lease, not a timestamp. A key with `EXPIRE 3600` holds a promise: the store may keep this object for one hour, and after that the store is allowed to destroy it. Redis stores the deadline as an absolute Unix timestamp in milliseconds, which is why expiry survives restarts - and why a wall-clock jump (NTP correction, VM migration) can expire healthy leases instantly or extend them for free.

Redis expires keys two ways, and the difference is the whole section. **Passive expiration**: a key is tested for expiry when it is accessed, and deleted if dead. **Active expiration**: the store periodically samples keys with deadlines and reaps the expired ones - the source runs 20 keys per pass (`ACTIVE_EXPIRE_CYCLE_KEYS_PER_LOOP`), keeps sampling while the stale fraction in the sample exceeds 25% (`ACTIVE_EXPIRE_CYCLE_ACCEPTABLE_STALE`), and caps the slow cycle's CPU share at 25%. Passive-only is the misconfiguration that leaks: a session key written and never read again is dead weight the store will carry forever, because nothing ever touches it to trigger the test.

The fence simulates 600 minutes of a session keyspace - 5 writes per minute, a 60-minute lease, a 1% per-minute read rate per key - once under passive-only, once with the active cycle in the loop:

```python
# Keyspace simulation: minute resolution, 600 simulated minutes.
# 5 writes/min, TTL 60 min, 1%/min read rate. Deadline = absolute minute.
import random

rng = random.Random(7405)
ttl = {}  # key -> absolute deadline minute
reads = 0

for now in range(0, 600):
    for _ in range(5):
        ttl[f"session:{rng.randrange(3000)}"] = now + 60
    # passive expiration: only keys actually touched are reaped
    touched = [k for k in ttl if rng.random() < 0.01]
    reads += len(touched)
    for k in touched:
        if ttl[k] <= now:
            del ttl[k]

written_total = 5 * 600
lingering_passive = sum(1 for d in ttl.values() if d <= 600)
leak_pct = 100.0 * lingering_passive / max(1, len(ttl))

# active cycle: 20 keys/pass (ACTIVE_EXPIRE_CYCLE_KEYS_PER_LOOP), effort
# scales the per-round count; keep going while stale > 25% (ACCEPTABLE_STALE)
ttl2 = {}
total_passes = 0
for t in range(0, 600):
    for _ in range(5):
        ttl2[f"session:{rng.randrange(3000)}"] = t + 60
    passes = 0
    while True:
        sample = rng.sample(sorted(ttl2), min(20, len(ttl2)))
        stale = [k for k in sample if ttl2[k] <= t]
        for k in stale:
            del ttl2[k]
        passes += 1
        total_passes += 1
        if not sample or len(stale) / len(sample) <= 0.25 or passes > 20:
            break

lingering_active = sum(1 for d in ttl2.values() if d <= 600)
leak2_pct = 100.0 * lingering_active / max(1, len(ttl2))

# The killer: SET overwrite clears TTL
exp = {}
immortal_bare = 0
for s in range(50):
    k = f"session:{s}"
    exp[k] = 3600
    for _ in range(3):
        exp.pop(k, None)  # bare SET clears expiry -> immortal
    if k not in exp:
        immortal_bare += 1
immortal_guarded = 0
for s in range(50):
    k = f"guarded:{s}"
    exp[k] = 3600
    for _ in range(3):
        exp[k] = 3600  # SET EX / EXPIRE NX after write keeps the lease
    if k not in exp:
        immortal_guarded += 1

print(f"writes={written_total} passive-only lingering={lingering_passive}/{len(ttl)} ({leak_pct:.1f}% of resident keys dead-but-lingering), reads={reads}")
print(f"active-cycle lingering={lingering_active}/{len(ttl2)} ({leak2_pct:.1f}%), cycle passes={total_passes}")
print(f"bare-SET immortals={immortal_bare}/50 vs SET-EX guarded={immortal_guarded}/50")
print("TTL is a lease: passive-only leaks what is never read again;"
      " the active cycle reaps it; an overwrite without EXPIRE pays forever")
```

Read the three lines. **Passive-only**: of 678 resident keys at the end, 396 are dead-but-lingering - 58.4% of the store is expired inventory that 3,422 sampled reads never happened to touch. **Active cycle**: 693 sampling passes of 20 keys each drive the residue to 63 of 344 - 18.3%, which is not a failure but the algorithm's own design point: the cycle stops when the sample's stale fraction falls to 25% (`ACCEPTABLE_STALE`), so a small dead population is the steady state, by design. The absolute improvement is 396 to 63 lingering - 6.3x - and the resident store itself halves, because dead keys stop crowding the live ones.

The third line is the bug that eats production deployments. A session key gets its lease with `SET key value EX 3600`. Later, the application updates the session's data with a plain `SET key newvalue` - and the lease is gone. An overwrite without an expiry option clears the TTL entirely (the key returns to persistent); the key becomes immortal under any policy that never evicts it. The fence's bare-SET rows all 50 session keys lost their lease - 50/50 immortal; the guarded form (re-issue `SET ... EX` or `EXPIRE` after every write, or use the conditional options - `EXPIRE` gained `NX/XX/GT/LT` in Redis 7.0, where `GT`/`LT` only move the deadline in the named direction) keeps all 50 on schedule. The failure is silent: no error, no log, just a keyspace that grows one immortal key per session until something else breaks. `INFO`'s `expired_keys` counter will not show it - these keys never expire - and `evicted_keys` will only show it if an eviction policy is armed to clean up the mess.

One more lease subtlety the fence's minute-resolution world hides: `RENAME` transfers the TTL to the new name, and expiry is evaluated with a sub-millisecond clock since Redis 2.6 - but the deadline is still an absolute wall-clock reading. A lease is a promise about a moment in time; treat it as approximate on any host whose clock can jump.

## The Budget: Eviction Policies and Who Pays

Expiration is the first line of memory control; eviction is the second, and it only fires when `maxmemory` binds. Redis ships ten policies across two axes: the allkeys family (`allkeys-lru`, `allkeys-lfu`, `allkeys-random`, and `allkeys-lrm` - least-recently-modified, new in Redis 8.6, whose timestamp moves only on writes) may evict any key, while the volatile family (`volatile-lru`, `volatile-lfu`, `volatile-random`, `volatile-ttl`) may only evict keys that carry a TTL. `noeviction` - the default - evicts nothing and rejects writes with an error when the budget is full. Two approximations matter in practice: LRU and LFU are sampled, not exact - each eviction examines `maxmemory-samples` candidates (default 5, with a candidate pool since Redis 3.0) rather than maintaining a global order, and LFU stores its frequency in a Morris-style counter capped at 255, saturating around a million accesses with `lfu-log-factor 10` and cooling by one every `lfu-decay-time` minutes (default 1).

The question a deployment actually needs answered is not "which policy is smartest" but "who pays." The fence runs an agent runtime on one shared instance - half of each operation writes fresh scratch state with a 120-operation lease, the reads are recency-local over recent writes plus occasional checkpoint reads, and the active cycle from Section 2 is in the loop doing the first-line reaping:

```python
# Workload: an agent runtime on one shared KV instance.
# - writes: 50% of ops append scratch state (scratch:{w}, TTL 120 ops)
# - reads: 95% recency-local scratch (uniform over the last 200 written
#   names -- the agent re-reads what it recently wrote), 5% checkpoint
#   reads (checkpoints are write-once/read-until-crash: LRU-cold by nature)
# - expiration IS in the loop: every op samples 20 resident volatile
#   keys and reaps expired ones (Section 2's active cycle)
import random

BUDGET = 120
OPS = 6000
TTL = 120

def run(policy):
    rng = random.Random(7405)
    store = {}   # key -> deadline (None = persistent)
    order = []   # LRU proxy: front = least recent (resident keys only)
    written = [] # write-order log for recency-local reads
    w = 0
    hits = misses = rejects = evicted_ckpt = evicted_total = expired_reaped = 0
    for op in range(OPS):
        # active-cycle sweep: sample 20 volatile keys, reap expired
        vol = [k for k in store if store[k] is not None]
        for k in rng.sample(vol, min(20, len(vol))):
            if store[k] <= op:
                del store[k]
                order.remove(k)
                expired_reaped += 1
        roll = rng.random()
        if roll < 0.50:  # write fresh scratch state
            k = f"scratch:{w}"
            written.append(w); w += 1
            if len(store) >= BUDGET:
                if policy == "noeviction":
                    rejects += 1
                    written.pop()
                    continue
                if policy.startswith("volatile"):
                    cand = [x for x in order if store[x] is not None]
                    if not cand:  # no TTL keys resident -> noeviction behavior
                        rejects += 1
                        written.pop()
                        continue
                else:
                    cand = order
                victim = cand[0]  # LRU front
                if victim.startswith("ckpt:"):
                    evicted_ckpt += 1
                del store[victim]
                order.remove(victim)
                evicted_total += 1
            store[k] = op + TTL
            order.append(k)
        else:  # read
            if rng.random() < 0.95:
                j = written[rng.randrange(max(1, len(written) - 200), len(written))]
                k = f"scratch:{j}"
            else:
                k = f"ckpt:{rng.randrange(100)}"
            if k in store:
                hits += 1
                if k in order:
                    order.remove(k); order.append(k)
            else:
                misses += 1
                if k.startswith("ckpt:"):
                    # checkpoint materializes on first touch (write-once)
                    if len(store) >= BUDGET:
                        if policy == "noeviction":
                            rejects += 1
                            continue
                        if policy.startswith("volatile"):
                            cand = [x for x in order if store[x] is not None]
                            if not cand:
                                rejects += 1
                                continue
                        else:
                            cand = order
                        victim = cand[0]
                        if victim.startswith("ckpt:"):
                            evicted_ckpt += 1
                        del store[victim]
                        order.remove(victim)
                        evicted_total += 1
                    store[k] = None
                    order.append(k)
    hit = hits / max(1, hits + misses)
    return hit, evicted_ckpt, evicted_total, rejects, expired_reaped, len(store)

print("policy         hit-rate  evictions  of-which-ckpt  rejected-writes  expired-reaped")
for p in ("noeviction", "allkeys-lru", "volatile-lru"):
    h, e, t, r, x, n = run(p)
    print(f"{p:<15} {h:.4f}    {t:<9} {e:<14} {r:<16} {x}")

# degradation probe: the budget fills with PERSISTENT keys only (every TTL
# key expired) -> volatile-* has no candidate and degrades to noeviction
burst = 50
work = {f"ckpt:{i}": [None, 0] for i in range(BUDGET)}
order = list(work)
acc_all = acc_vol = 0
for b in range(burst):
    if len(work) >= BUDGET:
        order.pop(0)  # allkeys-lru: evict LRU (a checkpoint)
    work[f"new:{b}"] = [None, b]
    order.append(f"new:{b}")
    acc_all += 1
work2 = {f"ckpt:{i}": [None, 0] for i in range(BUDGET)}
order2 = list(work2)
for b in range(burst):
    if len(work2) >= BUDGET:
        cand = [x for x in order2 if work2[x][0] is not None]
        if not cand:
            continue  # volatile-* + no TTL keys = noeviction: write REJECTED
        victim = cand[0]
        del work2[victim]; order2.remove(victim)
    work2[f"new:{b}"] = [None, b]; order2.append(f"new:{b}")
    acc_vol += 1
print(f"degradation probe (budget full of persistent keys, {burst}-write burst):"
      f" allkeys-lru accepts {acc_all}/{burst} (evicts checkpoints),"
      f" volatile-lru accepts {acc_vol}/{burst} (no-TTL-keys = noeviction)")
print("expiry is the first line of scratch turnover; eviction is the second."
      " allkeys-lru serves the churn by paying checkpoint keys;"
      " volatile-lru shields them but starves once TTLs run out")
```

The table's story is the eviction columns, not the hit rates - which sit at 0.2994, 0.3238, and 0.3036 because the hit rate is governed by the workload's locality and the TTL, not by who gets thrown overboard when the budget binds. **noeviction**: 287 writes rejected with errors - the default policy fails the deployment in the open. **allkeys-lru**: only 51 evictions total, and every single one is a checkpoint. That concentration is the finding: with the active cycle expiring scratch keys on schedule, the scratch population turns over before it can go LRU-cold, so when the budget does bind, the only LRU-cold keys left are the write-once/read-until-crash checkpoints - the exact keys a memory architecture cannot afford to lose. The policy did not reduce the burden; it aimed it. **volatile-lru**: 1,040 evictions, zero checkpoints - the volatile family pays for churn out of the scratch namespace alone, at the price of evicting far more keys because it cannot touch the durable ones.

The probe is the gotcha the Redis docs state plainly: when the budget fills with keys that carry no TTL - every lease expired, or the namespace discipline never existed - `volatile-*` has no candidate to evict and behaves exactly like `noeviction`. The probe's 50-write burst into a checkpoint-full budget: allkeys-lru accepts 50/50 (destroying 50 checkpoints to do it), volatile-lru accepts 0/50 - writes start failing with errors and nothing in the policy name warned anyone. The docs' own recommendation for mixed workloads is architectural: run the two namespaces on separate instances, or enforce prefix-level namespace discipline so the durable keys are never in the same eviction pool as the scratch. `INFO`'s counters - `keyspace_hits`/`keyspace_misses`, `evicted_keys`, `expired_keys` - are the tripwire set: a rising `evicted_keys` on an instance that holds checkpoints is the 51-evictions column happening live.

## The Checkpoint Store: Agent State as a KV Contract

Everything above is engine semantics. This section is the contract an agent actually signs when it persists run state - and it is the store [7404](7404-Reflective-Memory-and-Context-Paging.md)'s paging and [7304](../7300-orchestration/7304-Event-Buses-Deadlocks-and-Human-Gates.md)'s interrupt/resume mechanics land in. The LangGraph persistence layer makes the contract concrete: a checkpointer writes one checkpoint per super-step, keyed by thread. With `langgraph-checkpoint-redis` (0.5.2 at the time of writing), the Redis-backed saver is built and indexed explicitly - `RedisSaver.from_conn_string(...)` inside a context manager, then a mandatory `checkpointer.setup()` that creates the RediSearch indices the queries need; the async twin is `AsyncRedisSaver` with `asetup()`. It requires RedisJSON and RediSearch (bundled in Redis 8.0+, or Redis Stack below that), and it deliberately wants a plain `redis.Redis` client, not a cluster client, because it needs its keys colocated for search.

Two shape decisions and one lease decision are the whole contract. **Shape, history versus latest**: the default saver stores every checkpoint - one key per step - so any prior state is resumable (LangGraph's time travel). `ShallowRedisSaver` keeps only the latest checkpoint per thread: the store is one key per thread, and history is gone by construction. **Lease**: without configuration, checkpoints persist indefinitely; a `ttl={"default_ttl": 60, "refresh_on_read": True}` config gives every checkpoint a 60-minute lease that extends each time the thread is read - `refresh_on_read=False` leaves the lease fixed from write time.

The fence builds both shapes over a 30-step run and walks the lease with a crashed process:

```python
# A completed 30-step agent run: one checkpoint write per step, ~90 B each
import json

def state(s):
    return json.dumps({"step": s, "messages": [f"m{i}" for i in range(8)],
                       "scratch": f"s{s}"})

STEPS = 30
full = {f"ckpt:t1:{s}": state(s) for s in range(STEPS)}
shallow = {"ckpt:t1": state(STEPS - 1)}
full_bytes = sum(len(v.encode()) for v in full.values())
shallow_bytes = sum(len(v.encode()) for v in shallow.values())
print(f"after {STEPS} steps: full-history store = {len(full)} keys / {full_bytes} B,"
      f" shallow store = {len(shallow)} key / {shallow_bytes} B"
      f" ({full_bytes / shallow_bytes:.0f}x)")

# rewind: the operator wants to re-plan from step 18 of the finished run
r_full = full["ckpt:t1:18"]
r_shallow = shallow.get("ckpt:t1:18")
print(f"time travel to step 18: full-history -> {r_full[:14]}... (served);"
      f" shallow -> {r_shallow} (gone forever: latest-only keeps step {STEPS-1})")

# TTL walk: the process crashed at step 20; 2 h idle, status poll / 5 min
def walk(refresh):
    deadline = 60
    for t in range(5, 121, 5):
        if t > deadline:
            return None  # silently expired before the poll
        if refresh:
            deadline = t + 60
    return full["ckpt:t1:20"]

r_no_refresh = walk(False)
r_refresh = walk(True)
print(f"TTL 60min, polls to t+120min: refresh_on_read=False -> {r_no_refresh} (state GONE);"
      f" refresh_on_read=True -> ok ({len(r_refresh)} B restored)")
print("the checkpoint store is a KV contract: exact key, TTL lease,"
      " and a shape (history vs latest) chosen at saver construction")
```

The three lines price the three decisions. **Storage**: 30 keys and 2,740 B for full history against 1 key and 92 B shallow - a 30x multiple that grows linearly in run length; an agent serving thousands of concurrent threads pays that multiple on every one. **Shape**: rewinding to step 18 to re-plan after a bad branch is served from the history store and returns `None` from the shallow one - latest-only keeps step 29 and nothing before it, which is the right trade exactly when nobody will ever time travel and the wrong trade the day someone needs to. **Lease**: the process crashed at step 20, then sat idle for two hours while a status poller read the thread every 5 minutes. With `refresh_on_read=False`, the 60-minute lease expires at minute 60 and the resume at t+120 finds `None` - the state is gone, silently, with no error at write time or read time. With `refresh_on_read=True`, every poll extends the lease and the resume restores its 92 B. The lesson of the walk is that the resume horizon is a configuration value: `default_ttl` must cover the longest idle-then-resume gap the product promises, and `refresh_on_read` is what keeps a hot thread alive through an idle stretch that no fixed lease would survive.

The same three decisions price every managed checkpoint store - the names change (Upstash, Momento, a managed Redis), the contract does not: exact keys, a lease you configured, a shape you chose. The one thing the contract does not include is a warning when the lease wins - expiry deletes checkpoint state with the same silence it deletes session keys, and nothing in the read path distinguishes "no such thread" from "your lease lapsed."

## The Ledger: One Fleet, Four Memory Bills

The four mechanisms - the address space, the lease, the budget, the checkpoint shape - are one deployment's knobs. The campaign fence runs one fleet profile - 50,000 sessions a day, each carrying a 24 KB agent checkpoint with its message history, 10% of sessions ever attempting a resume, resume attempts landing 1 to 96 hours after creation - through 30 days under four configurations:

```python
# Deterministic cohort simulation, hour resolution, 30 days.
# Every session: created at hour h, ONE resume attempt at h + U(1,96).
HOURS = 30 * 24
PER_HOUR = 2083               # ~50,000 sessions/day
STATE_KB = 24.0               # one agent checkpoint, messages included
GB = 1024 * 1024
RESUME_FRAC = 0.10            # fraction of sessions ever resumed
RESUME_SPAN = 96              # attempt delay uniform 1..96 h
DUE = RESUME_FRAC * PER_HOUR  # total attempts per cohort
OOM_GB = 16.0

CONFIGS = [
    ("none: no TTL, no eviction", None, False, False),
    ("ttl24-passive: lease, passive only", 24, False, False),
    ("ttl24-active: lease + active cycle", 24, True, False),
    ("ttl168-refresh: 7d lease + refresh", 168, True, True),
]

print("config                              day-7 GB   day-30 GB   resume-success")
for name, ttl_h, active, refresh in CONFIGS:
    # cohorts: [created_hour, resident, deadline, attempts_left]
    cohorts = []
    resident = 0
    ok = fail = 0.0
    d7 = d30 = None
    for h in range(HOURS):
        cohorts.append([h, float(PER_HOUR),
                        (h + ttl_h) if ttl_h else None, DUE])
        resident += PER_HOUR
        for coh in cohorts:
            age = h - coh[0]
            if 1 <= age <= RESUME_SPAN and coh[3] > 0:
                due = min(DUE / RESUME_SPAN, coh[3])
                coh[3] -= due
                alive = coh[2] is None or h < coh[2]
                if alive:
                    ok += due
                    if refresh and ttl_h:
                        coh[2] = h + ttl_h
                else:
                    fail += due
                    if not active:          # passive read reaps the corpse
                        coh[1] -= due
                        resident -= due
        if active and ttl_h:
            for coh in cohorts:
                if coh[2] is not None and h >= coh[2] and coh[1] > 0:
                    resident -= coh[1]
                    coh[1] = 0.0
                if coh[2] is not None and h >= coh[2] and coh[3] > 0:
                    fail += coh[3]          # key gone: remaining attempts all fail
                    coh[3] = 0.0
        cohorts = [c for c in cohorts if c[1] > 0]
        if h == 24 * 7 - 1:
            d7 = resident * STATE_KB / GB
    d30 = resident * STATE_KB / GB
    succ = ok / (ok + fail) if (ok + fail) else 1.0
    print(f"{name:<36} {d7:8.2f}   {d30:8.2f}   {succ:.2f}")
oom_hour = OOM_GB * GB / (STATE_KB * PER_HOUR)
print(f"OOM horizon (config 'none', {OOM_GB:.0f} GB box): day {oom_hour / 24:.1f}"
      f" -- growth is {STATE_KB * PER_HOUR * 24 / GB:.2f} GB/day, linear, forever")
print("one fleet, four bills: no lease grows forever, passive leaks the"
      " never-read majority while still failing late resumes, the active cycle"
      " buys the memory bound, TTL length is the resume budget, refresh"
      " shields the threads that get read")
```

The ledger reads as four answers to one question - what does this configuration cost, and what does it fail to deliver?

**none** - no lease, no eviction: 8.01 GB at day 7, 34.33 GB at day 30, growing 1.14 GB/day forever, and a 16 GB box dies on day 14.0. Its 1.00 resume success is theoretical - the state is all there until the instance is not. **ttl24-passive** - the lease without the cycle: 31.93 GB at day 30, within a tenth of the no-lease bill, because the 90% of sessions that are never resumed are never read and passive expiration never touches them - the lease exists on paper and leaks in fact. And it still fails 3 of 4 resumes (0.25): a session whose one attempt lands past hour 24 reads a key that expired hours or days earlier. This is the config to recognize in a postmortem - the team bought the lease and kept both the leak and the losses. **ttl24-active** - the lease with the cycle: 1.14 GB flat from day 7 to day 30, the active reaping buying the memory bound - and still 0.24 resume success, because no reaping policy changes what the lease length promises. 24 hours of lease over a 96-hour attempt window answers 24/96 of the attempts; the missing 0.76 is not a bug to fix, it is the horizon the configuration chose. **ttl168-refresh** - the 7-day lease with refresh-on-read: 12.59 GB at day 30 and holding (the ceiling is the refreshed lease tail), 1.00 resume success - every attempt inside the 96-hour window lands on a live key. The bill for the guarantees is 11x the active config's floor, and it is an honest price: the knob that bounds memory (the cycle) and the knob that answers resumes (the lease length) are different knobs, and a deployment needs both set deliberately.

The one-line summary of the ledger: **the TTL length is the resume budget, the active cycle is the memory bound, and refresh-on-read is the hot-thread insurance** - a configuration missing any one of the three pays for the absence in exactly the column the fence names.

## Known Failure Modes

| # | Failure | Cause | Fix |
|---|---------|-------|-----|
| 1 | Session keys become immortal, memory grows forever | Data updates re-write the key with a plain `SET`, which clears the TTL silently | Every write re-issues the lease (`SET ... EX` or `EXPIRE` after the write); monitor for keys with no deadline in a namespace that should be all-lease |
| 2 | The store fills with dead sessions nobody reads | Passive-only expiration - keys are tested on access, and never-accessed keys are never reaped | Keep the active expiration cycle enabled (it is default-on in real Redis); sizing counts its 18.3% steady-state residual, not zero |
| 3 | Writes start failing with errors under maxmemory | `volatile-*` configured on an instance whose TTL keys all expired - it degrades to `noeviction` | Guarantee a volatile population or use `allkeys-*`; alert on rejected writes, not just on evictions |
| 4 | Checkpoints vanish under memory pressure | `allkeys-*` on an instance holding checkpoints: the burden concentrates on exactly the LRU-cold durable keys (the fence's 51-of-51) | Namespace discipline or separate instances - the docs' own advice; the checkpoint namespace gets `volatile-*` or its own budget |
| 5 | Resume after idle returns `None` with no error | `default_ttl` shorter than the product's idle-then-resume horizon, `refresh_on_read` off | Set the TTL from the resume SLA, turn refresh-on-read on for polled threads; treat expiry of checkpoint state as data loss, not cleanup |
| 6 | The checkpoint store grows linearly with run length | Full-history saver keeping one key per step (the fence's 30x) forever | `ShallowRedisSaver` when nobody time-travels; history only where re-planning from a prior step is a product feature |
| 7 | A lease dies mid-idle on a healthy thread | Deadlines are absolute wall-clock timestamps - an NTP correction or VM migration jumps the clock and expires (or extends) leases wholesale | NTP-stable hosts; treat the lease as approximate; refresh-on-read shrinks the exposure window |
| 8 | First checkpoint write fails with search-index errors | The saver was built with `from_conn_string` but `setup()` (or `asetup()`) never ran, so the RediSearch indices do not exist | Call `setup()` once at deployment; verify the modules (RedisJSON, RediSearch) are present - bundled in Redis 8.0+, Redis Stack below |

## Summary

- **The address space is the contract.** A known key returns the object verbatim at O(1) - `['sku-1', 'sku-7']` at 84.5 - while the same intent through similarity search hands back a refund policy; an unknown key returns `None` where the search answers. Route state reads by address, knowledge reads by query - the error to fear is a wrong object, not a slow one.
- **TTL is a lease, and it has two enforcement mechanisms.** Passive-only expiration leaves 396 of 678 resident keys dead-but-lingering (58.4%); the active cycle - 20 keys per pass, stopping at the 25% stale design point - drives it to 63 of 344 (18.3%) in 693 passes. The residual is by design, not by neglect.
- **The overwrite clears the lease.** A plain `SET` on an expiring key makes it immortal - 50/50 in the fence; the guarded form keeps 50/50 on schedule. The bug is silent, invisible to `expired_keys`, and compounds one immortal key per session per write path.
- **Eviction does not shrink the burden; it aims it.** Under a TTL'd workload, allkeys-lru's 51 evictions are all checkpoints and volatile-lru's 1,040 are none - and once no TTL keys remain, `volatile-*` silently becomes `noeviction` (0/50 writes accepted in the probe). The policy decides who pays, not whether.
- **The checkpoint store is three decisions.** History or latest (30x storage, time travel or none), lease length and refresh (the 60-minute fixed lease deletes resume state at minute 60 while refresh-on-read survives 2 idle hours of polling), and the exact-key contract underneath both - plus `setup()` before the first write.
- **The ledger's knobs are orthogonal and all mandatory.** No lease grows 1.14 GB/day (OOM day 14.0); the lease without the cycle leaks 31.93 GB and still fails 3 of 4 resumes; the cycle buys 1.14 GB flat; the 7-day lease with refresh answers every resume for 12.59 GB. TTL length is the resume budget, the cycle is the memory bound, refresh is the hot-thread insurance.

## References

### Related Minder Academy Documents

- [7401: Long-term Memory for Agents](7401-Long-term-Memory.md) - the tier list whose storage shapes motivate the exact-key half this lesson owns
- [7403: Vector Memory and Embedding-Based Storage](7403-Vector-Memory.md) - the semantic reader on the other side of the address-space split, and the taxonomy whose storage-shape column Question 4 leans on
- [7404: Reflective Memory and Context Paging](7404-Reflective-Memory-and-Context-Paging.md) - the paging policy whose page-outs land in exactly the store this lesson specifies
- [7304: Event Buses, Deadlocks and Human Gates](../7300-orchestration/7304-Event-Buses-Deadlocks-and-Human-Gates.md) - the orchestration interrupt/resume mechanics whose run state the checkpoint store persists
- [7101: ReAct Loop System](../7100-architecture/7101-ReAct-Loop-System.md) - the loop whose per-step state one checkpoint per super-step captures
- [6505: Response Caching and Stage Scaling](../../phase6-rag/6500-mlops-pipelines/6505-Response-Caching-and-Stage-Scaling.md) - the other request-keyed store in the stack: caching economics at the serving layer versus the agent-state store this lesson owns

### Primary Sources

- Redis docs. [Key eviction policy](https://redis.io/docs/latest/develop/reference/eviction/) - the ten-policy table, `noeviction` as default, sampled LRU/LFU (`maxmemory-samples` 5, candidate pool since 3.0), LFU's Morris counter with `lfu-log-factor`/`lfu-decay-time`, and the volatile-family-degrades-to-noeviction warning with the separate-instances recommendation.
- Redis docs. [EXPIRE](https://redis.io/docs/latest/commands/expire/) - passive and active expiration, expiry as absolute millisecond timestamps, `NX/XX/GT/LT` options (7.0+), and the overwrite-clears-TTL behavior shown in the command's own examples.
- Redis source. [`src/expire.c` (8.0 branch)](https://github.com/redis/redis/blob/8.0/src/expire.c) - `ACTIVE_EXPIRE_CYCLE_KEYS_PER_LOOP` (20), `ACTIVE_EXPIRE_CYCLE_ACCEPTABLE_STALE` (10% target / 25% hard stop in the sampling loop), `ACTIVE_EXPIRE_CYCLE_SLOW_TIME_PERC` (25% CPU cap).
- Redis. [`langgraph-redis` (redis-developer/langgraph-redis)](https://github.com/redis-developer/langgraph-redis) - `RedisSaver.from_conn_string` + mandatory `setup()` (RediSearch indices), `AsyncRedisSaver`/`asetup()`, `ShallowRedisSaver` latest-only semantics, `ttl={"default_ttl", "refresh_on_read"}` config, RedisJSON + RediSearch requirement, plain-client-not-cluster note. Published as [`langgraph-checkpoint-redis` on PyPI](https://pypi.org/project/langgraph-checkpoint-redis/) (0.5.2, requires `langgraph-checkpoint>=4.1.1`, `redis>=5.2.1`, `redisvl>=0.15.0`).
- Redis Ltd. [redis-py](https://pypi.org/project/redis/) (8.1.0) and the Linux Foundation's [Valkey](https://valkey.io) - the open-source BSD fork continuing the Redis protocol, with [`valkey-py`](https://pypi.org/project/valkey/) (6.1.1) forked from redis-py and server releases 9.1.2 (2026-09); Redis server current release 8.10.2 (2026-09). The engine semantics this lesson teaches are shared by both.

## Next Steps

- **Next Module:** [assessment/QUIZ.md](assessment/QUIZ.md) - Question 4 is the question this lesson answers; the exact-key-versus-ANN split with the cart dict served verbatim against the refund doc, the 58.4%-to-18.3% expiration walk, and the 51-of-51 checkpoint eviction concentration are the mechanics behind the "direct lookup by key" answer.
- **Continue with:** [7500: Agent Security](../7500-security/README.md) - a shared KV store is a trust boundary: every agent thread's state sits behind one keyspace, and what a compromised writer can do to another agent's checkpoints (and how ACLs and namespace isolation bound it) is that module's charter.
- **Assessment:** extend the fences - raise the TTL fence's read rate to 10% and report whether passive-only still leaks; add `allkeys-random` to the eviction table and report where its 51-eviction analog lands; drop the campaign's resume fraction to 2% and re-read which config's bill changes; then halve the 7-day lease and find the resume-success cliff.

**Estimated Time:** 3 hours (1 hour reading, 2 hours hands-on with the fences)
