// R-H165（2026-09-19）：本表行号按 caps_registry.py **实际行号**刷新（因 sched_define 后新增约 30 行而漂移；非静默改数）
/* GBT小土豆V8 · 上帝视角 · 主进程骨架（W3）
 *
 * 职责（《W3上帝视角镜像方案.md》§2.2）：
 *   单例锁 · 窗口注册表（windows.json）· 托盘（图标运行时生成，维度不放二进制）
 *   · 布局持久化（userData/window-layout.json，越界回落主屏）· 吸附
 *   · 只读 IPC（渲染进程零写口）· 主进程侧订阅 /api/events
 *
 * 为什么 SSE 订阅在主进程：panel_server 的 _send_json 不发 CORS 头，
 * 渲染进程从 file:// 直接 fetch 会被浏览器拦死；给它加头就是动生产代码（本轮红线）。
 * 所以订阅者前移到主进程，推送通道**仍是同一条 /api/events**，不新增第二套。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
"use strict";

const { app, BrowserWindow, Tray, Menu, ipcMain, screen, nativeImage, shell } = require("electron");
const fs = require("fs");
const path = require("path");
const http = require("http");
const zlib = require("zlib");
const crypto = require("crypto");
const { execFile, spawn } = require("child_process");
const layout = require("./layout.cjs");
const features = require("./features.cjs");
const chrome = require("./chrome.cjs");
const os = require("os");

const HERE = __dirname;
const PANEL = process.env.GBT_PANEL_URL || "http://127.0.0.1:8765";
const READONLY_NOTE = "只读态：自检结果仅 UI 显示，不落盘";

function findRepoRoot(start) {
  let cur = start;
  for (let i = 0; i < 12; i++) {
    if (fs.existsSync(path.join(cur, "gbt_allinone"))) return cur;
    const up = path.dirname(cur);
    if (up === cur) break;
    cur = up;
  }
  return null;
}

const ROOT = findRepoRoot(HERE);
const STORE = ROOT ? path.join(ROOT, "gbt_allinone", "store") : null;
const DOCS = ROOT ? path.join(ROOT, "gbt_allinone", "docs") : null;
const LAYOUT_FILE = path.join(app.getPath("userData"), "window-layout.json");

function readRegistry() {
  const file = path.join(HERE, "windows.json");
  try {
    const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
    if (parsed && Array.isArray(parsed.windows)) return parsed;
  } catch (err) {
    /* 注册表坏了就当空的，不抛 */
  }
  return { version: 1, windows: [] };
}

/* ── 托盘图标：运行时生成，维度里不放二进制 ── */

function crcTable() {
  const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c;
  }
  return t;
}
const CRC_T = crcTable();

function crc32(buf) {
  let c = 0xffffffff;
  for (let i = 0; i < buf.length; i++) c = CRC_T[(c ^ buf[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function pngChunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length, 0);
  const body = Buffer.concat([Buffer.from(type, "ascii"), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body), 0);
  return Buffer.concat([len, body, crc]);
}

function trayIcon(size, fill, edge) {
  const stride = size * 4 + 1;
  const raw = Buffer.alloc(stride * size);
  for (let y = 0; y < size; y++) {
    raw[y * stride] = 0;
    for (let x = 0; x < size; x++) {
      const o = y * stride + 1 + x * 4;
      const onEdge = x === 0 || y === 0 || x === size - 1 || y === size - 1;
      const c = onEdge ? edge : fill;
      raw[o] = c[0]; raw[o + 1] = c[1]; raw[o + 2] = c[2]; raw[o + 3] = 0xff;
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(size, 0);
  ihdr.writeUInt32BE(size, 4);
  ihdr[8] = 8; ihdr[9] = 6; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  const png = Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
    pngChunk("IHDR", ihdr),
    pngChunk("IDAT", zlib.deflateSync(raw)),
    pngChunk("IEND", Buffer.alloc(0)),
  ]);
  return nativeImage.createFromBuffer(png);
}

/* ── 只读数据口 ── */

function tailLines(file, maxBytes, maxLines) {
  const st = fs.statSync(file);
  const start = Math.max(0, st.size - maxBytes);
  const fd = fs.openSync(file, "r");
  const buf = Buffer.alloc(st.size - start);
  try {
    fs.readSync(fd, buf, 0, buf.length, start);
  } finally {
    fs.closeSync(fd);
  }
  const lines = buf.toString("utf8").split(/\r?\n/).filter((s) => s.trim());
  if (start > 0 && lines.length) lines.shift();   /* 首行多半被截断，丢掉 */
  return lines.slice(-maxLines);
}

function ok(data) { return { ok: true, data: data }; }
function no(error, extra) { return Object.assign({ ok: false, error: error }, extra || {}); }

function httpGetJson(url, timeoutMs) {
  return new Promise((resolve) => {
    const req = http.get(url, (res) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (d) => { body += d; });
      res.on("end", () => {
        if (res.statusCode !== 200) return resolve(no("HTTP " + res.statusCode));
        try { resolve(ok(JSON.parse(body))); }
        catch (err) { resolve(no("响应不是 JSON")); }
      });
    });
    req.on("error", (err) => resolve(no(String(err.message || err))));
    req.setTimeout(timeoutMs || 2500, () => { req.destroy(); resolve(no("超时")); });
  });
}

function w3State() { return httpGetJson(PANEL + "/api/state", 2500); }

/* ── R-H295 · 把框架自己的只读审计接进上帝视角 ──
 *
 * 欠账出处：docs/待落刀登记.md
 *   · 「覆盖审计接进上帝视角（实时显示覆盖率与死角）」—— **未接**
 *   · 「把零调用点清单接进上帝视角 / 工作区（定期扫、可点名）」—— **未接**
 *
 * 为什么以前接不上：`:8765` 的 `/api/capability` 是**异步**口 —— 它返回
 * `{accepted, deferred, request_id}`，真结果由 `cap_result` 事件从 `/api/events`
 * 送回来（panel_server.py:2290-2311）。渲染进程从 file:// 直接 fetch 会被 CORS 拦死
 * （见本文件头注），所以「调能力 + 等结果」这件事只能在主进程做。
 * 本函数就是补上这半截：POST 拿 request_id → 在该表上等 SSE 送回同名 request_id。
 */
const CAP_PENDING = new Map();

function httpPostJson(pathname, bodyObj, timeoutMs) {
  return new Promise((resolve) => {
    const data = Buffer.from(JSON.stringify(bodyObj || {}), "utf8");
    const m = PANEL.match(/^https?:\/\/([^\/:]+)(?::(\d+))?/);
    const req = http.request({
      host: (m && m[1]) || "127.0.0.1",
      port: Number((m && m[2]) || 8765),
      path: pathname,
      method: "POST",
      headers: { "Content-Type": "application/json",
                 "Content-Length": data.length },
    }, (res) => {
      let raw = "";
      res.setEncoding("utf8");
      res.on("data", (d) => { raw += d; });
      res.on("end", () => {
        if (res.statusCode !== 200) return resolve(no("HTTP " + res.statusCode));
        try { resolve(ok(JSON.parse(raw))); }
        catch (e) { resolve(no("响应不是 JSON")); }
      });
    });
    req.on("error", (err) => resolve(no(String(err.message || err))));
    req.setTimeout(timeoutMs || 30000, () => { req.destroy(); resolve(no("超时")); });
    req.write(data);
    req.end();
  });
}

/* 调一个能力并把结果等回来。
 *
 * R-H295：**自带订阅**，不复用全局那条 SSE。原因：app.whenReady() 里
 * registerIpc → createWindow → buildTray → refreshTrayMenu → startSse 是**一条不断的链**，
 * 上游任一环抛错（例如托盘图标构造失败）整条链就在 .catch 里结束，startSse 永远不会跑 ——
 * 那时"能力调用超时"看起来像能力坏了，其实是订阅压根没建。
 * 本函数自己开一条 /api/events 只等自己那个 request_id，拿到即断，与托盘/窗口解耦。
 * 超时如实报超时，不拿空对象冒充成功。
 */
function callCapability(kind, payload, waitMs) {
  return new Promise((resolve) => {
    const data = Buffer.from(JSON.stringify({
      kind: kind, payload: payload || {}, confirm: true,
    }), "utf8");
    const m = PANEL.match(/^https?:\/\/([^\/:]+)(?::(\d+))?/);
    const host = (m && m[1]) || "127.0.0.1";
    const port = Number((m && m[2]) || 8765);
    const deadline = Date.now() + (waitMs || 60000);
    let settled = false;
    let sseReq = null;

    function finish(value) {
      if (settled) return;
      settled = true;
      if (sseReq) { try { sseReq.destroy(); } catch (e) { /* 已断 */ } }
      resolve(value);
    }

    /* 先挂订阅，再发调用 —— 反过来会漏掉"结果比订阅先到"的窗口 */
    sseReq = http.get({ host: host, port: port, path: "/api/events" }, (res) => {
      if (res.statusCode !== 200) { finish(no("事件流 HTTP " + res.statusCode)); return; }
      let buf = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        buf += chunk;
        let idx = buf.indexOf("\n\n");
        while (idx >= 0) {
          const block = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          const dataLines = [];
          const lines = block.split("\n");
          for (let li = 0; li < lines.length; li++) {
            const t = lines[li].replace(/\r$/, "");
            if (t.indexOf("data:") === 0) dataLines.push(t.slice(5).replace(/^ /, ""));
          }
          if (!dataLines.length) { idx = buf.indexOf("\n\n"); continue; }
          try {
            const ev = JSON.parse(dataLines.join("\n"));
            if (ev && ev.type === "cap_result" && ev.request_id === rid) {
              finish(ok({ kind: ev.kind, request_id: ev.request_id,
                          result: ev.result === undefined ? null : ev.result }));
            }
          } catch (e) { /* 非 JSON 忽略 */ }
          idx = buf.indexOf("\n\n");
        }
      });
      res.on("end", () => { /* 服务端断流：交给下面的超时兜底 */ });
    });
    sseReq.on("error", (err) => finish(no("事件流断开：" + String(err.message || err))));

    let rid = null;
    const posted = http.request({
      host: host, port: port, path: "/api/capability", method: "POST",
      headers: { "Content-Type": "application/json", "Content-Length": data.length },
    }, (res) => {
      let raw = "";
      res.setEncoding("utf8");
      res.on("data", (d) => { raw += d; });
      res.on("end", () => {
        let meta = {};
        try { meta = JSON.parse(raw); } catch (e) { finish(no("能力口响应不是 JSON")); return; }
        if (!meta.ok) { finish(no(meta.error || "能力口拒绝")); return; }
        if (meta.needs_confirmation) {
          finish(no("能力层要求二次确认，主进程未代确认（不绕门）",
                    { kind: kind, needs_confirmation: true }));
          return;
        }
        if (!meta.request_id) { finish(no("面板未回 request_id（异步口口径变了？）", meta)); return; }
        rid = meta.request_id;
        const timer = setInterval(() => {
          if (Date.now() > deadline) {
            clearInterval(timer);
            finish(no("等结果超时（" + Math.round((waitMs || 60000) / 1000) + "s）：cap_result 没回来",
                      { request_id: rid }));
          }
        }, 250);
      });
    });
    posted.on("error", (err) => finish(no("能力口断开：" + String(err.message || err))));
    posted.setTimeout(15000, () => { posted.destroy(); finish(no("能力口超时")); });
    posted.write(data);
    posted.end();
  });
}

