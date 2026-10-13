/**
 * GBT小土豆V8 · 能力栏 · 浏览器半边**无头验收**（把真 bundle 装进假装载器跑 apply()）
 * 照 plugins/gbt-master/tools/verify-client-apply.mjs 的口径，面更小：
 *   · 6 个断言：两个插槽注册上（id/order 对）· 浮层真渲染（iframe 指向白名单页）· 零开窗原语 ·
 *     **不写 data-gbt-gen**（不许踩 gbt-master 的自愈判据）· 自报挂钩在 · 自己的键在
 *   · 带**负对照**：把插槽名改坏 / 塞一个开窗调用 ⇒ 判据必须报红（不能红的闸不算闸）
 *
 * 用法：node plugins/gbt-capability-bar/tools/verify-client-apply.mjs
 * 退出码：0 全过 / 1 有 FAIL
 */
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '..', '..', '..')
const BUNDLE = resolve(HERE, '..', 'lib', 'client.js')
const SRC = readFileSync(BUNDLE, 'utf8')

// ── 假环境：window / document / react（只到 bundle 用得到的那几样）──────────────
function makeEnv() {
  const regs = []
  const styleEls = []
  const posts = []
  const datasets = {}
  const loaded = {}
  const listeners = {}
  const doc = {
    title: '',
    head: { appendChild(el) { styleEls.push(el) } },
    documentElement: { dataset: datasets },
    createElement(tag) {
      return { tagName: tag, id: '', className: '', textContent: '', parentNode: null }
    },
    getElementById(id) { return styleEls.find((e) => e.id === id) || null },
    addEventListener() {}, removeEventListener() {},
  }
  const win = {
    __ModuleLoader__: { load(def) { loaded[def.id] = def } },
    document: doc,
    addEventListener(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn) },
    removeEventListener() {},
    fetch(url, opt) { posts.push({ url, opt }); return Promise.resolve({ ok: true }) },
  }
  const React = {
    createElement(type, props, ...children) { return { type, props: props || {}, children } },
    useState(init) { return [init, function () {}] },
    useEffect(fn) { try { fn() } catch (e) { /* 无副作用执行，报错就跳过 */ } return undefined },
  }
  return { regs, styleEls, posts, datasets, loaded, win, React, doc, listeners }
}

function runBundle(env, code) {
  // 把 bundle 在假 window 下跑一遍：它只依赖 window.__ModuleLoader__ 与 fetch
  const fn = new Function('window', 'document', 'fetch', 'Promise', code)
  fn(env.win, env.doc, env.win.fetch, Promise)
  const def = env.loaded['gbt-potato-capability-bar-v1']
  if (!def) throw new Error('bundle 没有注册 id=gbt-potato-capability-bar-v1')
  const mod = def.factory(function (name) {
    if (name === 'react') return env.React
    throw new Error('bundle 只许 require("react")，实际要了：' + name)
  })
  return mod
}

const rows = []
function add(name, ok, detail) { rows.push({ name, ok: !!ok, detail: String(detail) }) }

// ── 正跑：真 bundle + 假 ctx ────────────────────────────────────────────────
const env = makeEnv()
const mod = runBundle(env, SRC)
const ctx = {
  effect(fn) { return fn() },
  slots: {
    inject(slotName, fn) { return fn() },
    register(def, comp) { env.regs.push({ def, comp }); return function () {} },
  },
}
let applyErr = null
try { mod.apply(ctx) } catch (e) { applyErr = e }
add('A1 apply() 真跑不抛', applyErr === null, applyErr ? String(applyErr.message) : 'ok')
add('A2 inject 声明 = ["slots"]（不占别的服务）', JSON.stringify(mod.inject) === '["slots"]', JSON.stringify(mod.inject))

const foot = env.regs.find((r) => r.def && r.def.name === 'sidebar.footer.action')
const over = env.regs.find((r) => r.def && r.def.name === 'shell.overlay')
add('A3 左栏脚部一格注册上（id gbt-capbar · order 42 · label 能力栏）',
  !!foot && foot.def.id === 'gbt-capbar' && foot.def.order === 42 && foot.def.label === '能力栏',
  foot ? JSON.stringify(foot.def) : '未注册')
add('A4 浮层一格注册上（id gbt-capbar-layer · order 41）',
  !!over && over.def.id === 'gbt-capbar-layer' && over.def.order === 41,
  over ? JSON.stringify(over.def) : '未注册')

