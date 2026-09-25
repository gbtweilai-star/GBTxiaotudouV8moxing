/**
 * GBT小土豆V8 · 面板加装 · 浏览器半边（已构建 bundle）
 *
 * 口径（Owner 2026-09-22 定）：
 *   ① 原面板（对话面板）保持原样，只往上加装能力 —— 不另起中央面板、不占左栏图标位；
 *   ② **一律内嵌**：面板嵌在 DSH 自己的浮层位（`shell.overlay`）里用 iframe 呈现，
 *      **不做任何跳转**（不开新窗口/新标签页）。
 *
 * 入口（2026-09-23 主人令后改）：**不再往会话头贴按钮**（原话「把这两个去掉…太难看了」
 * ＋「挨个镶嵌进去设计」）。改成嵌进左栏既有设计，一点界面都不多占：
 *   ① 左栏**品牌标本身可点** ⇒ 打开面板清单；
 *   ② 左栏**脚部**两条动作（走装机自己的 `sidebar.footer.action` 槽）⇒ 「面板」/「上帝视角」。
 * 面板本体仍一律内嵌在 `shell.overlay` 浮层里，iframe 呈现，**不做任何跳转**。
 * 品牌加装：左栏品牌行的标/名、新会话大标题上的品牌标。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */

/* 残留名册条目兼容壳：改名前的 id 仍留在这个进程的浏览器名册里（对账只认当前存在的
   entry 名，所以它们会一直留到进程重启）。给它们不放副作用的空壳，那几条也能正常解析，
   页面不会多报"找不到模块"；**重启后随名册重算自然消失** —— 这是唯一该留的兼容壳，
   别在磁盘上再留旧副本（旧副本才是重启后误导模型的源头）。

   本包改过九次名，所以有九个旧 id：
     gbt-master              （第一代 · v1.0.x）
     gbt-potato-master       （第二代）
     gbt-potato-master-v2    （第三代）
     gbt-potato-master-v3    （第四代）
     gbt-potato-master-v4    （第五代）
     gbt-potato-master-v5    （第六代）
     gbt-potato-master-v6    （第七代）
     gbt-potato-master-v7    （第八代）
     gbt-potato-master-v8    （第九代 · 现役为 gbt-potato-master-v9） */
function __gbtStub(id) {
	window.__ModuleLoader__.load({
		id: id,
		factory: () => {
			var stub = { exports: {} };
			stub.exports.apply = function () {};
			stub.exports.inject = [];
			return stub.exports;
		}
	});
}
__gbtStub("gbt-master");
__gbtStub("gbt-potato-master");
__gbtStub("gbt-potato-master-v2");
__gbtStub("gbt-potato-master-v3");
__gbtStub("gbt-potato-master-v4");
__gbtStub("gbt-potato-master-v5");
__gbtStub("gbt-potato-master-v6");
__gbtStub("gbt-potato-master-v7");
__gbtStub("gbt-potato-master-v8");

