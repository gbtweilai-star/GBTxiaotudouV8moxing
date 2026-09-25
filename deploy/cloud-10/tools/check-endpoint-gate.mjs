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
const TOK = "tok-aaaa-1111";
const TOK2 = "tok-bbbb-2222";
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
      headers: { "content-type": "application/json", ...(headers || {}) },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined,
    }),
  );
}

// 云端契约：受门动作要先有授权。本机照同一条路走，**不旁路**。
async function meshWith(env) {
  const mesh = createMesh({ OWNER_TOKEN: OWNER, ...env });
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
  for (const t of [TOK, TOK2]) if (String(txt).includes(t)) LEAK.push(`${where} 泄漏了令牌值`);
}

// ══════════════════════════════════════════════════════════════════════════
// ① 令牌闸：没配 ⇒ 如实说不校验（不许让人以为锁上了）
// ══════════════════════════════════════════════════════════════════════════
{
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub() });
  const modelsRes = await req(mesh, "GET", "/v1/models");
  const models = await modelsRes.json();
  scanForToken("① /v1/models", JSON.stringify(models));
  const g = models.gbt || {};
  ck("① 没配令牌 ⇒ auth_scope.chat=none（如实报「没锁」）",
     (g.auth_scope || {}).chat === "none" && g.auth_scope.tokens_configured === 0, JSON.stringify(g.auth_scope));
  ck("① 没配令牌 ⇒ 人读那句话也直说「不校验」",
     /不校验/.test(String(g.auth)) && /令牌闸已开/.test(String(g.auth)) === false, String(g.auth));
  ck("① /v1/models 这一路公开（无 Authorization 也 200）",
     modelsRes.status === 200, `status=${modelsRes.status}`);
  const r = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "在吗" }]));
  // 负控：没配令牌时**不许** 401 —— 401 就说明闸门自己开着了（与读数相反）
  ck("① 负控：没配令牌时带不带 Authorization 都不该 401",
     r.status !== 401 && (r.body?.error?.type || "") !== "authentication_error",
     `status=${r.status} type=${r.body?.error?.type}`);
}

// ══════════════════════════════════════════════════════════════════════════
// ② 令牌闸：配了 ⇒ 错钥必拒 / 多令牌 / 常数时间分支 / 公开面与受管面对照
// ══════════════════════════════════════════════════════════════════════════
{
  const mesh = await meshWith({
    WORKERS_AI_MODEL: MODEL,
    AI: aiStub(),
    GBT_ENDPOINT_TOKENS: `${TOK},${TOK2}`,
  });
  const msgs = [{ role: "user", content: "在吗" }];

  const wrong = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: "Bearer nope-0000" });
  scanForToken("② 错钥回包", JSON.stringify(wrong.body));
  ck("② 错钥 ⇒ 401 + authentication_error",
     wrong.status === 401 && wrong.body?.error?.type === "authentication_error",
     `${wrong.status} ${wrong.body?.error?.type}`);
  ck("② 被拒时点明配了几个令牌（可判字段）",
     wrong.body?.gbt?.tokens_configured === 2 && wrong.body?.gbt?.scheme === "Bearer",
     JSON.stringify(wrong.body?.gbt));

  const none = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs));
  ck("② 不带 Authorization ⇒ 拒（不是放行）", none.status === 401, `status=${none.status}`);

  const second = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: `Bearer ${TOK2}` });
  ck("② 多令牌：第 2 个令牌能用（一消费方一钥的前提）",
     second.status !== 401, `status=${second.status}`);

  const lower = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: `bEarer ${TOK}` });
  ck("② `Bearer` 前缀大小写不敏感", lower.status !== 401, `status=${lower.status}`);

  const raw = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: TOK });
  ck("② 裸令牌（不带 Bearer 前缀）也认 —— 这是实测行为，写下来钉住",
     raw.status !== 401, `status=${raw.status}`);

  const longer = await postJSON(mesh, "/v1/chat/completions", chatBody(msgs), { authorization: "Bearer " + TOK + "-x" });
  ck("② 负控：长度不同的令牌 ⇒ 401（不是 500：常数时间比较不许抛）",
     longer.status === 401, `status=${longer.status}`);

  // 决定性负控：公开面真公开、受管面真受管 —— 一句话两处对照，声明才不是空话
  const modelsOpen = await req(mesh, "GET", "/v1/models");
  const modelsOpenBody = await modelsOpen.json();
  const g = modelsOpenBody.gbt || {};
  ck("② 负控/正控对照：/v1/models 无 Authorization=200，而 /v1/chat/completions 无 Authorization=401",
     modelsOpen.status === 200 && none.status === 401,
     `models=${modelsOpen.status} chat=${none.status}`);
  ck("② 机器读的 auth_scope 说清了作用面",
     g.auth_scope?.chat === "bearer" && g.auth_scope?.models === "public" && g.auth_scope?.tokens_configured === 2,
     JSON.stringify(g.auth_scope));
  ck("② 人读 auth 与机器读 auth_scope 一致（口径不许两套）",
     /2 个令牌/.test(String(g.auth)) && /v1\/models 这一路公开/.test(String(g.auth)),
     String(g.auth));
  ck("② 读数标了常数时间比较（且下面用源码证明它不是空话）",
     g.auth_scope?.compare === "sha256+timingSafeEqual", String(g.auth_scope?.compare));
  scanForToken("② /v1/models（配了令牌时）", JSON.stringify(modelsOpenBody));
}

// ══════════════════════════════════════════════════════════════════════════
// ③ 兼容旧单值变量 GBT_ENDPOINT_TOKEN
// ══════════════════════════════════════════════════════════════════════════
{
  const mesh = await meshWith({ WORKERS_AI_MODEL: MODEL, AI: aiStub(), GBT_ENDPOINT_TOKEN: TOK });
  const ok = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }]), { authorization: `Bearer ${TOK}` });
  const bad = await postJSON(mesh, "/v1/chat/completions", chatBody([{ role: "user", content: "甲" }]), { authorization: "Bearer other-token" });
  const models = await (await req(mesh, "GET", "/v1/models")).json();
  ck("③ 旧单值 GBT_ENDPOINT_TOKEN 仍然生效（正控）", ok.status !== 401, `status=${ok.status}`);
  ck("③ 旧单值下错钥仍拒（负控）", bad.status === 401, `status=${bad.status}`);
  ck("③ 旧单值按 1 个令牌报", models.gbt?.auth_scope?.tokens_configured === 1, JSON.stringify(models.gbt?.auth_scope));
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
  console.log("  · 令牌闸只覆盖 /v1/chat/completions；/v1/models 公开 —— 上面两条判据是对照着量的。");
}
process.exit(failed.length ? 1 : 0);
