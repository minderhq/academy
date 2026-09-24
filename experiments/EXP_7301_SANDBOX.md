# EXP_7301: Code Sandbox Experiment

**Project:** AI Engineering Curriculum
**Phase:** [7200] Tool Use
**Document ID:** 7202
**Experiment ID:** EXP_7301_SANDBOX
**Date:** 2026-02-04
**Status:** Completed

---

## Experiment Metadata

| Field | Value |
|-------|-------|
| **Title** | Sandboxed Code Execution for Agents |
| **Objective** | Test safe Python code execution in agent tools |
| **Hypothesis** | Sandbox enables safe code execution |
| **Category** | Security/Performance |
| **Priority** | Critical |
| **Estimated Duration** | 5 hours |

---

## Infrastructure Used

```text
Sandbox: RestrictedPython + Docker
Agent: Llama-2-7B with tool access
Test Cases: Safe, unsafe, malicious code
```

---

## Variables

| Variable | Values | Level |
|----------|--------|-------|
| Sandbox Type | RestrictedPython, Docker, None | Categorical |
| Timeout | 5s, 10s, 30s | Categorical |
| Memory Limit | 128MB, 256MB, 512MB | Categorical |

---

## Results

| Sandbox Type | Safety | Performance | Complexity |
|--------------|--------|-------------|------------|
| None | ❌ Unsafe | Fast | Low |
| RestrictedPython | ⚠️ Medium | Fast | Low |
| Docker | ✅ Safe | Medium | High |

### Security Tests

| Code Type | No Sandbox | RestrictedPython | Docker |
|------------|------------|------------------|--------|
| Safe | ✅ Pass | ✅ Pass | ✅ Pass |
| File Access | ❌ Blocked | ❌ Blocked | ✅ Blocked |
| Network | ❌ Blocked | ❌ Blocked | ✅ Blocked |
| Infinite Loop | ❌ Fail | ✅ Timeout | ✅ Timeout |
| Malicious | ❌ Fail | ⚠️ Partial | ✅ Blocked |

### Key Findings

1. ✅ Docker provides complete isolation
2. ⚠️ RestrictedPython has vulnerabilities
3. ✅ Timeout is essential for resource management
4. ✅ Memory limits prevent OOM attacks

---

## Recommendations

**For Production Agents:**
```python
# Use Docker-based sandbox
sandbox_config = {
    'timeout': 10,  # seconds
    'memory': '256m',
    'network': False,
    'readonly_fs': True
}
```

---

**Next Steps:** [7401: Agent Memory](./EXP_7401_AGENT_MEMORY.md) - Test memory systems