window.__ModuleLoader__.load({
	id: "gbt-potato-master-v9",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });

		const React = require("react");

		const BASE = "/gbt-master";
		const FS_BASE = BASE + "/fs/";
		const LOGO = FS_BASE + "assets/brand/logo-potato-64.png";
		const GODVIEW_ID = "w3";
		const SIGN = "开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属";

		const CSS = [
			".gbtm-root{--gbtm-gold:#F5B041;--gbtm-cyan:#00E5FF;--gbtm-violet:#7C4DFF;--gbtm-bg:#060912;--gbtm-panel:#131a30;--gbtm-line:rgba(124,77,255,.34);--gbtm-soft:rgba(0,229,255,.18);--gbtm-text:#E8ECF8;--gbtm-dim:#9AA4C4;--gbtm-radius:12px}",
			".gbtm-gv{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid var(--gbtm-line);color:var(--gbtm-text);border-radius:999px;padding:3px 10px;cursor:pointer;font-size:12px;line-height:1.4;white-space:nowrap}",
			".gbtm-gv:hover{border-color:var(--gbtm-cyan);color:var(--gbtm-cyan)}",
			".gbtm-gvmark{display:block;border-radius:4px}",
			".gbtm-sidebar-mark{display:block;border-radius:7px;box-shadow:0 0 0 1px var(--gbtm-line),0 0 14px var(--gbtm-soft)}",
			".gbtm-sidebar-name{font-weight:800;font-size:15px;letter-spacing:.6px;white-space:nowrap;background:linear-gradient(90deg,var(--gbtm-violet),var(--gbtm-cyan),var(--gbtm-gold));-webkit-background-clip:text;background-clip:text;color:transparent}",
			".gbtm-bigmark{display:block;border-radius:18px;box-shadow:0 0 0 1px var(--gbtm-line),0 0 40px var(--gbtm-soft)}",
			/* 🔴 观感修复（Owner：「挤在一起看起来跟个盗版货是的」）：
			   病根是**半透明**三连：遮罩 rgba(.66) + 卡片底 rgba(.94) + hover 底 rgba(.72)
			   ⇒ 底下的会话列表整个浮上来，和面板清单的字**叠在一起**，远看就是几层字糊成一团。
			   修法：遮罩加深 + 背景模糊，卡片与 hover 底改**实色**（不透 ⇒ 不串字）。 */
			".gbtm-scrim{position:fixed;inset:0;background:rgba(2,4,10,.92);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;pointer-events:auto;z-index:40}",
			".gbtm-card{width:94vw;height:88vh;display:flex;flex-direction:column;background:var(--gbtm-bg);color:var(--gbtm-text);border:1px solid var(--gbtm-line);border-radius:var(--gbtm-radius);overflow:hidden;box-shadow:0 24px 80px rgba(0,0,0,.72);font-size:13px}",
			".gbtm-head{display:flex;align-items:center;gap:12px;padding:12px 16px}",
			".gbtm-mark{width:40px;height:40px;border-radius:12px;box-shadow:0 0 0 1px var(--gbtm-line),0 0 22px var(--gbtm-soft)}",
			".gbtm-word{font-weight:800;font-size:19px;letter-spacing:.7px;background:linear-gradient(90deg,var(--gbtm-violet),var(--gbtm-cyan),var(--gbtm-gold));-webkit-background-clip:text;background-clip:text;color:transparent}",
			".gbtm-slogan{display:block;font-size:11px;color:var(--gbtm-dim);margin-top:2px}",
			".gbtm-grow{flex:1}",
			".gbtm-bar{height:3px;background:linear-gradient(90deg,var(--gbtm-violet),var(--gbtm-cyan),var(--gbtm-gold))}",
			".gbtm-body{display:flex;flex:1;min-height:0}",
			/* 清单给足空间：230→272px、行高抬高、说明最多两行带省略号 —— 不再两行字挤成一块 */
			".gbtm-rail{width:272px;flex:none;overflow:auto;border-right:1px solid var(--gbtm-line);padding:10px}",
			".gbtm-row{display:flex;gap:9px;align-items:flex-start;padding:9px 10px;border-radius:10px;cursor:pointer;border:1px solid transparent;min-height:44px}",
			".gbtm-row:hover{background:var(--gbtm-panel)}",
			".gbtm-row.is-on{border-color:var(--gbtm-cyan);background:var(--gbtm-panel)}",
			".gbtm-idx{font-size:11px;color:var(--gbtm-dim);font-variant-numeric:tabular-nums}",
			".gbtm-rname{flex:1;line-height:1.3}",
			".gbtm-note{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:11px;color:var(--gbtm-dim);margin-top:2px;line-height:1.5}",
			".gbtm-badge{font-size:10px;padding:1px 6px;border-radius:999px;border:1px solid var(--gbtm-soft);color:var(--gbtm-cyan);flex:none}",
			".gbtm-badge.is-off{color:var(--gbtm-gold);border-color:var(--gbtm-gold)}",
			".gbtm-stage{flex:1;min-width:0;display:flex;flex-direction:column}",
			".gbtm-tools{display:flex;align-items:center;gap:8px;padding:8px 12px;border-bottom:1px solid var(--gbtm-line)}",
			".gbtm-chip{font-size:11px;padding:2px 8px;border:1px solid var(--gbtm-soft);border-radius:999px;color:var(--gbtm-dim);white-space:nowrap}",
			".gbtm-btn{background:transparent;border:1px solid var(--gbtm-line);color:var(--gbtm-text);border-radius:10px;padding:4px 10px;cursor:pointer;font-size:12px;white-space:nowrap}",
			".gbtm-btn:hover{border-color:var(--gbtm-cyan)}",
			".gbtm-warn{margin:8px 12px 0;padding:8px 10px;border:1px solid var(--gbtm-gold);border-radius:10px;color:var(--gbtm-gold);font-size:12px;line-height:1.5}",
			".gbtm-frame{flex:1;width:100%;border:0;background:var(--gbtm-panel)}",
			".gbtm-foot{padding:6px 14px;border-top:1px solid var(--gbtm-line);color:var(--gbtm-dim);font-size:11px}",
			// 左栏脚部两条动作：**不做成胶囊按钮**（那正是主人说丑的形态）。
			// 只做一个安静的文字动作，悬停才亮 —— 位置与间距由宿主的 footer 槽给。
			".gbtm-side-action{display:block;width:100%;text-align:left;background:transparent;border:0;padding:4px 8px;margin:0;border-radius:8px;color:var(--gbtm-dim);font:inherit;font-size:12px;cursor:pointer}",
			".gbtm-side-action:hover{color:var(--gbtm-cyan);background:rgba(0,229,255,.06)}",
			".gbtm-side-action:focus-visible{outline:1px solid var(--gbtm-cyan);outline-offset:1px}",
		].join("\n");

		const STYLE_ID = "gbt-potato-master-v9-style";

		/* ── 浮层状态（模块内共享：会话头按钮 → 浮层） ──────────────────────── */
		var view = { open: false, id: null };
		var subs = [];
		function emit() {
			for (var i = 0; i < subs.length; i++) { try { subs[i](); } catch (e) { /* 单个订阅坏了不影响其他 */ } }
		}
		function openPanel(id) { view.open = true; view.id = id || view.id; emit(); }
		function closePanel() { view.open = false; emit(); }
		function choosePanel(id) { view.id = id; emit(); }

		/* ── 品牌：左栏品牌行（标 + 名） ─────────────────────────────────────
		   2026-09-23 主人令后改：**标本身可点** ⇒ 打开面板清单。
		   这是"镶嵌"最省的做法 —— 一点界面都没多，入口长在已有的品牌标上。 */
		function GbtSidebarMark(props) {
			const size = props && typeof props.size === "number" ? props.size : 22;
			return React.createElement("img", {
				className: "gbtm-sidebar-mark", src: LOGO, width: size, height: size,
				alt: "GBT小土豆V8", draggable: false,
				title: "面板清单（内嵌打开，不跳转）",
				onClick: function () { openPanel(null); },
			});
		}

		function GbtSidebarName() {
			return React.createElement("span", { className: "gbtm-sidebar-name" }, "GBT小土豆V8");
		}

		/* ── 左栏脚部两条动作：走**装机自己的** `sidebar.footer.action` 槽 ──────
		   为什么不自己画一排：主人判过"组装货"。走宿主槽 ⇒ 位置、间距、字号、
		   悬停态都由宿主给，我们只交一个 label 和一个点击 —— 这才叫嵌进去。 */
		function GbtSideAction(props) {
			const label = (props && props.label) || "";
			return React.createElement("button", {
				className: "gbtm-side-action", type: "button",
				title: (props && props.title) || label,
				onClick: function () { openPanel((props && props.panelId) || null); },
			}, label);
		}

		/* ── 品牌：新会话大标题上的品牌标 ──────────────────────────────────── */
		function GbtHeroMark(props) {
			const want = props && typeof props.size === "number" ? props.size : 48;
			const size = Math.max(want, 56);
			const cls = (props && props.className ? props.className + " " : "") + "gbtm-bigmark";
			return React.createElement("img", {
				className: cls, src: LOGO, width: size, height: size,
				alt: "GBT小土豆V8", draggable: false,
			});
		}

		/* ── 会话头两个入口：**已按主人令去掉**（2026-09-23）────────────────────
		   主人原话：「把这两个去掉，不是这样这几太难看了」（配了截图）。
		   去掉前实测（写在这是为了后来人别又加回来）：
		     · `openPanel()` 在全仓**只被这两个按钮调用**（L148 / L159 两处），
		       所以它们去掉之后，**浮层暂时没有 GUI 入口** —— 面板本体没动，
		       仍可从总索引页 `index.html` 进。要换入口就换到别处，别把丑的加回头部。
		     · 另：`host.js` 里那句自报「挂载：左栏「总面板」…· 会话头右上「GBT小土豆 · 上帝视角」」
		       **与事实不符** —— 全仓没有任何 `sidebar.panellist` 注册，头部那两条现已删除。
		       已同步改掉，免得模型按假声明去找界面。
		   组件 `PanelEntry` / `GodViewEntry` 一并删除（留着就是死代码）。 */

		/* ── 浮层：内嵌舞台（面板本体嵌在 iframe 里，本界面不离开） ──────────── */
		function PanelLayer() {
			const st = React.useState(0);
			const force = st[1];
			const ds = React.useState(null);
			const data = ds[0];
			const setData = ds[1];
			const ns = React.useState(0);
			const nonce = ns[0];
			const setNonce = ns[1];

			React.useEffect(function () {
				const tick = function () { force(function (n) { return n + 1; }); };
				subs.push(tick);
				return function () {
					const i = subs.indexOf(tick);
					if (i >= 0) subs.splice(i, 1);
				};
			}, []);

			React.useEffect(function () {
				let alive = true;
				fetch(BASE, { headers: { accept: "application/json" }, cache: "no-store" })
					.then(function (r) { return r.json(); })
					.then(function (res) { if (alive) setData(res); })
					.catch(function () { if (alive) setData({ ok: false, panels: [] }); });
				return function () { alive = false; };
			}, []);

			React.useEffect(function () {
				if (!view.open) return undefined;
				const onKey = function (ev) { if (ev && ev.key === "Escape") closePanel(); };
				window.addEventListener("keydown", onKey);
				return function () { window.removeEventListener("keydown", onKey); };
			}, [view.open]);

			if (!view.open) return null;

			const panels = (data && data.panels) || [];
			let current = null;
			for (let i = 0; i < panels.length; i++) if (panels[i].id === view.id) current = panels[i];
			if (current === null && panels.length) current = panels[0];

			const rows = panels.map(function (p, i) {
				return React.createElement("div", {
					key: p.id,
					className: "gbtm-row" + (current && p.id === current.id ? " is-on" : ""),
					onClick: function () { choosePanel(p.id); setNonce(0); },
				},
					React.createElement("span", { className: "gbtm-idx" }, (i + 1 < 10 ? "0" : "") + String(i + 1)),
					React.createElement("span", { className: "gbtm-rname" }, p.name, React.createElement("span", { className: "gbtm-note" }, p.note || "")),
					React.createElement("span", { className: "gbtm-badge" + (p.exists ? "" : " is-off") }, p.exists ? "在" : "缺"));
			});

			let stage = null;
			if (current === null) {
				stage = React.createElement("div", { className: "gbtm-stage" },
					React.createElement("div", { className: "gbtm-warn" }, "正在向宿主读取面板目录…"));
			} else {
				const kids = [React.createElement("div", { key: "tools", className: "gbtm-tools" },
					React.createElement("b", null, current.name),
					React.createElement("span", { className: "gbtm-chip" }, current.file),
					React.createElement("span", { className: "gbtm-grow" }),
					React.createElement("button", { className: "gbtm-btn", type: "button", onClick: function () { setNonce(nonce + 1); } }, "重载"),
					React.createElement("button", { className: "gbtm-btn", type: "button", onClick: closePanel }, "关闭"))];
				if (!current.exists) {
					kids.push(React.createElement("div", { key: "miss", className: "gbtm-warn" },
						"文件不在盘上：" + current.file + " —— 面板目录只报实情，不顶替。"));
				} else if (current.needs) {
					kids.push(React.createElement("div", { key: "need", className: "gbtm-warn" }, current.needs));
				}
				if (current.exists) {
					kids.push(React.createElement("iframe", {
						key: current.id + ":" + nonce,
						className: "gbtm-frame",
						title: current.name,
						src: nonce ? current.url + "?r=" + nonce : current.url,
						sandbox: "allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads",
					}));
				}
				stage = React.createElement("div", { className: "gbtm-stage" }, kids);
			}

			return React.createElement("div", {
				className: "gbtm-scrim",
				onClick: function (ev) { if (ev && ev.target === ev.currentTarget) closePanel(); },
			},
				React.createElement("div", { className: "gbtm-card" },
					React.createElement("div", { className: "gbtm-head" },
						React.createElement("img", { className: "gbtm-mark", src: LOGO, width: 40, height: 40, alt: "GBT小土豆V8" }),
						React.createElement("div", null,
							React.createElement("div", { className: "gbtm-word" }, "GBT小土豆 V8 · 面板"),
							React.createElement("span", { className: "gbtm-slogan" },
								data ? ("工作区可视化面板 · 在 " + data.present + " / " + data.total + "（内嵌打开，不跳转）") : "正在读取面板目录…")),
						React.createElement("span", { className: "gbtm-grow" }),
						React.createElement("button", { className: "gbtm-btn", type: "button", onClick: closePanel }, "关闭 Esc")),
					React.createElement("div", { className: "gbtm-bar" }),
					React.createElement("div", { className: "gbtm-body" },
						React.createElement("div", { className: "gbtm-rail" }, rows),
						stage),
					React.createElement("div", { className: "gbtm-foot" }, SIGN)));
		}

		/** 必需服务：UI 插槽注册表 */
		const inject = ["slots"];

		function apply(ctx) {
			const install = function () {
				const el = document.createElement("style");
				el.id = STYLE_ID;
				el.textContent = CSS;
				document.head.appendChild(el);
				return function () { if (el.parentNode) el.parentNode.removeChild(el); };
			};
			if (typeof ctx.effect === "function") {
				if (!document.getElementById(STYLE_ID)) ctx.effect(install, "gbt-potato-master-v9 styles");
			} else if (!document.getElementById(STYLE_ID)) {
				install();
			}

			// ── 入口：**不往会话头贴按钮了**（主人令 2026-09-23：「把这两个去掉…太难看了」
			//    ＋「挨个镶嵌进去设计」）。改成**嵌进左栏既有设计**，一点都不多占：
			//      ① 左栏品牌标（已经在品牌行里）**本身可点** ⇒ 打开面板清单；
			//      ② 左栏脚部（设置那一行旁边）两条动作 ⇒ 「面板」/「上帝视角」，
			//         走的是装机自己的 `sidebar.footer.action` 槽 ⇒ 长相由宿主给，不是我们贴的。
			//    为什么要这么改：原来那两条是**追加到会话头**的独立胶囊（土豆标 + 文字），
			//    和官方那排控件挤在一行 —— 主人截图判"组装货"。嵌进既有位置后，
			//    功能区没少（`openPanel` 照样有人调），但不再多出一排东西。

			// 内嵌浮层：面板就装在这里（该层默认点透，条目自己开指针事件）
			ctx.slots.inject("shell.overlay", function () {
				return ctx.slots.register({ name: "shell.overlay", id: "gbt-panel-layer", order: 40 }, PanelLayer);
			});

			// ── 品牌三格 + **一次可读的自报诊断**（v9）──────────────────────────
			// 病史：v6 / v7 / v8 三代都"以为注册上了"，实测左栏两格始终是官方那条（截图判的）。
			// 插槽检查器也判不了责任：single 槽只报"一条占用"，而本构建里 `registrant` 是
			// **通用标签** —— 实测头部 4 条、浮层那条（确定是我们的 `gbt-panel-layer`）、
			// 品牌那条，**全是 `Ba`** ⇒ 从它分不清是谁填的。
			// ⇒ 只能**自报**：每一步注册都进 try/catch，结果经两条路出去 ——
			//   ① 写进页面标题（截图肉眼可见）；② POST 给宿主的 `/gbt-master/diag`（存档）。
			// 形态说明：v8 用的是官方那套"嵌套 + 生成器"（`inject(mark) → inject(name) → function*(){yield…}`），
			// 本版改成**三格各自独立、普通函数**（这是唯一在动态件上实测**成功占位**的形态）。
			const diag = [];
			function step(name, fn) {
				try {
					const d = fn();
					diag.push(name + ":ok");
					return d;
				} catch (e) {
					diag.push(name + ":ERR " + String((e && e.message) || e).slice(0, 50));
					return null;
				}
			}

			// 品牌：新会话大标题上的品牌标（该位 replaceRisk: none）
			step("hero", function () {
				return ctx.slots.inject("conversation.hero.brand.mark", function () {
					return ctx.slots.register({ name: "conversation.hero.brand.mark" }, GbtHeroMark);
				});
			});

			// 品牌：左栏品牌行两格（本次两格**各自独立**注册，不再嵌套）
			step("sideMark", function () {
				return ctx.slots.inject("sidebar.brand.mark", function () {
					return ctx.slots.register({ name: "sidebar.brand.mark" }, GbtSidebarMark);
				});
			});
			step("sideName", function () {
				return ctx.slots.inject("sidebar.brand.name", function () {
					return ctx.slots.register({ name: "sidebar.brand.name" }, GbtSidebarName);
				});
			});

			// 入口镶嵌①：左栏脚部「面板」（走宿主的 footer 动作槽，不自己贴样式）
			step("footPanels", function () {
				return ctx.slots.inject("sidebar.footer.action", function () {
					return ctx.slots.register({
						name: "sidebar.footer.action", id: "gbt-panels", order: 40, label: "面板",
					}, function () {
						return React.createElement(GbtSideAction, {
							label: "面板", title: "打开面板清单（内嵌打开，不跳转）" });
					});
				});
			});
			// 入口镶嵌②：左栏脚部「上帝视角」（同一浮层、预选 W3）
			step("footGodview", function () {
				return ctx.slots.inject("sidebar.footer.action", function () {
					return ctx.slots.register({
						name: "sidebar.footer.action", id: "gbt-godview", order: 41, label: "上帝视角",
					}, function () {
						return React.createElement(GbtSideAction, {
							label: "上帝视角", panelId: GODVIEW_ID,
							title: "上帝视角 · 六页签实时驾驶舱（内嵌打开，不跳转）" });
					});
				});
			});

			// 诊断上报（两条路，失败都不影响页面）：页面标题 + 宿主 /gbt-master/diag
			try {
				const line = diag.join(" | ");
				try { document.title = "[gbt] " + line.slice(0, 110); } catch (e) { /* 标题改不了就算了 */ }
				fetch("/gbt-master/diag", {
					method: "POST",
					headers: { "content-type": "application/json" },
					body: JSON.stringify({ gen: "gbt-potato-master-v9", diag: diag }),
				}).catch(function () { /* 报不上去也不影响页面 */ });
			} catch (e) { /* 同上 */ }

			// 世代戳：让"自愈注入"能分辨**页面拿的是哪一代包**。
			// 只判断"入口在不在"不够 —— 品牌这种局部缺失时入口是在的，自愈就不会刷，
			// 局部缺陷会一直挂着。戳上世代名，宿主侧拿自己的名字对，不一致才刷。
			try {
				document.documentElement.dataset.gbtGen = "gbt-potato-master-v9";
			} catch (e) { /* 拿不到 documentElement 就算了，自愈退化为"只看入口在不在" */ }
		}

		exports.apply = apply;
		exports.inject = inject;
		return module.exports;
	}
});
