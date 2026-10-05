#!/usr/bin/env python3
"""notebook code-cell gate (NBC-01..14) for Minder Academy.

The .md AST gate family never sees notebook code: codeblock_syntax_scan
and fence_import_check walk CommonMark fences in docs/**/*.md, while
docs/notebooks/*.ipynb code cells are JSON - a notebook teaching broken
code ships to the platform crawler, the launcher runs it, and the
learner hits the failure mid-lesson. NBC extends the fence-gate
judgments to the notebook universe.

NBC-01  code-cell syntax: ast.parse fails on a cell's joined source -
        the same guarantee codeblock_syntax_scan gives every ```python
        fence (CB-01), applied per cell. Cell indices are 0-based
        positions in the file's `cells` list (markdown cells count).

NBC-02  unresolvable import root: a top-level import root that neither
        resolves against the kurulu-stack nor belongs to the corpus
        class - fence_import_check's IC-01 judgment, mirrored
        mechanism-for-mechanism (import_module with a verdict cache,
        dotted-ancestor class matching, relative imports skipped and
        counted). A syntax-failed cell is an NBC-01 finding and its
        imports are not walked (there is no AST to walk).

NBC-03..11  the unsafe family's twin (born tick-702): the .md
        unsafe gates (broad_except_scan, unsafe_deserialize_scan,
        mutable_default_scan, insecure_temp_scan, http_timeout_scan,
        open_encoding_scan, cors_wildcard_scan, secret_shape_scan,
        trust_remote_code_scan, crypto_hygiene_scan) each declare
        ".ipynb are outside the md universe" - their docstrings
        walk docs/**/*.md only, while the launcher RUNS notebook
        code cells, so every unsafe pattern class was invisible to
        the whole fleet inside .ipynb. The census->classify->lock
        way (tick-702 census: 20 notebooks / 102 code cells,
        token-level family rules) measured 4 real teaching-code
        defects across 3 notebooks (NB-204 c9 empty mutable
        default, NB-205 c5+c7 bare except, NB-701 c3 eval + broad
        except) - all drained in-tick, and 8 further classes
        measured clean (pickle/dill, yaml.unsafe, shell=True,
        os.system, mktemp, trust_remote_code, open-no-encoding,
        requests-no-timeout). The gate is born at zero over the
        drained corpus. AST-judged (not token-regex) so a comment
        mentioning eval or a string containing except: never
        fires; the rules:

        NBC-03  bare or broad except: an ExceptHandler with no type
                (bare) or whose type is/contains Exception or
                BaseException (broad, tuples included). A bare
                handler hides real failures from the learner; the
                narrow class the call actually raises is the
                teaching point.
        NBC-04  unsafe deserialization: a call to pickle.load(s) /
                dill.load(s) (an untrusted pickle executes code on
                load) or yaml.load / yaml.unsafe_load /
                yaml.full_load (constructor tags run; safe_load is
                the safe name and stays silent).
        NBC-05  eval / exec call: a plain Name call (an attribute
                call like obj.eval is a method, not the builtin -
                silent, mirroring the census lookbehind).
        NBC-06  empty mutable default: a function (nested included)
                defaulting a parameter to [], {} or set() - created
                once at def time and shared across calls.
        NBC-07  shell out: a call to os.system / os.popen, or any
                call carrying shell=True.
        NBC-08  tempfile race: a call to mktemp (tempfile.mktemp or
                a from-import); mkstemp/NamedTemporaryFile are the
                safe names.
        NBC-09  trust_remote_code=True: the keyword anywhere - the
                corpus convention teaches the False default.
        NBC-10  open without encoding: a builtin open() call with
                no encoding kwarg (a **kwargs splat is unknown and
                stays silent) - the host locale varies, the
                platform expects utf-8.
        NBC-11  requests without timeout: requests.get/post/put/
                delete/head/patch with no timeout kwarg (splat
launcher cell.

NBC-12..14  the secret/crypto twins (born tick-703): secret_shape_scan
        (SS-01) and crypto_hygiene_scan (CH-01/CH-02) declare
        ".ipynb are outside the md universe" like the rest of the
        family - the launcher RUNS code cells, so a leaked key
        shape, a token built from random.* or a weak hash on
        security material was invisible inside notebooks. The
        tick-703 census measured the closet clean (0 provider
        shapes, 8 random.* producers all ML sampling with no
        security vocabulary attached, 0 md5/sha1 calls) and the
        extension is born at zero to keep it; a cell carrying the
        danger marker (DANGEROUS / wrong: / unsafe / vulnerab,
        casefold - the md twins' escape) stays silent for these
        three rules.

        NBC-12  credentialed-shaped string constant: a provider
                key shape (sk- + 20+, ghp_/gho_/ghu_/ghs_/ghr_ +
                30+, github_pat_ + 22+, AKIA + 16, AIza + 35, xox-
                + 10+) - a shape on the page reads as a leaked
                credential and GitHub secret scanning flags it on
                push; the tail demands partition placeholders by
                construction, and environment reads never carry
                the shape (the walk sees string Constants only).
        NBC-13  security material from random: a random.<producer>()
                call (bare random Name base only - np.random is the
                ML sampling universe) when the security vocabulary
                attaches at the call site (assignment target,
                enclosing def name, string-Constant or Name
                argument, keyword name or Name keyword value).
        NBC-14  security material weak-hashed: hashlib.md5/sha1
                when the vocabulary attaches to the digest input
                or the assignment target - vocabulary-free
                dedup/bucketing hashing stays out, the md twin's
                measured carve.

Structural health (unparseable JSON, malformed cells/sources) is
NBH-03's jurisdiction - NBC silently skips what NBH flags, and the
NEG face is the designed cross-gate agreement, not a gap.

The corpus class (born tick-691 from the probe census, the same
census->classify->lock path fence_import_check took at tick-323/325):
alternative / optional third-party stacks the notebooks deliberately
reference without requiring installation, each one declared by the
corpus's own dependency surfaces - ENVIRONMENT-SETUP.md installs
chromadb, sentence-transformers and trl via `uv pip install`
(LAB-003 pins trl>=1.14.0 via `uv add`, 4102 teaches
`uv pip install optimum`, SOL-001 pins sentence-transformers==6.1.0).
A root outside the class means a learner hits ModuleNotFoundError as
written: exit 1.

Born tick-691 from the probe census: 20 notebooks, 224 cells (102
code), syntax_fails=2 -> both real defects drained this tick (NB-203
cell 7 - a quote-collision raw regex string that terminated early;
NB-703 cell 5 - a literal backslash-n inside a list tail), and
unresolvable_roots=4 (sentence_transformers x4, optimum x1, trl x1,
chromadb x1) -> all classified into the corpus class. Born at zero,
hard-gated so the broken-teaching class can never regrow.

NBC-03..11 born tick-702 the same way: the census measured the md
unsafe family's declared blind spot as real (4 teaching-code defects
in 3 notebooks), the drains landed first (mutable default -> None +
or, bare except -> ImportError, eval -> an AST allow-list evaluator),
and the gate was born at zero over the drained corpus - the NBT
drain-and-lock order.

NBC-12..14 born tick-703 the NBM-06 way: the census measured the
closet CLEAN (0 shapes, 8 sampling producers vocab-free, 0 md5/sha1
calls across the same 20 notebooks / 102 code cells), so there was
nothing to drain - the extension is born at zero to keep the
convention (credentials from the environment, randomness stays ML
sampling, sha256 for any real hashing).

Hard gate (exit 1 on findings): baseline 0 at birth (tick-691 for
NBC-01..02, tick-702 for NBC-03..11, tick-703 for NBC-12..14).

Run over the whole corpus:
    python scripts/qa/notebook_code_scan.py --root .
"""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import re
import sys
from pathlib import Path

