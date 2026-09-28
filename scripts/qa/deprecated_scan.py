#!/usr/bin/env python3
"""deprecated-API gate for the PROJECT-OMEGA corpus.

DA-01  a ```python fence must not call ``datetime.utcnow()`` or
       ``datetime.utcfromtimestamp()``. Both are deprecated since
       Python 3.12 (the corpus stack is 3.13) and return naive
       datetimes - the modern idiom is the timezone-aware
       ``datetime.now(timezone.utc)``. Naive ``utcnow().timestamp()``
       is worse than deprecated: it silently interprets the value in
       the local timezone. The drained corpus also shows why the naive
       pattern hurts pedagogy: ``isoformat() + "Z"`` produced a
       double suffix once the aware form carries its own ``+00:00``.

DA-02  a ```python fence must not pass ``use_auth_token=``. The HF
       hub kwarg is removed in transformers 5.x (the installed stack
       is 5.10.2: zero references left in from_pretrained) and its
       modern name is ``token=`` - empirically verified against the
       installed package before the rule was written (tick-228).

DA-03  a ```python fence must not call the pydantic v1 API:
       ``@validator``, ``@root_validator``, ``parse_obj_as()`` or
       ``.dict()``. All are deprecated in pydantic 2.x (the installed
       stack is 2.13.5 - empirically verified: ``.dict()`` emits
       PydanticDeprecatedSince20, ``.model_dump()`` is clean) and are
       slated for removal in pydantic 3; the modern names are
       ``.model_dump()`` and ``@field_validator``. The ``.dict()``
       pattern is only activated when the file imports pydantic -
       multiprocessing's ``manager.dict()`` shares the shape and is
       legitimate stdlib, so the shape-only rule would false-positive
       on it (the unambiguous v1-only names stay unconditional).

Comment-only mentions (a fence teaching that utcnow is deprecated,
like the 2303 API-design lesson) are not findings: the check looks
for the pattern position before any ``#`` on the line.

Hard gate (exit 1 on findings): baseline 0 after the tick-227 drain
(13 call sites across 7 files moved to ``datetime.now(timezone.utc)``),
the tick-228 drain (LAB-012 ``use_auth_token=False`` → ``token=``) and
the tick-235 drain (LAB-007 ``doc.dict()`` → ``doc.model_dump()``).

Run over the whole corpus:
    python scripts/qa/deprecated_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

# (pattern, message) pairs - each finding reports the first matching rule.
RULES = [
    (re.compile(r"\bdatetime\.utcnow\b|\bdatetime\.utcfromtimestamp\b"),
     "DA-01 deprecated datetime API (since Python 3.12) - use "
     "datetime.now(timezone.utc)"),
    (re.compile(r"\buse_auth_token\s*="),
     "DA-02 HF use_auth_token kwarg (removed in transformers 5.x) - "
     "use token="),
    (re.compile(r"@validator\b|@root_validator\b|parse_obj_as\("),
     "DA-03 pydantic v1 validation API (deprecated in 2.x, removed in "
     "3) - use @field_validator / TypeAdapter"),
]

# DA-03 continuation: ``.dict()`` is only flagged in files that import
# pydantic - multiprocessing's ``manager.dict()`` shares the shape and
# is legitimate stdlib (tick-235: the only corpus hit would have been
# a false positive without the file-level activation).
PYD_RULES = [
    (re.compile(r"\.dict\(\)"),
     "DA-03 pydantic v1 serialization API (.dict() deprecated in 2.x, "
     "removed in 3) - use model_dump()"),
]
PYD_IMPORT_RE = re.compile(r"^\s*from pydantic import|\bimport pydantic\b")


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    rules = list(RULES)
    if any(PYD_IMPORT_RE.search(line) for line in lines):
        rules += PYD_RULES
    in_fence = False
    lang = ""
    start = 0
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            in_fence = not in_fence
            lang = "" if not in_fence else FENCE_RE.match(raw).group(2).lower()
            start = ln if in_fence else 0
            continue
        if in_fence and lang == "python":
            code = raw.split("#", 1)[0]
            for pat, msg in rules:
                if pat.search(code):
                    findings.append(
                        f"{rel}:{ln}: {msg}; opened at line {start}")
                    break


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    docs = args.root / "docs"
    findings: list[str] = []
    n_files: set[str] = set()
    for path in sorted(docs.rglob("*.md")):
        try:
            before = len(findings)
            scan_file(args.root, path, findings)
            if len(findings) > before:
                n_files.add(path.relative_to(args.root).as_posix())
        except (UnicodeDecodeError, OSError):
            continue
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"deprecated_scan: {len(findings)} findings "
          f"(DA-01 datetime.utcnow/utcfromtimestamp, "
          f"DA-02 use_auth_token, "
          f"DA-03 pydantic v1 API) "
          f"in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
