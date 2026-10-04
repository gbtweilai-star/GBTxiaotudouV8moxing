// GBT小土豆V8 · 10 云插件拼接网 · **端点闸本机验收**（离线 · 不出一字节网）
// 开发者：自由的风 · 守护者：公主土豆 · 禁止删除
//
// ## 为什么单独有这一件
// `run-mesh-local.mjs` 量的是**形状**（10 位在不在 · 90 条边通不通 · 门开不开）。
// 它**没有**覆盖 worker.js 里 2026-09-25 那 4 批改动 —— 那 4 批正是「她一句话都答不出来」
// 的直接病根，又因为没部署，云端从来没跑过：
//   ① 令牌闸（多令牌 / 常数时间比较 / 没配就如实说"不校验"）
//   ② `/v1/models` 的按作用面读数（老版一句「令牌闸已开」比事实大）
//   ③ `normalizeMessages`：上游只认 `content` 字符串，块数组必须拍平
//   ④ 错误分档（5021 上下文超窗 ≠ 4006 配额用尽 ≠ 配置没填 ≠ 通用上游故障）
// 这四批要么在云端真验，要么在本机**离线**验。本件选后者：不部署、不联网、不花钱，
// 就能拿到「这四批到底有没有牙」的读数。
//
// ## 口径（不许念错）
// - 本机跑 ≠ 云端跑：这里验的是**代码行为**（给定输入给定输出），不是云上真读数。
// - **每条判据都配负控**：该红的必须红，红不了就是判据坏了（本仓的老坑）。
// - HTTP 状态在 `Response` 上、业务读数在 body 里 —— **两层分开念**。
// - `crypto.subtle.timingSafeEqual` 是 Workers 扩展，Node 没有 ⇒ 本机走的是**回退分支**
//   （逐字节异或累加）。所以本机通过只证明"行为对"，不证明"云上用的就是那条指令"。
//
// 用法：node deploy/cloud-10/tools/check-endpoint-gate.mjs [--json]

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { createMesh } from "../src/worker.js";

// 🔴 判据前必须先剥注释：worker.js 的注释里**正引着旧代码原文**
//    「原来是最朴素的 `got !== "Bearer " + token` 明文比较」
//    —— 直接扫原文会把自己的注释判成"旧比较还在"（假红）。
//    ⚠️ 而且必须**按 CRLF 也管用**的方式剥：第一版用 `.split("\n")` + `/\/\/.*$/`，
//    在 LF 上正常，一旦文件是 CRLF，`.*` 吃不到 `\r`、`$` 又不匹配行中位置 ⇒
//    **整条剥注释静默失效**，判据当场变成假红。这是变异测试逼出来的，不是想出来的。
function stripComments(s) {
  return String(s).replace(/\/\*[\s\S]*?\*\//g, "")
    .split(/\r?\n/).map((l) => l.replace(/\/\/.*$/, "")).join("\n");
}

const asJson = process.argv.includes("--json");
const rows = [];

function ck(name, pass, reading) {
  rows.push({ name, pass: !!pass, reading: String(reading) });
  if (!asJson) console.log(`  ${pass ? "PASS" : "FAIL"}  ${name}  ::  ${reading}`);
}

const OWNER = "owner-token-for-endpoint-gate";
const GW = "gw-auth-test-key";
const MODEL = "@cf/stub/model";

// ── 桩：AI 绑定。三种形态 —— 普通回包 / SSE 流 / 抛错 ──────────────────────
function aiStub({ text = "桩回答", sse = null, throwMsg = null, record = null } = {}) {
  return {
    async run(model, input) {
      if (record) record.push({ model, input });
      if (throwMsg) throw new Error(throwMsg);
      if (sse) {
        const enc = new TextEncoder();
        return new ReadableStream({
          start(c) { for (const line of sse) c.enqueue(enc.encode(line)); c.close(); },
        });
      }
      return { response: text, usage: { total_tokens: 7 } };
    },
  };
}

function req(mesh, method, path, body, headers) {
  return mesh.fetch(
    new Request("https://mesh.local" + path, {
      method,
      // 2026-10-04：/v1/chat 与 /rpc 现在缺 GW_AUTH 就 fail-closed ⇒ 脚手架上默认带
      // 测试网关钥匙；要测「不带 Authorization」的用例显式传 { authorization: "" } 覆盖。
      headers: { "content-type": "application/json", authorization: `Bearer ${GW}`, ...(headers || {}) },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined,
    }),
  );
}

// 云端契约：受门动作要先有授权。本机照同一条路走，**不旁路**。
async function meshWith(env) {
  // 2026-10-04：默认配测试网关钥匙（GW）；要测"没配网关"的场景显式传 GW_AUTH: ""。
  const { GW_AUTH: gwOverride, ...rest } = env || {};
  const mesh = createMesh({ OWNER_TOKEN: OWNER, GW_AUTH: gwOverride === undefined ? GW : gwOverride, ...rest });
  await req(mesh, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER });
  return mesh;
}

