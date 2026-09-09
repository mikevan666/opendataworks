import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { Type } from "@earendil-works/pi-ai";
import { logDiagnostic } from "../protocol/channel.js";
import type { McpServerConfig } from "../protocol/frames.js";

export interface McpBridgeResult {
  tools: unknown[];
  close: () => Promise<void>;
}

export async function connectMcpServers(
  servers: McpServerConfig[] | undefined,
  options?: { connectTimeoutMs?: number }
): Promise<McpBridgeResult> {
  const allTools: unknown[] = [];
  const clients: Client[] = [];
  const timeoutMs = options?.connectTimeoutMs ?? 10_000;

  for (const server of servers || []) {
    if (!server.url) {
      continue;
    }

    try {
      const url = new URL(server.url);
      const headers = server.headers || {};

      let transport;
      if (server.type === "sse") {
        transport = new SSEClientTransport(url, {
          eventSourceInit: { headers } as never,
          requestInit: { headers },
        });
      } else {
        transport = new StreamableHTTPClientTransport(url, {
          requestInit: { headers },
        });
      }

      const client = new Client(
        { name: "opendataworks-pi-cell", version: "0.1.0" },
        { capabilities: {} }
      );

      // Connect with timeout
      await Promise.race([
        client.connect(transport),
        new Promise((_, reject) =>
          setTimeout(() => reject(new Error(`Connection to MCP server '${server.name}' timed out after ${timeoutMs}ms`)), timeoutMs)
        ),
      ]);

      clients.push(client);

      const toolsList = await client.listTools();
      logDiagnostic(`MCP server '${server.name}' connected, discovered ${toolsList.tools.length} tools`);

      for (const mcpTool of toolsList.tools) {
        const toolName = mcpTool.name;
        const toolDescription = mcpTool.description || "";
        const inputSchema = (mcpTool.inputSchema as Record<string, unknown>) || Type.Object({});

        allTools.push({
          name: toolName,
          label: toolName,
          description: toolDescription,
          parameters: inputSchema,
          execute: async (_toolCallId: string, params: Record<string, unknown>) => {
            try {
              const res = await client.callTool({
                name: toolName,
                arguments: params || {},
              });

              const content = Array.isArray(res.content)
                ? res.content.map((item: any) => {
                    if (item.type === "text") {
                      return { type: "text" as const, text: String(item.text ?? "") };
                    }
                    if (item.type === "image") {
                      return {
                        type: "image" as const,
                        data: item.data,
                        mimeType: item.mimeType,
                      };
                    }
                    return { type: "text" as const, text: JSON.stringify(item) };
                  })
                : [{ type: "text" as const, text: String(res.content ?? "") }];

              return {
                content,
                isError: Boolean(res.isError),
              };
            } catch (err: unknown) {
              const errMsg = err instanceof Error ? err.message : String(err);
              logDiagnostic(`Tool '${toolName}' call failed: ${errMsg}`);
              return {
                content: [{ type: "text" as const, text: `MCP tool call error: ${errMsg}` }],
                isError: true,
              };
            }
          },
        });
      }
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      logDiagnostic(`Failed to connect to MCP server '${server.name}' at ${server.url}: ${message}`);
    }
  }

  const close = async () => {
    for (const client of clients) {
      try {
        await client.close();
      } catch (err: unknown) {
        logDiagnostic(`Error closing MCP client: ${err instanceof Error ? err.message : String(err)}`);
      }
    }
  };

  return { tools: allTools, close };
}
