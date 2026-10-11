---
Document ID: CHEAT-SHEET-032
Title: "CHEAT-SHEET-032: Code Interpreter Sandbox"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Advanced
Tags: ['cheatsheet', 'agents', 'tool-calling', 'code-interpreter']
---

# CHEAT-SHEET-032: Code Interpreter Sandbox

**Quick Reference for:** the four-tier sandbox ladder - process, container, in-process, managed microVM - and the rule that picks between them, the resource limits that belong to the child and never to your own process, the regex screen over real import lines, the normalised `ok`/`failed`/`blocked` envelope, and the telemetry that catches runaway agents. CHEAT-SHEET-027 owns the tool-calling round trip and the MCP contract; CHEAT-SHEET-026 owns the security trio; CHEAT-SHEET-029 owns the training surface that makes calls valid in the first place; this sheet owns what happens after the model emits code - executing it without letting the worst thing it could write happen. The closing rule: every generated line is adversarial until the sandbox says otherwise, and the isolation level must match the blast radius of that worst code, not the code you expect.

## The Ladder: Four Tiers

| tier | isolation boundary | typical latency | reach for it when |
|---|---|---|---|
| process | `subprocess [python, -I, -c code]` | ~50 ms | untrusted logic, no third-party packages |
| container | `docker run --network none --read-only` | ~1 s | scientific stack in a team-standard image |
| in-process | `RestrictedPython compile_restricted` | microseconds | high-frequency tool calls inside one service |
| microVM | E2B `Sandbox()` (Firecracker) | ~150 ms + network | production agents without self-managed infra |

Latency is the price of trust: each rung adds isolation boundary - OS process, namespaces and cgroups, bytecode guards, hardware virtualization - and each boundary costs startup time and infrastructure. **Pick the weakest tier that contains your actual threat model.** The risk list every tier must scope: infinite loops, excessive resource usage, file-system access, network calls, malicious imports.

```text
process    subprocess -I        ~50 ms      untrusted logic, no 3rd-party pkgs
container  docker run           ~1 s        scientific stack, team-standard image
in-process RestrictedPython     us          high-frequency calls, one service
microVM    E2B (Firecracker)    ~150 ms     production, no self-managed infra
```

## Process Tier: Blast Radius Without Capability Restriction

A fresh OS process per execution: `subprocess.run([sys.executable, "-I", "-c", code], timeout=...)`. The `-I` isolated mode drops user site-packages, environment variables and current-directory imports; the parent's timeout is the wall clock - `execute('print(2 + 2)')` returns `'4\n'`, `execute('while True: pass')` is killed at the 2-second timeout. The honest limitation: **process isolation limits the blast radius but removes no capabilities** - the child can still `import os`. Keeping capabilities away entirely is the container and in-process tiers' job.

## Container Tier: the read_only Trap

Docker adds namespaces, cgroups, `mem_limit="128m"`, `cpus=0.5`, `network_disabled=True`, `read_only=True` - and the canonical pitfall: **a read-write host bind mount silently defeats `read_only=True`**. Mount scratch space as `tmpfs={"/tmp": "rw,size=64m"}` (kernel memory that disappears with the container) instead of bind-mounting a host directory read-write. On timeout the parent kills the container outright - no zombie children, no leaked interpreter state.

## In-Process Tier: Two Layers Before Any Code Runs

| layer | guard | what dies |
|---|---|---|
| compile-time | names starting with `_` rejected at the AST rewrite | `__import__('os').getcwd()` never compiles |
| runtime | builtins allowlist has no `__import__` | `import os` -> `ImportError: __import__ not found` |
| runtime | `safer_getattr` blocks dunder reach-through | `obj.__globals__` attribute access refused |