// 真渲染：先点那一格，再让浮层组件出一次渲染结果。
// 🔴 组件的 onClick 在**组件函数体内**创建 ⇒ 光调工厂拿不到，必须把元素再渲染一层（假 react 只需一次调用）。
let layerEl = null, renderErr = null
try {
  const btnEl = foot.comp({})
  const rendered = (typeof btnEl.type === 'function') ? btnEl.type(btnEl.props) : btnEl
  if (rendered && rendered.props && typeof rendered.props.onClick === 'function') rendered.props.onClick()
  layerEl = over.comp({})
} catch (e) { renderErr = e }
function findIframe(el) {
  if (!el || typeof el !== 'object') return null
  if (el.type === 'iframe') return el
  const kids = [].concat(el.children || [])
  for (const k of kids) { const r = findIframe(k); if (r) return r }
  for (const k of Object.keys(el.props || {})) {
    const v = el.props[k]
    if (v && typeof v === 'object' && v.type) { const r = findIframe(v); if (r) return r }
  }
  return null
}
const iframe = findIframe(layerEl)
const src = iframe ? iframe.props.src : ''
add('A5 浮层真渲染出 iframe（同源白名单页；零开窗）',
  renderErr === null && !!iframe && src.indexOf('/gbt-capability-bar/fs/holo_pet_w3/capability-bar/index.html') === 0,
  renderErr ? String(renderErr.message) : ('src=' + src))

// ── 静面红线（对代码断言，先剥注释）─────────────────────────────────────────
function stripJsComments(s) {
  return s.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/[^\n]*/g, '$1 ')
}
const code = stripJsComments(SRC)
add('A6 零开窗：代码里没有 window.open / window.location 跳转',
  !/window\.open\b/.test(code) && !/window\.location\s*=/.test(code) && !/location\.href\s*=/.test(code),
  'open=' + /window\.open\b/.test(code))
add('A7 **不写 data-gbt-gen**（那是 gbt-master 自愈判据，写它会引发整页误刷）· 只写自己的 data-gbt-capbar',
  !/dataset\.gbtGen/.test(code) && /dataset\.gbtCapbar/.test(code),
  'gbtGen=' + /dataset\.gbtGen/.test(code) + ' capbar=' + /dataset\.gbtCapbar/.test(code))
add('A8 自报挂钩在：POST /gbt-capability-bar/diag + 页面标题',
  /\/diag/.test(code) && /document\.title/.test(code) && env.posts.length > 0,
  'POST 次数=' + env.posts.length + ' url=' + ((env.posts[0] || {}).url || '—'))
add('A9 样式作用域化：类名一律 gbtcb- 前缀（不与 gbt-master 的 gbtm- 混）',
  /gbtcb-/.test(code) && !/gbtm-/.test(code), 'gbtcb=' + /gbtcb-/.test(code) + ' 混入 gbtm=' + /gbtm-/.test(code))
add('A10 加法不许减法：代码里没有 disable/摘除官方行的动作',
  !/disable/.test(code), 'disable=' + /disable/.test(code))

// ── 负对照：喂坏 ⇒ 必须有判据报红（正面判据对喂坏副本也要能红） ────────────────
function runBroken(codeText, mutate) {
  const e2 = makeEnv()
  let m2 = null
  try { m2 = runBundle(e2, mutate(codeText)) } catch (err) { return { thrown: err, regs: e2.regs, env: e2 } }
  const c2 = {
    effect(fn) { return fn() },
    slots: { inject(s, fn) { return fn() }, register(def, comp) { e2.regs.push({ def, comp }); return function () {} } },
  }
  let err2 = null
  try { m2.apply(c2) } catch (e) { err2 = e }
  return { thrown: err2, regs: e2.regs, env: e2, mod: m2 }
}
{
  const b1 = runBroken(SRC, (s) => s.split('sidebar.footer.action').join('sidebar.footer.somewhere'))
  const foot2 = b1.regs.find((r) => r.def && r.def.name === 'sidebar.footer.action')
  add('N1 负对照：插槽名改坏（两处一起改）⇒ A3 必须红', !foot2,
    '改坏后注册到的槽：' + JSON.stringify(b1.regs.map((r) => r.def && r.def.name)))
}
{
  const b2 = runBroken(SRC, (s) => s.replace('onClick: openBar,', 'onClick: function(){ window.open("https://example.com"); },'))
  const c2 = stripJsComments(b2.env ? SRC.replace('onClick: openBar,', 'onClick: function(){ window.open("https://example.com"); },') : SRC)
  add('N2 负对照：塞一个开窗调用 ⇒ A6 必须红', /window\.open\b/.test(c2), '命中 window.open=' + /window\.open\b/.test(c2))
}
{
  const broken = SRC.replace('document.documentElement.dataset.gbtCapbar', 'document.documentElement.dataset.gbtGen')
  const c3 = stripJsComments(broken)
  add('N3 负对照：把它写成 data-gbt-gen ⇒ A7 必须红', /dataset\.gbtGen/.test(c3), '命中 dataset.gbtGen=' + /dataset\.gbtGen/.test(c3))
}

const fails = rows.filter((r) => !r.ok)
for (const r of rows) console.log((r.ok ? 'PASS ' : 'FAIL ') + r.name + ' — ' + r.detail)
console.log('—'.repeat(80))
console.log('浏览器半边无头验收：PASS ' + (rows.length - fails.length) + ' · FAIL ' + fails.length)
process.exit(fails.length ? 1 : 0)
