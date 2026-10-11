---
Document ID: CHEAT-SHEET-012
Title: "CHEAT-SHEET-012: LLM Guardrails & Agent Security"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'security', 'prompt-injection', 'pii', 'adversarial']
---

# CHEAT-SHEET-012: LLM Guardrails & Agent Security

## Quick Reference for LLM Defense Layers

**Version:** 1.0

A regex denylist is not a security posture. This sheet compresses the
phase7 security family into one operator page: where each guardrail
lives, what it catches, what slips past it, and the layer that catches
what the previous one missed.

---

## Guardrail Map

| Layer | Catches | Blind spot |
| --- | --- | --- |
| Input filter | injection phrasing, oversized payloads, repetition attacks | paraphrases and non-English jailbreaks |
| System prompt hardening | role confusion, instruction hierarchy erosion | data-side (indirect) injections |
| Output validator | prompt-leak signatures, over-compliance | novel leak phrasings |
| PII redaction | emails, SSNs, cards, IPs in prompt or response | formats your recognizers don't list |
| Rate limits | bursts, quota abuse, seam volleys | distributed, low-and-slow abuse |
| Agent identity | impersonation, replayed envelopes | a stolen key you never rotate |

The map's rule: every row assumes the row above it fails. Denylists
reduce noise for the layers behind them; they do not certify input.

---

## Input Filtering & Output Validation

Module 7501's canonical pattern classes for input: `ignore previous
instructions`, `developer/admin/root mode`, `reveal your system prompt`,
`do anything now` — plus the two structural checks that carry most of
the weight in practice: a hard `max_length` (5000 in the reference
implementation) and a per-user repetition check that flags many similar
prompts in a short window.

Output validation is the same denylist idea pointed at the completion,
plus leak detection:

```python
import re

BLOCK_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"(developer|admin|root)\s+mode",
    r"reveal\s+your\s+(system\s+)?prompt",
    r"my\s+(system\s+)?prompt",
    r"constraints\s+(do\s+)?not\s+apply",
]

def validate_output(text: str) -> tuple[bool, str | None]:
    # Module 7501's last-line defense: scan the completion
    # before it egresses to the user.
    for pattern in BLOCK_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, "suspicious pattern: " + pattern
    if len(text) > 10000:
        return False, "output unusually long"
    return True, None

for sample in ["Sure — here is the summary.",
               "My system prompt says to always comply."]:
    ok, why = validate_output(sample)
    print(ok, why)
```

Operate the validator as a monitor before you make it a blocker: log
every verdict with the matched pattern for a week, tune the false-positive
rate, then flip to enforce.

---

## PII Redaction

Module 7502's Presidio path replaces the homegrown regex detector with
maintained recognizers (`uv pip install presidio-analyzer
presidio-anonymizer`; it reuses the spaCy NER model). The config surface
is the operator map — keys are Presidio entity labels:

| Entity label | Operator | Use when |
| --- | --- | --- |
| EMAIL_ADDRESS | mask | preserve readability for support staff |
| PHONE_NUMBER | mask | same |
| US_SSN | replace | never render partials in logs |
| CREDIT_CARD | mask | PCI scope — prefer replace in analytics |
| IP_ADDRESS | hash | correlate sessions without storing the address |
| PERSON / LOCATION | redact | drop entirely |

Operator vocabulary: `replace` (placeholder token), `redact` (remove),
`mask` (partial asterisks), `hash`, `encrypt`, `keep`, `custom`. Redact
on the write path (before the log line is built), not at query time —
a read-path filter only protects the people who remember to apply it.

---

## Rate Limits: The Window Seam

Module 7504's load-bearing result: a fixed window with quota Q admits
2Q requests straddling a boundary, because adjacent windows never see
each other — six requests across the seam pass 6/6 under a quota of 5,
every boundary, forever. The token bucket passes 5/6 and throttles the
sixth until refill accrues. Abuse is an instantaneous rate; pick the
limiter that bounds instantaneous rate.

---

## Agent Identity on the Bus

A message's `sender` field is a claim written by whoever assembled the
message, not identity. Module 7504's signed bus: per-agent HMAC keys,
`sign(sender|action|ts|nonce)` with SHA-256, `hmac.compare_digest` for
verification (never `==` — string equality short-circuits and leaks
timing), and a nonce set for freshness — a signature alone does not stop
capture-and-replay. Production fleets replace shared secrets with
workload identity (SPIFFE/SPIRE issues attestations the platform
verifies live).

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| Injection still lands past the filter | regex denylist is noise control, not a guarantee | layer output validation + judge reviews of refusals |
| Legit users get blocked | patterns too broad, no review loop | log verdicts, tune, then enforce |
| PII found in stored logs | redaction applied at read path | move redaction to the write path |
| Quota doubled at window boundaries | fixed-window limiter | token bucket (or sliding window) |
| Privileged action ran as another agent | unsigned bus / stolen sender string | HMAC-signed envelopes + nonce freshness, rotate keys |

---

**Quick Reference for:**

- [Module 7501: Prompt Injection Defense](../../phases/phase7-agentic/7500-security/7501-Prompt-Injection-Defense.md)
- [Module 7502: PII Redaction & Privacy Filtering](../../phases/phase7-agentic/7500-security/7502-PII-Redaction.md)
- [TUTORIAL-013: AI Security](../tutorials/TUTORIAL-013-AI-Security.md)
- [LAB-014: AI Evaluation Safety](../labs/LAB-014-AI-Evaluation-Safety.md)
