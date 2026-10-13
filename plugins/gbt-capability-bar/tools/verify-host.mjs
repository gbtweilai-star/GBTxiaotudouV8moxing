/**
 * GBT小土豆V8 · 能力栏 · 宿主半边**进程外真跑**验收（照 plugins/gbt-master/tools/verify-host.mjs 的口径）
 *
 * 为什么必须进程外跑一遍：宿主半边是**进程启动时装载**的代码，而正式挂载点（~/.dsh）不许本件去碰。
 * ⇒ 用假 ctx（假 fs / 假 webServer / 假 res）把 apply() 真跑起来，逐条路由打真请求，
 *   白名单**含负对照**（越界必须 404；能放行的必须 200 —— 两面都要有，否则"只报绿"的闸等于没有）。
 *
 * 用法：node plugins/gbt-capability-bar/tools/verify-host.mjs [工作区根]
 * 退出码：0 全过 / 1 有 FAIL
 */
import { readFileSync, existsSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = (process.argv[2] || resolve(HERE, '..', '..', '..')).replace(/\\/g, '/')
const HOST = resolve(HERE, '..', 'lib', 'host.js')

const rows = []
function add(name, ok, detail) { rows.push({ name, ok: !!ok, detail: String(detail) }) }

// ── 假 ctx：只提供 host.js 声明要用的三个面（fs / webServer / effect），不多不少 ──
const routes = []
const fakeFs = {
  async resolve(p) { return p },
  async readBytes(p, _opt, max) {
    const buf = readFileSync(p)
    if (max && buf.length > max) throw new Error('over max')
    return new Uint8Array(buf)
  },
}
const ctx = {
  config: { workspace: ROOT },
  fs: fakeFs,
  webServer: {
    register(def) { routes.push(def); return () => {} },
    tapIndex() { throw new Error('能力栏**不该**注入首页（不许和 gbt-master 的自愈器抢路）') },
  },
  effect(fn) { return fn() },
  logger: { info() {}, warn() {} },
}

const mod = await import('file://' + HOST.replace(/\\/g, '/'))
add('C0 host.js 导出 apply/inject', typeof mod.apply === 'function' && Array.isArray(mod.inject),
  'inject=' + JSON.stringify(mod.inject))

function runApply() { mod.apply(ctx, { workspace: ROOT }) }
let applyErr = null
try { runApply() } catch (e) { applyErr = e }
add('C1 apply() 真跑不抛', applyErr === null, applyErr ? String(applyErr.message) : 'ok · 注册路由 ' + routes.length + ' 条')

// ── 假请求/假响应 ────────────────────────────────────────────────────────────
function mkRes() {
  return {
    code: null, headers: null, body: '', _events: {},
    writeHead(code, headers) { this.code = code; this.headers = headers || {} },
    end(b) { this.body = b === undefined ? '' : String(b) },
    on(ev, fn) { (this._events[ev] = this._events[ev] || []).push(fn) },
    destroy() {},
    get writableEnded() { return this.body !== '' },
    get headersSent() { return this.code !== null },
  }
}
function mkReq(method, url, bodyText) {
  const listeners = {}
  const req = {
    method, url, headers: {},
    on(ev, fn) { (listeners[ev] = listeners[ev] || []).push(fn) },
    pipe() {},
  }
  process.nextTick(() => {
    if (bodyText !== undefined) (listeners.data || []).forEach((f) => f(Buffer.from(bodyText)))
    ;(listeners.end || []).forEach((f) => f())
  })
  return req
}
function pick(pathname) {
  // 精确优先（与 DSH 行为一致：exact 先注册，命中即停）
  const exact = routes.filter((r) => r.kind === 'exact' && r.path === pathname)
  if (exact.length) return exact[exact.length - 1]
  const prefix = routes.filter((r) => r.kind === 'prefix' &&
    (pathname === r.path || pathname.indexOf(r.path + '/') === 0))
  return prefix.length ? prefix[prefix.length - 1] : null
}
async function hit(pathname, method = 'GET', body) {
  const r = pick(pathname)
  if (!r) return { code: null, body: '', note: '没有路由接这条（=DSH 兜底 404）' }
  const res = mkRes()
  await r.handler(mkReq(method, pathname, body), res)
  await new Promise((r2) => setTimeout(r2, 15))   // POST 体的 data/end 在 nextTick ⇒ 等它落账再快照
  return { code: res.code, body: res.body, headers: res.headers }
}

// ── ① 目录 JSON ──
{
  const r = await hit('/gbt-capability-bar')
  let j = null
  try { j = JSON.parse(r.body) } catch (e) { /* 下面按 null 判 */ }
  add('C2 GET /gbt-capability-bar 回 JSON 且带 plugin/version/counts',
    r.code === 200 && j && j.plugin === 'gbt-potato-capability-bar-v1' && j.counts && j.counts.caps === 240,
    'code=' + r.code + ' plugin=' + (j && j.plugin) + ' caps=' + (j && j.counts && j.counts.caps))
  add('C3 目录里报的页路径 = 白名单内的那一条（不是任意路径）',
    !!(j && j.page === '/gbt-capability-bar/fs/holo_pet_w3/capability-bar/index.html'),
    'page=' + (j && j.page))
}

// ── ② 现读数据件 ──
{
  const r = await hit('/gbt-capability-bar/live.js')
  const m = /window\.GBT_CAPBAR_LIVE\s*=\s*(\{[\s\S]*\});\s*$/.exec(r.body)
  let p = null
  try { p = m ? JSON.parse(m[1]) : null } catch (e) { /* null */ }
  const ev = p && p.evidence
  const capNames = new Set(JSON.parse(readFileSync(ROOT + '/state/cap-bindings.json', 'utf8')).caps.map((c) => c.name))
  const ghost = ev && ev.map ? Object.keys(ev.map).filter((k) => !capNames.has(k)) : ['（无 map）']
  add('C4 GET /live.js 回经典脚本且证据件结构齐（window_hours/read_bytes/capped/map）',
    r.code === 200 && p && ev && ev.window_hours === 24 && typeof ev.read_bytes === 'number'
      && typeof ev.capped === 'boolean' && ev.map && Object.keys(ev.map).length > 0,
    'code=' + r.code + ' 窗口 ' + (ev && ev.window_hours) + 'h · 回读 ' + (ev && (ev.read_bytes / 1048576).toFixed(1)) + 'MB · 命中 ' + (ev && ev.map ? Object.keys(ev.map).length : '—') + ' 位')
  add('C5 证据 map 的键全在册（不拿不在册 kind 冒充）', ghost.length === 0, '不在册 ' + JSON.stringify(ghost.slice(0, 5)))
  add('C6 live 件带能量运行时与记录本读数（或如实报错，不许编）',
    p && p.energy_runtime && p.logbook && (p.energy_runtime.ok === true || p.energy_runtime.error) &&
      (p.logbook.ok === true || p.logbook.error),
    'runtime=' + (p && p.energy_runtime && (p.energy_runtime.ok ? 'ok' : 'err')) + ' logbook=' + (p && p.logbook && (p.logbook.ok ? 'ok' : 'err')))
}

// ── ③ 页面包装 ──
{
  const r = await hit('/gbt-capability-bar/fs/holo_pet_w3/capability-bar/index.html')
  const raw = readFileSync(ROOT + '/holo_pet_w3/capability-bar/index.html', 'utf8')
  const hasTag = r.body.indexOf('<script src="/gbt-capability-bar/live.js"></script>') >= 0
  add('C7 页面包装：注入 live.js 且比源文件更长（同源 HTTP 下一份源文件零分叉）',
    r.code === 200 && hasTag && r.body.length > raw.length,
    'code=' + r.code + ' 注入=' + hasTag + ' 源 ' + raw.length + ' → 出 ' + r.body.length)
}

// ── ④ 只读白名单：能放行的 + 越界必须拒（负对照成对出现） ──────────────────
{
  const okIn = [
    '/gbt-capability-bar/fs/holo_pet_w3/capability-bar/run-evidence.js',
    '/gbt-capability-bar/fs/holo_pet_w3/energy/energy-data.js',
    '/gbt-capability-bar/fs/holo_pet_w3/capabilities/index.html',
    '/gbt-capability-bar/fs/assets/brand/logo-potato-64.png',
  ]
  const must404 = [
    '/gbt-capability-bar/fs/state/cap-bindings.json',       // 真源在名单外
    '/gbt-capability-bar/fs/memory/2026-09-22-品牌与Logo不丢.md',
    '/gbt-capability-bar/fs/gbt_allinone/store/audit.jsonl',
    '/gbt-capability-bar/fs/plugins/gbt-master/lib/host.js',
    '/gbt-capability-bar/fs/holo_pet_w3/energy/../energy-data.js',
    '/gbt-capability-bar/fs/holo_pet_w3/capability-bar/%2e%2e/%2e%2e/state/cap-bindings.json',
    '/gbt-capability-bar/fs/holo_pet_w3/capability-bar/../../../../Windows/win.ini',
    '/gbt-capability-bar/fs/.env',
    '/gbt-capability-bar/fs/holo_pet_w3/energy/energy-data.txt',
  ]
  const okGot = []
  for (const p of okIn) { const r = await hit(p); okGot.push(r.code) }
  const badGot = []
  for (const p of must404) { const r = await hit(p); badGot.push(r.code) }
  add('C8 白名单放行面（4 条在册路径全 200）', okGot.every((c) => c === 200), JSON.stringify(okGot))
  add('C9 **负对照**：越界 9 条（含编码穿越/上级目录/内部树/非白名单扩展名）必须全 404',
    badGot.every((c) => c === 404), JSON.stringify(badGot))
  add('C10 放行与拒绝两面结果不同（闸有判别力，不是只会报绿）',
    okGot.every((c) => c === 200) && badGot.every((c) => c === 404), '放行 ' + JSON.stringify(okGot) + ' / 拒绝 ' + JSON.stringify(badGot))
}

// ── ⑤ 写盘红线：host.js 里不许出现写原语 / 不许碰 ~/.dsh ─────────────────────
// 🔴 对**代码**断言、不对**文本**断言（本仓的教训：注释里提到这些词不算违规）⇒ 先剥注释。
function stripJsComments(src) {
  return src.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/[^\n]*/g, '$1 ')
}
{
  const src = stripJsComments(readFileSync(HOST, 'utf8'))
  const bad = []
  if (/writeFile|appendFile|mkdir|createWriteStream|rmSync|unlink/.test(src)) bad.push('写盘原语')
  if (/\.dsh[\\/]/.test(src) || /profiles[\\/]web/.test(src)) bad.push('~/.dsh 路径')
  add('C11 host.js 无写盘原语、无 ~/.dsh 路径（只读纪律 · 剥注释后判）', bad.length === 0, bad.join('、') || '无')
}

// ── ⑥ 自报诊断路由 ──
{
  const r1 = await hit('/gbt-capability-bar/diag', 'POST', JSON.stringify({ gen: 'gbt-potato-capability-bar-v1', diag: ['footBar:ok', 'overlay:ok'] }))
  await new Promise((r) => setTimeout(r, 30))          // POST 体的 data/end 在 nextTick ⇒ 等它落账再读回
  const r2 = await hit('/gbt-capability-bar')
  let j = null
  try { j = JSON.parse(r2.body) } catch (e) { /* null */ }
  add('C12 POST /diag 收自报 → GET 目录能读回 clientDiag',
    r1.code === 200 && j && j.clientDiag && j.clientDiag.diag.length === 2,
    'diag=' + JSON.stringify(j && j.clientDiag && j.clientDiag.diag))
}

// ── 汇总 ──
const fails = rows.filter((r) => !r.ok)
for (const r of rows) console.log((r.ok ? 'PASS ' : 'FAIL ') + r.name + ' — ' + r.detail)
console.log('—'.repeat(80))
console.log('宿主进程外真跑：PASS ' + (rows.length - fails.length) + ' · FAIL ' + fails.length)
process.exit(fails.length ? 1 : 0)
