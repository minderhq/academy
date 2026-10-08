#!/usr/bin/env python3
"""notebook code-cell gate (NBC-01..24) for Minder Academy.

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
        NBC-15  insecure TLS verification (born tick-704): a
                requests.<verb> call carrying a falsy verify=
                constant, a .verify attribute assigned False/None,
                ssl._create_unverified_context(), or a .verify_mode
                assignment of ssl.CERT_NONE - every face turns
                certificate validation off, so the endpoint's
                identity claim is unchecked and a man-in-the-middle
                reads everything the cell sends (the requests
                verbs mirror NBC-11's base).
        NBC-16  legacy typing spelling (born tick-706): the
                typing_legacy_scan (TL-01..03) twin - the md gate
                walks docs/**/*.md python fences only, while the
                launcher RUNS code cells, so a cell teaching
                Optional[...] / a from-typing import of the legacy
                names / a bare -> Dict was invisible to the
                modernity doctrine. Judged per-line on the joined
                source (the family's first per-line face,
                deliberate), first match wins per line in the TL
                order (import, bracket, bare), and strings and
                comments are NOT exempted - a legacy spelling
                inside a docstring also teaches the old idiom, the
                md twin's documented design.
        NBC-17..21  deprecated-API spellings (born tick-707):
                the deprecated_scan (DA-01..05) twin - the md
                gate walks docs/**/*.md python fences only,
                while the launcher RUNS code cells, so a cell
                calling datetime.utcnow() (DA-01, deprecated
                since 3.12, naive datetimes), passing the
                removed HF use_auth_token= kwarg (DA-02, gone
                in transformers 5.x), speaking the pydantic v1
                API @validator / @root_validator / parse_obj_as
                or the pydantic-imported .dict() (DA-03),
                importing the torch.cuda.amp namespace (DA-04,
                deprecated since PyTorch 2.4) or passing
                torch_dtype= (DA-05, the transformers shim
                that warns on every load) was invisible to the
                whole fleet inside notebooks. Same per-line
                face as NBC-16 (deliberate: the DA judgment
                is per-line), first match wins per line in
                the DA rule order, and the #-split carve
                comes first - a comment teaching the
                deprecation stays invisible (the md twin's
                documented design); the .dict() face
                activates only when the notebook imports
                pydantic (the md twin's per-file activation
                mirrored per notebook, so multiprocessing's
                manager.dict() stays legitimate stdlib).
        NBC-22..23  the SQL-interpolation twins (born tick-708):
                the sql_interp_scan (SQ-01/SQ-02) twin - the md
                gate walks docs/**/*.md python fences only,
                while the launcher RUNS code cells, so a cell
                passing an f-string carrying SQL text to an
                execution call (NBC-22, direct or via a query
                variable resolved one hop to its nearest
                preceding assignment, the += fragment chain
                included), or merging the query client-side by
                percent-formatting, str.format() or
                placeholder-free concatenation (NBC-23), was
                invisible to the whole fleet inside notebooks.
                The walk enters only when the query expression's
                string leaves carry SQL vocabulary, carves the
                Constant query with %s/? placeholders plus a
                params second argument and the placeholder-
                carrying builder, and escapes on the danger
                marker per cell (DANGEROUS / wrong: / unsafe /
                vulnerab, casefold - the md twins' escape).
        NBC-24  the Cypher-interpolation twin (born tick-709):
                the cypher_interp_scan (CI-01/CI-02) twin - the md
                gate walks docs/**/*.md python fences only, while
                the launcher RUNS code cells, so a cell passing an
                f-string to a run()/execute_query() call whose
                literal part ends at ":" (a label/rel-type
                position, the md twin's CI-01) or at ".."/"*" (a
                variable-length path bound, CI-02) was invisible
                to the whole fleet inside notebooks. $parameters
                bind values, never schema names (6301-Neo4j), and
                cannot set variable-length path bounds
                (6304-GraphRAG), so the interpolated value
                reaches the query engine raw. Escapes per
                interpolant: the int-cast (max(1, int(x))), the
                allowlist membership guard on the interpolated
                name, a one-hop Name resolving to a cast-shaped
                value; the danger marker escapes per cell (the
                md twins' escape).

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

NBC-15 born tick-704 the same born-at-zero way: the census measured
the TLS-off closet clean (0 falsy verify= kwargs, 0 .verify
assignments, 0 _create_unverified_context calls, 0 CERT_NONE
assignments across the same 20 notebooks / 102 code cells) and the
class has no md twin at all - invisible to the whole fleet on both
surfaces - so the extension locks the convention (certificate
verification stays on in runnable code).

NBC-16 born tick-706 the drain-and-lock way: the census (the TL
judgment mirrored exactly) measured 24 real legacy spellings across
6 notebooks (10 bracket, 4 import, 10 bare) - the docs-fence modernity
epic had drained the md universe corpus-wide while the notebook layer
stayed invisible - the drains landed first (builtin generics, PEP 604
unions, the four import lines removed), and the gate was born over
the drained corpus, hard-gated so the old idiom can never regrow.

NBC-17..21 born tick-707 at zero the NBM-06 way: the census (the
DA judgment mirrored exactly) measured the closet CLEAN (0
utcnow/utcfromtimestamp faces, 0 use_auth_token kwargs, 0 pydantic
v1 spellings, 0 torch.cuda.amp imports, 0 torch_dtype kwargs across
the same 20 notebooks / 102 code cells), so there was nothing to
drain - the docs-fence modernity epic had already drained the md
universe (ticks 227, 228, 235, 347, 639) while the notebook layer
stayed unmeasured, and the extension locks the convention (the
corpus teaches the 3.12+, transformers-5, pydantic-2 and torch-2.x
surfaces only) - the launcher RUNS these cells, so a deprecated
spelling would warn or crash the learner today.

NBC-22..23 born tick-708 at zero the NBM-06 way: the census (the
SQ judgment mirrored exactly by importing the md gate's own
functions over the same 20 notebooks / 102 code cells) measured
the closet CLEAN (SQ-01=0, SQ-02=0; 101 cells walked, 1
danger-marker skip, and the walk's entry set - execute/
executemany/executescript/read_sql/read_sql_query calls - absent
from the notebook universe entirely), so there was nothing to
drain - the extension locks the convention (bound parameters,
never string-merged queries, for any future notebook teaching
persistence).

NBC-24 born tick-709 at zero the same born-at-zero way: the
census (the CI judgment mirrored exactly by importing the md
gate's own functions over the same 20 notebooks / 102 code
cells) measured the closet CLEAN (CI-01=0, CI-02=0; 101 cells
walked, 1 danger-marker skip; the walk's entry set - run()/
execute_query() calls - present at exactly 3 faces, all NB-701
agent-task .run() calls whose Name targets resolve to
non-JoinedStr values, out of class), so there was nothing to
drain - the extension locks the convention ($parameters bind
values, never schema names, and cannot set path bounds, for
any future notebook teaching graph queries) and completes the
notebook query-injection pair (NBC-22..23 SQL, NBC-24 Cypher).

Hard gate (exit 1 on findings): baseline 0 at birth (tick-691 for
NBC-01..02, tick-702 for NBC-03..11, tick-703 for NBC-12..14,
tick-704 for NBC-15, tick-706 for NBC-16, tick-707 for
NBC-17..21, tick-708 for NBC-22..23, tick-709 for NBC-24).

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


def falsy_const(node: ast.expr) -> bool:
    """True for a constant False/None (TLS verification disabled)."""
    return (isinstance(node, ast.Constant)
            and (node.value is False or node.value is None))


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


def scan_tls(tree: ast.AST, rel: str, idx: int,
             findings: list[str]) -> None:
    """NBC-15 over one parsed cell tree (born tick-704 at zero)."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func,
                                                     ast.Attribute):
            base = (node.func.value.id
                    if isinstance(node.func.value, ast.Name) else None)
            if base == "requests" and node.func.attr in _HTTP_VERBS:
                for kw in node.keywords:
                    if kw.arg == "verify" and falsy_const(kw.value):
                        findings.append(
                            f"{rel}: NBC-15 requests."
                            f"{node.func.attr} with verify="
                            f"{kw.value.value!r} in code cell {idx} - "
                            f"certificate validation is off, so the "
                            f"endpoint's identity claim is unchecked "
                            f"and a man-in-the-middle reads everything "
                            f"the cell sends; keep verify=True or point "
                            f"verify at a real CA bundle")
            elif (base == "ssl" and node.func.attr
                    == "_create_unverified_context"):
                findings.append(
                    f"{rel}: NBC-15 ssl._create_unverified_context() "
                    f"in code cell {idx} - a context that accepts any "
                    f"certificate turns transport encryption into a "
                    f"costume; use ssl.create_default_context()")
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = ([node.target] if isinstance(node, ast.AnnAssign)
                       else node.targets)
            for t in targets:
                if not isinstance(t, ast.Attribute):
                    continue
                if t.attr == "verify" and falsy_const(node.value):
                    findings.append(
                        f"{rel}: NBC-15 .verify set to a falsy "
                        f"constant in code cell {idx} - session-level "
                        f"verification off has the same "
                        f"man-in-the-middle exposure as verify=False "
                        f"on the call; keep verification on")
                elif (t.attr == "verify_mode" and node.value is not None
                        and dotted_name(node.value) == "ssl.CERT_NONE"):
                    findings.append(
                        f"{rel}: NBC-15 verify_mode set to "
                        f"ssl.CERT_NONE in code cell {idx} - the "
                        f"context accepts any certificate chain; "
                        f"CERT_REQUIRED is the default and stays the "
                        f"default")


