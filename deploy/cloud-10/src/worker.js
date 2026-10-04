// GBT小土豆V8 · 10 云插件拼接网 · Worker 入口（形态 A：10 模块同一 isolate）
// 开发者：自由的风 · 守护者：公主土豆 · 禁止删除
//
// 这份 worker.js 同时能被云端 wrangler 和本机 Node 直接跑：
//   云端 = 真部署；本机 = 只做形状验收（拼接通不通、门开不开），不替代真云读数。
//
// 路由：
//   GET  /              路由索引
//   GET  /mesh          形态 + 10 模块职责 + 声明边数
//   GET  /edges         90 条边矩阵 + 自环/对称/条数三项核对 + 已观测边数
//   GET  /health        逐模块探活（10/10 才算整齐）
//   POST /rpc/<id>/<op> 单次调用（先过 09 号门）
//   POST /mesh/full-ping 每位与其余 9 位互 ping ⇒ 记满 90 条边
//   POST /admin/grant   发授权：只有主人令牌能开，AI 没有旁路

import { MODULES, createState, SCOPES, NS_PREFIX, withIdentity } from "./modules.js";
import { MESH, MODULE_IDS, OP_GATES, PEERS } from "./mesh.generated.js";

const JSON_HEADERS = { "content-type": "application/json; charset=utf-8" };

// ══════════════════════════════════════════════════════════════════════════
// 🔴 2026-09-25 修：转发前把 OpenAI **内容块数组** 拍平成字符串
// ══════════════════════════════════════════════════════════════════════════
// 病根（**上游 502 回包逐字**，不是推断）：
//   5006: oneOf at '/' not met … required properties at '/' are 'prompt',
//     Type mismatch of '/messages/0/content', 'array' not in 'string'   ← 0..44 条全是
//     Type mismatch of '/messages/45/content', 'string' not in 'null'
//   上游 `@cf/openai/gpt-oss-120b`（Workers AI）**只认 `content` 是字符串**，
//   而 DSH harness 按 OpenAI 多模态规范发的是 `content: [{type:"text",text:"…"}, …]`。
//   本文件原来把 `messages` **原样透传** ⇒ 凡是带块数组的请求全被上游 schema 拒掉
//   ⇒ **她一句话都答不出来**（与配额那个 4006 是两回事，别混）。
// 修法：逐条归一 —— 数组拍平成文本；`null`（带 tool_calls 的 assistant 消息）转空串；
//   图片块在本上游是纯文本模型，落一行**确定性占位文本**（不静默丢，也不假装看得见）。
//   `tool_calls` / `tool_call_id` / `name` 原样保留（丢了下游工具调用就断了）。
function normalizeMessages(msgs) {
  const out = [];
  for (const m of Array.isArray(msgs) ? msgs : []) {
    if (!m || typeof m !== "object") continue;
    const role = String(m.role || "user");
    let content = m.content;
    if (content == null) {
      content = "";
    } else if (Array.isArray(content)) {
      const bits = [];
      for (const p of content) {
        if (p == null) continue;
        if (typeof p === "string") { bits.push(p); continue; }
        const t = String(p.type || "");
        if (t === "text" || t === "input_text") bits.push(String(p.text || ""));
        else if (t === "image_url" || t === "input_image") bits.push("[图片]");
        else bits.push(String(p.text || ""));
      }
      content = bits.join("\n");
    } else {
      content = String(content);
    }
    const row = { role, content };
    if (Array.isArray(m.tool_calls) && m.tool_calls.length) row.tool_calls = m.tool_calls;
    if (m.tool_call_id) row.tool_call_id = m.tool_call_id;
    if (m.name) row.name = m.name;
    out.push(row);
  }
  return out;
}
// 🔴 控制面（授权）与数据面（模块的用户键）**必须分前缀**。
//    上一版把授权写进 `mesh10/grants/owner.json` —— 那正是模块自己的命名空间，
//    于是 08 号的 `list` 把**内部授权文件**当用户键列了出来（本机验收的负控当场逮到：
//    列出的键里多了 `grants/owner.json`）。更要紧的是 `MEM` 绑的是主人**已有**的 KV，
//    把控制面状态混进主人的数据命名空间，与"往主人 D1 里写我们的表"是同一类错。
const CTL_PREFIX = "mesh10-ctl/";
const GRANTS_KEY = CTL_PREFIX + "grants.json";
const GRANTS_TTL_MS = 5000;

function json(body, status = 200) {
  return new Response(JSON.stringify(body, null, 2), { status, headers: JSON_HEADERS });
}

