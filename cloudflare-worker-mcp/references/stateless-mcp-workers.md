# Stateless MCP on Cloudflare Workers (validated 2026-08-20)

Replicating a deployed MCP worker from a bundle is non-trivial; this captures
the working stateless pattern and the debugging path that led to it.

## The working pattern (SDK ^1.30 on Workers)

```ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { object, string, number, optional, picklist, parse, type GenericSchema } from "valibot";
import { toJsonSchema } from "@valibot/to-json-schema";

// registerTools(server, tools) — valibot object({...}) → toJsonSchema(...) →
// parse(...) in CallToolRequestSchema (see elysia2-valibot-mcp.md)

export default {
  fetch(request: Request, env: Env) {
    currentEnv = env;
    const url = new URL(request.url);
    if (url.pathname === "/mcp") return handleMcp(request);
    return new Response("not found", { status: 404 });
  },
} satisfies ExportedHandler<Env>;

function handleMcp(request: Request): Promise<Response> {
  // FRESH Server + stateless transport per HTTP request — this is the
  // stateless mode that lets plain JSON-RPC POSTs work without sessions.
  const server = new Server(
    { name: "investment-vault", version: "0.1.0" },
    { capabilities: { tools: {} } },
  );
  registerTools(server, tools);
  const transport = new WebStandardStreamableHTTPServerTransport({
    enableJsonResponse: true,
    sessionIdGenerator: undefined,  // stateless: no Mcp-Session-Id, no DO
  });
  return server.connect(transport).then(() => transport.handleRequest(request));
}
```

Client flow that works (no session dance at all):
```
POST /mcp {"jsonrpc":"2.0","id":1,"method":"initialize",...}   → 200
POST /mcp {"jsonrpc":"2.0","id":3,"method":"tools/list"}        → 200
POST /mcp {"jsonrpc":"2.0","id":4,"method":"tools/call",...}    → 200
```
No `Mcp-Session-Id` header needed anywhere in stateless mode.

## Debugging path that produced it (3 failed attempts)

1. **Shared module-scope Server** (state persists across requests) +
   per-request transport → Error 1101: `server.connect(transport)` crashes on
   the 2nd request (the first transport's connection state pollutes the next).
   `get_company` worked without init; after init everything 500'd.
2. **Fresh Server per request + stateful transport** (`sessionIdGenerator: () => uuidv7()`,
   DO eventStore) → 400 `Bad Request: Server not initialized`: the SDK requires
   an initialize/initialized handshake tied to a session; a fresh Server per
   request loses that state, and notifications sent without a session header
   were rejected.
3. **Fresh Server per request + stateless transport** (`sessionIdGenerator:
   undefined`) → 17/17 tools OK. ✅

The live worker (deployed from another machine) used an even newer SDK API —
`server.receive(body, { sessionId: "stateless", sessionInfo: {...} })` inside a
Hono `app.post("/mcp")` — which 1.30.0 does not export. The pattern above is
the equivalent with the SDK version actually in the repo.

## Replicating a live worker from its bundle

When the deployed worker differs from repo code (deployed from another
machine), reverse-engineer from the live artifact:

1. `curl -s "https://api.cloudflare.com/client/v4/accounts/$ACCT/workers/scripts/<name>" \
   -H "Authorization: Bearer $TOK" -H "Content-Type: text/javascript"` — returns
   the **bundle** (multipart; first part is `worker.js`).
2. `tools/list` via POST JSON-RPC gives exact tool names, descriptions, and
   inputSchema (copy verbatim).
3. Probe every tool with representative args to capture response shapes
   (list rows vs `{person, positions}` vs plain string for not-found).
4. `grep -oE 'sessionId: "stateless"'` on the bundle reveals the transport mode.
5. Check D1 row counts vs the seed script's statement count to detect foreign
   imports (e.g. seed has 962 INSERTs but D1 has 495 rows with different
   created_at timestamps → someone else imported corrupt data).

## Probing a Workers MCP endpoint from Python

```python
import json, urllib.request
URL = "https://...workers.dev/mcp"
HDRS = {"Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}
def call(method, params=None, id=None):
    msg = {"jsonrpc": "2.0", "method": method}
    if id is not None: msg["id"] = id
    if params is not None: msg["params"] = params
    req = urllib.request.Request(URL, data=json.dumps(msg).encode(), headers=HDRS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())
```
Pitfalls:
- **`Python-urllib` UA gets 403** from Cloudflare — spoof a browser UA.
- **JSON-RPC notifications must NOT carry an `id`**; the SDK rejects them with
  400 if they do.
- In stateful mode, every request needs `Mcp-Session-Id` (from the initialize
  response header); stateless mode needs none.

## R2 notes listing (list_notes / get_note)

Notes live in R2, NOT D1 (user preference: "Note di R2. Shareholder history
d1"). The D1 `notes` table holds metadata only:
```ts
const listed = await currentEnv!.FILES.list({ prefix: "notes/" });
return listed.objects.map((o) => ({ key: o.key, size: o.size, uploaded: o.uploaded.toISOString() }));
// get_note: const obj = await currentEnv!.FILES.get(key); return { key, size, content: await obj.text() };
```