_TL_TYPE = r"(?:Optional|Union|List|Dict|Tuple|Set|FrozenSet|Type)"
_TL_IMPORT_RE = re.compile(
    rf"^\s*from\s+typing\s+import\s+.*\b{_TL_TYPE}\b")
_TL_BRACKET_RE = re.compile(rf"\b{_TL_TYPE}\[")
_TL_BARE_RE = re.compile(
    rf"(->\s*(?:typing\.)?{_TL_TYPE}\b"
    rf"|:\s*(?:typing\.)?{_TL_TYPE}\b"
    rf"|[(,]\s*(?:typing\.)?{_TL_TYPE}\b"
    rf"|\[\s*(?:typing\.)?{_TL_TYPE}\b"
    rf"|,\s*(?:typing\.)?{_TL_TYPE}\b)")


def scan_typing(src: str, rel: str, idx: int,
                findings: list[str]) -> None:
    """NBC-16 over one cell's joined source, per line (born tick-706
    over the drained corpus; the TL judgment mirrored: the import
    line first so a multi-name import is not double-counted, first
    match wins per line, docstrings and comments NOT exempted - they
    also teach the old idiom)."""
    for ln in src.split("\n"):
        if _TL_IMPORT_RE.search(ln):
            findings.append(
                f"{rel}: NBC-16 legacy typing import in code cell "
                f"{idx} - the import-based generics are deprecated "
                f"since the builtin generics (3.9) and the PEP 604 "
                f"unions (3.10); drop the import and write the "
                f"builtin spellings")
            continue
        if _TL_BRACKET_RE.search(ln):
            findings.append(
                f"{rel}: NBC-16 legacy typing spelling in code "
                f"cell {idx} - {ln.strip()[:60]!r} - write the "
                f"builtin-generic spelling (list[str], "
                f"dict[str, int])")
            continue
        if _TL_BARE_RE.search(ln):
            findings.append(
                f"{rel}: NBC-16 bare legacy generic in code cell "
                f"{idx} - {ln.strip()[:60]!r} - write the bare "
                f"builtin (dict, not the capital-D legacy name)")


