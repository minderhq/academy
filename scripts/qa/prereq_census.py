#!/usr/bin/env python3
"""Prerequisites field census (PQ-01..PQ-03) for PROJECT-OMEGA.

Prerequisites is the curriculum's learning-path backbone: on the
platform a dangling prerequisite is a lesson that can never be
unlocked. Tick-409 measured the corpus: 108 docs carry the field,
the name is uniform (0 variants), and values fall into four
shapes - 95 free-text "See module README", 4 "See
PREREQUISITES.md", 3 bare token lists (`TUTORIAL-001`,
`TUTORIAL-005, LAB-009`), 3 titled brackets (`[1201] Proxmox
Hypervisor SOP`, `[1101] ..., [1102] ...`), and 3 prose
sentences.

PQ-01  machine-parseable token resolves to ZERO files (dangling).
PQ-02  machine-parseable token resolves to MULTIPLE files
       (ambiguous).
PQ-03  machine-parseable value not in canonical bracketed
       bare-token list form (`[1101, 1102]`, matching the Related
       field standard). HARD - drained tick-410: all 5 birth
       sites canonicalized (3 titled brackets stripped of titles,
       2 bare lists bracketed); free-text ("See module README",
       "See PREREQUISITES.md") and prose sentences remain allowed
       as authoring-stage pointers, a separate content pass.

PQ-06  the machine-parseable Prerequisites subgraph is ACYCLIC
       (Tarjan SCC: any cycle of 2+ docs, or a doc listing
       itself, is a finding). On the platform a prereq cycle is
       an unlock deadlock - neither side can ever be satisfied,
       so both lessons are permanently unreachable. Born
       tick-574 at zero: the live graph is 8 machine-parseable
       docs / 12 tokens / 12 edges, every edge forward in the
       lesson order, and the corpus already carries the legal
       diamond shape (1103 requiring both 1101 and 1102) that
       must NOT fire - shared dependencies are DAGs, not cycles.
       Edges come ONLY from the gate's own machine-parseable
       shapes (canonical bracketed, or the PQ-03-shaped pure
       token list): prose and the tolerated [PHASE-N] /
       phase-pointer brackets carry no graph edges, mirroring
       PQ-01..03 exactly - a cycle visible only through prose is
       an authoring-stage problem, not a fleet failure. The
       Related graph's one sibling cycle (module 1100-network:
       1101 -> 1102 -> 1103 -> 1101) is deliberate navigation -
       "see also your siblings" - not unlock semantics, so it is
       printed as census context and never gated. The PO
       boundary: prereq_ordering_scan's PO-01/PO-02 own the
       spine-local half (a 4-digit token numbered ahead of or
       equal to its own doc); PQ-06 is the numbering-free
       whole-graph half - it needs no monotonic-numbering
       assumption and covers the LAB-/TUTORIAL- edges PO's scope
       excludes (TUTORIAL-014 -> LAB-009 is a live such edge),
       so a cycle threaded through a lab or a multi-doc hop is
       visible here and nowhere else; a 4-digit self-listing
       honestly fires both gates - one defect, two hard locks.

HARD GATE - exit 1 on any finding. PQ-01/PQ-02 hard from birth
(KW-03 born-at-zero: 108 docs / 7 tokens, all resolving exactly
one file at tick-409); PQ-03 joined after the tick-410 shape
drain (census -> drain -> gate cycle); PQ-06 born-at-zero
tick-574.

Run over the whole corpus:
    python scripts/qa/prereq_census.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

FM_OPEN = re.compile(r"^---\s*$")
FM_CLOSE = re.compile(r"^(---|\.\.\.)\s*$")
PQ_FIELD = re.compile(r"^Prerequisites:(.*)$")
TOKEN = re.compile(r"\d{4}|\b(?:LAB|TUTORIAL)-\d{3}\b")
CANON = re.compile(r"^\[(?:\d{4}|(?:LAB|TUTORIAL)-\d{3})"
                   r"(?:, (?:\d{4}|(?:LAB|TUTORIAL)-\d{3}))*\]$")
FREE_TEXT = ("See module README", "See PREREQUISITES.md")


def pq_field(lines: list[str]) -> str | None:
    """Top-level Prerequisites value of one doc, or None."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = PQ_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def build_index(paths: list[Path], root: Path) -> dict[str, list[Path]]:
    """Token -> files, from filename prefixes (4-digit, LAB-NNN,
    TUTORIAL-NNN); other stems keyed by name."""
    index: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(paths):
        m = re.match(r"^(\d{4}|(?:LAB|TUTORIAL)-\d{3})-", p.name)
        if m:
            index[m.group(1)].append(p)
        else:
            index[p.stem].append(p)
    return {k: [x.relative_to(root) for x in v] for k, v in index.items()}


RELATED_FIELD = re.compile(r"^Related:(.*)$")
RELATED_FREE = ("See module README", "See References")


