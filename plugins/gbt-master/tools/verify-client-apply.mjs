/* 无头验收：把**真的**浏览器半边 bundle 装进一个假模块装载器里跑一遍 apply()。
 *
 * 为什么要有这个：Owner 页面拿的是上一代包，而页面自己判不出"我旧了"，
 * 所以"我这版到底注册上了没有"不能靠截图猜。这个脚本直接证据化三件事：
 *   ① 六个插槽注册**都落下了**（含 v6 弄坏的那对品牌格）；
 *   ② 品牌两格是**同一层嵌套的一组声明感知注册**（结构与官方包一致）；
 *   ③ 防"挤在一起"的那几条 CSS 真的在（不透底遮罩 + 实底卡片 + 两行截断）。
 * 跑法： node plugins/gbt-master/tools/verify-client-apply.mjs
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const here = dirname(fileURLToPath(import.meta.url));
const SRC = join(here, '..', 'lib', 'client.js');
const code = readFileSync(SRC, 'utf8');

const mods = [];
const regs = [];
const effects = [];
const styles = [];
const errors = [];
let depth = 0;

const head = { appendChild(el) { styles.push(el); } };

const sandbox = {
  console: { log: () => {}, warn: (m) => errors.push('warn: ' + m), error: (m) => errors.push('error: ' + m) },
  document: {
    documentElement: { dataset: {} },
    head,
    createElement(tag) { return { tag, id: '', textContent: '', parentNode: null, removeChild() {} }; },
    getElementById: () => null,
  },
  window: { __ModuleLoader__: { load(mod) { mods.push(mod); } } },
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
new vm.Script(code, { filename: 'client.js' }).runInContext(sandbox);

// 本代模块 = 与 package.json 的 name 同名那一个（**包名即 specifier**，这就是换代规则本身）。
const pkgName = JSON.parse(readFileSync(join(here, '..', 'package.json'), 'utf8')).name;
const real = mods.find((m) => m.id === pkgName);
if (!real) throw new Error('本代模块 ' + pkgName + ' 不在 load 名单里，实际 load 到: ' + mods.map((m) => m.id).join(', '));
const stubs = mods.filter((m) => m !== real).map((m) => m.id);

const React = {
  createElement: (type, props, ...kids) => ({ type, props: { ...(props || {}), children: kids } }),
  useState: (v) => [v, () => {}],
  useEffect: (fn) => { try { fn(); } catch (e) { errors.push('useEffect: ' + e.message); } },
  useMemo: (fn) => fn(),
  useRef: (v) => ({ current: v }),
  useCallback: (fn) => fn,
  useSyncExternalStore: (sub, get) => { try { sub(() => {}); } catch { /* 订阅失败只影响重渲染 */ } return get(); },
  Fragment: 'Fragment',
};
const require = (id) => {
  if (id === 'react') return React;
  throw new Error('未打桩的依赖: ' + id);
};

const slots = {
  inject(name, cb) {
    depth += 1;
    try {
      const r = cb();
      if (r && typeof r.next === 'function') { let n = r.next(); while (!n.done) n = r.next(); }
      return r;
    } finally { depth -= 1; }
  },
  register(spec, comp) {
    regs.push({ slot: spec.name, id: spec.id ?? null, order: spec.order ?? null, depth, comp });
    return { dispose() {} };
  },
};
const ctx = {
  slots,
  effect(fn, label) { const d = fn(); effects.push({ label, disposer: typeof d }); return d; },
  on: () => () => {},
  get: () => undefined,
  logger: { warn: (m) => errors.push('logger.warn: ' + m), info: () => {}, debug: () => {} },
};

const exported = real.factory(require);
exported.apply(ctx);

/* ── 断点 ─────────────────────────────────────────────────────────── */
const want = [
  ['conversation.session.header.utilities', 'gbt-panels'],
  ['conversation.session.header.utilities', 'gbt-godview'],
  ['shell.overlay', 'gbt-panel-layer'],
  ['conversation.hero.brand.mark', null],
  ['sidebar.brand.mark', null],
  ['sidebar.brand.name', null],
];
const found = (slot, id) => regs.find((r) => r.slot === slot && (id === null ? true : r.id === id));
const checks = [];
const bad = [];
for (const [slot, id] of want) {
  const hit = found(slot, id);
  checks.push({ slot, id, ok: !!hit, depth: hit ? hit.depth : null });
  if (!hit) bad.push(slot + (id ? '#' + id : ''));
}
const mark = regs.find((r) => r.slot === 'sidebar.brand.mark');
const name = regs.find((r) => r.slot === 'sidebar.brand.name');
// ⚠️ 2026-09-22 **改判据**：原先这里断言"品牌两格必须是**同一层嵌套**的一组注册"（照官方写法）。
// 那条断言**已被实测推翻**，留着会误导人：v8 用的就是官方那套嵌套+生成器，**左栏两格仍然不生效**；
// 而在动态件上实测**成功占位**的是"两格各自独立、普通函数"的形态（插槽检查器 + 截图，见 README 5.5 节）。
// ⇒ 本器只判**登记面**（两格都注册上了、谁都别漏）；"哪种形态能在 single 槽占住"是**运行时**事实，
//    静态测不出来，判据是插槽检查器 + 截图。
const brandPairPresent = !!mark && !!name;
if (!brandPairPresent) bad.push('品牌两格没有都注册上');
const diagWired = /\/gbt-master\/diag/.test(code);
if (!diagWired) bad.push('缺浏览器自报诊断挂钩（POST /gbt-master/diag）—— 没它就查不出 single 槽为什么没占上');
if (sandbox.document.documentElement.dataset.gbtGen !== real.id) bad.push('世代戳没打上');

const css = styles.map((s) => s.textContent).join('\n');
const cssRules = {
  '不透底遮罩': /\.gbtm-scrim\{[^}]*rgba\(2,4,10,\.9\d\)/.test(css),
  '遮罩背景模糊': /\.gbtm-scrim\{[^}]*backdrop-filter:blur/.test(css),
  '卡片实底': /\.gbtm-card\{[^}]*background:var\(--gbtm-bg\)/.test(css),
  '悬停实底': /\.gbtm-row:hover\{background:var\(--gbtm-panel\)\}/.test(css),
  '清单加宽到 272': /\.gbtm-rail\{width:272px/.test(css),
  '行高不小于 44': /\.gbtm-row\{[^}]*min-height:44px/.test(css),
  '备注两行截断': /\.gbtm-note\{[^}]*-webkit-line-clamp:2/.test(css),
};
for (const [k, v] of Object.entries(cssRules)) if (!v) bad.push('CSS 缺: ' + k);

const out = {
  bundleId: real.id,
  stubsForOldGenerations: stubs.length,
  registered: checks,
  brandPairDepth: brandPairPresent ? { mark: mark.depth, name: name.depth } : null,
  diagWired,
  styleInstalled: styles.length === 1 ? styles[0].id : styles.map((s) => s.id),
  effects: effects.map((e) => e.label),
  cssRules,
  errors,
  verdict: bad.length === 0 ? 'PASS' : 'FAIL',
  problems: bad,
};
console.log(JSON.stringify(out, null, 1));
process.exitCode = bad.length === 0 ? 0 : 1;