_DA_DT_RE = re.compile(
    r"\bdatetime\.utcnow\b|\bdatetime\.utcfromtimestamp\b")
_DA_TOKEN_RE = re.compile(r"\buse_auth_token\s*=")
_DA_V1_RE = re.compile(
    r"@validator\b|@root_validator\b|parse_obj_as\(")
_DA_AMP_RE = re.compile(r"\btorch\.cuda\.amp\b")
_DA_DTYPE_RE = re.compile(r"\btorch_dtype\s*=")
_DA_DICT_RE = re.compile(r"\.dict\(\)")
_PYD_IMPORT_RE = re.compile(
    r"^\s*from pydantic import|\bimport pydantic\b")


def scan_deprecated(src: str, rel: str, idx: int, pyd: bool,
                    findings: list[str]) -> None:
    """NBC-17..21 over one cell's joined source, per line (born
    tick-707 at zero; the DA judgment mirrored: per-line first
    match in rule order, the #-split carve first so a comment
    teaching the deprecation stays invisible, and the .dict()
    face activates only when the notebook imports pydantic)."""
    for ln in src.split("\n"):
        code = ln.split("#", 1)[0]
        if _DA_DT_RE.search(code):
            findings.append(
                f"{rel}: NBC-17 deprecated datetime API in code "
                f"cell {idx} - utcnow/utcfromtimestamp are "
                f"deprecated since 3.12 and return naive "
                f"datetimes; write datetime.now(timezone.utc)")
            continue
        if _DA_TOKEN_RE.search(code):
            findings.append(
                f"{rel}: NBC-18 removed HF kwarg use_auth_token= "
                f"in code cell {idx} - gone in transformers 5.x; "
                f"write token=")
            continue
        if _DA_V1_RE.search(code):
            findings.append(
                f"{rel}: NBC-19 pydantic v1 API in code cell "
                f"{idx} - @validator/@root_validator/"
                f"parse_obj_as deprecated in 2.x, removed in 3; "
                f"write @field_validator or TypeAdapter")
            continue
        if _DA_AMP_RE.search(code):
            findings.append(
                f"{rel}: NBC-20 torch.cuda.amp namespace in code "
                f"cell {idx} - deprecated since PyTorch 2.4; "
                f"use the torch.amp namespace")
            continue
        if _DA_DTYPE_RE.search(code):
            findings.append(
                f"{rel}: NBC-21 transformers torch_dtype kwarg in "
                f"code cell {idx} - deprecated, the stack warns "
                f"on every load; write dtype=")
            continue
        if pyd and _DA_DICT_RE.search(code):
            findings.append(
                f"{rel}: NBC-19 pydantic v1 serialization in code "
                f"cell {idx} - .dict() deprecated in 2.x, removed "
                f"in 3; write model_dump()")