for _pkg in ("torch", "pydantic"):
    try:
        importlib.import_module(_pkg)
    except ImportError:  # environment problem, not a doc problem
        print(f"notebook_code_scan: {_pkg} not importable in this "
              "interpreter - NBC-02 resolves cell imports against the "
              "kurulu-stack; run the scorecard with that python "
              "(see ENVIRONMENT-SETUP.md)")
        sys.exit(2)

# The corpus class for the notebook universe (born tick-691): the
# alternative/optional third-party stacks the notebooks deliberately
# reference, each declared by the corpus's own dependency surfaces
# (ENVIRONMENT-SETUP.md uv pip lines, LAB-003's uv add line, 4102's
# uv pip install optimum, SOL-001's requirements block). Dotted
# ancestors match, so optimum.bettertransformer is accepted without
# weakening the gate for a genuinely-missing root.
NBC_ACCEPTED = frozenset({
    "chromadb", "optimum", "sentence_transformers", "trl",
})

_verdict_cache: dict[str, bool] = {}


def resolves(root: str) -> bool:
    """True when the import root resolves against the kurulu-stack."""
    if root in _verdict_cache:
        return _verdict_cache[root]
    try:
        importlib.import_module(root)
        ok = True
    except Exception:  # noqa: BLE001 - any failure means "cannot run"
        ok = False
    _verdict_cache[root] = ok
    return ok


