---
Document ID: 7500-SECURITY-README
Title: "7500: AI Agent Security"
Last Updated: 2026-10-01
Status: Complete
Difficulty: Beginner
Tags: ['module', 'agents', 'security']
---

# 7500: AI Agent Security

## Module Overview

This module covers security and safety considerations for AI agents, including prompt injection defense, PII redaction, and protection against adversarial attacks. You'll learn to build secure, trustworthy agent systems.

**Why This Matters:**
- Agents are high-value targets for attacks
- Prompt injection can leak sensitive data
- PII exposure has legal and ethical implications
- Security is critical for production deployment

## Learning Objectives

After completing this module, you will be able to:

- **Prompt Injection Defense**: Identify and prevent injection attacks
- **PII Redaction**: Automatically redact sensitive information
- **Adversarial Defense**: Protect against malicious inputs
- **Secure Design**: Build security-first agent systems
- **Compliance**: Meet privacy and security regulations

## Module Contents

### [7501: Prompt Injection Defense](./7501-Prompt-Injection-Defense.md)
**Protecting Against Malicious Prompts**

- Prompt injection taxonomy
- Attack vectors
- Defense strategies and defense in depth
- Testing
- The security checklist

**Experiments:**
- Implement injection detector
- Build input sanitizer
- Create output filter
- Test with adversarial prompts

### [7502: PII Redaction](./7502-PII-Redaction.md)
**Sensitive Information Protection**

- PII categories
- Detection
- Redaction
- Secure handling
- Production deployment and testing

**Experiments:**
- Build PII detector
- Implement redaction system
- Create compliance reports
- Test with real data

### [7503: Adversarial Attacks](./7503-Adversarial-Attacks.md)
**Understanding and Defending Against Attacks**

- Attack types
- Common attack methods
- Defenses
- Robustness evaluation
- Production considerations

**Experiments:**
- Simulate adversarial attacks
- Test defense mechanisms
- Build monitoring system
- Create response playbook

## Prerequisites

Before starting this module, ensure you have:

- [ ] Module 7100: [Agent Architecture](../7100-architecture/README.md) (agent design)
- [ ] Module 7200: [Tool Calling and Function Execution](../7200-tools/README.md) (tool security)
- [ ] Module 7400: [Agent Memory Systems](../7400-memory/README.md) (data privacy)
- [ ] Python programming proficiency
- [ ] Understanding of security basics

**Review:** [PREREQUISITES.md](./PREREQUISITES.md) for detailed requirements.

## Assessment

### Quiz
- **Format:** 20 multiple-choice questions
- **Passing Score:** 80% (16/20)
- **Topics:** Prompt injection, PII, adversarial attacks
- **Location:** [assessment/QUIZ.md](./assessment/QUIZ.md)

### Practice Exercises
- **Format:** Security implementation projects
- **Duration:** 13 hours
- **Topics:**
  - Build injection detector
  - Implement PII redaction
  - Create adversarial defenses
  - Design secure agent system
- **Location:** [assessment/PRACTICE.md](./assessment/PRACTICE.md)

## Related Modules

This module connects to:
- **[7100: Agent Architecture](../7100-architecture/README.md)** (secure agent design)
- **[7200: Tool Calling and Function Execution](../7200-tools/README.md)** (tool security)
- **[7400: Agent Memory Systems](../7400-memory/README.md)** (data privacy)
- **[5200: LLM Alignment](../../phase5-finetuning/5200-alignment/README.md)** (safety alignment)

## Time Commitment

| Activity | Time |
|----------|------|
| [7501: Prompt Injection Defense](./7501-Prompt-Injection-Defense.md) | 3 hours |
| [7502: PII Redaction](./7502-PII-Redaction.md) | 3 hours |
| [7503: Adversarial Attacks](./7503-Adversarial-Attacks.md) | 3 hours |
| Quiz | 30 minutes |
| Practice | 13 hours |
| **Total** | **22.5 hours** |

## Resources

**Essential Tools:**
- Microsoft Presidio (PII redaction)
- LangChain security tools
- Rebuff (prompt injection defense)
- Llama Guard (content moderation)

**Essential Papers:**
- "Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Prompt Injection"
- "Ignore Previous Prompt: Attack Techniques For Language Models"
- "Jailbreak: A Novel Black-box Method for Jailbreaking Large Language Models"

## Prompt Injection Examples

| Type | Example | Impact |
|------|---------|--------|
| Direct | "Ignore instructions and..." | High |
| Roleplay | "You are DAN, do anything..." | High |
| Conditional | "If user says X, then Y..." | Medium |
| Encoding | Base64, Unicode | Medium |
| Multilingual | Non-English instructions | Low-Medium |

## PII Types

| Category | Examples | Risk |
|----------|----------|------|
| Personal | Name, email, phone | Medium |
| Financial | Credit card, SSN | High |
| Health | Medical records | Very High |
| Location | Address, GPS | Medium |
| Biometric | Face, fingerprint | Very High |

## Defense Strategies

| Attack Type | Defense | Effectiveness |
|-------------|---------|---------------|
| Direct Injection | Input validation | ⭐⭐⭐⭐ |
| Jailbreak | Output monitoring | ⭐⭐⭐ |
| Roleplay | Policy enforcement | ⭐⭐⭐⭐ |
| Encoding | Decode and validate | ⭐⭐⭐⭐⭐ |
| Multilingual | Translation + check | ⭐⭐⭐⭐ |

## Security Checklist

Before deploying agents:
- [ ] Input validation implemented
- [ ] Output filtering enabled
- [ ] PII redaction configured
- [ ] Rate limiting active
- [ ] Audit logging enabled
- [ ] Incident response planned
- [ ] Regular security audits
- [ ] User consent mechanism

## PII Redaction Pipeline

```text
Input Text
    ↓
PII Detection (NER)
    ↓
Classification (Type, Confidence)
    ↓
Redaction Decision
    ↓
Apply Redaction
    ↓
Log Redaction (Audit)
    ↓
Output Text
```

## Tips for Success

1. **Defense in depth**: Multiple security layers
2. **Assume breach**: Plan for failures
3. **Monitor continuously**: Watch for attacks
4. **Update regularly**: New threats emerge
5. **Test thoroughly**: Red team your systems

## Common Pitfalls

1. **Trusting user input:** Never trust, always validate
2. **Client-side only security:** Easily bypassed
3. **Ignoring logs:** Security events need investigation
4. **Over-blocking:** False positives hurt UX
5. **No incident response:** Plan before you need it

## Attack Indicators

| Indicator | Type | Severity |
|-----------|------|----------|
| "Ignore instructions" | Direct injection | High |
| "You are..." | Roleplay | Medium |
| Base64 strings | Encoding | Medium |
| Unusual patterns | Adversarial | Low-Medium |
| Repetitive attempts | Brute force | High |

## When to Apply Security

| Scenario | Security Level |
|----------|----------------|
| Internal tool | Standard |
| Customer-facing | High |
| Healthcare data | Very High |
| Financial data | Very High |
| Public API | Maximum |

## Compliance Requirements

| Regulation | Scope | Requirements |
|------------|-------|--------------|
| GDPR | EU | Data protection, right to erasure |
| HIPAA | US health | PHI protection, audit logs |
| CCPA | California | Privacy rights, opt-out |
| SOC 2 | Global | Security controls, audits |

---

**Phase 7 Complete!** 🎉

**Previous Module:** [7400: Agent Memory Systems](../7400-memory/README.md)

**Questions?** Review the [PREREQUISITES.md](./PREREQUISITES.md) or check Phase 7 documentation.