# The SQL-interpolation twins (born tick-708), mirrored from
# sql_interp_scan (SQ-01/SQ-02): _SQ_EXEC_ATTRS is the walk's
# entry set (run/execute_query belong to cypher_interp_scan,
# disjoint by attr, single ownership by construction),
# _SQ_KEYWORD_RE the vocabulary gate, _SQ_PLACEHOLDER_RE the
# binding carve.
_SQ_EXEC_ATTRS = frozenset({
    "execute", "executemany", "executescript",
    "read_sql", "read_sql_query"})
_SQ_KEYWORD_RE = re.compile(
    r"\b(select|insert|update|delete|create|drop|alter|from|where|into"
    r"|values|order\s+by|group\s+by)\b", re.IGNORECASE)
_SQ_PLACEHOLDER_RE = re.compile(r"%s|\?")


def _has_sql(text: str) -> bool:
    return bool(_SQ_KEYWORD_RE.search(text))


def _constant_leaves(node: ast.expr) -> list[str]:
    """Every string-Constant leaf of an expression tree (Add chains
    included)."""
    out: list[str] = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            out.append(n.value)
    return out


def _is_add_chain(node: ast.expr) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add)


def _joinedstr_leaves(node: ast.expr) -> list[ast.JoinedStr]:
    return [n for n in ast.walk(node) if isinstance(n, ast.JoinedStr)]


