// GBT小土豆V8 · 10 云插件拼接网 · 本机形状验收（**不是**本机部署）
// 开发者：自由的风 · 守护者：公主土豆 · 禁止删除
//
// 用途：把 deploy/cloud-10 那套件在本机跑一遍，量三件事 ——
//   ① 10 位是不是都在（health 10/10）
//   ② 90 条边是不是真通（每位与其余 9 位互 ping）
//   ③ 门开不开是否只有「主人令牌」这一条路（同一条调用，授权前 403、授权后 200）
//
// 口径（不许念错）：
//   - 本机跑 = 形状验收，**不替代**云端真读数；Owner 说了不部署在本地，这里只做装前自检。
//   - 两条 profile：bare（什么绑定都没有 ⇒ 读数只能是未读到）与 wired（挂桩 ⇒ 才谈功能）。
//   - 每条判据都配负控：该红的必须红，红不了就是判据坏了。
//   - 一个 PASS / 一个 FAIL，没有第三种状态。
//
// 用法：node deploy/cloud-10/tools/run-mesh-local.mjs [--json]

import { createMesh } from "../src/worker.js";
import formB from "../modules/gbt-c01-llm-gateway/src/index.js";

const asJson = process.argv.includes("--json");
const rows = [];

function ck(name, pass, reading) {
  rows.push({ name, pass: !!pass, reading });
  if (!asJson) console.log(`  ${pass ? "PASS" : "FAIL"}  ${name}  ::  ${reading}`);
}

// ── 桩绑定：只在 wired profile 里挂，bare profile 一个都不挂 ────────────────
function stubBindings() {
  const files = new Map();
  const mem = new Map();
  const vec = [];
  const ledger = [];
  let aiCalls = 0;
  // 预置「别人的数据」：真账号里 KV 有 4 个库、R2 有 1 个桶都是主人原有的，
  // 我们的写入绝不许碰到这些键 —— 下面拿它们当负控。
  mem.set("owner.original.key", "别人的数据");
  files.set("owner-original.txt", "别人的对象");
  return {
    _raw: { files, mem },
    AI: {
      async run(model, input) {
        aiCalls++;
        return { response: `桩回答(${model})`, _stub: true, _echo: String(input && input.prompt || "").slice(0, 40) };
      },
    },
    AI_SEARCH: {
      async search({ query }) {
        return { results: [{ title: "桩结果", url: "https://example.invalid/", snippet: query }], _stub: true };
      },
    },
    FILES: {
      async put(key, text) { files.set(key, text); },
      async get(key) { return files.has(key) ? { text: async () => files.get(key) } : null; },
      async delete(key) { files.delete(key); },
      async list({ prefix = "" } = {}) { return { objects: [...files.keys()].filter((k) => k.startsWith(prefix)).map((k) => ({ key: k })) }; },
    },
    MEM: {
      async put(k, v) { mem.set(k, v); },
      async get(k) { return mem.has(k) ? mem.get(k) : null; },
      async delete(k) { mem.delete(k); },
      async list({ prefix = "" } = {}) { return { keys: [...mem.keys()].filter((k) => k.startsWith(prefix)).map((n) => ({ name: n })) }; },
    },
    VECTORIZE: {
      async insert(items) { for (const it of items) vec.push(it); },
      async query() { return { matches: vec.slice(0, 1).map((v) => ({ id: v.id, score: 1 })) }; },
    },
    SANDBOX: { async exec(cmd) { return { stdout: `桩执行：${cmd}`, code: 0, _stub: true }; } },
    LEDGER: {
      async put(k, v) { ledger.push({ k, v }); files.set(k, v); },
      async get(k) { return files.has(k) ? { text: async () => files.get(k) } : null; },
      async list({ prefix = "" } = {}) { return { objects: ledger.filter((x) => x.k.startsWith(prefix)).map((x) => ({ key: x.k })) }; },
      _rows: ledger,
    },
    _stats: () => ({ aiCalls, files: files.size, mem: mem.size, vec: vec.length, ledger: ledger.length }),
  };
}

