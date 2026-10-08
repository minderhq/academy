#!/usr/bin/env python3
"""Action-version registry gate for the Minder Academy corpus.

AV-01  a ``uses: owner/repo@vN`` pin on any line of a docs/*.md file
       must name an action whose MAJOR version matches the registry
       below. GitHub Actions majors move fast (checkout shipped six
       majors in four years) and a stale pin in teaching material
       becomes wrong the day the old major's node20 runtime is
       retired, so examples must teach current majors. The registry
       is the single source of truth - born from the tick-366..368
       CI-modernization drain that moved ~35 stale pins across the
       corpus (checkout v2/v3/v4 -> v7, cache v3 -> v4, codecov v3
       -> v5, buildx/login v2 -> v3, metadata v4 -> v5, build-push
       v4 -> v6). Baseline 0 at birth.

       Canonical registry at birth (tick-368):
         actions/checkout@v7, astral-sh/setup-uv@v9, actions/cache@v4,
         codecov/codecov-action@v5, docker/setup-buildx-action@v3,
         docker/login-action@v3, docker/metadata-action@v5,
         docker/build-push-action@v6, actions/upload-artifact@v7,
         actions/download-artifact@v8,
         gaurav-nelson/github-action-markdown-link-check@v1.

       Full-tag entries (tick-800): a registry value may be an int
       (major-pin contract, verified against the moving major tag)
       or a string (exact full-tag pin, required when the action
       publishes no resolvable major ref). astral-sh/setup-uv is the
       born case: its tags are full versions only (v10.2.0 latest,
       2026-10 verification), its branches carry no vN major branch,
       and its own README pins by commit SHA - so ``@v9``-style
       majors simply do not resolve, and the corpus teaches the
       readable middle ground ``setup-uv@v10.2.0``. The tick-800
       re-verification against the live release pages also bumped
       cache 4->6, codecov 5->7, buildx 3->4, login 3->4, metadata
       5->6 and build-push 6->7 (the 6502 prose had already taught
       cache@v6 from its own 2026-09 page check - the registry was
       the stale half of that split).

Same change-means-update-the-registry contract as the fence-class
gate: an action NOT in the registry is also a finding - either the
pin is stale or the action is new and needs its current major
recorded. A newer major in the wild bumps the registry number in
the same commit that fixes the examples.

Comment-only mentions (a line whose ``uses:`` sits after a ``#``)
are not findings - the check looks at the part before any ``#``.

Hard gate (exit 1 on findings): baseline 0 at birth (tick-368).

Run over the whole corpus:
    python scripts/qa/action_version_scan.py --root .
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# action (owner/repo) -> current major taught by the corpus.
# An int value is a major-pin contract (the moving major tag exists,
# verified); a str value is an exact full-tag pin (no resolvable
# major ref exists - see the setup-uv note below).
REGISTRY: dict[str, int | str] = {
    "actions/checkout": 7,
    # setup-uv publishes full-version tags only - no major tag and no
    # vN major branch (verified 2026-10 against the tag and branch
    # lists; its own README pins by commit SHA), so @v9-style majors
    # do not resolve. The corpus teaches the full-version pin.
    "astral-sh/setup-uv": "v10.2.0",
    "actions/cache": 6,
    "codecov/codecov-action": 7,
    "docker/setup-buildx-action": 4,
    "docker/login-action": 4,
    "docker/metadata-action": 6,
    "docker/build-push-action": 7,
    "actions/upload-artifact": 7,
    "actions/download-artifact": 8,
    "gaurav-nelson/github-action-markdown-link-check": 1,
    # recorded at birth: TUTORIAL-005 deploy notify steps; v3 is the
    # action's current major (no v4 exists as of 2026-09). v3 resolves
    # as a moving branch (there is no v3 tag), verified 2026-10.
    "8398a7/action-slack": 3,
}

USES_RE = re.compile(
    r"^\s*(?:-\s+)?uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@v(\d+(?:\.\d+)*)\s*$"
)


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8").split("\n")
    for ln, raw in enumerate(lines, 1):
        code = raw.split("#", 1)[0]
        m = USES_RE.match(code)
        if not m:
            continue
        action, ver = m.group(1), m.group(2)
        expected = REGISTRY.get(action)
        if isinstance(expected, int):
            ok = int(ver.split(".")[0]) == expected
        elif isinstance(expected, str):
            ok = f"v{ver}" == expected
        else:
            ok = False
        if not ok:
            want = f"v{expected}" if isinstance(expected, int) else expected
            findings.append(
                f"{rel}:{ln}: AV-01 action pin {action}@v{ver} not "
                f"in the canonical registry (or a stale major; "
                f"expected {action}@{want}) - "
                f"update the pin or record its current major"
            )


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
    print(f"action_version_scan: {len(findings)} findings "
          f"(AV-01 uses: pin off the canonical registry or a stale "
          f"major) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
