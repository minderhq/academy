#!/usr/bin/env python3
"""Front-matter VALUE contracts (FV-01..13, HARD) - the platform
ingestion simulation.

FS-01/02 gate the six standard field NAMES; the dup gates check
specific values in isolation. This gate verifies the VALUE
CONTRACTS the eventual platform will rely on when it ingests
front matter as machine metadata - by doing exactly what the
platform will do: yaml.safe_load the block, then type-check the
fields that drive filters, sort orders and reading-time displays.

FV-01  Last Updated is a real calendar date in YYYY-MM-DD form -
       the ISO-8601 contract; a display layer parses it with a
       date parser, and locale-flavored or prose dates
       ("Sept 30th, 2026") crash it
FV-02  Estimated Time is machine-comparable: either the
       single-regime form "N hours|minutes" (fractional N legal,
       singular with 1) or the canonical two-regime form
       "30 minutes (quick review) - N hours (full review)" used
       by PREREQUISITES docs - the reading-time pipeline does
       arithmetic on this field, prose variants are invisible
FV-03  Tags parses to a list of strings - the platform's tag
       filter builds UI checkboxes from this list; a bare string
       or a string-with-commas silently degrades into one giant
       filter token
FV-04  the whole front-matter block yaml.safe_loads to a dict -
       this IS the ingestion call; one unparseable value and the
       platform drops the doc's metadata entirely
FV-05  an integer inside a Related list must be the Document ID
       of an existing doc - the platform renders Related as
       next-lesson cards; a dangling id is a broken card at
       runtime (two-pass: collect all Document IDs first, then
       verify - cross-file reference)
FV-06  Related, when present, is a prose pointer (str) or a list
       of ids/names - never a number, bool or mapping; the triage
       census (tick-494) found exactly these forms corpus-wide:
       178 canonical "See module README", 11 lists, 4 prose
       variants, 215 absent
FV-07  Difficulty is one of the three canonical tiers
       Beginner/Intermediate/Advanced - the platform's difficulty
       filter and sort are closed enums; a fourth value is an
       invisible filter hole (census tick-495: 71/117/220, zero
       strays)
FV-08  Title is a non-empty string - it becomes the platform
       card title; an empty or non-string Title renders as
       nothing (census tick-495: 0 bad of 408)
FV-09  Last Updated is not in the future - a date the doc cannot
       have been updated on yet poisons "recently updated" sorts
       (census tick-495: 0 of 408)
FV-10  a string Document ID is a URL-safe key: uppercase-initial
       or module-numbered, hyphen-separated alphanumerics, no
       whitespace or other punctuation - the platform uses it as
       canonical key AND URL slug; anything else needs escaping
       (census tick-496: 293/293 clean; the corpus mixes pure
       namespace tokens like LAB-003 with descriptive forms like
       TEMPLATE-001-Simple-LLM-App - both legal, both 1100-
       PRACTICE-style module numbering)
FV-11  a Related string element in the LAB-<n> or TUTORIAL-<n>
       namespace resolves to an existing file whose name starts
       with that id - same broken-card bug as FV-05, string
       edition; the two namespaces resolve against the
       learning-resources labs/ and tutorials/ file sets
       (collected in pass 1), other namespaces stay free-form
       (census tick-497: 3 refs corpus-wide, all resolve)
FV-12  under experiments/, the keyset fields Title, Status and
       Difficulty are present - frontmatter_lint's FM-03 walks
       docs/ only and EC-01 binds the Document ID alone, so the
       other keyset fields' absence was invisible on the second
       tree; Last Updated absence needs no clause here because
       FV-01 already fires on it, which is why the list is
       exactly three fields (census tick-612: 48/48 carry all
       five keyset fields)
FV-13  under experiments/, Status is the FM-04 enum {Complete} -
       the platform's completion filter is the same closed
       vocabulary docs/ answers to; any other value is an
       invisible filter hole, and the field was vouched nowhere
       on the second tree before this clause (census tick-612:
       48/48 Complete, TEMPLATE included - no name-keyed
       exemption, the EC-02 lesson)

Scope: all docs/**/*.md, FM block = first ---...--- (within 40
lines, FS-01's contract). Related string elements are not
resolved against Document IDs by FV-05 - the LAB-/TUTORIAL-
namespaces are FV-11's, resolved against the learning-resources
file sets; every other string form stays free-form by design.

Census at birth (tick-493): 408/408 yaml-parseable, 408/408
ISO dates, Tags clean; one real drain ("1 hours" -> "1 hour" in
phase1 1100 PRACTICE.md) and the two-regime PREREQUISITES form
canonized as FV-02's second arm. FV-05/06 born tick-494
born-at-zero: 32 Related integer refs, 0 dangling. FV-07..09
born tick-495 born-at-zero: Difficulty 71/117/220 canonical,
Title 0 bad, future-dated Last Updated 0. Document ID mixed
typing (115 int + 293 namespace-string) censused as corpus
convention, deliberately ungated. Negative tests also caught
PyYAML raising ValueError OUT of safe_load on an impossible
bare date ("2026-13-45" - the timestamp constructor builds
dt.date without wrapping), which the platform experiences as an
ingestion crash; FV-04 therefore catches ValueError/TypeError
alongside YAMLError. FV-11 born tick-497 born-at-zero: the 3
LAB-/TUTORIAL- Related refs all resolve. A broader
scaffold-marker census the same tick re-derived the existing
UM-01 axis (born tick-276, baseline 0) - the QA-TOOLING
register is the authoritative axis inventory; read it BEFORE
censusing a new axis. Tick-498: the lesson fired again -
FV-11's own axis overlaps RL-01 (related_census, tick-405);
both kept deliberately (different universes: corpus-wide
filename prefixes vs canonical resource dirs; RL-02 ambiguity
detection is RL's alone). Heading-case was the other tick-496
candidate and is formally SKIPPED with measurement: of 8795
H2/H3 headings, 5617 are sentence case, 3158 are sentence case
with Title-Case topic phrases (Docker Fundamentals, GPU
Passthrough), 20 all-caps - a mechanical rule would need a
curated proper-noun/phrase allowlist; recorded as the axis
tombstone. FV-10 born tick-496 born-at-zero: 293/293 str keys
clean.

Scope (tick-611): the corpus is two trees - docs/ (408 FM docs)
and experiments/ (48 FM files, the 5-field keyset EC-01 locked).
The ingestion simulation walks BOTH: FV-01/04/07/08/09 apply to
experiments/ unchanged (ISO dates, yaml parse, Difficulty tiers,
Title string, no future dates); two contract reconciliations were
required and are documented here - FV-03's Tags presence duty
follows the keyset (docs/ requires Tags by convention, the
experiments/ keyset carries no Tags, so absence there is by
design and a malformed Tags would still fire), and FV-10's key
grammar accepts the EC-01-canonical EXP_NNNN form (underscore is
RFC-3986 unreserved - a URL path needs no escaping for it; the
naive extension fired 47 FV-10s before the grammar learned the
shape). Born-clean on both trees: 48/48 ISO, 48/48 canonical
tiers, 48/48 yaml-parses.

Scope (tick-612): the second tree's Status column and keyset
presence joined the simulation - frontmatter_lint (FM-03
required keys, FM-04 the Status enum) walks docs/ only, so an
experiments/ file with a missing Title/Status/Difficulty or a
non-canonical Status answered to no gate at all. FV-12/FV-13
are scoped to experiments/ so docs/ stays FM-03/FM-04's alone
(no double-report); absence of Last Updated stays FV-01's (it
already fires there). Born-clean at 48/48 five-field keysets,
48/48 Status Complete.

Note: this gate is the fleet's only third-party import (PyYAML) -
deliberate, because the rule under test is "yaml.safe_load
succeeds", and a re-implementation would test something else.

Run over the whole corpus:
    python scripts/qa/frontmatter_value_scan.py --root .

Output is ASCII-escaped so it is safe on cp1254 consoles.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

TIME_SINGLE = re.compile(r"^\d+(\.\d+)? (hour|minute)s?$")
TIME_DOUBLE = re.compile(r"^30 minutes \(quick review\) - \d+(\.\d+)? hours \(full review\)$")
ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
CANON_DIFFICULTY = ("Beginner", "Intermediate", "Advanced")
STATUS_ENUM = ("Complete",)
DOC_KEY = re.compile(r"^(?:[A-Z0-9][A-Za-z0-9]*(-[A-Za-z0-9]+)*|EXP_\d{4})$")
RES_ID = re.compile(r"^(LAB|TUTORIAL)-\d+")    # filename prefix
RES_REF = re.compile(r"^(LAB|TUTORIAL)-\d+$")  # Related str element


def esc(text: str) -> str:
    return text.encode("ascii", "backslashreplace").decode("ascii")


def fm_block(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3 or len(parts[0].splitlines()) > 40:
        return None
    return parts[1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()

    findings: list[str] = []
    n_docs = 0
    # pass 1: collect (rel, data) pairs and the Document ID universe
    parsed: list[tuple[str, dict]] = []
    doc_ids: set[int] = set()
    for path in (sorted((args.root / "docs").rglob("*.md"))
                 + sorted((args.root / "experiments").glob("*.md"))):
        rel = path.relative_to(args.root).as_posix()
        text = path.read_text(encoding="utf-8")
        block = fm_block(text)
        if block is None:
            continue  # FS-01's domain
        n_docs += 1
        try:
            data = yaml.safe_load(block)
            if not isinstance(data, dict):
                raise yaml.YAMLError("front matter is not a mapping")
        except (yaml.YAMLError, ValueError, TypeError) as exc:
            # ValueError/TypeError too: PyYAML's timestamp constructor
            # builds dt.date(...) bare, so an impossible bare date
            # ("2026-13-45") raises OUT of safe_load - from the
            # platform's side that is an ingestion crash, not a parse
            # miss (tick-495 lesson, negative test caught the gate
            # itself crashing)
            findings.append(
                "FV-04 %s: front matter fails yaml.safe_load - %s; the "
                "platform ingests FM with this exact call and drops all "
                "metadata when it fails (see docstring)" % (rel, str(exc)[:80]))
            continue
        parsed.append((rel, data))
        did = data.get("Document ID")
        if isinstance(did, int):
            doc_ids.add(did)
        elif isinstance(did, str) and did.isdigit():
            doc_ids.add(int(did))
    # the resource id universe: files under learning-resources carry
    # their id as a filename prefix (LAB-003-LoRA-FineTuning,
    # TUTORIAL-002-Docker-Essentials)
    res_ids: dict[str, set[str]] = {}
    for sub, ns in (("labs", "LAB"), ("tutorials", "TUTORIAL")):
        rdir = args.root / "docs" / "learning-resources" / sub
        ids = res_ids.setdefault(ns, set())
        if rdir.is_dir():
            for p in sorted(rdir.glob("*.md")):
                m = RES_ID.match(p.stem)
                if m:
                    ids.add(m.group(0))
    # pass 2: value contracts
    for rel, data in parsed:
        lu = data.get("Last Updated")
        # yaml auto-converts bare ISO dates to datetime.date - that
        # conversion IS the ISO contract (it fails for impossible
        # dates); quoted ISO strings and (as failure) everything
        # else are checked explicitly
        if isinstance(lu, dt.date) and not isinstance(lu, dt.datetime):
            pass
        elif isinstance(lu, str) and ISO_DATE.match(lu):
            try:
                dt.date(int(lu[:4]), int(lu[5:7]), int(lu[8:10]))
            except ValueError:
                findings.append(
                    "FV-01 %s: Last Updated %r is not a real calendar "
                    "date" % (rel, lu))
        else:
            findings.append(
                "FV-01 %s: Last Updated %r is not YYYY-MM-DD - the "
                "ISO-8601 contract; date parsers crash on locale or "
                "prose forms" % (rel, lu))
        et = data.get("Estimated Time")
        if et is not None and not (isinstance(et, str)
                                   and (TIME_SINGLE.match(et)
                                        or TIME_DOUBLE.match(et))):
            findings.append(
                "FV-02 %s: Estimated Time %r is not machine-comparable - "
                "use \"N hours|minutes\" or the canonical \"30 minutes "
                "(quick review) - N hours (full review)\"; the reading-"
                "time pipeline does arithmetic on this field"
                % (rel, et))
        tags = data.get("Tags")
        # experiments/ keyset (EC-01, tick-608) carries no Tags - the
        # field is neither required nor checked when absent there; docs/
        # convention carries Tags on every FM doc, so absence is a
        # finding on the docs/ side only
        tags_absent_by_keyset = (rel.startswith("experiments/")
                                 and tags is None)
        if not tags_absent_by_keyset and not (
                isinstance(tags, list) and tags
                and all(isinstance(t, str) and t for t in tags)):
            findings.append(
                "FV-03 %s: Tags %r is not a non-empty list of strings - "
                "the platform's tag filter builds UI from this list; "
                "bare/comma strings degrade into one giant token"
                % (rel, tags))
        relv = data.get("Related")
        if relv is not None and not isinstance(relv, (str, list)):
            findings.append(
                "FV-06 %s: Related %r is neither a prose pointer (str) "
                "nor a list - numbers, bools and mappings have no "
                "rendering on the platform (triage census in docstring)"
                % (rel, relv))
        if isinstance(relv, list):
            for el in relv:
                if isinstance(el, bool) or not isinstance(el, (int, str)):
                    findings.append(
                        "FV-06 %s: Related list element %r is neither an "
                        "id (int) nor a name (str) - the platform renders "
                        "Related as next-lesson cards" % (rel, el))
                elif isinstance(el, int) and el not in doc_ids:
                    findings.append(
                        "FV-05 %s: Related references Document ID %d, "
                        "which no doc carries - the platform renders "
                        "Related as next-lesson cards; a dangling id is "
                        "a broken card at runtime" % (rel, el))
                elif isinstance(el, str):
                    m = RES_REF.match(el)
                    if m and el not in res_ids.get(m.group(1), ()):
                        findings.append(
                            "FV-11 %s: Related references %s, which "
                            "matches no file under learning-resources - "
                            "the platform renders Related as next-lesson "
                            "cards; a dangling resource pointer is a "
                            "broken card at runtime" % (rel, el))
        diff = data.get("Difficulty")
        if diff is not None and diff not in CANON_DIFFICULTY:
            findings.append(
                "FV-07 %s: Difficulty %r is not a canonical tier - the "
                "platform's difficulty filter/sort is the closed enum "
                "Beginner/Intermediate/Advanced; a fourth value is an "
                "invisible filter hole" % (rel, diff))
        title = data.get("Title")
        if title is not None and not (isinstance(title, str)
                                      and title.strip()):
            findings.append(
                "FV-08 %s: Title %r is not a non-empty string - it "
                "becomes the platform card title; empty or non-string "
                "renders as nothing" % (rel, title))
        lu_date = None
        if isinstance(lu, dt.date) and not isinstance(lu, dt.datetime):
            lu_date = lu
        elif isinstance(lu, str) and ISO_DATE.match(lu):
            try:
                lu_date = dt.date(int(lu[:4]), int(lu[5:7]), int(lu[8:10]))
            except ValueError:
                pass  # FV-01 already flagged the impossible date
        if lu_date is not None and lu_date > dt.date.today():
            findings.append(
                "FV-09 %s: Last Updated %s is in the future - a date the "
                "doc cannot have been updated on yet poisons "
                "recently-updated sorts" % (rel, lu_date.isoformat()))
        did = data.get("Document ID")
        if isinstance(did, str) and not DOC_KEY.match(did):
            findings.append(
                "FV-10 %s: Document ID %r is not a URL-safe key - the "
                "platform uses it as canonical key AND URL slug; "
                "whitespace or punctuation needs escaping (convention: "
                "uppercase-initial or module-numbered, hyphen-separated "
                "alphanumerics, or the EC-01-canonical EXP_NNNN form - "
                "underscore is RFC-3986 unreserved, no escaping needed)"
                % (rel, did))
        # tick-612: the second tree's Status column and keyset
        # presence - FM-03/FM-04 walk docs/ only and EC-01 binds the
        # Document ID alone, so under experiments/ a missing keyset
        # field or a non-canonical Status answered to no gate;
        # scoped to experiments/ so docs/ stays FM-03/FM-04's alone
        if rel.startswith("experiments/"):
            for key in ("Title", "Status", "Difficulty"):
                if data.get(key) is None:
                    findings.append(
                        "FV-12 %s: keyset field %r is absent - the "
                        "platform catalogs experiments by the full "
                        "EC-01 keyset; Document ID presence is EC-01's "
                        "duty and Last Updated absence fires FV-01 "
                        "already, so this clause carries exactly the "
                        "three fields no other gate saw" % (rel, key))
            st = data.get("Status")
            if st is not None and st not in STATUS_ENUM:
                findings.append(
                    "FV-13 %s: Status %r is not in the FM-04 enum "
                    "{Complete} - the platform's completion filter is "
                    "a closed vocabulary; any other value is an "
                    "invisible filter hole" % (rel, st))
    for f in findings:
        print("  " + esc(f))
    print("frontmatter_value_scan: %d docs with FM inspected; %d FV "
          "findings - hard (FV-01 ISO dates, FV-02 machine-comparable "
          "time, FV-03 Tags list-of-string, FV-04 yaml.safe_load, FV-05 "
          "no dangling Related int, FV-06 Related str-or-list, FV-07 "
          "canonical Difficulty tier, FV-08 non-empty Title string, "
          "FV-09 no future-dated Last Updated, FV-10 URL-safe string "
          "Document ID, FV-11 resolvable LAB-/TUTORIAL- Related refs, "
          "FV-12 experiments/ keyset presence (Title/Status/"
          "Difficulty), FV-13 experiments/ Status in the FM-04 enum = "
          "the platform ingestion simulation; scope tick-611 extended "
          "to experiments/ (48 files): FV-01/04/07/08/09 apply there, "
          "FV-03 is presence-required only where the keyset carries "
          "Tags (docs/) and FV-10's key grammar accepts the EC-01-"
          "canonical EXP_NNNN form (underscore is RFC-3986 unreserved); "
          "scope tick-612: FV-12/FV-13 vouch the second tree's keyset "
          "presence and Status enum - FM-03/FM-04 walk docs/ only; "
          "born tick-493 with one drain ('1 hours' -> '1 hour'), "
          "Related tick-494, tier/title/date tick-495, key-shape "
          "tick-496, resource refs tick-497 - all born-at-zero; see "
          "docstring)"
          % (n_docs, len(findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