`compile_restricted` rewrites the AST and rejects underscore-prefixed names before execution; the runtime allowlist then refuses imports and dunder traversal independently. `safe_builtins` ships **81 names, deliberately minimal** - no `sum`, no `min`, no `list` - so extend it explicitly per tool (`{"print", "sum", "min", "max", "list", "dict", "enumerate"}`). The demo: `print('hello')` plus `result = sum(range(10))` returns `{'result': 45, 'printed': 'hello\n'}`. In-process means microseconds per call - the tier for high-frequency tool calls - but `SIGALRM` wall-clock enforcement is POSIX-only, so Windows relies on a process-level tier for timeouts.

## Limits Belong to the Child

`resource.setrlimit` applied in the calling process **never restores** - an in-process call would throttle the application itself and cap every later execution. The correct Unix pattern binds limits **between fork and exec** via `preexec_fn`, so only the child inherits: `RLIMIT_AS` turns runaway allocation into the child's `MemoryError`, `RLIMIT_CPU` kills a compute-bound child. Both are POSIX-only - on Windows the same request reports `resource limits require a POSIX OS` - and the parent's `subprocess` timeout remains the portable wall clock, because **Python cannot kill a thread portably** and `SIGALRM` does not exist on Windows.

## Screen, Execute, Envelope

The agent pipeline has three stages - static screening (cheap, first), restricted execution (the most restrictive sandbox that fits), and a **normalised envelope** (`ok` / `failed` / `blocked`) the model can always parse. Screening matches the regex `^\s*(?:import|from)\s+([\w.]+)` with `MULTILINE` over **real import statements only**, against `BLOCKED_MODULES = frozenset({"os", "sys", "subprocess", "shutil", "socket", "pickle"})`:

- `text = 'position of the sun'` plus `result = len(text)` -> `[]`, status `ok`, result `19` - `'position'` contains `'os'`, and that is exactly why a **substring check would false-positive**; only import lines are screened.
- `import os` -> `['os']`, status `blocked`.
- `x = 1; import os` -> the regex sees nothing - the line starts with `x`. **The boundary is the sandbox, not the regex**: semicolon-hidden and dynamic imports slip the first pass, and serious static analysis walks the AST with the `ast` module.

| status | when | shape |
|---|---|---|
| `ok` | the code ran and returned | `{'status': 'ok', 'result': 19}` |
| `blocked` | screening refused a module | `{'status': 'blocked', 'blocked': ['os']}` |
| `failed` | the code ran and raised | `{'status': 'failed', 'error': 'division by zero'}` |

Rejection is **loud** - a status the model reads and adapts to - never a silent comment-out.

## The Jupyter Tier

A Jupyter kernel is a separate child process with the full scientific stack - pandas, numpy, preinstalled on E2B's Firecracker microVMs. Two protocol traps: the manager and client live in **`jupyter_client`, not `IPython.kernel`**, and **output rides the IOPUB channel** - the shell channel only carries the `execute_reply` ack, so a second `get_shell_msg()` blocks forever; collect IOPUB messages until `msg['header']['msg_type'] == 'status'` and `content['execution_state'] == 'idle'`, streaming `stream` and `execute_result` along the way. The tier's real feature: **kernel state persists between executes** - variables, models and DataFrames survive across tool calls, so one session doubles as the agent's scratch memory.

## Monitoring

Wrap any envelope-speaking sandbox in a monitor that records duration (`perf_counter`), success, and memory (`tracemalloc` peak) per execution. `tracemalloc` traces **this process only** - meaningful for the in-process tier, near zero for process/container/microVM children whose memory lives outside the interpreter (Linux reads child peak via `resource.getrusage(RUSAGE_CHILDREN).ru_maxrss`). Two monitored executions - `sum(range(1000))` ok, `1/0` failed - land `total=2 success_rate=0.5`; ship **duration and success rate per session**, the two numbers that catch runaway agents first, as first-class regression metrics.

## Known Failure Modes

