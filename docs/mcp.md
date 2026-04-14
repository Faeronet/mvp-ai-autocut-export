# MCP

HTTP endpoint: `POST http://localhost:8090/mcp` with JSON-RPC body.

Headers:
- `Mcp-Protocol-Version: 2024-11-05`
- `Mcp-Session-Id: <optional; issued on first response>`

Origin policy: requests with `Origin` must target allowed hosts (`MCP_ALLOWED_HOSTS`).

Example `initialize`:

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"cli","version":"0"}}}
```

Stdio mode: `mcp --stdio` reads one JSON-RPC object per line from stdin.
