/* GBT小土豆V8 · 桌面壳 · URL 与窗口来源策略（**纯函数模块**）
 *
 * 为什么单独抽出来：这段是**安全件**（决定"壳能加载什么"）。
 * 它原来内联在 `main.cjs` 里，而 `main.cjs` 第一行就 `require("electron")` ——
 * 于是**根本没法在普通 node 下单元测试**，只能靠"我看着对"。
 * 抽成不依赖 electron 的纯模块后，`tests/test_url_policy.cjs` 能直接 require 它，
 * 用 `node --test` 把每条接受/拒绝规则钉死。
 *
 * 规则（就一条）：**只放行本机回环 http/https**。
 *   放行：http(s)://127.0.0.1:* / localhost / ::1 / [::1]
 *   拒绝：外部主机、file:、javascript:、data:、非 URL、空
 * 为什么必须这么严：这是个**常驻托盘 + preload 的壳**。`loadURL` 一旦不限域，
 *   它就变成一个通用浏览器 —— 完全不同的安全面。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
"use strict";

const LOOPBACK_HOSTS = new Set(["127.0.0.1", "localhost", "::1", "[::1]"]);
const OK_PROTOCOLS = new Set(["http:", "https:"]);

/** 只放行本机回环 http/https。返回 `{ ok, url }` 或 `{ ok:false, why }`。 */
function loopbackUrlOnly(raw) {
  const s = String(raw == null ? "" : raw).trim();
  if (!s) return { ok: false, why: "空 URL" };
  let u;
  try {
    u = new URL(s);
  } catch (err) {
    return { ok: false, why: "不是合法 URL：" + s.slice(0, 80) };
  }
  if (!OK_PROTOCOLS.has(u.protocol)) {
    return { ok: false, why: "只放行 http/https，收到 " + u.protocol };
  }
  if (!LOOPBACK_HOSTS.has(u.hostname)) {
    return { ok: false, why: "只放行本机回环，收到主机 " + u.hostname };
  }
  return { ok: true, url: u.toString() };
}

/** 主机名是不是回环（给别的调用方复用，别各写一份）。 */
function isLoopbackHost(host) {
  return LOOPBACK_HOSTS.has(String(host == null ? "" : host));
}

/**
 * 一个窗注册项该加载什么 —— **单一决策点**。
 *
 * 返回 `{kind, ...}`：
 *   `url`     带着 `url`（已过白名单）→ 主进程 `loadURL`
 *   `blocked` 声明了 url 但不合法 → 落到拒绝页，`why` 写清原因（**不静默**）
 *   `connect` 声明了 `needs_url`（要主人运行时给 URL，例如 DSH 对话面）→ 落到本地引导页
 *   `file`    本地文件 → `loadFile`
 */
function windowSource(entry) {
  const e = entry || {};
  if (e.url) {
    const chk = loopbackUrlOnly(e.url);
    return chk.ok
      ? { kind: "url", url: chk.url }
      : { kind: "blocked", why: chk.why, id: e.id };
  }
  if (e.needs_url) {
    return { kind: "connect", id: e.id, port: Number(e.port) || 0 };
  }
  if (e.file) {
    return { kind: "file", file: e.file };
  }
  return { kind: "blocked", why: "既没有 url、也没有 needs_url、也没有 file", id: e.id };
}

module.exports = { LOOPBACK_HOSTS, OK_PROTOCOLS, loopbackUrlOnly, isLoopbackHost, windowSource };