def _is_percent_format(node: ast.expr) -> bool:
    return isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod)


def _is_format_call(node: ast.expr) -> bool:
    return (isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "format")


def _classify(expr: ast.expr) -> str | None:
    """NBC code for a resolved query expression, or None when out of
    class. NBC-22 wins: an f-string in the chain is the loudest form
    (the SQ-01 judgment; SQ-02 maps to NBC-23)."""
    for js in _joinedstr_leaves(expr):
        if any(_has_sql(p) for p in _constant_leaves(js)):
            return "NBC-22"
    if _is_percent_format(expr) or _is_format_call(expr):
        if any(_has_sql(p) for p in _constant_leaves(expr)):
            return "NBC-23"
    if _is_add_chain(expr):
        leaves = _constant_leaves(expr)
        has_placeholder = any(_SQ_PLACEHOLDER_RE.search(p) for p in leaves)
        has_dynamic = any(not isinstance(n, ast.Constant)
                          for n in ast.walk(expr)
                          if isinstance(n, (ast.Name, ast.Call,
                                            ast.JoinedStr,
                                            ast.FormattedValue)))
        if not has_placeholder and has_dynamic \
                and any(_has_sql(p) for p in leaves):
            return "NBC-23"
    return None


def _collect_assigns(body: list[ast.stmt],
                     out: list[tuple[int, str, ast.expr]]) -> None:
    """``name = <expr>`` and ``name += <expr>`` assignments from a
    statement list, recursing into compound statements but NOT into
    functions/classes (those own their scopes)."""
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif (isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None):
            out.append((node.lineno, node.target.id, node.value))
        elif isinstance(node, ast.AugAssign) \
                and isinstance(node.target, ast.Name):
            out.append((node.lineno, node.target.id, node.value))
        for child in ast.iter_child_nodes(node):
            _collect_assigns([child], out)


def _func_assigns(func: ast.AST) -> list[tuple[int, str, ast.expr]]:
    out: list[tuple[int, str, ast.expr]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif (isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None):
            out.append((node.lineno, node.target.id, node.value))
        elif isinstance(node, ast.AugAssign) \
                and isinstance(node.target, ast.Name):
            out.append((node.lineno, node.target.id, node.value))
    return sorted(out, key=lambda t: t[0])


def _builder_chain(
        name: str, line: int,
        assigns: list[tuple[int, str, ast.expr]],
) -> ast.expr | None:
    """Resolve a query variable backwards through its same-name
    assignment history (nearest PRECEDING first, then earlier
    fragments while the value is an Add chain) - a builder that
    grows SQL across several ``query +=`` fragments is not judged
    by its last fragment alone."""
    history = sorted(((ln, v) for ln, an, v in assigns
                      if an == name and ln < line), key=lambda t: t[0])
    if not history:
        return None
    parts: list[ast.expr] = [history[-1][1]]
    for _, v in reversed(history[:-1]):
        if _is_add_chain(v) or isinstance(v, ast.Constant):
            parts.append(v)
        else:
            break
    node = parts[0]
    for p in parts[1:]:
        node = ast.BinOp(left=node, op=ast.Add(), right=p)
    return node


def scan_sqlinterp(src: str, tree: ast.AST, rel: str, idx: int,
                   findings: list[str]) -> None:
    """NBC-22..23 over one parsed cell tree (born tick-708 at zero;
    the sql_interp_scan SQ-01/SQ-02 judgment mirrored per cell:
    the danger-marker escape first, Constant queries and the
    placeholder-bound forms carved, one-hop query-variable
    resolution with the += fragment chain, and one finding per
    execution call)."""
    if _DANGER_RE.search(src):
        return
    assigns: list[tuple[int, str, ast.expr]] = []
    _collect_assigns(tree.body, assigns)
    calls: list[tuple[ast.Call, ast.AST | None]] = []

    class _Collector(ast.NodeVisitor):
        def __init__(self) -> None:
            self.func_stack: list[ast.AST] = []

        def visit_FunctionDef(self, node) -> None:  # type: ignore[override]
            self.func_stack.append(node)
            self.generic_visit(node)
            self.func_stack.pop()

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Attribute) \
                    and node.func.attr in _SQ_EXEC_ATTRS and node.args:
                calls.append((node, self.func_stack[-1]
                              if self.func_stack else None))
            self.generic_visit(node)

    _Collector().visit(tree)
    for call, func in calls:
        arg0 = call.args[0]
        code: str | None = None
        if not isinstance(arg0, ast.Constant):
            if _classify(arg0) is not None:
                code = _classify(arg0)
            elif isinstance(arg0, ast.Name):
                scope_assigns = (_func_assigns(func) if func is not None
                                 else assigns)
                value = _builder_chain(arg0.id, call.lineno, scope_assigns)
                if value is None and func is not None:
                    value = _builder_chain(arg0.id, call.lineno, assigns)
                if value is not None:
                    code = _classify(value)
        if code is None:
            continue  # Constant query / placeholder idiom / non-SQL
        verb = call.func.attr
        findings.append(
            f"{rel}: {code} SQL interpolated into {verb}() in code "
            f"cell {idx} - the value is merged into the query text "
            f"client-side, before the driver sees it, so no "
            f"placeholder can bind it (a value containing a quote "
            f"closes the literal and the rest executes as SQL); bind "
            f"values instead: a Constant query with %s/? placeholders "
            f"plus a params second argument, or the builder idiom "
            f"(query += \" AND x <= %s\"; params.append(v); "
            f"execute(query, params))")
        # one finding per execution call


