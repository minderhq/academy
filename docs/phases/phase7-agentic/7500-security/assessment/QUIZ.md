---
Document ID: 7500-QUIZ
Title: "7500: Agent Security - Quiz"
Last Updated: 2026-09-29
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
