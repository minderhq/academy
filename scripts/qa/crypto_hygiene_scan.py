#!/usr/bin/env python3
"""Crypto-hygiene gate for the PROJECT-OMEGA corpus.

CH-01  a ```python fence must not generate security material with the
       ``random`` module - random is a Mersenne Twister: its output is
       predictable from a handful of observed values, so a token, API
       key, OTP, salt or session id built from random.* is forgeable
       (OWASP: "cryptographically secure randomness" - Python's answer
       is the ``secrets`` module). The producer call
       (``random.random/randint/randrange/randbytes/getrandbits/
       uniform/choice/choices/sample/shuffle/rand``) fires when the
       security vocabulary attaches AT THE CALL SITE: an enclosing
       assignment target (``api_key = random.choice(alphabet)``), a
       string-Constant or Name argument (``random.bytes(salt)``),
       a keyword name or keyword value
       (``token=random.random()``), or an enclosing function name
       (``def generate_token(): return random.getrandbits(128)``).

CH-02  the same fence must not weak-hash security material -
       ``hashlib.md5``/``hashlib.sha1`` are collision-broken: two
       chosen inputs share a digest, so a password or token hashed
       with them can be swapped, not just guessed (password storage
       wants PBKDF2/scrypt/argon2; integrity wants sha256). The call
       fires when the security vocabulary attaches to the digest
       input (a string-Constant, Name id or Attribute attr among the
       first argument's leaves: ``hashlib.md5(password.encode())``)
       or to the enclosing assignment target (``secret_hash =
       hashlib.sha1(name)``).

Out of the class by construction:

  - non-security randomness: the ML corpus's 39 random.* calls are
    dropout masks, sampling, shuffling and canary rolls - the
    fence-level vocabulary probe read 24 false positives (5300-PRACTICE
    template sampling, PROJECT-003 dropout, 2304 canary randint);
    only call-site attachment enters (born census tick-654: 0).
  - non-security weak hashing: the corpus's 15 md5 calls are dedup
    checksums and A/B bucketing - TUTORIAL-014 and 2304 both carry
    the corpus's own teaching "md5 here is BUCKETING, not security";
    vocabulary-free digest inputs stay out (born census: 0).
  - the affirmative forms the corpus teaches: ``secrets.token_hex(...)``
    (TUTORIAL-013:438-439 builds key ids exactly so) and
    ``hashlib.sha256(...)`` (the whole 7500-security phase hashes with
    sha256 - 7501/7502/2302/2401) - Attribute bases ``secrets`` and
    ``sha256`` never match the walk.
  - ``random.SystemRandom``: cryptographically secure by design.
  - non-producer random calls (``random.seed(42)`` generates nothing).
  - ``np.random.*``/``numpy.random.*``: the walk demands a bare
    ``random`` Name base; the numpy universe is ML sampling.
  - from-import rebindings (born census: 0 - the corpus imports the
    module form everywhere).
  - string mentions and prose never reach the walk (AST, not text).
  - a fence carrying a danger marker (``DANGEROUS``, ``Wrong:``,
    ``unsafe``, ``vulnerab`` - casefold, any line) is deliberate
    danger-teaching, the sibling unsafe_*/interp gates' escape.
  - notebooks (.ipynb) are outside the md universe.

Hard gate (exit 1 on findings): born census tick-654 read every
random.*/hashlib.md5|sha1 call in every md python fence fence-aware
with call-site attachment = 0 findings (39 random.* producers all
sampling/ML, 15 md5 all dedup/bucketing, 0 sha1) - the corpus's own
security tutorial teaches secrets+sha256 and its infrastructure docs
teach the md5-bucketing distinction, so the class froze at the rule
the moment it was named: zero-drain, hard from birth, owned
preemptively per the US-02/US-03 and RT-02 precedent.

Run over the whole corpus:
    python scripts/qa/crypto_hygiene_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

FENCE_RE = re.compile(r"^\s*(```|~~~)\s*([A-Za-z0-9_+-]*)\s*$")

DANGER_MARKER_RE = re.compile(r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)

# Randomness producers - calls that yield unpredictable material.
RAND_VERBS = {"random", "rand", "randint", "randrange", "randbytes",
              "getrandbits", "uniform", "choice", "choices", "sample",
              "shuffle"}

# Security-material vocabulary; the attachment check, not the fence text.
SEC_VOCAB_RE = re.compile(
    r"token|secret|password|passwd|pwd|api[_-]?key|otp|nonce|salt"
    r"|session[_-]?id|credential|auth[_-]?(code|state)|csrf"
    r"|reset[_-]?code|confirm[_-]?code", re.IGNORECASE)


def _vocab(text: str) -> bool:
    return bool(SEC_VOCAB_RE.search(text))


def _string_constants(node: ast.expr) -> list[str]:
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def _name_ids(node: ast.expr) -> list[str]:
    out = [n.id for n in ast.walk(node) if isinstance(n, ast.Name)]
    out += [n.attr for n in ast.walk(node) if isinstance(n, ast.Attribute)]
    return out


def _ch01_attached(call: ast.Call, assign_name: str | None,
                   func_name: str | None) -> bool:
    if assign_name is not None and _vocab(assign_name):
        return True
    if func_name is not None and _vocab(func_name):
        return True
    for a in call.args:
        if isinstance(a, ast.Constant) and isinstance(a.value, str) \
                and _vocab(a.value):
            return True
        if isinstance(a, ast.Name) and _vocab(a.id):
            return True
    for kw in call.keywords:
        if _vocab(kw.arg or ""):
            return True
        if isinstance(kw.value, ast.Name) and _vocab(kw.value.id):
            return True
    return False


def _ch02_attached(call: ast.Call, assign_name: str | None) -> bool:
    if assign_name is not None and _vocab(assign_name):
        return True
    if not call.args:
        return False
    arg0 = call.args[0]
    if any(_vocab(s) for s in _string_constants(arg0)):
        return True
    if any(_vocab(i) for i in _name_ids(arg0)):
        return True
    return False


def _scan_fence(rel: str, start: int, fence_lines: list[tuple[int, str]],
                findings: list[str]) -> None:
    src = "\n".join(raw for _, raw in fence_lines)
    if DANGER_MARKER_RE.search(src):
        return
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return
    base = start  # fence content line 1 == fence-open line + 1

    assigns: dict[int, str] = {}   # call lineno -> enclosing assign target
    funcs: dict[int, str] = {}     # call lineno -> enclosing def name

    class _Collector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.func_name: str | None = None
            self.assign_name: str | None = None

        def visit_FunctionDef(self, node) -> None:  # type: ignore[override]
            prev, self.func_name = self.func_name, node.name
            self.generic_visit(node)
            self.func_name = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Assign(self, node) -> None:  # type: ignore[override]
            prev = self.assign_name
            if len(node.targets) == 1 and isinstance(node.targets[0],
                                                     ast.Name):
                self.assign_name = node.targets[0].id
            self.generic_visit(node)
            self.assign_name = prev

        def visit_AnnAssign(self, node) -> None:  # type: ignore[override]
            prev = self.assign_name
            if isinstance(node.target, ast.Name):
                self.assign_name = node.target.id
            self.generic_visit(node)
            self.assign_name = prev

        def visit_AugAssign(self, node) -> None:  # type: ignore[override]
            prev = self.assign_name
            if isinstance(node.target, ast.Name):
                self.assign_name = node.target.id
            self.generic_visit(node)
            self.assign_name = prev

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                base_node = node.func.value
                base_name = base_node.id if isinstance(base_node, ast.Name) \
                    else None
                if (base_name == "random" and attr in RAND_VERBS
                        and _ch01_attached(node, self.assign_name,
                                           self.func_name)):
                    assigns[node.lineno] = self.assign_name or ""
                    funcs[node.lineno] = self.func_name or ""
                    findings.append(
                        f"{rel}:{base + node.lineno}: CH-01 security "
                        f"material built with random.{attr}() - the "
                        f"Mersenne Twister is predictable from observed "
                        f"output, so a token/key/OTP/salt from random.* "
                        f"is forgeable; use the secrets module "
                        f"(secrets.token_hex/token_urlsafe/randbelow), "
                        f"the TUTORIAL-013-AI-Security idiom")
                elif (base_name == "hashlib"
                      and attr in ("md5", "sha1")
                      and _ch02_attached(node, self.assign_name)):
                    assigns[node.lineno] = self.assign_name or ""
                    findings.append(
                        f"{rel}:{base + node.lineno}: CH-02 security "
                        f"material weak-hashed with hashlib.{attr}() - "
                        f"md5/sha1 are collision-broken, a hashed "
                        f"password/token can be swapped not just "
                        f"guessed; hash with hashlib.sha256 (the "
                        f"7500-security idiom) and store passwords "
                        f"under PBKDF2/scrypt/argon2")
            self.generic_visit(node)

    _Collector().visit(tree)


def scan_file(root: Path, path: Path, findings: list[str]) -> None:
    rel = path.relative_to(root).as_posix()
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    in_fence = False
    lang = ""
    start = 0
    fence_lines: list[tuple[int, str]] = []
    for ln, raw in enumerate(lines, 1):
        if FENCE_RE.match(raw):
            if in_fence and lang == "python" and fence_lines:
                _scan_fence(rel, start, fence_lines, findings)
            in_fence = not in_fence
            lang = "" if not in_fence else FENCE_RE.match(raw).group(2).lower()
            start = ln if in_fence else 0
            fence_lines = []
            continue
        if in_fence:
            fence_lines.append((ln, raw))
    if in_fence and lang == "python" and fence_lines:
        _scan_fence(rel, start, fence_lines, findings)


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
    print(f"crypto_hygiene_scan: {len(findings)} findings "
          f"(CH-01 random-for-security-material, CH-02 weak-hash on "
          f"security-material) in {len(n_files)} files across docs/")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