def accepted(root: str) -> bool:
    """True when root or a dotted ancestor is a corpus class member."""
    while root:
        if root in NBC_ACCEPTED:
            return True
        root = root.rpartition(".")[0]
    return False


def cell_source(cell: dict) -> str:
    src = cell.get("source")
    if isinstance(src, list):
        return "".join(s for s in src if isinstance(s, str))
    return src if isinstance(src, str) else ""


_BROAD_EXC = ("Exception", "BaseException")
_DESERIALIZE = {
    "pickle": ("load", "loads"),
    "dill": ("load", "loads"),
}
_YAML_UNSAFE = ("load", "unsafe_load", "full_load")
_HTTP_VERBS = ("get", "post", "put", "delete", "head", "patch")

# The secret/crypto twins (born tick-703), mirrored from
# secret_shape_scan (SS-01) and crypto_hygiene_scan (CH-01/CH-02).
_SECRET_SHAPES = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{22,}"),
    re.compile(r"\bAKIA[A-Z0-9]{16}"),
    re.compile(r"\bAIza[0-9A-Za-z_-]{35}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
)
_DANGER_RE = re.compile(
    r"DANGEROUS|wrong:|unsafe|vulnerab", re.IGNORECASE)
_SEC_VOCAB_RE = re.compile(
    r"token|secret|password|passwd|pwd|api[_-]?key|otp|nonce|salt"
    r"|session[_-]?id|credential|auth[_-]?(code|state)|csrf"
    r"|reset[_-]?code|confirm[_-]?code", re.IGNORECASE)
_RAND_VERBS = frozenset({
    "random", "rand", "randint", "randrange", "randbytes",
    "getrandbits", "uniform", "choice", "choices", "sample",
    "shuffle",
})


def dotted_name(node: ast.expr) -> str | None:
    """Dotted name of a Name/Attribute chain, else None."""
    parts: list[str] = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None


def kw_is_true(call: ast.Call, name: str) -> bool:
    """True when the call carries keyword name with literal True."""
    return any(kw.arg == name
               and isinstance(kw.value, ast.Constant)
               and kw.value.value is True
               for kw in call.keywords)


def has_splat(call: ast.Call) -> bool:
    """True when the call carries **kwargs (argument surface unknown)."""
    return any(kw.arg is None for kw in call.keywords)


def broad_handler(exc_type: ast.expr | None) -> str | None:
    """'bare' or 'broad' for an ExceptHandler.type, else None."""
    if exc_type is None:
        return "bare"
    if isinstance(exc_type, ast.Name):
        return "broad" if exc_type.id in _BROAD_EXC else None
    if isinstance(exc_type, ast.Attribute):
        return "broad" if exc_type.attr in _BROAD_EXC else None
    if isinstance(exc_type, ast.Tuple):
        if any(broad_handler(elt) for elt in exc_type.elts):
            return "broad"
    return None


