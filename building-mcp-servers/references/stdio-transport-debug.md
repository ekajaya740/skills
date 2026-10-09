# Stdio Transport Debugging

The `mcp` Python SDK v1.27+ uses **newline-delimited JSON** over stdio, not Content-Length framing. This trips up anyone who has worked with the older MCP protocol draft or HTTP-style transports.

## The Symptom

Testing your MCP server with `Content-Length` framing produces errors like:

```
Received exception from stream: 1 validation error for JSONRPCMessage
  Invalid JSON: expected value at line 1 column 1 [type=json_invalid, input_value='Content-Length: 166\n', input_type=str]
```

## The Fix

Send each JSON-RPC message as a single line terminated by `\n`:

```python
import asyncio
import json
import subprocess
import sys

async def test_mcp():
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "/path/to/server.py",
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    await asyncio.sleep(0.5)  # let server start

    def send(req):
        msg = json.dumps(req)
        proc.stdin.write(f"{msg}\n".encode())

    # Initialize
    send({
        "jsonrpc": "2.0", "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    })
    resp = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
    print("Init:", json.loads(resp.decode().strip()))

    # Initialized notification
    send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    # List tools
    send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    resp = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
    print("Tools:", json.loads(resp.decode().strip()))

    # Call a tool
    send({
        "jsonrpc": "2.0", "id": 3,
        "method": "tools/call",
        "params": {"name": "my_tool", "arguments": {}},
    })
    resp = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
    print("Result:", json.loads(resp.decode().strip()))

    proc.kill()
    await proc.wait()

asyncio.run(test_mcp())
```

## Verify Server Process State

Before sending the first message, always check if the process is still alive:

```python
if proc.returncode is not None:
    print(f"Server exited early with code: {proc.returncode}")
    return
```

## Key Facts

- The `mcp.server.stdio.stdio_server()` wraps `sys.stdin.buffer` and `sys.stdout.buffer` with `TextIOWrapper(encoding="utf-8")` and then `anyio.wrap_file()`.
- It reads line-by-line: `async for line in stdin:`.
- Each line is validated as `JSONRPCMessage.model_validate_json(line)`.
- Empty lines or `Content-Length` headers fail validation immediately.

## References

- `mcp` SDK source: `mcp/server/stdio.py` — the `stdin_reader()` coroutine.