/* SSE 分发：命中等待表就把结果交回去（其余事件照旧广播给渲染层） */
function settleCapPending(ev) {
  if (!ev || ev.request_id === undefined) return false;
  const slot = CAP_PENDING.get(ev.request_id);
  if (!slot) return false;
  CAP_PENDING.delete(ev.request_id);
  clearTimeout(slot.timer);
  slot.resolve(ok({ kind: ev.kind, request_id: ev.request_id,
                    result: ev.result === undefined ? null : ev.result }));
  return true;
}

/* 覆盖率审计（实时：每次调用现跑框架那只只读审计器，不存快照、不猜） */
async function w3Coverage() {
  const r = await callCapability("coverage_auditor", {}, 60000);
  if (!r.ok) return r;
  const body = (r.data && r.data.result) || {};
  const inner = body.result && typeof body.result === "object" ? body.result : body;
  return ok({
    readonly: true,
    note: "实时跑 coverage_auditor（只读审计器）；覆盖率与死角以它为准，面板不做二次判读。",
    at: new Date().toISOString(),
    raw: inner,
  });
}

/* 渲染进化的最优基因（欠账：「进 trace_store · 工作区可跑实验 · 上帝视角显示最优基因」—— 未接）。
   同 coverage/orphans：实时现跑 render_evolution，不落快照。
   诚实口径：现在 genomes=0 —— 面板就该显示「还没有最优基因」，不许拿某个默认值冒充
   （该能力自己的红线第 1 条就是「无基线不许进化」）。 */
async function w3Gene() {
  const r = await callCapability("render_evolution", {}, 60000);
  if (!r.ok) return r;
  const body = (r.data && r.data.result) || {};
  const inner = body.result && typeof body.result === "object" ? body.result : body;
  return ok({
    readonly: true,
    note: "实时跑 render_evolution（只读）；最优基因与实验数以它为准。0 代就如实写 0 代。",
    at: new Date().toISOString(),
    raw: inner,
  });
}


async function w3Orphans() {
  const r = await callCapability("caps_called_audit", {}, 60000);
  if (!r.ok) return r;
  const body = (r.data && r.data.result) || {};
  const inner = body.result && typeof body.result === "object" ? body.result : body;
  return ok({
    readonly: true,
    note: "实时跑 caps_called_audit（只读审计器）；孤儿口径以它自己的 rule 字段为准。",
    at: new Date().toISOString(),
    raw: inner,
  });
}


function w3Tasks() {
  const file = path.join(STORE, "tasks.json");
  try {
    const parsed = JSON.parse(fs.readFileSync(file, "utf8"));
    const tasks = Array.isArray(parsed.tasks) ? parsed.tasks : [];
    return ok({ next_id: parsed.next_id, total: tasks.length, tasks: tasks.slice(-8) });
  } catch (err) {
    return no("tasks.json 读不动：" + String(err.message || err));
  }
}

function w3Env() {
  return new Promise((resolve) => {
    const code = "import json,sys;sys.path.insert(0," + JSON.stringify(ROOT) +
      ");from gbt_allinone import services as s;print(json.dumps(s.inspect(quiet=True),ensure_ascii=True,default=str))";
    execFile("py", ["-3.10", "-c", code], { timeout: 25000, windowsHide: true }, (err, stdout, stderr) => {
      if (err) return resolve(no("inspect 跑不动：" + String(err.message || err), { stderr: String(stderr || "").slice(0, 300) }));
      try { resolve(ok(JSON.parse(String(stdout).trim()))); }
      catch (e) { return resolve(no("inspect 输出不是 JSON")); }
    });
  });
}

function w3Ledger() {
  const audit = path.join(STORE, "audit.jsonl");
  const dir = path.join(STORE, "ledger");
  const out = { audit_tail: [], ledgers: {}, ledger_dir: dir };
  try {
    out.audit_tail = tailLines(audit, 16384, 8).map((ln) => {
      try { return JSON.parse(ln); } catch (e) { return { raw: ln.slice(0, 160) }; }
    });
  } catch (err) {
    return no("audit.jsonl tail 读不动：" + String(err.message || err));
  }
  if (!fs.existsSync(dir)) {
    out.note = "store/ledger/ 尚未成形 —— 四路账本要等一次真实往返（V2）才有行；按《反空壳律》如实记，不拿空文件顶替。";
    return ok(out);
  }
  fs.readdirSync(dir).filter((f) => f.endsWith(".jsonl")).forEach((f) => {
    try {
      out.ledgers[f] = tailLines(path.join(dir, f), 16384, 12).map((ln) => {
        try { return JSON.parse(ln); } catch (e) { return { raw: ln.slice(0, 160) }; }
      });
    } catch (err) {
      out.ledgers[f] = { error: String(err.message || err) };
    }
  });
  return ok(out);
}

function w3Health() {
  const dir = path.join(STORE, "health");
  if (!fs.existsSync(dir)) return ok({ records: [], byFault: {}, note: "store/health/ 还不存在" });
  const records = [];
  const byFault = {};
  fs.readdirSync(dir).filter((f) => f.endsWith(".jsonl")).forEach((f) => {
    try {
      const last = tailLines(path.join(dir, f), 8192, 1)[0];
      if (!last) return;
      const rec = JSON.parse(last);
      rec.source_file = f;
      records.push(rec);
      if (rec.fault_id) byFault[rec.fault_id] = rec;
    } catch (err) {
      records.push({ source_file: f, parse_error: String(err.message || err) });
    }
  });
  return ok({ records: records, byFault: byFault });
}

function w3Matrix() {
  const file = path.join(DOCS, "GBT全故障点设计.md");
  let text;
  try {
    text = fs.readFileSync(file, "utf8");
  } catch (err) {
    return no("母表读不动：" + String(err.message || err));
  }
  const lines = text.split(/\r?\n/);
  const rows = [];
  let inTable = false;
  lines.forEach((line) => {
    if (/^\|\s*故障点\s*\|/.test(line)) { inTable = true; return; }
    if (!inTable) return;
    if (!line.startsWith("|")) { if (rows.length) inTable = false; return; }
    if (/^\|[\s\-:|]+\|$/.test(line)) return;
    const cells = line.split("|").slice(1, -1).map((s) => s.trim().replace(/\*\*/g, ""));
    if (cells.length < 6) return;
    rows.push({
      label: cells[0], id: (cells[0].split(/\s+/)[0] || "").trim(),
      probe: cells[1], beat: cells[2], audit: cells[3], user: cells[4], why: cells[5] || "",
    });
  });
  if (!rows.length) return no("母表 §10.2 没解析出任何行");
  const payload = ok(rows);
  payload.rows = rows;
  payload.source = "gbt_allinone/docs/GBT全故障点设计.md §10.2（" + rows.length + " 点）";
  return payload;
}

function w3Mindmap() {
  const file = path.join(DOCS, "GBT全项目思维导图.md");
  let text;
  try { text = fs.readFileSync(file, "utf8"); } catch (err) { return no("思维导图源文件读不动：" + String(err.message || err)); }
  const fence = /```markdown\r?\n([\s\S]*?)```/.exec(text);
  if (!fence) return no("没找到 §一 的 markmap markdown 块");
  return ok(fence[1]);
}

function w3Selfcheck() {
  const checks = [];
  return w3State().then((st) => {
    checks.push({ name: "面板 /api/state", pass: st.ok === true, detail: st.ok ? "ok:true" : st.error });
    checks.push({ name: "store/tasks.json", pass: fs.existsSync(path.join(STORE, "tasks.json")), detail: "只读探测存在性" });
    checks.push({ name: "store/audit.jsonl", pass: fs.existsSync(path.join(STORE, "audit.jsonl")), detail: "只读探测存在性" });
    const h = w3Health();
    checks.push({ name: "store/health/ 记录数", pass: true, detail: String((h.data && h.data.records.length) || 0) + " 条" });
    checks.push({ name: "渲染进程写口", pass: true, detail: "0 个（preload 只暴露只读 IPC）" });
    return ok({ readonly: true, note: READONLY_NOTE, wrote_anything: false, checks: checks });
  });
}

function w3Introspect() {
  const h = w3Health();
  const t = w3Tasks();
  return Promise.resolve(ok({
    readonly: true,
    note: "全局自省 = 只读汇总；写盘要等后台探针服务独立进程上线",
    health_records: (h.data && h.data.records.length) || 0,
    tasks: t.ok ? t.data.total : "<" + (t.error || "取不到") + ">",
    collected_at: new Date().toISOString(),
  }));
}