// 🔴 授权必须**活过重启**。这是主人那条红线（「限制全改人工授权」）的前提：
//    授权要是只躺在 isolate 内存里，一次重启/重新部署就把主人发的授权**悄悄抹掉**，
//    于是所有受门动作重新变成拒绝 —— 主人会以为"我明明授权过了"。
//    实测证据（2026-09-25）：重启后 `get` 直接 403 缺 filesystem_read。
//    ⇒ 授权落 KV（`mesh10/grants/owner.json`），每个 isolate 最多 5 秒回读一次。
//    ⚠️ KV 最终一致：刚发完授权别的副本可能还要等几秒，这条边界要如实写在读数里。
// 授权有两个来源，**必须分开记**（否则撤不掉）：
//   ① 配置授权 `GRANTED_SCOPES`（写在 wrangler.toml 里 ⇒ 看得见、可审计、**删掉即撤**）
//   ② 运行时授权 `/admin/grant`（要主人令牌，落 KV，活过重启）
// 生效集 = 两者并集。**撤权就撤得干净**：删配置那一行、或清 KV —— 不会互相残留。
function configGrants(e) {
  const raw = String((e && e.GRANTED_SCOPES) || "");
  return raw.split(",").map((s) => s.trim()).filter((s) => SCOPES.includes(s));
}

function refreshEffective(state) {
  state.grants = new Set([...(state.configGrants || []), ...(state.runtimeGrants || [])]);
}

async function loadGrants(e, state, force) {
  state.configGrants = configGrants(e);
  if (!e.MEM) {
    state.grantsSink = "isolate-memory";
    refreshEffective(state);
    return;
  }
  const fresh = state.grantsLoadedAt && Date.now() - state.grantsLoadedAt < GRANTS_TTL_MS;
  if (fresh && !force) {
    refreshEffective(state);
    return;
  }
  try {
    const raw = await e.MEM.get(GRANTS_KEY);
    if (raw) {
      const arr = JSON.parse(raw);
      if (Array.isArray(arr)) state.runtimeGrants = arr.filter((x) => SCOPES.includes(x));
    }
  } catch (err) {
    state.grantsSink = "kv(读失败)";
    refreshEffective(state);
    return;
  }
  state.grantsSink = "kv";
  state.grantsLoadedAt = Date.now();
  refreshEffective(state);
}

async function saveGrants(e, state) {
  const list = [...(state.runtimeGrants || [])];   // 只落**运行时**那部分：配置那份归配置文件管
  if (!e.MEM) return "isolate-memory";
  try {
    await e.MEM.put(GRANTS_KEY, JSON.stringify(list));
    state.grantsSink = "kv";
    return "kv";
  } catch (err) {
    return "isolate-memory(写KV失败)";
  }
}

