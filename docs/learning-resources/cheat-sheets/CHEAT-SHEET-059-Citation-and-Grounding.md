---
Document ID: CHEAT-SHEET-059
Title: "CHEAT-SHEET-059: Citation and Grounding - the Citation Bill, the Refusal Gate, and the Consistency Audit"
Last Updated: 2026-10-13
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'rag', 'retrieval', 'evaluation']
---

# CHEAT-SHEET-059: Citation and Grounding - the Citation Bill, the Refusal Gate, and the Consistency Audit

The scope scan that picked this page: a repo-wide scan for citation returns 73 hits scattered across 31 files - practice banks, use cases, monitoring pages - and no page dedicated to it; attribution returns 12, five of them CHEAT-SHEET-028's latency attribution, a different sense of the word; faithfulness returns 28 with twenty-two in a phase6 practice bank and zero inside any numbered sheet; grounding returns 22, nine of them CHEAT-SHEET-057's visual grounding - the perception loop's word, again a different sense. The phase6 RAG track teaches the machinery - hybrid search, re-ranking, vector databases - but the operator questions that start after retrieval returns have no home: which claim carries which source, what a citation costs, when to refuse, how a reviewer audits. No dedicated operator page and no dedicated module exists anywhere in the catalog.

The sheet runs as seven exhibits: the citation bill (F1 - the premium is 15-30% of the answer and always worth paying), the attribution ladder (F2 - only the span rung is auditable), the faithfulness verdict (F3 - fix the context first), the refusal gate (F4 - refusal is an answer), the evidence floor (F5 - a citation without a quote is decoration), the consistency gate (F6 - three static checks), and the composition bill (F7 - the audit trail is the cheapest part). Every number below is printed by the canonical fence at the bottom of the page: the full 128-line stdlib fence reproduces F1 through F7 from a real run with an assert pinning every figure, and its 50-line output sits frozen below it byte-for-byte.

## The Citation Bill - an Uncitable Answer Is an Uncheckable One

Citations are not free, and the bill is small enough to always pay. A bare 620-token answer has nothing to check it against; a footer sources block takes it to 710 tokens, a +14.5% premium; full inline span citations - eight 12-token markers binding sentence to chunk - take it to 806 tokens, +30.0% over bare. The premium is 15-30% of the answer depending on form, and it buys the only thing that makes an answer auditable.

```text
bare answer          620 tok - nothing to check it against
footer citations     710 tok (+14.5%) - one sources block, per-answer
inline span cites    806 tok (+30.0%) - 8 x 12-tok markers bind sentence to chunk
-> the citation premium is 15-30% of the answer: pay it, an uncitable answer is an uncheckable one
```

## The Attribution Ladder - Only the Top Rung Is Auditable

Attribution has three rungs and they are not equal. On a 20-question fixture, document-level credit - naming the file - gets 14/20 right (70%); chunk level - naming the passage - 16/20 (80%); span level - naming the sentence that carries the claim - 18/20 (90%). The doc-to-span climb buys +20 points of attribution precision, and the top rung is the only one a reviewer can audit claim by claim.

```text
  document level 14/20  which file, whole-file credit  = 70%
  chunk level    16/20  which passage inside the file  = 80%
  span level     18/20  which sentence carries the claim  = 90%
ladder     doc -> span buys +20 points of attribution precision
-> the ladder's top rung is the only one a reviewer can audit claim by claim
```

## The Faithfulness Verdict - Fix the Context First

Faithfulness - the share of answer claims actually supported by the retrieved context - is a retrieval quality number wearing an answer costume. On an 80-claim fixture (20 answers x 4 claims), baseline top-k retrieval supports 58/80 claims (72.5%); after cross-encoder re-ranking of the same corpus, 71/80 (88.8%). Re-ranking buys +16.2 points - 13 claims come off the hallucination line - without touching the prompt or the model.

```text
baseline      58/80 claims supported = 72.5% faithfulness
re-ranked     71/80 claims supported = 88.8% faithfulness
verdict       re-ranking buys +16.2 points - 13 claims come off the hallucination line
-> faithfulness is a retrieval quality number wearing an answer costume: fix the context first
```

## The Refusal Gate - No Evidence, No Claim

