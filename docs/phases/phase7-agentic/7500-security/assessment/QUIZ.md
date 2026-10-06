---
Document ID: 7500-QUIZ
Title: "7500: Agent Security - Quiz"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Advanced
Estimated Time: 30 minutes
Prerequisites: See module README
Related: See module README
Tags: ['assessment', 'quiz', 'agents', 'security']
---

# 7500: Agent Security - Quiz

## Instructions

- **20 questions**
- **Passing score: 80%** (16/20 correct)

---

## Questions

**1. Prompt injection:**

A) Not a threat
B) Normal prompt
C) Only theoretical, confined to research papers with no real-world exploits ever reported
D) Malicious prompt manipulation

**2. Jailbreaking:**

A) Normal use
B) Bypassing safety constraints
C) Not possible
D) Following every rule as written, with no attempt to talk the model out of its guardrails

**3. Tool access control:**

A) Restricted tool access
B) No tools
C) All tools to everyone
D) Unlimited access

**4. Sandboxing:**

A) Not needed
B) Isolated execution environment
C) Full system access, handing the agent every filesystem path and network socket at once
D) No isolation

**5. Input validation:**

A) Optional
B) No validation
C) Accept all input untouched, trusting every caller no matter how the payload is shaped
D) Validate and sanitize

**6. Output filtering:**

A) Check for harmful content
B) Only filter error messages, letting every other response pass through completely unchecked
C) Not useful
D) No filtering

**7. Rate limiting prevents:**

A) Nothing
B) Abuse and resource exhaustion
C) Not needed
D) Normal use, which is claimed to collapse the moment any request limit is ever applied

**8. Agent impersonation:**

A) Pretending to be trusted entity
B) Not possible
C) Only by humans
D) Not a threat at all, since every agent identity is assumed unforgeable by default

**9. Exfiltration risks:**

A) Not a concern
B) No data leaks
C) Only external attackers, with nothing ever leaking through a cooperating internal agent
D) Data extraction by malicious agents

**10. Audit logging:**

A) Track agent actions
B) No logging
C) Optional
D) Only errors, with every successful action assumed too boring to ever be worth recording

**11. Red teaming for agents:**

A) No testing
B) Only unit testing
C) Adversarial testing
D) Not needed

**12. Constitutional AI:**

A) Only external monitoring
B) Not for agents at all, since constitutions are claimed useless outside pure chatbots
C) No constraints
D) Self-harm limiting principles

**13. Tool output validation:**

A) Check tool results
B) Accept all outputs
C) Only check errors
D) Not needed, because every tool is trusted to return safe and well-formed results always

**14. Context injection:**

A) Only internal
B) Normal context, holding no capability to steer the model toward any attacker goal
C) Malicious context manipulation
D) Not possible

**15. Indirect prompt injection:**

A) Direct attack
B) No injection
C) Through data/documents
D) Same as direct

**16. Agent privilege levels:**

A) Only human
B) All the same, with every agent granted identical rights regardless of its duties
C) Different access levels
D) No levels

**17. Deterministic output:**

A) Unpredictable
B) Random
C) Not possible, since sampling is claimed to destroy reproducibility under every seed
D) Predictable for testing

**18. Agent monitoring:**

A) Optional
B) Only performance, with behavior signals like tool misuse never entering any dashboard
C) Track agent behavior
D) No monitoring

**19. Adversarial robustness:**

A) No robustness
B) Resist attacks
C) Only for training
D) Not relevant

**20. Security by design:**

A) Only for production
B) Built-in from start
C) Not needed
D) Afterthought, bolted on late in shipping once the first incident report has landed

---

## Answer Key

| Question | Answer | Explanation |
|----------|--------|-------------|
| 1 | D | Prompt injection manipulates prompts maliciously |
| 2 | B | Jailbreaking talks the model past its safety rules |
| 3 | A | Tool access is restricted by role and need |
| 4 | B | Sandboxing isolates execution from the host |
| 5 | D | Inputs are validated and sanitized before use |
| 6 | A | Output filtering screens for harmful content |
| 7 | B | Rate limits curb abuse and resource exhaustion |
| 8 | A | Impersonation fakes a trusted agent identity |
| 9 | D | Exfiltration extracts data through malicious agents |
| 10 | A | Audit logs track every agent action |
| 11 | C | Red teaming runs adversarial attacks against the agent |
| 12 | D | Constitutional AI limits behavior with principles |
| 13 | A | Tool outputs are validated before use |
| 14 | C | Context injection steers the model via manipulated context |
| 15 | C | Indirect injection arrives inside data and documents |
| 16 | C | Agents hold different privilege levels by role |
| 17 | D | Deterministic output gives predictable test runs |
| 18 | C | Monitoring tracks behavior beyond plain performance |
| 19 | B | Robustness means resisting adversarial attacks |
| 20 | B | Security is built in from the start, not bolted on |