def related_field(lines: list[str]) -> str | None:
    """Top-level Related value of one doc, or None (mirrors
    related_census's parse - free-text shapes carry no edges)."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = RELATED_FIELD.match(raw)
                if m:
                    return m.group(1).strip()
            return None
    return None


def find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Non-trivial SCCs of the token graph: every cycle of 2+ docs,
    or a self-edge (a doc listing itself), as a sorted member list.
    Tarjan; corpus graphs are tens of nodes, recursion is fine."""
    index: dict[str, int] = {}
    low: dict[str, int] = {}
    onstack: set[str] = set()
    stack: list[str] = []
    out: list[list[str]] = []
    counter = 0

    def connect(v: str) -> None:
        nonlocal counter
        index[v] = low[v] = counter
        counter += 1
        stack.append(v)
        onstack.add(v)
        for w in sorted(graph.get(v, ())):
            if w not in index:
                connect(w)
                low[v] = min(low[v], low[w])
            elif w in onstack:
                low[v] = min(low[v], index[w])
        if low[v] == index[v]:
            scc: list[str] = []
            while True:
                w = stack.pop()
                onstack.discard(w)
                scc.append(w)
                if w == v:
                    break
            if len(scc) > 1 or scc[0] in graph.get(scc[0], ()):
                out.append(sorted(scc))

    for v in sorted(graph):
        if v not in index:
            connect(v)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    paths = sorted(docs.rglob("*.md"))
    index = build_index(paths, args.root)

    findings: list[str] = []
    shapes = Counter()
    n_docs = 0
    n_tokens = 0
    targets_n = Counter()
    graph: dict[str, set[str]] = {}
    rgraph: dict[str, set[str]] = {}
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        val = pq_field(lines)
        if val is None:
            continue
        rel = path.relative_to(args.root).as_posix()
        n_docs += 1
        toks: list[str] = []
        if any(val.startswith(t) for t in FREE_TEXT):
            shapes["free-text"] += 1
        elif CANON.match(val):
            shapes["canonical-bracketed"] += 1
            toks = TOKEN.findall(val)
        else:
            ctoks = TOKEN.findall(val)
            # prose sentences may carry stray digits; treat as
            # machine-parseable only if every comma item is a
            # pure token or token list
            items = [s.strip() for s in val.split(",")]
            if ctoks and all(TOKEN.fullmatch(s) for s in items):
                shapes["non-canonical"] += 1
                toks = ctoks
                findings.append(f"{rel}: PQ-03 non-canonical Prerequisites "
                                f"shape {val!r} (use bracketed bare-token "
                                f"list [tok, tok]; titles belong in the "
                                f"target doc)")
            else:
                shapes["prose"] += 1
        for tok in toks:
            n_tokens += 1
            targets = index.get(tok, [])
            targets_n[len(targets)] += 1
            if not targets:
                findings.append(f"{rel}: PQ-01 dangling Prerequisite "
                                f"{tok!r} (no file)")
            elif len(targets) > 1:
                names = ", ".join(str(t) for t in targets)
                findings.append(f"{rel}: PQ-02 ambiguous Prerequisite "
                                f"{tok!r} ({len(targets)} files: {names})")
            else:
                # PQ-06 edge: exactly-one resolution, doc -> doc
                graph.setdefault(rel, set()).add(targets[0].as_posix())

    # related graph: navigation context - reported, never gated
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rval = related_field(lines)
        if rval is None or any(rval.startswith(t) for t in RELATED_FREE):
            continue
        rrel = path.relative_to(args.root).as_posix()
        for tok in TOKEN.findall(rval):
            targets = index.get(tok, [])
            if len(targets) == 1:
                rgraph.setdefault(rrel, set()).add(targets[0].as_posix())

    cycles = find_cycles(graph)
    for scc in cycles:
        if len(scc) == 1:
            findings.append(f"{scc[0]}: PQ-06 Prerequisites self-cycle "
                            f"(a doc requires itself)")
        else:
            findings.append(f"{scc[0]}: PQ-06 Prerequisites cycle "
                            f"({len(scc)} docs): "
                            f"{' -> '.join(scc)} -> {scc[0]}")
    rel_cycles = find_cycles(rgraph)

    pq01 = sum(1 for f in findings if " PQ-01 " in f)
    pq02 = sum(1 for f in findings if " PQ-02 " in f)
    pq03 = sum(1 for f in findings if " PQ-03 " in f)
    pq06 = sum(1 for f in findings if " PQ-06 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"prereq_census: docs={n_docs} tokens={n_tokens} "
          f"shapes={dict(shapes)} resolve0={targets_n[0]} "
          f"resolve1={targets_n[1]} resolveN={targets_n[2]} "
          f"edges={sum(len(v) for v in graph.values())} "
          f"PQ-01={pq01} PQ-02={pq02} PQ-03={pq03} PQ-06={pq06} "
          f"related-cycles={len(rel_cycles)} "
          f"(hard gate; PQ-03 drained tick-410, PQ-06 born tick-574 "
          f"at zero; related cycles are navigation, not unlock - "
          f"reported, never gated)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
