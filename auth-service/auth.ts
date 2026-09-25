import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export const auth = betterAuth({
  database: prismaAdapter(prisma, {
    provider: "sqlite",
  }),
  emailAndPassword: {
    enabled: true,
  },
  appName: "GBT小土豆V8",
  baseURL: process.env.BETTER_AUTH_URL || "http://127.0.0.1:3000",
  secret: process.env.BETTER_AUTH_SECRET || "change-me",
});