# The Cypher-interpolation twin (born tick-709), mirrored from
# cypher_interp_scan (CI-01/CI-02): _CI_RUN_ATTRS is the walk's
# entry set (execute/executemany/executescript/read_sql/
# read_sql_query belong to the SQL twin above, disjoint by attr,
# single ownership by construction); a literal part ending at ":"
# arms a label/rel-type position (CI-01), at ".."/"*" a
# variable-length path bound (CI-02). The resolution helpers
# carry the _ci_ prefix because the SQL twin above owns the
# +=-fragment names (the CI judgment has no AugAssign branch -
# a += fragment is not a fresh query).
_CI_RUN_ATTRS = frozenset({"run", "execute_query"})


def _ci_collect_assigns(
        body: list[ast.stmt],
        out: list[tuple[int, str, ast.expr]]) -> None:
    """``name = <expr>`` assignments from a statement list,
    recursing into compound statements but NOT into
    functions/classes (those own their scopes) - the CI twin's
    face: Assign/AnnAssign only, no AugAssign branch."""
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif (isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None):
            out.append((node.lineno, node.target.id, node.value))
        for child in ast.iter_child_nodes(node):
            _ci_collect_assigns([child], out)


class _CallCollector(ast.NodeVisitor):
    """Collect run()/execute_query() calls together with their
    enclosing function (for per-function-scope one-hop
    resolution)."""

    def __init__(self) -> None:
        self.calls: list[tuple[ast.Call, ast.AST | None]] = []
        self.func_stack: list[ast.AST] = []

    def visit_FunctionDef(self, node) -> None:  # type: ignore[override]
        self.func_stack.append(node)
        self.generic_visit(node)
        self.func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) \
                and node.func.attr in _CI_RUN_ATTRS and node.args:
            self.calls.append((node, self.func_stack[-1]
                              if self.func_stack else None))
        self.generic_visit(node)


def _ci_func_assigns(
        func: ast.AST) -> list[tuple[int, str, ast.expr]]:
    out: list[tuple[int, str, ast.expr]] = []
    for node in ast.walk(func):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 \
                and isinstance(node.targets[0], ast.Name):
            out.append((node.lineno, node.targets[0].id, node.value))
        elif (isinstance(node, ast.AnnAssign)
                and isinstance(node.target, ast.Name)
                and node.value is not None):
            out.append((node.lineno, node.target.id, node.value))
    return sorted(out, key=lambda t: t[0])