/* ── 主进程侧 SSE 订阅 ── */

function startSse(broadcast) {
  let req = null;
  let retry = null;
  /* 🔴 2026-09-23 第 43 轮：**状态变化如实打出来**。
     为什么非打不可：这条链上有**三处静默出口**（非 200 / error / end），
     任何一处走到，屏上只有「未接」三个字，盘上什么都没有 ——
     于是"实时流没接上"这件事**没法从日志里查**，只能靠猜。
     与本仓既定的"灰态必须带原因"同一条规矩。 */
  function notify(st) {
    lastStreamState = st;
    console.log("[w3] 实时流状态: %s", st);
    broadcast("w3:stream", st);
  }
  function connect() {
    req = http.get(PANEL + "/api/events", (res) => {
      if (res.statusCode !== 200) {
        console.error("[w3] 实时流被拒：HTTP %s（目标 %s/api/events）", res.statusCode, PANEL);
        notify("closed");
        return schedule();
      }
      notify("open");
      let buf = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        buf += chunk;
        let idx = buf.indexOf("\n\n");
        while (idx >= 0) {
          const block = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          /* R-H295 · 修根因：原来这里是
           *     if (block.indexOf("data: ") === 0) { ... }
           * 而 panel_server._write_sse（panel_server.py:2856）每条事件都**先写 `id: N\n`
           * 再写 `data: …\n\n`** —— 于是**没有任何一个块是以 "data: " 开头的**，
           * 这个条件永远不成立 ⇒ 上帝视角的实时推送从来没送进渲染层一条事件；
           * 15 秒一次的心跳是注释行（`: heartbeat`），同样被丢掉，所以连"活着"都看不出来。
           * 副作用：新接的 callCapability 也拿不到 cap_result（它也喂自这里）。
           * 现在按 SSE 规范逐行解析：`data:` 可多行、`id:`/`event:`/注释各自独立；
           * 首个块还夹着 HTTP 响应头（`\r\n\r\n`），逐行解析天然忽略它们。 */
          const dataLines = [];
          const lines = block.split("\n");
          for (let li = 0; li < lines.length; li++) {
            const t = lines[li].replace(/\r$/, "");
            if (t.indexOf("data:") === 0) dataLines.push(t.slice(5).replace(/^ /, ""));
          }
          if (dataLines.length) {
            try {
              const ev = JSON.parse(dataLines.join("\n"));
              /* 先喂等待表（callCapability 的结果就在 cap_result 上回来），再广播 */
              settleCapPending(ev);
              broadcast("w3:event", ev);
            } catch (e) { /* 非 JSON 的心跳等忽略 */ }
          }
          idx = buf.indexOf("\n\n");
        }
      });
      res.on("end", () => { notify("closed"); schedule(); });
    });
    /* 🔴 2026-09-23 第 43 轮：这一行原来把**错误对象整个吞掉** ——
       `req.on("error", () => { notify("closed"); schedule(); })`。
       后果：实时流可以**永远**连不上（每 5 s 重试一次，一路静默），
       而盘上、屏上都不说为什么 —— 页脚只有「未接」三个字。
       这与 `broadcast` 那边早就定下的规矩（"坏因如实打到 stderr"）自相矛盾。
       现在如实打出来：错误码 + 目标地址，让人**一眼知道断在哪**。 */
    req.on("error", (err) => {
      const why = (err && (err.code || err.message)) || "未知";
      console.error("[w3] 实时流断开：%s（目标 %s/api/events）", why, PANEL);
      notify("closed");
      schedule();
    });
  }
  function schedule() {
    if (retry) return;
    retry = setTimeout(() => { retry = null; connect(); }, 5000);
  }
  connect();
  return () => { if (req) req.destroy(); if (retry) clearTimeout(retry); };
}

/* ── §12 工具出口（只读视图 · 刀 2b） ──
 *
 * 硬约束（O54 同族）：本口不得产生任何健康通道写入、不得落足迹 ——
 * 只做 fs 只读 + 展示映射；不 import 能力层、不起子进程、不落账。
 * 只读视图，任何状态判定以能力层为准，面板只做展示映射。
 * 灰态必须带原因（不得只灰不解释，否则又变成「有货架没货」）。
 *
 * 出口清单的真身在 gbt_allinone/coze_mail_cap.py 与 gbt_allinone/file_operation.py；
 * 能力接线后必须同批更新本表（PROJECT_BLUEPRINT §八「能力落地必须同批登记出口清单」）。
 */

const TOOLS_CAPS = [
  {
    cap: "prompt_bridge",
    registered: "caps_registry.py:593",
    actions: [
      { name: "status", state: "live", reason: "只读纯函数：先问当前态再决定发不发车（零副作用）" },
      { name: "compile", state: "live", reason: "只读纯本地：四段模板 + 原意保真自检（丢词即 intent_loss）" },
      { name: "passthrough", state: "live", reason: "只读：原样透传（不转化）" },
    ],
  },
  {
    cap: "voice_orchestra",
    actions: [
      { name: "list", state: "live", reason: "read-only: list skill atoms" },
      { name: "pipeline", state: "live", reason: "read-only: scene to pipeline" },
      { name: "status", state: "live", reason: "read-only: local backend availability" },
    ],
  },
  {
    cap: "coze_mail",
    registered: "caps_registry.py:498",
    actions: [
      { name: "status", state: "live", reason: "只读探针：读 state.json 与通道行数，不调能力层" },
      { name: "search", state: "pending", reason: "后端未接线 backend_not_wired（coze_mail_cap.py:69 _UnwiredTransport）" },
      { name: "read", state: "pending", reason: "后端未接线 backend_not_wired（同上）" },
      { name: "draft", state: "pending", reason: "" },
    ],
  },
  {
    cap: "create",
    registered: "caps_registry.py:504",
    actions: [
      { name: "status", state: "live", reason: "只读探针：读 state.json 与写根存在性，零字节零目录" },
      { name: "intent", state: "pending", reason: "本地登记（不发网络）；本轮不开放点击" },
      { name: "output", state: "pending", reason: "文本出口未接线 text_exit_not_wired：result=pending，不伪造成成功" },
    ],
  },
];

const TOOLS_NOT_EXPORTED = "敏感档动作不挂出口（物理上没有键）：coze_mail mark / send / reply / register · create configure / write";
const TOOLS_LINES_CAP_BYTES = 1048576;

/* R-H295：`registered` 原来是**硬编码行号**，实测已经漂了一个 ——
   voice_orchestra 声明 `caps_registry.py:560`，而 560 是 prompt_bridge 的行号，
   真实在 572（对着注册表逐个数出来的）。行号会随注册表增删漂移：本文件开头
   （main.cjs:1）自己就记着「本表行号按 caps_registry.py 实际行号刷新（因 sched_define
   后新增约 30 行而漂移；非静默改数）」—— 也就是靠人工重刷维持。
   指向**别人**的行号比不写更坏：读者会照着一个假引用去查，还查到东西。
   改成运行时现查真实行号；查不到就如实说查不到，不编、也不留旧值。 */
function registeredAt(cap) {
  try {
    if (!ROOT) return null;
    const p = path.join(ROOT, "gbt_allinone", "caps_registry.py");
    if (!fs.existsSync(p)) return null;
    const lines = fs.readFileSync(p, "utf8").split(/\r?\n/);
    const re = new RegExp('^\\s*"' + String(cap).replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + '":');
    for (let i = 0; i < lines.length; i++) {
      if (re.test(lines[i])) return "caps_registry.py:" + (i + 1);
    }
    return null;
  } catch (e) {
    return null;
  }
}

function readJsonIfPresent(file) {
  try {
    if (!file || !fs.existsSync(file)) return { present: false, data: null, error: null };
    return { present: true, data: JSON.parse(fs.readFileSync(file, "utf8")), error: null };
  } catch (err) {
    return { present: true, data: null, error: String((err && err.message) || err) };
  }
}

function channelLines(file) {
  try {
    if (!file || !fs.existsSync(file)) return 0;
    if (fs.statSync(file).size > TOOLS_LINES_CAP_BYTES) return null;
    return fs.readFileSync(file, "utf8").split(/\r?\n/).filter((s) => s.trim()).length;
  } catch (err) {
    return null;
  }
}

function draftReason(allowCount) {
  if (allowCount === null || allowCount === undefined) return "白名单读数不可用（未取到 allow_to）-> 按全拒口径处理";
  if (allowCount === 0) return "白名单为空（allow_to 0 条）-> 全拒（coze_mail_cap.py:416 _check_recipient）";
  return "白名单 " + allowCount + " 条；本轮仍不开放点击";
}

