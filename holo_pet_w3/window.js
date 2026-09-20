/* GBT小土豆V8 · 上帝视角 · 数据绑定（W3）
 *
 * 纪律（《W3上帝视角镜像方案.md》§2.1 / §10.5）：
 *   1) 只读——本文件**不含任何写调用**：没有 fetch、没有 POST、没有 fs。
 *      全部数据经 preload 暴露的只读 IPC 拿；SSE 订阅在主进程侧（同一条 /api/events）。
 *   2) 不假数据——取不到就显示"取不到 + 原因"，不拿默认值顶替。
 *   3) 假绿铁律——没有探针在跑的点一律灰，**灰绝不渲染成绿**。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
(function () {
  "use strict";

  var $ = function (id) { return document.getElementById(id); };
  var bridge = window.gbtW3 || null;

  var REFRESH_MS = 5000;              /* §11.4：节点状态 5 s 一刷 */
  var TTL_DEFAULT_S = 180;            /* 与 W2.5 probe.json 的 ttl_s 对齐 */
  var MATRIX = [];                    /* 母表行缓存（来自 §10.2，不在此另立） */
  var FILTER = "";

  /* ── 工具 ── */

  function noBridge() {
    return { ok: false, error: "没有接上宿主进程（gbtW3 未注入）—— 取不到" };
  }

  function callBridge(name, payload) {
    if (!bridge || typeof bridge[name] !== "function") return Promise.resolve(noBridge());
    try {
      var call = (payload === undefined) ? bridge[name]() : bridge[name](payload);
      return Promise.resolve(call).catch(function (err) {
        return { ok: false, error: String(err && err.message ? err.message : err) };
      });
    } catch (err) {
      return Promise.resolve({ ok: false, error: String(err) });
    }
  }

  function put(el, payload, pretty) {
    if (!el) return;
    if (!payload || payload.ok !== true) {
      el.textContent = "取不到：" + ((payload && payload.error) || "原因未报");
      el.dataset.state = "fault";
      return;
    }
    el.dataset.state = "ok";
    el.textContent = pretty ? JSON.stringify(payload.data, null, 2) : String(payload.data);
  }

  function textOf(v) { return v === undefined || v === null ? "—" : String(v); }

  /* ── 假绿铁律：记录超期即灰 ── */

  function ageSeconds(ts) {
    var t = Date.parse(String(ts || "").replace(" ", "T"));
    if (isNaN(t)) return null;
    return (Date.now() - t) / 1000;
  }

  function healthStateOf(rec) {
    /* 返回 §10.3 四态之一。缺记录 = 灰；超期 = 灰；fail = 红/黄。 */
    if (!rec) return "gray";
    var ttl = Number(rec.ttl_s || TTL_DEFAULT_S);
    var age = ageSeconds(rec.ts);
    if (age === null || age > ttl) return "gray";
    if (String(rec.result) === "ok") return "ok";
    var d = String(rec.detail || "");
    if (d.indexOf("process_alive:") === 0) return "fault";
    return "warn";
  }

  /* ── 顶部徽章 ── */

  function setBadge(el, state, text) {
    if (!el) return;
    el.dataset.state = state;
    el.textContent = text;
  }

  /* ── 视图切换 ── */

  function showView(name) {
    var views = document.querySelectorAll(".gbt-view");
    for (var i = 0; i < views.length; i++) views[i].removeAttribute("data-active");
    var tabs = document.querySelectorAll(".gbt-tab");
    for (var j = 0; j < tabs.length; j++) tabs[j].removeAttribute("data-active");
    var view = $("view-" + name);
    if (view) view.setAttribute("data-active", "true");
    var tab = document.querySelector('.gbt-tab[data-view="' + name + '"]');
    if (tab) tab.setAttribute("data-active", "true");
  }

  /* ── 工作树：三层叠加里的第①层（结构） ── */

  function parseMarkmap(text) {
    /* 把 Markmap 的 markdown 转成 {label, children} 树。标题与列表都吃。 */
    var root = { label: "GBT小土豆V8", children: [], depth: -1 };
    var stack = [root];
    String(text || "").split(/\r?\n/).forEach(function (raw) {
      var line = raw.replace(/\s+$/, "");
      if (!line.trim() || line.trim() === "```markdown" || line.trim() === "```") return;
      var m = /^(#{1,6})\s+(.*)$/.exec(line);
      var depth, label;
      if (m) {
        depth = m[1].length - 1;
        label = m[2].trim();
      } else {
        m = /^(\s*)[-*]\s+(.*)$/.exec(line);
        if (!m) return;
        depth = Math.floor(m[1].replace(/\t/g, "  ").length / 2) + 1;
        label = m[2].trim();
      }
      while (stack.length > 1 && stack[stack.length - 1].depth >= depth) stack.pop();
      var node = { label: label, children: [], depth: depth };
      stack[stack.length - 1].children.push(node);
      stack.push(node);
    });
    return root;
  }

  function detectEngine(pref) {
    if (pref && pref !== "auto") return pref;
    if (window.markmap && typeof window.markmap.Markmap === "function") return "markmap";
    if (window.d3 && typeof window.d3.hierarchy === "function") return "d3";
    return "text";   /* 离线可用、永远跑得通的那条 */
  }

  function renderTreeText(node, host, depth) {
    var wrap = document.createElement("div");
    wrap.className = "gbt-node";
    wrap.dataset.state = node.state || "off";
    wrap.dataset.hot = node.hot ? "true" : "false";
    var label = document.createElement("span");
    label.className = "gbt-node-label";
    label.textContent = node.label;
    label.addEventListener("click", function () {
      openSidebar("节点", {
        label: node.label,
        file: node.file || "未登记 file:line",
        pid: node.pid || "未登记 pid",
        port: node.port || "未登记 port",
        faults: node.faults || [],
        note: "节点大小 = 资源占用：本机 psutil 未装，按《反空壳律》画『未启用』，不用默认值顶替。",
      });
    });
    wrap.appendChild(label);
    var kids = node.children || [];
    for (var i = 0; i < kids.length; i++) wrap.appendChild(renderTreeText(kids[i], host, depth + 1));
    return wrap;
  }

  function renderTree(payload) {
    var host = $("tree-host");
    if (!host) return;
    var engine = detectEngine(payload && payload.engine);
    host.dataset.engine = engine;
    var badge = $("tree-engine");
    if (badge) badge.textContent = engine + (engine === "text" ? "（离线兜底）" : "");
    host.innerHTML = "";
    if (!payload || payload.ok !== true) {
      host.textContent = "取不到工作树：" + ((payload && payload.error) || "原因未报");
      return;
    }
    var tree = parseMarkmap(payload.text);
    if (engine === "markmap") {
      var svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      host.appendChild(svg);
      window.markmap.Markmap.create(svg, null, window.markmap.transform(payload.text));
      return;
    }
    if (engine === "d3") {
      var root = window.d3.hierarchy(tree);
      var out = window.d3.tree().nodeSize([22, 220])(root);
      var g = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      g.setAttribute("width", "100%");
      g.setAttribute("height", String((out.height + 1) * 22));
      out.descendants().forEach(function (d) {
        var t = document.createElementNS("http://www.w3.org/2000/svg", "text");
        t.setAttribute("x", String(d.y + 8));
        t.setAttribute("y", String(d.x + 14));
        t.setAttribute("fill", "currentColor");
        t.textContent = d.data.label;
        g.appendChild(t);
      });
      host.appendChild(g);
      return;
    }
    host.appendChild(renderTreeText(tree, host, 0));
    applyFilter();
  }

  /* ── 故障矩阵：逐点吃母表，行本身不在此新定 ── */

  function modeClass(mark) {
    if (mark === "✓") return "mode-yes";
    if (mark === "S") return "mode-s";
    if (mark === "✗") return "mode-no";
    return "mode-na";
  }

  function renderMatrix(payload, health) {
    var body = $("matrix-body");
    var src = $("matrix-source");
    if (!body) return;
    body.innerHTML = "";
    if (!payload || payload.ok !== true || !payload.rows || !payload.rows.length) {
      var tr = document.createElement("tr");
      var td = document.createElement("td");
      td.colSpan = 7;
      td.className = "gbt-dim";
      td.textContent = "取不到矩阵：" + ((payload && payload.error) || "母表未读到");
      tr.appendChild(td);
      body.appendChild(tr);
      if (src) src.textContent = "来源：取不到";
      return;
    }
    if (src) src.textContent = "来源：" + (payload.source || "—");
    MATRIX = payload.rows;
    var blind = 0, active = 0;
    payload.rows.forEach(function (row) {
      var tr2 = document.createElement("tr");
      /* 只读期：store/health 里没有逐点记录 → 一律灰（不假绿） */
      var rec = health && health.byFault ? health.byFault[row.id] : null;
      var state = healthStateOf(rec);
      var isBlind = false;
      if (!rec && row.user === "✓" && row.probe === "✗" && row.beat === "✗" && row.audit === "✗") {
        blind += 1;                       /* 只靠用户 = 盲区 */
        isBlind = true;
      }
      if (state === "fault" || state === "warn") active += 1;
      tr2.dataset.state = state;
      /* 盲区独立标记：只喂 CSS §9.1 的深空紫描边，**不动** data-state 的四色语义 */
      if (isBlind) tr2.dataset.blind = "true";
      tr2.dataset.hit = (FILTER && row.label.toLowerCase().indexOf(FILTER) < 0) ? "false" : "true";

      var tdName = document.createElement("td");
      tdName.textContent = row.label;
      tr2.appendChild(tdName);
      ["probe", "beat", "audit", "user"].forEach(function (k) {
        var cell = document.createElement("td");
        cell.className = modeClass(row[k]);
        cell.textContent = row[k];
        tr2.appendChild(cell);
      });
      var tdState = document.createElement("td");
      tdState.className = "state";
      tdState.textContent = ({ ok: "健康", warn: "告警 / 降级中", fault: "故障", gray: "灰（未启用）" })[state];
      if (isBlind) {
        var blindTag = document.createElement("span");
        blindTag.className = "gbt-blind-tag";
        blindTag.textContent = "盲区";
        tdState.appendChild(blindTag);
      }
      tr2.appendChild(tdState);
      var tdWhy = document.createElement("td");
      tdWhy.textContent = row.why || "—";
      tr2.appendChild(tdWhy);

      tr2.addEventListener("click", function () {
        openSidebar(row.label, {
          五要素: "检 / 诊 / 恢 / 降 / 审 —— 逐条见《GBT全故障点设计.md》§十一–§十四",
          探针: row.probe, 心跳: row.beat, 审计: row.audit, 用户: row.user,
          判定: row.why, 当前状态: tdState.textContent,
          健康记录: rec || "store/health 里没有这一点的记录（灰，不许当绿）",
        });
      });
      body.appendChild(tr2);
    });
    $("stat-blind").textContent = String(blind);
    $("stat-active").textContent = String(active);
    applyFilter();
  }

  /* ── 搜索过滤（矩阵行 + 树节点共用） ── */

  function applyFilter() {
    var rows = document.querySelectorAll("#matrix-body tr");
    for (var i = 0; i < rows.length; i++) {
      var hit = !FILTER || String(rows[i].textContent || "").toLowerCase().indexOf(FILTER) >= 0;
      rows[i].dataset.hit = hit ? "true" : "false";
    }
    var nodes = document.querySelectorAll("#tree-host .gbt-node");
    for (var j = 0; j < nodes.length; j++) {
      var label = nodes[j].querySelector(".gbt-node-label");
      var ok = !FILTER || String(label ? label.textContent : "").toLowerCase().indexOf(FILTER) >= 0;
      nodes[j].dataset.hit = ok ? "true" : "false";
    }
  }

  /* ── 右侧边栏 ── */

  function openSidebar(title, body) {
    var bar = $("sidebar");
    if (!bar) return;
    $("sidebar-title").textContent = title;
    $("sidebar-body").textContent = typeof body === "string" ? body : JSON.stringify(body, null, 2);
    bar.hidden = false;
  }

  /* ── 一轮刷新 ── */

  function refresh() {
    callBridge("state").then(function (r) { put($("card-self"), r, true); });
    callBridge("tasks").then(function (r) { put($("card-tasks"), r, true); });
    callBridge("env").then(function (r) { put($("card-env"), r, true); });
    callBridge("ledger").then(function (r) { put($("card-ledger"), r, true); });
    callBridge("matrix").then(function (m) {
      callBridge("health").then(function (h) {
        renderMatrix(m, h && h.ok ? h.data : null);
        setBadge($("health-badge"), overallState(h && h.ok ? h.data : null),
                 "健康度 " + overallText(h && h.ok ? h.data : null));
      });
    });
    callBridge("mindmap").then(function (r) {
      var cfg = null;
      renderTree(r.ok ? { ok: true, text: r.data, engine: cfg } : r);
    });
    var clock = $("stat-clock");
    if (clock) clock.textContent = new Date().toLocaleTimeString("zh-CN");
  }

  function overallState(health) {
    if (!health || !health.records || !health.records.length) return "gray";
    var worst = "gray";
    health.records.forEach(function (rec) {
      var s = healthStateOf(rec);
      if (s === "fault") worst = "fault";
      else if (s === "warn" && worst !== "fault") worst = "warn";
      else if (s === "ok" && worst === "gray") worst = "ok";
    });
    return worst;
  }

  function overallText(health) {
    if (!health || !health.records || !health.records.length) return "无记录（灰）";
    var n = { ok: 0, warn: 0, fault: 0, gray: 0 };
    health.records.forEach(function (rec) { n[healthStateOf(rec)] += 1; });
    return "绿 " + n.ok + " / 黄 " + n.warn + " / 红 " + n.fault + " / 灰 " + n.gray;
  }

  /* ── §12 工具出口（只读视图 · 刀 2b） ── */

  function toolsRow(tbody, cap, act) {
    var tr = document.createElement("tr");
    var tdCap = document.createElement("td");
    tdCap.textContent = cap;
    var tdAct = document.createElement("td");
    tdAct.textContent = act.name;
    var tdState = document.createElement("td");
    var badge = document.createElement("span");
    badge.className = "gbt-badge";
    badge.dataset.state = act.state === "live" ? "ok" : "gray";
    badge.textContent = act.state === "live" ? "可用" : "未开放";
    tdState.appendChild(badge);
    var tdWhy = document.createElement("td");
    tdWhy.className = "gbt-dim";
    tdWhy.textContent = act.reason || "—";
    tr.appendChild(tdCap); tr.appendChild(tdAct); tr.appendChild(tdState); tr.appendChild(tdWhy);
    tbody.appendChild(tr);
  }

  function toolsFail(tbody, msg) {
    var tr = document.createElement("tr");
    var td = document.createElement("td");
    td.colSpan = 4;
    td.className = "gbt-dim";
    td.textContent = "✕ 取不到：" + (msg || "未知原因");
    tr.appendChild(td);
    tbody.appendChild(tr);
  }

  function renderTools(r) {
    var tbody = $("tools-body");
    if (!tbody) return;
    tbody.textContent = "";
    var store = $("tools-store");
    var note = $("tools-note");
    var foot = $("tools-foot");
    var okData = (r && r.ok) ? r.data : null;
    if (store) store.textContent = okData ? (okData.store || "—") : "取不到";
    if (note) note.textContent = okData ? (okData.note || "") : String((r && r.error) || "取不到");
    if (foot) foot.textContent = okData ? (okData.not_exported_note || "—") : "取不到就不显示绿（负对照口径）";
    if (!okData) { toolsFail(tbody, r && r.error); return; }
    var caps = okData.caps || [];
    for (var i = 0; i < caps.length; i++) {
      var acts = caps[i].actions || [];
      for (var j = 0; j < acts.length; j++) toolsRow(tbody, caps[i].cap, acts[j]);
    }
  }

  function loadTools() {
    callBridge("tools").then(renderTools);
  }


  /* ── §13 数字人召唤台 + AI 朋友圈（W9） ──
   * 纪律照旧：只读——本段没有 fetch / 没有 fs / 没有写调用；
   * 召唤是一次 IPC，真正的 spawn 在主进程；渲染层只是把「就绪态」如实画出来。
   * 就绪才给点；未就绪按钮禁用，原因写在旁边（灰绝不画成绿）。
   */

  var PETS = null;

  function newEl(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined && text !== null) e.textContent = String(text);
    return e;
  }

  function carrierCard(row) {
    var card = newEl("div", "gbt-pet");
    card.dataset.ready = row.ready ? "true" : "false";
    card.appendChild(newEl("h3", null, row.title || row.id));
    card.appendChild(newEl("div", "gbt-pet-state", row.ready ? "就绪" : "未就绪"));
    card.appendChild(newEl("div", "gbt-pet-reason", row.reason || "—"));
    if (row.note) card.appendChild(newEl("div", "gbt-pet-reason", row.note));
    var btn = newEl("button", "gbt-btn", "召唤数字人");
    btn.type = "button";
    btn.disabled = row.ready !== true;
    if (btn.disabled) btn.title = "不就绪不给点：" + (row.reason || "原因未报");
    btn.addEventListener("click", function () { summonCarrier(row.id); });
    card.appendChild(btn);
    return card;
  }

  function modelCard(row) {
    var card = newEl("div", "gbt-pet");
    card.dataset.ready = row.ready ? "true" : "false";
    card.appendChild(newEl("h3", null, row.name));
    card.appendChild(newEl("div", "gbt-pet-reason",
      "动作 " + row.motions + " · 表情 " + row.expressions + " · 贴图 " + row.textures +
      " · " + Math.round((row.bytes || 0) / 1024) + " KB"));
    card.appendChild(newEl("div", row.ready ? "gbt-pet-reason" : "gbt-pet-issues",
      row.ready ? "齐件：model3 + moc3 + 贴图都在" : row.issues.join(" · ")));
    return card;
  }

  function renderPets(r) {
    var hosts = $("pets-carriers");
    var mhost = $("pets-models");
    if (!hosts || !mhost) return;
    hosts.textContent = "";
    mhost.textContent = "";
    var note = $("pets-note");
    var py = $("pets-python");
    var cnt = $("pets-count");
    var out = $("pets-summon-out");
    var d = (r && r.ok) ? r.data : null;
    if (!d) {
      hosts.appendChild(newEl("div", "gbt-pet-reason", "取不到：" + ((r && r.error) || "原因未报")));
      mhost.appendChild(newEl("div", "gbt-pet-reason", "取不到就不显示绿（负对照口径）"));
      if (py) py.textContent = "Python 腿：取不到";
      return;
    }
    PETS = d;
    if (note) note.textContent = d.note || "";
    if (cnt) cnt.textContent = d.model_count + " 个（" + (d.resources_present ? "目录在位" : "目录不在位") + "）";
    if (py) {
      py.textContent = "Python 腿：" + (d.python.checked
        ? (d.python.pyside6 && d.python.live2d ? "就位" : "缺依赖")
        : "探针没跑起来");
    }
    (d.carriers || []).forEach(function (row) { hosts.appendChild(carrierCard(row)); });
    var models = d.models || [];
    if (!models.length) {
      mhost.appendChild(newEl("div", "gbt-pet-reason",
        "形象库为空或目录不在位 —— 按《反空壳律》如实记，不画假形象"));
    }
    models.forEach(function (row) { mhost.appendChild(modelCard(row)); });
    if ((d.issues || []).length) {
      d.issues.forEach(function (t) { mhost.appendChild(newEl("div", "gbt-pet-issues", "✕ " + t)); });
    }
    if (out) out.textContent = "主载体：" + (d.primary || "无（两条腿都不就绪）");
  }

  function loadPets(force) {
    callBridge("pets", { refresh: force === true }).then(renderPets);
  }

  function summonCarrier(id) {
    var out = $("pets-summon-out");
    if (out) out.textContent = "召唤中…（只起一个本机窗口，不写文件、不发网络）";
    callBridge("summon", { carrier: id }).then(function (r) {
      if (out) {
        out.textContent = (r && r.ok)
          ? ("已召唤 · " + id + " · pid " + r.data.pid + " · " + (r.data.reason || ""))
          : ("召唤被拒：" + ((r && r.error) || "原因未报"));
      }
      openSidebar("召唤结果", (r && r.ok) ? r.data : { error: (r && r.error) || "取不到" });
    });
  }

  function renderEigenflux(r) {
    var R = window.gbtEfRender;
    var feed = $("ef-feed");
    var friends = $("ef-friends");
    var msgs = $("ef-messages");
    var prof = $("ef-profile");
    var note = $("ef-note");
    if (!R) {
      if (note) note.textContent = "渲染层没加载（ef_render.js 没进来）—— 取不到就显示取不到";
      return;
    }
    var d = (r && r.ok) ? r.data : null;
    if (!d) {
      var why = "取不到：" + ((r && r.error) || "原因未报");
      if (note) note.textContent = why;
      if (feed) R.empty(feed, why);
      return;
    }
    if (note) {
      note.textContent = "本机 " + d.home_label + " · 好友 " + d.counts.friends +
        " / 动态 " + d.counts.feed + " / 私信 " + d.counts.messages +
        (d.source && d.source.feed ? (" · 动态源 " + d.source.feed.file) : "");
    }
    if (feed) {
      R.list(feed, d.feed, R.item,
        d.initialized ? "动态流是空的（本机缓存里确实没有条目）" : "未初始化：本机还没有 EigenFlux");
      R.issues(feed, d.issues);
    }
    if (friends) R.list(friends, d.friends, R.friend, "没有好友记录");
    if (msgs) R.list(msgs, d.messages, R.message, "没有私信记录");
    if (prof) { prof.textContent = ""; prof.appendChild(R.profile(d.profile)); }
  }

  function loadEigenflux() { callBridge("eigenflux").then(renderEigenflux); }
  /* ── 绑定 ── */

  function bind() {
    var tabs = document.querySelectorAll(".gbt-tab");
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].addEventListener("click", function (ev) { showView(ev.currentTarget.dataset.view); });
    }
    $("btn-refresh").addEventListener("click", refresh);
    $("btn-collapse").addEventListener("click", function () {
      var nodes = document.querySelectorAll("#tree-host .gbt-node");
      for (var k = 0; k < nodes.length; k++) {
        if ((nodes[k].dataset.depth || 0) >= 2) nodes[k].hidden = !nodes[k].hidden;
      }
    });
    $("btn-selfcheck").addEventListener("click", function () {
      callBridge("selfcheck").then(function (r) {
        openSidebar(
          "自检（只读态）",
          (r && r.ok ? r.data : { error: (r && r.error) || "取不到" })
        );
      });
    });
    $("search-box").addEventListener("input", function (ev) {
      FILTER = String(ev.target.value || "").trim().toLowerCase();
      applyFilter();
    });
    $("btn-sidebar-close").addEventListener("click", function () { $("sidebar").hidden = true; });
    $("btn-blind-detail").addEventListener("click", function () {
      openSidebar("盲区整改", "盲区 = 四模态里只有『用户』一列为 ✓ 的点；逐条整改见《GBT全故障点设计.md》§十五。");
    });
    $("btn-schedule").addEventListener("click", function () {
      $("cockpit-out").textContent = "只读态：全局调度在 W3 阶段不产生任何写操作——本次只显示，不动手。";
    });
    $("btn-introspect").addEventListener("click", function () {
      callBridge("introspect").then(function (r) {
        $("cockpit-out").textContent = JSON.stringify(r && r.ok ? r.data : { error: (r && r.error) || "取不到" }, null, 2);
      });
    });
    var toolsTab = document.querySelector('.gbt-tab[data-view="tools"]');
    if (toolsTab) toolsTab.addEventListener("click", function () { loadTools(); });
    var toolsBtn = $("btn-tools-refresh");
    if (toolsBtn) toolsBtn.addEventListener("click", loadTools);
    var petsTab = document.querySelector('.gbt-tab[data-view="pets"]');
    if (petsTab) petsTab.addEventListener("click", function () { loadPets(false); loadEigenflux(); });
    var petsBtn = $("btn-pets-refresh");
    if (petsBtn) petsBtn.addEventListener("click", function () { loadPets(true); loadEigenflux(); });    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape") $("sidebar").hidden = true;
    });
  }

  /* ── 起 ── */

  function boot() {
    bind();
    showView("quad");
    if (bridge && typeof bridge.onEvent === "function") {
      bridge.onEvent(function (msg) {
        var badge = $("stream-badge");
        if (badge) { badge.dataset.state = "ok"; badge.textContent = "实时流：已接 · " + (msg && msg.event ? msg.event : "event"); }
        if (msg && msg.kind === "health") refresh();
      });
    }
    if (bridge && typeof bridge.onStreamState === "function") {
      bridge.onStreamState(function (st) {
        setBadge($("stream-badge"), st === "open" ? "ok" : "gray",
                 "实时流：" + (st === "open" ? "已接" : "未接（退到 5 s 轮询）"));
      });
    }
    refresh();
    setInterval(refresh, REFRESH_MS);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
}());