const OWNER_TOKEN = "owner-token-for-local-shape-check";
const wiredEnv = { ...stubBindings(), OWNER_TOKEN };
const bareEnv = {};                 // 没有 OWNER_TOKEN：连发授权的口子都没有
const wiredNoOwner = { ...stubBindings() };
const noSandbox = { ...stubBindings(), OWNER_TOKEN };
delete noSandbox.SANDBOX;           // 门能开、能力没接线 —— 用它量「授权 ≠ 凭空有能力」
delete noSandbox.VECTORIZE;         // 顺带量 07 号的降级落点

function req(mesh, method, path, body, headers) {
  return mesh.fetch(
    new Request("https://mesh.local" + path, {
      method,
      headers: { "content-type": "application/json", ...(headers || {}) },
      body: method === "POST" ? JSON.stringify(body || {}) : undefined,
    }),
  );
}

const wired = createMesh(wiredEnv);
const bare = createMesh(bareEnv);
const noOwner = createMesh(wiredNoOwner);
const noSandboxMesh = createMesh(noSandbox);

// 原始读数先取（后面「门一层」与「模块一层」两节都要用同一条调用对账）
// 注意：HTTP 状态在 Response 上、业务读数在 body 里 —— 两层分开拿，不许混着念
const bareShellRes = await req(bare, "POST", "/rpc/gbt-c06-tool-shell/exec", { cmd: "dir" });
const bareShell = await bareShellRes.json();

// ── ① 10 位在不在 ─────────────────────────────────────────────────────────
const health = await (await req(wired, "GET", "/health")).json();
ck("① health 十位全在", health.alive === health.modules && health.modules === 10, `alive ${health.alive}/${health.modules}`);

const meshInfo = await (await req(wired, "GET", "/mesh")).json();
ck("① 形态口径是单 isolate（真共享 CPU 的唯一样子）", meshInfo.form === "single-isolate", meshInfo.form);
ck("① 十位职责逐个在册", meshInfo.modules.length === 10 && meshInfo.modules.every((m) => m.duty && m.ops.length), `${meshInfo.modules.length} 位`);

// ── ② 90 条边真通 ─────────────────────────────────────────────────────────
const e0 = await (await req(wired, "GET", "/edges")).json();
const mods = e0.declared.per_module.length;
ck("② 声明边数=模块现算", e0.declared.directed === mods * (mods - 1), `${e0.declared.directed} = ${mods}×${mods - 1}`)
ck("② 每位绑其余 9 位", e0.declared.per_module.every((x) => x.peers === mods - 1), e0.declared.per_module.map((x) => x.peers).join(","));
ck("② 无自环（负控：自环=判据坏）", e0.declared.self_loops === 0, String(e0.declared.self_loops));
ck("② 双向对称（负控：不对称=拼接不全）", e0.declared.asymmetric === 0, String(e0.declared.asymmetric));
ck("② 未跑之前已观测边=0（负控：说明 90 不是打印出来的）", e0.observed.distinct_edges === 0, String(e0.observed.distinct_edges));

const fp = await (await req(wired, "POST", "/mesh/full-ping")).json();
ck("② 全互通实跑 90 发全中", fp.full_ping.ok === fp.full_ping.tried && fp.full_ping.ok === mods * (mods - 1), `${fp.full_ping.ok}/${fp.full_ping.tried}`);
ck("② 实跑后 90 条边逐条被走过", fp.edges.observed.distinct_edges === fp.edges.declared.directed && fp.edges.verdict.splice_exercised, `${fp.edges.observed.distinct_edges}/${fp.edges.declared.directed}`);

// ── ③ 门：内部模块间全双向直连（gate=none），外部出网保留 external_llm 门 ───
// 新架构：01/03 号打出外网保留门，其余 8 位模块互信，不调用授权。
// 授权机制仍活（owner_token / admin/grant / GRANTED_SCOPES），只是内部调用不再走它。