/* 只读视图，任何状态判定以能力层为准，面板只做展示映射。 */
async function w3Tools() {
  if (!STORE) return no("找不到仓库根（上层没有 gbt_allinone）-> 工具出口不猜路径");
  if (!fs.existsSync(STORE)) {
    return no("store 不存在：" + path.basename(STORE) + "（取不到就不显示绿 · 负对照口径）",
              { store: path.basename(STORE), store_present: false });
  }
  const mailState = readJsonIfPresent(path.join(STORE, "health", "coze_mail", "state.json"));
  const mailAllow = mailState.data && Array.isArray(mailState.data.allow_to)
    ? mailState.data.allow_to.length : null;
  const createState = readJsonIfPresent(path.join(STORE, "health", "create", "state.json"));
  const writeRoot = process.env.GBT_CREATE_ROOT || (ROOT ? path.join(ROOT, "outputs") : null);
  const facts = {
    coze_mail: {
      state_present: mailState.present,
      state_error: mailState.error,
      enabled: mailState.data ? mailState.data.enabled !== false : null,
      address_set: !!(mailState.data && mailState.data.address),
      allow_to_count: mailAllow,
      events_lines: channelLines(path.join(STORE, "health", "coze_mail", "events.jsonl")),
    },
    create: {
      state_present: createState.present,
      state_error: createState.error,
      text_exit_target: (createState.data && createState.data.text_exit_target) || "eigenflux",
      text_exit_source: (createState.data && createState.data.text_exit_source) || "default",
      write_root_label: writeRoot ? path.basename(writeRoot) : null,
      write_root_exists: !!(writeRoot && fs.existsSync(writeRoot)),
      events_lines: channelLines(path.join(STORE, "health", "create", "events.jsonl")),
    },
  };
  const caps = TOOLS_CAPS.map((c) => {
    const acts = c.actions.map((a) => {
      let reason = a.reason;
      if (c.cap === "coze_mail" && a.name === "draft") reason = draftReason(mailAllow);
      return { name: a.name, state: a.state, reason: reason };
    });
    // 现查真实行号；查不到就如实说，不回落到可能已漂的硬编码值
    const at = registeredAt(c.cap);
    return { cap: c.cap, registered: at || "未在 caps_registry.py 找到（不编行号）",
             declared: c.registered || null, actions: acts, facts: facts[c.cap] };
  });
  /* R-H295 · ⑤ 修「命名与覆盖面错位」。
   * 本页标题写的是「工具出口」，读的人自然以为它列出**全部**出口；实际 TOOLS_CAPS
   * 是一张**精选 4 项**的硬编码表（prompt_bridge / voice_orchestra / coze_mail / create），
   * 而注册表里有 141 个可用能力。落差 137 项**在面板上完全看不见**，
   * 脚注还只说「敏感档动作不挂出口（物理上没有键）」—— 暗示其余都挂了，那是假的。
   * 修法不是把 141 项全塞进这张表（那会把"展示映射"变成第二份能力表，
   * 违背本口「不复制任何一份能力表」的硬约束），而是**把落差本身如实显示出来**：
   * 全量口径取自正门 `/api/capabilities`（返回注册表 + 面板自身能力面），不自己数。
   */
  let coverage = { curated: TOOLS_CAPS.length, total: null, enabled: null,
                   disabled: null, app_routes: null, source: "/api/capabilities" };
  try {
    const disc = await httpGetJson(PANEL + "/api/capabilities", 4000);
    if (disc.ok && disc.data) {
      const dd = disc.data;
      coverage.total = dd.total === undefined ? null : dd.total;
      coverage.enabled = dd.enabled === undefined ? null : dd.enabled;
      coverage.disabled = dd.disabled === undefined ? null : dd.disabled;
      coverage.app_routes = (dd.app && Array.isArray(dd.app.routes)) ? dd.app.routes.length : null;
      coverage.note = ("本页是**精选展示**：" + coverage.curated + " / " +
                       (coverage.total === null ? "?" : coverage.total) +
                       "（可用 " + (coverage.enabled === null ? "?" : coverage.enabled) +
                       " · 禁用 " + (coverage.disabled === null ? "?" : coverage.disabled) +
                       "）。全量清单看能力总目录，不在这里复制第二份。");
    } else {
      coverage.note = "取不到全量口径（" + (disc.error || "未返回") + "）—— 落差数字如实留空，不估。";
    }
  } catch (err) {
    coverage.note = "取不到全量口径（" + String(err.message || err) + "）—— 落差数字如实留空，不估。";
  }

  return ok({
    readonly: true,
    store: path.basename(STORE),
    root: ROOT ? path.basename(ROOT) : null,
    note: "只读视图：不落账、不建目录、不写健康通道；面板只做展示映射。",
    caps: caps,
    coverage: coverage,
    not_exported_note: TOOLS_NOT_EXPORTED,
  });
}

/* ── 窗口 6 · 赏金台（阶段一：本机只读） ── */

const H1_BINARY_ENV = "GBT_H1_BINARY";
const H1_DRAFTS_ENV = "GBT_H1_DRAFTS";
const H1_BINARY_DEFAULT = process.env.LOCALAPPDATA
  ? path.join(process.env.LOCALAPPDATA, "gbt_allinone", "bin", "h1mcp.exe") : null;
const H1_DRAFTS_DEFAULT = process.env.APPDATA
  ? path.join(process.env.APPDATA, "h1mcp", "drafts") : null;

/* 配置项优先级：环境变量（测试钩子）> windows.json 的 entry.config > 内置默认。绝不查 PATH。 */
function h1ConfiguredPath(envName, configKey, fallback) {
  if (process.env[envName]) return process.env[envName];
  const entry = (registry.windows || []).filter((e) => e.id === "h1")[0];
  const raw = entry && entry.config ? entry.config[configKey] : null;
  if (typeof raw === "string" && raw.trim()) {
    return raw.trim().replace(/%([^%]+)%/g, (m, name) => (process.env[name] || m));
  }
  return fallback;
}
const H1_CRED_VARS = [
  { name: "H1_USERNAME", role: "HackerOne 用户名", read_by: "h1mcp v0.1.4" },
  { name: "H1_API_KEY", role: "API 令牌（二进制实际读取名）", read_by: "h1mcp v0.1.4" },
  { name: "H1_API_TOKEN", role: "历史口径名（h1mcp v0.1.4 不读取）", read_by: null },
];