def _ci_nearest_assign(
        name: str, line: int,
        scope_assigns: list[tuple[int, str, ast.expr]],
) -> ast.expr | None:
    """Nearest PRECEDING assignment of ``name`` in the scope (the
    per-function scope is the twin's tick-649 design lesson - a
    flat per-fence dict let a second assignment overwrite the
    first and hide a site)."""
    best: ast.expr | None = None
    best_line = -1
    for lineno, aname, value in scope_assigns:
        if aname == name and best_line < lineno < line:
            best, best_line = value, lineno
    return best


def _is_cast_shaped(node: ast.expr) -> bool:
    """The 6304 mitigation shape: ``int(x)`` or ``max(1, int(x))``
    - a value that cannot smuggle Cypher metacharacters or
    unbounded hops."""
    if isinstance(node, ast.Call) and isinstance(node.func,
                                                 ast.Name):
        if node.func.id == "int":
            return True
        if node.func.id in ("max", "min"):
            return any(_is_cast_shaped(a) for a in node.args)
    return False


def _has_membership_guard(scope: ast.AST | None,
                          name: str) -> bool:
    """True if the enclosing scope tests ``name`` against a
    container (``if label not in ALLOWED_LABELS:``) - the
    allowlist idiom for a position no $parameter can fill."""
    if scope is None:
        return False
    for node in ast.walk(scope):
        if isinstance(node, ast.Compare) and any(
                isinstance(op, (ast.In, ast.NotIn))
                for op in node.ops):
            for operand in [node.left, *node.comparators]:
                if isinstance(operand, ast.Name) \
                        and operand.id == name:
                    return True
    return False


def _position_interpolants(js: ast.JoinedStr,
                           want: str) -> list[ast.expr]:
    """FormattedValues immediately following a literal part ending
    with the class marker: ``:`` for label/rel-type positions,
    ``..``/``*`` for variable-length path bounds."""
    out: list[ast.expr] = []
    armed = False
    for v in js.values:
        if isinstance(v, ast.Constant) and isinstance(v.value, str):
            if want == ":":
                armed = v.value.endswith(":")
            else:
                armed = (v.value.endswith("..")
                         or v.value.endswith("*"))
        elif isinstance(v, ast.FormattedValue) and armed:
            out.append(v.value)
            armed = False
    return out