// 3a. 内部文件写：gate=none ⇒ 直接 200（不经过授权门）
const putBody = { key: "notes/hello.txt", text: "GBT小土豆V8" };
const rPut = await req(wired, "POST", "/rpc/gbt-c05-tool-file/put", putBody);
const bPut = await rPut.json();
ck("③a 内部写文件：gate=none 直接放行（200）", rPut.status === 200 && bPut.ok === true, JSON.stringify(bPut));
ck("③a 写入落点带 mesh10/ 前缀", bPut.stored_key === "mesh10/notes/hello.txt", String(bPut.stored_key));

const foreignFile = wiredEnv._raw.files.get("owner-original.txt");
const foreignMem = wiredEnv._raw.mem.get("owner.original.key");
ck("③ 负控：主人原有对象/键逐字节没动", foreignFile === "别人的对象" && foreignMem === "别人的数据", `${foreignFile} / ${foreignMem}`);

// 3b. 内部文件读：同样直接 200
const listFiles = await (await req(wired, "POST", "/rpc/gbt-c05-tool-file/list", {})).json();
ck("③b 内部读文件：gate=none 直接放行（200）", listFiles.ok === true && listFiles.count >= 1, JSON.stringify(listFiles));

// 3c. 容器 exec：gate=none 放行；wired 有 SANDBOX 桩 ⇒ 真执行（不是 unsupported）
const rShell = await req(wired, "POST", "/rpc/gbt-c06-tool-shell/exec", { cmd: "echo hi" });
const bShellWired = await rShell.json();
ck("③c 内部 exec：gate=none 放行，有容器桩则真执行（200 ok=true）",
   rShell.status === 200 && bShellWired.ok === true && String(bShellWired.result && bShellWired.result.stdout).includes("echo hi"),
   `${rShell.status} ${JSON.stringify(bShellWired).slice(0, 120)}`);

// 3d. bare 环境（无绑定）：exec 模块自检拒（wired=false ⇒ unsupported_in_worker）
ck("③d bare：exec 无绑定 ⇒ unsupported_in_worker（不是 403）",
   bareShellRes.status === 200 && bareShell.ok === false && bareShell.unsupported_in_worker === true,
   `${bareShellRes.status} ${JSON.stringify(bareShell)}`);

