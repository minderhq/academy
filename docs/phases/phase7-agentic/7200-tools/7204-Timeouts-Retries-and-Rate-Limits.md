---
Document ID: 7204
Title: "7204: Timeouts, Retries, and Rate Limits"
Phase: 7
Module: 7200
Last Updated: 2026-10-06
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'tool-calling', 'production', 'api-design']
---

# 7204: Timeouts, Retries, and Rate Limits

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Unguarded Call](#the-unguarded-call)
- [Timeout Budgets: Connect Versus Read](#timeout-budgets-connect-versus-read)
- [Retrying Is a Decision: Classification and the Idempotency Key](#retrying-is-a-decision-classification-and-the-idempotency-key)
- [Backoff Is a Fleet Behavior: Formula and Jitter](#backoff-is-a-fleet-behavior-formula-and-jitter)
- [The Caller Owns a Bucket Too: Self-Throttling](#the-caller-owns-a-bucket-too-self-throttling)
- [One Agent Through the Brownout: The Composed Stack](#one-agent-through-the-brownout-the-composed-stack)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Abstract

The 7200 module quiz leans on "production discipline" for its question about tool-integration resilience, and its own review note admits why: explicit timeout, backoff, and rate-limit triads are taught nowhere in the curriculum — [7201](./7201-Tool-Calling.md) teaches the calling mechanism, [2303](../../phase2-foundations/2300-framework-engineering/2303-API-Design-for-ML.md) teaches the server's half (return 429 with `Retry-After`), [7302](../7300-orchestration/7302-Communication-Protocols.md) teaches the message-bus form of the jitter loop, and [7504](../7500-security/7504-Agent-Abuse-Prevention-and-Identity-Threats.md) teaches the bucket as a defense against incoming abuse. What exists nowhere is the caller's side of the tool boundary as working code: the per-call timeout budget that bounds a hung read, the retry decision that separates retryable failures from permanent ones and gates the retryable ones on an idempotency key, the backoff formula as a fleet behavior where jitter is what keeps forty clients from retrying in lockstep, the caller-side bucket that obeys the quota instead of discovering it in 429s, and the circuit breaker that routes around an outage instead of feeding it. Five self-contained fences price each layer on deterministic fake clocks — the un-budgeted agent turn that never returns against the budgeted one that ends at 8.6s with 7/8 answered, the naive re-POST ledger that double-charges customer c2 against the keyed ledger that returns the original receipt, the lockstep herd that lands all 40 clients on the same tick against the jittered spread, the raw burst that eats 40 serial Retry-After waits against the bucketed client that finishes 36.0s faster with zero 429s, and the brownout campaign where the breaker routes 2 calls around a dead endpoint instead of into it.

## Learning Objectives

By the end of this lesson you will be able to:

1. Bound every tool call with a read timeout separate from the connect timeout, and show that only the read budget catches the accepted-then-hung call.
2. Classify failures as retryable or permanent before spending retry budget, and gate retryable write calls on an idempotency key so a retry cannot double-apply.
3. Compute the exponential-backoff delay formula and explain why jitter — not the exponent — is what saves a fleet from synchronized retry waves.
4. Self-throttle a burst with a client-side token bucket, and state the boundary against 7504: the defender's bucket rejects, the caller's bucket obeys.
5. Compose the stack — timeout, classified retry, bucket, circuit breaker — and read a brownout timeline showing which layer owns which failure class.

## The Unguarded Call

An agent turn is a wall-clock budget: the loop that plans, calls tools, and observes has to finish inside the latency envelope its users tolerate. Every tool call inside that turn is a bet that some other process — an HTTP server, a database, a code sandbox — answers in time. The bet is unpriced by default. A socket connect that gets refused fails in milliseconds and costs almost nothing; a server that **accepts** the connection and then never answers costs the rest of the turn, and with no timeout, more than that: it costs the turn forever. Nothing in the tool-calling mechanism from 7201 bounds this — the mechanism describes *how* to call, not *what to do when the other side stops talking*.

The same is true one layer out. One flaky endpoint does not just hang one call: every agent in the fleet hits the same endpoint, and without shared discipline they all hang together, all retry together, and all get throttled together. The four fences that follow price each piece of that discipline separately, and the campaign fence composes them.

## Timeout Budgets: Connect Versus Read

A timeout has to split, because the two ways a call fails are different shapes. **Connect** is the wait for the socket: refused is fast, silent-drop is what a connect budget bounds. **Read** is the wait after the server accepted you: this is where hangs live, because "accepted" and "working" are different facts and the client cannot tell them apart by waiting longer. The fences below simulate eight tool calls on a fake clock — durations stand in for real waits, so the arithmetic is exact and the run is instant:

```python
class ToolTimeout(Exception):
    """A call exceeded its read budget."""


calls = [
    # (name, connect_s, read_s) - read None = server accepted, never answers
    ("search_docs",    0.2, 0.8),
    ("get_weather",    0.3, 0.5),
    ("run_sql",        0.4, 2.5),
    ("billing_charge", 0.2, 1.1),
    ("flaky_report",   0.3, None),
    ("send_email",     0.2, 0.6),
    ("get_invoice",    0.3, 0.9),
    ("log_event",      0.1, 0.2),
]
TURN_BUDGET = 12.0
READ_BUDGET = 2.0

print("F1 timeout budgets: 8-call agent turn, budget 12.0s, read budget 2.0s")

# policy A: no read budget -> the accepted-then-hung call consumes the turn forever
t, answered = 0.0, 0
for name, c, r in calls:
    if r is None:
        t += c                       # connect succeeded...
        hung_at = name               # ...the read never ends: the turn never ends
        break
    t += c + r
    answered += 1
print(f"  no budget: '{hung_at}' accepts at +{t:.1f}s and never answers; {answered}/8 "
      f"answered, the hung read plus the {8 - answered - 1} never-attempted calls return never")

# policy B: read budget 2.0s -> the hang is bounded, the turn completes
t, answered, timed_out = 0.0, 0, []
for name, c, r in calls:
    t += c
    try:
        if r is None:
            raise ToolTimeout(f"{name} exceeded the {READ_BUDGET}s read budget")
        t += r
        answered += 1
    except ToolTimeout:
        timed_out.append(name)
print(f"  read budget {READ_BUDGET}s: '{timed_out[0]}' raises ToolTimeout at +{READ_BUDGET}s, "
      f"turn ends {t:.1f}s under the {TURN_BUDGET}s budget with {answered}/8 answered "
      f"and {len(timed_out)} bounded failure")

print("  connect vs read: a refused connect fails in ~0.2s on its own (cheap); "
      "an accepted-then-hung read is bounded by nothing but the read timeout")
```

The asymmetry is the lesson. Without the read budget the turn is not *slow* — it is **unterminated**: 4 of 8 calls answered and the rest never, which for an agent means no observation, no next thought, no completion. With the read budget the same turn ends at 8.6s — under budget — with 7/8 answered and one failure the loop can classify and handle. Production SDKs make the split explicit: `httpx.Timeout` carries separate `connect`, `read`, `write`, and `pool` values (5 seconds each by default), and the OpenAI SDK's clients default to a 10-minute request timeout with `max_retries=2` — the budget exists even when you never write it.

## Retrying Is a Decision: Classification and the Idempotency Key

A retry is not a reflex; it is a bet that the same request will succeed later. That bet is only rational for **retryable** failures — connection errors, timeouts, 503, 429 — and irrational for **permanent** ones: a 400 will be a 400 on every attempt, and each attempt spends budget for nothing. The second half of the decision is idempotency: retrying a read is free, but retrying a write re-sends a mutation, and a mutation applied twice is a different business event. That is why `urllib3.Retry` defaults `allowed_methods` to the idempotent verbs only — `DELETE, GET, HEAD, OPTIONS, PUT, TRACE` — with `POST` excluded, and why the OpenAI SDK auto-retries connection errors and 408/409/429/5xx only "when their body can be safely resent." When a write **must** be retried, the client sends an **idempotency key**: the server ledger dedupes on the key and returns the original receipt instead of applying the mutation again:

```python
from collections import Counter


charges = [("c1", "ok"), ("c2", "503"), ("c3", "ok"),
           ("c4", "400"), ("c5", "ok"), ("c6", "ok")]

ledger_naive = []   # every request body the server received, keyed by customer
ledger_keyed = {}   # idempotency key -> receipt
wasted = 0

for cid, status in charges:
    if status == "ok":
        ledger_naive.append(cid)
        ledger_keyed.setdefault(cid, "receipt")
        continue
    retryable = status in ("503", "timeout", "429")
    if retryable:
        ledger_naive.append(cid)              # naive client re-POSTs...
        ledger_keyed.setdefault(cid, "receipt")   # ...keyed client re-POSTs the SAME key
        if cid == "c2":
            ledger_naive.append(cid)          # provider retried internally once more
            ledger_keyed.setdefault(cid, "receipt")
    else:
        wasted += 1                           # a retry-everything client burns this
print("F2 retry classification + idempotency (6 charges, one 503, one 400)")
print(f"  naive re-POST ledger: {len(ledger_naive)} entries for 6 charges "
      f"({Counter(ledger_naive)['c2']} of them are c2 = double-charged); the 400 burned "
      f"{wasted} retry attempt that could never succeed")
print(f"  keyed ledger: {len(ledger_keyed)} receipts - c2's duplicate POST carried the same "
      f"key and returned the original receipt (1 charge), c4's 400 never became a charge")
```

Read the two ledgers as two businesses. The naive one holds 6 entries for 6 charges — customer c2 appears twice, which is a support ticket and a refund, and the 400 still produced nothing no matter how many attempts it was given. The keyed one holds 5 receipts: c2's duplicate hit the ledger, found its key already present, and returned the original receipt — the retry became *safe* without becoming *different*. Classification is what stops the 400 from costing retries; the key is what stops the 503 from costing double.

## Backoff Is a Fleet Behavior: Formula and Jitter

The delay between retries is not a courtesy; it is a control surface, and it has two regimes. **One client** retries on the exponential formula — base times two to the attempt, clamped by a max: with base 0.5s and cap 8s the delays walk 0.5s, 1s, 2s, 4s, 8s. That is the shape `tenacity`'s `wait_exponential(multiplier, min, max)` implements (2^x times the multiplier, clamped into the min/max band) and `urllib3` implements as `backoff_factor * 2**(number of previous retries)` capped by `backoff_max` (120s by default, with a `backoff_jitter` knob of its own).

**Forty clients** hitting the same provider blip turn the formula into a liability: every one of them computes the *same* delays, so the whole fleet retries at the same instants — 0.5s, 1s, 2s in perfect lockstep, each wave re-tripping the limiter it was escaping. **Jitter** is the fix, and it is not decoration: randomizing each delay across the same exponential range keeps the *average* backoff while destroying the synchronization. `tenacity` calls the idiom `wait_random_exponential` — "exponentially increasing jitter" — and the major cloud SDKs jitter by default:

```python
import random
from collections import Counter


BASE, MAXD, N = 0.5, 8.0, 40
formula = [min(BASE * 2 ** a, MAXD) for a in range(5)]

rng = random.Random(42)
peak_jit, slots_used = 0, 0
for a in range(5):
    hi = min(BASE * 2 ** a, MAXD)
    buckets = Counter()
    for _ in range(N):                    # N independent clients, attempt a
        buckets[round(rng.uniform(0, hi) / 0.25)] += 1
    peak_jit = max(peak_jit, max(buckets.values()))
    slots_used += len(buckets)

print("F3 backoff formula + jitter (base 0.5s, cap 8s, 40 clients)")
print("  one client, delays attempt 0..4:", ", ".join(f"{d:g}s" for d in formula))
print(f"  fleet, no jitter: all {N} clients retry on the same 5 shared ticks "
      f"(peak concurrency {N} at each tick)")
print(f"  fleet, seeded jitter: peak concurrency {peak_jit} in the busiest 0.25s slot, "
      f"retries spread across {slots_used} distinct slots - same average wait, "
      f"no synchronized wave")
```

The exponent sets how *fast* the fleet gives up pressing; the jitter sets whether it presses *together*. The fence's seeded spread tops out at 19 of 40 clients in the busiest 0.25s slot, with retries landing across 56 distinct slots — not perfectly flat, but no synchronized wave. Without jitter the retry storm is a metronome — every failure period reproduces a full-strength synchronized wave. With jitter the same budget spreads into a background hum the limiter can absorb.

## The Caller Owns a Bucket Too: Self-Throttling

A rate limit has two owners. **7504** met the bucket as a defense: the *server* runs it to reject incoming abuse, and the caller experiences the rejection as a 429 plus a `Retry-After` wait. The caller-side discipline is to run the **same bucket arithmetic on its own sends** — tokens refill at the quota, each send spends one — so the burst the quota forbids never touches the wire. `urllib3` honors the server's hint by default (`respect_retry_after_header=True` on statuses 413/429/503, capped by `retry_after_max` at 21600s); the bucket makes the hint rare instead of routine:

```python
RATE, CAP, BURST = 10.0, 10.0, 50      # quota 10/s, bucket cap 10, a 50-call burst
RETRY_AFTER = 1.0                      # server's hint per rejected call (fake clock)

# policy A: send everything at once, deal with the consequences
ok_now = min(BURST, CAP)
banned = BURST - ok_now
t_raw = ok_now / RATE + banned * RETRY_AFTER   # quota-pace + serial 429 waits

# policy B: the client's own token bucket paces the burst into the quota
t_bucket, tokens, sent = 0.0, CAP, 0
while sent < BURST:
    if tokens >= 1:
        tokens -= 1
        sent += 1
        t_bucket += 1 / RATE
    else:
        tokens = min(CAP, tokens + 1)        # one token back per quota tick
print(f"F4 caller-side bucket (quota {RATE:g} rps, cap {CAP:g}, burst {BURST})")
print(f"  raw burst: all {BURST} hit the wire, {banned:g} came back 429, "
      f"wall {t_raw:.1f}s ({banned:g} serial Retry-After waits on the fake clock)")
print(f"  bucketed client: 0 429s, all {BURST} paced into the quota, wall {t_bucket:.1f}s "
      f"({t_raw - t_bucket:.1f}s faster)")
print("  boundary: same bucket arithmetic as 7504, opposite side of the wire - "
      "the defender's bucket rejects, the caller's bucket obeys")
```

The raw burst is not just rejected — it is *punished*: 40 rejections each collect a full Retry-After second of wall time, so the naive client finishes at 41.0s while the self-throttled client finishes at 5.0s having never been rejected. Pacing is not slower than blasting; against any enforced quota it is strictly faster, because it never pays the rejection tax.

## One Agent Through the Brownout: The Composed Stack

The four mechanics compose into one resilience stack, and each owns exactly its own failure class: the timeout bounds the hang, the classified retry repairs the blip, the bucket obeys the quota, and the **circuit breaker** — the one piece with no smaller parts left — stops the fleet from feeding a dead endpoint. The breaker is a three-state machine: **closed** (normal), **open** after N consecutive retryable failures (route around the endpoint entirely), **half-open** after a cooldown (probe it; close on success, reopen on failure). On a 30-call timeline with a brownout across calls 12–18:

```python
N5 = 30
BROWNOUT = range(12, 19)               # calls 12..18 fail 503
CB_N, CB_COOLDOWN = 3, 2               # open after 3 consecutive failures, probe after 2 slots


def call_outcome(i):
    if i in BROWNOUT:
        return "503"
    if i % 7 == 3:
        return "429"
    if i % 11 == 5:
        return "timeout"
    return "ok"


def run(with_breaker):
    ok = attempts = consec = skipped = open_fired = 0
    open_until = -1
    for i in range(N5):
        if with_breaker and i < open_until:
            skipped += 1
            continue
        attempts += 1
        oc = call_outcome(i)
        if oc == "ok":
            ok += 1
            consec = 0
        elif oc in ("503", "timeout"):
            if with_breaker:
                consec += 1
                if consec >= CB_N:
                    open_fired += 1
                    open_until = i + 1 + CB_COOLDOWN
                    consec = 0
                    continue
    return ok, attempts, skipped, open_fired


print(f"F5 campaign: 30 calls, brownout on calls 12-18, breaker N={CB_N} cooldown={CB_COOLDOWN}")
ok_b, att_b, _, _ = run(False)
ok_c, att_c, skipped, open_fired = run(True)
print(f"  unguarded: {att_b} attempts for {ok_b} successes - {att_b - ok_b} calls burn on "
      f"failures, {len(BROWNOUT)} of them straight into the brownout")
print(f"  guarded:   {att_c} attempts for {ok_c} successes, breaker OPEN x{open_fired} "
      f"routing {skipped} calls around the dead endpoint instead of into it")
print("  line: the timeout bounds the call, the retry fixes the blip, the bucket obeys the "
      "quota, the breaker survives the outage - each layer owns exactly its own failure class")
```

Same timeline, two agents. The unguarded one spends all 30 attempts and eats all 12 failures because retrying is all it knows — including 7 attempts straight into a brownout that will outlive its retry budget. The guarded one still lands 18 successes but stops feeding the outage: after three consecutive retryable failures the breaker opens and two calls are routed around the dead endpoint entirely — attempts the agent can spend on work that can succeed. The breaker's cooldown is a tuning surface, not a virtue: too short and the cooldown's expiry just hands the outage more attempts (calls 17–18 here land right after it and fail), too long and healthy traffic is skipped after the endpoint has recovered.

## Known Failure Modes

| Failure | Symptom | The discipline this lesson owns |
|---------|---------|--------------------------------|
| No read timeout on a tool call | Agent turn never returns; one hung server ends the run | Split connect/read budgets — only the read budget catches accepted-then-hung |
| Retrying permanent 4xx | Retry budget burned, same error every attempt | Classify first: 503/timeout/429 retryable, 400/401/404 permanent |
| Retrying a write without an idempotency key | Double charge, double apply | Key the mutation; the server ledger returns the original receipt |
| Backoff without jitter | Fleet-wide synchronized retry waves | Randomize each delay across the exponential range (`wait_random_exponential`) |
| One global timeout | Connect-refused treated like a hang (or a hang unbounded) | `httpx.Timeout(connect, read, write, pool)` — they are different failures |
| `time.sleep` inside an async loop | The wait blocks every task on the loop | Await the backoff (7302's `send_with_jitter`) |
| Bursting past your own quota | 40 429s, each eating a serial Retry-After | Caller-side token bucket: pace into the quota before the wire |
| Breaker cooldown mistuned | Probe burns attempts into the outage, or healthy calls skipped | Tune N and cooldown to the outage's timescale, not to taste |
| Retrying a streamed response | Duplicated partial output | Streams cannot be safely resent — the OpenAI SDK excludes them from auto-retry |

## Summary

- **The turn is the budget.** An un-budgeted read does not make the agent slow, it makes it unterminated: 4/8 answered and never the rest, against 8.6s and 7/8 with a 2.0s read budget.
- **A retry is a bet, and bets need classification.** The 400 never succeeds on any attempt; the 503 does — and the write-side 503 is only safe to retry when an idempotency key makes the second POST a lookup.
- **The exponent paces, the jitter un-syncs.** 0.5s → 1s → 2s → 4s → 8s is one client's climb; forty clients on the same formula land on the same five ticks, and jitter is what spreads the same budget across the window.
- **The bucket you own is cheaper than the bucket you hit.** Blasting a 10 rps quota with 50 calls costs 41.0s of serial Retry-After waits; pacing the same 50 costs 5.0s and zero rejections.
- **The breaker is the layer that stops trying.** Timeout, retry, and bucket all still talk to a dead endpoint; the breaker routes around it — 2 calls never sent, 18 successes either way, and the difference is budget the agent can spend elsewhere.
- **Each layer owns exactly its own failure class** — and the corpus taught none of them at the tool boundary before this lesson.

## References

### Related Minder Academy Documents

- [7201: Tool Calling](./7201-Tool-Calling.md) — the calling mechanism this lesson makes survivable: schemas, registries, and the execution path the timeout wraps.
- [7302: Multi-Agent Communication Protocols](../7300-orchestration/7302-Communication-Protocols.md) — the message-bus form of the discipline: `send_with_jitter`, `Retry-After` honoring, dead-letter queues, and the fleet-level rules list.
- [2303: API Design for ML](../../phase2-foundations/2300-framework-engineering/2303-API-Design-for-ML.md) — the server's half of the contract: return 429 with `Retry-After` so the client's half has something to honor.
- [7504: Agent Abuse Prevention and Identity Threats](../7500-security/7504-Agent-Abuse-Prevention-and-Identity-Threats.md) — the bucket as defense: fixed-window versus token-bucket on the server's side of the wire.
- [QUIZ](./assessment/QUIZ.md) — question 17's production triad, with this lesson as its review pointer.

### Primary Sources

- tenacity documentation — `wait_exponential(multiplier, min, max)` clamping, `wait_random_exponential` as "exponentially increasing jitter", `retry_if_exception_type`, `stop_after_attempt` (tenacity 9.1.4, Apache-2.0).
- urllib3 advanced usage reference — `Retry(total=10, backoff_factor, status_forcelist, allowed_methods, respect_retry_after_header=True, retry_after_max=21600, backoff_max=120)`, the idempotent-verb default for `allowed_methods`, and `RETRY_AFTER_STATUS_CODES = {413, 429, 503}`.
- OpenAI Python SDK README — default `max_retries=2` with a 10-minute request timeout; auto-retry of connection errors and 408/409/429/5xx "when their body can be safely resent"; streams excluded.
- httpx timeouts documentation — `httpx.Timeout(connect, read, write, pool)`, 5-second defaults, and the four distinct timeout exceptions.

## Next Steps

- **Next Module:** [QUIZ](./assessment/QUIZ.md) — question 17's answer is now a set of fences: the hung read bounded at +2.0s, the keyed ledger at 5 receipts, the jittered herd, the 5.0s bucket, and the breaker's OPEN.
- **Continue with:** [7300: Multi-Agent Orchestration](../7300-orchestration/README.md) — where the same discipline meets message buses, deadlock analysis, and human gates (7304).
- **Assessment:** extend the fences — retune the breaker's cooldown until the half-open probe closes on the first try, and price the retry budget the 400-wasting client burns.