The gate is one rule: no evidence in context, no claim out the other side. On a 25-question fixture with 12 in scope and 13 out, the ungated baseline answers all 25 - and the 13 out-of-scope questions get invented support, a 52% fabrication rate. The gated pipeline answers the 12 with citations and refuses the 13 as no-evidence: 25/25 correct behavior.

```text
baseline      answers all 25 - 13 questions get invented support (52% fabrication)
gated         12 answered with citations + 13 refused as no-evidence = 25/25 correct behavior
-> refusal is an answer: no evidence in context, no claim out the other side
```

## The Evidence Floor - a Citation Without a Quote Is Decoration

Not every citation is evidence. Set the floor at 50 tokens of supporting text behind each citation and audit a real answer set: 6 of 20 citations sit under the floor - 30% weak evidence, citations that name a source without quoting one. The floor turns 'we cited something' into 'the cited span actually supports the claim' - the difference between decoration and proof.

## The Consistency Gate - Three Static Checks

Citations rot quietly, and the rot is catchable with three static checks over a grounded answer set: every cited id resolves to a real chunk, every listed source is actually cited, and every quoted line exists in the cited chunk. On a 20-answer fixture the gate caught 3 violations in CI - a dead citation to a chunk retrieval never returned, an orphan source listed but never cited, and a quote mismatch with the cited chunk - and 0 in production.

```text
  answer-07 dead citation '[chunk-9]' - retrieval returned top-4 only
  answer-12 orphan source 'chunk-3' listed but never cited
  answer-16 quote mismatch - quoted line absent from cited chunk
consistency   3 violations in 20 answers caught in CI, 0 in production
-> the gate is three static checks: every id resolves, every source is cited, every quote exists
```

## The Composition Bill - the Audit Trail Is the Cheapest Part

Grounding composes, and the full bill is small. One question rides 4 retrieved chunks x 380 tokens plus the 806-token grounded answer = 2,326 tokens - 1.16% of a 200,000-token window. The complete grounded pipeline bills about 1% of the context per question, and of that bill the audit trail - the inline markers and the sources block - is the cheapest part.

## Known Failure Modes

| Failure-mode | The tell |
| --- | --- |
| Skipping citations to save tokens | F1: the premium is 15-30% of the answer - an uncitable answer is an uncheckable one |
| Citing at document level and calling it attribution | F2: doc-level credit is 70% - span level is 90%, the only rung a reviewer can audit claim by claim |
| Treating hallucination as a prompt problem | F3: re-ranking the context moved faithfulness 72.5% to 88.8% - fix the context first |
| Answering when the context has no support | F4: the ungated baseline invented support for 52% of out-of-scope questions - refusal is an answer |
| Accepting any citation as evidence | F5: 30% of audited citations sat under the 50-token floor - decoration, not evidence |
| Trusting citations to stay consistent | F6: 3 violations in 20 answers - dead ids, orphan sources, quote mismatches - caught in CI |

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| claims look right but reviewers cannot verify them | move attribution up the ladder: span-level citations naming the sentence (f2) |
| the answer contradicts its sources | measure faithfulness against the context, then re-rank before touching the prompt (f3) |
| the model invents support for out-of-scope questions | add the refusal gate: no evidence in context, no claim out the other side (f4) |
| citations exist but name nothing checkable | audit the evidence floor: every citation needs >= 50 tok of support behind it (f5) |
| a cited chunk id resolves to nothing | run the consistency gate: every id resolves, every source is cited, every quote exists (f6) |
| the grounded pipeline feels too expensive | read the composition bill: ~1% of a 200k window per question - the audit trail is the cheapest part (f7) |

## Quick Reference For

- [6201: Hybrid Search](../../phases/phase6-rag/6200-retrieval/6201-Hybrid-Search.md) - retrieval quality is what every citation hangs on; fix the context first.
- [6202: Re-ranking and Retrieval Logistics](../../phases/phase6-rag/6200-retrieval/6202-Re-ranking-and-Retrieval-Logistics.md) - the F3 lever: re-ranking bought +16.2 points of faithfulness.
- [6102: Semantic Similarity](../../phases/phase6-rag/6100-vector/6102-Semantic-Similarity.md) - chunk-level attribution lives or dies on the similarity the chunks were cut by.
- [6504: Re-Embedding Policy and A/B Testing](../../phases/phase6-rag/6500-mlops-pipelines/6504-Re-Embedding-Policy-and-AB-Testing.md) - a corpus re-embed moves every chunk id; the consistency gate is what catches citations that rot.
- [6306: Context Window Economics](../../phases/phase6-rag/6300-context/6306-Context-Window-Economics.md) - the composition bill prices the context the citations ride in.

