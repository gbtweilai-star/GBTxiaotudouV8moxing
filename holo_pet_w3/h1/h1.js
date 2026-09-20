/* GBT小土豆V8 · 窗口 6 赏金台（W8 · 阶段一 · 本机只读）
 * 只消费 main.cjs 的 w3:h1 只读口；取不到就不显示绿，灰态一律带原因。
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
(function () {
  "use strict";

  var bridge = window.gbtW3 || {};
  var api = typeof bridge.h1 === "function" ? bridge.h1 : null;

  function $(id) { return document.getElementById(id); }

  function setBadge(el, state, text) {
    if (!el) return;
    el.dataset.state = state || "gray";
    el.textContent = text || "";
  }

  function clear(node) { while (node && node.firstChild) node.removeChild(node.firstChild); }

  function row(cells, dim) {
    var tr = document.createElement("tr");
    if (dim) tr.className = "gbt-dim";
    cells.forEach(function (v) {
      var td = document.createElement("td");
      td.textContent = (v === null || v === undefined || v === "") ? "—" : String(v);
      tr.appendChild(td);
    });
    return tr;
  }

  function kv(host, pairs) {
    if (!host) return;
    clear(host);
    pairs.forEach(function (p) {
      var k = document.createElement("div"); k.className = "h1-k"; k.textContent = p[0];
      var v = document.createElement("div"); v.className = "h1-v"; v.textContent = p[1];
      host.appendChild(k); host.appendChild(v);
    });
  }

  function shaLabel(b) {
    if (!b.sha256) return "未读到";
    var tail = b.sha_match === true ? "（与侧车一致）"
      : b.sha_match === false ? "（与侧车不一致）" : "（无侧车可比）";
    return b.sha256.slice(0, 16) + "…" + tail;
  }

  function render(r) {
    var ok = r && r.ok === true;
    var body = ok ? r.data : (r && r.panel) || null;
    if (!body) {
      setBadge($("h1-badge"), "fault", "取不到");
      setBadge($("h1-foot-badge"), "fault", "取不到");
      if ($("h1-note")) $("h1-note").textContent = "取不到：" + ((r && r.error) || "面板无载荷");
      return;
    }
    var b = body.binary || {};
    var ready = body.badge === "ok";
    setBadge($("h1-badge"), body.badge || "gray",
      ready ? "就绪" : (b.present ? "部分就绪" : "未就绪"));
    setBadge($("h1-foot-badge"), body.badge || "gray", body.stage || "stage1");
    if ($("h1-note")) $("h1-note").textContent =
      (ok ? "" : "取不到：" + ((r && r.error) || "面板无载荷") + " —— ") + (body.note || "");
    kv($("h1-binary"), [
      ["二进制", b.path || "—"],
      ["存在", b.present ? "是" : "否"],
      ["大小", b.bytes ? b.bytes + " B" : "—"],
      ["版本", b.tag || "未登记"],
      ["sha256", shaLabel(b)],
      ["状态", b.reason || (b.present ? "已就位" : "取不到")],
    ]);
    var credBody = $("h1-cred-body");
    clear(credBody);
    ((body.credentials && body.credentials.items) || []).forEach(function (c) {
      credBody.appendChild(row([c.name, c.role, c.configured ? "已配置" : "未配置",
        c.read_by ? ("读取者：" + c.read_by) : "备注：h1mcp v0.1.4 不读取此名"], false));
    });
    if (credBody && !credBody.firstChild) credBody.appendChild(row(["—", "—", "未取", "—"], true));
    if ($("h1-sensitive")) $("h1-sensitive").textContent = body.sensitive_note || "";
    (body.api_surfaces || []).forEach(function (s) {
      var el = $("h1-" + s.id);
      if (el) el.textContent = "○ " + (s.title || s.id) + "：" + (s.reason || s.state || "未接入");
    });
    var d = body.drafts || {};
    kv($("h1-drafts"), [
      ["目录", d.path || "—"],
      ["状态", d.initialized ? "已初始化" : (d.reason || "未初始化")],
      ["草稿数", d.initialized ? String(d.count) : "—"],
    ]);
    var db = $("h1-draft-body");
    clear(db);
    (d.files || []).forEach(function (f) {
      db.appendChild(row([f.name, f.title, f.program_handle, f.bytes,
        f.mtime ? f.mtime.replace("T", " ").slice(0, 19) : (f.parse_error || "")], false));
    });
    if (db && !db.firstChild) {
      db.appendChild(row([d.initialized ? "（空）" : "未取", "—", "—", "—", d.reason || "—"], true));
    }
  }

  function refresh() {
    if (!api) {
      setBadge($("h1-badge"), "fault", "桥断");
      setBadge($("h1-foot-badge"), "fault", "桥断");
      if ($("h1-note")) $("h1-note").textContent = "preload 没挂 h1() 只读口 —— 判定为取不到，不显示绿。";
      return;
    }
    if (bridge.readonly !== true) {
      setBadge($("h1-badge"), "fault", "非只读");
      if ($("h1-note")) $("h1-note").textContent = "preload 未声明只读 —— 拒绝渲染。";
      return;
    }
    api().then(render).catch(function (err) {
      setBadge($("h1-badge"), "fault", "异常");
      if ($("h1-note")) $("h1-note").textContent = "w3:h1 调用异常：" + String((err && err.message) || err);
    });
  }

  var btn = $("btn-h1-refresh");
  if (btn) btn.addEventListener("click", refresh);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", refresh);
  else refresh();
})();
