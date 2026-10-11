---
Document ID: CHEAT-SHEET-013
Title: "CHEAT-SHEET-013: Structured Output & Function Calling"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'function-calling', 'constrained-decoding', 'inference']
---

# CHEAT-SHEET-013: Structured Output & Function Calling

## Quick Reference for Schema-Constrained Generation

**Version:** 1.0

A prompt that asks for JSON is a wish; a grammar over the logits is a
guarantee. This sheet maps the constraint mechanism, the knob each
serving stack exposes, and the trap that burns most teams: reading a
100%-valid parse rate as a quality metric.

---

## The Grammar-to-Mask Mechanism

Outlines' reformulation (Willard and Louf, arXiv 2307.09702): any
generation step under a grammar is choosing the next token from the
subset the grammar's state admits — so constrain by zeroing the logits
of every token outside that subset. No architecture change, no
fine-tune, model-agnostic. XGrammar (Dong et al., arXiv 2411.15100,
MLSys 2025) made it production-fast by partitioning the vocabulary into
admissibility that is context-independent (precomputed once per
grammar) and context-dependent (checked against a persistent stack),
with near-zero per-token overhead.

```python
LOGITS = {"the": 4.2, "fn:": 3.0, "search": 2.8, "maybe": 1.9}

def masked_argmax(logits, allowed):
    # Grammar-to-mask, one step: every token the grammar's
    # current state does not admit is zeroed before the argmax.
    masked = {t: v for t, v in logits.items() if t in allowed}
    return max(masked, key=masked.get)

print("raw argmax    :", max(LOGITS, key=LOGITS.get))
print("masked argmax :", masked_argmax(LOGITS, {"fn:", "search"}))
```

---

## Prompting Is Not Constraining

Module 7106's measured shape: prompt-only compliance scores ~0.79 valid
and feels deployable until the tool list changes — the prompt's
enumeration is a snapshot that rots, while the mask recompiles from the
grammar. Base-model ungrounded tool choice is what Gorilla measured
(Gorilla's hallucination rates 36.55/37.16/78.65 percent across three
hubs). Rule: a prompt may shape semantics; only the mask owns syntax.

---

## Stack-by-Stack Knobs

| Stack | Knob | Notes |
| --- | --- | --- |
| vLLM | `guided_json` / guided-grammar in `extra_body` | XGrammar-backed; see CHEAT-SHEET-007 |
| OpenAI-compatible API | `response_format: json_schema` | strict mode; schema travels with the request |
| SGLang | `json_schema` parameter | same schema object, different server flag |
| Ollama | `format` parameter | accepts a JSON schema or `json` shorthand |
| llama.cpp | `--grammar` (GBNF file) | grammar constrains at the sampler level |

---

## Syntax Guarantees, Semantics Trains

The 2x2 behind module 7106's ledger: masking an untrained model yields
1.0000 valid and 0.3033 correct — exactly chance. Every call parses; a
third are right. Constrained decoding is a syntax guarantee, and
reading its valid rate as quality is the surface's core trap. When
parse-validity is the floor, train the binding: the Gorilla/APIBench
recipe prices it once — roughly 11,000 pairs at 300 tokens for 3
epochs — and the ledger's argument is the shape (one-time correctness
bill vs per-request syntax insurance), not a token-for-token
break-even. Watch pair contamination: wrong-key pairs at rare query
words zero the evidence for the legal continuation, and the mask keeps
the malformed binding parseable all the way into production.

---

## Troubleshooting

| Symptom | Root cause | Fix |
| --- | --- | --- |
| 100% valid calls, a third wrong | masked untrained model; valid rate misread as quality | train the binding (pairs), validate with the extractor, not the parser |
| Compliance drops after a tool-list change | prompt enumeration went stale | recompile the mask from the grammar |
| Cross-paper numbers incomparable | served at different temperatures | quote the serving protocol next to every tool-accuracy number |
| JSON mode emits markdown fences | chat template framing, not the sampler | verify the template + request `response_format`, not just the prompt |
| Rare tool args always misbound | contaminated training pairs at rare query words | audit pairs; the mask cannot fix a wrong key binding |

---

**Quick Reference for:**

- [Module 7106: Function-Calling Training and Constrained Decoding](../../phases/phase7-agentic/7100-architecture/7106-Function-Calling-Training-and-Constrained-Decoding.md)
- [Module 7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
- [Module 1405: SGLang](../../phases/phase1-infra/1400-llmops/1405-SGLang.md)
- [CHEAT-SHEET-007: vLLM Serving & Inference](./CHEAT-SHEET-007-vLLM-Serving.md)
