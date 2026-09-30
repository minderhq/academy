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

| # | Answer |
|---|--------|
| 1 | D |
| 2 | B |
| 3 | A |
| 4 | B |
| 5 | D |
| 6 | A |
| 7 | B |
| 8 | A |
| 9 | D |
| 10 | A |
| 11 | C |
| 12 | D |
| 13 | A |
| 14 | C |
| 15 | C |
| 16 | C |
| 17 | D |
| 18 | C |
| 19 | B |
| 20 | B |
