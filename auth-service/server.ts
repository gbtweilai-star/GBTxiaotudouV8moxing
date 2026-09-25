import { auth } from "./auth.ts";
import { toNodeHandler } from "better-auth/node";
import { createServer } from "node:http";

const handler = toNodeHandler(auth);

createServer(async (req, res) => {
  if (req.url?.startsWith("/api/auth")) {
    return handler(req, res);
  }
  res.writeHead(404);
  res.end("not found");
}).listen(3000, "127.0.0.1", () => {
  console.log("✅ auth-service 已启动: http://127.0.0.1:3000");
});