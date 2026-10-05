---
Document ID: 7203
Title: "7203: MCP Hands-On — Tool Servers and Clients"
Phase: 7
Module: 7200
Last Updated: 2026-10-05
Status: Complete
Difficulty: Intermediate
Estimated Time: 4 hours
Prerequisites: See module README
Related: See module README
Tags: ['agents', 'tool-calling', 'mcp']
---

# 7203: MCP Hands-On — Tool Servers and Clients

## Table of Contents

- [Learning Objectives](#learning-objectives)
- [Abstract](#abstract)
- [Why MCP Exists](#why-mcp-exists)
- [The Architecture](#the-architecture)
- [Server Primitives](#server-primitives)
- [Hands-On: The Tool Server](#hands-on-the-tool-server)
- [Hands-On: The Client Loop](#hands-on-the-client-loop)
- [The Wire Under the SDK](#the-wire-under-the-sdk)
- [The Contract Before the Call](#the-contract-before-the-call)
- [Versioning: The v1 to v2 Rename](#versioning-the-v1-to-v2-rename)
- [Known Failure Modes](#known-failure-modes)
- [Summary](#summary)
- [References](#references)
- [Next Steps](#next-steps)

---

## Learning Objectives

After completing this lesson, you will be able to:

- Explain what problem the Model Context Protocol solves — the N×M integration problem between agent hosts and tool providers, collapsed to N+M by one standard surface per side
- Build an MCP tool server — register tools with `@mcp.tool()`, let type hints generate the input schema and the docstring become the description the model reads
- Walk the client loop — open a `Client` over stdio or streamable HTTP, discover tools with `list_tools()`, invoke with `call_tool()`, and branch on `is_error` instead of catching exceptions
- Read the wire beneath the SDK — initialize handshakes, `tools/list` and `tools/call` as JSON-RPC 2.0 messages paired by id, with results and errors as ordinary response objects
- Validate the tool contract before dispatch — the input schema is data, and checking arguments against it client-side is what keeps a bad call from becoming a bad execution
- Navigate the SDK's version boundary — the v1 `FastMCP` to v2 `MCPServer` rename, the `<2` pin for legacy code, and which protocol features the 2026-07-28 spec retired

---

## Abstract

The Model Context Protocol (MCP) standardizes how an agent talks to tools: one JSON-RPC 2.0 surface for discovery, invocation and errors, so a tool written once is usable by every MCP host. This lesson builds both ends — a tool server with the SDK's decorator surface and a client that discovers, calls and reads in-band errors — then drops below the SDK to the wire messages and the schema contract that make the protocol debuggable.

---

## Why MCP Exists

The [7201 lesson](./7201-Tool-Calling.md) built tool calling against one provider's API: you declare a function schema in the request, the model answers with a tool call, you execute and feed the result back. That loop is per-provider glue — every host rewrites it, and every tool author re-wraps their API for every host they want to reach. N hosts × M tools is N×M integrations.

MCP collapses that to N+M. A tool author publishes one **server**; every host that speaks the protocol is a **client** that can use it. The [orchestration lesson](../7300-orchestration/7302-Communication-Protocols.md) draws the boundary this corpus uses: MCP standardizes the *tool layer* — discovery, invocation, resource access — and deliberately stops there, leaving agent-to-agent discovery and task handoffs to A2A-style protocols.

```text
Without MCP (N x M):            With MCP (N + M):

Host A --- glue --- Tool 1      Host A ---+         +--- Tool 1
Host A --- glue --- Tool 2                |         |
Host B --- glue --- Tool 1      Host B ---+--- MCP ---+--- Tool 2
Host B --- glue --- Tool 2      (one integration per side)
```

In practice an MCP deployment starts as one config file — the `mcpServers` block every MCP client reads, shown in [7302](../7300-orchestration/7302-Communication-Protocols.md) — where each entry either launches a stdio server as a subprocess (`command` + `args`) or points at a streamable-HTTP one (`url`). This lesson is the Python side of that config.

---

## The Architecture

MCP is JSON-RPC 2.0 over one of two transports:

| Transport | Shape | Use when |
|-----------|-------|----------|
| **stdio** (default) | The host launches the server as a subprocess and speaks over stdin/stdout | Local tools: file access, shell-out, anything sharing the host's trust |
| **streamable-http** | The server listens on a URL; requests stream over HTTP | Remote or shared tools: a team's internal API, a hosted service |

The older SSE transport is superseded — you will meet it in older tutorials, but new servers pick stdio or streamable-http.

The protocol evolves through **dated revisions**, and version negotiation is the first thing that happens on the wire: the client's `initialize` request carries its `protocolVersion`, and the server answers with the revision it will speak. The SDK's current stable line speaks the **2026-07-28** revision and still serves clients from the **2025-11-25** era, which matters when your fleet mixes old and new.

```text
Host (MCP client)                    Server (tool provider)
       |                                    |
       |--- initialize (protocolVersion) -->|
       |<-- result (capabilities, tools) ---|
       |                                    |
       |--- tools/list -------------------->|   discovery
       |<-- result (tool descriptors) ------|
       |                                    |
       |--- tools/call (name, arguments) -->|   invocation
       |<-- result (content, isError) ------|
```

---

## Server Primitives

A server surfaces three primitives, and the client verbs mirror them:

| Primitive | What it is | Client verb |
|-----------|------------|-------------|
| **Tools** | Model-invoked actions — the function-calling face | `list_tools()` / `call_tool()` |
| **Resources** | Read-only context the application can attach — files, query results | `list_resources()` / `read_resource()` |
| **Prompts** | Reusable, parameterized prompt templates the server authors | `list_prompts()` / `get_prompt()` |

Tools are the primitive agents consume autonomously; resources and prompts are things the *application* or the *user* selects. This lesson works the tools face end to end — it is the one that connects to the [7201 round trip](./7201-Tool-Calling.md).

The protocol also runs in reverse: a server can ask its **client** for help. The current mechanism is **elicitation** — the server asks the user for a form or URL confirmation mid-task, answered by a callback your client registers. Registering a callback is also how a client declares a capability: without one, the SDK refuses the server's request on your behalf rather than hanging. Two older reverse-direction features — server-initiated **sampling** (the server asking your model to complete text) and **roots** (workspace boundaries) — were retired by the 2026-07-28 spec in favor of multi-round-trip requests; the callbacks still exist to talk to older servers.

---

## Hands-On: The Tool Server

The SDK's high-level server is `MCPServer` (v2 — the versioning section below explains where `FastMCP` went). The decorator does the work the [module README's](./README.md#authoring-tools-the-tool-decorator) `@tool` section preached: one source of truth, and the schema follows the function.

```python
# pip install "mcp>=2"    # v2 is the current stable line
from mcp.server import MCPServer

# One server object is one tool provider. The name shows up in
# the initialize handshake and in host UIs.
mcp = MCPServer("academy-weather")


@mcp.tool()
def get_weather(city: str, units: str = "celsius") -> str:
    """Current weather for a city."""
    return "22C and clear"  # stand-in for a real forecast client


@mcp.tool()
def convert_temperature(celsius: float) -> float:
    """Convert a Celsius temperature to Fahrenheit."""

    return celsius * 9 / 5 + 32


if __name__ == "__main__":
    # run() is synchronous and blocks for the life of the server.
    # stdio is the default transport; pass transport="streamable-http"
    # (plus host/port) to listen on a URL instead. Everything that
    # loads this file - tests, the Inspector, an importing client -
    # hits the guard first, so an import never becomes a running server.
    mcp.run(transport="stdio")
```

What the decorator generated, invisibly:

- **`inputSchema`** — from the type hints: `city` a required string, `units` an optional string, `celsius` a required number. The wire contract is the signature.
- **`description`** — the docstring. This is not documentation for humans; it is the text the model reads when choosing among tools. Docstring quality is tool-selection quality.
- **`outputSchema`** — from the return hint. A tool returning a plain `str` surfaces its answer twice: as text in `content`, and as `{"result": "..."}` in `structured_content`. Bare scalars get wrapped in a `result` property so the structured channel always carries an object.

The boundary against [7201](./7201-Tool-Calling.md): there the schema was the whole integration — you wrote the dict, the provider executed nothing, and your process owned execution. Here the server owns execution and the protocol carries discovery with it; a host that has never seen your code can list and call the tool.

---

## Hands-On: The Client Loop

The high-level client is `Client`, and its first argument *is* the transport choice: a URL string for streamable HTTP, a `StdioServerParameters` to launch a subprocess.

```python
import asyncio

from mcp import Client, StdioServerParameters

# stdio: launch the server above as a subprocess. For a remote
# server the same code starts Client("https://host/mcp") instead.
server = StdioServerParameters(command="python", args=["weather_server.py"])


async def main():
    async with Client(server) as client:
        # Inside the block the handshake already happened:
        # client.protocol_version, server_capabilities and
        # server_info are populated.

        tools = await client.list_tools()
        print([t.name for t in tools])  # ['get_weather', 'convert_temperature']
        # Large catalogs paginate: loop while next_cursor is not None.

        result = await client.call_tool(
            "get_weather", {"city": "Tokyo", "units": "celsius"}
        )
        if result.is_error:
            # A raising tool is a RESULT, not an exception - the
            # failure travels in-band so the model can read it
            # and adapt. A client that only catches exceptions
            # silently misreads every tool failure.
            print("tool failed:", result.content[0].text)
        else:
            print(result.content[0].text)       # the model-facing text
            print(result.structured_content)    # the code-facing data


asyncio.run(main())
```

`content` is a list of typed blocks (`TextContent` and siblings) — narrow with `isinstance` before reading, because a tool may return several. `structured_content` is what your code consumes; `is_error` is the branch that keeps the loop honest.

---

## The Wire Under the SDK

The SDK earns its keep, but debugging an MCP integration means reading JSON-RPC 2.0 — every message is a request, response or notification, responses pair with requests by `id`, and each response carries either a `result` or an `error` object. This demo builds the three messages of the weather round trip by hand and checks the pairing rules:

```python
import json

# JSON-RPC 2.0: every request has a method, params and an id that
# the response echoes back. MCP layers initialize / tools/list /
# tools/call on top of that envelope.
next_id = 0


def request(method, params):
    global next_id
    next_id += 1
    return {"jsonrpc": "2.0", "id": next_id, "method": method, "params": params}


initialize = request(
    "initialize",
    {
        "protocolVersion": "2026-07-28",
        "capabilities": {},
        "clientInfo": {"name": "academy-client", "version": "1.0"},
    },
)
tools_list = request("tools/list", {})
tools_call = request(
    "tools/call",
    {"name": "get_weather", "arguments": {"city": "Tokyo", "units": "celsius"}},
)

assert initialize["method"] == "initialize"
assert tools_call["params"]["name"] == "get_weather"
assert tools_call["params"]["arguments"]["units"] == "celsius"

# Responses pair by id and carry exactly one of result / error.
# A tool failure is a RESULT with isError set; an error object is
# for protocol-level problems (unknown method, bad params, unknown tool).
responses = [
    {
        "jsonrpc": "2.0",
        "id": tools_call["id"],
        "result": {
            "content": [{"type": "text", "text": "22C and clear"}],
            "isError": False,
        },
    },
    {
        "jsonrpc": "2.0",
        "id": 99,
        "error": {"code": -32602, "message": "Unknown tool: nope"},
    },
]
by_id = {r["id"]: r for r in responses}
ok = by_id[tools_call["id"]]
assert ok["result"]["isError"] is False
assert ok["result"]["content"][0]["type"] == "text"
assert set(by_id[99]["error"]) == {"code", "message"}

print(
    json.dumps(
        {
            "handshake": initialize["method"],
            "pairing": by_id[tools_call["id"]]["id"] == tools_call["id"],
            "protocol_error_code": by_id[99]["error"]["code"],
        }
    )
)
```

When a host logs look wrong, this is the layer to read: is the `id` paired, is the failure in `result.isError` or in `error`, did the `initialize` negotiate the revision you assumed.

---

## The Contract Before the Call

The input schema is ordinary JSON Schema data, which means a careful client can validate arguments *before* spending a round trip — and the failure semantics are worth rehearsing, because "the tool raised" and "the protocol refused" reach the model through different doors:

```python
# The wire descriptor for get_weather - exactly what tools/list
# returns. The SDK generated it from type hints; here it is data,
# so the validation contract can be exercised without the SDK.
TOOLS = {
    "get_weather": {
        "description": "Current weather for a city",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string"},
                "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["city"],
        },
    },
}


def validate(schema, args):
    """Return None when args satisfy the schema, else the problem."""
    if schema.get("type") != "object" or not isinstance(args, dict):
        return "arguments must be an object"
    for name in schema.get("required", []):
        if name not in args:
            return f"missing required argument: {name}"
    for name, value in args.items():
        spec = schema.get("properties", {}).get(name)
        if spec is None:
            return f"unknown argument: {name}"
        if spec.get("type") == "string" and not isinstance(value, str):
            return f"{name} must be a string"
        if "enum" in spec and value not in spec["enum"]:
            return f"{name} must be one of {spec['enum']}"
    return None


assert validate(TOOLS["get_weather"]["inputSchema"], {"city": "Tokyo"}) is None
assert (
    "missing required"
    in validate(TOOLS["get_weather"]["inputSchema"], {"units": "celsius"})
)
assert (
    "must be one of"
    in validate(TOOLS["get_weather"]["inputSchema"], {"city": "Oslo", "units": "kelvin"})
)


# MCP error semantics, replayed: a raising tool is a result with
# isError, not an exception - the model reads the failure and can
# retry with different arguments. Protocol refusals (unknown tool)
# also arrive in-band here for symmetry with the real SDK.
def dispatch(name, args):
    if name not in TOOLS:
        return {"isError": True, "text": f"Unknown tool: {name}"}
    problem = validate(TOOLS[name]["inputSchema"], args)
    if problem:
        return {"isError": True, "text": f"Invalid arguments: {problem}"}
    return {"isError": False, "text": "22C and clear"}  # stand-in execution


assert dispatch("get_weather", {"city": "Tokyo"})["isError"] is False
assert dispatch("nope", {})["isError"] is True
print("contract holds: validate -> dispatch -> in-band isError")
```

This is also where [7201's best-practice list](./7201-Tool-Calling.md#tool-calling-best-practices) lands on new ground: the decorator makes schema drift structurally impossible (the schema *is* the signature), but the moment a team hand-writes descriptors beside implementations, drift returns — validate against the descriptor `list_tools()` actually returned, not the one the README promised.

---

## Versioning: The v1 to v2 Rename

You will meet both generations in the wild, and the difference is one rename plus a field-style change:

| | v1 (≤ 1.30.0) | v2 (2.x, current stable) |
|---|---|---|
| Server class | `from mcp.server.fastmcp import FastMCP` | `from mcp.server import MCPServer` |
| Client | `ClientSession` + `stdio_client` plumbing | `Client(...)` — one entry for every transport |
| Python fields | camelCase (`inputSchema`) | snake_case (`input_schema`) |
| Spec era | 2025-03-26 / 2025-06-18 | 2026-07-28 (serves 2025-11-25 clients too) |

The v1 import path no longer exists in v2: importing `mcp.server.fastmcp` raises `ModuleNotFoundError` with a message that names the rename and links the migration guide — the SDK itself refuses to let old code fail silently. Teams still on v1 pin `mcp<2`; the 1.x line takes critical fixes but is not where new surfaces land. Older tutorials (including some otherwise-excellent ones) show `FastMCP` and the `ClientSession` plumbing — read them for the concepts, which did not change; write against the table above.

---

## Known Failure Modes

| Failure | What it looks like | Mitigation |
|---------|--------------------|------------|
| **Tool-description injection** | A malicious or compromised server writes instructions *into* tool descriptions or results, aimed at the model, not at your code | Treat every description and every tool result as untrusted text; require human approval for sensitive tools; prefer servers you vet |
| **Confused deputy** | A trusted server relays the agent's broad credentials to a narrower upstream, amplifying reach | Scope tokens per server and per audience; never hand one server another's credentials |
| **Exceptions-only clients** | The code `try/except`s around `call_tool()` and never reads `is_error`, so in-band failures route back to the model as successes | Branch on `is_error` first; treat a raised exception as a protocol bug, not a tool outcome |
| **Schema drift** | Hand-maintained tool descriptors diverge from the implementation; the model calls a tool that no longer accepts those arguments | Derive schemas from code (decorators); validate against the descriptor `list_tools()` returned |
| **Environment leaks through stdio** | A config block passes the full shell environment to a subprocess server, which forwards it to a third-party API | Pass an explicit minimal env allowlist per server entry |
| **Unbounded catalogs** | Fifty servers × ten tools flood the model's context and degrade selection | Filter `list_tools()` results per task; fewer, sharper tools beat more |

---

## Summary

- MCP collapses the N×M host-to-tool integration problem to N+M with one JSON-RPC 2.0 surface — the tool layer, with A2A-style protocols owning the agent layer
- Two transports: **stdio** for local subprocess servers, **streamable-http** for remote ones; SSE is superseded, and dated spec revisions are negotiated at `initialize`
- Three server primitives — tools, resources, prompts — and a reverse direction where the server asks the client (elicitation is current; sampling and roots moved to multi-round-trip requests in the 2026-07-28 spec)
- The v2 SDK is one decorator and one client: `@mcp.tool()` turns hints into schema, docstring into description, return type into structured output; `Client` walks every transport; failures arrive as results with `is_error`
- Under the SDK: requests pair by id, tool failures are results, protocol refusals are errors — read that layer when an integration misbehaves
- The v1→v2 rename (`FastMCP` → `MCPServer`) is the one migration wall most MCP material on the internet has not caught up with yet

---

## References

- [1] Anthropic. "Model Context Protocol" - [https://modelcontextprotocol.io](https://modelcontextprotocol.io)
- [2] MCP Python SDK documentation (v2) - [https://pypi.org/project/mcp/](https://pypi.org/project/mcp/)
- [3] modelcontextprotocol/python-sdk repository - [https://github.com/modelcontextprotocol/python-sdk](https://github.com/modelcontextprotocol/python-sdk)

---

## Next Steps

- [7201: Tool Calling](./7201-Tool-Calling.md) — the per-provider round trip MCP standardizes; start here if the schema-and-dispatch contract above felt unfamiliar
- [7302: Communication Protocols](../7300-orchestration/7302-Communication-Protocols.md) — where MCP stops (tool layer) and agent-to-agent protocols begin
- [7500: AI Agent Security](../7500-security/README.md) — prompt injection and tool-safety defenses for the failure modes this lesson named