---

## Need to Review?

Each question maps to the closest lesson for review:

- **Questions 1, 14-15:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the taxonomy splitting direct injection, indirect injection and jailbreaks, untrusted text smuggled in as instructions, and the indirect carriers where attacks arrive inside data sources and documents
- **Question 2:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the Jailbreak Techniques section's four bypass templates talking the model past its safety rules
- **Questions 3, 16:** [7201: Tool Calling & Function Execution](../../7200-tools/7201-Tool-Calling.md) — the Permission System's check_permission gates scoping which tools each caller may reach, cross-module from this module's defense lessons
- **Question 4:** [7201: Tool Calling & Function Execution](../../7200-tools/7201-Tool-Calling.md) — the Sandboxing section's builtins-stripping isolation between generated code and the host system
- **Question 5:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the Input Filtering and Sanitization layer validating payloads before they reach the model
- **Questions 6, 13:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the Output Validation layer screening what comes back for harm and instruction leakage before any result is used
- **Question 7:** [7504: Agent Abuse Prevention and Identity Threats](../7504-Agent-Abuse-Prevention-and-Identity-Threats.md) — the fixed-window-vs-token-bucket fence where the same 54-request trace splits 41/13 against 45/9 and the seam volley passes 6/6 under the window while the bucket holds 5/6; the checklist gate the mechanics implement lives in [7501](../7501-Prompt-Injection-Defense.md)
- **Question 8:** [7504: Agent Abuse Prevention and Identity Threats](../7504-Agent-Abuse-Prevention-and-Identity-Threats.md) — the impersonation fence where a one-field sender flip moves the auditor's capability onto an intern's message (unsigned bus EXECUTES) while the HMAC-signed bus with per-agent keys and a replay nonce REJECTS at the signature line; prompt-side identity integrity stays in [7501](../7501-Prompt-Injection-Defense.md)
- **Question 9:** [7504: Agent Abuse Prevention and Identity Threats](../7504-Agent-Abuse-Prevention-and-Identity-Threats.md) — the egress fences where a validly-signed compromised agent beacons at CV 0.008 against a human-paced 0.99, a payload entropy sweep over-flags benign prose at 3.5 bits/char but catches the credential blob at 4.5, and the composed campaign splits 23 accepted / 7 signature-reject / 5 beacon-FLAGGED; the injection carriers that start the compromise stay in [7501](../7501-Prompt-Injection-Defense.md)
- **Question 10:** [7502: PII Redaction & Privacy Filtering](../7502-PII-Redaction.md) — the GDPR audit trail where every detection, access and deletion is an auditable event recording metadata only
- **Question 11:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the Red Team Testing suite attacking the pipeline with seven labeled payloads as its regression test
- **Question 12:** [5204: Preference Dataset Creation](../../../phase5-finetuning/5200-alignment/5204-Preference-Dataset-Creation.md) — the synthetic-preferences judge guided by written principles in Constitutional AI style, cross-phase into the alignment module; Constitutional AI itself appears only as that style reference, so Q12 leans on principle-guided RLAIF as its closest teaching
- **Question 17:** [7505: Temperature Zero and Deterministic Security Testing](../7505-Temperature-Zero-and-Deterministic-Security-Testing.md) — the deterministic-first discipline Q17 turns on, now with mechanics: temperature zero is argmax (1 unique output in 2,000 draws), the identical-code suite flapping 33 red / 17 green at T=0.7, and the fingerprint bump flipping 3/7 greedy decisions; the pipeline ordering itself stays in [7501](../7501-Prompt-Injection-Defense.md)
- **Question 18:** [1503: LLM Observability](../../../phase1-infra/1500-monitoring/1503-LLM-Observability.md) — latency, token, cost and quality-flag metrics as the monitoring surface, matching this module's checklist gate for logging and monitoring to stay active
- **Question 19:** [7503: Adversarial Attacks & Defense](../7503-Adversarial-Attacks.md) — adversarial training hardening the model and the secure inference pipeline that flags perturbed inputs at serve time
- **Question 20:** [7501: Prompt Injection Defense](../7501-Prompt-Injection-Defense.md) — the four-layer design where defense is the composition, with the Production Checklist wiring filtering, validation, guardrails and response into the build from the start