def empty_mutable(default: ast.expr) -> bool:
    """[] / {} / set() as a parameter default."""
    if isinstance(default, (ast.List, ast.Set)) and not default.elts:
        return True
    if isinstance(default, ast.Dict) and not default.keys:
        return True
    if isinstance(default, ast.Call):
        return (dotted_name(default.func) == "set"
                and not default.args and not default.keywords)
    return False


def sec_vocab(text: str) -> bool:
    """Security-vocabulary probe (the md crypto twin's attachment)."""
    return bool(_SEC_VOCAB_RE.search(text))


def ch01_attached(call: ast.Call, assign_name: str | None,
                  func_name: str | None) -> bool:
    """Vocabulary attached to a random.* call site."""
    if assign_name is not None and sec_vocab(assign_name):
        return True
    if func_name is not None and sec_vocab(func_name):
        return True
    for a in call.args:
        if (isinstance(a, ast.Constant) and isinstance(a.value, str)
                and sec_vocab(a.value)):
            return True
        if isinstance(a, ast.Name) and sec_vocab(a.id):
            return True
    for kw in call.keywords:
        if sec_vocab(kw.arg or ""):
            return True
        if isinstance(kw.value, ast.Name) and sec_vocab(kw.value.id):
            return True
    return False


def ch02_attached(call: ast.Call, assign_name: str | None) -> bool:
    """Vocabulary attached to a hashlib weak-hash call site."""
    if assign_name is not None and sec_vocab(assign_name):
        return True
    if not call.args:
        return False
    arg0 = call.args[0]
    consts = [n.value for n in ast.walk(arg0)
              if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    ids = ([n.id for n in ast.walk(arg0) if isinstance(n, ast.Name)]
           + [n.attr for n in ast.walk(arg0)
              if isinstance(n, ast.Attribute)])
    return (any(sec_vocab(s) for s in consts)
            or any(sec_vocab(i) for i in ids))


def scan_security(src: str, tree: ast.AST, rel: str, idx: int,
                  findings: list[str]) -> None:
    """NBC-12..14 over one parsed cell tree (danger-marker escape
    mirrored from the md twins, per cell)."""
    if _DANGER_RE.search(src):
        return
    for node in ast.walk(tree):
        if (isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and any(p.search(node.value) for p in _SECRET_SHAPES)):
            findings.append(
                f"{rel}: NBC-12 credentialed-shaped string literal in "
                f"code cell {idx} - a provider key shape on the page "
                f"reads as a leaked credential and GitHub secret "
                f"scanning flags it on push; read it from the "
                f"environment (os.environ / os.getenv)")

    class _Collector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.func_name: str | None = None
            self.assign_name: str | None = None

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            prev, self.func_name = self.func_name, node.name
            self.generic_visit(node)
            self.func_name = prev

        visit_AsyncFunctionDef = visit_FunctionDef

        def _assign(self, target: ast.expr) -> bool:
            if isinstance(target, ast.Name):
                self.assign_name = target.id
                return True
            return False

        def visit_Assign(self, node: ast.Assign) -> None:
            prev = self.assign_name
            if len(node.targets) == 1:
                self._assign(node.targets[0])
            self.generic_visit(node)
            self.assign_name = prev

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            prev = self.assign_name
            self._assign(node.target)
            self.generic_visit(node)
            self.assign_name = prev

        def visit_AugAssign(self, node: ast.AugAssign) -> None:
            prev = self.assign_name
            self._assign(node.target)
            self.generic_visit(node)
            self.assign_name = prev

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute):
                attr = node.func.attr
                base_node = node.func.value
                base = (base_node.id
                        if isinstance(base_node, ast.Name) else None)
                if (base == "random" and attr in _RAND_VERBS
                        and ch01_attached(node, self.assign_name,
                                          self.func_name)):
                    findings.append(
                        f"{rel}: NBC-13 security material built with "
                        f"random.{attr}() in code cell {idx} - the "
                        f"Mersenne Twister is predictable from "
                        f"observed output, so a token/key/salt from "
                        f"random.* is forgeable; use the secrets "
                        f"module (token_hex/token_urlsafe/randbelow)")
                elif (base == "hashlib" and attr in ("md5", "sha1")
                        and ch02_attached(node, self.assign_name)):
                    findings.append(
                        f"{rel}: NBC-14 security material weak-hashed "
                        f"with hashlib.{attr}() in code cell {idx} - "
                        f"md5/sha1 are collision-broken, a hashed "
                        f"password/token can be swapped not just "
                        f"guessed; hash with hashlib.sha256 and "
                        f"store passwords under PBKDF2/scrypt/argon2")
            self.generic_visit(node)

    _Collector().visit(tree)