| failure | lesson |
|---|---|
| Pick isolation by convenience | the ladder rule: match the worst code's blast radius, not the code you expect |
| Bind limits in-process | `setrlimit` never restores - `preexec_fn` binds the child only |
| Enforce timeouts with a thread | Python cannot kill threads portably - parent-enforced child timeout |
| Screen with a substring match | `'position'` contains `'os'` - regex over real import lines |
| Trust the regex as the boundary | semicolon and dynamic imports slip past - the sandbox itself is the boundary |

## References

- Repository, *Module 7202: Code Interpreter - Sandbox Execution for Agent Code Testing*
- Zope Foundation, *RestrictedPython* - the compile-time and runtime guard layers
- E2B, *Code Interpreter SDK* - Firecracker microVM sandboxes for agents
- Jupyter, *jupyter_client* - kernel manager, client, and the IOPUB channel

## Troubleshooting

| symptom | cause | fix |
|---|---|---|
| Sandbox escape via `__import__` | in-process tier without compile-time guards | underscore rejection plus the builtins allowlist - two independent layers |
| `'position'` blocked as `'os'` | substring screening | regex over real import statements only |
| The app slows after limits are set | `setrlimit` called in-process | move limits to `preexec_fn` so only the child inherits them |
| Notebook output never arrives | reading the shell channel | output rides IOPUB; collect until `status: idle` |
| `read_only` silently bypassed | read-write host bind mount | mount scratch as `tmpfs`, not a host bind |
| Memory telemetry reads zero | `tracemalloc` on a subprocess tier | in-process only - `RUSAGE_CHILDREN.ru_maxrss` on Linux |

## Quick Reference for

| target | role on this surface |
|---|---|
| [Module 7202: Code Interpreter](../../phases/phase7-agentic/7200-tools/guides/7202-Code-Interpreter.md) | this sheet's source module - the full four-sandbox walkthrough with runnable code |
| [Module 7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md) | the round trip that hands the model's code to an executor like this |
| [CHEAT-SHEET-027: Tool Calling and MCP](CHEAT-SHEET-027-Tool-Calling-and-MCP.md) | the tool-layer contract - transport, validation gate, result triple |
| [CHEAT-SHEET-026: Agent Security](CHEAT-SHEET-026-Agent-Security.md) | the security trio - stripped builtins, deny-by-default permissions, input validation |