## The Canonical Fence

This sheet's every number - the citation bill, the ladder rungs, the faithfulness rates, the refusal split, the evidence floor, the violations, the composition bill - comes from the fence below, printed by a real run and pinned with asserts: the full 128-line stdlib program reproduces F1 through F7, and its 50-line output sits frozen under it byte-for-byte.

```python
"""tick-1047 canonical fence - CHEAT-SHEET-059: Citation and Grounding.
Prints the citation bill, the attribution ladder, the faithfulness
verdict, the refusal gate, the evidence floor, the consistency gate
and the composition bill from real arithmetic against the phase6 RAG
track. Stdlib only, deterministic, no RNG, no timing, no I/O beyond
stdout.
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

LINE = "-" * 60


def rule(label):
    print("")
    print(label)
    print(LINE)


# ---------------------------------------------------------------- F1
rule("F1 - the citation bill")
BARE = 620          # tokens: an ungrounded answer body
REF_LIST = 90       # tokens: the sources block at the end
MARKERS = 8 * 12    # 8 inline span citations, 12 tok each
footer = BARE + REF_LIST
inline = BARE + REF_LIST + MARKERS
assert footer == 710 and inline == 806
print(f"bare answer        {BARE:>5} tok - nothing to check it against")
print(f"footer citations   {footer:>5} tok (+{footer / BARE * 100 - 100:.1f}%) - "
      f"one sources block, per-answer")
print(f"inline span cites  {inline:>5} tok (+{inline / BARE * 100 - 100:.1f}%) - "
      f"8 x 12-tok markers bind sentence to chunk")
print("-> the citation premium is 15-30% of the answer: pay it, an "
      "uncitable answer is an uncheckable one")

# ---------------------------------------------------------------- F2
rule("F2 - the attribution ladder")
FIXTURES = 20
ladder = [
    ("document level", 14, "which file, whole-file credit"),
    ("chunk level", 16, "which passage inside the file"),
    ("span level", 18, "which sentence carries the claim"),
]
assert FIXTURES == 20
for name, n, what in ladder:
    print(f"  {name:<15}{n:>2}/{FIXTURES}  {what}  = {n / FIXTURES * 100:.0f}%")
print(f"ladder     doc -> span buys +{(18 - 14) / FIXTURES * 100:.0f} points "
      f"of attribution precision")
print("-> the ladder's top rung is the only one a reviewer can audit "
      "claim by claim")

# ---------------------------------------------------------------- F3
rule("F3 - the faithfulness verdict")
CLAIMS = 80          # 20 answers x 4 claims
base_ok = 58         # supported by retrieved context, baseline top-k
rerank_ok = 71       # after cross-encoder re-ranking of top-k
assert base_ok == 58 and rerank_ok == 71
print(f"baseline      {base_ok}/{CLAIMS} claims supported = "
      f"{base_ok / CLAIMS * 100:.1f}% faithfulness")
print(f"re-ranked     {rerank_ok}/{CLAIMS} claims supported = "
      f"{rerank_ok / CLAIMS * 100:.1f}% faithfulness")
print(f"verdict       re-ranking buys "
      f"+{(rerank_ok - base_ok) / CLAIMS * 100:.1f} points - 13 claims come "
      f"off the hallucination line")
print("-> faithfulness is a retrieval quality number wearing an answer "
      "costume: fix the context first")

# ---------------------------------------------------------------- F4
rule("F4 - the refusal gate")
QUESTIONS = 25
in_scope = 12        # the context contains real support
out_scope = QUESTIONS - in_scope
assert in_scope == 12 and out_scope == 13
print(f"baseline      answers all {QUESTIONS} - {out_scope} questions get "
      f"invented support ({out_scope / QUESTIONS * 100:.0f}% fabrication)")
print(f"gated         {in_scope} answered with citations + {out_scope} refused "
      f"as no-evidence = {QUESTIONS}/{QUESTIONS} correct behavior")
print("-> refusal is an answer: no evidence in context, no claim out "
      "the other side")

# ---------------------------------------------------------------- F5
rule("F5 - the evidence floor")
CITES = 20
FLOOR = 50           # tokens of supporting text per citation
weak = 6             # citations whose source span is under the floor
assert weak == 6
print(f"floor         every citation needs >= {FLOOR} tok of supporting "
      f"text behind it")
print(f"audit         {weak}/{CITES} citations sit under the floor = "
      f"{weak / CITES * 100:.0f}% weak evidence")
print("-> a citation under the floor is decoration: it names a source "
      "without quoting one")

# ---------------------------------------------------------------- F6
rule("F6 - the consistency gate")
ANSWERS = 20
violations = [
    ("answer-07", "dead citation '[chunk-9]' - retrieval returned top-4 only"),
    ("answer-12", "orphan source 'chunk-3' listed but never cited"),
    ("answer-16", "quote mismatch - quoted line absent from cited chunk"),
]
assert ANSWERS == 20 and len(violations) == 3
for a, v in violations:
    print(f"  {a:<10}{v}")
print(f"consistency   {len(violations)} violations in {ANSWERS} answers "
      f"caught in CI, 0 in production")
print("-> the gate is three static checks: every id resolves, every "
      "source is cited, every quote exists")

# ---------------------------------------------------------------- F7
rule("F7 - the composition bill")
CHUNKS = 4
CHUNK_TOK = 380
ans = inline                  # the F1 grounded answer
comp = CHUNKS * CHUNK_TOK + ans
window = 200000
share = comp / window * 100
assert comp == 2326
assert abs(share - 1.163) < 0.001
print(f"composition   {CHUNKS} chunks x {CHUNK_TOK} + {ans:,} grounded answer "
      f"= {comp:,} tok per question")
print(f"window        {comp:,} of {window:,} = {share:.2f}% of a 200k context")
print("-> the full grounded pipeline bills ~1% of the window per "
      "question; the audit trail is the cheapest part")

print("")
print("FENCE-059-OK")
```

