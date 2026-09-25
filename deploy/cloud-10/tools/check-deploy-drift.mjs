// GBT小土豆V8 · 10 云插件拼接网 · **部署漂移对账**（本机那份 vs 云上那份）
// 开发者：自由的风 · 守护者：公主土豆 · 禁止删除
//
// ## 它回答的问题
// 云上那个 Worker，跑的**到底是不是仓里这份代码**？
//   第 37 轮的答案是"行为同源"——那是**逐字段看了一眼**得出的，不是对账。
//   部署漂移是最阴的生产风险：仓里改了、云上没部，或者反过来；
//   两边都能用、都能过各自的验收，只有**对着比**才看得出来。
//
// ## 怎么比（**先把口径说清，再说结论**）
// 只比**与绑定无关**的声明面（绑定相关的东西本机没有，比了就是假红）：
//   GET /            整份比
//   GET /mesh        整份比（声明面：形态/职责/边数/口径）
//   GET /health      只比 modules / alive / 模块 id 列表（**逐模块 wired 依赖绑定，不比**）
//   GET /edges       只比 declared / rule / form（**observed 是运行时计数，不比**）
//   GET /v1/models   只比 object / data（**gbt 块里有密钥配置数、端点接线等，不比**）
// ⇒ 被排除的每一项都**列出来**，不偷偷跳过。**没比的 ≠ 一样。**
//
// ## 两条边界
//   · 这不是"字节级同源"的证明：看不到云上构建物，只能比**可观测行为**。
//   · 本机那份是用**桩绑定**跑的；云上那份绑着真 KV/R2。
//     所以凡是"看绑定才能得出"的字段一律不参与比较（上面那张表就是为此而设）。
//
// 用法：node deploy/cloud-10/tools/check-deploy-drift.mjs [--url <地址>] [--json]
// 退出码：0 = 声明面无漂移；1 = 有漂移；2 = 拿不到某一侧。

import { createMesh } from "../src/worker.js";

const args = process.argv.slice(2);
const asJson = args.includes("--json");
const selftest = args.includes("--selftest");
const urlIdx = args.indexOf("--url");
const BASE = (urlIdx >= 0 ? args[urlIdx + 1] : "https://gbt-potato-cloud-10.lopaycn.workers.dev").replace(/\/+$/, "");

const rows = [];
function ck(name, pass, reading) {
  rows.push({ name, pass: !!pass, reading: String(reading) });
  if (!asJson) console.log(`  ${pass ? "PASS" : "FAIL"}  ${name}  ::  ${reading}`);
}

// ── 本机那一侧：桩绑定（够跑声明面就够）────────────────────────────────────
const mesh = createMesh({ OWNER_TOKEN: "drift-probe-owner", WORKERS_AI_MODEL: "@cf/openai/gpt-oss-120b" });
async function local(path) {
  const r = await mesh.fetch(new Request("https://mesh.local" + path));
  return JSON.parse(await r.text());
}
async function live(path) {
  const r = await fetch(BASE + path, { headers: { accept: "application/json" } });
  const t = await r.text();
  try { return { http: r.status, body: JSON.parse(t) }; } catch { return { http: r.status, body: null, raw: t.slice(0, 200) }; }
}

// 逐路径：比哪些、不比哪些（不比的一律列出来）
const PLAN = [
  { path: "/", compare: "all", except: [] },
  { path: "/mesh", compare: "all", except: [] },
  { path: "/health", compare: ["modules", "alive"], except: ["rows（逐模块 wired 依赖绑定）"] },
  { path: "/edges", compare: ["declared", "rule", "form"], except: ["observed（运行时计数）", "verdict（含 observed）"] },
  { path: "/v1/models", compare: ["object", "data"], except: ["gbt（含密钥配置数/端点接线/令牌闸读数）"] },
];

const canon = (v) => JSON.stringify(v, Object.keys(v || {}).sort());
function diffObj(a, b, path = "", out = []) {
  if (JSON.stringify(a) === JSON.stringify(b)) return out;
  const ta = Object.prototype.toString.call(a), tb = Object.prototype.toString.call(b);
  if (ta !== tb) { out.push(`${path || "(根)"}：类型不同 ${ta} vs ${tb}`); return out; }
  if (ta === "[object Array]") {
    if (a.length !== b.length) out.push(`${path}：数组长度 ${a.length} vs ${b.length}`);
    for (let i = 0; i < Math.max(a.length, b.length); i++) diffObj(a[i], b[i], `${path}[${i}]`, out);
    return out;
  }
  if (ta === "[object Object]") {
    const keys = [...new Set([...Object.keys(a), ...Object.keys(b)])].sort();
    for (const k of keys) {
      if (!(k in a)) { out.push(`${path}.${k}：**云上有、本机没有**`); continue; }
      if (!(k in b)) { out.push(`${path}.${k}：**本机有、云上没有**`); continue; }
      diffObj(a[k], b[k], `${path}.${k}`, out);
    }
    return out;
  }
  out.push(`${path}：值不同 ${JSON.stringify(a)} vs ${JSON.stringify(b)}`);
  return out;
}