export function createMesh(env, sharedState) {
  const state = sharedState || createState();
  const e = env || {};

  async function dispatch(id, op, args, from) {
    if (!MODULE_IDS.includes(id)) return { ok: false, code: 404, body: { error: "unknown module", id } };
    if (from && from !== id) state.calls.push({ from, to: id, op });
    if (op === "ping") {
      return { ok: true, code: 200, body: { op: "ping", module: id, seq: MESH.modules.find((m) => m.id === id).seq, from: from || null } };
    }
    const mod = MODULES[id];
    if (!mod || !mod.ops[op]) return { ok: false, code: 404, body: { error: "unknown op", id, op, available: Object.keys((mod && mod.ops) || {}) } };

    const gate = (OP_GATES[id] || {})[op] || "none";
    if (gate !== "none") {
      await loadGrants(e, state, false);
      const verdict = await dispatch("gbt-c09-policy-guard", "evaluate", { scope: gate }, id);
      const v = verdict.body || {};
      if (!v.allowed) {
        return {
          ok: false,
          code: 403,
          body: {
            denied: true,
            id,
            op,
            missing_scopes: v.missing_scopes || [gate],
            scope: gate,
            how_to_grant: "只能主人在终端发放；AI 没有旁路。",
          },
        };
      }
    }

    state.counters.rpc++;
    const ctx = {
      env: e,
      state,
      self: id,
      peers: (x) => PEERS[x] || [],
      // 🔴 两个调用口必须分清（这是本轮逮到的系统性 bug 的根因）：
      //   `call`  = 完整信封 {ok, code, body} —— 只用来判"通没通"（扇出、跨模块调用记录）。
      //   `callBody` = **只要本体** —— 凡是要读对方字段的，一律用这个。
      //   原来所有读字段的地方都拿信封当本体 ⇒ 字段全 undefined ⇒
      //   分支"碰巧"走进了未接线那条（看着对，其实是因为读数取错了层）；
      //   一旦真接了容器，它**仍然**会拒 —— 功能永远不可能生效。
      call: (pid, pop, pargs) => dispatch(pid, pop, pargs, id),
      callBody: async (pid, pop, pargs) => (await dispatch(pid, pop, pargs, id)).body,
      record: (row) => state.calls.push(row),
    };
    const body = await mod.ops[op](ctx, args || {});
    return { ok: true, code: 200, body };
  }

  function edgesReport() {
    const directed = [];
    for (const id of MODULE_IDS) for (const p of PEERS[id] || []) directed.push([id, p]);
    const selfLoops = directed.filter(([a, b]) => a === b).length;
    const set = new Set(directed.map(([a, b]) => a + ">" + b));
    const asymmetric = directed.filter(([a, b]) => !set.has(b + ">" + a)).map(([a, b]) => a + ">" + b);
    const observed = state.calls.filter((c) => c.from && c.to && c.from !== c.to);
    const observedSet = new Set(observed.map((c) => c.from + ">" + c.to));
    return {
      rule: MESH.edges.rule,
      form: MESH.form,
      declared: {
        directed: directed.length,
        expecting: MESH.edges.directed_expected,
        undirected: directed.length / 2,
        self_loops: selfLoops,
        asymmetric: asymmetric.length,
        asymmetric_samples: asymmetric.slice(0, 5),
        per_module: MODULE_IDS.map((id) => ({ id, peers: (PEERS[id] || []).length })),
      },
      observed: {
        calls: observed.length,
        distinct_edges: observedSet.size,
        expecting: MESH.edges.directed_expected,
        missing: directed.map(([a, b]) => a + ">" + b).filter((k) => !observedSet.has(k)).length,
      },
      verdict: {
        shape_ok: directed.length === MESH.edges.directed_expected && selfLoops === 0 && asymmetric.length === 0,
        splice_exercised: observedSet.size === MESH.edges.directed_expected,
      },
      boundary: "互通 90 条是接线读数，不是算力读数：它不增加一个核、不增加一字节显存。",
    };
  }

  async function fullPing() {
    let ok = 0;
    const bad = [];
    for (const id of MODULE_IDS) {
      for (const p of PEERS[id] || []) {
        const r = await dispatch(p, "ping", {}, id);
        if (r.ok) ok++;
        else bad.push(id + ">" + p);
      }
    }
    return { tried: MODULE_IDS.length * (MODULE_IDS.length - 1), ok, failed: bad.length, failed_samples: bad.slice(0, 5) };
  }

  async function health() {
    const rows = [];
    for (const m of MESH.modules) {
      const op = (MODULES[m.id] && MODULES[m.id].ops.status) ? "status" : "ping";
      const r = await dispatch(m.id, op, {}, null);
      rows.push({ seq: m.seq, id: m.id, op, ok: r.ok, wired: r.body ? r.body.wired : undefined, reading: r.body ? r.body.reading : undefined });
    }
    return { modules: rows.length, alive: rows.filter((r) => r.ok).length, rows };
  }

  async function handle(request) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";
    const method = request.method.toUpperCase();

    // 🔴 先回读授权，**每条路由都读**（isolate 内最多 5 秒一次）。
    //    上一版只在"受门 op"里回读 ⇒ `grants` 这个读数自己报「在册 0 条」，
    //    而同一时刻门其实认这份授权、放行了写读 —— **读数与事实打架**。
    //    红线是"授权不许被悄悄抹掉"，那读数就必须先跟事实对齐。
    await loadGrants(e, state, false);

    // ── OpenAI 兼容面（主人 2026-09-25 令「把大模型切换到 GBT小土豆V8 试试」）──────
    // 为什么必须有：拼接网自家说的是 `/rpc/<模块>/<op>`，而"切换模型"要的是**客户端认得的协议**
    // （DSH 的模型适配器就是 OpenAI 兼容那一套）。所以这里把 01 号包成
    // `GET /v1/models` + `POST /v1/chat/completions`。
    // ✅ 流式**已实现**（SSE 分片现测通过 —— 见 L313 起的分支与 L274 的 `stream: true` 读数）。
    // 🔴 2026-09-25 更正：本行原文写的是「**流式还没实现** ⇒ 要 `stream:true` 的一律如实 501」，
    //    而九行之下 L274 同时写着「已实现（SSE 分片现测通过）」—— **同一函数里自己打自己**。
    //    代码事实站在 L274 那边（L313 起真有 SSE 分支）。**声明必须跟着事实走。**
    //    工具调用（tools）**原样透传**给上游，回包里的 tool_calls 也**原样带回来**，
    //    但"上游到底支不支持"要**量出来**再说，不许我先替它表态。
    if (method === "GET" && path === "/v1/models") {
      const _gwAuth = String(e.GW_AUTH || "");
      return json({
        object: "list",
        data: [{ id: "gbt-potato-v8", object: "model", created: 0, owned_by: "GBT小土豆V8" }],
        gbt: {          upstream: e.WORKERS_AI_MODEL || null,
          // 🔴 2026-09-25 **修「会说谎的指示灯」**（实测，不是理论风险）：
          //    原来这里是 `Boolean(e.LLM_ENDPOINT)` —— 只要**配置**了 LLM_ENDPOINT
          //    就报「权重是我们的」。而本文件 `e.AI.run` **只有一处**
          //    （L329 流式路径，实测 grep），`LLM_ENDPOINT` **从来没有任何分支**
          //    ⇒ 流量照旧烧 Workers AI 的神经元，读数却翻成 `true`。
          //    **配置 ≠ 接线。** 现在按事实报：
          //    **按「路径」分开报**（2026-09-25 自纠）：非流式那条转给 `gbt-c01-llm-gateway`，
          //    模块里**真实现了**自托管分支（`callOpenAI(LLM_ENDPOINT)`，报 weights_ours=true）；
          //    流式那条在本文件里**没有**该分支，恒走 Workers AI。
          //    ⇒ 一个扁平的 `weights_ours` 说不清这件事，所以拆成两条路各报各的。
          weights_ours: false,
          llm_endpoint_wired: { non_stream: Boolean(e.LLM_ENDPOINT), stream: false },
          llm_endpoint_note: e.LLM_ENDPOINT
            ? "已配 LLM_ENDPOINT：**非流式**走自托管（模块里有分支）；**流式**没有分支，仍走 Workers AI"
            : "未配 LLM_ENDPOINT ⇒ 两条路都走 Workers AI",
          identity: "GBT小土豆V8",
          stream: true,           // 已实现（SSE 分片现测通过）
          tools: true,            // 已实现（tools 原样转发 + tool_calls 原样带回，含第二轮工具结果）
          // 网关鉴权：单 key（GW_AUTH），不是多令牌；/v1/models 公开不校验，/v1/chat 要 Bearer。
          // 🔴 2026-10-04 收紧（24h 审查实证）：**没设 GW_AUTH ⇒ /v1/chat 与 /rpc fail-closed 拒服务**，
          //    不再"没设就不校验"（那等于公开 workers.dev 端点静默裸奔）。本地开发请显式设 GW_AUTH。
          auth: _gwAuth
            ? ("网关鉴权已开（GW_AUTH 单 key · /v1/models 公开 · /v1/chat 要 Bearer）")
            : "🔴 未设 GW_AUTH ⇒ /v1/chat 与 /rpc fail-closed 拒服务（2026-10-04 起，不再静默放行）",
          auth_scope: {
            chat: _gwAuth ? "bearer" : "fail-closed",
            rpc: _gwAuth ? "bearer" : "open(dev)",
            models: "public",
            scheme: "GW_AUTH Bearer",
          },
        },
      });
    }
    if (method === "POST" && path === "/v1/chat/completions") {
      // 网关鉴权（**统一单 key · GW_AUTH**）。2026-10-03 简化：不再用多令牌，
      // 所有消费方共享同一把 GW_AUTH，改一次即可轮换。
      // 常数时间比较：两边各做 SHA-256 再 timingSafeEqual，消掉时序侧信道。
      // 🔴 2026-10-04 收紧（24h 审查实证）：**没设 GW_AUTH ⇒ fail-closed（503）**——
      //    原实现"没设就跳过校验"，在公开 workers.dev 端点上等于静默裸奔。
      const _gwAuth = String(e.GW_AUTH || "");
      if (!_gwAuth) {
        return json({
          error: {
            message: "网关密钥未配置（GW_AUTH 未设）⇒ 本端点 fail-closed 拒服务。" +
              "部署端请：wrangler secret put GW_AUTH --config wrangler.toml",
            type: "configuration_error",
          },
          gbt: { scheme: "Bearer GW_AUTH", fail_closed: true },
        }, 503);
      }
      {
        const got = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "").trim();
        const enc = new TextEncoder();
        const [a, b] = await Promise.all([
          crypto.subtle.digest("SHA-256", enc.encode(got)),
          crypto.subtle.digest("SHA-256", enc.encode(_gwAuth)),
        ]);
        const ta = new Uint8Array(a), tb = new Uint8Array(b);
        let ok = false;
        if (crypto.subtle.timingSafeEqual) ok = crypto.subtle.timingSafeEqual(ta, tb);
        else { let diff = 0; for (let i = 0; i < ta.length; i++) diff |= ta[i] ^ tb[i]; ok = diff === 0; }
        if (!ok) {
          return json({
            error: { message: "Authorization 不对（本端点已开启网关鉴权）", type: "authentication_error" },
            gbt: { scheme: "Bearer GW_AUTH" },
          }, 401);
        }
      }
      let body = {};
      try {
        body = await request.json();
      } catch (err) {
        return json({ error: { message: "body 不是 JSON", type: "invalid_request_error" } }, 400);
      }
      // 🔴 **先算变量，再做分支**：上一版把流式分支写在 `const msgs` 声明之前 ⇒
      //    命中暂时性死区（TDZ）⇒ 云端直接 1101（Worker 抛异常）。
      //    与 modules.js 那次是同一类错（那次被 try/catch 吞成了"模型没答"）。
      const msgs = Array.isArray(body.messages) ? body.messages : [];
      if (!msgs.length) return json({ error: { message: "messages 为空", type: "invalid_request_error" } }, 400);
      // ⚠️ 2026-09-25 **自纠（第一版我放错了位置）**：我把「LLM_ENDPOINT 未接线」的守卫
      //    放在了**全局**，那是错的 —— `modules.js`（`gbt-c01-llm-gateway`）里
      //    **自托管分支是真实现了的**（`callOpenAI(ctx.env, ctx.env.LLM_ENDPOINT, …)`，
      //    并如实报 `weights_ours: true`）。
      //    ⇒ 真正缺分支的**只有本文件的流式路径**（非流式那条转给模块，是认 LLM_ENDPOINT 的）。
      //    全局守卫会把**一条本来能用的配置**一起拦掉。守卫已下移到流式分支内。
      if (body.stream === true) {
        // 🔴 流式：客户端（含 DSH 的适配器）多数默认要 SSE，所以这条必须真做出来，
        //    不然"切换过去"会当场失败 —— 而不是模型不行。
        //    口径：**门照样要过**（external_llm）；SSE 分片按 OpenAI 的 delta 形状发。
        const verdict = await dispatch("gbt-c09-policy-guard", "evaluate", { scope: "external_llm" }, null);
        if (!(verdict.body || {}).allowed) {
          return json({ error: { message: "缺授权 external_llm", type: "permission_error" }, gbt: { missing_scopes: (verdict.body || {}).missing_scopes } }, 403);
        }
        // 🔴 fail-closed（2026-09-25 · 只在这条路上）：配了 `LLM_ENDPOINT` 却走流式时，
        //    **不许静默烧 Workers AI** —— 那正是「配了就算自己权重」的读数来源。
        //    非流式那条转给模块、模块里**有**自托管分支；流式这条在本文件里**没有**。
        //    ⇒ 要么补上流式的自托管分支，要么让调用方走非流式；这里如实 501，不假装。
        if (e.LLM_ENDPOINT) {
          return json({
            error: {
              message: "流式路径没有自托管分支：LLM_ENDPOINT 已配，但 `stream:true` 这条"
                       + "恒走 Workers AI（非流式那条走 `gbt-c01-llm-gateway`，是认 LLM_ENDPOINT 的）",
              type: "not_implemented",
            },
            gbt: {
              configured: "LLM_ENDPOINT", wired: { non_stream: true, stream: false },
              how_to_fix: "补流式自托管分支；或用 stream:false 让请求走模块那条已接线的路",
              why: "静默走 Workers AI 会烧免费神经元、还让人以为走的是自建端点",
            },
          }, 501);
        }
        const wid = (body.model && body.model !== "gbt-potato-v8") ? body.model : e.WORKERS_AI_MODEL;
        // 🔴 2026-09-25 **改错误分档**：这两条原来都报 `502 / upstream_error` —— **归错了**。
        //    它们根本不是上游故障：一条是**绑定没配**，一条是**模型 id 没填**，
        //    都是**本地配置缺失**，而且**一次上游请求都没发出去**。
        //    用 502（Bad Gateway）报"配置没填"，读起来像远端坏了 ——
        //    与 `5021`（上下文超窗）被归成通用 502 是**同一类病**：真因被通用档吞掉。
        //    ⇒ 改报 `configuration_error` + HTTP 500（服务端自身没配好，不是客户端的问题、
        //      也不是上游的问题），并给出可机读的 `how_to_fix`。
        if (!e.AI) {
          return json({
            error: { message: "没有 AI 绑定（wrangler.toml 的 [ai] binding = \"AI\" 没生效）",
                     type: "configuration_error" },
            gbt: { missing: "AI binding", how_to_fix: "确认 wrangler.toml 里有 [ai] binding = \"AI\" 且已部署" },
          }, 500);
        }
        if (!wid) {
          return json({
            error: { message: "没配上游模型 id（WORKERS_AI_MODEL 为空）", type: "configuration_error" },
            gbt: { missing: "WORKERS_AI_MODEL", how_to_fix: "在 wrangler.toml 的 [vars] 里填上模型 id（见 `wrangler ai models`）",
                   detail: "不替主人挑模型" },
          }, 500);
        }
        const idz = withIdentity(e, msgs);
        // 🔴 上游只认 content 字符串 ⇒ 转发前必须归一（见 normalizeMessages 的注释）
        const norm = normalizeMessages(idz.messages);
        let upstream;
        try {
          upstream = await e.AI.run(wid, { messages: norm, max_tokens: body.max_tokens || body.max_completion_tokens || 512, stream: true });
        } catch (err) {
          // 🔴 2026-09-25 **配额/限流不许混进通用 upstream_error**（实测踩到）。
          //    现场：Workers AI 免费额度用尽时上游回
          //      `4006: you have used up your daily free allocation of 10,000 neurons`
          //    老版把它并进 `502 / upstream_error` ⇒ 调用方（含 DSH 的 llm 适配层，
          //    它**认得 QUOTA / RATE_LIMIT 这两个稳定码**）完全分不清
          //    「代码坏了」和「额度用完了」。主人也当场被这个读数绕住过（问"为什么还是 502"）。
          //    ⇒ 按语义分档 + 给出可机读字段，别再让人从一串英文里猜。
          const _msg = String((err && err.message) || err);
          // ⚠️ 自纠（2026-09-25）：我第一版把 `exceeded` 放进了**配额**正则，
          //    而 `5021`（上下文超窗）的报文里**正好有 "exceeded"**
          //    ⇒ 两类条件会互相吃掉。现在把两个正则**做成互斥**的。
          const _ctx = /5021|context window|context length|maximum context|too many tokens/i.test(_msg);
          const _quota = !_ctx && /neuron|daily free allocation|quota|4006|\b429\b|rate[ _-]?limit/i.test(_msg);
          return json({
            error: {
              message: _msg,
              type: _ctx ? "context_window_exceeded" : (_quota ? "quota_error" : "upstream_error"),
            },
            gbt: {
              quota_exhausted: _quota,
              context_window_exceeded: _ctx,
              upstream_model: wid,
              via: "workers-ai",
              upstream_code: (_msg.match(/\b\d{4}\b/) || [null])[0],
              hint: _ctx
                ? "本会话的累积上下文已超过该上游的窗口（gpt-oss-120b = 128,000）。"
                  + "这是**算术墙**，不是服务坏了：换短会话/开新会话即可；本路由没有压缩能力。"
                : (_quota
                  ? "Workers AI 免费额度（10,000 neurons/日）用尽，按 00:00 UTC 重置；"
                    + "要彻底绕开配额得先把 LLM_ENDPOINT 真接线（现在它只是个空声明）"
                  : null),
            },
          }, _ctx ? 400 : (_quota ? 429 : 502));
        }
        const created = Math.floor(Date.now() / 1000);
        const cid = "chatcmpl-gbt-" + Date.now();
        const enc = new TextEncoder();
        const dec = new TextDecoder();
        const sse = new ReadableStream({
          async start(controller) {
            const send = (obj) => controller.enqueue(enc.encode("data: " + JSON.stringify(obj) + "\n\n"));
            send({ id: cid, object: "chat.completion.chunk", created, model: "gbt-potato-v8",
                   choices: [{ index: 0, delta: { role: "assistant" }, finish_reason: null }] });
            let buf = "";
            let chars = 0;
            try {
              const reader = upstream.getReader();
              for (;;) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += dec.decode(value, { stream: true });
                const parts = buf.split("\n");
                buf = parts.pop();
                for (const line of parts) {
                  const t = line.trim();
                  if (!t.startsWith("data:")) continue;
                  const payload = t.slice(5).trim();
                  if (!payload || payload === "[DONE]") continue;
                  let j = null;
                  try {
                    j = JSON.parse(payload);
                  } catch (err) {
                    continue;
                  }
                  const piece = (j.choices && j.choices[0] && (j.choices[0].delta ? j.choices[0].delta.content : j.choices[0].text)) || j.response || "";
                  if (piece) {
                    chars += String(piece).length;
                    send({ id: cid, object: "chat.completion.chunk", created, model: "gbt-potato-v8",
                           choices: [{ index: 0, delta: { content: String(piece) }, finish_reason: null }] });
                  }
                }
              }
              send({ id: cid, object: "chat.completion.chunk", created, model: "gbt-potato-v8",
                     choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
                     gbt: { upstream_model: wid, weights_ours: false, identity_injected: idz.injected, chars } });
              controller.enqueue(enc.encode("data: [DONE]\n\n"));
            } catch (err) {
              send({ id: cid, object: "chat.completion.chunk", created, model: "gbt-potato-v8",
                     choices: [{ index: 0, delta: {}, finish_reason: "error" }], gbt: { error: String((err && err.message) || err) } });
              controller.enqueue(enc.encode("data: [DONE]\n\n"));
            }
            controller.close();
          },
        });
        return new Response(sse, { headers: { "content-type": "text/event-stream; charset=utf-8", "cache-control": "no-cache" } });
      }
      const r = await dispatch("gbt-c01-llm-gateway", "complete", {
        // 🔴 同流式那条：上游只认 content 字符串，转发前必须归一
        messages: normalizeMessages(msgs), max_tokens: body.max_tokens || body.max_completion_tokens || 512,
        temperature: body.temperature, tools: body.tools, tool_choice: body.tool_choice,
        // `model` 透传：客户端点了哪个上游模型就走哪个（不写死）。
        // 现读到的模型 id 见 `wrangler ai models`；不认识的 id 由上游如实报错，**不替它兜底**。
        model: body.model && body.model !== "gbt-potato-v8" ? body.model : undefined,
      }, null);
      const b = r.body || {};
      if (r.code !== 200 || b.ok !== true) {
        // 🔴 2026-09-25 **非流式这条也有同一处假归错**（只修流式 = 只修一半）：
        //    这里原先把模块的任何非 200 都压成 `upstream_error` + 502。
        //    但模块自己**知道**它为什么失败，而且如实写在 `reason` / `detail` 里：
        //      · `gbt-c01-llm-gateway` 报 `reason: NOT_READ` 时，含义是
        //        「AI 绑定在，但没配 WORKERS_AI_MODEL」（**本地配置缺失**，不是上游故障）；
        //      · 403 那条是 `denied`（授权门），已有独立档。
        //    ⇒ 按模块给的理由分档：NOT_READ ⇒ `configuration_error` + 500，
        //      其余才落 `upstream_error` + 502。**别把"本地没配好"说成"远端坏了"。**
        const _reason = String(b.reason || "");
        const _isCfg = (_reason === "NOT_READ") || (r.code === 500);
        return json({
          error: {
            message: String(b.detail || b.error || b.reason || "上游没给出正文"),
            type: _isCfg ? "configuration_error" : "upstream_error",
          },
          gbt: { denied: b.denied || false, missing_scopes: b.missing_scopes || [],
                 diag: b.diag || null, content_path: b.content_path || null,
                 module_reason: _reason || null },
        }, r.code === 403 ? 403 : (_isCfg ? 500 : 502));
      }
      return json({
        id: "chatcmpl-gbt-" + Date.now(),
        object: "chat.completion",
        created: Math.floor(Date.now() / 1000),
        model: "gbt-potato-v8",
        choices: [{ index: 0, message: { role: "assistant", content: b.content, ...(b.tool_calls && b.tool_calls.length ? { tool_calls: b.tool_calls } : {}) }, finish_reason: (b.tool_calls && b.tool_calls.length) ? "tool_calls" : (b.diag && b.diag.finish_reason ? b.diag.finish_reason : "stop") }],
        usage: b.usage || null,
        gbt: { upstream_model: b.model, weights_ours: b.weights_ours, via: b.via, ms: b.ms, identity_injected: b.identity_injected, content_path: b.content_path },
      });
    }

    if (method === "GET" && path === "/") {
      return json({
        name: "GBT小土豆V8 · 10 云插件拼接网",
        form: MESH.form,
        modules: MODULE_IDS.length,
        routes: ["GET /mesh", "GET /edges", "GET /health", "POST /rpc/<id>/<op>", "POST /mesh/full-ping", "POST /admin/grant"],
      });
    }
    if (method === "GET" && path === "/mesh") {
      return json({
        form: MESH.form,
        form_note: MESH.form_note,
        doctrine: MESH.doctrine,
        owner_labels: MESH.owner_labels,
        modules: MESH.modules.map((m) => ({ seq: m.seq, id: m.id, owner_label: m.owner_label, duty: m.duty, ops: m.ops, gates: m.op_gates, cloud: m.cloud, boundary: m.boundary })),
        edges_expected: MESH.edges.directed_expected,
        state_scope: {
          scope: "isolate",
          note: "计数/日志/授权活在**同一 isolate 内**跨请求；isolate 会被回收也会有多副本 ⇒ 要算数的授权必须落 KV/DO/secret。",
        },
      });
    }
    if (method === "GET" && path === "/edges") return json(edgesReport());
    if (method === "GET" && path === "/health") return json(await health());

    if (method === "POST" && path === "/mesh/full-ping") {
      const r = await fullPing();
      return json({ full_ping: r, edges: edgesReport() });
    }
    if (method === "POST" && path === "/admin/grant") {
      const owner = e.OWNER_TOKEN;
      const given = request.headers.get("x-owner-token") || "";
      if (!owner) return json({ ok: false, reason: "未读到主人令牌：本实例没有发授权的口子。" }, 403);
      if (given !== owner) return json({ ok: false, reason: "令牌不对，拒绝。" }, 403);
      let body = {};
      try {
        body = await request.json();
      } catch (err) {
        return json({ ok: false, reason: "body 不是 JSON" }, 400);
      }
      const scopes = Array.isArray(body.scopes) ? body.scopes : [];
      const unknown = scopes.filter((s) => !SCOPES.includes(s));
      if (unknown.length) return json({ ok: false, reason: "作用域名不在 15 条表里", unknown }, 400);
      await loadGrants(e, state, true);
      state.runtimeGrants = [...new Set([...(state.runtimeGrants || []), ...scopes])];
      refreshEffective(state);
      const persisted = await saveGrants(e, state);
      return json({
        ok: true,
        granted: [...state.grants],
        from_config: state.configGrants || [],
        from_runtime: state.runtimeGrants || [],
        persisted,
        note: persisted === "kv" ? "运行时授权已落 KV ⇒ 活过重启/重部署。" : "⚠️ 没有 KV 绑定 ⇒ 这份授权**只活在 isolate 里，重启即失**。云端请务必让 MEM 绑上。",
      });
    }
    if (method === "POST" && path.startsWith("/rpc/")) {
      // 2026-10-04 收紧（24h 审查）：网关配了（GW_AUTH 非空）⇒ /rpc 与 /v1/chat 同规格要求 bearer
      //   —— 公开 workers.dev 上匿名调用者能触发全部"未挂作用域"的 module op（写 KV/R2/内存），
      //   原实现此处零鉴权。没配网关（本地开发态）保持原样，读数见 /v1/models 的 auth_scope.rpc。
      const _gwRpc = String(e.GW_AUTH || "");
      if (_gwRpc) {
        const _gotR = (request.headers.get("authorization") || "").replace(/^Bearer\s+/i, "").trim();
        const _encR = new TextEncoder();
        const [_ha, _hb] = await Promise.all([
          crypto.subtle.digest("SHA-256", _encR.encode(_gotR)),
          crypto.subtle.digest("SHA-256", _encR.encode(_gwRpc)),
        ]);
        const _ta = new Uint8Array(_ha), _tb = new Uint8Array(_hb);
        let _okR = false;
        if (crypto.subtle.timingSafeEqual) _okR = crypto.subtle.timingSafeEqual(_ta, _tb);
        else { let _d = 0; for (let i = 0; i < _ta.length; i++) _d |= _ta[i] ^ _tb[i]; _okR = _d === 0; }
        if (!_okR) {
          return json({ ok: false, reason: "Authorization 不对（本端点已开启网关鉴权）", gbt: { scheme: "Bearer GW_AUTH" } }, 401);
        }
      }
      const parts = path.split("/").filter(Boolean);
      if (parts.length < 3) return json({ ok: false, reason: "用法 /rpc/<id>/<op>" }, 400);
      let body = {};
      try {
        body = await request.json();
      } catch (err) {
        body = {};
      }
      const r = await dispatch(parts[1], parts[2], body, null);
      return json(r.body, r.code);
    }
    return json({ ok: false, reason: "no such route", path, method }, 404);
  }

  return { fetch: handle, state, dispatch, edgesReport, fullPing, health };
}

// 🔴 这条是本机验收抓不到、真跑才抓到的：Worker 的默认导出**每次请求都会重新执行**，
//    所以「每次请求 new 一个 mesh」会让计数的边、发的授权、落账全部**出了这次请求就没了**。
//    修法：账（state）提到**模块级** ⇒ 同一 isolate 内跨请求活着。
//    边界（不许念过头）：isolate 是**尽力而为**的 —— 会被回收、会同时存在多个副本。
//    ⇒ 计数与日志当"热读数"可以；**授权这种要算数的东西必须落 KV/DO/secret**，
//      否则 A 副本发的授权，B 副本看不见（这条已写进 /mesh 的读数里）。
let ISOLATE_STATE = null;

export function isolateState() {
  if (!ISOLATE_STATE) ISOLATE_STATE = createState();
  return ISOLATE_STATE;
}

export default {
  fetch(request, env, ctx) {
    return createMesh(env, isolateState()).fetch(request);
  },
};