function h1FileSha256(file) {
  try { return crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex"); }
  catch (err) { return null; }
}

/* 只读视图：不调 API、不起子进程、不写文件；取不到就不许显示绿。凭据只报布尔，不回显值（连用户名也不回显）。 */
function w3H1() {
  const h1Binary = h1ConfiguredPath(H1_BINARY_ENV, "binary_path", H1_BINARY_DEFAULT);
  const h1Drafts = h1ConfiguredPath(H1_DRAFTS_ENV, "drafts_path", H1_DRAFTS_DEFAULT);
  const binary = {
    path: h1Binary, present: false, bytes: null, tag: null,
    sha256: null, recorded_sha256: null, sha_match: null,
    sidecar_present: false, reason: null,
  };
  if (!h1Binary) {
    binary.reason = "LOCALAPPDATA 不可用 -> 拿不到稳定工具目录";
  } else if (!fs.existsSync(h1Binary)) {
    binary.reason = "二进制不存在（未安装或路径不符）";
  } else {
    try {
      binary.present = true;
      binary.bytes = fs.statSync(h1Binary).size;
      binary.sha256 = h1FileSha256(h1Binary);
      const sidecar = h1Binary + ".sha256";
      if (fs.existsSync(sidecar)) {
        binary.sidecar_present = true;
        const txt = fs.readFileSync(sidecar, "utf8");
        const hm = txt.match(/[0-9a-fA-F]{64}/);
        if (hm) binary.recorded_sha256 = hm[0].toLowerCase();
        const vm = txt.match(/tag=([^\r\n]+)/);
        if (vm) binary.tag = vm[1].trim();
      }
      binary.sha_match = (binary.sha256 && binary.recorded_sha256)
        ? binary.sha256 === binary.recorded_sha256 : null;
      if (binary.sha_match === false) binary.reason = "侧车哈希与产物不一致（产物被替换过）";
    } catch (err) {
      binary.reason = "读取失败：" + (err && err.code ? err.code : String(err));
    }
  }

  const credItems = H1_CRED_VARS.map((v) => ({
    name: v.name,
    role: v.role,
    read_by: v.read_by,
    configured: !!process.env[v.name],   /* 只报布尔，不回显值 */
  }));
  const credsReady = credItems.filter((c) => c.name === "H1_USERNAME" || c.name === "H1_API_KEY")
    .every((c) => c.configured);

  const drafts = { path: h1Drafts, initialized: false, count: null, files: [], reason: null };
  if (!h1Drafts) {
    drafts.reason = "APPDATA 不可用 -> 拿不到草稿目录";
  } else if (!fs.existsSync(h1Drafts)) {
    drafts.reason = "目录不存在（未初始化）";
  } else {
    try {
      const names = fs.readdirSync(h1Drafts).filter((n) => /\.json$/i.test(n)).sort().slice(0, 50);
      drafts.initialized = true;
      drafts.count = names.length;
      drafts.files = names.map((n) => {
        const row = { name: n, bytes: null, mtime: null, title: null, program_handle: null, parse_error: null };
        try {
          const p = path.join(h1Drafts, n);
          const st = fs.statSync(p);
          row.bytes = st.size;
          row.mtime = st.mtime.toISOString();
          const doc = JSON.parse(fs.readFileSync(p, "utf8"));
          if (typeof doc.title === "string") row.title = doc.title;
          if (typeof doc.program_handle === "string") row.program_handle = doc.program_handle;
        } catch (err) { row.parse_error = (err && err.name) || "READ_ERROR"; }
        return row;
      });
    } catch (err) {
      drafts.reason = "目录读取失败：" + (err && err.code ? err.code : String(err));
    }
  }

  const ready = binary.present === true && binary.sha_match === true && credsReady;
  const body = {
    readonly: true,
    stage: "stage1-local-readonly",
    note: "只读：不调 API、不起子进程、不写文件；凭据只报配置状态，不回显值。",
    badge: ready ? "ok" : (binary.present ? "warn" : "off"),
    binary: binary,
    credentials: { ready: credsReady, items: credItems },
    drafts: drafts,
    api_surfaces: [
      { id: "programs_scope", title: "程序与 scope", state: "pending", reason: "阶段二未接入（走 mcp_bridge 能力层，需 Owner 单独放行）" },
      { id: "reports", title: "我的报告", state: "pending", reason: "阶段二未接入（同上）" },
      { id: "earnings", title: "收益", state: "pending", reason: "阶段二未接入（同上）" },
    ],
    sensitive_note: "敏感档动作不接：submit_report / submit_draft / add_comment / close_report / update_report_severity / request_disclosure。",
  };
  if (!binary.present) return no("h1mcp 取不到：" + (binary.reason || "未知原因"), { panel: body });
  return ok(body);
}

/* ── §13 数字人召唤台 + AI 朋友圈（W9） ──
 *
 * 定性：本段新增**两个口**，只有一个是"动作口"：
 *   w3:pets / w3:eigenflux  —— 只读探测，零写盘、零网络、零子进程（除一次懒探测）。
 *   w3:summon               —— 唯一动作口：**只起一个本机窗口**；不写任何文件、
 *                              不发任何网络、不 kill 任何进程、不碰 store。
 * 面板上「可点」一律由**实测就绪态**决定：不就绪就不给点，并把原因写在按钮旁边（不假绿）。
 *
 * 决策全在 ./features.cjs（纯函数层，可被 node --test 钉住）；本段只做
 * fs 只读探测 / execFile 探针 / spawn 一次。绝对路径**不回显**给渲染层，只出 basename。
 */

const PETS_RESOURCES = ROOT ? path.join(ROOT, "potato_pet", "resources") : null;
const PETS_ELECTRON = ROOT
  ? path.join(ROOT, "holo_pet", "node_modules", "electron", "dist", "electron.exe") : null;
const PETS_PY_EXE = process.env.GBT_PY_EXE || "py";
const EF_SERVER = "eigenflux";

/* Python 腿就绪态：只查两个模块**在不在**，不 import（import PySide6 会拉起 Qt，太重）。
 * 结果缓存一次；点「刷新就绪态」才 force 重测 —— 不猜、也不每次点都起子进程。 */
let PETS_PY_PROBE = null;

function probePythonLeg(force) {
  if (PETS_PY_PROBE && force !== true) return Promise.resolve(PETS_PY_PROBE);
  const code = [
    "import json",
    "import importlib.util as u",
    "def has(n):",
    "    try: return u.find_spec(n) is not None",
    "    except Exception: return False",
    "print(json.dumps({'pyside6': has('PySide6'), 'live2d': has('live2d')}))",
  ].join("\n");
  return new Promise((resolve) => {
    execFile(PETS_PY_EXE, ["-3.10", "-c", code], { timeout: 20000, windowsHide: true },
      (err, stdout) => {
        const out = { checked: false, pyside6: false, live2d: false,
                      interpreter: PETS_PY_EXE + " -3.10" };
        if (!err) {
          try {
            const parsed = JSON.parse(String(stdout).trim());
            out.pyside6 = parsed.pyside6 === true;
            out.live2d = parsed.live2d === true;
            out.checked = true;
          } catch (e) { out.checked = false; }
        }
        PETS_PY_PROBE = out;
        resolve(out);
      });
  });
}

/* 面板是否在服务：拿到任何响应头即算在服务（不看状态码，只看"有没有人接电话"）。 */
function panelPing() {
  return new Promise((resolve) => {
    const req = http.get(PANEL + "/api/state", (res) => { res.resume(); resolve(true); });
    req.on("error", () => resolve(false));
    req.setTimeout(1500, () => { req.destroy(); resolve(false); });
  });
}

async function petsSnapshot(force) {
  const models = features.scanPetResources(fs, PETS_RESOURCES);
  const electronPresent = !!(PETS_ELECTRON && fs.existsSync(PETS_ELECTRON));
  let electronBytes = 0;
  if (electronPresent) {
    try { electronBytes = fs.statSync(PETS_ELECTRON).size; } catch (err) { electronBytes = 0; }
  }
  const python = await probePythonLeg(force);
  const panelReachable = await panelPing();
  const carriers = features.buildCarriers({
    python: python, electronPresent: electronPresent, panelReachable: panelReachable,
    electronBytes: electronBytes, models: models.length,
  });
  return { models: models, carriers: carriers, panelReachable: panelReachable, python: python };
}

/* 只读视图：不起窗口、不写文件、不发网络。绝对路径不回显。 */
async function w3Pets(payload) {
  if (!ROOT) return no("找不到仓库根（上层没有 gbt_allinone）-> 形象库不猜路径");
  const snap = await petsSnapshot(!!(payload && payload.refresh === true));
  const issues = [];
  if (!snap.python.checked) issues.push("py -3.10 探针没跑起来（解释器不可用？）—— Python 腿按未探测记，不猜");
  if (!PETS_RESOURCES || !fs.existsSync(PETS_RESOURCES)) issues.push("potato_pet/resources 不在位");
  return ok({
    readonly: true,
    stage: "w9",
    note: "只读探测：不起窗口、不写文件、不发网络；点「召唤数字人」才起一个本机窗口。",
    resources_label: PETS_RESOURCES ? path.basename(PETS_RESOURCES) : null,
    resources_present: !!(PETS_RESOURCES && fs.existsSync(PETS_RESOURCES)),
    models: snap.models,
    model_count: snap.models.length,
    carriers: snap.carriers.carriers,
    primary: snap.carriers.primary,
    python: snap.python,
    panel_reachable: snap.panelReachable,
    issues: issues,
  });
}

/* 唯一动作口：就绪才起，起完 unref（壳一退，数字人不跟着死）。 */
async function w3Summon(payload) {
  const carrier = payload && payload.carrier ? String(payload.carrier) : "";
  if (!ROOT) return no("找不到仓库根 -> 拒绝召唤", { carrier: carrier });
  const plan = features.summonPlan({
    carrier: carrier, repoRoot: ROOT, electronExe: PETS_ELECTRON, pythonExe: PETS_PY_EXE,
  });
  if (!plan.ok) return no("召唤被拒：" + plan.reason, { carrier: carrier });
  const snap = await petsSnapshot(false);
  const row = snap.carriers.carriers.filter((c) => c.id === carrier)[0];
  if (!row || row.ready !== true) {
    return no("载体未就绪，拒绝起进程：" + ((row && row.reason) || "没有这一条载体"),
              { carrier: carrier, ready: false });
  }
  if (!fs.existsSync(plan.exe)) {
    return no("可执行文件不在位：" + path.basename(plan.exe), { carrier: carrier });
  }
  try {
    const child = spawn(plan.exe, plan.argv, { detached: true, cwd: plan.cwd, stdio: "ignore" });
    child.unref();
    return ok({
      summoned: true, carrier: carrier, pid: child.pid, reason: plan.reason,
      cwd_label: path.basename(plan.cwd),
      argv_label: plan.argv.map((a) => path.basename(a)).join(" "),
      wrote_anything: false, killed_anything: false,
    });
  } catch (err) {
    return no("起不来：" + String((err && err.message) || err), { carrier: carrier });
  }
}

/* ── §13b AI 朋友圈（W9）· 本机只读 ──
 *
 * 为什么读盘在主进程：窗口 CSP 是 connect-src 'none'，渲染层**没有任何网络口**；
 * 数据在 ~/.eigenflux，只能由主进程 fs 读、归一化后经 IPC 交出去。
 * 远端来的文本一律先经 features.redact()；邮箱只出布尔，绝对路径不回显。
 */

function readJsonVia(file) {
  try { return { ok: true, doc: JSON.parse(fs.readFileSync(file, "utf8")) }; }
  catch (err) {
    return { ok: false, error: (err && err.code) ? String(err.code) : String((err && err.name) || err) };
  }
}

function listFilesDeep(dir, depth) {
  const out = [];
  if (!dir || depth > 3 || !fs.existsSync(dir)) return out;
  let names;
  try { names = fs.readdirSync(dir); } catch (err) { return out; }
  names.forEach((n) => {
    const p = path.join(dir, n);
    let st;
    try { st = fs.statSync(p); } catch (err) { return; }
    if (st.isDirectory()) { listFilesDeep(p, depth + 1).forEach((x) => out.push(x)); return; }
    out.push({ file: p, name: n, bytes: st.size, mtimeMs: st.mtimeMs });
  });
  return out;
}

function w3Eigenflux() {
  const home = features.resolveHome(process.env, os.homedir());
  const paths = features.eigenfluxPaths(home, EF_SERVER);
  const body = {
    readonly: true,
    stage: "w9",
    note: "只读：不调 API、不发网络、不写文件、不发消息；全部数据来自本机缓存。",
    home_label: features.homeLabel(home),
    initialized: false,
    issues: [],
    source: {},
    profile: null,
    friends: [],
    feed: [],
    messages: [],
    counts: { friends: 0, feed: 0, messages: 0 },
  };
  if (!fs.existsSync(paths.root)) {
    body.issues.push("未初始化：本机还没有 EigenFlux（" + body.home_label +
      " 下没有 servers/" + EF_SERVER + "）—— 是未初始化，不是空数据");
    return ok(body);
  }
  body.initialized = true;

  const pr = readJsonVia(paths.profile);
  if (pr.ok && pr.doc && !Array.isArray(pr.doc)) {
    body.profile = features.normalizeProfile(pr.doc);
    body.source.profile = path.basename(paths.profile);
  } else {
    body.issues.push("档案读不到：" + (pr.ok ? "profile.json 不是对象" : pr.error));
  }

  const cr = readJsonVia(paths.contacts);
  if (cr.ok && Array.isArray(cr.doc)) {
    body.friends = cr.doc.slice(0, features.LIMITS.friends).map(features.normalizeFriend);
    body.source.contacts = path.basename(paths.contacts);
  } else {
    body.issues.push("好友读不到：" + (cr.ok ? "contacts.json 不是数组" : cr.error));
  }

  const feedFiles = listFilesDeep(paths.broadcasts, 2).filter((f) => /\.json$/i.test(f.name));
  const latestFeed = features.pickLatest(feedFiles);
  if (!latestFeed) {
    body.issues.push("动态流读不到：broadcasts 下没有 JSON —— 本机还没收到过动态");
  } else {
    const fr = readJsonVia(latestFeed.file);
    if (!fr.ok) {
      body.issues.push("最新动态文件解析失败：" + fr.error);
    } else {
      const items = Array.isArray(fr.doc) ? fr.doc
        : (fr.doc && Array.isArray(fr.doc.items) ? fr.doc.items : []);
      body.feed = items.slice(0, features.LIMITS.feed_items).map(features.normalizeFeedItem);
      body.source.feed = {
        file: latestFeed.name, files_total: feedFiles.length,
        items_in_file: items.length, mtime: features.toIso(latestFeed.mtimeMs),
      };
    }
  }

  const msgFiles = listFilesDeep(paths.messages, 2).filter((f) => /\.json$/i.test(f.name));
  msgFiles.sort((a, b) => (Number(b.mtimeMs) || 0) - (Number(a.mtimeMs) || 0));
  const picked = msgFiles.slice(0, 4);
  if (!picked.length) {
    body.issues.push("私信读不到：messages 下没有 JSON —— 本机还没有会话");
  }
  const lists = [];
  picked.forEach((f) => {
    const mr = readJsonVia(f.file);
    if (!mr.ok) { body.issues.push("私信文件解析失败：" + f.name + "（" + mr.error + "）"); return; }
    const rows = Array.isArray(mr.doc) ? mr.doc
      : (mr.doc && Array.isArray(mr.doc.items) ? mr.doc.items : []);
    lists.push(rows);
  });
  body.messages = features.mergeMessages(lists, features.LIMITS);
  body.source.messages = { files_total: msgFiles.length, files_read: picked.length };
  body.counts = {
    friends: body.friends.length, feed: body.feed.length, messages: body.messages.length,
  };
  return ok(body);
}
/* ── 窗口 ── */

const registry = readRegistry();
const wins = new Map();
let tray = null;
/* 实时流的**当前状态**（2026-09-23 第 43 轮加）。
   为什么要记：`startSse` 跑在建窗之前（R-H295 的"数据面先立"），那条 `notify("open")`
   发生时还没有窗口 ⇒ 状态只报一次就丢。记下来，建窗完成后**补发**给迟到的订阅者。
   null = 还没连过（此时不该补发任何状态 —— 补发 null 等于替面板编一个状态）。 */
let lastStreamState = null;

function broadcast(channel, payload) {
  /* R-H295：原实现没有任何错误隔离 —— 某个窗口的 webContents 处于异常态时
     （`isDestroyed` 本身可能抛、`send` 也可能抛），异常会从 SSE 的 data 回调里冒出来，
     而那条路径上没人接：**实时流会整条断掉甚至带走主进程**，
     症状和"实时流未接"一样，但原因完全不同。
     逐窗口隔离：坏的那扇跳过，其余照推；坏因如实打到 stderr。 */
  wins.forEach((w, id) => {
    try {
      if (w && !w.isDestroyed() && w.webContents && !w.webContents.isDestroyed()) {
        w.webContents.send(channel, payload);
      }
    } catch (err) {
      console.error("[w3] 推送失败（跳过该窗，其余照推） id=" + id + " ch=" + channel + ":", err);
    }
  });
}

function saveWindowState() {
  const data = layout.loadLayout(LAYOUT_FILE);
  wins.forEach((w, id) => {
    if (!w || w.isDestroyed()) return;
    data.windows[id] = layout.fromBrowserBounds(w.getBounds(), id, w.isVisible());
  });
  try { layout.saveLayout(LAYOUT_FILE, data); } catch (err) { /* 写不进布局文件不该拖垮壳 */ }
}

/* ── 2026-09-23 加：窗可以加载**回环 HTTP**（一体式要塞对话面）────────────────
   规则与测试见 `shell/url-policy.cjs` —— 它**不依赖 electron**，所以能在普通 node 下单测
   （`tests/test_url_policy.cjs`）。这里只是把它接上；**策略本身不在这份文件里**。

   ⚠️ 对话面（DSH）的**真实约束**（2026-09-23 实测）：
     `GET http://127.0.0.1:3080/` → **HTTP 401**
     body 原文：`dsh web authentication required; reopen the URL printed by dsh web.`
   ⇒ 它要的是 **`dsh web` 启动时打印的那条带 token 的 URL**，不是裸 URL。
     **本文件不保存、不读、不猜那个 token**（凭据不许明文落盘）。
     带 token 的 URL 只能由**主人在运行时**提供 —— 见 windows.json 里 `dsh-chat` 的 `needs_url`。 */
const urlPolicy = require("./url-policy.cjs");
const loopbackUrlOnly = urlPolicy.loopbackUrlOnly;

function createWindow(entry) {
  const stored = layout.loadLayout(LAYOUT_FILE).windows[entry.id];
  const displays = screen.getAllDisplays();
  const wanted = stored || entry.default;
  const placed = layout.clampBounds(layout.normalize(wanted, entry.id), displays);
  /* 🔴 **真启动预演的插桩**（2026-09-23 第 37 轮）：`GBT_W3_STARTUP_PROBE=1` 时
     所有窗**屏幕外 + 不显示**，但引导链**一个环节都不跳**（单例锁 → registerIpc →
     startSse → createWindow → buildTray → refreshTrayMenu）。
     为什么插在这里而不是另写一条探针链：另写一条就**不是真启动**了 ——
     托盘图标构造失败会让 startSse 永远不跑（本文件上面记着这条实测），
     那种缺陷只有走真链才抓得到。**只改两个字段，不设这个变量时行为一个字节不动。** */
  const PROBE = process.env.GBT_W3_STARTUP_PROBE === "1";
  const win = new BrowserWindow({
    x: PROBE ? -20000 : placed.x, y: PROBE ? -20000 : placed.y,
    width: placed.w, height: placed.h,
    minWidth: 720, minHeight: 480,
    transparent: entry.transparent !== false,
    frame: entry.frame === true,
    resizable: entry.resizable !== false,
    alwaysOnTop: entry.alwaysOnTop !== false,
    hasShadow: false,
    backgroundColor: "#00000000",
    show: placed.visible !== false,   /* 可见性来自注册表 / 持久化布局（W7）——声明了就要生效 */
    title: entry.title || entry.id,
    webPreferences: {
      preload: path.join(HERE, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });
  if (entry.alwaysOnTop !== false) win.setAlwaysOnTop(true, "screen-saver");

  /* 一体式 App 铬（2026-09-23 第 32 轮）：**壳这一层注入**，不改那 8 个页面一行。
     `chrome.attach` 内部自己排除 `dsh-chat`（DSH 的窗，内容不是我们的）。 */
  try { chrome.attach(win, entry, registry); } catch (err) { console.error("[w3] 铬挂载失败:", err); }

  /* 加载什么 —— 决策在 url-policy.windowSource（**单一决策点**，可单测）。
     四种结果：url / blocked（不合法→拒绝页，理由写清）/ connect（要主人运行时给 URL）/ file。 */
  const src = urlPolicy.windowSource(entry);
  if (src.kind === "url") {
    win.loadURL(src.url);
  } else if (src.kind === "connect") {
    win.loadFile(path.join(HERE, "connect.html"),
                 { query: { id: String(src.id || entry.id), port: String(src.port || 0) } });
  } else if (src.kind === "file") {
    win.loadFile(path.join(HERE, src.file));
  } else {
    console.error("[gbt-shell] 拒绝加载（%s）：%s", entry.id, src.why);
    win.loadFile(path.join(HERE, "blocked.html"),
                 { query: { why: src.why, id: String(entry.id) } });
  }
  /* 🔴 **2026-09-23 第 43 轮修的「迟到订阅者」缺陷**（一条只有真跑才照得到的死角）。

     症状：页脚**永远**显示「实时流：未接」，而面板端其实在推、连接也真的建起来了 ——
     录下来的页面 innerText 就是「实时流：未接」，可与此同时账本还在出数（走 5 s 轮询兜底）。

     查证（三步都是实测，不是推断）：
       ① 面板端有这条路由：`panel_server.py:3445` → `GET /api/events`；
          Python 直连拿到 `HTTP 200 · text/event-stream` + 真事件字节；
          Node 照本壳的写法直连 **13 ms** 拿到 `status 200` ⇒ **不是网络、不是面板**。
       ② `preload.cjs:47-48` 两个口（`onEvent` / `onStreamState`）都在 ⇒ 不是桥没接。
       ③ `window.js:1056-1060` 订阅也在，徽章默认文案就是 HTML 里写死的「实时流：未接」
          ⇒ **只要那条 `w3:stream` 消息没到，页脚就永远停在默认值**。

     真因（**是 R-H295 那次修法的副作用**）：
       R-H295 把 `startSse` 提到 `createWindow` **之前**（数据面先立 —— 这个方向是对的，
       它治的是"托盘坏掉会弄死实时流"）。但 `broadcast()` 是**遍历 `wins`** 推送的，
       于是 `notify("open")` 发生的那一刻 `wins` **还空着**，那条状态**没有任何窗口听得到**。
       ⇒ 生产者被挪到了消费者前面，"状态只报一次"的毛病就露出来了。

     修法（**不许把 startSse 挪回去**，那会退回老病）：补**状态回放** ——
     窗口加载完成后，把当前状态单独补发给它。迟到的订阅者也能拿到现状，这是 pub/sub 的本分。 */
  win.webContents.on("did-finish-load", () => {
    if (!lastStreamState) return;
    try {
      win.webContents.send("w3:stream", lastStreamState);
    } catch (err) {
      console.error("[w3] 补发实时流状态失败 id=" + entry.id + ":", err);
    }
  });
  /* 🔴 **2026-09-23 第 37 轮修的真缺陷：`moved` 在 Windows 上永远不触发。**
     Electron 文档对 `BrowserWindow` 的 `moved` 事件原文写着 **"macOS only"** ——
     而本壳跑在 Windows 11 上 ⇒ 下面这段（吸附对齐 + 挪窗后落盘）**在本机从来没跑过**。

     怎么发现的：新加的「真启动预演」（`shell/startup.cjs`）里有一条
     「主动挪一下窗，看布局文件会不会被重写」——**判红**。查下去才是这个原因。
     为什么以前的门全都放绿：预检**刻意不启动**、复演只验载入、取证只拍图 ——
     **没有一格会去动一下窗**。这是一条只有"真启动 + 真动手"才照得到的死角。

     修法：抽出 `onMoved()`，`moved`（macOS）与 `move`（全平台）都接上；
     `move` 在拖动期间会**连续**触发，所以做防抖 —— 每次拖动都跑一遍吸附 + 写盘会白烧磁盘。 */
  function onMoved() {
    const others = [];
    wins.forEach((o, oid) => { if (oid !== entry.id && o && !o.isDestroyed()) others.push(layout.fromBrowserBounds(o.getBounds(), oid)); });
    const snapped = layout.snapBounds(layout.fromBrowserBounds(win.getBounds(), entry.id), screen.getAllDisplays(), others, layout.SNAP_PX);
    const next = layout.toBrowserBounds(snapped);
    const cur = win.getBounds();
    if (next.x !== cur.x || next.y !== cur.y) win.setBounds(next);
    saveWindowState();
  }
  let moveTimer = null;
  win.on("moved", onMoved);                       // macOS
  win.on("move", () => {                          // Windows / Linux（全平台）
    if (moveTimer) clearTimeout(moveTimer);
    moveTimer = setTimeout(() => { moveTimer = null; onMoved(); }, 220);
  });
  win.on("resized", saveWindowState);
  win.on("close", saveWindowState);
  win.on("closed", () => { if (moveTimer) clearTimeout(moveTimer); wins.delete(entry.id); });
  wins.set(entry.id, win);
  return win;
}

/* ── W9 · 窗 A：把对话面接上（**主人在运行时给 URL**）─────────────────────────
   背景：对话面裸 URL 回 401，要 `dsh web` 打印的**带 token 的 URL**。
   纪律（三条，写在这儿免得以后有人"顺手优化"掉）：
     ① **不落盘**：URL 只在内存里交给 `loadURL`，不写任何配置文件、不进布局文件；
     ② **不回显**：返回值只给 `host`（`127.0.0.1:3080`），**绝不把整条 URL 回给渲染进程**
        —— 它带 token，一回显就会进界面/日志；
     ③ **不白名单外**：仍然过 `loopbackUrlOnly()`，只放行本机回环。 */
function w3ConnectDsh(payload) {
  const raw = String((payload && payload.url) || "").trim();
  if (!raw) return { ok: false, error: "没有给 URL" };
  const chk = loopbackUrlOnly(raw);
  if (!chk.ok) return { ok: false, error: chk.why, rule: "只放行本机回环（127.0.0.1 / localhost / ::1）" };
  const win = wins.get("dsh-chat");
  if (!win || win.isDestroyed()) return { ok: false, error: "对话面的窗不在（先从托盘菜单把它开起来）" };
  let host = "";
  try { host = new URL(chk.url).host; } catch (err) { host = "(无法解析)"; }
  win.loadURL(chk.url);
  /* 落一张**不含 token** 的回执：这是"真接上过一次"的机器证据（守卫 B1e 读它）。
     回执里只有 host 与时间 —— **绝不写 URL、绝不写 token**。 */
  try {
    const dir = path.join(ROOT, "state");
    fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(path.join(dir, "desktop-dsh-connect-receipt.json"),
      JSON.stringify({ host: host, at: new Date().toISOString(),
                       note: "由桌面壳 w3ConnectDsh 落盘：只记 host 与时间，不含 URL/token" }, null, 1),
      "utf8");
  } catch (err) {
    /* 回执写不了不影响接上；但也不静默 —— 记一行给排查 */
    console.error("[gbt-shell] 回执写不了：%s", String(err).slice(0, 120));
  }
  return { ok: true, host: host, note: "已交给对话框加载；URL 只在内存，未落盘、未回显" };
}

function buildTray() {
  tray = new Tray(trayIcon(16, [0xf5, 0xb0, 0x41], [0x00, 0xe5, 0xff]));
  tray.setToolTip("GBT小土豆V8 · 上帝视角（W3）");
  tray.on("click", () => { wins.forEach((w) => { if (!w.isDestroyed()) w.isVisible() ? w.hide() : w.show(); }); });
  return tray;
}

function refreshTrayMenu() {
  if (!tray) return;
  const items = registry.windows.map((entry) => ({
    label: (wins.has(entry.id) && !wins.get(entry.id).isDestroyed() && wins.get(entry.id).isVisible() ? "隐藏 " : "显示 ") + (entry.title || entry.id),
    click: () => {
      const w = wins.get(entry.id);
      if (!w || w.isDestroyed()) createWindow(entry);
      else if (w.isVisible()) w.hide();
      else { w.show(); w.focus(); }
      refreshTrayMenu();
    },
  }));
  items.push({ type: "separator" });
  items.push({ label: "重载当前窗口", click: () => wins.forEach((w) => { if (!w.isDestroyed()) w.reload(); }) });
  items.push({
    label: "重置布局",
    click: () => {
      const empty = layout.emptyLayout();
      try { layout.saveLayout(LAYOUT_FILE, empty); } catch (err) { /* 忽略 */ }
      wins.forEach((w, id) => {
        const entry = registry.windows.filter((e) => e.id === id)[0];
        if (!entry || w.isDestroyed()) return;
        const b = layout.clampBounds(layout.normalize(entry.default, id), screen.getAllDisplays());
        w.setBounds(layout.toBrowserBounds(b));
      });
    },
  });
  items.push({ label: "退出", click: () => { app.isQuitting = true; app.quit(); } });
  tray.setContextMenu(Menu.buildFromTemplate(items));
}

function registerIpc() {
  ipcMain.handle("w3:config", () => ok({ engine: process.env.GBT_TREE_ENGINE || "auto", readonly: true, root: ROOT ? path.basename(ROOT) : null }));
  /* 实时流的**现状**（只读拉取，2026-09-23 第 45 轮加）。
     为什么要能"拉"：`w3:stream` 是**推**，只在状态**变化**时发一次；
     而窗口是**后来才建**的（`startSse` 跑在建窗之前 —— R-H295 的"数据面先立"）。
     上一轮用"建窗后补发"治了主进程建的那条路，但**别的东西建的窗**（取证器 shots 自己建窗）
     照样收不到 ⇒ 屏上又是一句「实时流：未接」，而主进程其实连着。
     ⇒ 补一个**只读拉取**：谁建的窗都能问一句"现在什么状态"。推 + 拉都在，才不挑宿主。 */
  ipcMain.handle("w3:stream-state", () => ok({ state: lastStreamState }));
  ipcMain.handle("w3:state", () => w3State());
  ipcMain.handle("w3:tasks", () => w3Tasks());
  ipcMain.handle("w3:env", () => w3Env());
  ipcMain.handle("w3:ledger", () => w3Ledger());
  ipcMain.handle("w3:health", () => w3Health());
  ipcMain.handle("w3:matrix", () => w3Matrix());
  ipcMain.handle("w3:mindmap", () => w3Mindmap());
  ipcMain.handle("w3:selfcheck", () => w3Selfcheck());
  ipcMain.handle("w3:introspect", () => w3Introspect());
  ipcMain.handle("w3:tools", () => w3Tools());
  ipcMain.handle("w3:h1", () => w3H1());
  ipcMain.handle("w3:pets", (ev, payload) => w3Pets(payload));
  ipcMain.handle("w3:summon", (ev, payload) => w3Summon(payload));
  ipcMain.handle("w3:eigenflux", () => w3Eigenflux());
  /* R-H295 新接：框架自己的两只只读审计器（欠账「覆盖审计 / 零调用点清单接进上帝视角」）*/
  ipcMain.handle("w3:coverage", () => w3Coverage());
  ipcMain.handle("w3:orphans", () => w3Orphans());
  ipcMain.handle("w3:gene", () => w3Gene());
  /* W9 · 窗 A 的动作口：把主人粘进来的 URL 交给对话框。
     它**不是数据写口**（不写文件、不写配置），但**是动作口** ——
     preload 里 `non_readonly_capability` 那一行必须同步登记它，不许悄悄放宽。 */
  ipcMain.handle("w3:connect-dsh", (ev, payload) => w3ConnectDsh(payload));
  /* W13 · 一体式 App 铬的跨窗跳转口（2026-09-23 第 32 轮加）。
     它**不是数据写口**，但是**动作口**（会改窗口可见性/焦点）⇒：
       · 只认注册表里**已有的 id**（白名单，不认任意字符串）；
       · 不写文件、不出网、不 kill 任何东西；
       · `preload.cjs` 的 `non_readonly_capability` 那一行**同步登记**它，不许悄悄放宽。 */
  ipcMain.handle("w3:show-window", (ev, payload) => {
    /* 判据在 `chrome.showWindow`（纯函数、可单测）—— 这里只做 `ok()/no()` 的适配。 */
    const r = chrome.showWindow(registry, wins, payload);
    return r.ok ? ok(r.data) : no(r.error);
  });

  /* ══ W3 · 语音对讲（2026-09-23 第 58 轮）══════════════════════════════════
     主人令：「我打开页面就自动监听，关闭她也跟着关闭，但是大脑后台是在运行的。」
     ⇒ 四条硬纪律（写死，别改）：
       ① **不设开关**：页面打开就起，页面关闭就停。本进程**不做常驻守护** ——
          "大脑后台照常运行"是 DSH 的事，不归这一段。
       ② **绑 webContents**：`sender.once('destroyed', …)` 才是"关页面就停"的**可靠实现**。
          页面被强杀时它自己的 `pagehide` 发不出去；只靠那一句，麦克风就留在那儿开着。
       ③ **一切走唯一门**：这里只拉起 `tools/codex-scripts/intercom.py`，
          它内部调 `five-dim.py cap voice`（= `api.run_task`）。
          **主进程不直接碰 voice_cap、不碰麦克风、不读凭据、不写任何数据。**
       ④ `preload.cjs` 的 `non_readonly_capability` 那一行**同步登记**本口（它开麦克风+出声），
          不许悄悄放宽。
     ⚠️ 现读实况（2026-09-23）：本机**没有可用录音设备**（唯一输入端点是 iPhone 蓝牙免提，
        未连接）⇒ 监听会如实回 `no_input` 并退避；**这不是坏，是没设备**，页面按黄色显示。
     */
  const intercomSessions = new Map();   // webContents.id → {child, startedAt, rounds, heard, last}
  const INTERCOM_JS = path.join(ROOT, "tools", "codex-scripts", "intercom.py");

  function intercomStop(id) {
    const s = intercomSessions.get(id);
    if (!s) return false;
    try { if (s.child && !s.child.killed) s.child.kill(); } catch (e) { /* 可能已退，如实忽略 */ }
    intercomSessions.delete(id);
    return true;
  }

  /* 三条腿的状态**只问一次、缓存在主进程**（第 58 轮补）。
     为什么必须缓存：走一次门要起 Python + 加载框架 + 连发两次 `cap voice`，
     实测要好几秒；而取证/开窗在那一秒就发生了 ⇒ 页面会显示"未取到"，
     那是**时序**不是"坏"。缓存后：**注册时就先预热**，等窗口起来时读数已经在了。 */
  let intercomStatusCache = null;
  function intercomStatus(force) {
    if (intercomStatusCache && !force) return Promise.resolve(intercomStatusCache);
    return intercomRun(["status"], 120000).then((r) => {
      intercomStatusCache = (r && r.ok && r.data) ? r.data : null;
      return intercomStatusCache;
    }, () => null);
  }

  function intercomStart(wc) {
    const id = wc.id;
    if (intercomSessions.has(id)) return intercomSessions.get(id);
    const child = spawn(PETS_PY_EXE,
      ["-3.10", INTERCOM_JS, "watch", "--jsonl", "--seconds", "4", "--culture", "zh-CN"],
      { cwd: ROOT, windowsHide: true, stdio: ["ignore", "pipe", "pipe"] });
    const sess = { child: child, startedAt: Date.now(), rounds: 0, heard: 0, last: null,
                   status: null };
    intercomSessions.set(id, sess);
    /* 三条腿：优先吃**预热好的缓存**（`intercomStatus()` 在注册时就已发起）。 */
    intercomStatus().then((s) => { sess.status = s; }, () => { sess.status = null; });
    let buf = "";
    child.stdout.on("data", (d) => {
      buf += d.toString("utf8");
      let i;
      while ((i = buf.indexOf("\n")) >= 0) {
        const line = buf.slice(0, i).trim();
        buf = buf.slice(i + 1);
        if (line.charAt(0) !== "{") continue;          // 非 JSON 行（进度/告警）不转给页面
        try {
          const rec = JSON.parse(line);
          sess.rounds = rec.rounds_total || sess.rounds + 1;
          sess.heard = rec.heard_total || sess.heard;
          sess.last = rec;
          if (!wc.isDestroyed()) wc.send("w3:intercom-event", rec);
        } catch (e) { /* 半行/坏行丢掉 —— 不编一条假读数 */ }
      }
    });
    child.on("exit", (code) => {
      const s = intercomSessions.get(id);
      if (s && s.child === child) intercomSessions.delete(id);
      if (!wc.isDestroyed()) wc.send("w3:intercom-event", { status: "stopped", exit: code });
    });
    /* 🔴 这一句就是「关掉页面她也跟着关」的可靠实现。 */
    wc.once("destroyed", () => { intercomStop(id); });
    return sess;
  }

  /* 一次性调用（status / say）：同一件脚本、同一道门。 */
  function intercomRun(args, timeoutMs) {
    return new Promise((resolve) => {
      execFile(PETS_PY_EXE, ["-3.10", INTERCOM_JS].concat(args),
        { cwd: ROOT, timeout: timeoutMs || 120000, windowsHide: true, maxBuffer: 1 << 20 },
        (err, stdout, stderr) => {
          const txt = String(stdout || "");
          const i = txt.indexOf("{");
          if (i < 0) {
            resolve(no("对讲件没吐 JSON：" + String(stderr || err || "").slice(0, 160)));
            return;
          }
          try { resolve(ok(JSON.parse(txt.slice(i)))); }
          catch (e) { resolve(no("JSON 解析失败：" + String(e).slice(0, 120))); }
        });
    });
  }

  ipcMain.handle("w3:intercom", (ev, payload) => {
    const op = (payload && payload.op) || "state";
    const args = (payload && payload.args) || {};
    const wc = ev.sender;
    if (op === "status") return intercomStatus(true).then((s) => ok(s || { ok: false }));
    if (op === "start") {
      const s = intercomStart(wc);
      return ok({ listening: true, rounds: s.rounds, heard: s.heard, last: s.last,
                  status: s.status || null });
    }
    if (op === "stop") { intercomStop(wc.id); return ok({ listening: false }); }
    if (op === "state") {
      const s = intercomSessions.get(wc.id);
      return ok({ listening: !!s, rounds: s ? s.rounds : 0, heard: s ? s.heard : 0,
                  last: s ? s.last : null, status: (s && s.status) || null });
    }
    if (op === "say") {
      if (!args.text) return no("缺少 text");
      return intercomRun(["say", String(args.text)], 180000);
    }
    return no("未知 op：" + op);
  });
  /* **预热**：注册完就先把三条腿问一次（不阻塞、失败也不报错），
     等第一扇窗起来时缓存里已经有读数了 —— 这正是"页面显示未取到"那个时序坑的解。 */
  intercomStatus();
}

/* 🔴 **只接线模式**（2026-09-23 第 31 轮加，为真壳取证器 `shots.cjs` 而开）：
 * `GBT_W3_WIRE_ONLY=1` 时**只建立只读数据面（IPC）**，不开窗、不进托盘、不抢单例锁。
 *
 * 为什么要它：`shots.cjs` 要拍的是**"真实数据面下的窗长什么样"**。
 * 而唯一可靠的做法是复用**同一份** `registerIpc` —— 在取证器里重写一遍接线，
 * 两份必然漂（那时拍的就不是真壳，是"我以为的壳"）。
 * 只加一个分支，**不设这个变量时走的还是原来那条路，既有行为一个字节不动**。
 */
const WIRE_ONLY = process.env.GBT_W3_WIRE_ONLY === "1";
if (WIRE_ONLY) {
  /* `app &&`：让**无 Electron 的 node 进程**也能 require 本件只为拿那几个只读数据函数
     （形状探针用）。没有这一层，`app.whenReady()` 会当场抛，导出的函数就用不上了。 */
  if (app) {
    app.whenReady().then(() => {
      registerIpc();
      try { startSse(broadcast); } catch (err) { console.error("[w3] 只接线模式 SSE 未起:", err); }
    });
  }
} else if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    wins.forEach((w, id) => {
      if (w.isDestroyed()) return;
      const entry = registry.windows.filter((e) => e.id === id)[0];
      if (entry && entry.default && entry.default.visible === false) return;   /* 默认不开的窗：第二个实例不唤它（W7） */
      if (w.isMinimized()) w.restore();
      w.show();
      w.focus();
    });
  });
  app.whenReady().then(() => {
    /* R-H295 · 数据面先立，展示面后立，且展示面不许拖垮数据面。
     * 病根：这里原来是一条不断的链
     *     registerIpc → createWindow → buildTray → refreshTrayMenu → startSse
     * 任一环抛错就整条进 .catch（记「启动失败」后 app.quit()）—— 于是
     * **托盘图标/菜单一旦出问题，实时推送 startSse 就永远不执行，而且没有任何提示**：
     * 页脚只是安静地显示「实时流：未接」，能力调用则表现为"超时"。
     * 实测（无头桩里 refreshTrayMenu 抛 `isVisible is not a function`）就复现了这条路径。
     * 现在：只读数据面（IPC + SSE 订阅）先无条件建立；窗口/托盘各自 try/catch，
     * 坏了就在盘上如实说坏了，不牵连数据面。 */
    registerIpc();
    startSse(broadcast);

    try {
      registry.windows.forEach((entry) => createWindow(entry));
    } catch (err) {
      console.error("[w3] 建窗失败（数据面不受影响）:", err);
    }
    try {
      buildTray();
      refreshTrayMenu();
    } catch (err) {
      console.error("[w3] 托盘失败（数据面不受影响，实时流照常）:", err);
    }
    try {
      screen.on("display-metrics-changed", () => {
        wins.forEach((w, id) => {
          if (w.isDestroyed()) return;
          w.setBounds(layout.toBrowserBounds(layout.clampBounds(w.getBounds(), screen.getAllDisplays())));
        });
        saveWindowState();
      });
    } catch (err) {
      console.error("[w3] 显示器事件挂载失败:", err);
    }
    if (process.env.GBT_W3_DEBUG) {
      console.log("[w3] root=" + ROOT + " windows=" + registry.windows.map((e) => e.id).join(","));
    }
  }).catch((err) => {
    console.error("[w3] 启动失败:", err);
    app.quit();
  });
  app.on("window-all-closed", () => {
    const hasMain = registry.windows.some((e) => e.role === "main");
    if (hasMain) app.quit();
    /* W3 只登记子窗口：全关 ≠ 退出，退到托盘常驻（§2.2） */
  });
}

/* 只读数据面整体导出 —— 让探针能脱离 Electron 直接验它们（见 .scratch/_w3_ipc_harness.cjs）。 */
module.exports = {
  findRepoRoot,
  tailLines,
  trayIcon,
  w3State,
  w3Tasks,
  w3Env,
  w3Ledger,
  w3Health,
  w3Matrix,
  w3Mindmap,
  w3Selfcheck,
  w3Introspect,
  w3Tools,
  w3H1,
  w3Pets,
  w3Summon,
  w3Eigenflux,
  /* R-H295 新接的两只只读审计器（脱离 Electron 也能探）*/
  w3Coverage,
  w3Orphans,
  w3Gene,
  callCapability,
};
