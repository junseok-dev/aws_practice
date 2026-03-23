import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import fs from "fs";
import path from "path";

const server = new Server(
  { name: "file-summary", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

// 툴 목록 정의
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "get_project_files",
      description: "프로젝트 파일 목록과 내용을 반환한다",
      inputSchema: {
        type: "object",
        properties: {
          dir: { type: "string", description: "읽을 폴더 경로" }
        },
        required: ["dir"]
      }
    }
  ]
}));

// 툴 실행
server.setRequestHandler("tools/call", async (req) => {
  const dir = req.params.arguments.dir;
  const files = fs.readdirSync(dir);

  const result = files.map((file) => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat.isFile()) {
      const content = fs.readFileSync(filePath, "utf-8").slice(0, 500);
      return `📄 ${file}\n${content}\n`;
    }
    return `📁 ${file}/`;
  }).join("\n---\n");

  return {
    content: [{ type: "text", text: result }]
  };
});

const transport = new StdioServerTransport();
await server.connect(transport);