def scan_cypherinterp(src: str, tree: ast.AST, rel: str, idx: int,
                      findings: list[str]) -> None:
    """NBC-24 over one parsed cell tree (born tick-709 at zero; the
    cypher_interp_scan CI-01/CI-02 judgment mirrored per cell: the
    danger-marker escape first, the ":" / ".." / "*" position
    arming on the query's literal parts, the int-cast and
    allowlist-guard escapes, one-hop Name resolution, and one
    finding per execution call)."""
    if _DANGER_RE.search(src):
        return
    assigns: list[tuple[int, str, ast.expr]] = []
    _ci_collect_assigns(tree.body, assigns)
    collector = _CallCollector()
    collector.visit(tree)
    for call, func in collector.calls:
        target = call.args[0]
        js: ast.JoinedStr | None = None
        if isinstance(target, ast.JoinedStr):
            js = target
        elif isinstance(target, ast.Name):
            scope_assigns = (_ci_func_assigns(func)
                             if func is not None else assigns)
            value = _ci_nearest_assign(target.id, call.lineno,
                                       scope_assigns)
            if value is None and func is not None:
                value = _ci_nearest_assign(target.id, call.lineno,
                                           assigns)
            if isinstance(value, ast.JoinedStr):
                js = value
        if js is None:
            continue  # Constant = the parameterized affirmative form
        str_parts = [v.value for v in js.values
                     if isinstance(v, ast.Constant)
                     and isinstance(v.value, str)]
        if any(p.endswith(":") for p in str_parts):
            want, code = ":", "CI-01"
        elif any(p.endswith("..") or p.endswith("*")
                 for p in str_parts):
            want, code = "..", "CI-02"
        else:
            continue
        scope: ast.AST | None = func
        scope_assigns = (_ci_func_assigns(func)
                         if func is not None else assigns)
        for interp in _position_interpolants(js, want):
            if code == "CI-01":
                if _is_cast_shaped(interp):
                    continue
                if isinstance(interp, ast.Name) \
                        and _has_membership_guard(scope, interp.id):
                    continue
                kind = ("label/rel-type position interpolation "
                        "without an allowlist guard")
            else:
                if _is_cast_shaped(interp):
                    continue
                if isinstance(interp, ast.Name):
                    value = _ci_nearest_assign(
                        interp.id, call.lineno, scope_assigns)
                    if value is None and func is not None:
                        value = _ci_nearest_assign(
                            interp.id, call.lineno, assigns)
                    if value is not None \
                            and _is_cast_shaped(value):
                        continue
                kind = ("variable-length path-bound "
                        "interpolation without the int-cast")
            remedy = ("an allowlist membership guard"
                      if code == "CI-01" else
                      "the int-cast (hop_bound = max(1, int(x)))")
            verb = call.func.attr
            findings.append(
                f"{rel}: NBC-24 Cypher {kind} in {verb}() in "
                f"code cell {idx} - $parameters cannot fill this "
                f"position (6301: values are bound with "
                f"$parameters, never interpolated into the "
                f"string; 6304: parameters cannot set "
                f"variable-length path bounds), so the "
                f"interpolated value reaches the query engine "
                f"raw; guard it with {remedy}, the corpus-taught "
                f"idiom")
            break  # one finding per execution call

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
    _pyd = any(
        _PYD_IMPORT_RE.search(cell_source(c))
        for c in nb["cells"]
        if isinstance(c, dict) and c.get("cell_type") == "code")
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
        scan_tls(tree, rel, idx, findings)
        scan_typing(src, rel, idx, findings)
        scan_deprecated(src, rel, idx, _pyd, findings)
        scan_sqlinterp(src, tree, rel, idx, findings)
        scan_cypherinterp(src, tree, rel, idx, findings)
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
          f"/ NBC-03..24 the md twins: bare-broad except, "
          f"unsafe deserialize, eval-exec, empty mutable default, "
          f"shell-out, mktemp, trust_remote_code, open-no-encoding, "
          f"requests-no-timeout, insecure-tls, secret-shape literals, "
          f"random-for-security, weak-hash-security, legacy-typing, "
          f"deprecated-API, sql-interpolation, cypher-interpolation; "
          f"{stats[4]} import(s) accepted, {stats[3]} relative skipped, "
          f"{stats[2]} cell(s) left to NBH-03) across {stats[0]} "
          f"notebooks / {stats[1]} code cells in docs/notebooks/ "
          f"(hard; born tick-691 at zero - 2 real syntax defects "
          f"drained, 4 unresolvable roots corpus-classified; NBC-03..11 "
          f"born tick-702 at zero - the md unsafe family's declared "
          f"blind spot closed, 4 real teaching-code defects drained "
          f"in-tick; NBC-12..14 born tick-703 at zero - the "
          f"secret/crypto twins closed, the census clean; "
          f"NBC-15 born tick-704 at zero - the TLS-off face "
          f"closed, the census clean; NBC-16 born tick-706 over the "
          f"drained corpus - the md typing gate's declared blind "
          f"spot closed, 24 real legacy spellings drained in-tick; "
          f"NBC-17..21 born tick-707 at zero - the md deprecation "
          f"gate's declared blind spot closed, the census clean; "
          f"NBC-22..23 born tick-708 at zero - the md SQL-"
          f"interpolation gate's declared blind spot closed, the "
          f"census clean; NBC-24 born tick-709 at zero - the md "
          f"Cypher-interpolation gate's declared blind spot "
          f"closed, the census clean, the query-injection pair "
          f"complete)")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
