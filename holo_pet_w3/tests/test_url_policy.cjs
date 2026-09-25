/* GBT小土豆V8 · 桌面壳 · URL / 窗口来源策略 · 契约测试
 *
 * 跑法（自动被 tests/run_tests.py 发现）：
 *     py -3.14 holo_pet_w3/tests/run_tests.py
 *   或 node --test holo_pet_w3/tests/test_url_policy.cjs
 *
 * 为什么这组测试必须存在：`shell/url-policy.cjs` 决定"这个常驻托盘壳能加载什么"。
 * 它原来是 `main.cjs` 里的一段内联代码，而 `main.cjs` 第一行就 require("electron")
 * ⇒ 在普通 node 下**根本没法测**，只能靠"我看着对"。抽成纯模块后，这里把每条规则钉死。
 *
 * 纪律：**负对照必须占多数** —— 只测"合法地址能过"等于没测防护。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
"use strict";

const test = require("node:test");
const assert = require("node:assert");
const path = require("node:path");

const P = require(path.join(__dirname, "..", "shell", "url-policy.cjs"));

/* ── 必须放行：本机回环 http/https ── */
test("放行：127.0.0.1 带端口", () => {
  const r = P.loopbackUrlOnly("http://127.0.0.1:3080/?token=abc");
  assert.strictEqual(r.ok, true, r.why);
  assert.match(r.url, /^http:\/\/127\.0\.0\.1:3080\//);
});

test("放行：localhost 与 ::1 与 [::1]", () => {
  for (const u of ["http://localhost:8765/x", "http://[::1]:3080/", "https://127.0.0.1/y"]) {
    const r = P.loopbackUrlOnly(u);
    assert.strictEqual(r.ok, true, u + " 应放行，实得 " + JSON.stringify(r));
  }
});

/* ── 必须拒绝：这是安全件的本体，逐个钉 ── */
test("拒绝：外部主机（http 与 https 都要拒）", () => {
  for (const u of ["http://example.com/", "https://evil.test/x", "http://192.168.1.10:3080/"]) {
    const r = P.loopbackUrlOnly(u);
    assert.strictEqual(r.ok, false, u + " 竟然放行了");
    assert.match(r.why, /回环|主机/, "拒绝理由必须说清是主机不合格");
  }
});

test("拒绝：危险协议 file/javascript/data", () => {
  for (const u of ["file:///C:/Windows/System32/calc.exe",
                   "javascript:alert(1)",
                   "data:text/html,<script>1</script>"]) {
    const r = P.loopbackUrlOnly(u);
    assert.strictEqual(r.ok, false, u + " 竟然放行了");
  }
});

test("拒绝：空 / 非 URL / 只有主机名", () => {
  for (const u of ["", "   ", "not a url", "127.0.0.1:3080"]) {
    const r = P.loopbackUrlOnly(u);
    assert.strictEqual(r.ok, false, JSON.stringify(u) + " 竟然放行了");
  }
});

test("拒绝理由不许是空串（静默拒绝比报错更难查）", () => {
  for (const u of ["", "http://example.com/", "file:///x", "javascript:1"]) {
    const r = P.loopbackUrlOnly(u);
    assert.strictEqual(r.ok, false);
    assert.ok(String(r.why || "").trim().length > 0, JSON.stringify(u) + " 的 why 是空的");
  }
});

/* ── 窗口来源决策：单一决策点 ── */
test("windowSource：带合法 url → kind=url", () => {
  const s = P.windowSource({ id: "a", url: "http://127.0.0.1:3080/" });
  assert.strictEqual(s.kind, "url");
});

test("windowSource：带非法 url → kind=blocked 且带 why（不许静默变 file）", () => {
  const s = P.windowSource({ id: "a", url: "http://example.com/" });
  assert.strictEqual(s.kind, "blocked");
  assert.ok(s.why, "blocked 必须带 why");
});

test("windowSource：needs_url → kind=connect 且带 port", () => {
  const s = P.windowSource({ id: "dsh-chat", needs_url: true, port: 3080 });
  assert.strictEqual(s.kind, "connect");
  assert.strictEqual(s.port, 3080);
});

test("windowSource：只有 file → kind=file", () => {
  const s = P.windowSource({ id: "g", file: "../index.html" });
  assert.strictEqual(s.kind, "file");
  assert.strictEqual(s.file, "../index.html");
});

test("windowSource：三样都没有 → blocked（不许猜一个默认页）", () => {
  const s = P.windowSource({ id: "empty" });
  assert.strictEqual(s.kind, "blocked");
});

test("优先级：url 存在时即使也写了 file，也必须按 url 判（不许回退到本地文件绕过白名单）", () => {
  const s = P.windowSource({ id: "x", url: "http://example.com/", file: "../index.html" });
  assert.strictEqual(s.kind, "blocked",
    "url 非法却回退去 loadFile ⇒ 白名单可被绕过");
});

/* ── 与真实注册表对照：现读的 windows.json 必须全过 ── */
test("现读 windows.json：每个窗都能被判成一个合法来源", () => {
  const fs = require("node:fs");
  const reg = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "shell", "windows.json"), "utf8"));
  assert.ok(Array.isArray(reg.windows) && reg.windows.length > 0);
  for (const w of reg.windows) {
    const s = P.windowSource(w);
    assert.ok(["url", "connect", "file"].includes(s.kind),
      `窗 ${w.id} 判成了 ${s.kind}（${s.why || ""}）—— 注册表里有个加载不了的窗`);
  }
});