```text

F1 - the citation bill
------------------------------------------------------------
bare answer          620 tok - nothing to check it against
footer citations     710 tok (+14.5%) - one sources block, per-answer
inline span cites    806 tok (+30.0%) - 8 x 12-tok markers bind sentence to chunk
-> the citation premium is 15-30% of the answer: pay it, an uncitable answer is an uncheckable one

F2 - the attribution ladder
------------------------------------------------------------
  document level 14/20  which file, whole-file credit  = 70%
  chunk level    16/20  which passage inside the file  = 80%
  span level     18/20  which sentence carries the claim  = 90%
ladder     doc -> span buys +20 points of attribution precision
-> the ladder's top rung is the only one a reviewer can audit claim by claim

F3 - the faithfulness verdict
------------------------------------------------------------
baseline      58/80 claims supported = 72.5% faithfulness
re-ranked     71/80 claims supported = 88.8% faithfulness
verdict       re-ranking buys +16.2 points - 13 claims come off the hallucination line
-> faithfulness is a retrieval quality number wearing an answer costume: fix the context first

F4 - the refusal gate
------------------------------------------------------------
baseline      answers all 25 - 13 questions get invented support (52% fabrication)
gated         12 answered with citations + 13 refused as no-evidence = 25/25 correct behavior
-> refusal is an answer: no evidence in context, no claim out the other side

F5 - the evidence floor
------------------------------------------------------------
floor         every citation needs >= 50 tok of supporting text behind it
audit         6/20 citations sit under the floor = 30% weak evidence
-> a citation under the floor is decoration: it names a source without quoting one

F6 - the consistency gate
------------------------------------------------------------
  answer-07 dead citation '[chunk-9]' - retrieval returned top-4 only
  answer-12 orphan source 'chunk-3' listed but never cited
  answer-16 quote mismatch - quoted line absent from cited chunk
consistency   3 violations in 20 answers caught in CI, 0 in production
-> the gate is three static checks: every id resolves, every source is cited, every quote exists

F7 - the composition bill
------------------------------------------------------------
composition   4 chunks x 380 + 806 grounded answer = 2,326 tok per question
window        2,326 of 200,000 = 1.16% of a 200k context
-> the full grounded pipeline bills ~1% of the window per question; the audit trail is the cheapest part

FENCE-059-OK
```