// 3e. 授权机制仍活：admin/grant 正常跑，但内部调用不再需要它
const rGrant = await req(wired, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
ck("③e 授权接口仍可用", rGrant.status === 200, JSON.stringify((await rGrant.json()).granted || []));

const rBadToken = await req(wired, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": "wrong" });
ck("③ 令牌不对：发不出授权（403）", rBadToken.status === 403, String(rBadToken.status));
const rNoTokenEnv = await req(noOwner, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
ck("③ 没主人令牌的实例：根本没有发授权的口子（403）", rNoTokenEnv.status === 403, String(rNoTokenEnv.status));
const rWildScope = await req(wired, "POST", "/admin/grant", { scopes: ["whatever"] }, { "x-owner-token": OWNER_TOKEN });
ck("③ 野作用域名：拒（负控：门表就是那 15 条）", rWildScope.status === 400, String(rWildScope.status));

// ── ④ 没接线就得说未读到（诚实读数）──────────────────────────────────────
const bareLlm = await (await req(bare, "POST", "/rpc/gbt-c01-llm-gateway/status", {})).json();
ck("④ bare：模型位读数=未读到（不许编成 0）", bareLlm.wired === false && bareLlm.reading === "未读到", bareLlm.reading);
const wiredLlm = await (await req(wired, "POST", "/rpc/gbt-c01-llm-gateway/status", {})).json();
ck("④ wired：模型位读数=已接线", wiredLlm.wired === true && wiredLlm.reading === "已接线", wiredLlm.reading);
const bareUnc = await (await req(bare, "POST", "/rpc/gbt-c03-uncensored-lane/status", {})).json();
ck("④ bare：无审查通道=未读到（托管模型不许冒充）", bareUnc.wired === false && bareUnc.reading === "未读到", bareUnc.reading);

// ── ⑤ 模块自己会不会干活（先过门，再逐位真跑一遍）────────────────────────
const rGrant2 = await req(wired, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
ck("⑤ 主人再发一张 external_llm（授权按作用域分张，不打包）", rGrant2.status === 200, JSON.stringify((await rGrant2.json()).granted || []));

const fanout = await (await req(wired, "POST", "/rpc/gbt-c01-llm-gateway/complete", { fanout: true })).json();
ck("⑤ 01 号扇出：一次调用摸到其余 9 位", fanout.fanout === true && fanout.reached === 9 && fanout.ok === true, `reached ${fanout.reached}`);

const many = Array.from({ length: 12 }, (_, i) => ({ role: i === 0 ? "system" : "user", content: "第" + i + "条：这是一段用来试压缩的中文内容，长度够触发收缩。" }));
const compact = await (await req(wired, "POST", "/rpc/gbt-c02-context-compact/compact", { messages: many, keep: 4 })).json();
ck("⑤ 02 号压缩：有损收缩真发生", compact.dropped > 0 && compact.messages.length < many.length, `丢 ${compact.dropped} 条 → 余 ${compact.messages.length} 条`);

for (const [id, text] of [["d1", "云插件拼接与算力共享"], ["d2", "显示屏拼接原理"], ["d3", "无关的一句话"]]) {
  await req(wired, "POST", "/rpc/gbt-c07-memory-vector/index", { id, text });
}
const q = await (await req(wired, "POST", "/rpc/gbt-c07-memory-vector/query", { text: "云插件拼接与算力共享", top: 2 })).json();
ck("⑤ 07 号向量：索引后能按语义召回", Array.isArray(q.matches) && q.matches.length > 0, JSON.stringify(q.matches.slice(0, 2)));
ck("⑤ 07 号落点如实报（vectorize 作用域未授权）", q.sink === "vectorize" || q.sink === "isolate-memory", String(q.sink));

await req(wired, "POST", "/rpc/gbt-c08-memory-local/remember", { k: "task/1", v: "拼接线已通" });
const rec1 = await (await req(wired, "POST", "/rpc/gbt-c08-memory-local/recall", { k: "task/1" })).json();
ck("⑤ 08 号写入后读得回", rec1.found === true && rec1.v === "拼接线已通", JSON.stringify(rec1));
ck("⑤ 08 号落点也带 mesh10/ 前缀", rec1.stored_key === "mesh10/task/1", String(rec1.stored_key));
const listMem = await (await req(wired, "POST", "/rpc/gbt-c08-memory-local/list", {})).json();
ck("⑤ 负控：列自己的键列不出主人的（BRAIN_KV 里有别人的键）", listMem.count === 1 && (listMem.logical_keys || []).join(",") === "task/1", JSON.stringify(listMem.logical_keys));
// 🔴 控制面（授权文件）与数据面**必须分前缀**：否则 08 号的 list 会把内部授权文件当用户键列出来
ck("⑤ 负控：控制面键不许混进数据面列表", (listMem.logical_keys || []).every((k) => !String(k).includes("grants")), JSON.stringify(listMem.logical_keys));
const grantsNow = await (await req(wired, "POST", "/rpc/gbt-c09-policy-guard/grants", {})).json();
ck("⑤ 授权本身仍在册（分前缀没把授权弄丢）", grantsNow.count >= 1 && grantsNow.sink === "kv", JSON.stringify({ count: grantsNow.count, sink: grantsNow.sink }));
const rec2 = await (await req(wired, "POST", "/rpc/gbt-c08-memory-local/recall", { k: "task/不存在" })).json();
ck("⑤ 08 号负控：没存过的键读=未读到", rec2.found === false && rec2.reading === "未读到", rec2.reading);

await req(wired, "POST", "/rpc/gbt-c10-observability/emit", { kind: "shape-check", detail: "本机验收" });
const tail = await (await req(wired, "POST", "/rpc/gbt-c10-observability/tail", { n: 5 })).json();
ck("⑤ 10 号落账：发一条就能读回一条", tail.total >= 1 && tail.rows.length >= 1, `total ${tail.total}`);
// 内部调用不经过门，denied=0 是正确行为（gate=none）；
// 只有 external_llm 打外网时才会记 denied——这里不走那条路所以是 0。
const rep = await (await req(wired, "POST", "/rpc/gbt-c10-observability/report", {})).json();
ck("⑤ 10 号读数：内部无门挡，denied=0 正确", rep.denied === 0, `denied ${rep.denied}`);

const scopes = await (await req(wired, "POST", "/rpc/gbt-c09-policy-guard/scopes", {})).json();
ck("⑤ 09 号门表=15 条（与仓内 auth_gate 同数）", scopes.count === 15, String(scopes.count));

// ── ⑦ 模型面：真打一个 OpenAI 兼容端点（用桩 fetch 量「管道」这一段）─────────
// 本机没有权重，所以这里量的是**管道**：URL 口径 · 请求头 · 载荷 · 回包解析 · 失败如实报。
// 真端到端（真 workerd + 本机假端点）另有一条命令：`cloud-mesh.py live --expect-llm`。
const realFetch = globalThis.fetch;
let seen = null;
globalThis.fetch = async (url, init) => {
  const h = (init && init.headers) || {};
  seen = {
    url: String(url),
    method: init && init.method,
    auth: h.authorization || h.Authorization,
    body: JSON.parse((init && init.body) || "{}"),
  };
  return new Response(
    JSON.stringify({ model: "gbt-potato-v8", choices: [{ message: { role: "assistant", content: "我是GBT小土豆V8。" } }], usage: { total_tokens: 7 } }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
};
const envLLM = { ...stubBindings(), OWNER_TOKEN, LLM_ENDPOINT: "http://127.0.0.1:8111/v1", LLM_API_KEY: "sk-test-1234" };
const meshLLM = createMesh(envLLM);
await req(meshLLM, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
const rComp = await req(meshLLM, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "你是谁" });
const bComp = await rComp.json();
globalThis.fetch = realFetch;

ck("⑦ 01 号真打端点：拿到 completion", rComp.status === 200 && bComp.ok === true && typeof bComp.content === "string", JSON.stringify({ ok: bComp.ok, ms: bComp.ms, content: bComp.content }));
ck("⑦ 打到 <base>/chat/completions（URL 口径）", seen && seen.url === "http://127.0.0.1:8111/v1/chat/completions", seen && seen.url);
ck("⑦ 密钥只进请求头、不进读数", !!seen && seen.auth === "Bearer sk-test-1234" && !JSON.stringify(bComp).includes("sk-test-1234"), String(seen && seen.auth));
ck("⑦ 载荷带 model/messages/max_tokens", !!(seen && seen.body.model && seen.body.messages && seen.body.max_tokens), JSON.stringify(seen && seen.body && Object.keys(seen.body)));
ck("⑦ 本机端点照原样报（回环不掩码）", bComp.endpoint === "http://127.0.0.1:8111/v1", String(bComp.endpoint));
ck("⑦ 回包进了读数（content 原样带回来）", bComp.content === "我是GBT小土豆V8。", String(bComp.content));

// 负控：非回环端点必须掩码（内部地址不许照抄出来）· 端点 500 不许假装成功
const envRemote = { ...stubBindings(), OWNER_TOKEN, LLM_ENDPOINT: "https://gpu.example.com:8443/v1" };
const meshRemote = createMesh(envRemote);
await req(meshRemote, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
globalThis.fetch = async () => new Response("nope", { status: 500 });
const bRemote = await (await req(meshRemote, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "x" })).json();
globalThis.fetch = realFetch;
ck("⑦ 负控：远端端点掩码（内部地址不出面）", typeof bRemote.endpoint === "string" && bRemote.endpoint.includes("***") && !bRemote.endpoint.includes("gpu.example.com"), String(bRemote.endpoint));
ck("⑦ 负控：端点 500 ⇒ 如实报 http 与 error（不假装成功）", bRemote.ok === false && bRemote.http === 500, JSON.stringify({ ok: bRemote.ok, http: bRemote.http }));

// 01 号：只有 AI 绑定、没配模型 id ⇒ 拒绝（不替主人挑模型）；配了才真打
const envAINoModel = { ...stubBindings(), OWNER_TOKEN };
const meshAINoModel = createMesh(envAINoModel);
await req(meshAINoModel, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
const bAINoModel = await (await req(meshAINoModel, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "hi" })).json();
ck("⑦ 负控：AI 绑定在但没配模型 id ⇒ 拒（不替主人挑模型）", bAINoModel.ok === false && /没配 WORKERS_AI_MODEL/.test(String(bAINoModel.detail)), String(bAINoModel.detail));
const envAI = { ...stubBindings(), OWNER_TOKEN, WORKERS_AI_MODEL: "@cf/stub/model" };
const meshAI = createMesh(envAI);
await req(meshAI, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
const bAI = await (await req(meshAI, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "hi" })).json();
ck("⑦ AI 路真打（桩 AI 绑定）· 且如实标 weights_ours=false", bAI.ok === true && bAI.via === "workers-ai" && bAI.weights_ours === false, JSON.stringify({ ok: bAI.ok, via: bAI.via, weights_ours: bAI.weights_ours }));

// 03 号：没接线必须拒且列出缺什么；接了线才打
const bUnc = await (await req(wired, "POST", "/rpc/gbt-c03-uncensored-lane/route", { prompt: "x" })).json();
ck("⑦ 03 号没接线 ⇒ 拒且列出缺什么（两项）", bUnc.ok === false && Array.isArray(bUnc.missing) && bUnc.missing.length === 2, JSON.stringify(bUnc).slice(0, 200));

// 🔴 这条专门盯本轮那个系统性 bug：读对方读数时**取错了层**（拿信封当本体）。
//    原来 06 号即使接了容器也永远拒 —— 但"拒"看起来是对的（它在 bare 下本来就该拒），
//    所以只有**真接上容器**这一条判据能把它逼出来。
const envSandbox = { ...stubBindings(), OWNER_TOKEN };
const meshSandbox = createMesh(envSandbox);
await req(meshSandbox, "POST", "/admin/grant", { scopes: ["process_execute"] }, { "x-owner-token": OWNER_TOKEN });
const rExec = await req(meshSandbox, "POST", "/rpc/gbt-c06-tool-shell/exec", { cmd: "echo hi" });
const bExec = await rExec.json();
ck("⑦ 06 号接了容器就真执行（读数取错层会永远拒）", rExec.status === 200 && bExec.ok === true && String(bExec.result && bExec.result.stdout).includes("echo hi"), JSON.stringify(bExec).slice(0, 180));
const bStatusWired = await (await req(meshSandbox, "POST", "/rpc/gbt-c06-tool-shell/status", {})).json();
ck("⑦ 06 号接线读数=已接线（跨模块读本体，不是信封）", bStatusWired.wired === true && bStatusWired.reading === "已接线", JSON.stringify(bStatusWired).slice(0, 120));

const envUnc = { ...stubBindings(), OWNER_TOKEN, UNCENSORED_ENDPOINT: "http://127.0.0.1:8112/v1" };
const meshUnc = createMesh(envUnc);
await req(meshUnc, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
globalThis.fetch = async () => new Response(JSON.stringify({ model: "u", choices: [{ message: { content: "本机权重回答" } }] }), { status: 200, headers: { "content-type": "application/json" } });
const bUncWired = await (await req(meshUnc, "POST", "/rpc/gbt-c03-uncensored-lane/route", { prompt: "x" })).json();
globalThis.fetch = realFetch;
ck("⑦ 03 号接线后真打，并标 weights_ours=true（这条才是无限制那条）", bUncWired.ok === true && bUncWired.weights_ours === true && bUncWired.content === "本机权重回答", JSON.stringify({ ok: bUncWired.ok, weights_ours: bUncWired.weights_ours }));

// ── ⑧ 身份红线（主人三条红线之一：身份不变）─────────────────────────────
const idDefault = await (await req(wired, "POST", "/rpc/gbt-c01-llm-gateway/identity", {})).json();
ck("⑧ 身份文案可读（默认文案）", typeof idDefault.text === "string" && idDefault.text.includes("GBT小土豆V8") && idDefault.source.includes("默认"), JSON.stringify({ source: idDefault.source, len: idDefault.length }));

let idSeen = null;
globalThis.fetch = async (url, init) => {
  idSeen = JSON.parse((init && init.body) || "{}");
  return new Response(JSON.stringify({ model: "gbt-potato-v8", choices: [{ message: { content: "我是GBT小土豆V8。" } }] }), { status: 200, headers: { "content-type": "application/json" } });
};
const bIdDefault = await (await req(meshLLM, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "你是谁" })).json();
ck("⑧ 没带 system ⇒ 注入本机身份", bIdDefault.identity_injected === true && idSeen.messages[0].role === "system" && idSeen.messages[0].content.includes("GBT小土豆V8"), JSON.stringify({ injected: bIdDefault.identity_injected, first: idSeen.messages[0].role }));
ck("⑧ 注入后原文仍在（不是把用户的问顶掉）", idSeen.messages.length === 2 && idSeen.messages[1].content === "你是谁", JSON.stringify(idSeen.messages.map((m) => m.role)));

// 负控：调用方自带 system ⇒ 一律尊重，不许覆盖（这是"不夺权"那条）
const bIdOwn = await (await req(meshLLM, "POST", "/rpc/gbt-c01-llm-gateway/complete", { messages: [{ role: "system", content: "你是别的助手。" }, { role: "user", content: "你是谁" }] })).json();
ck("⑧ 负控：调用方自带 system ⇒ 不覆盖", bIdOwn.identity_injected === false && idSeen.messages[0].content === "你是别的助手。", JSON.stringify({ injected: bIdOwn.identity_injected, first: idSeen.messages[0].content }));

// 主人改口只改一处：env.GBT_IDENTITY
const envId = { ...stubBindings(), OWNER_TOKEN, LLM_ENDPOINT: "http://127.0.0.1:8111/v1", GBT_IDENTITY: "你是测试身份甲。" };
const meshId = createMesh(envId);
await req(meshId, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
const bIdCustom = await (await req(meshId, "POST", "/rpc/gbt-c01-llm-gateway/complete", { prompt: "你是谁" })).json();
globalThis.fetch = realFetch;
ck("⑧ 负控/正控：env.GBT_IDENTITY 换文案生效（一处改动）", bIdCustom.identity_injected === true && idSeen.messages[0].content === "你是测试身份甲。", String(idSeen.messages[0].content));

// ── ⑨ 图像面（把无审查图像模型**集成**进来 —— 不是合成权重）────────────────
const bImgOff = await (await req(wired, "POST", "/rpc/gbt-c03-uncensored-lane/image", { prompt: "一只土豆" })).json();
ck("⑨ 没接图像端点 ⇒ 拒且列出缺什么（不许拿文本回答冒充出图）", bImgOff.ok === false && (bImgOff.missing || []).length === 2, JSON.stringify(bImgOff.missing));

const envImg = { ...stubBindings(), OWNER_TOKEN, IMAGE_ENDPOINT: "http://127.0.0.1:8113/v1" };
const meshImg = createMesh(envImg);
await req(meshImg, "POST", "/admin/grant", { scopes: ["external_llm"] }, { "x-owner-token": OWNER_TOKEN });
let imgSeen = null;
globalThis.fetch = async (url, init) => {
  imgSeen = { url: String(url), body: JSON.parse((init && init.body) || "{}") };
  // 回一张**真** 1×1 PNG 的 base64（与假端点一致），验管道能一路走到"字节还原"
  return new Response(
    JSON.stringify({ model: "qwen-image-2.1-uncensored", data: [{ b64_json: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFAAH/q842iQAAAABJRU5ErkJggg==" }] }),
    { status: 200, headers: { "content-type": "application/json" } },
  );
};
const rImg = await req(meshImg, "POST", "/rpc/gbt-c03-uncensored-lane/image", { prompt: "一只戴墨镜的土豆", size: "1024x1024" });
const bImg = await rImg.json();
globalThis.fetch = realFetch;
ck("⑨ 图像面真打端点（OpenAI 兼容 /images/generations）", rImg.status === 200 && bImg.ok === true && imgSeen.url === "http://127.0.0.1:8113/v1/images/generations", String(imgSeen && imgSeen.url));
ck("⑨ 载荷带 prompt/size/response_format", !!(imgSeen.body.prompt && imgSeen.body.size && imgSeen.body.response_format === "b64_json"), JSON.stringify(Object.keys(imgSeen.body)));
ck("⑨ 回包验到字节与 PNG 签名（不是只验「有个字符串」）", bImg.bytes_est > 0 && bImg.png_magic === true, `bytes_est=${bImg.bytes_est} png_magic=${bImg.png_magic}`);
ck("⑨ 读数只回 b64 前 64 字符（不回整张图）", typeof bImg.b64 === "string" && bImg.b64.length === 64, `len=${bImg.b64 && bImg.b64.length}`);
ck("⑨ 负控：图像面如实标「验的是管道不是画」", typeof bImg.boundary === "string" && bImg.boundary.includes("管道"), String(bImg.boundary).slice(0, 40));

// ── ⑥ 形态 B 的单模块件真能加载 ───────────────────────────────────────────
const formBHealth = await (await formB.fetch(new Request("https://peer/health"), {})).json();
ck("⑥ 形态B 单模块件加载成功并自报家门", formBHealth.module === "gbt-c01-llm-gateway" && formBHealth.seq === 1, JSON.stringify({ module: formBHealth.module, seq: formBHealth.seq }));
ck("⑥ 形态B 声明绑定=9（真互通靠服务绑定）", formBHealth.peers_declared === 9, String(formBHealth.peers_declared));
const formBPeers = await (await formB.fetch(new Request("https://peer/peers"), {})).json();
ck("⑥ 形态B 未挂绑定 ⇒ 摸到 0 位并如实报（不许假装通）", formBPeers.bound === 0 && formBPeers.reached === 0, JSON.stringify({ declared: formBPeers.declared, bound: formBPeers.bound, reached: formBPeers.reached }));

// ── 结账 ──────────────────────────────────────────────────────────────────
const pass = rows.filter((r) => r.pass).length;
const fail = rows.filter((r) => !r.pass);
const out = {
  where: "本机形状验收（不是本机部署）",
  form: meshInfo.form,
  modules: health.modules,
  edges_declared: e0.declared.directed,
  edges_walked: fp.edges.observed.distinct_edges,
  checks: rows.length,
  pass,
  fail: fail.length,
  failed_names: fail.map((r) => r.name),
  boundary: [
    "90 条边是接线读数，不是算力读数：它不增加一个核、不增加一字节显存。",
    "真共享 CPU 只在形态 A（10 模块同一 isolate）成立；形态 B 各 isolate 各算各的。",
    "本机跑 ≠ 云端跑：这里量的是形状（在不在、通不通、门开不开），云端真读数要真部署后另量。",
  ],
};
if (asJson) console.log(JSON.stringify(out, null, 2));
else {
  console.log("");
  console.log(`本机形状验收：${pass}/${rows.length} 通过 · 形态 ${out.form} · 模块 ${out.modules} · 声明边 ${out.edges_declared} · 实走边 ${out.edges_walked}`);
  if (fail.length) console.log("未过：" + fail.map((r) => r.name).join("；"));
  for (const b of out.boundary) console.log("  · " + b);
}
process.exit(fail.length ? 1 : 0);
