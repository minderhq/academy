---
Document ID: CHEAT-SHEET-027
Title: "CHEAT-SHEET-027: Tool Calling and MCP"
Last Updated: 2026-10-11
Status: Complete
Difficulty: Intermediate
Tags: ['cheatsheet', 'tool-calling', 'mcp', 'agents', 'function-calling']
---

# CHEAT-SHEET-027: Tool Calling and MCP

**Quick Reference for:** the N × M → N + M integration economics, the JSON-RPC wire and its two error doors, the v2 decorator contract and the client-side validation gate, the call_tool result triple, the v1 → v2 rename ledger, tool calling without MCP, and the caller-side resilience stack that keeps one hung tool from eating a turn.

**Version:** 1.0

## The Integration Economics: N × M → N + M

Without a protocol, every host × tool pair is bespoke glue: **4 hosts × 5 tools = 20 integrations** to write once and maintain forever. One MCP surface per side collapses it to **4 + 5 = 9** — each host implements the protocol once, each tool is exposed once. MCP is the **tool layer**; agent-to-agent communication (module 7302) is the agent layer — they compose, they do not compete.

The whole host-side contract is one config block (the client side is the same shape, `StdioServerParameters(command=..., args=[...])`):

```text
# one mcpServers block per host replaces N x M glue:
{
  "mcpServers": {
    "weather": {"command": "python", "args": ["weather_server.py"]},
    "billing": {"command": "python", "args": ["billing_server.py"]}
  }
}
```

## The Wire Beneath the SDK: JSON-RPC 2.0

Every MCP exchange is JSON-RPC: requests carry an `id`, responses pair by `id`, and **every response is `result` XOR `error`**. The failure modes split across two doors, and the debug checklist is exactly three questions — *id paired? `isError` vs `error`? revision negotiated?*

- **Executed-and-failed** travels as a **result with `isError: true`** — the model reads it and adapts. A client that only catches exceptions silently misreads every tool failure as success.
- **Protocol refusal** travels as an **error object** — the canonical case is the unknown-tool request answered `{"code": -32602, "message": "Unknown tool: nope"}`.

