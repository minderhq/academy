---
Document ID: 7202
Title: "7202: Code Interpreter - Sandbox Execution for Agent Code Testing"
Last Updated: 2026-09-24
Status: Complete
Difficulty: Advanced
---

# 7202: Code Interpreter - Sandbox Execution for Agent Code Testing

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Sandbox Architecture](#sandbox-architecture)
- [Resource Management](#resource-management)
- [Safe Execution for Agents](#safe-execution-for-agents)
- [Monitoring and Logging](#monitoring-and-logging)
- [References](#references)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain Sandbox Architecture
- Explain Resource Management
- Explain Safe Execution for Agents
- Measure and evaluate Monitoring and Logging

---

## Abstract
A safe Python interpreter enables agents to execute code in a sandboxed environment, preventing malicious or erroneous code from affecting the host system.

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

#### Option 1: PyPy Sandbox
```python
import subprocess
import tempfile
import os

class PyPySandbox:
    """
    PyPy sandbox with restricted operations
    """
    def __init__(self, timeout=10, memory_mb=100):
        self.timeout = timeout
        self.memory_mb = memory_mb

    def execute(self, code: str, inputs: dict = None) -> any:
        """
        Execute code in sandbox
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Write code to file
            f.write(code)
            code_file = f.name

        try:
            # Run with pypy (restricted mode)
            result = subprocess.run(
                [
                    'pypy',
                    '--sandbox',
                    f'-mtimeout={self.timeout}',
                    code_file
                ],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=str(inputs) if inputs else None
            )

            if result.returncode == 0:
                # Parse output
                return self._parse_output(result.stdout)
            else:
                return {
                    "error": result.stderr,
                    "traceback": result.stdout
                }

        except subprocess.TimeoutExpired:
            return {"error": "Execution timeout"}
        finally:
            os.unlink(code_file)

    def _parse_output(self, output: str) -> any:
        """Parse sandbox output"""
        try:
            # Try to eval as Python expression
            return eval(output)
        except:
            return {"output": output}
```

#### Option 2: Docker Container
```python
import docker

class DockerSandbox:
    """
    Docker-based sandbox for code execution
    """
    def __init__(self):
        self.client = docker.from_env()

    def execute(self, code: str, timeout=10) -> any:
        """
        Execute code in isolated container
        """
        # Create container
        container = self.client.containers.run(
            'python:3.11-slim',
            command=['python', '-c', code],
            mem_limit='128m',
            cpus=0.5,
            network_disabled=True,
            read_only=True,
            # Mount temp directory (read-write)
            volumes={'/tmp': {'bind': '/tmp', 'mode': 'rw'}},
            # Run in background
            detach=True
        )

        try:
            # Wait for completion or timeout
            result = container.wait(timeout=timeout)

            # Get logs
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')

            if result['StatusCode'] == 0:
                return {"output": logs}
            else:
                return {"error": logs}

        finally:
            # Remove container
            container.remove(force=True)
```

#### Option 3: RestrictedPython (Most Secure)
```python
from RestrictedPython import compile_restricted
from RestrictedPython.Guards import safe_builtins
import sys

class RestrictedPythonSandbox:
    """
    RestrictedPython: Bytecode-level restrictions
    """
    def __init__(self):
        self.allowed_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bin': bin,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'format': format,
            'hex': hex,
            'int': int,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'oct': oct,
            'ord': ord,
            'pow': pow,
            'print': print,
            'range': range,
            'repr': repr,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
        }

    def execute(self, code: str, timeout=10) -> any:
        """
        Execute restricted code
        """
        # Compile with restrictions
        byte_code = compile_restricted(
            code,
            filename='<string>',
            mode='exec'
        )

        # Create restricted globals
        safe_globals = {
            '__builtins__': self.allowed_builtins,
        }

        # Create safe locals
        safe_locals = {}

        try:
            # Execute with signal alarm for timeout
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError("Execution timeout")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout)

            # Execute
            exec(byte_code, safe_globals, safe_locals)

            # Disable alarm
            signal.alarm(0)

            # Return result (look for 'result' variable)
            return safe_locals.get('result', None)

        except TimeoutError:
            return {"error": "Execution timeout"}
        except Exception as e:
            return {"error": str(e)}
```

## Resource Management

### Memory Limits
```python
import resource
import platform

class ResourceLimitedSandbox:
    """
    Sandbox with resource limits
    """
    def __init__(self, max_memory_mb=100, max_time=10):
        self.max_memory_mb = max_memory_mb
        self.max_time = max_time

    def _set_limits(self):
        """Set resource limits (Unix only)"""
        if platform.system() != "Linux":
            return  # Resource limits only work on Unix

        # Set memory limit
        resource.setrlimit(
            resource.RLIMIT_AS,
            (self.max_memory_mb * 1024 * 1024, self.max_memory_mb * 1024 * 1024)
        )

        # Set CPU time limit
        resource.setrlimit(
            resource.RLIMIT_CPU,
            (self.max_time, self.max_time)
        )

    def execute(self, code: str) -> any:
        """Execute with resource limits"""
        self._set_limits()

        try:
            # Create execution context
            exec_globals = {}
            exec_locals = {}

            # Execute
            exec(code, exec_globals, exec_locals)

            return {"result": exec_locals}

        except MemoryError:
            return {"error": "Memory limit exceeded"}
        except Exception as e:
            return {"error": str(e)}
```

### Timeout Handling
```python
import signal
import contextlib

class TimeoutSandbox:
    """
    Sandbox with timeout using signals
    """
    @contextlib.contextmanager
    def time_limit(self, seconds):
        """
        Context manager for time limit
        """
        def signal_handler(signum, frame):
            raise TimeoutError(f"Timed out after {seconds} seconds")

        # Set signal handler
        old_handler = signal.signal(signal.SIGALRM, signal_handler)
        signal.alarm(seconds)

        try:
            yield
        finally:
            # Restore old handler
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

    def execute(self, code: str, timeout=10) -> any:
        """Execute with timeout"""
        try:
            with self.time_limit(timeout):
                exec_globals = {}
                exec_locals = {}
                exec(code, exec_globals, exec_locals)
                return {"result": exec_locals}

        except TimeoutError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}
```

## Safe Execution for Agents

### LLM Code Execution
```python
class AgentCodeExecutor:
    """
    Safe code execution for LLM agents
    """
    def __init__(self):
        # Use most secure option
        self.sandbox = RestrictedPythonSandbox()

    def execute_agent_code(self, code: str) -> str:
        """
        Execute code generated by agent
        """
        # Pre-process code
        processed_code = self._preprocess(code)

        # Execute in sandbox
        result = self.sandbox.execute(processed_code)

        # Post-process result
        return self._postprocess(result)

    def _preprocess(self, code: str) -> str:
        """
        Pre-process code for safety
        """
        # Remove dangerous imports
        dangerous_imports = [
            'os', 'subprocess', 'sys', 'shutil',
            'pickle', 'eval', 'exec', '__import__'
        ]

        lines = []
        for line in code.split('\n'):
            # Check for dangerous imports
            if any(imp in line for imp in dangerous_imports):
                # Comment out
                lines.append(f"# {line}  # Blocked for security")
            else:
                lines.append(line)

        # Wrap in try-except
        wrapped = f"""
try:
{chr(10).join(lines}
    result = eval(str(locals()))
except Exception as e:
    result = {{"error": str(e)}}
"""

        return wrapped

    def _postprocess(self, result: any) -> str:
        """Format result for LLM"""
        if isinstance(result, dict) and "error" in result:
            return f"Execution failed: {result['error']}"
        else:
            return f"Execution result: {result}"
```

### Jupyter Integration
```python
class JupyterSandbox:
    """
    Sandboxed Jupyter kernel for agents
    """
    def __init__(self):
        from IPython.kernel import KernelManager
        self.km = KernelManager()
        self.km.start_kernel()
        self.kc = self.km.client()

    def execute(self, code: str) -> any:
        """
        Execute code in Jupyter kernel
        """
        # Execute
        self.kc.execute(code)

        # Get result
        msg = self.kc.get_shell_msg(timeout=10)

        if msg['content']['status'] == 'ok':
            # Get output
            data = self.kc.get_shell_msg(timeout=10)
            return data['content']
        else:
            return {
                'error': msg['content'].get('ename', 'Unknown error'),
                'traceback': msg['content'].get('traceback', [])
            }

    def shutdown(self):
        """Shutdown kernel"""
        self.kc.stop_channels()
        self.km.shutdown_kernel()
```

## Monitoring and Logging

### Execution Monitoring
```python
class MonitoredSandbox:
    """
    Sandbox with detailed execution monitoring
    """
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.execution_log = []

    def execute(self, code: str) -> any:
        """
        Execute with monitoring
        """
        import time
        import tracemalloc

        # Start monitoring
        start_time = time.time()
        tracemalloc.start()

        # Execute
        result = self.sandbox.execute(code)

        # Stop monitoring
        elapsed = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Log execution
        log_entry = {
            'timestamp': time.time(),
            'duration': elapsed,
            'memory_peak_mb': peak / 1024 / 1024,
            'success': 'error' not in result
        }

        self.execution_log.append(log_entry)

        return result

    def get_stats(self) -> dict:
        """Get execution statistics"""
        if not self.execution_log:
            return {}

        total_duration = sum(e['duration'] for e in self.execution_log)
        avg_memory = sum(e['memory_peak_mb'] for e in self.execution_log) / len(self.execution_log)
        success_rate = sum(1 for e in self.execution_log if e['success']) / len(self.execution_log)

        return {
            'total_executions': len(self.execution_log),
            'total_duration': total_duration,
            'avg_memory_mb': avg_memory,
            'success_rate': success_rate
        }
```


---

## References

### Related ai-engineering-curriculum Documents

- [7201: Tool Calling & Function Execution](../7201-Tool-Calling.md)

---

## Next Steps

- Return to: **[Module README](../README.md)**

---
---

**Related Documents:**
- [7301: Collaborative Tasking](../../7300-orchestration/7301-Orchestration.md)
- [7101: ReAct Loop](../../7100-architecture/7101-ReAct-Loop-System.md)
- [1302: GPU Scheduler](../../../phase1-infra/1300-kubernetes/1302-GPU-Scheduler.md)

**Experiment Template:** `experiments/EXP_7202_SANDBOX.md`