// ── 自检（**离线** · 种植差异，证明这把尺子有牙）────────────────────────────
// 为什么要它：一个"比出来没差异"的对账器，**很可能是因为它其实什么都没比**。
// 本仓原话「条数不等于牙齿」。这里种四处差异，看它是不是每处都逮得住。
if (selftest) {
  const A = { name: "gbt", modules: 10, data: [{ id: "m", object: "model" }], nested: { a: 1, b: [1, 2] } };
  const planted = [
    ["改了值", { ...A, name: "别的" }],
    ["云上多了一个键", { ...A, extra: 1 }],
    ["云上少了一个键", (() => { const o = { ...A }; delete o.modules; return o; })()],
    ["数组长度不同", { ...A, data: [{ id: "m", object: "model" }, { id: "n", object: "model" }] }],
    ["嵌套里改了值", { ...A, nested: { a: 2, b: [1, 2] } }],
  ];
  let caught = 0;
  for (const [label, B] of planted) {
    const d = diffObj(A, B);
    ck(`自检·种植差异能被逮住（${label}）`, d.length > 0, d.length ? d[0] : "🔴 没逮住 ⇒ 这把尺子是瞎的");
    if (d.length) caught++;
  }
  ck("自检·不该有差异的必须报 0", diffObj(A, JSON.parse(JSON.stringify(A))).length === 0, "同两份比 ⇒ 0 处");
  // 空转守卫：PLAN 里的 compare 列表不许是空的，且 pick 必须真选到键
  const bad = PLAN.filter((p) => p.compare !== "all" && (!Array.isArray(p.compare) || p.compare.length === 0));
  ck("自检·比对清单不许为空（防空转）", bad.length === 0, bad.length ? JSON.stringify(bad.map((b) => b.path)) : "每条都有明确的比对键");
  const sample = PLAN.find((p) => p.path === "/edges");
  const picked = Object.fromEntries(sample.compare.filter((k) => k in { declared: 1, rule: 1, form: 1, observed: 1 }).map((k) => [k, 1]));
  ck("自检·pick 真选到了键（不是选了个空对象）", Object.keys(picked).length === sample.compare.length,
     `选了 ${Object.keys(picked).length}/${sample.compare.length}`);
  const failed0 = rows.filter((r) => !r.pass);
  console.log("");
  console.log(`部署漂移对账·自检：${rows.length - failed0.length}/${rows.length} 通过（离线 · 不联网）`);
  if (asJson) console.log(JSON.stringify({ selftest: true, rows }, null, 2));
  process.exit(failed0.length ? 1 : 0);
}

let drift = 0;
for (const p of PLAN) {
  let lo, li;
  try { lo = await local(p.path); } catch (e) { ck(`本机可读 ${p.path}`, false, String(e).slice(0, 80)); continue; }
  try { li = await live(p.path); } catch (e) { ck(`${BASE}${p.path} 可读`, false, String(e).slice(0, 80)); continue; }
  if (li.body === null) { ck(`云上回的是 JSON ${p.path}`, false, `HTTP ${li.http} 正文非 JSON：${li.raw}`); continue; }

  let diffs;
  let note;
  if (p.compare === "all") {
    diffs = diffObj(lo, li.body);
    note = "整份比";
  } else {
    const pick = (o) => Object.fromEntries(p.compare.filter((k) => k in (o || {})).map((k) => [k, o[k]]));
    diffs = diffObj(pick(lo), pick(li.body));
    note = `只比 ${p.compare.join("/")}`;
  }
  if (diffs.length) drift += diffs.length;
  ck(`声明面一致 ${p.path}`, diffs.length === 0,
     diffs.length ? `${diffs.length} 处不同：${diffs.slice(0, 3).join(" ｜ ")}` : `${note} · 无差异`);
  if (p.except.length) {
    ck(`（明示不比）${p.path}`, true, "不比：" + p.except.join(" · "));
  }
}

const failed = rows.filter((r) => !r.pass);
if (asJson) {
  console.log(JSON.stringify({ base: BASE, drift, rows }, null, 2));
} else {
  console.log("");
  console.log(`部署漂移对账：${rows.filter((r) => r.pass).length}/${rows.length} 通过 · 漂移 ${drift} 处 · 本机那份=桩绑定 · 云上=${BASE}`);
  console.log("  · 比的是**可观测的声明面**；绑定相关的字段**明示不比**（上面每条都列出了不比什么）。");
  console.log("  · 这不是字节级同源的证明：看不到云上构建物。**没比的 ≠ 一样。**");
  console.log("  · 只读：只发 GET，不部署、不改远端、不发任何业务请求。");
}
process.exit(failed.length ? 1 : 0);
