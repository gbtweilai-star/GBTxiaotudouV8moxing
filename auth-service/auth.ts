import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

// 🔴 2026-09-26 修：原来缺失时静默回退到公开可知的 "change-me" —— 任何会话 cookie 都能被
//    伪造（fail-open 型凭据缺陷）。现在缺配置就拒绝启动（fail-closed）。
const secret = process.env.BETTER_AUTH_SECRET;
if (!secret || secret === "change-me") {
  throw new Error(
    "BETTER_AUTH_SECRET 未配置（或仍是占位值 change-me）—— 拒绝用可伪造的签名密钥启动"
  );
}

export const auth = betterAuth({
  database: prismaAdapter(prisma, {
    provider: "sqlite",
  }),
  emailAndPassword: {
    enabled: true,
  },
  appName: "GBT小土豆V8",
  baseURL: process.env.BETTER_AUTH_URL || "http://127.0.0.1:3000",
  secret,
});