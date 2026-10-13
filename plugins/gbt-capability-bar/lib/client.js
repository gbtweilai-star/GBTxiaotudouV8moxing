/**
 * GBT小土豆V8 · 能力栏 · 浏览器半边（已构建 bundle 形态：window.__ModuleLoader__.load({id, factory})）
 *
 * 口径（主人令 2026-10-08「记得能力栏精细设计一下」＋「使用官方的 APP 来改造」）：
 *   · **只加一格**：左栏脚部走装机自己的 `sidebar.footer.action` 槽（id `gbt-capbar`，order 42 ——
 *     排在 gbt-master 的「面板 / 上帝视角」之后）。**不占品牌位、不动它那两格、不动会话头**。
 *   · **一律内嵌**：本体嵌在 `shell.overlay` 浮层里的 iframe（同源路由），**零开窗**（全文没有开新窗的调用）。
 *   · **加法不许减法**：本文件里没有任何"关掉官方行"的动作；插槽是 list 语义 ⇒ 与 gbt-master 各自独立。
 *   · 🔴 **不写 `data-gbt-gen`**：那个键是 gbt-master 自愈器的判据（页面戳 vs 宿主现报的世代），
 *     本件写它会让对方的自愈器把整页判成"旧世代"而触发刷新 ⇒ 本件只写自己的键 `data-gbt-capbar`。
 *   · 数据侧零代码：页面自己读同源数据件（宿主注入的 `live.js` + 两张既有数据件），本 bundle 只嵌它。
 *
 * 安装（**未执行**，改动点见 docs/能力栏-精细设计.md §六）：
 *   node <dsh bin> plugin --profile web add "file:<工作区>/plugins/gbt-capability-bar"
 *   ~/.dsh/profiles/web/cordis.patch.yml 里加一行 insert（name: gbt-potato-capability-bar-v1）
 *   浏览器 F5 一次（客户端模块随页面引导载荷入册）。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */

window.__ModuleLoader__.load({
	id: "gbt-potato-capability-bar-v1",
	factory: (require) => {
		var module = { exports: {} };
		var exports = module.exports;
		Object.defineProperty(exports, Symbol.toStringTag, { value: "Module" });

		const React = require("react");

		const BASE = "/gbt-capability-bar";
		const PAGE = BASE + "/fs/holo_pet_w3/capability-bar/index.html";
		const LOGO = BASE + "/fs/assets/brand/logo-potato-64.png";
		const SIGN = "开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属";

		/* 令牌与类名都带 gbtcb- 前缀：与 gbt-master 的 gbtm- 互不干扰（两家样式各自作用域化） */
		const CSS = [
			".gbtcb-root{--gbtcb-gold:#F5B041;--gbtcb-cyan:#00E5FF;--gbtcb-violet:#7C4DFF;--gbtcb-bg:#060912;--gbtcb-panel:#131a30;--gbtcb-line:rgba(124,77,255,.34);--gbtcb-soft:rgba(0,229,255,.18);--gbtcb-text:#E8ECF8;--gbtcb-dim:#9AA4C4;--gbtcb-radius:12px}",
			// 左栏脚部那一格：**不做成胶囊按钮**（主人判过"组装货"），只做安静的文字动作，悬停才亮
			".gbtcb-side-action{display:block;width:100%;text-align:left;background:transparent;border:0;padding:4px 8px;margin:0;border-radius:8px;color:var(--gbtcb-dim);font:inherit;font-size:12px;cursor:pointer}",
			".gbtcb-side-action:hover{color:var(--gbtcb-cyan);background:rgba(0,229,255,.06)}",
			".gbtcb-side-action:focus-visible{outline:1px solid var(--gbtcb-cyan);outline-offset:1px}",
			// 浮层：**实色**底（半透明会把底下会话列表透上来、几层字叠成一团 —— gbt-master 踩过，别重犯）
			".gbtcb-scrim{position:fixed;inset:0;background:rgba(2,4,10,.92);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;pointer-events:auto;z-index:41}",
			".gbtcb-card{width:94vw;height:88vh;display:flex;flex-direction:column;background:var(--gbtcb-bg);color:var(--gbtcb-text);border:1px solid var(--gbtcb-line);border-radius:var(--gbtcb-radius);overflow:hidden;box-shadow:0 24px 80px rgba(0,0,0,.72);font-size:13px}",
			".gbtcb-head{display:flex;align-items:center;gap:12px;padding:12px 16px}",
			".gbtcb-mark{width:36px;height:36px;border-radius:10px;box-shadow:0 0 0 1px var(--gbtcb-line),0 0 22px var(--gbtcb-soft)}",
			".gbtcb-word{font-weight:800;font-size:18px;letter-spacing:.7px;background:linear-gradient(90deg,var(--gbtcb-violet),var(--gbtcb-cyan),var(--gbtcb-gold));-webkit-background-clip:text;background-clip:text;color:transparent}",
			".gbtcb-slogan{display:block;font-size:11px;color:var(--gbtcb-dim);margin-top:2px}",
			".gbtcb-grow{flex:1}",
			".gbtcb-bar{height:3px;background:linear-gradient(90deg,var(--gbtcb-violet),var(--gbtcb-cyan),var(--gbtcb-gold))}",
			".gbtcb-btn{background:transparent;border:1px solid var(--gbtcb-line);color:var(--gbtcb-text);border-radius:10px;padding:4px 10px;cursor:pointer;font-size:12px;white-space:nowrap}",
			".gbtcb-btn:hover{border-color:var(--gbtcb-cyan)}",
			".gbtcb-frame{flex:1;width:100%;border:0;background:var(--gbtcb-panel)}",
			".gbtcb-foot{display:flex;gap:12px;align-items:center;justify-content:space-between;padding:6px 14px;border-top:1px solid var(--gbtcb-line);color:var(--gbtcb-dim);font-size:11px;flex-wrap:wrap}",
		].join("\n");

		const STYLE_ID = "gbt-potato-capability-bar-v1-style";

		/* ── 浮层开关（模块内共享：左栏那一格 → 浮层）──────────────────────── */
		var view = { open: false };
		var subs = [];
		function emit() {
			for (var i = 0; i < subs.length; i++) { try { subs[i](); } catch (e) { /* 单个订阅坏了不影响其他 */ } }
		}
		function openBar() { view.open = true; emit(); }
		function closeBar() { view.open = false; emit(); }

		/* ── 左栏脚部那一格（走宿主的 footer 动作槽；长相由宿主给，不自己贴样式）──── */
		function GbtCapBarAction(props) {
			return React.createElement("button", {
				className: "gbtcb-side-action", type: "button",
				title: "能力栏：240 位 × 族 × 三态（内嵌打开，不跳转）",
				onClick: openBar,
			}, (props && props.label) || "能力栏");
		}

		/* ── 浮层：内嵌舞台（iframe 载同源页；本界面不离开、不开新窗）────────────── */
		function CapBarLayer() {
			const st = React.useState(0);
			const force = st[1];
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
				if (!view.open) return undefined;
				const onKey = function (ev) { if (ev && ev.key === "Escape") closeBar(); };
				window.addEventListener("keydown", onKey);
				return function () { window.removeEventListener("keydown", onKey); };
			}, [view.open]);

			if (!view.open) return null;

			return React.createElement("div", {
				className: "gbtcb-scrim",
				onClick: function (ev) { if (ev && ev.target === ev.currentTarget) closeBar(); },
			},
				React.createElement("div", { className: "gbtcb-card" },
					React.createElement("div", { className: "gbtcb-head" },
						React.createElement("img", { className: "gbtcb-mark", src: LOGO, width: 36, height: 36, alt: "GBT小土豆V8" }),
						React.createElement("div", null,
							React.createElement("div", { className: "gbtcb-word" }, "GBT小土豆 V8 · 能力栏"),
							React.createElement("span", { className: "gbtcb-slogan" },
								"族 × 三态 · 一屏可读 · 每个数字带来源与时刻（内嵌打开，不跳转；宿主现读账本尾部窗口）")),
						React.createElement("span", { className: "gbtcb-grow" }),
						React.createElement("button", { className: "gbtcb-btn", type: "button",
							onClick: function () { setNonce(nonce + 1); } }, "重载"),
						React.createElement("button", { className: "gbtcb-btn", type: "button", onClick: closeBar }, "关闭 Esc")),
					React.createElement("div", { className: "gbtcb-bar" }),
					React.createElement("iframe", {
						key: "capbar:" + nonce,
						className: "gbtcb-frame",
						title: "GBT小土豆V8 · 能力栏",
						src: nonce ? PAGE + "?r=" + nonce : PAGE,
						sandbox: "allow-scripts allow-same-origin allow-forms allow-modals",
					}),
					React.createElement("div", { className: "gbtcb-foot" },
						React.createElement("span", null, SIGN),
						React.createElement("span", null, "数据：state/cap-bindings.json · state/capability-audit.json · gbt_allinone/store/audit.jsonl（只读）"))));
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
				if (!document.getElementById(STYLE_ID)) ctx.effect(install, "gbt-capability-bar styles");
			} else if (!document.getElementById(STYLE_ID)) {
				install();
			}

			// 每一步注册都进 try/catch，结果两条路出去：① 页面标题 ② POST 给宿主的自报路由
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

			// 入口（**只此一格**）：左栏脚部「能力栏」——与 gbt-master 的「面板/上帝视角」同一排、排在它们后面
			step("footBar", function () {
				return ctx.slots.inject("sidebar.footer.action", function () {
					return ctx.slots.register({
						name: "sidebar.footer.action", id: "gbt-capbar", order: 42, label: "能力栏",
					}, function () {
						return React.createElement(GbtCapBarAction, { label: "能力栏" });
					});
				});
			});

			// 浮层一格：能力栏本体嵌在这里（iframe 同源路由，零开窗）
			step("overlay", function () {
				return ctx.slots.inject("shell.overlay", function () {
					return ctx.slots.register({ name: "shell.overlay", id: "gbt-capbar-layer", order: 41 }, CapBarLayer);
				});
			});

			// 自报（两条路，失败都不影响页面）：页面标题 + 宿主 /gbt-capability-bar/diag
			try {
				const line = diag.join(" | ");
				try { document.title = "[gbt-capbar] " + line.slice(0, 110); } catch (e) { /* 改不了就算了 */ }
				fetch(BASE + "/diag", {
					method: "POST",
					headers: { "content-type": "application/json" },
					body: JSON.stringify({ gen: "gbt-potato-capability-bar-v1", diag: diag }),
				}).catch(function () { /* 报不上去也不影响页面 */ });
			} catch (e) { /* 同上 */ }

			// 自己的世代戳（**绝不写 data-gbt-gen** —— 那是 gbt-master 自愈器的判据，见文件头）
			try {
				document.documentElement.dataset.gbtCapbar = "gbt-potato-capability-bar-v1";
			} catch (e) { /* 拿不到就算了 */ }
		}

		exports.apply = apply;
		exports.inject = inject;
		return module.exports;
	}
});