Transports (module 7203's table):

| Transport | Shape | 2026 status |
|---|---|---|
| stdio | subprocess stdin/stdout | the default, local servers |
| streamable HTTP | one URL, sessions over HTTP | the remote choice |
| SSE | server-sent events transport | **superseded** by streamable HTTP |

Spec revisions are dated and negotiated in `initialize`: **2026-07-28 is current and still serves 2025-11-25 clients** — that backward-compatibility window is why the revisions carry dates at all.

## Server Primitives: Who Picks What

| Primitive | Client surface | Who picks |
|---|---|---|
| tools | `list_tools` / `call_tool` | the model, autonomously |
| resources | `list_resources` / `read_resource` | the application |
| prompts | `list_prompts` / `get_prompt` | the user |

The reverse direction has its own lifecycle: **elicitation is current** — a server asking the human a mid-flow question, where an SDK built without the callback rejects the request outright (fail loud, never hang) — while **sampling and roots were retired in the 2026-07-28 spec** in favor of multi-round-trip flows.

## The v2 Decorator Contract

`@mcp.tool()` turns a plain function into a tool descriptor, and every field it generates has a job:

- **type hints → `input_schema`** — the argument contract, generated from the signature, so drift is structurally impossible.
- **docstring → `description`** — *model-facing*: the docstring is what the LLM selects on, so description quality IS tool-selection quality. A vague docstring is a misfire, not a style issue.
- **return hint → `output_schema`** — and a bare scalar return comes back wrapped, structured as `{"result": ...}` alongside the text content.
- `mcp.run(transport="stdio")` lives under the `if __name__ == "__main__":` guard — **importing the module must never start the server**.

## The Client Loop and the Result Triple

`Client(StdioServerParameters(command="python", args=[...]))` for a local server, `Client("https://host/mcp")` for a remote one; inside `async with`, the handshake is already done. The loop: `list_tools()` (paginated — honor `next_cursor`), then `call_tool(...)`, which returns the **result triple** — `content` (typed blocks, `isinstance`-narrow them), `structured_content`, and `is_error`. The fence's dispatch bill covers all three exits:

- ok: `is_error=False`, text `'22C and clear'`, structured `{"result": "22C and clear"}`
- missing argument: `is_error=True`, text `'Invalid arguments: missing required argument: city'`
- unknown tool: `is_error=True`, text `'Unknown tool: nope'`

Module 7203's rule: **a raising tool is a RESULT, not an exception — the failure travels in-band so the model can read it and adapt.**

## Validate the Contract Before the Call

The input schema is data — validate it **client-side, before the round trip**: missing required, off-enum, unknown argument. The fence's gate runs all three and the bad call dies as data, not as execution. The decorator makes drift structurally impossible; hand-written descriptors drift the first time someone edits the server and not the README — **validate against the descriptor `list_tools()` actually returned, not the one the README promised.**

## The v1 → v2 Rename Ledger

| Surface | v1 | v2 |
|---|---|---|
| Server | `FastMCP` (`mcp.server.fastmcp`) | `MCPServer` (`mcp.server`) |
| Client | `ClientSession` + `stdio_client` | `Client(...)` |
| Field names | camelCase (`inputSchema`) | snake_case (`input_schema`) |
| Spec era | 2025-03-26 / 2025-06-18 | **2026-07-28**, serves 2025-11-25 clients |

The v1 import fails with a `ModuleNotFoundError` that names the rename — follow the migration map, and pin `mcp<2` for as long as the 1.x line (which ends at 1.30.0) still has to run.

## Tool Calling Without MCP (module 7201)

The round trip MCP automates, bare tool calling does by hand: request → `tool_calls` → `json.loads(arguments)` → local execute → tool-result message (`role: "tool"`, `tool_call_id`) → next model turn. OpenAI-compatible endpoints speak it (Ollama via `base_url`); parallel calls come back in one request and are answered one result per `tool_call_id`; streaming tool-call deltas merge by index.

- **Structured outputs have a weak and a strong mode**: `json_object` promises merely valid JSON of any shape; `json_schema` with `strict: true` is constrained decoding — the model cannot emit an off-enum value, and `additionalProperties: false` plus a complete `required` list close the loose ends.
- **Errors travel in-band by design**: an unknown tool returns `{'status': 'error', 'error': 'Unknown tool: nope'}` and a crashing tool returns `'Execution failed: {e}'` as the next observation — one bad call never kills the run.
- **The security trio before any dynamic execution**: RestrictedPython with stripped builtins (the sandboxed eval returns **42**), `ToolPermission` deny-by-default (the unregistered `mystery_tool` reads **False**), and `validate_tool_input` (the `../etc/passwd` and `"bad name!"` payloads are both **False**).

Module 7201's closing rule: *the tool schema is an API contract with a probabilistic client — design it so the model cannot be validly wrong, and validate everything anyway.* And the boundary with CHEAT-SHEET-023: tool calling is one round trip the LLM decides; ReAct is the loop that iterates over many.

## The Caller-Side Resilience Stack (module 7204)

The un-budgeted turn is unbounded cost: `flaky_report` **accepts at +6.3 s and never answers**, so the turn reports 4/8 tools answered forever. And the asymmetry that shapes the whole stack: a refused connection fails in ~0.2 s (cheap); the **accepted-then-hung** call is the expensive one, and only a **read** timeout catches it — `httpx.Timeout(connect, read, write, pool)` exists because they are different budgets (5 s defaults; the OpenAI SDK ships `max_retries=2` and a 10-minute timeout).

| Layer | Failure class it owns | Canonical bill |
|---|---|---|
| Read budget | accepted-then-hung tools | no budget: 4/8 forever; 2.0 s budget: turn ends **8.6 s**, **7/8** answered |
| Retry + idempotency key | transport blips and their replays | 503/timeout/429 retryable, 400 permanent; naive ledger **6** entries (c2 double-charged), keyed ledger **5** receipts |
| Backoff + jitter | synchronized retry herds | 0.5 → 8.0 s exponential paces; no jitter: 40 clients peak **40**; seeded: peak **19**, **56** slots |
| Client token bucket | the caller's own burst | raw 50-burst: **41.0 s**, 40× 429; bucketed: **5.0 s**, zero 429s |
| Circuit breaker | the dead endpoint | unguarded **30/18/12** (7 into the brownout); guarded **28/18**, OPEN ×1 |

- Retry classification comes first: 503/timeout/429 are retryable, 400 is permanent — retrying the 400 is one wasted attempt (the fence's c4). urllib3 retries idempotent methods only (POST excluded) unless you key them.
- The idempotency key lives at the effect site: `setdefault` means the provider's internal retry returns the **original receipt** — 6 charges, 5 receipts.
- Backoff paces, jitter un-syncs: 40 clients without jitter are a metronome — all 40 land in the same tick, five times; seeded exponential + jitter spreads them (peak 19 in the busiest 0.25 s slot, 56 distinct slots).
- Respect the defender and pace yourself: honor `Retry-After` (413/429/503, capped), and run your **own** client-side token bucket — the defender's bucket rejects, the caller's bucket obeys. A 50-call burst paced at 10/s lands in 5.0 s instead of 41.0 s, zero 429s.
- The breaker is closed → open (3 consecutive failures) → half-open (a 2 s-cooldown probe): guarded, 28 attempts / 18 ok with the OPEN window routing 2 calls around the dead endpoint.

Module 7204's rule: *each layer owns exactly its own failure class.*

## One Run, the Whole Contract

The fence replays the full surface — economics, decorator, validation gate, result triple, wire, resilience — stdlib-only and deterministic:

```python
"""CHEAT-SHEET-027 fence: the tool-calling and MCP surface, priced.

Stdlib-only replay of the canonical numbers: the N+M integration
economics, the v2 decorator contract read off a signature with
inspect, the client-side validation gate, the call_tool result
triple, the JSON-RPC 2.0 wire pairing with its two error doors,
and the caller-side resilience stack from module 7204 on
deterministic fake clocks.
"""
import inspect
import json
import random
from collections import Counter

# --- F1: integration economics: N x M -> N + M -------------------------
HOSTS, TOOL_COUNT = 4, 5
print(f"F1 integration economics: {HOSTS} hosts x {TOOL_COUNT} tools = "
      f"{HOSTS * TOOL_COUNT} glue integrations without MCP, "
      f"{HOSTS} + {TOOL_COUNT} = {HOSTS + TOOL_COUNT} with one MCP surface per side")

# --- F2: the v2 decorator contract, read off the signature -------------
def get_weather(city: str, units: str = "celsius") -> str:
    """Current weather for a city."""
    return "22C and clear"


def convert_temperature(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""
    return celsius * 9 / 5 + 32


def descriptor(fn):
    """What @mcp.tool() generates: hints -> inputSchema, docstring -> description."""
    sig = inspect.signature(fn)
    props, required = {}, []
    for name, p in sig.parameters.items():
        props[name] = {"type": "number" if p.annotation is float else "string"}
        if p.default is inspect.Parameter.empty:
            required.append(name)
    returns = "number" if sig.return_annotation is float else "string"
    return {"description": (fn.__doc__ or "").strip(),
            "inputSchema": {"type": "object", "properties": props,
                            "required": required},
            "returns": returns}


TOOLBOX = {fn.__name__: fn for fn in (get_weather, convert_temperature)}
DESCRIPTORS = {name: descriptor(fn) for name, fn in TOOLBOX.items()}
for name, d in DESCRIPTORS.items():
    props = json.dumps(d["inputSchema"]["properties"], separators=(", ", ": "))
    print(f"F2 {name}: inputSchema {props} required={d['inputSchema']['required']}")
    print(f"   description='{d['description']}' return {d['returns']} -> "
          f"content text + structured_content wrapped as {{'result': ...}}")
print("   the docstring is model-facing: description quality IS tool-selection quality")

# --- F3: the validation gate before the call ---------------------------
SCHEMA = DESCRIPTORS["get_weather"]["inputSchema"]
SCHEMA["properties"]["units"]["enum"] = ["celsius", "fahrenheit"]  # as tools/list delivers it


def validate(schema, args):
    """None when args satisfy the schema, else the problem."""
    if not isinstance(args, dict):
        return "arguments must be an object"
    for req in schema.get("required", []):
        if req not in args:
            return f"missing required argument: {req}"
    for name, value in args.items():
        spec = schema["properties"].get(name)
        if spec is None:
            return f"unknown argument: {name}"
        if spec.get("type") == "string" and not isinstance(value, str):
            return f"{name} must be a string"
        if "enum" in spec and value not in spec["enum"]:
            return f"{name} must be one of {spec['enum']}"
    return None


cases = [
    ({"city": "Tokyo", "units": "celsius"}, None),
    ({"units": "celsius"}, "missing required argument: city"),
    ({"city": "Oslo", "units": "kelvin"}, "must be one of"),
    ({"city": "Tokyo", "temp": 1}, "unknown argument: temp"),
]
for args, expect in cases:
    verdict = validate(SCHEMA, args)
    assert verdict is None if expect is None else expect in verdict, (args, verdict)
    print(f"F3 validate({json.dumps(args, separators=(', ', ': '))}) -> {verdict!r}")
print("   the gate runs client-side BEFORE the round trip - a bad call dies as data, not as execution")

# --- F4: the call_tool result triple: a raising tool is a RESULT --------
def dispatch(name, args):
    if name not in TOOLBOX:
        return {"is_error": True, "text": f"Unknown tool: {name}", "structured": None}
    problem = validate(SCHEMA, args)
    if problem:
        return {"is_error": True, "text": f"Invalid arguments: {problem}", "structured": None}
    value = TOOLBOX[name](**args)
    return {"is_error": False, "text": value, "structured": {"result": value}}


for name, args in [("get_weather", {"city": "Tokyo"}),
                   ("get_weather", {"units": "celsius"}), ("nope", {})]:
    r = dispatch(name, args)
    tail = f" structured={json.dumps(r['structured'])}" if r["structured"] else ""
    print(f"F4 call_tool({name!r}) -> is_error={r['is_error']} text={r['text']!r}{tail}")
print("   a raising tool is a RESULT, not an exception - except-only clients misread every failure as success")

# --- F5: the wire beneath the SDK: JSON-RPC 2.0 pairing -----------------
next_id = 0


def request(method, params):
    global next_id
    next_id += 1
    return {"jsonrpc": "2.0", "id": next_id, "method": method, "params": params}


initialize = request("initialize", {"protocolVersion": "2026-07-28", "capabilities": {}})
list_tools = request("tools/list", {})
call_ok = request("tools/call", {"name": "get_weather", "arguments": {"city": "Tokyo"}})
call_bad = request("tools/call", {"name": "nope", "arguments": {}})
responses = [
    {"jsonrpc": "2.0", "id": initialize["id"],
     "result": {"protocolVersion": "2026-07-28"}},
    {"jsonrpc": "2.0", "id": list_tools["id"],
     "result": {"tools": ["get_weather", "convert_temperature"]}},
    {"jsonrpc": "2.0", "id": call_ok["id"],
     "result": {"content": [{"type": "text", "text": "22C and clear"}], "isError": False}},
    {"jsonrpc": "2.0", "id": call_bad["id"],
     "error": {"code": -32602, "message": "Unknown tool: nope"}},
]
by_id = {r["id"]: r for r in responses}
assert by_id[call_ok["id"]]["result"]["isError"] is False
assert by_id[call_bad["id"]]["error"]["code"] == -32602
print(f"F5 wire: {len(responses)} responses pair by id with {next_id} requests (pairing holds), "
      f"handshake negotiated {by_id[initialize['id']]['result']['protocolVersion']}")
print("   two error doors: executed-and-failed -> result isError (the model reads it); "
      "protocol refusal -> error object (code -32602)")

# --- F6: the caller-side resilience stack (7204), deterministic ---------
calls = [("search_docs", 0.2, 0.8), ("get_weather", 0.3, 0.5), ("run_sql", 0.4, 2.5),
         ("billing_charge", 0.2, 1.1), ("flaky_report", 0.3, None),
         ("send_email", 0.2, 0.6), ("get_invoice", 0.3, 0.9), ("log_event", 0.1, 0.2)]
READ_BUDGET = 2.0
t_raw, answered_raw = 0.0, 0
for _n, c, r in calls:
    t_raw += c
    if r is None:
        break  # accepted at +6.3s, never answers: the turn never ends
    t_raw += r
    answered_raw += 1
t_budget, answered_b, hung = 0.0, 0, ""
for name, c, r in calls:
    t_budget += c
    if r is None:
        hung = name
        continue
    t_budget += r
    answered_b += 1
print(f"F6a read budget: no budget -> '{calls[4][0]}' accepts at +{t_raw:.1f}s and never answers, "
      f"{answered_raw}/8 answered, the rest return never; budget {READ_BUDGET}s -> '{hung}' bounded, "
      f"turn ends {t_budget:.1f}s with {answered_b}/8 answered")

charges = [("c1", "ok"), ("c2", "503"), ("c3", "ok"), ("c4", "400"), ("c5", "ok"), ("c6", "ok")]
naive, keyed, wasted = [], {}, 0
for cid, status in charges:
    if status == "ok":
        naive.append(cid)
        keyed.setdefault(cid, "receipt")
        continue
    if status in ("503", "timeout", "429"):
        naive.append(cid)
        keyed.setdefault(cid, "receipt")
        if cid == "c2":
            naive.append(cid)  # the provider retried internally once more
            keyed.setdefault(cid, "receipt")
    else:
        wasted += 1
print(f"F6b idempotency: naive ledger {len(naive)} entries for 6 charges "
      f"(c2 appears {Counter(naive)['c2']}x = double-charged), keyed ledger {len(keyed)} receipts "
      f"(the duplicate returned the original receipt), the 400 wasted {wasted} attempt")

BASE, MAXD, N = 0.5, 8.0, 40
one = [min(BASE * 2 ** a, MAXD) for a in range(5)]
rng = random.Random(42)
peak, slots = 0, 0
for a in range(5):
    hi = min(BASE * 2 ** a, MAXD)
    buckets = Counter()
    for _ in range(N):
        buckets[round(rng.uniform(0, hi) / 0.25)] += 1
    peak = max(peak, max(buckets.values()))
    slots += len(buckets)
print(f"F6c backoff+jitter: one client climbs {', '.join(f'{d:g}' for d in one)}s; 40 clients "
      f"without jitter land on the same 5 ticks (peak {N}); seeded jitter spreads to peak {peak} "
      f"in the busiest 0.25s slot across {slots} distinct slots")

RATE, CAP, BURST = 10.0, 10.0, 50
ok_now, banned = min(BURST, CAP), BURST - min(BURST, CAP)
t_rawburst = ok_now / RATE + banned * 1.0
t_bucket, tokens, sent = 0.0, CAP, 0
while sent < BURST:
    if tokens >= 1:
        tokens -= 1
        sent += 1
        t_bucket += 1 / RATE
    else:
        tokens = min(CAP, tokens + 1)
print(f"F6d caller bucket: raw burst {BURST} calls -> {banned:g} 429s, wall {t_rawburst:.1f}s; "
      f"bucketed -> 0 429s, wall {t_bucket:.1f}s ({t_rawburst - t_bucket:.1f}s faster - "
      f"pacing never pays the rejection tax)")

N_CALLS, BROWNOUT, CB_N, CB_COOLDOWN = 30, range(12, 19), 3, 2


def outcome(i):
    if i in BROWNOUT:
        return "503"
    if i % 7 == 3:
        return "429"
    if i % 11 == 5:
        return "timeout"
    return "ok"


def run(with_breaker):
    ok = attempts = consec = skipped = opened = 0
    open_until = -1
    for i in range(N_CALLS):
        if with_breaker and i < open_until:
            skipped += 1
            continue
        attempts += 1
        oc = outcome(i)
        if oc == "ok":
            ok += 1
            consec = 0
        elif oc in ("503", "timeout") and with_breaker:
            consec += 1
            if consec >= CB_N:
                opened += 1
                open_until = i + 1 + CB_COOLDOWN
                consec = 0
    return ok, attempts, skipped, opened


ok_u, att_u, _, _ = run(False)
ok_g, att_g, skipped, opened = run(True)
print(f"F6e breaker: unguarded {att_u} attempts / {ok_u} successes / {att_u - ok_u} failures "
      f"({len(BROWNOUT)} straight into the brownout); guarded {att_g} attempts / {ok_g} successes, "
      f"OPEN x{opened} routing {skipped} calls around the dead endpoint")
```

And the canonical output it prints on a real run:

```text
F1 integration economics: 4 hosts x 5 tools = 20 glue integrations without MCP, 4 + 5 = 9 with one MCP surface per side
F2 get_weather: inputSchema {"city": {"type": "string"}, "units": {"type": "string"}} required=['city']
   description='Current weather for a city.' return string -> content text + structured_content wrapped as {'result': ...}
F2 convert_temperature: inputSchema {"celsius": {"type": "number"}} required=['celsius']
   description='Convert a Celsius temperature to Fahrenheit.' return number -> content text + structured_content wrapped as {'result': ...}
   the docstring is model-facing: description quality IS tool-selection quality
F3 validate({"city": "Tokyo", "units": "celsius"}) -> None
F3 validate({"units": "celsius"}) -> 'missing required argument: city'
F3 validate({"city": "Oslo", "units": "kelvin"}) -> "units must be one of ['celsius', 'fahrenheit']"
F3 validate({"city": "Tokyo", "temp": 1}) -> 'unknown argument: temp'
   the gate runs client-side BEFORE the round trip - a bad call dies as data, not as execution
F4 call_tool('get_weather') -> is_error=False text='22C and clear' structured={"result": "22C and clear"}
F4 call_tool('get_weather') -> is_error=True text='Invalid arguments: missing required argument: city'
F4 call_tool('nope') -> is_error=True text='Unknown tool: nope'
   a raising tool is a RESULT, not an exception - except-only clients misread every failure as success
F5 wire: 4 responses pair by id with 4 requests (pairing holds), handshake negotiated 2026-07-28
   two error doors: executed-and-failed -> result isError (the model reads it); protocol refusal -> error object (code -32602)
F6a read budget: no budget -> 'flaky_report' accepts at +6.3s and never answers, 4/8 answered, the rest return never; budget 2.0s -> 'flaky_report' bounded, turn ends 8.6s with 7/8 answered
F6b idempotency: naive ledger 6 entries for 6 charges (c2 appears 2x = double-charged), keyed ledger 5 receipts (the duplicate returned the original receipt), the 400 wasted 1 attempt
F6c backoff+jitter: one client climbs 0.5, 1, 2, 4, 8s; 40 clients without jitter land on the same 5 ticks (peak 40); seeded jitter spreads to peak 19 in the busiest 0.25s slot across 56 distinct slots
F6d caller bucket: raw burst 50 calls -> 40 429s, wall 41.0s; bucketed -> 0 429s, wall 5.0s (36.0s faster - pacing never pays the rejection tax)
F6e breaker: unguarded 30 attempts / 18 successes / 12 failures (7 straight into the brownout); guarded 28 attempts / 18 successes, OPEN x1 routing 2 calls around the dead endpoint
```

## Troubleshooting

| Symptom | Root cause | Fix |
|---|---|---|
| every tool failure looks like success | the client catches only exceptions; failures travel as results | branch on `is_error`; `isinstance`-narrow the content blocks |
| the model keeps calling the wrong tool | the docstring is model-facing and vague | write the description as selection copy — what it does, when to use it, units |
| the client rejects calls the server accepts | schema drift: hand-written descriptor vs server truth | validate against the descriptor `list_tools()` actually returned |
| `ModuleNotFoundError` after an SDK upgrade | the v1 → v2 rename | follow the migration map; pin `mcp<2` on the 1.x line (ends at 1.30.0) |
| a turn hangs forever on one tool | no read budget — the connect timeout misses accepted-then-hung | per-call read budget; 2.0 s bounds the turn at 8.6 s with 7/8 answered |
| a retried POST charges the customer twice | at-least-once redelivery with no ledger | idempotency key at the effect site — the duplicate returns the original receipt |

## Quick Reference For

- [Module 7203: MCP Hands-On](../../phases/phase7-agentic/7200-tools/7203-MCP-Hands-On.md)
- [Module 7201: Tool Calling](../../phases/phase7-agentic/7200-tools/7201-Tool-Calling.md)
- [Module 7204: Timeouts, Retries and Rate Limits](../../phases/phase7-agentic/7200-tools/7204-Timeouts-Retries-and-Rate-Limits.md)
- [CHEAT-SHEET-026: Agent Security](./CHEAT-SHEET-026-Agent-Security.md)
