import test from "node:test";
import assert from "node:assert/strict";
import { connectMcpServers } from "../src/mcp/portal-mcp-client.js";

test("connectMcpServers returns empty tools when servers list is empty or undefined", async () => {
  const result1 = await connectMcpServers(undefined);
  assert.deepEqual(result1.tools, []);
  await result1.close();

  const result2 = await connectMcpServers([]);
  assert.deepEqual(result2.tools, []);
  await result2.close();
});

test("connectMcpServers handles unreachable server gracefully without crashing", async () => {
  const result = await connectMcpServers(
    [
      {
        name: "portal",
        url: "http://127.0.0.1:59999/mcp/",
        type: "http",
        headers: { "X-Portal-MCP-Token": "fake" },
      },
    ],
    { connectTimeoutMs: 500 }
  );

  assert.deepEqual(result.tools, []);
  await result.close();
});