```python
"""CHEAT-SHEET-032 fence: the sandbox execution ladder for agent-written code.

Stdlib only. The process tier runs real child interpreters (-I, parent
timeout); the screening regex, the envelope normaliser and the monitor run
for real; the container, in-process (RestrictedPython), resource-limit and
Jupyter canons are recorded as ledgers from the source module's runs because
those tiers need docker / restrictedpython / jupyter_client packages.
"""
import re
import subprocess
import sys
import time
import tracemalloc

sys.stdout.reconfigure(encoding="utf-8")

# --- F1: the isolation ladder (recorded) -------------------------------------
print("F1  isolation ladder: four tiers - latency is the price of trust")
ladder = [
    ("process", "subprocess [python, -I, -c code]", "~50 ms",
     "untrusted logic, no third-party packages"),
    ("container", "docker run --network none --read-only", "~1 s",
     "scientific stack in a team-standard image"),
    ("in-process", "RestrictedPython compile_restricted", "microseconds",
     "high-frequency tool calls inside one service"),
    ("microVM", "E2B Sandbox (Firecracker)", "~150 ms + network",
     "production agents without self-managed infra"),
]
for tier, boundary, latency, when in ladder:
    print(f"{tier:11s} | {boundary:39s} | {latency:18s} | {when}")
print("rule: pick the weakest tier that contains your threat model - scope:")
print("infinite loops, resource burn, fs access, network calls, imports")

# --- F2: the process tier, for real -------------------------------------------
print("F2  process tier: fresh interpreter [python, -I, -c] + parent timeout")
r_ok = subprocess.run([sys.executable, "-I", "-c", "print(2 + 2)"],
                      capture_output=True, text=True, timeout=30)
print("execute('print(2 + 2)') ->", repr(r_ok.stdout))
try:
    subprocess.run([sys.executable, "-I", "-c", "while True: pass"],
                   capture_output=True, timeout=2)
    print("BUG: the infinite loop survived the parent timeout")
except subprocess.TimeoutExpired:
    print("execute('while True: pass') -> killed by the 2s parent timeout")
print("-I drops user site-packages, env vars and cwd imports; the process")
print("limits the blast radius, but the child can still import os -")
print("capability restriction is the container / in-process tier's job")

# --- F3: the in-process tier's two layers (recorded) --------------------------
print("F3  in-process tier: RestrictedPython guards in two layers")
print("compile-time | '_'-names die at the AST rewrite: "
      "__import__('os') never compiles")
print("runtime      | builtins allowlist has no __import__: "
      "import os -> ImportError: __import__ not found")
print("runtime      | safer_getattr blocks dunder reach-through: "
      "obj.__globals__ refused")
print("safe_builtins ships 81 names, deliberately minimal (no sum/min/list)")
print("extend explicitly; demo -> {'result': 45, 'printed': 'hello\\n'}")

# --- F4: limits belong to the child -------------------------------------------
print("F4  resource limits: setrlimit in-process NEVER restores - bind the child")
print("wrong: resource.setrlimit in your own process caps the app itself")
print("right: preexec_fn runs between fork and exec - only the child inherits")
print("RLIMIT_AS -> MemoryError in the child; RLIMIT_CPU kills compute-bound;")
print("POSIX only ('resource limits require a POSIX OS' on Windows); threads")
print("cannot be killed portably - the parent timeout stays the wall clock")

# --- F5: static screening, for real -------------------------------------------
print("F5  screening: regex over REAL import lines, loud rejection")
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.MULTILINE)
BLOCKED_MODULES = frozenset(
    {"os", "sys", "subprocess", "shutil", "socket", "pickle"})


def screen(code):
    roots = {m.group(1).split(".")[0] for m in IMPORT_RE.finditer(code)}
    return sorted(roots & BLOCKED_MODULES)


benign = "text = 'position of the sun'\nresult = len(text)"
evil = "import os\nresult = os.getcwd()"
sneaky = "x = 1; import os"
print("benign ->", screen(benign), "| ok, result 19 - 'position' holds 'os',")
print("          only real import lines are screened")
print("evil   ->", screen(evil), "| blocked ['os']")
print("sneaky ->", screen(sneaky), "| regex blind, the line starts with 'x';")
print("the boundary is the sandbox, not the regex - deep checks walk the AST")

# --- F6: the normalised envelope ----------------------------------------------
print("F6  envelope: one schema the model can always parse")


def envelope(fn, code=""):
    blocked = screen(code)
    if blocked:
        return {"status": "blocked", "blocked": blocked}
    try:
        return {"status": "ok", "result": fn()}
    except Exception as exc:
        return {"status": "failed", "error": str(exc)}


print("ok      :", envelope(lambda: len("position of the sun"), benign))
print("blocked :", envelope(lambda: None, evil))
print("failed  :", envelope(lambda: 1 / 0))
print("three stages: screen -> most restrictive sandbox -> envelope; rejection")
print("is loud (a status the model reads), never a silent comment-out")

# --- F7: the Jupyter kernel tier (recorded protocol facts) --------------------
print("F7  jupyter kernel tier: the full scientific stack in a child process")
print("manager + client live in jupyter_client, NOT IPython.kernel; output")
print("rides the IOPUB channel - the shell channel only carries the ack, so")
print("a second get_shell_msg() blocks forever; collect IOPUB until idle;")
print("kernel state persists across executes: variables, models, DataFrames")
print("survive - one session doubles as the agent's scratch memory")

# --- F8: monitoring, for real --------------------------------------------------
print("F8  monitoring: wrap any envelope-speaking sandbox")
tracemalloc.start()
MON = []


def monitored(fn):
    t0 = time.perf_counter()
    env = fn()
    MON.append((time.perf_counter() - t0, env["status"]))
    return env


e1 = monitored(lambda: {"status": "ok", "result": sum(range(1000))})
e2 = monitored(lambda: envelope(lambda: 1 / 0))
_, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()
print(e1)
print(e2)
n = len(MON)
ok_n = sum(1 for _, status in MON if status == "ok")
print(f"total={n} success_rate={ok_n / n:.1f} "
      f"tracemalloc_peak={peak / 1024:.0f}KB")
print("tracemalloc watches THIS process only - child tiers read near zero;")
print("Linux child peak: resource.getrusage(RUSAGE_CHILDREN).ru_maxrss")
print("ship duration + success rate per session: they catch runaways first")
```