async function postJSON(mesh, path, body, headers) {
  const r = await req(mesh, "POST", path, body, headers);
  let j = null;
  try { j = await r.json(); } catch (err) { j = null; }
  return { status: r.status, body: j };
}
const chatBody = (msgs, extra) => ({ model: "gbt-potato-v8", messages: msgs, ...(extra || {}) });

// 全局凭据泄漏红线：任何回包正文里**不许出现**配下去的令牌值
const LEAK = [];
function scanForToken(where, txt) {
  if (String(txt).includes(GW)) LEAK.push(`${where} 泄漏了网关密钥值`);
}

// ══════════════════════════════════════════════════════════════════════════
// ① 网关鉴权：没配 GW_AUTH ⇒ **fail-closed**（2026-10-04 收紧；原口径是"如实说不校验"）
// ══════════════════════════════════════════════════════════════════════════
{
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub(), GW_AUTH: "" });
  const modelsRes = await req(mesh, "GET", "/v1/models");
  const models = await modelsRes.json();
  scanForToken("① /v1/models", JSON.stringify(models));
  const g = models.gbt || {};
  ck("① 没配网关 ⇒ auth_scope.chat=fail-closed（如实报「锁不上就不服务」）",
     (g.auth_scope || {}).chat === "fail-closed" && (g.auth_scope || {}).models === "public", JSON.stringify(g.auth_scope));
  ck("① 没配网关 ⇒ 人读那句话直说 fail-closed（不再说「不校验」）",
     /fail-closed/.test(String(g.auth)) && /不校验/.test(String(g.auth)) === false, String(g.auth));
  ck("① /v1/models 这一路公开（无 Authorization 也 200）",
     modelsRes.status === 200, `status=${modelsRes.status}`);
  const r = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "在吗" }]));
  // 2026-10-04 收紧：没配网关时**不许放行** —— 必须 503 + configuration_error（fail-closed）
  ck("① fail-closed：没配网关时 /v1/chat 拒服务（503 configuration_error）",
     r.status === 503 && (r.body?.error?.type || "") === "configuration_error" && !!r.body?.gbt?.fail_closed,
     `status=${r.status} type=${r.body?.error?.type} fc=${r.body?.gbt?.fail_closed}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ② 网关鉴权：配了 GW_AUTH ⇒ 错钥必拒 / 公开面与受管面对照
// ══════════════════════════════════════════════════════════════════════════
{
  const mesh = await meshWith({
    WORKERS_AI_MODEL: MODEL,
    AI: aiStub(),
    GW_AUTH: GW,
  });
  const msgs = [{ role: "user", content: "在吗" }];

  const wrong = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: "Bearer nope-0000" });
  scanForToken("② 错钥回包", JSON.stringify(wrong.body));
  ck("② 错钥 ⇒ 401 + authentication_error",
     wrong.status === 401 && wrong.body?.error?.type === "authentication_error",
     `${wrong.status} ${wrong.body?.error?.type}`);
  ck("② 被拒时点明使用 GW_AUTH Bearer",
     wrong.body?.gbt?.scheme === "Bearer GW_AUTH",
     JSON.stringify(wrong.body?.gbt));

  const none = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: "" });
  ck("② 不带 Authorization ⇒ 拒（不是放行）", none.status === 401, `status=${none.status}`);

  const correct = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: `Bearer ${GW}` });
  ck("② 正确密钥放行（200）", correct.status !== 401, `status=${correct.status}`);

  const lower = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: `bEarer ${GW}` });
  ck("② `Bearer` 前缀大小写不敏感", lower.status !== 401, `status=${lower.status}`);

  // 决定性负控：公开面真公开、受管面真受管 —— 一句话两处对照，声明才不是空话
  const modelsOpen = await req(mesh, "GET", "/v1/models");
  const modelsOpenBody = await modelsOpen.json();
  const g = modelsOpenBody.gbt || {};
  ck("② 负控/正控对照：/v1/models 无 Authorization=200，而 /v1/chat/completions 无 Authorization=401",
     modelsOpen.status === 200 && none.status === 401,
     `models=${modelsOpen.status} chat=${none.status}`);
  ck("② 机器读的 auth_scope 说清了作用面",
     g.auth_scope?.chat === "bearer" && g.auth_scope?.models === "public" && g.auth_scope?.scheme === "GW_AUTH Bearer",
     JSON.stringify(g.auth_scope));
  ck("② 人读 auth 与机器读 auth_scope 一致（口径不许两套）",
     /网关鉴权已开/.test(String(g.auth)),
     String(g.auth));
  scanForToken("② /v1/models（配了网关时）", JSON.stringify(modelsOpenBody));

  // ── 2026-10-04 新增：配了网关 ⇒ /rpc 与 /v1/chat 同规格（原实现 /rpc 零鉴权）──────
  const rpcNoAuth = await postJSON(mesh, "/rpc/gbt-c01-llm-gateway/ping", {}, { authorization: "" });
  ck("② 配了网关 ⇒ /rpc 不带 Authorization = 401（不是放行）",
     rpcNoAuth.status === 401, `status=${rpcNoAuth.status} reason=${rpcNoAuth.body?.reason}`);
  const rpcOk = await postJSON(mesh, "/rpc/gbt-c01-llm-gateway/ping", {}, { authorization: `Bearer ${GW}` });
  ck("② 配了网关 ⇒ /rpc 带对钥放行（200）", rpcOk.status === 200, `status=${rpcOk.status}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ③ 旧变量退役：GBT_ENDPOINT_TOKENS 已不再被读取（2026-10-03 简化 ⇒ 负控）
//    ⚠️ 修 2026-10-04：原用例引用**未定义**的 TOK/TOK2 ⇒ 本文件此前跑到 ③ 就崩，
//       ④~⑨ 从来没被执行过（24h 审查实证）。口径跟着事实走：现在要证的恰恰是
//       「旧多令牌不再生效」，并配一条正控证明 401 是旧令牌造成的、不是实例坏了。
// ══════════════════════════════════════════════════════════════════════════
{
  const LEGACY = "legacy-multi-token-1";
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub(),
    GBT_ENDPOINT_TOKENS: `${LEGACY},legacy-multi-token-2`, GW_AUTH: GW });
  const oldTok = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }]), { authorization: `Bearer ${LEGACY}` });
  ck("③ 旧多令牌 GBT_ENDPOINT_TOKENS 已退役（负控：拿旧令牌必 401）", oldTok.status === 401, `status=${oldTok.status}`);
  const newTok = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }]), { authorization: `Bearer ${GW}` });
  ck("③ 正控：同一实例上 GW_AUTH 仍放行（证明 401 是旧令牌造成的，不是实例坏了）", newTok.status === 200, `status=${newTok.status}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ④ 常数时间比较：读数里那句 compare 必须是真接线，不是打印出来的
// ══════════════════════════════════════════════════════════════════════════
{
  const here = dirname(fileURLToPath(import.meta.url));
  const raw = readFileSync(join(here, "..", "src", "worker.js"), "utf8");
  const src = stripComments(raw);
  const NAIVE = /got\s*!==\s*"Bearer "\s*\+/;
  // 判据自检（先证判据本身，再看被检物）：剥注释在 LF 与 CRLF 上都必须管用
  const PROBE_LF = 'const x = 1; // got !== "Bearer " + token\nconst y = 2;';
  const PROBE_CRLF = 'const x = 1; // got !== "Bearer " + token\r\nconst y = 2;';
  const probeOk = NAIVE.test(PROBE_LF) && !NAIVE.test(stripComments(PROBE_LF))
                && NAIVE.test(PROBE_CRLF) && !NAIVE.test(stripComments(PROBE_CRLF));
  ck("④ 判据自检：剥注释在 LF 与 CRLF 上都管用（否则下面那条是假红/假绿）", probeOk,
     `LF 剥后命中=${NAIVE.test(stripComments(PROBE_LF))} CRLF 剥后命中=${NAIVE.test(stripComments(PROBE_CRLF))}`);
  ck("④ 判据有牙自检：探针原文里必须**能**命中（探针没牙则判据是空的）",
     NAIVE.test(PROBE_LF) && NAIVE.test(PROBE_CRLF), "两个探针都命中");
  const eol = raw.includes("\r\n") ? "CRLF" : "LF";
  const hasDigest = /crypto\.subtle\.digest\(\s*"SHA-256"/.test(src);
  const hasTsEqual = /timingSafeEqual/.test(src);
  const naive = NAIVE.test(src);
  ck("④ 源码（去注释后）里真有 SHA-256 摘要（不是只写了个字符串）", hasDigest, `digest=${hasDigest}`);
  ck("④ 源码（去注释后）里真有 timingSafeEqual（Workers 扩展或回退分支）", hasTsEqual, `timingSafeEqual=${hasTsEqual}`);
  ck("④ 负控：旧的明文比较已不在（注释里的引用不算）", naive === false, `naiveCompare=${naive} 行尾=${eol}`);
  ck("④ 负控自检：注释确实被剥掉了（否则上面那条是假绿）",
     raw.includes('got !== "Bearer " + token') === false || src.includes("原来是最朴素的") === false,
     `原文含该注释=${raw.includes("原来是最朴素的")} 剥后含=${src.includes("原来是最朴素的")}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ⑤ normalizeMessages：上游只认 content 字符串 ⇒ 块数组必须拍平
//    （这是"她一句话都答不出来"的直接病根，必须**行为**验，不能只看有没有写）
// ══════════════════════════════════════════════════════════════════════════
{
  const rec = [];
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ record: rec }) });
  const cases = [
    { name: "⑤ 块数组拍平成字符串（原样透传会被上游 schema 拒）",
      sent: [{ role: "user", content: [{ type: "text", text: "甲" }, { type: "text", text: "乙" }] }],
      want: (c) => c === "甲\n乙" },
    { name: "⑤ content=null（带 tool_calls 的 assistant）⇒ 空串，不许是 null",
      sent: [{ role: "assistant", content: null, tool_calls: [{ id: "t1", type: "function", function: { name: "f", arguments: "{}" } }] }],
      want: (c, row) => c === "" && Array.isArray(row.tool_calls) && row.tool_calls.length === 1 },
    { name: "⑤ 图片块落确定性占位文本（不静默丢，也不假装看得见）",
      sent: [{ role: "user", content: [{ type: "text", text: "看这个" }, { type: "image_url", image_url: { url: "data:image/png;base64,AAAA" } }] }],
      want: (c) => c === "看这个\n[图片]" },
    { name: "⑤ 纯字符串内容原样不动",
      sent: [{ role: "user", content: "原样" }],
      want: (c) => c === "原样" },
    { name: "⑤ tool_call_id / name 原样保留（丢了下游工具调用就断）",
      sent: [{ role: "tool", content: "结果", tool_call_id: "t1", name: "f" }],
      want: (c, row) => c === "结果" && row.tool_call_id === "t1" && row.name === "f" },
    { name: "⑤ 字符串型块（有些客户端这么发）也拍平",
      sent: [{ role: "user", content: ["甲", "乙"] }],
      want: (c) => c === "甲\n乙" },
  ];
  for (const c of cases) {
    rec.length = 0;
    // 走**流式**那条：worker 自己直接调 e.AI.run，桩能逐字收到上游真的拿到什么
    const r = await postJSON(mesh, "/v1/chat/completions", chatBody(c.sent, { stream: true }));
    // 🔴 取**最后一条**，不是 [0]：身份注入会把 system 顶到最前面（`withIdentity` 前置），
    //    [0] 拿到的是注入的身份而不是我发的那条 —— 第一版我就这么读错了，
    //    而且**负控跟着一起假绿**（拿字符串去判 string，恒真）。
    const rowsGot = rec[0]?.input?.messages || [];
    const got = rowsGot[rowsGot.length - 1];
    const content = got?.content;
    ck(c.name, r.status === 200 && got?.role === c.sent[0].role && c.want(content, got),
       `status=${r.status} role=${got?.role} content=${JSON.stringify(content)}`);
    ck(c.name.replace(/^⑤ /, "⑤ 负控：送到上游的 content 绝不是数组 · "),
       got !== undefined && !Array.isArray(content), got === undefined ? "没取到那一条 ⇒ 判据自己坏了" : typeof content);
  }
  ck("⑤ 前置的注入身份那条 system 也一并在归一之列（不是只归一我发的那条）",
     (rec[0]?.input?.messages || []).every((m) => typeof m.content === "string"),
     JSON.stringify((rec[0]?.input?.messages || []).map((m) => typeof m.content)));
  // 非流式那条：worker 先归一，模块里也有一份归一 —— 两层都要真过
  const rec2 = [];
  const mesh2 = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ record: rec2 }) });
  const r2 = await postJSON(mesh2, "/v1/chat/completions",
    chatBody([{ role: "user", content: [{ type: "text", text: "丙" }] }]));
  const c2rows = rec2[0]?.input?.messages || [];
  const c2row = c2rows[c2rows.length - 1];
  const c2 = c2row?.content;
  ck("⑤ 非流式那条路（worker→模块→AI）也拍平", r2.status === 200 && c2 === "丙" && c2row?.role === "user",
     `status=${r2.status} role=${c2row?.role} content=${JSON.stringify(c2)}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ⑥ 流式分支的错误分档：5021 上下文超窗 ≠ 4006 配额 ≠ 配置 ≠ 通用上游
// ══════════════════════════════════════════════════════════════════════════
{
  const cases = [
    { msg: "AiError: 5021: prompt has exceeded the context window of 128000 tokens",
      status: 400, type: "context_window_exceeded", code: "5021", ctx: true, quota: false },
    { msg: "4006: you have used up your daily free allocation of 10,000 neurons",
      status: 429, type: "quota_error", code: "4006", ctx: false, quota: true },
    { msg: "maximum context length exceeded",
      status: 400, type: "context_window_exceeded", code: null, ctx: true, quota: false },
    { msg: "rate limit exceeded, retry later",
      status: 429, type: "quota_error", code: null, ctx: false, quota: true },
    { msg: "socket hang up",
      status: 502, type: "upstream_error", code: null, ctx: false, quota: false },
    // 🔴 这一条专治那处自纠：`exceeded` 一度被放进**配额**正则，会把通用上游故障
    //    也念成"额度用完了"。报文里只有 exceeded、没有 5021/neuron/quota/rate limit
    //    ⇒ 必须落回通用上游故障。把它写进来，是为了下面那次变异测试能把它打红。
    { msg: "upstream request exceeded retry budget",
      status: 502, type: "upstream_error", code: null, ctx: false, quota: false },
  ];
  for (const c of cases) {
    const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ throwMsg: c.msg }) });
    const r = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
    const g = r.body?.gbt || {}, e = r.body?.error || {};
    const okShape = r.status === c.status && e.type === c.type
      && g.context_window_exceeded === c.ctx && g.quota_exhausted === c.quota;
    ck(`⑥ 「${c.msg.slice(0, 34)}…」⇒ ${c.status} ${c.type}`, okShape,
       `${r.status} ${e.type} ctx=${g.context_window_exceeded} quota=${g.quota_exhausted}`);
  }
  // 决定性：两个正则必须**互斥** —— 上一版 `exceeded` 放进配额正则会互相吃掉
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ throwMsg: "5021 context window exceeded" }) });
  const r = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  ck("⑥ 负控：报文里同时有 exceeded 与 5021 时 ⇒ 只能归上下文，不许被配额吃掉",
     r.status === 400 && r.body?.gbt?.context_window_exceeded === true && r.body?.gbt?.quota_exhausted === false,
     `${r.status} ctx=${r.body?.gbt?.context_window_exceeded} quota=${r.body?.gbt?.quota_exhausted}`);
  ck("⑥ 上下文超窗给出可机读 hint（算术墙，不是服务坏了）",
     /算术墙|换短会话/.test(String(r.body?.gbt?.hint || "")), String(r.body?.gbt?.hint || "").slice(0, 40));
}

// ══════════════════════════════════════════════════════════════════════════
// ⑦ fail-closed：配了 LLM_ENDPOINT 却走流式 ⇒ 501 如实（不许静默烧 Workers AI）
// ══════════════════════════════════════════════════════════════════════════
{
  const meshLLM = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub(), LLM_ENDPOINT: "http://127.0.0.1:8111/v1" });
  const r = await postJSON(meshLLM, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  ck("⑦ 流式 + 已配 LLM_ENDPOINT ⇒ 501 not_implemented（不静默改道）",
     r.status === 501 && r.body?.error?.type === "not_implemented", `${r.status} ${r.body?.error?.type}`);
  ck("⑦ 501 里标明两条路各是什么（可判，不是一句话糊过去）",
     r.body?.gbt?.wired?.non_stream === true && r.body?.gbt?.wired?.stream === false && !!r.body?.gbt?.how_to_fix,
     JSON.stringify(r.body?.gbt?.wired));

  // 负控：不配 LLM_ENDPOINT 的同一发 ⇒ 不许是 501（否则 501 就是恒真）
  const meshNo = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub() });
  const rNo = await postJSON(meshNo, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  ck("⑦ 负控：没配 LLM_ENDPOINT 时同一发绝不是 501", rNo.status !== 501 && rNo.status === 200, `status=${rNo.status}`);

  const meshBare = await meshWith({ WORKERS_AI_MODEL: MODEL });
  const rBare = await postJSON(meshBare, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  ck("⑦ 没有 AI 绑定 ⇒ 500 configuration_error（本地没配，不许报成远端 502）",
     rBare.status === 500 && rBare.body?.error?.type === "configuration_error",
     `${rBare.status} ${rBare.body?.error?.type}`);

  const meshNoModel = await meshWith({ AI: aiStub() });
  const rNoModel = await postJSON(meshNoModel, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  ck("⑦ AI 绑定在但没配模型 id ⇒ 500 configuration_error + 明说「不替主人挑模型」",
     rNoModel.status === 500 && /不替主人挑模型/.test(String(rNoModel.body?.gbt?.detail || "")),
     `${rNoModel.status} ${rNoModel.body?.gbt?.detail}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ⑧ 流式正路（`/v1/models` 里那句 `stream: true` 必须不是空话）
// ══════════════════════════════════════════════════════════════════════════
{
  const sse = [
    'data: {"choices":[{"delta":{"content":"你"}}]}\n\n',
    'data: {"choices":[{"delta":{"content":"好"}}]}\n\n',
    'data: [DONE]\n\n',
  ];
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ sse }) });
  const res = await req(mesh, "POST", "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  const txt = await res.text();
  ck("⑧ 流式真出 SSE（content-type 对）",
     res.status === 200 && /text\/event-stream/.test(res.headers.get("content-type") || ""),
     `${res.status} ${res.headers.get("content-type")}`);
  const joined = txt.split("\n").filter((l) => l.startsWith("data:") && !l.includes("[DONE]"))
    .map((l) => { try { const j = JSON.parse(l.slice(5)); return j.choices?.[0]?.delta?.content || ""; } catch (e) { return ""; } }).join("");
  ck("⑧ 分片拼回原文（delta 是逐字发的）", joined === "你好", JSON.stringify(joined));
  ck("⑧ 收尾发 [DONE]", txt.trimEnd().endsWith("data: [DONE]"), txt.trim().split("\n").pop());
  ck("⑧ 尾片如实标 weights_ours=false（流式这条路不冒充自托管）",
     /"weights_ours":\s*false/.test(txt) && /"chars":\s*2/.test(txt),
     (txt.match(/"gbt":\s*\{[^}]*\}/) || [""])[0].slice(0, 80));
  scanForToken("⑧ 流式回包", txt);

  // 负控：上游一个字符都不给 ⇒ 不许编内容，但收尾仍要闭得上
  const mesh0 = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub({ sse: ['data: {"choices":[{"delta":{}}]}\n\n'] }) });
  const r0 = await req(mesh0, "POST", "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }], { stream: true }));
  const t0 = await r0.text();
  ck("⑧ 负控：上游零字符 ⇒ 不编内容（chars=0）且仍发 [DONE]",
     /"chars":\s*0/.test(t0) && t0.trimEnd().endsWith("data: [DONE]"),
     (t0.match(/"chars":\s*\d+/) || [""])[0]);
}

// ══════════════════════════════════════════════════════════════════════════
// ⑨ 凭据红线（总账）：全流程任何回包里都不许出现令牌值
// ══════════════════════════════════════════════════════════════════════════
ck("⑨ 全程零令牌泄漏（回包正文里不出现配下去的令牌值）", LEAK.length === 0,
   LEAK.length ? LEAK.join(" · ") : "0 处");

const failed = rows.filter((r) => !r.pass);
if (asJson) {
  console.log(JSON.stringify({ total: rows.length, failed: failed.length, rows }, null, 2));
} else {
  console.log("");
  console.log(`端点闸本机验收：${rows.length - failed.length}/${rows.length} 通过 · 离线 · 未出一字节网`);
  console.log("  · 本机跑 ≠ 云端跑：这里验的是代码行为（给定输入→给定输出），云上真读数要真部署后另量。");
  console.log("  · Node 没有 crypto.subtle.timingSafeEqual ⇒ 本机走回退分支；云上走 Workers 扩展那条。");
  console.log("  · 令牌闸覆盖 /v1/chat/completions 与 /rpc（2026-10-04 收紧）；/v1/models 公开 —— 判据是对照着量的。");
}
process.exit(failed.length ? 1 : 0);
