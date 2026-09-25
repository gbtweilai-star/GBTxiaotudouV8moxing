/**
 * 进程外验证 gbt-master 宿主半边的三处新改动（用真 node:fs / 真 8765 / 真 http）：
 *   ① /api 内嵌反代：服务在 → 原样透传；服务停 → 503 如实回话（用临时副本改端口来验）
 *   ② holo_pet/node_modules/three 白名单放行（含凭据文件仍被拒的负对照）
 *   ③ 需要本机服务的面板页注入同源改写（含"不该注入的页不注入"的负对照）
 */
import { readFileSync, writeFileSync, statSync, readdirSync, mkdirSync, rmSync, existsSync } from 'node:fs'
import { Readable, Writable } from 'node:stream'
import { pathToFileURL } from 'node:url'
import { join } from 'node:path'

const WS = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const HOST = join(WS, 'plugins/gbt-master/lib/host.js')

function makeCtx(routes, contexts) {
  return {
    fs: {
      async resolve(p) { return { targetKey: String(p).replace(/\\/g, '/'), displayPath: String(p) } },
      async stat(t) {
        try { const s = statSync(t.targetKey); return { type: s.isDirectory() ? 'directory' : (s.isFile() ? 'file' : 'other'), size: s.size, version: 'v1' } }
        catch { return undefined }
      },
      async readBytes(t, signal, max) {
        const b = readFileSync(t.targetKey)
        if (b.length > max) throw new Error('FS_TOO_LARGE')
        return new Uint8Array(b)
      },
      async listDir(t) {
        return readdirSync(t.targetKey, { withFileTypes: true }).map((e) => ({
          name: e.name, type: e.isDirectory() ? 'directory' : (e.isFile() ? 'file' : 'other'),
          target: { targetKey: t.targetKey + '/' + e.name, displayPath: '' },
        }))
      },
      async writeText() { return { operation: 'update', version: 'v1', before: null, after: '' } },
    },
    webServer: { register(r) { routes.push(r); return () => {} } },
    systemPrompt: { context(c) { contexts.push(c); return () => {} } },
    logger: { info() {} },
    effect(fn) { return fn() },
    get(name) { return name === 'timer' ? undefined : this[name] },
  }
}

function res() {
  const chunks = []
  const w = new Writable({ write(c, e, cb) { chunks.push(Buffer.from(c)); cb() } })
  w.code = null
  w.headers = null
  w._done = null
  w.writeHead = function (c, h) { this.code = c; this.headers = h || {}; return this }
  Object.defineProperty(w, 'body', { get() { return Buffer.concat(chunks).toString('utf8') } })
  w.on('finish', () => { if (typeof w._done === 'function') { const f = w._done; w._done = null; f() } })
  return w
}
function req(url, method = 'GET') {
  const r = Readable.from([])
  r.url = url; r.method = method; r.headers = { accept: '*/*' }
  return r
}
async function hit(route, url, waitMs = 8000) {
  const r = res()
  const done = new Promise((ok) => { r._done = ok })
  await route.handler(req(url), r)
  if (r.code === null) await Promise.race([done, new Promise((ok) => setTimeout(ok, waitMs))])
  return r
}
const ct = (r) => (r.headers && r.headers['content-type']) || '(无 content-type)'

// ── 现行 host.js ──────────────────────────────────────────────────────────
const routes = [], contexts = []
const mod = await import(pathToFileURL(HOST).href)
mod.apply(makeCtx(routes, contexts), { workspace: WS })
console.log('路由:', routes.map((r) => r.kind + ' ' + r.path).join('  |  '))
console.log('注入上下文:', contexts.map((c) => c.name + '(order ' + c.order + ')').join(', ') || '（无）')
const apiRoute = routes.find((x) => x.kind === 'prefix' && x.path === '/gbt-master/api')
const fsRoute = routes.find((x) => x.kind === 'prefix' && x.path === '/gbt-master')

// ① 反代 → 真 8765（服务现在在跑）
let r1 = await hit(apiRoute, '/gbt-master/api/state')
console.log('① 反代（真服务在跑）:', r1.code, ct(r1), '|', r1.body.replace(/\s+/g, ' ').slice(0, 110))
let r1b = await hit(apiRoute, '/gbt-master/api/definitely-not-a-real-endpoint')
console.log('① 反代透传未知端点:', r1b.code, '|', r1b.body.replace(/\s+/g, ' ').slice(0, 80))

// ①′ 服务停 → 503（临时副本改端口，不动现行文件）
const tmp = join(WS, '.scratch/_host_port8799.mjs')
writeFileSync(tmp, readFileSync(HOST, 'utf8').replace("port: 8765", "port: 8799"), 'utf8')
const routes2 = [], contexts2 = []
const mod2 = await import(pathToFileURL(tmp).href + '?v=' + Date.now())
mod2.apply(makeCtx(routes2, contexts2), { workspace: WS })
const apiRoute2 = routes2.find((x) => x.kind === 'prefix' && x.path === '/gbt-master/api')
let r2 = await hit(apiRoute2, '/gbt-master/api/state')
console.log('①′ 反代（服务没起）:', r2.code, '|', r2.body.replace(/\s+/g, ' ').slice(0, 160))
rmSync(tmp, { force: true })

// ② three 放行（造临时文件来验，验完删）
// ⚠️ 只用独立探针文件名，绝不碰真文件（曾经覆盖过真的 three.module.js，教训）
const probeDir = join(WS, 'holo_pet/node_modules/three/build')
const probeFile = join(probeDir, '_gbt_verify_probe.js')
const probeRel = 'holo_pet/node_modules/three/build/_gbt_verify_probe.js'
if (existsSync(probeFile)) throw new Error('探针文件已存在，拒绝覆盖: ' + probeFile)
mkdirSync(probeDir, { recursive: true })
writeFileSync(probeFile, 'export const VERIFY = true;\n')
let r3 = await hit(fsRoute, '/gbt-master/fs/' + probeRel)
console.log('② three 前缀放行（探针）:', r3.code, ct(r3), '字节=' + Buffer.byteLength(r3.body))
let r4 = await hit(fsRoute, '/gbt-master/fs/config/mcporter.json')
console.log('② 负对照（凭据文件）:', r4.code, '|', r4.body.slice(0, 40))
rmSync(probeFile, { force: true })
console.log('   探针已删: ' + !existsSync(probeFile) + ' · 真文件未被触碰')

// ③ 同源改写注入
let r5 = await hit(fsRoute, '/gbt-master/fs/holo_pet/index.html')
const ok5 = r5.body.includes('/gbt-master/api') && r5.body.includes('XMLHttpRequest.prototype.open')
console.log('③ 数字人面板页注入改写:', r5.code, '含改写=' + ok5, '字节=' + Buffer.byteLength(r5.body))
let r6 = await hit(fsRoute, '/gbt-master/fs/index.html')
console.log('③ 负对照（总索引页不该注入）:', r6.code, '含改写=' + r6.body.includes('XMLHttpRequest.prototype.open'))



