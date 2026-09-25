/**
 * **目录路由延迟门**：`/gbt-master` 的 `catalog()` 不许 N+1 顺序等待。
 *
 * 为什么要有它（2026-09-22 现读实锤）：
 *   `/gbt-master` 只有 4.8 KB，而实测**每次要 8–10 秒**（连测 6 次：10.15 / 10.07 / 9.02 / 8.12 / 8.24 / 8.55 s）。
 *   根因在宿主半边：`catalog()` 对 12 个面板**逐个 `await statOf()`**，再加一次 `fs.listDir(render/)`
 *   —— **13 次顺序 await**，每次都要过 `fs` 服务一个来回 ⇒ 累加成 8–10 秒。
 *   后果不止"慢"：总索引页的台账要等它、能力球的现读对齐要等它，而且
 *   **几支验收器的前置取数会偶发超时**（本轮 `check-panel-syntax --all` 与 `verify-index-panel` 都撞过）。
 *
 * 判据：把 `fs` 服务**打桩成每次调用固定延迟 LAT_MS**，跑一次真实的路由处理器，量总耗时：
 *   · 顺序 N+1 ⇒ 约 13 × LAT_MS
 *   · 并行     ⇒ 约 1 × LAT_MS
 *   断言 `elapsed < 4 × LAT_MS`（留足抖动余量，但远离 13 × LAT_MS）。
 *
 * 用法：node plugins/gbt-master/tools/verify-catalog-latency.mjs [host.js 路径]
 *       默认测**工作区源稿**；也可以指到装机副本，做"改前/改后"对照。
 * 退出码：0 = 已是并行；1 = 仍是顺序（超阈）；2 = 跑不起来。
 */
import { statSync, readdirSync, existsSync } from 'node:fs'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const WS = resolve(HERE, '..', '..', '..')
const TARGET = process.argv[2] ? resolve(process.argv[2]) : join(WS, 'plugins', 'gbt-master', 'lib', 'host.js')
const LAT_MS = 600
const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

const routes = []
const contexts = []
let fsCalls = 0
function makeCtx() {
  return {
    logger: { info() {}, warn() {}, error() {} },
    effect(fn) { try { const d = fn(); return typeof d === 'function' ? d : () => {} } catch { return () => {} } },
    get(name) {
      if (name === 'timer') return undefined
      return undefined
    },
    fs: {
      async resolve(p) { fsCalls++; await sleep(LAT_MS); return { targetKey: String(p).replace(/\\/g, '/'), displayPath: String(p) } },
      async stat(t) {
        fsCalls++; await sleep(LAT_MS)
        try {
          const s = statSync(t.targetKey)
          return { type: s.isDirectory() ? 'directory' : (s.isFile() ? 'file' : 'other'), size: s.size }
        } catch { return undefined }
      },
      async listDir(t) {
        fsCalls++; await sleep(LAT_MS)
        try { return readdirSync(t.targetKey).map((n) => ({ name: n, type: 'file' })) } catch { return [] }
      },
      async readText() { fsCalls++; await sleep(LAT_MS); return '' },
    },
    webServer: {
      register(route) { routes.push(route); return () => {} },
      tapIndex() { return () => {} },
    },
    systemPrompt: { context(c) { contexts.push(c); return () => {} } },
  }
}

if (!existsSync(TARGET)) { console.log('🔴 目标不在：' + TARGET); process.exit(2) }
const mod = await import(pathToFileURL(TARGET).href + '?v=' + Date.now())
mod.apply(makeCtx(), { workspace: WS })

const route = routes.find((r) => r.path === '/gbt-master')
if (!route) { console.log('🔴 没抓到 /gbt-master 路由（挂载失败？）'); process.exit(2) }

function fakeRes() {
  const chunks = []
  return {
    headersSent: false, writableEnded: false,
    writeHead() { this.headersSent = true; return this },
    end(b) { this.writableEnded = true; if (b) chunks.push(Buffer.from(b)); return this },
    _body() { return Buffer.concat(chunks).toString('utf8') },
  }
}

const res = fakeRes()
const t0 = Date.now()
await route.handler({ method: 'GET', url: '/gbt-master', headers: { accept: 'application/json' } }, res)
const elapsed = Date.now() - t0
let panels = -1
try { panels = JSON.parse(res._body()).total } catch {}

console.log('='.repeat(84))
console.log(`目录路由延迟门 · 目标 ${TARGET.replace(WS + '\\', '')}`)
console.log('='.repeat(84))
console.log(`  fs 服务打桩延迟 ${LAT_MS} ms/次 · 本轮实际调用 ${fsCalls} 次`)
console.log(`  /gbt-master 实测耗时 ${elapsed} ms · 面板 ${panels} 条`)
const seq = 13 * LAT_MS
console.log(`  参照：顺序 N+1 应约 ${seq} ms · 并行应约 ${LAT_MS} ms · 阈值 ${4 * LAT_MS} ms`)
const ok = elapsed < 4 * LAT_MS
console.log(ok
  ? '  ✅ 结论：已是并行取数（没有 N+1 顺序等待）'
  : `  🔴 结论：**仍是顺序等待**（${elapsed} ms 接近 13×${LAT_MS}）—— catalog() 里那 13 个 await 还在串行跑`)
process.exit(ok ? 0 : 1)
