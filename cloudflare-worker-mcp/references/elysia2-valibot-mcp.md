# Elysia 2 beta + low-level MCP SDK + Valibot (no zod, no elysia-mcp)

Session-proven stack after the user asked to replace zod with Valibot
("jangan pakai zod. pakai valibot"). Dropping zod forces dropping
`elysia-mcp` too (it imports zod). Raw `@modelcontextprotocol/sdk` +
`@valibot/to-json-schema` is smaller and has no peer-conflict.

## Measured bundle impact

| Variant | gzip bundle |
|---|---|
| Elysia + elysia-mcp + zod (17 tools) | ~405 KiB |
| Elysia + raw SDK + valibot (17 tools) | ~247 KiB |
| REST-only worker (Elysia, TypeBox) | ~150 KiB |

## Imports

```ts
import { Elysia } from "elysia";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { v7 as uuidv7 } from "uuid";
import { object, string, number, optional, picklist, parse, type GenericSchema } from "valibot";
import { toJsonSchema } from "@valibot/to-json-schema";
```

Note: MCP SDK server subpaths use `.js` extension and do NOT import zod —
they accept whatever `inputSchema` JSON you pass from `toJsonSchema(...)`.

## Tool registration (Valibot → JSON Schema)

```ts
interface McpTool {
  name: string;
  description: string;
  input: GenericSchema<Record<string, unknown>>;
  handler: (args: Record<string, unknown>) => Promise<unknown>;
}

function registerTools(server: Server, tools: McpTool[]) {
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: tools.map((t) => ({
      name: t.name,
      description: t.description,
      inputSchema: toJsonSchema(t.input) as Record<string, unknown>,
    })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const tool = tools.find((t) => t.name === request.params.name);
    if (!tool) return { content: [{ type: "text", text: `Unknown tool: ${request.params.name}` }], isError: true };
    try {
      const args = parse(tool.input, request.params.arguments ?? {});
      const result = await tool.handler(args as Record<string, unknown>);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      return { content: [{ type: "text", text: `Invalid arguments: ${String(err)}` }], isError: true };
    }
  });
}
```

Valibot building blocks: `object({ ticker: string("Ticker code, e.g. BBRI") })`,
`optional(number("Year"))` for defaults, `picklist(["Annual","TW"])` for enums
— valibot has NO `enum`; use `picklist`.

## Worker mount (per-request Server + transport)

```ts
const app = new Elysia();
app.all("/mcp", async ({ request }) => {
  const server = new Server(
    { name: "investment-vault", version: "0.1.0" },
    { capabilities: { tools: {} } },
  );
  registerTools(server, tools);
  const transport = new WebStandardStreamableHTTPServerTransport({
    enableJsonResponse: true,          // REQUIRED for plain HTTP/JSON clients
    sessionIdGenerator: () => uuidv7(),
    eventStore: new DoEventStore(() => currentEnv!.MCP_SESSIONS),
  });
  await server.connect(transport);
  return transport.handleRequest(request);
});

export default { fetch(request: Request, env: Env) { currentEnv = env; return app.fetch(request); } };
```

The Server is constructed fresh per request (transport is per-request).

## Elysia 2.0.0-beta.5 API differences (vs 1.x)

Read from `node_modules/elysia/dist/base.d.ts`, `error.d.ts`, `context.d.ts`
(the package no longer has a flat `index.d.ts` at dist root).

- `.error(fn)` replaces `.onError(code, handler)`. Signature:
  `.error(({ error, set }) => ...)` — no `code` string.
- Error classes importable from `"elysia"`: `ValidationError` (status 422),
  `ParseError` (400), `NotFound` (404). Use `instanceof`.
- Route registration order changed: `post(path, hook, fn)` — the schema hook
  comes BEFORE the handler. v1 was `post(path, fn, hook)`.
  ```ts
  .post("/groups", { body: t.Object({ name: t.String({ minLength: 1 }) }) }, ({ body, set }) => {...})
  ```
- GET routes without schema still take `(path, fn)` as usual.
- Validation for REST bodies uses TypeBox `t.*` (Elysia 2 built-in) — only
  MCP tool schemas use Valibot.

## Two-worker split (MCP + REST API)

User wanted the MCP "opened via api too". Decision: two separate Workers in
one monorepo — `apps/mcp` (MCP server) + `apps/api` (REST). Both bind the same
D1/KV/R2; `apps/mcp` additionally binds the Durable Object.

Shared query layer lives in `packages/db` (`src/queries.ts`) — each function
takes `db: D1Database` as first arg:

```ts
export async function getTickerProfile(db: D1Database, ticker: string) { const d = drizzle(db); ... }
```

Both apps import `{ getTickerProfile, ... } from "@investment-vault/db"`.
Deploy = `wrangler deploy` in each app dir (mcp first, then api).