def scan_unsafe(tree: ast.AST, rel: str, idx: int,
                findings: list[str]) -> None:
    """NBC-03..11 over one parsed cell tree."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            which = broad_handler(node.type)
            if which:
                findings.append(
                    f"{rel}: NBC-03 {which} except in code cell {idx} - "
                    f"a {which} handler swallows every failure the "
                    f"launcher cell hits; catch the narrow exception "
                    f"the call actually raises")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            defaults = list(node.args.defaults) + [
                d for d in node.args.kw_defaults if d is not None]
            for default in defaults:
                if empty_mutable(default):
                    findings.append(
                        f"{rel}: NBC-06 empty mutable default on "
                        f"'{node.name}' in code cell {idx} - the "
                        f"default object is created once at def time "
                        f"and shared across calls; take None and "
                        f"build inside the function")
        elif isinstance(node, ast.Call):
            fn = node.func
            name = dotted_name(fn)
            if (isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id in _DESERIALIZE
                    and fn.attr in _DESERIALIZE[fn.value.id]):
                findings.append(
                    f"{rel}: NBC-04 unsafe deserialization "
                    f"{name}(...) in code cell {idx} - an untrusted "
                    f"pickle executes code on load; exchange data as "
                    f"json or pickle only trusted self-produced bytes")
            elif (isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "yaml"
                    and fn.attr in _YAML_UNSAFE):
                findings.append(
                    f"{rel}: NBC-04 unsafe deserialization "
                    f"yaml.{fn.attr}(...) in code cell {idx} - the "
                    f"loader runs constructor tags; use yaml.safe_load")
            elif isinstance(fn, ast.Name) and fn.id in ("eval", "exec"):
                findings.append(
                    f"{rel}: NBC-05 eval/exec call in code cell {idx} "
                    f"- executes arbitrary code from its argument, "
                    f"and lesson input flows through the launcher; "
                    f"parse the expression (ast) or use "
                    f"ast.literal_eval")
            elif name in ("os.system", "os.popen") or kw_is_true(
                    node, "shell"):
                findings.append(
                    f"{rel}: NBC-07 shell-out call in code cell {idx} "
                    f"- runs a shell with the caller's privileges and "
                    f"a lesson string is untrusted input; use the "
                    f"subprocess list form with shell=False")
            elif (isinstance(fn, (ast.Name, ast.Attribute))
                    and (fn.id if isinstance(fn, ast.Name) else fn.attr)
                    == "mktemp"):
                findings.append(
                    f"{rel}: NBC-08 tempfile.mktemp in code cell "
                    f"{idx} - a race-prone predictable name another "
                    f"process can claim; use NamedTemporaryFile or "
                    f"mkstemp")
            elif kw_is_true(node, "trust_remote_code"):
                findings.append(
                    f"{rel}: NBC-09 trust_remote_code=True in code "
                    f"cell {idx} - executes model-repo code on this "
                    f"host; the corpus convention is the False "
                    f"default")
            elif (isinstance(fn, ast.Name) and fn.id == "open"
                    and not has_splat(node)
                    and not any(kw.arg == "encoding"
                                for kw in node.keywords)):
                findings.append(
                    f"{rel}: NBC-10 open() without encoding in code "
                    f"cell {idx} - text decodes with the host locale "
                    f"while the platform expects utf-8; pass "
                    f"encoding='utf-8'")
            elif (isinstance(fn, ast.Attribute)
                    and isinstance(fn.value, ast.Name)
                    and fn.value.id == "requests"
                    and fn.attr in _HTTP_VERBS
                    and not has_splat(node)
                    and not any(kw.arg == "timeout"
                                for kw in node.keywords)):
                findings.append(
                    f"{rel}: NBC-11 requests.{fn.attr} without timeout "
                    f"in code cell {idx} - a hung endpoint hangs the "
                    f"launcher cell forever; pass a timeout")


def scan_nb(root: Path, path: Path, findings: list[str],
            stats: list[int]) -> None:
    rel = path.relative_to(root).as_posix()
    try:
        nb = json.loads(path.read_bytes().decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, OSError):
        stats[2] += 1  # structural-health jurisdiction: NBH-03 flags it
        return
    if not isinstance(nb, dict) or not isinstance(nb.get("cells"), list):
        stats[2] += 1
        return
    for idx, cell in enumerate(nb["cells"]):
        if not isinstance(cell, dict) or cell.get("cell_type") != "code":
            continue
        stats[1] += 1
        if not isinstance(cell.get("source"), (str, list)):
            stats[2] += 1  # NBH-03 jurisdiction
            continue
        src = cell_source(cell)
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            findings.append(
                f"{rel}: NBC-01 code cell {idx} fails to parse - "
                f"{exc.msg}")
            continue
        scan_unsafe(tree, rel, idx, findings)
        scan_security(src, tree, rel, idx, findings)
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    stats[3] += 1  # relative: no package context, skipped
                    continue
                root_name = (node.module or "").split(".")[0]
                if root_name:
                    roots.add(root_name)
        for root_name in sorted(roots):
            if accepted(root_name) or resolves(root_name):
                stats[4] += 1
            else:
                findings.append(
                    f"{rel}: NBC-02 import root '{root_name}' in code "
                    f"cell {idx} does not resolve and is outside the "
                    f"corpus class - a learner hits "
                    f"ModuleNotFoundError as written")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    findings: list[str] = []
    stats = [0, 0, 0, 0, 0]  # notebooks, code cells, NBH-skipped, rel, ok
    for path in sorted((args.root / "docs" / "notebooks").glob("*.ipynb")):
        stats[0] += 1
        scan_nb(args.root, path, findings, stats)
    for f in findings:
        print(f.encode("ascii", "backslashreplace").decode("ascii"))
    print(f"notebook_code_scan: {len(findings)} findings "
          f"(NBC-01 code-cell syntax / NBC-02 unresolvable import root "
          f"/ NBC-03..14 the unsafe family twin: bare-broad except, "
          f"unsafe deserialize, eval-exec, empty mutable default, "
          f"shell-out, mktemp, trust_remote_code, open-no-encoding, "
          f"requests-no-timeout, secret-shape literals, "
          f"random-for-security, weak-hash-security; "
          f"{stats[4]} import(s) accepted, {stats[3]} relative skipped, "
          f"{stats[2]} cell(s) left to NBH-03) across {stats[0]} "
          f"notebooks / {stats[1]} code cells in docs/notebooks/ "
          f"(hard; born tick-691 at zero - 2 real syntax defects "
          f"drained, 4 unresolvable roots corpus-classified; NBC-03..11 "
          f"born tick-702 at zero - the md unsafe family's declared "
          f"blind spot closed, 4 real teaching-code defects drained "
          f"in-tick; NBC-12..14 born tick-703 at zero - the "
          f"secret/crypto twins closed, the census clean)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
