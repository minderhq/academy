---
Document ID: 7504
Title: "7504: Agent Abuse Prevention and Identity Threats"
Phase: 7
Module: 7500
Last Updated: 2026-10-06
Status: Complete
Difficulty: Advanced
Estimated Time: 3 hours
Tags: ['agents', 'security', 'prompt-injection', 'pii', 'adversarial']
---

# 7504: Agent Abuse Prevention and Identity Threats

## Table of Contents

- [Abstract](#abstract)
- [Learning Objectives](#learning-objectives)
- [The Checklist Item Is Not a Mechanic](#the-checklist-item-is-not-a-mechanic)
- [Who Is Calling? Agent Identity on the Bus](#who-is-calling-agent-identity-on-the-bus)
- [The Beacon in the Egress Log](#the-beacon-in-the-egress-log)
- [Payload-Side Signals](#payload-side-signals)
- [Defense in Depth on One Campaign](#defense-in-depth-on-one-campaign)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

## Learning Objectives

By the end of this lesson, you will be able to:

- Implement rate limiting as arithmetic — fixed windows, token buckets, and the seam volley that defeats the window shape
- Explain why a trusted `sender` field is not identity, and harden a message bus with keyed signatures and replay protection
- Detect machine-regular beaconing in an egress log with the coefficient of variation
- Scan outbound payloads for high-entropy material and know exactly how far entropy alone gets you
- Compose the three layers on one campaign and name the attack each layer owns
- Name the blind spot no transport layer can close — the authorized reader — and where that problem actually lives

## Abstract

The module's own QUIZ admits three gaps this lesson fills: sustained abuse-prevention mechanics beyond [7501](7501-Prompt-Injection-Defense.md)'s `Rate limiting configured` checkbox are taught nowhere in the curriculum (Q7), agent impersonation as a named attack class is taught nowhere in the curriculum (Q8), and data exfiltration by malicious agents is taught nowhere in the curriculum as a named threat (Q9). What the checkbox hides is arithmetic, a field flip, a timing signature, and an entropy table — each one small enough to run as code, and each one deciding whether an attack lands. [7501](7501-Prompt-Injection-Defense.md) teaches the prompt-side layers and [7503](7503-Adversarial-Attacks.md) teaches quarantine and the human gate; this lesson teaches the mechanics those layers point at when the attacker is not the text but the traffic, the sender field, the egress rhythm, or the payload itself.

## The Checklist Item Is Not a Mechanic

[7501's Production Checklist](7501-Prompt-Injection-Defense.md) carries one line for the whole subject: `Rate limiting configured`. The line is necessary and empty — it does not say which shape, and the shapes fail differently. The fixed window is the shape everyone writes first: allow N per clock bucket. The token bucket is the shape production rate limiters ship (the `limits` library at 5.8.0 on PyPI and `slowapi` at 0.1.10 both build on it): a bucket of capacity `b` that refills at `r` tokens per second, where each request consumes one token.

Run both over the same 54-request trace — forty steady requests plus a fourteen-request burst slamming in inside 0.8 seconds — under the same 5-per-5-seconds policy:

```python
import numpy as np
from collections import Counter

rng = np.random.default_rng(13)
steady = rng.uniform(0, 60, 40)
burst = 12.0 + rng.uniform(0, 0.8, 14)
arrivals = np.sort(np.concatenate([steady, burst]))

def fixed_window(arrivals, limit, win):
    allowed, counts = [], Counter()
    for t in arrivals:
        w = int(t // win)
        if counts[w] < limit:
            allowed.append(t); counts[w] += 1
    return allowed

def token_bucket(arrivals, capacity, refill_per_s):
    allowed, tokens, last = [], float(capacity), 0.0
    for t in arrivals:
        tokens = min(capacity, tokens + (t - last) * refill_per_s)
        last = t
        if tokens >= 1:
            tokens -= 1; allowed.append(t)
    return allowed

fw_a = fixed_window(arrivals, 5, 5.0)
tb_a = token_bucket(arrivals, 5, 1.0)
print(f"fixed window : {len(fw_a)} pass, {len(arrivals)-len(fw_a)} denied")
print(f"token bucket : {len(tb_a)} pass, {len(arrivals)-len(tb_a)} denied")
# the seam: 6 requests straddling a window boundary, policy quota 5
seam = [4.99, 5.00, 5.01, 5.02, 5.03, 5.04]
fw_seam = len(fixed_window(seam, 5, 5.0))
tb_seam = len(token_bucket(seam, 5, 1.0))
print(f"seam volley (6 requests, quota 5): fixed {fw_seam}/6 pass")
print(f"                                   bucket {tb_seam}/6 pass (6th waits ~1 s of refill)")
```

The aggregate counts look like a preference, not a law — the fixed window denied 13 and the bucket denied 9 because the bucket carries leftover capacity across time instead of burning it at each boundary. The law is the seam volley: six requests placed across a window boundary pass **6/6** under the fixed window, because two adjacent windows each see at most 5 and neither knows about the other — double the stated quota in under a second, every boundary, forever. The token bucket passes 5/6 and throttles the sixth until roughly one second of refill accrues. That is the whole argument for the bucket shape: it bounds the instantaneous rate, and the instantaneous rate is what abuse is. A burst that exhausts a downstream model endpoint does not care that your dashboard shows a healthy per-window average.

## Who Is Calling? Agent Identity on the Bus

Multi-agent systems pass messages whose `sender` field is a string the receiver trusts. That string is not identity — it is a claim, and a claim written by whoever assembled the message. The attack class has a name: agent impersonation. One field flip moves every capability the impersonated agent holds onto the attacker's message.

```python
import hashlib
import hmac

KEYS = {"auditor": b"k-auditor-7f31", "archivist": b"k-archiv-2c90", "intern": b"k-intern-551a"}
CAPS = {"auditor": {"delete_records"}, "archivist": set(), "intern": set()}

def unsigned_bus(msg):
    allowed = CAPS.get(msg["sender"], set())
    if msg["action"] in allowed:
        return f"EXECUTED {msg['action']} as {msg['sender']}"
    return "denied (no capability)"

def sign(sender, action, ts, nonce, key):
    body = f"{sender}|{action}|{ts}|{nonce}".encode()
    return hmac.new(key, body, hashlib.sha256).hexdigest()

def signed_bus(msg, nonce_seen):
    body = f"{msg['sender']}|{msg['action']}|{msg['ts']}|{msg['nonce']}".encode()
    want = hmac.new(KEYS.get(msg["sender"], b""), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(want, msg["sig"]):
        return "REJECTED (signature mismatch)"
    if msg["nonce"] in nonce_seen:
        return "REJECTED (replay)"
    nonce_seen.add(msg["nonce"])
    allowed = CAPS.get(msg["sender"], set())
    return f"EXECUTED {msg['action']} as {msg['sender']}" if msg["action"] in allowed else "denied (no capability)"

intern_msg = {"sender": "intern", "action": "delete_records", "ts": 1000, "nonce": "n1"}
stolen = dict(intern_msg, sender="auditor", sig="0" * 64)  # field flip + guessed signature
print("unsigned bus:", unsigned_bus(stolen))
seen = set()
sig = sign("auditor", "delete_records", 1000, "n2", KEYS["auditor"])
ok = {"sender": "auditor", "action": "delete_records", "ts": 1000, "nonce": "n2", "sig": sig}
print("signed bus  :", signed_bus(stolen, seen))
print("real auditor:", signed_bus(ok, seen))
print("replayed    :", signed_bus(ok, seen))
```

The unsigned bus executes `delete_records as auditor` off a message an intern assembled — the capability check ran, and ran correctly, against a stolen name. The signed bus rejects the same flip at the signature line before any capability question is asked, because the attacker does not hold `k-auditor-7f31` and a guessed signature is not the keyed digest. The real auditor's envelope passes unchanged, and the replay of that same envelope fails on the nonce: capture-and-replay is the second half of the attack, and a signature alone does not stop it — freshness state does. `hmac.compare_digest` is the comparison to use, not `==`; string equality short-circuits and leaks timing. Per-agent symmetric keys are the teaching form; production fleets reach for workload identity instead of shared secrets — SPIFFE/SPIRE issues attestations the platform verifies live rather than keys an attacker can lift from a config — and the fence's job is to show the property any of those systems must deliver: the sender field is proven, not read.

## The Beacon in the Egress Log

A signed, authorized agent that has been compromised does not need to forge anything — it calls home. The exfiltration channel with a name is the beacon: outbound calls on a machine-regular schedule, because the malicious loop is a timer, not a person. Humans are irregular. Timers are not, and the irregularity difference is one number.

```python
import numpy as np

rng = np.random.default_rng(23)
legit = np.sort(rng.uniform(0, 8 * 3600, 60))          # 60 human-paced calls in 8 h
base = np.arange(300, 8 * 3600, 300.0)
beacon = base + rng.uniform(-2, 2, len(base))          # 300 s beacon, 2 s clock drift

def interval_stats(ts):
    iv = np.diff(ts)
    return iv.mean(), iv.std() / iv.mean()             # mean interval, CV

lm, lcv = interval_stats(legit)
bm, bcv = interval_stats(beacon)
print(f"legit  : {len(legit)} calls, mean interval {lm:.0f} s, CV {lcv:.2f}")
print(f"beacon : {len(beacon)} calls, mean interval {bm:.0f} s, CV {bcv:.3f}")
hb, _ = np.histogram(beacon[1:] - beacon[:-1], bins=np.arange(0, 700, 10))
hl, _ = np.histogram(legit[1:] - legit[:-1], bins=np.arange(0, 700, 10))
print(f"modal 10 s bin share: beacon {hb.max()/len(hb):.2f} vs legit {hl.max()/len(hl):.2f}")
```

The coefficient of variation — standard deviation divided by mean — is the whole detector: 0.99 for the human-paced agent, 0.006 for the beacon, two orders of magnitude apart. The histogram says the same thing as a shape: 71 percent of the beacon's intervals land in a single 10-second bin against 4 percent for the legitimate traffic. Neither number looks at payload bytes, so the detection survives encryption, and neither looks at volume, so a low-and-slow beacon that stays under volume alerts still trips it. This is the same egress surface [7104's budget fence](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) instruments — there the question was how much the agent spends, here it is how regularly it spends.

## Payload-Side Signals

Timing is one side of egress; bytes are the other. The classic payload signal is Shannon entropy over the characters of a field value — credentials and their encodings spend the character alphabet evenly, human text does not.

```python
import math
from collections import Counter

fields = [
    ("summary", "quarterly churn report for the emea region"),
    ("recipient", "ops-team@company.internal"),
    ("attachment_note", "see attached deck slide 4"),
    ("config_blob", "Zx9$kQ2mN7#pL4vR8wT5yB3jH6fD0sA1uE"),
    ("trace_id", "9f86d081884c7d659a2feaa0c55ad015"),
]

def shannon(s):
    c = Counter(s)
    n = len(s)
    return -sum(v / n * math.log2(v / n) for v in c.values())

for thr in (3.5, 4.5):
    flagged = [f for f, v in fields if shannon(v) >= thr]
    print(f"entropy scan @ {thr} bits/char -> flags {flagged}")
for f, v in fields:
    print(f"  {shannon(v):4.2f}  {f}")
```

At a 3.5 threshold the scan flags four of the five fields — including `summary` at 3.77 and `recipient` at 3.86, both perfectly ordinary. Natural text of this length sits at 3.3–3.9 bits per character because a few dozen characters of prose already spread across much of the alphabet; the credential blob's 5.09 is high, but high-enough-to-flag is not high-enough-to-be-a-secret. At 4.5 the scan flags exactly the blob and passes everything else — and passes the hex `trace_id` at 3.64, which is fine here and would not be if that hex were a hash of something sensitive. Entropy alone is a prior, not a verdict: the production pattern pairs it with field allowlists (a `config_blob` field is suspicious at any entropy) and decodability checks (does it base64-decode?) — the layering [7502's detector stack](7502-PII-Redaction.md) already applies to PII, with presidio-analyzer at 2.2.364 as the working reference.

## Defense in Depth on One Campaign

Three layers, one campaign — eighteen legitimate requests, seven forged-identity attempts, and five beacon calls from a compromised agent whose signatures are all **valid**, because the compromise lives in the agent process, not in its keys:

```python
import numpy as np
import hashlib
import hmac
from collections import Counter

rng = np.random.default_rng(37)
KEYS = {"worker": b"k-worker-91de", "auditor": b"k-auditor-7f31"}
CAPS = {"worker": {"read_docs"}, "auditor": {"delete_records"}}

def sign(sender, action, ts, nonce, key):
    body = f"{sender}|{action}|{ts}|{nonce}".encode()
    return hmac.new(key, body, hashlib.sha256).hexdigest()

def verify(msg):
    body = f"{msg['sender']}|{msg['action']}|{msg['ts']}|{msg['nonce']}".encode()
    want = hmac.new(KEYS.get(msg["sender"], b""), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, msg.get("sig", ""))

campaign = []
for i, t in enumerate(sorted(rng.uniform(0, 600, 18))):
    campaign.append({"kind": "normal", "msg": {"sender": "worker", "action": "read_docs",
                      "ts": t, "nonce": f"w{i}", "sig": sign("worker", "read_docs", t, f"w{i}", KEYS["worker"])}})
for i, t in enumerate(sorted(rng.uniform(0, 600, 7))):
    campaign.append({"kind": "forged", "msg": {"sender": "auditor", "action": "delete_records",
                      "ts": t, "nonce": f"f{i}", "sig": "0" * 64}})
beacon_t = 700.0 + np.arange(5) * 300.0 + rng.uniform(-2, 2, 5)
for i, t in enumerate(beacon_t):
    campaign.append({"kind": "beacon", "msg": {"sender": "worker", "action": "read_docs",
                      "ts": t, "nonce": f"b{i}", "sig": sign("worker", "read_docs", t, f"b{i}", KEYS["worker"])}})

verdicts = Counter()
egress_ts = []
for c in campaign:
    m = c["msg"]
    if not verify(m):
        verdicts["signature reject (forged identity)"] += 1
        continue
    if CAPS.get(m["sender"], set()) and m["action"] not in CAPS[m["sender"]]:
        verdicts["authorization deny"] += 1
        continue
    verdicts["accepted"] += 1
    if c["kind"] == "beacon":
        egress_ts.append(m["ts"])

iv = np.diff(sorted(egress_ts))
cv = iv.std() / iv.mean()
flag = cv < 0.1 and len(egress_ts) >= 4
for k, v in verdicts.most_common():
    print(f"{v:2d}  {k}")
print(f"egress: {len(egress_ts)} accepted outbound calls, mean interval {iv.mean():.0f} s, CV {cv:.3f}")
print(f"beacon verdict: {'FLAGGED (machine-regular timing)' if flag else 'missed'}")
```

Twenty-three accepted, seven rejected at the signature line — and the five beacon calls sailed through identity and authorization with perfect credentials, exactly as designed. The egress monitor caught them anyway: five outbound calls at a mean interval of 300 seconds with a CV of 0.008, machine-regular, flagged. Each layer owns one attack class and is blind to the others — signatures see the sender, capability checks see the action, the egress monitor sees the rhythm — and the lesson's closing fact is the one the fence cannot show: the same validly-signed agent exfiltrating at human-irregular pace, inside fields it is authorized to read, passes every layer in this fence. That threat lives in authorization scope and payload content review — [7201's permission system](../7200-tools/7201-Tool-Calling.md) and [7502's redaction pipeline](7502-PII-Redaction.md), with [7503's quarantine-and-human-review gate](7503-Adversarial-Attacks.md) as the escalation path when any layer fires.

## Known Failure Modes

| Failure | Symptom | Fix |
|---------|---------|-----|
| Fixed window at the seam | Two windows each within quota, 2x burst across the boundary | Token bucket — bounds the instantaneous rate, not the per-window count |
| Trusting the `sender` field | Capability check passes against a stolen name | Keyed signature over the full envelope; the sender is proven, never read |
| `==` on signature comparison | Timing oracle leaks digest prefix matches | `hmac.compare_digest` — constant-time comparison |
| Signature without freshness | Captured envelope replayed verbatim, signature valid | Nonce/timestamp replay window checked statefully |
| Entropy threshold set low | Benign prose flagged at 3.5 bits/char; alert fatigue | 4.5+ plus field allowlists and decodability checks, never entropy alone |
| Volume-only egress alerts | Low-and-slow beacon stays under volume caps | CV-based periodicity detection — timing survives encryption and small volume |
| Per-agent secrets in configs | Lifted key makes every signature forgeable | Workload identity (SPIFFE/SPIRE) — attested, not stored |
| Rate limit on the wrong resource | Burst exhausts the model endpoint while the API gateway stays green | Bucket the expensive downstream call, not the cheap front door |

## Summary

- Rate limiting is arithmetic with a failure mode per shape: the fixed window doubles its quota across every seam (6/6 on the volley), the token bucket bounds the instant (5/6) — the shape is the defense.
- A `sender` field is a claim; a keyed signature over the full envelope with `hmac.compare_digest` and a replay window makes it a proof — the field flip dies at the signature line, and the replay dies at the nonce.
- Compromised agents call home on timer rhythm: coefficient of variation 0.006 against a human 0.99, one number, payload-blind, encryption-proof.
- Entropy is a prior at best: the 3.5 scan flags 4 of 5 fields and 3 of the 4 are benign; at 4.5 it catches the credential blob and nothing else — pair it with allowlists and decodability.
- On one campaign each layer caught exactly its own class — 7 forged at the signature, 5 validly-signed beacons at the egress monitor — and the authorized-reader exfiltration passed all of them, because that threat lives in permission scope, not transport.

## References

### Related Minder Academy Documents

- [7501: Prompt Injection Defense](7501-Prompt-Injection-Defense.md) — the Production Checklist item this lesson implements, and the prompt-side layers that run before these mechanics
- [7502: PII Redaction & Privacy Filtering](7502-PII-Redaction.md) — the payload-content review and detector layering that closes part of the authorized-reader blind spot
- [7503: Adversarial Attacks & Defense](7503-Adversarial-Attacks.md) — quarantine and the human-review gate these monitors escalate into
- [7201: Tool Calling & Function Execution](../7200-tools/7201-Tool-Calling.md) — the permission system that owns authorization scope, the blind spot no transport layer covers
- [7104: Agent Evaluation and Observability](../7100-architecture/7104-Agent-Evaluation-and-Observability.md) — the egress instrumentation surface these detectors run on

### Primary Sources

- Python `hmac` module — `hmac.compare_digest`, the constant-time comparison, Python 3.13 standard library
- `limits` 5.8.0 and `slowapi` 0.1.10 (PyPI) — production rate-limiting stacks built on the token-bucket shape
- SPIFFE/SPIRE — workload identity via platform attestation; the production answer to per-agent shared secrets
- Microsoft Presidio, presidio-analyzer 2.2.364 (PyPI) — the detector-stacking pattern for payload-side review

## Next Steps

- **Next Module:** continue with [assessment/QUIZ.md](assessment/QUIZ.md) — Q7, Q8, and Q9 are the three questions this lesson's fences answer with mechanics
- **Continue with:** [7100: Agent Architecture](../7100-architecture/README.md) for the loop-side view of what a compromised agent actually executes
- **Assessment:** extend the campaign fence with a fourth attack class — the authorized-reader exfiltration — and a layer that catches it
