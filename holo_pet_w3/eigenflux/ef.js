/* GBT小土豆V8 · AI 朋友圈（独立窗 · W9）
 *
 * 只读：数据全部经 window.gbtW3.eigenflux() 从主进程拿（本机 EigenFlux 缓存）。
 * 本文件不含 fetch / fs / 任何写调用，也不发消息、不调 API、不拉 scope。
 * 空态一律写**理由**，不写占位数字（《反空壳律》：取不到就显示取不到 + 原因）。
 *
 * 卡片 DOM 由 ../ef_render.js 提供（与上帝视角窗口共用一份，免得两处对不上）。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var bridge = window.gbtW3 || null;

  function show(name) {
    var views = document.querySelectorAll(".ef-view");
    for (var i = 0; i < views.length; i++) views[i].removeAttribute("data-active");
    var tabs = document.querySelectorAll(".gbt-tab");
    for (var j = 0; j < tabs.length; j++) tabs[j].removeAttribute("data-active");
    var v = $("efview-" + name);
    if (v) v.setAttribute("data-active", "true");
    var t = document.querySelector('.gbt-tab[data-ef="' + name + '"]');
    if (t) t.setAttribute("data-active", "true");
  }

  function render(r) {
    var R = window.gbtEfRender;
    var state = $("ef-state");
    var counts = $("ef-counts");
    var source = $("ef-source");

    if (!R) {
      if (state) { state.dataset.state = "fault"; state.textContent = "渲染层缺失"; }
      if (source) source.textContent = "ef_render.js 没加载 —— 取不到就显示取不到";
      return;
    }

    var d = (r && r.ok) ? r.data : null;
    if (!d) {
      var why = "取不到：" + ((r && r.error) || "原因未报");
      if (state) { state.dataset.state = "gray"; state.textContent = "取不到"; }
      R.empty($("ef-feed-list"), why);
      R.empty($("ef-friend-list"), why);
      R.empty($("ef-msg-list"), why);
      R.empty($("ef-profile-list"), why);
      return;
    }

    if (state) {
      state.dataset.state = d.initialized ? "ok" : "gray";
      state.textContent = d.initialized ? "本机只读 · 已接" : "未初始化";
    }
    if (counts) {
      counts.dataset.state = "gray";
      counts.textContent = "好友 " + d.counts.friends + " · 动态 " + d.counts.feed +
        " · 私信 " + d.counts.messages;
    }
    if (source) {
      source.textContent = "通道：本机只读 " + d.home_label +
        (d.source && d.source.feed
          ? (" · 动态源 " + d.source.feed.file + "（" + (d.source.feed.mtime || "—") + "）")
          : "");
    }

    var feed = $("ef-feed-list");
    R.list(feed, d.feed, R.item,
      d.initialized ? "动态流是空的（本机缓存里确实没有条目）" : "未初始化：本机还没有 EigenFlux");
    R.issues(feed, d.issues);
    R.list($("ef-friend-list"), d.friends, R.friend, "没有好友记录");
    R.list($("ef-msg-list"), d.messages, R.message, "没有私信记录");

    var prof = $("ef-profile-list");
    if (prof) { prof.textContent = ""; prof.appendChild(R.profile(d.profile)); }
  }

  function load() {
    if (!bridge || typeof bridge.eigenflux !== "function") {
      render({ ok: false, error: "没有接上宿主进程（gbtW3 未注入）—— 取不到" });
      return;
    }
    var p;
    try { p = bridge.eigenflux(); }
    catch (err) { render({ ok: false, error: String(err) }); return; }
    Promise.resolve(p).then(render).catch(function (err) {
      render({ ok: false, error: String((err && err.message) || err) });
    });
  }

  function bind() {
    var tabs = document.querySelectorAll(".gbt-tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].addEventListener("click", function (ev) { show(ev.currentTarget.dataset.ef); });
    }
    var btn = $("ef-refresh");
    if (btn) btn.addEventListener("click", load);
  }

  function boot() { bind(); show("feed"); load(); }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
}());