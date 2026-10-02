#!/usr/bin/env python3
"""Prerequisites field census (PQ-01..03 + PQ-06..08) for
PROJECT-OMEGA.

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

PQ-07  difficulty never climbs the unlock path: on every PQ-06
       edge where both endpoints carry a canonical FM Difficulty,
       the prerequisite's tier must be <= the doc's own tier
       (Beginner=1 / Intermediate=2 / Advanced=3, the TIER_STARS
       map footer_fm_parity proved). Equal-tier and downhill
       edges are legal pedagogy - a lesson may require its own
       tier and must ease you in; an uphill edge is a lesson
       demanding harder material than itself, the wrong opening
       order on the platform. An out-of-vocabulary Difficulty on
       either endpoint skips the comparison (FV-07 owns the
       enum; PQ-07 never double-reports another gate's finding).
       Born tick-575 at zero: 12 edges compared, 6 equal-tier
       (1102->1101, 1103->1101/1102, 1202->1201,
       TUTORIAL-001->TUTORIAL-000, TUTORIAL-014->TUTORIAL-005
       and ->LAB-009), 6 downhill (TUTORIAL-003->TUTORIAL-000/
       001, TUTORIAL-007->TUTORIAL-001, TUTORIAL-009->
       TUTORIAL-003, TUTORIAL-014->TUTORIAL-007), 0 inversions,
       0 prereq docs lacking FM Difficulty.

PQ-08  the pointer contract: a doc whose Prerequisites defers
       "See module README" requires that module README to carry
       a canonical machine-parseable Prerequisites field - the
       indirection exists so the README is the module's single
       source of prereq truth, and 177 docs (111 lessons + 66
       assessments) resolved it to nothing machine-parseable
       until tick-607: 33/33 module READMEs carried no
       Prerequisites field at all. The drain transcribed each
       module's own PREREQUISITES.md cross-module declarations
       into the README FM (module-granularity normalization: a
       Review/Read bullet naming another module's lesson
       normalizes to that lesson's module), 9 modules with
       dependencies / 10 edges - 2200->[2100], 2300->[2200],
       2400->[2200], 3100->[3200] (the one forward edge: advanced
       attention reviews the embeddings module's RoPE lesson),
       4100->[1500], 4300->[4100], 4400->[4100, 4300],
       5100->[4100], 5400->[5300] - every remaining module `[]`,
       5500's "see 5400 if scaling is your bottleneck" left out
       honestly (conditional advice, not a prerequisite). PQ-08
       fires per offending README, aggregating the count of
       pointer docs that defer to it; a "See module README" doc
       with no resolvable module dir fires its own finding. The
       token index now resolves a bare 4-digit module token to
       its module README (0 filename collisions across the 33
       codes, measured before the extension). Born tick-607 at
       zero.

HARD GATE - exit 1 on any finding. PQ-01/PQ-02 hard from birth
(KW-03 born-at-zero: 108 docs / 7 tokens, all resolving exactly
one file at tick-409); PQ-03 joined after the tick-410 shape
drain (census -> drain -> gate cycle); PQ-06 born-at-zero
tick-574; PQ-07 born-at-zero tick-575; PQ-08 born-at-zero
tick-607 after the 33-README FM drain it defends.

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
CANON = re.compile(r"^(\[\]|"
                   r"\[(?:\d{4}|(?:LAB|TUTORIAL)-\d{3})"
                   r"(?:, (?:\d{4}|(?:LAB|TUTORIAL)-\d{3}))*\])$")
FREE_TEXT = ("See module README", "See PREREQUISITES.md")
MODULE_DIR = re.compile(r"^(\d{4})-")
DIFF_FIELD = re.compile(r"^Difficulty:(.*)$")
TIERS = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
TIER_NAME = {v: k for k, v in TIERS.items()}


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


def module_readme(path: Path, docs: Path) -> Path | None:
    """The README.md of the 4-digit module dir this doc belongs to
    (direct parent, or grandparent for an assessment/ subdir), or
    None when no module dir resolves above it."""
    for cand in (path.parent, path.parent.parent):
        if (MODULE_DIR.match(cand.name)
                and cand.parent.parent == docs / "phases"):
            rm = cand / "README.md"
            if rm.exists():
                return rm
    return None


def difficulty_tier(lines: list[str]) -> int | None:
    """Top-level Difficulty tier index of one doc, or None (mirror
    of pq_field; an out-of-vocabulary value yields None so FV-07
    stays the sole owner of the enum)."""
    if not lines or not FM_OPEN.match(lines[0]):
        return None
    for i in range(1, min(len(lines), 40)):
        if FM_CLOSE.match(lines[i]):
            for raw in lines[1:i]:
                m = DIFF_FIELD.match(raw)
                if m:
                    return TIERS.get(m.group(1).strip())
            return None
    return None


def build_index(paths: list[Path], root: Path) -> dict[str, list[Path]]:
    """Token -> files, from filename prefixes (4-digit, LAB-NNN,
    TUTORIAL-NNN); a module README (stem README.md under a 4-digit
    module dir) resolves its module's own 4-digit token - the
    module-level Prerequisites pointer target (tick-607); other
    stems keyed by name."""
    index: dict[str, list[Path]] = defaultdict(list)
    for p in sorted(paths):
        m = re.match(r"^(\d{4}|(?:LAB|TUTORIAL)-\d{3})-", p.name)
        if m:
            index[m.group(1)].append(p)
        else:
            pm = (re.match(r"^(\d{4})-", p.parent.name)
                  if p.name == "README.md" else None)
            if pm:
                index[pm.group(1)].append(p)
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
    tiers: dict[str, int] = {}
    # PQ-08 accumulation: docs deferring "See module README" per
    # module README, and the READMEs whose field breaks the
    # contract (missing, unreadable, or non-canonical)
    pointer_n: Counter = Counter()
    bad_readmes: set[str] = set()
    rm_cache: dict[Path, str | None] = {}
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8",
                                   errors="replace").split("\n")
        except (UnicodeDecodeError, OSError):
            continue
        rel = path.relative_to(args.root).as_posix()
        tier = difficulty_tier(lines)
        if tier is not None:
            tiers[rel] = tier
        val = pq_field(lines)
        if val is None:
            continue
        n_docs += 1
        toks: list[str] = []
        if any(val.startswith(t) for t in FREE_TEXT):
            shapes["free-text"] += 1
            if val.startswith("See module README"):
                # PQ-08: the pointer contract - deferring to the
                # module README only works if that README carries
                # the canonical machine-parseable field to resolve
                rm = module_readme(path, docs)
                if rm is None:
                    findings.append(
                        f"{rel}: PQ-08 pointer contract broken "
                        f"(defers 'See module README' but no 4-digit "
                        f"module dir resolves above it)")
                else:
                    rm_rel = rm.relative_to(args.root).as_posix()
                    pointer_n[rm_rel] += 1
                    if rm not in rm_cache:
                        try:
                            rm_cache[rm] = pq_field(
                                rm.read_text(encoding="utf-8",
                                             errors="replace")
                                .split("\n"))
                        except OSError:
                            rm_cache[rm] = None
                    rv = rm_cache[rm]
                    if rv is None or not CANON.match(rv):
                        bad_readmes.add(rm_rel)
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

    # PQ-08 emission: one finding per offending module README,
    # aggregating the pointer docs that defer to it
    for rm_rel in sorted(bad_readmes):
        findings.append(
            f"{rm_rel}: PQ-08 pointer contract broken "
            f"({pointer_n[rm_rel]} docs defer 'See module README' "
            f"here; the README carries no canonical machine-parseable "
            f"Prerequisites field)")

    # PQ-07: difficulty must not climb the unlock path - on every
    # PQ-06 edge, the prerequisite's tier must be <= the doc's own
    # tier (equal-tier and downhill legal; uphill = wrong order).
    tier_edges = 0
    for rel in sorted(graph):
        own = tiers.get(rel)
        if own is None:
            continue
        for tgt in sorted(graph[rel]):
            tt = tiers.get(tgt)
            if tt is None:
                continue  # out-of-vocabulary tier is FV-07's finding
            tier_edges += 1
            if tt > own:
                findings.append(
                    f"{rel}: PQ-07 Prerequisite difficulty inversion "
                    f"(this {TIER_NAME[own]} doc requires {tgt} at "
                    f"{TIER_NAME[tt]}; a lesson must not demand harder "
                    f"material than itself)")

    pq01 = sum(1 for f in findings if " PQ-01 " in f)
    pq02 = sum(1 for f in findings if " PQ-02 " in f)
    pq03 = sum(1 for f in findings if " PQ-03 " in f)
    pq06 = sum(1 for f in findings if " PQ-06 " in f)
    pq07 = sum(1 for f in findings if " PQ-07 " in f)
    pq08 = sum(1 for f in findings if " PQ-08 " in f)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"prereq_census: docs={n_docs} tokens={n_tokens} "
          f"shapes={dict(shapes)} resolve0={targets_n[0]} "
          f"resolve1={targets_n[1]} resolveN={targets_n[2]} "
          f"edges={sum(len(v) for v in graph.values())} "
          f"PQ-01={pq01} PQ-02={pq02} PQ-03={pq03} PQ-06={pq06} "
          f"PQ-07={pq07} PQ-08={pq08} tier-edges={tier_edges} "
          f"related-cycles={len(rel_cycles)} "
          f"(hard gate; PQ-03 drained tick-410, PQ-06 born tick-574 "
          f"at zero, PQ-07 born tick-575 at zero, PQ-08 born "
          f"tick-607 at zero; related cycles are navigation, not "
          f"unlock - reported, never gated)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