```text
F1  isolation ladder: four tiers - latency is the price of trust
process     | subprocess [python, -I, -c code]        | ~50 ms             | untrusted logic, no third-party packages
container   | docker run --network none --read-only   | ~1 s               | scientific stack in a team-standard image
in-process  | RestrictedPython compile_restricted     | microseconds       | high-frequency tool calls inside one service
microVM     | E2B Sandbox (Firecracker)               | ~150 ms + network  | production agents without self-managed infra
rule: pick the weakest tier that contains your threat model - scope:
infinite loops, resource burn, fs access, network calls, imports
F2  process tier: fresh interpreter [python, -I, -c] + parent timeout
execute('print(2 + 2)') -> '4\n'
execute('while True: pass') -> killed by the 2s parent timeout
-I drops user site-packages, env vars and cwd imports; the process
limits the blast radius, but the child can still import os -
capability restriction is the container / in-process tier's job
F3  in-process tier: RestrictedPython guards in two layers
compile-time | '_'-names die at the AST rewrite: __import__('os') never compiles
runtime      | builtins allowlist has no __import__: import os -> ImportError: __import__ not found
runtime      | safer_getattr blocks dunder reach-through: obj.__globals__ refused
safe_builtins ships 81 names, deliberately minimal (no sum/min/list)
extend explicitly; demo -> {'result': 45, 'printed': 'hello\n'}
F4  resource limits: setrlimit in-process NEVER restores - bind the child
wrong: resource.setrlimit in your own process caps the app itself
right: preexec_fn runs between fork and exec - only the child inherits
RLIMIT_AS -> MemoryError in the child; RLIMIT_CPU kills compute-bound;
POSIX only ('resource limits require a POSIX OS' on Windows); threads
cannot be killed portably - the parent timeout stays the wall clock
F5  screening: regex over REAL import lines, loud rejection
benign -> [] | ok, result 19 - 'position' holds 'os',
          only real import lines are screened
evil   -> ['os'] | blocked ['os']
sneaky -> [] | regex blind, the line starts with 'x';
the boundary is the sandbox, not the regex - deep checks walk the AST
F6  envelope: one schema the model can always parse
ok      : {'status': 'ok', 'result': 19}
blocked : {'status': 'blocked', 'blocked': ['os']}
failed  : {'status': 'failed', 'error': 'division by zero'}
three stages: screen -> most restrictive sandbox -> envelope; rejection
is loud (a status the model reads), never a silent comment-out
F7  jupyter kernel tier: the full scientific stack in a child process
manager + client live in jupyter_client, NOT IPython.kernel; output
rides the IOPUB channel - the shell channel only carries the ack, so
a second get_shell_msg() blocks forever; collect IOPUB until idle;
kernel state persists across executes: variables, models, DataFrames
survive - one session doubles as the agent's scratch memory
F8  monitoring: wrap any envelope-speaking sandbox
{'status': 'ok', 'result': 499500}
{'status': 'failed', 'error': 'division by zero'}
total=2 success_rate=0.5 tracemalloc_peak=1KB
tracemalloc watches THIS process only - child tiers read near zero;
Linux child peak: resource.getrusage(RUSAGE_CHILDREN).ru_maxrss
ship duration + success rate per session: they catch runaways first
```
