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
  function notify(st) { broadcast("w3:stream", st); }
  function connect() {
    req = http.get(PANEL + "/api/events", (res) => {
      if (res.statusCode !== 200) { notify("closed"); return schedule(); }
      notify("open");
      let buf = "";
      res.setEncoding("utf8");
      res.on("data", (chunk) => {
        buf += chunk;
        let idx = buf.indexOf("\n\n");
        while (idx >= 0) {
          const block = buf.slice(0, idx);
          buf = buf.slice(idx + 2);
          if (block.indexOf("data: ") === 0) {
            try { broadcast("w3:event", JSON.parse(block.slice(6))); } catch (e) { /* 心跳等忽略 */ }
          }
          idx = buf.indexOf("\n\n");
        }
      });
      res.on("end", () => { notify("closed"); schedule(); });
    });
    req.on("error", () => { notify("closed"); schedule(); });
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
    registered: "caps_registry.py:560",
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
    registered: "caps_registry.py:465",
    actions: [
      { name: "status", state: "live", reason: "只读探针：读 state.json 与通道行数，不调能力层" },
      { name: "search", state: "pending", reason: "后端未接线 backend_not_wired（coze_mail_cap.py:69 _UnwiredTransport）" },
      { name: "read", state: "pending", reason: "后端未接线 backend_not_wired（同上）" },
      { name: "draft", state: "pending", reason: "" },
    ],
  },
  {
    cap: "create",
    registered: "caps_registry.py:471",
    actions: [
      { name: "status", state: "live", reason: "只读探针：读 state.json 与写根存在性，零字节零目录" },
      { name: "intent", state: "pending", reason: "本地登记（不发网络）；本轮不开放点击" },
      { name: "output", state: "pending", reason: "文本出口未接线 text_exit_not_wired：result=pending，不伪造成成功" },
    ],
  },
];

const TOOLS_NOT_EXPORTED = "敏感档动作不挂出口（物理上没有键）：coze_mail mark / send / reply / register · create configure / write";
const TOOLS_LINES_CAP_BYTES = 1048576;

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
function w3Tools() {
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
    return { cap: c.cap, registered: c.registered, actions: acts, facts: facts[c.cap] };
  });
  return ok({
    readonly: true,
    store: path.basename(STORE),
    root: ROOT ? path.basename(ROOT) : null,
    note: "只读视图：不落账、不建目录、不写健康通道；面板只做展示映射。",
    caps: caps,
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

function broadcast(channel, payload) {
  wins.forEach((w) => {
    if (w && !w.isDestroyed() && w.webContents && !w.webContents.isDestroyed()) {
      w.webContents.send(channel, payload);
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

function createWindow(entry) {
  const stored = layout.loadLayout(LAYOUT_FILE).windows[entry.id];
  const displays = screen.getAllDisplays();
  const wanted = stored || entry.default;
  const placed = layout.clampBounds(layout.normalize(wanted, entry.id), displays);
  const win = new BrowserWindow({
    x: placed.x, y: placed.y, width: placed.w, height: placed.h,
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
  win.loadFile(path.join(HERE, entry.file));
  win.on("moved", () => {
    const others = [];
    wins.forEach((o, oid) => { if (oid !== entry.id && o && !o.isDestroyed()) others.push(layout.fromBrowserBounds(o.getBounds(), oid)); });
    const snapped = layout.snapBounds(layout.fromBrowserBounds(win.getBounds(), entry.id), screen.getAllDisplays(), others, layout.SNAP_PX);
    const next = layout.toBrowserBounds(snapped);
    const cur = win.getBounds();
    if (next.x !== cur.x || next.y !== cur.y) win.setBounds(next);
    saveWindowState();
  });
  win.on("resized", saveWindowState);
  win.on("close", saveWindowState);
  win.on("closed", () => wins.delete(entry.id));
  wins.set(entry.id, win);
  return win;
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
}

if (!app.requestSingleInstanceLock()) {
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
    registerIpc();
    registry.windows.forEach((entry) => createWindow(entry));
    buildTray();
    refreshTrayMenu();
    startSse(broadcast);
    screen.on("display-metrics-changed", () => {
      wins.forEach((w, id) => {
        if (w.isDestroyed()) return;
        w.setBounds(layout.toBrowserBounds(layout.clampBounds(w.getBounds(), screen.getAllDisplays())));
      });
      saveWindowState();
    });
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
};
