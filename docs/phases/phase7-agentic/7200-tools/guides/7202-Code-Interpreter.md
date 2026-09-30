---
Document ID: 7202
Title: "7202: Code Interpreter - Sandbox Execution for Agent Code Testing"
Last Updated: 2026-09-30
Status: Complete
Difficulty: Advanced
Estimated Time: 5 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'tool-calling', 'code-interpreter']
---

# 7202: Code Interpreter - Sandbox Execution for Agent Code Testing

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Sandbox Architecture](#sandbox-architecture)
- [Resource Management](#resource-management)
- [Safe Execution for Agents](#safe-execution-for-agents)
- [Monitoring and Logging](#monitoring-and-logging)
- [Summary](#summary)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Compare the four sandbox tiers (process isolation, container, in-process bytecode restriction, managed microVM) and select the right tier for a given threat model and latency budget
- Implement CPU, memory, and wall-clock limits that bind to a child process rather than the host application, and explain why in-process limits fail
- Screen agent-generated code for dangerous imports and execute it behind deny-by-default guards, returning a normalised result envelope to the model
- Instrument a sandbox with duration, peak-memory, and success-rate telemetry, and aggregate execution statistics for observability

---

## Abstract
A safe Python interpreter lets agents execute code in a sandboxed environment, so malicious or erroneous code cannot reach the host system. This lesson builds the standard isolation ladder - from a plain child-process sandbox you can run anywhere, through Docker containers and in-process bytecode restriction, up to managed microVM platforms - and wires the strongest Python-level tier into an agent execution pipeline with import screening, resource limits, and execution telemetry.

Install the libraries used in this lesson:

```bash
uv pip install restrictedpython docker jupyter-client ipykernel
uv pip install e2b-code-interpreter   # optional, managed microVM tier
```

## Sandbox Architecture

### Why Sandboxing?
```text
Agent-generated code risks:
  - Infinite loops
  - Excessive resource usage
  - File system access
  - Network calls
  - System calls
  - Malicious imports

Sandbox provides:
  - Isolated execution environment
  - Resource limits
  - Restricted imports
  - Timeouts
  - Memory limits
```

### Sandbox Options

The options below form an isolation ladder. Stronger isolation costs more
latency and infrastructure; pick the weakest tier that contains your actual
threat model.

| Tier | Isolation boundary | Typical latency | Reach for it when |
|------|--------------------|-----------------|-------------------|
| Process (`subprocess`) | OS process, fresh interpreter | ~50 ms | Untrusted logic, no third-party packages needed |
| Container (Docker) | Namespaces + cgroups | ~1 s | Scientific stack, team-standard environment |
| In-process (RestrictedPython) | Bytecode-level guards | microseconds | High-frequency tool calls inside one service |
| Managed microVM (E2B) | Hardware virtualization | ~150 ms + network | Production agents without self-managed infra |

#### Option 1: Process-Level Sandbox (subprocess)
```python
import subprocess
import sys

class ProcessSandbox:
    """
    Run agent code in a fresh interpreter process using Python's isolated
    mode (-I): no user site-packages, no environment variables, no imports
    from the host's working directory. The parent enforces a hard
    wall-clock timeout and reads back stdout/stderr.

    Process isolation limits the blast radius (the host interpreter is
    never touched and a runaway child is killed), but it does NOT remove
    capabilities: the child can still `import os`. Capability restriction
    is the job of the container and RestrictedPython tiers below.
    """
    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def execute(self, code: str) -> dict:
        """Execute code in a fresh isolated interpreter process."""
        try:
            result = subprocess.run(
                [sys.executable, "-I", "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired:
            return {"error": f"Execution timeout after {self.timeout}s"}

        if result.returncode == 0:
            return {"result": result.stdout}
        return {"error": result.stderr.strip()}


if __name__ == "__main__":
    sandbox = ProcessSandbox(timeout=3)
    print(sandbox.execute("print(2 + 2)"))
    # Output: {'result': '4\n'}
    print(sandbox.execute("while True: pass"))
    # Output: {'error': 'Execution timeout after 3s'}
```

#### Option 2: Docker Container
```python
import docker

class DockerSandbox:
    """
    Container sandbox: read-only root filesystem, no network, CPU and
    memory capped, and scratch space on an in-memory tmpfs.

    Common pitfall: bind-mounting a host directory read-write (`volumes=`
    with mode 'rw') quietly defeats read_only=True - the agent can write
    anywhere on the host that the mount exposes. Use tmpfs instead: it
    lives in kernel memory and disappears with the container.
    """
    def __init__(self, image: str = "python:3.13-slim", timeout: int = 10):
        self.client = docker.from_env()
        self.image = image
        self.timeout = timeout

    def execute(self, code: str) -> dict:
        """Execute code in an isolated container."""
        container = self.client.containers.run(
            self.image,
            command=["python", "-c", code],
            mem_limit="128m",
            cpus=0.5,
            network_disabled=True,
            read_only=True,
            tmpfs={"/tmp": "rw,size=64m"},
            detach=True,
        )
        try:
            result = container.wait(timeout=self.timeout)
        except Exception:
            container.kill()  # enforce the wall-clock limit
            result = {"StatusCode": -1}
        logs = container.logs(stdout=True, stderr=True).decode("utf-8")
        container.remove(force=True)

        if result["StatusCode"] == 0:
            return {"result": logs}
        return {"error": logs or f"Execution timeout after {self.timeout}s"}
```

#### Option 3: RestrictedPython (Most Secure)
```python
import signal
import warnings

from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins, safer_getattr
from RestrictedPython.PrintCollector import PrintCollector

class RestrictedPythonSandbox:
    """
    In-process bytecode restriction: compile_restricted rewrites the AST
    so every attribute access, iteration, and print goes through a guard
    you supply - then exec runs under a minimal builtins allowlist.

    Two layers do the heavy lifting:
      - Compile time: names starting with '_' are rejected outright, so
        `__import__`, `__class__`, and friends never even parse.
      - Runtime: `import` fails because '__import__' is not in the
        builtins allowlist, and attribute access goes through
        safer_getattr, which blocks dunder reach-through like
        obj.__globals__.
    """
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        # safe_builtins is deliberately minimal (81 names: no sum/min/list).
        # Extend it explicitly with what YOUR agent code may use.
        self.allowed_builtins = dict(safe_builtins)
        self.allowed_builtins.update(
            {"print": print, "sum": sum, "min": min, "max": max,
             "list": list, "dict": dict, "enumerate": enumerate})

    def execute(self, code: str) -> dict:
        """Execute restricted code; the code sets a 'result' variable."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                byte_code = compile_restricted(code, filename="<sandbox>", mode="exec")
        except SyntaxError as e:
            return {"error": f"blocked at compile time: {e}"}

        safe_globals = {
            "__builtins__": self.allowed_builtins,
            "_print_": PrintCollector,   # print() writes here, not the terminal
            "_getattr_": safer_getattr,  # every attribute access goes through this
            "_getiter_": iter,           # required by for-loops and unpacking
            "_write_": lambda obj: obj,  # required by attribute assignment
        }
        safe_locals = {}

        def timeout_handler(signum, frame):
            raise TimeoutError("Execution timeout")

        # SIGALRM is POSIX-only; on Windows this sandbox relies on the
        # process or container tier for wall-clock enforcement.
        has_alarm = hasattr(signal, "SIGALRM")
        old_handler = signal.signal(signal.SIGALRM, timeout_handler) if has_alarm else None
        if has_alarm:
            signal.alarm(self.timeout)
        try:
            exec(byte_code, safe_globals, safe_locals)
            # The compiler injects the print collector into locals as '_print'
            collector = safe_locals.get("_print")
            return {"result": safe_locals.get("result"),
                    "printed": collector() if collector else ""}
        except TimeoutError:
            return {"error": f"Execution timeout after {self.timeout}s"}
        except Exception as e:
            return {"error": f"{type(e).__name__}: {e}"}
        finally:
            if has_alarm:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)


if __name__ == "__main__":
    sandbox = RestrictedPythonSandbox()
    print(sandbox.execute("print('hello')\nresult = sum(range(10))"))
    # Output: {'result': 45, 'printed': 'hello\n'}
    print(sandbox.execute("import os"))
    # Output: {'error': 'ImportError: __import__ not found'}
```
The compile-time layer is invisible in that demo on purpose: try
`result = __import__("os").getcwd()` and compilation fails before a
single byte executes, because names starting with `_` are rejected by
the restricted compiler itself.

#### Managed MicroVM Platforms (E2B)
For production agents, the industry-standard option is a managed
microVM: each execution gets a hardware-virtualized sandbox (Firecracker
on E2B) with a preinstalled Jupyter kernel, so you get container-grade
isolation without operating any infrastructure. The client API is small:

```python
# uv pip install e2b-code-interpreter   (requires E2B_API_KEY)
from e2b_code_interpreter import Sandbox

with Sandbox() as sbx:  # Firecracker microVM, provisioned in the cloud
    execution = sbx.run_code("sum(range(10))")  # last expression = result
    print(execution.results[0].text)  # Output: 45
    print(execution.logs.stdout)      # captured print()/stream output
```

Provider APIs increasingly ship the same capability as a first-class tool
(the code-interpreter tool in OpenAI's and Anthropic's APIs), which moves
execution entirely off your infrastructure at the cost of provider lock-in.

## Resource Management

### Memory Limits
Resource limits belong to the CHILD process. `resource.setrlimit` applies
to the calling process and never restores, so calling it in-process would
throttle your application itself and cap every later execution. The
correct Unix pattern sets the limits between fork and exec via
`preexec_fn`, so only the sandboxed child inherits them:

```python
import platform
import subprocess
import sys

class ResourceLimitedSandbox:
    """
    Child-process execution under OS resource limits (POSIX only).
    RLIMIT_AS caps address space (allocation beyond it raises MemoryError
    in the child); RLIMIT_CPU kills a compute-bound child. The portable
    wall-clock timeout still comes from the parent via subprocess timeout.
    """
    def __init__(self, max_memory_mb: int = 100, max_time: int = 10):
        self.max_memory_mb = max_memory_mb
        self.max_time = max_time

    def execute(self, code: str) -> dict:
        """Execute code in a resource-limited child process."""
        if platform.system() != "Linux":
            return {"error": "resource limits require a POSIX OS"}

        def set_limits():
            import resource
            ceiling = self.max_memory_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
            resource.setrlimit(resource.RLIMIT_CPU, (self.max_time, self.max_time))

        try:
            result = subprocess.run(
                [sys.executable, "-I", "-c", code],
                capture_output=True, text=True,
                timeout=self.max_time, preexec_fn=set_limits,
            )
        except subprocess.TimeoutExpired:
            return {"error": f"Execution timeout after {self.max_time}s"}

        if result.returncode == 0:
            return {"result": result.stdout}
        return {"error": result.stderr.strip()}


if __name__ == "__main__":
    sandbox = ResourceLimitedSandbox(max_memory_mb=100)
    print(sandbox.execute("result = sum(range(10))"))
    # Output (Windows): {'error': 'resource limits require a POSIX OS'}
    # Output (Linux):   {'result': '45\n'}
```

On Linux, an allocation-heavy child dies with a MemoryError traceback on
stderr and a non-zero exit code, which this envelope reports as an error -
the host process never feels the limit.

### Timeout Handling
In-process timeouts ride on SIGALRM, which is POSIX-only. There is no
portable way to kill a thread in Python, so for cross-platform enforcement
run the code in a child process (Option 1) and let the parent time it out:

```python
import signal
from contextlib import contextmanager

@contextmanager
def time_limit(seconds: int):
    """
    Wall-clock limit for in-process execution (POSIX only - Windows has
    no SIGALRM). Always restores the previous handler, even on error.
    """
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Execution timeout after {seconds}s")

    if not hasattr(signal, "SIGALRM"):
        raise RuntimeError("SIGALRM unavailable; use a process-level sandbox for portable timeouts")
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


if __name__ == "__main__":
    try:
        with time_limit(2):
            while True:
                pass
    except RuntimeError as e:
        print(e)
        # Output (Windows): SIGALRM unavailable; use a process-level sandbox for portable timeouts
    except TimeoutError as e:
        print(e)
        # Output (POSIX): Execution timeout after 2s
```

## Safe Execution for Agents

### LLM Code Execution
The pipeline an agent loop actually needs is three stages: a cheap static
screening pass, execution in the most restrictive sandbox available, and a
normalised envelope the model can parse reliably. Screening uses a regex
on real import statements - a substring check would false-positive on
'os' inside words like "position" - and rejection is loud, not a silent
comment-out the model would keep "fixing" forever:

```python
import re

class AgentCodeExecutor:
    """
    Defense in depth for agent-generated code:
    static screening -> restricted execution -> result envelope.
    """
    BLOCKED_MODULES = frozenset(
        {"os", "sys", "subprocess", "shutil", "socket", "pickle"})
    # Flags real import statements anywhere in the code (line starts).
    IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([\w.]+)", re.MULTILINE)

    def __init__(self, sandbox: RestrictedPythonSandbox | None = None):
        self.sandbox = sandbox or RestrictedPythonSandbox()

    @classmethod
    def screen(cls, code: str) -> list:
        """Static check: which blocked modules does the code import?"""
        roots = {m.group(1).split(".")[0] for m in cls.IMPORT_RE.finditer(code)}
        return sorted(roots & cls.BLOCKED_MODULES)

    def execute_agent_code(self, code: str) -> dict:
        """Screen, execute, and normalise the result for the LLM."""
        blocked = self.screen(code)
        if blocked:
            return {"status": "blocked", "blocked": blocked}
        return self._format(self.sandbox.execute(code))

    @staticmethod
    def _format(result: dict) -> dict:
        """One stable envelope so the model sees the same schema always."""
        if "error" in result:
            return {"status": "failed", "error": result["error"]}
        out = {"status": "ok", "result": result.get("result")}
        if result.get("printed"):
            out["printed"] = result["printed"]
        return out


if __name__ == "__main__":
    executor = AgentCodeExecutor()
    # 'position' contains 'os' - only real import statements are screened
    print(executor.execute_agent_code("text = 'position of the sun'\nresult = len(text)"))
    # Output: {'status': 'ok', 'result': 19}
    print(executor.execute_agent_code("import os\nresult = os.getcwd()"))
    # Output: {'status': 'blocked', 'blocked': ['os']}
```

Regex screening is a first pass, not a boundary: `import os` hidden behind
a semicolon or built dynamically slips past it. The boundary is the
sandbox itself (which blocks the import anyway); for serious static
analysis, walk the AST with the `ast` module instead.

### Jupyter Integration
A Jupyter kernel executes in a separate process with the full scientific
stack importable - the natural sandbox when agent code needs pandas or
numpy. Two protocol facts trip up most first implementations: the kernel
manager/client live in `jupyter_client` (not `IPython.kernel`), and
execution output arrives on the IOPUB channel - the shell channel only
carries the execute_reply acknowledgement, so a second `get_shell_msg()`
call just blocks forever:

```python
from jupyter_client.manager import start_new_kernel

class JupyterSandbox:
    """
    Sandboxed Jupyter kernel for agents. Requires a python3 kernelspec:
    uv pip install jupyter-client ipykernel
    """
    def __init__(self, kernel_name: str = "python3"):
        self.km, self.kc = start_new_kernel(kernel_name=kernel_name)

    def execute(self, code: str, timeout: int = 30) -> dict:
        """Execute code and collect IOPUB output until the kernel idles."""
        from queue import Empty

        self.kc.execute(code)
        outputs, error = [], None
        while True:
            try:
                msg = self.kc.get_iopub_msg(timeout=timeout)
            except Empty:
                return {"error": "kernel output timeout"}
            msg_type, content = msg["msg_type"], msg["content"]
            if msg_type == "stream":
                outputs.append(content["text"])
            elif msg_type == "execute_result":
                outputs.append(content["data"].get("text/plain", ""))
            elif msg_type == "error":
                error = "\n".join(content["traceback"])
            if msg_type == "status" and content["execution_state"] == "idle":
                break
        if error:
            return {"error": error}
        return {"result": "".join(outputs).strip()}

    def shutdown(self):
        """Shutdown the kernel and close channels."""
        self.kc.stop_channels()
        self.km.shutdown_kernel()
```

Because kernel state persists between `execute` calls, a Jupyter sandbox
doubles as agent scratch memory - variables, loaded models, and DataFrames
survive across tool calls within one session.

## Monitoring and Logging

### Execution Monitoring
Wrap any sandbox that speaks the `{"result": ...} / {"error": ...}`
envelope to get execution telemetry for free. Note what `tracemalloc` can
and cannot see: it traces allocations in THIS process, so it is meaningful
for the in-process RestrictedPython tier and reads near zero for the
subprocess tiers (the child's memory lives outside this interpreter):

```python
import time
import tracemalloc

class MonitoredSandbox:
    """
    Decorator-style wrapper adding execution telemetry to any sandbox
    that returns the {"result": ...} / {"error": ...} envelope.
    """
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.execution_log: list = []

    def execute(self, code: str) -> dict:
        """Execute with duration and peak-memory capture."""
        start_time = time.perf_counter()
        tracemalloc.start()
        try:
            result = self.sandbox.execute(code)
        finally:
            elapsed = time.perf_counter() - start_time
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()

        self.execution_log.append({
            "duration_s": round(elapsed, 4),
            "memory_peak_mb": round(peak / 1024 / 1024, 3),
            "success": "error" not in result,
        })
        return result

    def get_stats(self) -> dict:
        """Aggregate the execution log."""
        if not self.execution_log:
            return {"total_executions": 0}
        n = len(self.execution_log)
        return {
            "total_executions": n,
            "total_duration_s": round(
                sum(e["duration_s"] for e in self.execution_log), 4),
            "avg_memory_mb": round(
                sum(e["memory_peak_mb"] for e in self.execution_log) / n, 3),
            "success_rate": sum(
                1 for e in self.execution_log if e["success"]) / n,
        }


if __name__ == "__main__":
    monitored = MonitoredSandbox(RestrictedPythonSandbox())
    monitored.execute("result = sum(range(1000))")
    monitored.execute("result = 1/0")
    stats = monitored.get_stats()
    print(stats["total_executions"], stats["success_rate"])
    # Output: 2 0.5
```

Ship the log entries to your observability stack (duration and success
rate per agent session are the two numbers that catch runaway agents
first); on Linux, child-process peak memory can be read from
`resource.getrusage(RUSAGE_CHILDREN).ru_maxrss` to extend monitoring to
the subprocess tiers.


---

## Summary

A safe interpreter lets agents execute code without trusting it: this lesson builds the standard isolation ladder from a plain child-process sandbox that runs anywhere, through Docker containers, to in-process restrictions - each rung costing setup but buying containment. The rule it leaves: assume every generated line of code is adversarial until the sandbox says otherwise - the isolation level must match the blast radius of the worst code the model will ever write, not the code you expect.

## References

### Related Documents

- [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---

**Related Documents:**
- [7301: Collaborative Tasking](../../7300-orchestration/7301-Orchestration.md)
- [7101: ReAct Loop](../../7100-architecture/7101-ReAct-Loop-System.md)
- [1302: GPU Scheduler](../../../phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)

**Experiment Template:** [EXP_7202: Sandbox](../../../../../experiments/EXP_7202_SANDBOX.md)
