// 形态 B · 单模块 Worker：gbt-c08-memory-local（第 8 号）
// 生成物，不要手改。真源：deploy/cloud-10/mesh.json
// 口径：本形态 = 真互通、各算各的（isolate 之间不共享 CPU）。
// 路径口径：件在 deploy/cloud-10/modules/<id>/src/index.js ⇒ 公共件在 ../../../src/
import { MODULES, createState } from "../../../src/modules.js";
import { MESH, OP_GATES } from "../../../src/mesh.generated.js";

const ID = "gbt-c08-memory-local";
const PEER_BINDINGS = ["PEER_01", "PEER_02", "PEER_03", "PEER_04", "PEER_05", "PEER_06", "PEER_07", "PEER_09", "PEER_10"];

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      const state = createState();
      const ops = MODULES[ID].ops;
      const body = ops.status ? await ops.status({ env, state, self: ID }) : { op: "ping", module: ID };
      return Response.json({ module: ID, seq: 8, ok: true, body, peers_bound: PEER_BINDINGS.filter((b) => env[b]).length, peers_declared: PEER_BINDINGS.length });
    }
    if (url.pathname === "/peers") {
      const bound = PEER_BINDINGS.filter((b) => env[b]);
      const rows = [];
      for (const b of bound) {
        try {
          const r = await env[b].fetch("https://peer/health");
          rows.push({ binding: b, ok: r.ok });
        } catch (e) {
          rows.push({ binding: b, ok: false, error: String(e && e.message || e) });
        }
      }
      return Response.json({ module: ID, declared: PEER_BINDINGS.length, bound: bound.length, reached: rows.filter((r) => r.ok).length, rows });
    }
    const parts = url.pathname.split("/").filter(Boolean);
    if (parts[0] === "rpc" && parts.length >= 3 && parts[1] === ID) {
      const state = createState();
      const op = parts[2];
      const gate = (OP_GATES[ID] || {})[op] || "none";
      if (gate !== "none") {
        return Response.json({ denied: true, missing_scopes: [gate], note: "形态 B 的门在 09 号那位身上；本单模块件不自带授权。" }, { status: 403 });
      }
      const fn = MODULES[ID].ops[op];
      if (!fn) return Response.json({ error: "unknown op", op }, { status: 404 });
      let args = {};
      try { args = await request.json(); } catch (e) {}
      return Response.json(await fn({ env, state, self: ID }, args));
    }
    return Response.json({ module: ID, seq: 8, routes: ["GET /health", "GET /peers", "POST /rpc/gbt-c08-memory-local/<op>"] });
  },
};
