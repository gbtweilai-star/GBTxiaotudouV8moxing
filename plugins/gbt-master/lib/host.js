/**
 * GBT小土豆V8 · 总面板 · 宿主半边
 *
 * 干两件事，都只走 DSH 自己的公开面：
 *   ① webServer.register —— 一条只读白名单路由，把工作区的可视化面板「同源」喂给浏览器
 *      （file:// 下 ES module 会被跨源拦掉，面板只剩空壳；同源才真跑）
 *   ② 目录 JSON —— /gbt-master 精确路由，客户端据此渲染面板清单（在/缺从盘上现读）
 *
 * 不发布任何 Cordis 服务，不占 fallback 席位，不改 DSH 一行源码。
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { request as httpRequest } from 'node:http'
import { readFileSync } from 'node:fs'

const HERE = dirname(fileURLToPath(import.meta.url))
/**
 * 工作区根：优先取组合行里显式声明的 `workspace`（部署事实属于组合层），
 * 没写才退回「跟着包走」的推导（上溯三级）。
 * ⚠️ pnpm 的 file: 安装是硬链接，import.meta.url 会落在 profile 的 node_modules 里，
 * 推导会指错 —— 所以正式挂载写 config.workspace，或用 link: 安装。
 */
const DERIVED = resolve(HERE, '..', '..', '..').replace(/\\/g, '/')
const FALLBACK = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const DEFAULT_WORKSPACE = DERIVED.indexOf('/node_modules/') < 0 ? DERIVED : FALLBACK

const BASE = '/gbt-master'
const FS_BASE = BASE + '/fs/'
const MAX_BYTES = 12 * 1024 * 1024

/** 面板若声明 apiShim，它的 /api/* 由内嵌反代转给本机服务（默认 127.0.0.1:8765） */
const API_SERVICE = { host: '127.0.0.1', port: 8765 }
const API_PREFIX = BASE + '/api/'

/** 这些前缀虽然含被拒目录段，但属于面板自身的静态依赖，单独放行 */
const EXEMPT = ['holo_pet/node_modules/three/']

/** 注入到需要本机服务的面板页里：把 /api/* 改写到内嵌反代（同源，不跳转） */
const API_SHIM = "<script>(function(){var P='" + BASE + "/api';function fix(u){return (typeof u==='string'&&u.charAt(0)==='/'&&u.indexOf('/api/')===0)?(P+u.slice(4)):u}"
  + "var of=window.fetch;window.fetch=function(u,o){try{u=fix(u)}catch(e){}return of.call(this,u,o)};"
  + "var xo=XMLHttpRequest.prototype.open;XMLHttpRequest.prototype.open=function(m,u){try{arguments[1]=fix(u)}catch(e){}return xo.apply(this,arguments)};"
  + "var EO=window.EventSource;if(EO){window.EventSource=function(u,c){return new EO(fix(u),c)}}})();</script>"

const TYPES = {
  html: 'text/html; charset=utf-8',
  css: 'text/css; charset=utf-8',
  js: 'text/javascript; charset=utf-8',
  mjs: 'text/javascript; charset=utf-8',
  json: 'application/json; charset=utf-8',
  txt: 'text/plain; charset=utf-8',
  md: 'text/plain; charset=utf-8',
  csv: 'text/csv; charset=utf-8',
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  webp: 'image/webp',
  gif: 'image/gif',
  svg: 'image/svg+xml',
  ico: 'image/x-icon',
  woff2: 'font/woff2',
  glb: 'model/gltf-binary',
  gltf: 'model/gltf+json',
  wasm: 'application/wasm',
  mp4: 'video/mp4',
  webm: 'video/webm',
}

/** 默认拒绝：这些目录段一律不出网（凭据、内部资料、依赖树） */
const DENY = [
  'node_modules', 'vendor', 'memory', 'config', 'store', 'delivery',
  'generated-images', 'outputs', 'data', 'state', 'brain', 'caps',
  'plugins', 'gbt_allinone', 'tools', 'skills', '.git', '.backups',
  '.trash', '.scratch', '.cluster', '.shadow-repo', '.agents', '.openclaw',
]

const PANELS = [
  { id: 'index', name: '可视化面板总索引', file: 'index.html', note: '一屏列全活面板与渲染留影' },
  { id: 'caps', name: '能力球 · 能力台', file: 'capabilities.html', note: '158 项能力铺在真 3D 球面上 · 拖拽旋转 · 点节点进独立页', apiShim: true, needs: '这一页的“最近调用 / 事件流”来自本机服务（127.0.0.1:8765）。宿主内已接内嵌反代；服务没起时这些读数会显示为空（不是假数据）。' },
  { id: 'w3', name: '上帝视角 W3', file: 'holo_pet_w3/index.html', note: '六页签实时驾驶舱', needs: '上帝视角设计为独立窗口，数据走 Electron IPC 桥；在宿主内看，只能看到静态壳与前端的如实降级态。' },
  { id: 'h1', name: '赏金台 · h1mcp', file: 'holo_pet_w3/h1/index.html', note: 'HackerOne 赏金台（阶段一 · 本机只读）：二进制在位 + 侧车 sha256 比对、凭据配置状态、本地草稿收件箱', apiShim: true, needs: '凭据 H1_USERNAME / H1_API_KEY 只报「已配置 / 未配置」，不回显值；没配时如实显示未配置，不假绿。本页在宿主内走**同源 HTTP**（原 Electron IPC 路保持不动）。' },
  { id: 'brain', name: '大脑执行层 · 五维合一', file: 'brain.html', note: '五维合一脑的排布图与连接网络：结构从 brain_exec.py 的 AST 现算，实时状态从 store/audit.jsonl 的真实事件尾部取', apiShim: true, needs: '源码里查不到的边不画 —— 注册表声称的执行链有 3 条在代码里不存在，图上如实标 drawn=false；本机服务没起时如实报取不到。' },
  { id: 'pet', name: '主控台 W1 · 数字人面板', file: 'holo_pet/index.html', note: '全息对话面板 + 3D 形象 + 能力栏', apiShim: true, needs: '这个面板的数据来自本机服务 holo_pet/launch_panel.py（默认 127.0.0.1:8765）；服务没起时，页面只能拿到静态壳，/api/* 一律拿不到。' },
  { id: 'avatar', name: '数字人形象页（成品）', file: 'holo_pet/assets/digital-human/web/avatar.html', note: '数字人主线的成品页：idle↔walk 交叉淡入状态机 · IBL + PBR Neutral + 接触阴影 + SSAA · HUD 现读', needs: '默认走全身动画件 raw/rig/model-rigged-anim.glb（3.37 MB）；`?model=bust` 换半身件 raw/portrait-bust-low-rigged.glb（4.28 MB）。两件都在宿主 12 MB 单文件上限内，所以能直接内嵌。4K 件（90.86 MB）超上限，不要指过来。' },
  { id: 'v22', name: 'V22 可交互原型', file: 'V22 GBT小土豆V8-可交互原型.html', note: '本版交付物之一 · App 类 · 单文件自带全部样式与脚本' },
  { id: 'v22c', name: 'V22 无限画布', file: 'V22 GBT小土豆V8-无限画布.html', note: '自由画布形态 · 拖拽 / 缩放 / 复位' },
  { id: 'hitl', name: 'HITL#1 审批屏', file: 'projects/_shared/templates/20260921-三方向-HITL1审批屏.html', note: '链状态 + 逐镜待填 + 闸口表 + 独立审计判定 + 作者认账' },
  { id: 'form', name: '分镜契约填写页', file: 'projects/_shared/templates/20260921-三方向-HITL1-分镜契约填写页.html', note: '把「审」变成「填」的 85 格契约表单' },
  { id: 'deploy', name: '部署版入口', file: 'deploy/index.html', note: '推到部署面的那份：**V21 代快照**（2026-09-21 18:58 落盘 · 与根上 V22 有 39 行差）；页内自称 V21、根上 V22 是**手工演进**（没有 build_v22 生成器）。重新部署＝外网写入 ⇒ 必须先问主人' },
  /* 2026-09-23 第 56 轮加：三方向自动化工作流流程台。
     它是**生成页**（`tools/codex-scripts/media-console.py`），数据全部现读：
     18 格抽屉状态取自 `media_flow`（同一份判据）· 三条链取自 `media_run.CHAINS` ·
     许可账取自 `media_license` · 发布包与平台口径取自 `media_publish`。
     页面自带生成时刻与重生成命令（快照自报家门），并明写「不会、也不能替你发布」。 */
  { id: 'media', name: '三方向自动化工作流', file: 'media-console.html', note: '短视频 / AI电影 / AI音乐 三条链的现读进度：18 格抽屉（有货·仅彩排·空）+ 许可账（逐件 sha256）+ 发布包（**停在主人授权门**）。生成：`py -3.14 tools/codex-scripts/media-console.py`' },
]

function extOf(p) {
  const i = p.lastIndexOf('.')
  return i < 0 ? '' : p.slice(i + 1).toLowerCase()
}

function encPath(p) {
  return String(p).split('/').map(encodeURIComponent).join('/')
}

function safeRel(raw) {
  let rel = String(raw || '').replace(/\\/g, '/')
  while (rel.charAt(0) === '/') rel = rel.slice(1)
  if (rel === '' || rel.length > 400) return null
  const exempt = EXEMPT.some((p) => rel.indexOf(p) === 0)
  const parts = rel.split('/')
  for (let i = 0; i < parts.length; i++) {
    const seg = parts[i]
    if (seg === '' || seg === '.' || seg === '..') return null
    if (seg.charAt(0) === '.') return null
    if (!exempt && DENY.indexOf(seg.toLowerCase()) >= 0) return null
  }
  if (TYPES[extOf(rel)] === undefined) return null
  return parts.join('/')
}

export const inject = ['fs', 'webServer', 'systemPrompt']

export function apply(ctx, config) {
  const cfg = (config && typeof config === 'object')
    ? config
    : (ctx.config && typeof ctx.config === 'object' ? ctx.config : {})
  const declared = typeof cfg.workspace === 'string' ? cfg.workspace.trim() : ''
  const WORKSPACE = (declared || DEFAULT_WORKSPACE).replace(/\\/g, '/').replace(/\/+$/, '')
  const fs = ctx.fs
  const webServer = ctx.webServer

  async function statOf(rel) {
    try {
      const info = await fs.stat(await fs.resolve(WORKSPACE + '/' + rel))
      if (info === undefined || info.type !== 'file') return null
      return info
    } catch (err) {
      return null
    }
  }

  async function catalog() {
    // 🔴 2026-09-22 修：这里原来是**13 个顺序 await**（12 个面板各 `await statOf()` + 一次 `fs.listDir(render/)`），
    // 每次都要过 `fs` 服务一个来回 ⇒ 实测 `/gbt-master` **每次 8–10 秒**（连测 6 次：10.15/10.07/9.02/8.12/8.24/8.55 s，
    // 而响应体只有 4.8 KB）。后果不止"慢"：总索引页的台账要等它、能力球的现读对齐要等它，
    // 而且**几支验收器的前置取数会偶发超时**（本轮 `check-panel-syntax --all` 与 `verify-index-panel` 都撞过）。
    // 改法：这些 stat **彼此独立** ⇒ 一次 `Promise.all` 并发取，把 N 个来回压成一个来回。
    // 门：`plugins/gbt-master/tools/verify-catalog-latency.mjs`（把 fs 打桩成固定延迟，顺序≈N×延迟 / 并行≈1×延迟）。
    const [infos, rendersCount] = await Promise.all([
      Promise.all(PANELS.map((p) => statOf(p.file))),
      (async () => {
        try {
          const entries = await fs.listDir(await fs.resolve(WORKSPACE + '/render'))
          return entries.filter((e) => e.type === 'file' && extOf(e.name) === 'png').length
        } catch (err) {
          return null
        }
      })(),
    ])
    let present = 0
    const panels = PANELS.map((p, i) => {
      const info = infos[i]
      if (info !== null) present += 1
      return {
        id: p.id,
        name: p.name,
        note: p.note,
        file: p.file,
        url: FS_BASE + encPath(p.file),
        exists: info !== null,
        size: info !== null && typeof info.size === 'number' ? info.size : null,
        needs: p.needs || null,
      }
    })
    const renders = rendersCount
    return {
      ok: true,
      plugin: 'gbt-potato-master-v9',
      // 🔴 每次改宿主半边**必须动这个版本号**：宿主代码是**进程启动时装载**的，
      //    `/gbt-master` 自报的 `version` 是"现在跑的是哪一版"的**唯一**现读信号
      //    （1.8.0 = 没有 §4.7 两处报告层修正、也没有 §4.12 的目录路由并发）。
      //    `tools/verify-after-restart.py` 的 ① 就按它判"重启到位没有"。
      version: '1.8.1',
      workspace: WORKSPACE,
      base: FS_BASE,
      panels,
      renders,
      total: panels.length,
      present,
      // 浏览器半边的自报（`POST /gbt-master/diag`）：品牌三格到底注册上没有、报了什么错。
      // 之所以要它：single 插槽的占用从插槽检查器看不出来（`registrant` 是通用标签）。
      clientDiag: clientDiag || null,
    }
  }

  function sendJson(res, code, value) {
    const body = JSON.stringify(value)
    // 🔴 这里原来写 `String(body.length)` —— 那是 **JS 字符串的字符数**，不是字节数。
    // 中文一多，`content-length` 就小于真实 body：严格客户端（curl、任何按 RFC 走的
    // 解析器）只读头里那个数 ⇒ **JSON 半截**（实测 4671 字节的目录被切成 3415，
    // 报 "Unterminated string ... panels[8].name"）。IWR / 浏览器宽容，所以一直没暴露。
    // 修法：按 UTF-8 真字节数报头。
    const bytes = Buffer.byteLength(body, 'utf8')
    res.writeHead(code, {
      'content-type': TYPES.json,
      'content-length': String(bytes),
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    })
    res.end(body)
  }

  function sendText(res, code, text) {
    res.writeHead(code, {
      'content-type': TYPES.txt,
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    })
    res.end(text)
  }

  // 目录 + 健康（精确路由）：客户端读它，也用来一眼判「接上没有」
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE,
    handler: async (req, res) => {
      try {
        const payload = await catalog()
        rememberSnapshot(payload)
        sendJson(res, 200, payload)
      } catch (err) {
        sendJson(res, 500, { ok: false, error: String(err && err.message ? err.message : err).slice(0, 200) })
      }
    },
  }), 'gbt-master 目录路由')

  // 自愈器（精确路由）：**每次请求现读磁盘**，这样"改自愈逻辑"不必再换一代包。
  // 为什么必须现读：注入进首页的只有一行 `<script src=…/heal.js>`（永不改变），
  // 真正的判据与节流都住在 lib/heal.js 里 —— 换代只需重装包，改逻辑只需改文件。
  // 路径取两份：① 组合行声明的工作区（唯一真源）；② 跟着包走（工作区没声明时的退路）。
  const HEAL_CANDIDATES = [
    WORKSPACE + '/plugins/gbt-master/lib/heal.js',
    resolve(HERE, 'heal.js'),
  ]
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/heal.js',
    handler: async (req, res) => {
      let text = null
      for (const p of HEAL_CANDIDATES) {
        try {
          const buf = readFileSync(p)
          if (buf && buf.length > 0) { text = buf.toString('utf8'); break }
        } catch (err) { /* 换下一个候选 */ }
      }
      if (text === null) {
        // 读不到就发一个**什么都不做**的最小件：页面不会报错，也不会乱刷。
        text = '/* gbt-master: heal.js 读不到（工作区/包内都没有）—— 本件故意空转 */\n'
      }
      res.writeHead(200, {
        'content-type': TYPES.js,
        'content-length': String(Buffer.byteLength(text, 'utf8')),
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      })
      res.end(text)
    },
  }), 'gbt-master 首页自愈器路由')

  // ── 上帝视角（W3）· 项目树数据源：**宿主自己读，静态路由一个字节都不放宽** ──
  // 为什么非要宿主读：W3 的项目树在 Electron 里读的是
  //   `<ROOT>/gbt_allinone/docs/GBT全项目思维导图.md` 里的 §一 markmap 块
  //   （`holo_pet_w3/shell/main.cjs` 的 `w3Mindmap()`）。
  //   而 `gbt_allinone` **在 `DENY` 名单里**（凭据/内部资料/依赖树一律不出网）⇒
  //   实测 `/gbt-master/fs/gbt_allinone/docs/…` 是 **404**，而且**那是设计，不是 bug**。
  //   ⇒ 放宽 DENY 是改安全口径（不是我的权限）；**改成宿主自己读**（同 `heal.js` 那条路），
  //     静态面依然一个字节都发不出去。
  // 口径：**只发那一个 markmap 块**（正则抽），不发整份文件 —— 最小暴露面。
  //   ⚠️ 本路由住在 `host.js` 里，而宿主半边是**进程内已 import 的模块** ⇒ **要等 DSH 重启**才生效。
  const MINDMAP_CANDIDATES = [
    WORKSPACE + '/gbt_allinone/docs/GBT全项目思维导图.md',
  ]
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/w3/mindmap',
    handler: async (req, res) => {
      let raw = null, used = null
      for (const p of MINDMAP_CANDIDATES) {
        try {
          const buf = readFileSync(p)
          if (buf && buf.length > 0) { raw = buf.toString('utf8'); used = p; break }
        } catch (err) { /* 换下一个候选 */ }
      }
      if (raw === null) {
        // 读不到就**如实报缺**，不编一份假的树（那会让"没接上"看起来像"接上了"）
        return sendJson(res, 200, {
          ok: false,
          error: '导图源文件读不到（候选路径都试过）—— 项目树这一窗如实报缺，不编',
          tried: MINDMAP_CANDIDATES,
        })
      }
      const m = /```markdown\r?\n([\s\S]*?)```/.exec(raw)
      if (!m) {
        return sendJson(res, 200, {
          ok: false, error: '源文件里没有 §一 的 markmap markdown 块', file: used,
        })
      }
      sendJson(res, 200, {
        ok: true,
        data: m[1],                       // ← `window.js` 期望的形状：`{ok, data}`（unpack 吃这个）
        file: used.replace(WORKSPACE + '/', ''),
        bytes: Buffer.byteLength(m[1], 'utf8'),
        readonly: true,
        note: '与 Electron 侧同源（同一份 .md 的同一个 markmap 块）；宿主只读，静态路由仍不放宽 DENY',
      })
    },
  }), 'gbt-master W3 项目树源（宿主只读）')

  // ── 上帝视角（W3）· **宿主内数据件**：同源脚本文件，页面**一个 fetch 都不发生** ──
  // 为什么必须是"同源 .js 文件"（三条都不行，只剩这条）：
  //   那一页的 CSP = `default-src 'none'; script-src 'self'; style-src 'self';
  //                   img-src 'self' data:; font-src 'self'; connect-src 'none'`
  //   ① 页面自己 fetch ⇒ `connect-src 'none'` **直接拒**（实测 8 条控制台红字）；
  //   ② 注入**内联** `<script>…</script>` ⇒ `script-src 'self'` **同样拒**（'self' 只放行同源**文件**）；
  //   ③ 放宽 CSP ⇒ 那是改主人的安全口径（这一页"离线自包含"是硬保证），**不是我能定的**。
  //   ⇒ 宿主把数据做成**同源 .js**发出去，页面用 `<script src>` 吃：CSP 一个字不用动，
  //     且**不产生任何网络取数**（`connect-src 'none'` 依然成立）。
  // 主人 2026-09-23 裁决原话：「按照原生能力挨个镶嵌进去，这样看起来自然」。
  function readPanelState() {
    // 宿主侧读本机面板服务（`/api/state`）—— 页面侧不再发这个请求
    return new Promise((resolve) => {
      let done = false
      const fin = (v) => { if (!done) { done = true; resolve(v) } }
      let req
      try {
        req = httpRequest({
          host: API_SERVICE.host, port: API_SERVICE.port, path: '/api/state', method: 'GET',
          headers: { host: API_SERVICE.host + ':' + String(API_SERVICE.port), accept: 'application/json' },
        }, (up) => {
          let b = ''
          up.setEncoding('utf8')
          up.on('data', (c) => { b += c })
          up.on('end', () => {
            try { fin({ ok: true, data: JSON.parse(b) }) }
            catch (err) { fin({ ok: false, error: 'state 返回不是 JSON（前 80 字：' + b.slice(0, 80) + '）' }) }
          })
        })
      } catch (err) { return fin({ ok: false, error: '本机服务连不上：' + String(err && err.message || err).slice(0, 120) }) }
      req.on('error', (err) => fin({ ok: false, error: '本机服务取不到：' + String(err && err.message || err).slice(0, 120) }))
      req.setTimeout(4000, () => { try { req.destroy() } catch (e) { /* ignore */ } fin({ ok: false, error: '本机服务 4s 没回' }) })
      req.end()
    })
  }
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/w3/data.js',
    handler: async (req, res) => {
      const out = { at: new Date().toISOString(), readonly: true, source: {} }
      try {
        const raw = readFileSync(MINDMAP_CANDIDATES[0], 'utf8')
        const m = /```markdown\r?\n([\s\S]*?)```/.exec(raw)
        if (m) {
          out.mindmap = { ok: true, data: m[1], bytes: Buffer.byteLength(m[1], 'utf8') }
          out.source.mindmap = 'gbt_allinone/docs/GBT全项目思维导图.md · §markmap'
        } else {
          out.mindmap = { ok: false, error: '源文件里没有 §一 的 markmap markdown 块' }
        }
      } catch (err) {
        out.mindmap = { ok: false, error: '导图源读不到：' + String(err && err.message || err).slice(0, 120) }
      }
      out.state = await readPanelState()
      out.source.state = API_SERVICE.host + ':' + String(API_SERVICE.port) + '/api/state（宿主代取）'
      // 交流视野（顾问席三栏之②）：宿主读**审计账本尾部**，随同一个数据件发下来（页面零 fetch）。
      // 🔴 口径要写在读数里：`count` 是**尾部窗口内**的条数，**不是全史总数** ——
      //    全史 30 万行、几十 MB，宿主每次请求全扫一遍是拿性能换一个好看的数字，不值。
      //    所以另外把 `file_bytes` 一并报出来，读的人能自己判断"这是尾巴"。
      try {
        const led = WORKSPACE + '/gbt_allinone/store/audit.jsonl'
        const buf = readFileSync(led)
        const WINDOW = 256 * 1024                       // 只读尾部 256 KB
        const start = Math.max(0, buf.length - WINDOW)
        const chunk = buf.slice(start).toString('utf8')
        const lines = chunk.split('\n').filter((x) => x.trim())
        if (start > 0) lines.shift()                    // 掐掉可能被截半的第一行
        const tail = []
        for (let i = lines.length - 1; i >= 0 && tail.length < 8; i--) {
          try {
            const r = JSON.parse(lines[i])
            const m = r.meta || {}
            tail.push({ iso: r.iso || '', kind: m.kind || r.kind || '?',
                        event: r.event || '', note: String(m.note || m.desc || '').slice(0, 40) })
          } catch (e) { /* 坏行跳过，不编 */ }
        }
        out.stream = { ok: true, data: { count: lines.length, tail: tail.reverse(),
                                         file_bytes: buf.length, window_bytes: WINDOW,
                                         window_bounded: start > 0 } }
        out.source.stream = 'gbt_allinone/store/audit.jsonl（宿主只读尾部窗口）'
      } catch (err) {
        out.stream = { ok: false, error: '审计账本读不到：' + String(err && err.message || err).slice(0, 120) }
      }
      // 顾问席三栏之③：两席的**只追加建议账**（`store/advisor/<席位>.jsonl`）。
      // 口径：只报**条数 + 尾部几条**；`executes:false` 由写入器保证，
      // 而"没有执行权"由 `tools/codex-scripts/advisor-audit.py` 的四条判据**机检**。
      // 读不到就如实报缺 —— 不编"某席位提过什么"。
      try {
        const SEATS = ['claude', 'dsh']
        const seats = {}
        for (const s of SEATS) {
          const f = WORKSPACE + '/gbt_allinone/store/advisor/' + s + '.jsonl'
          let lines = []
          try {
            lines = readFileSync(f, 'utf8').split('\n').filter((x) => x.trim())
          } catch (e) { lines = [] }                       // 席位还没开张 ≠ 出错
          const tail = []
          for (let i = lines.length - 1; i >= 0 && tail.length < 3; i--) {
            try { tail.push(JSON.parse(lines[i])) } catch (e) { tail.push({ 坏行: lines[i].slice(0, 60) }) }
          }
          seats[s] = { lines: lines.length, tail: tail.reverse(), readonly: '项目树 · 交流流' }
        }
        out.advisors = { ok: true, data: { seats: seats, seats_total: SEATS.length } }
        out.source.advisors = 'gbt_allinone/store/advisor/*.jsonl（宿主只读）'
      } catch (err) {
        out.advisors = { ok: false, error: '建议账读不到：' + String(err && err.message || err).slice(0, 120) }
      }
      const body = '/* gbt-master · W3 宿主内数据件（只读）：由**宿主**读盘与读本机服务后生成，\n'
        + '   页面不做任何 fetch（那张页的 CSP 是 connect-src \'none\'，离线自包含是它的设计保证）。\n'
        + '   票面时间 at 就是这份数据的时刻 —— 按它判断新鲜度，别把快照当实时。 */\n'
        + 'window.GBT_W3_DATA = ' + JSON.stringify(out) + ';\n'
      res.writeHead(200, {
        'content-type': TYPES.js,
        'content-length': String(Buffer.byteLength(body, 'utf8')),
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      })
      res.end(body)
    },
  }), 'gbt-master W3 宿主内数据件（同源脚本，零 fetch）')

  // ── W3 页的**宿主内包装**：只做一件事 —— 在 </body> 前注入那一行数据脚本 ──
  // 为什么不直接改页面文件：Electron（file://）下必须读到**原页**（多这一行就会在那边 404 喷红字）。
  //   ⇒ 宿主下才注入 = **同一份源文件、零分叉**（这句话是这一条路由存在的全部理由）。
  const W3_PAGE_FILE = WORKSPACE + '/holo_pet_w3/index.html'
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/fs/holo_pet_w3/index.html',
    handler: async (req, res) => {
      let html = null
      try { html = readFileSync(W3_PAGE_FILE, 'utf8') } catch (err) { html = null }
      if (html === null) {
        return sendText(res, 404, 'GBT总面板: W3 页读不到 · ' + W3_PAGE_FILE)
      }
      const tag = '<script src="' + BASE + '/w3/data.js"></script>'
      if (html.indexOf(tag) === -1) {
        // 注入点：**第一个脚本之前**。为什么不是 </body> 前 —— 那样会排在 window.js 之后，
        // 首帧 `window.gbtW3.mindmap()` 读到的还是空，于是先渲染一句"取不到"再等下一次刷新才补上。
        // 摆在最前 ⇒ 数据先就位，六窗第一次刷新就有真读数。
        const first = html.search(/<script\b/i)
        if (first >= 0) html = html.slice(0, first) + tag + '\n' + html.slice(first)
        else if (html.indexOf('</body>') >= 0) html = html.replace('</body>', tag + '\n</body>')
        else html = html + '\n' + tag + '\n'          // 兜底：两个锚点都没有就追加末尾
      }
      res.writeHead(200, {
        'content-type': 'text/html; charset=utf-8',
        'content-length': String(Buffer.byteLength(html, 'utf8')),
        'cache-control': 'no-store',
        'x-content-type-options': 'nosniff',
      })
      res.end(html)
    },
  }), 'gbt-master W3 页（宿主内注入数据脚本）')

  // 浏览器半边自报诊断（POST）：**为什么要有这条** —— single 插槽（左栏品牌两格）到底注册上没有，
  // 插槽检查器判不了责任（本构建里 `registrant` 是通用标签：头部 4 条、浮层那条、品牌那条全是 `Ba`），
  // 所以让页面**自己报**：每一步注册进没进、报什么错。存内存，由 `/gbt-master` 的 `clientDiag` 读回。
  // 只收 JSON、只存最新一条、限长 —— 这不是通道，是自检回执。
  var clientDiag = null
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/diag',
    handler: (req, res) => {
      if (String(req.method || '').toUpperCase() !== 'POST') {
        sendJson(res, 200, { ok: true, note: 'POST {gen,diag}；读回查 /gbt-master 的 clientDiag 字段' })
        return
      }
      let raw = ''
      req.on('data', (c) => { raw += c; if (raw.length > 8192) { raw = raw.slice(0, 8192) } })
      req.on('end', () => {
        try {
          const body = JSON.parse(raw || '{}')
          clientDiag = {
            at: new Date().toISOString(),
            gen: String(body.gen || '').slice(0, 60),
            diag: Array.isArray(body.diag) ? body.diag.slice(0, 12).map((s) => String(s).slice(0, 120)) : [],
          }
        } catch (err) {
          clientDiag = { at: new Date().toISOString(), gen: '', diag: ['宿主收到非 JSON 自报：' + String(err && err.message)] }
        }
        sendJson(res, 200, { ok: true })
      })
    },
  }), 'gbt-master 浏览器自报诊断路由')

  function needsShim(rel) {
    for (let i = 0; i < PANELS.length; i++) {
      if (PANELS[i].apiShim && PANELS[i].file === rel) return true
    }
    return false
  }

  // 内嵌反代：面板的 /api/* → 本机服务（127.0.0.1:8765）；服务没起时如实回 503，不伪装
  ctx.effect(() => webServer.register({
    kind: 'prefix',
    path: BASE + '/api',
    handler: (req, res) => {
      const raw = String(req.url || '')
      const cut = raw.indexOf('?')
      const pathOnly = cut < 0 ? raw : raw.slice(0, cut)
      const query = cut < 0 ? '' : raw.slice(cut)
      if (pathOnly.indexOf(API_PREFIX) !== 0) {
        sendJson(res, 404, { ok: false, error: 'GBT总面板: 反代只接 /gbt-master/api/*' })
        return
      }
      const target = '/api/' + pathOnly.slice(API_PREFIX.length) + query
      // 🔴 必须把 `content-length` 原样转下去（2026-09-22 穿透扫描抓到的真缺陷 #7）。
      // 不转它时，Node 的 http.request 会对请求体改用 **Transfer-Encoding: chunked**；
      // 而上游 `holo_pet/panel_server.py` 是 `BaseHTTP/0.6`（= HTTP/1.0）—— **不认 chunked**，
      // 于是按「没有 Content-Length」读 0 字节 ⇒ **请求体整个丢掉**。
      // 症状：所有 POST 端点经总面板都变成空动作（上游回「缺少 kind」「消息为空」），
      // 而直连 8765 一切正常 ⇒ 极难从界面看出来。
      // 裸 socket 对照实测（同一 body）：chunked → 400「缺少 kind」；content-length → 200 accepted。
      // `transfer-encoding` 绝不转发 —— 定帧交给 Node 按 content-length 做。
      const headers = { host: API_SERVICE.host + ':' + String(API_SERVICE.port), accept: String(req.headers.accept || '*/*') }
      if (req.headers['content-type'] !== undefined) headers['content-type'] = String(req.headers['content-type'])
      if (req.headers['content-length'] !== undefined) headers['content-length'] = String(req.headers['content-length'])
      const up = httpRequest({ host: API_SERVICE.host, port: API_SERVICE.port, path: target, method: req.method, headers },
        (upRes) => {
          const out = { 'cache-control': 'no-store', 'x-content-type-options': 'nosniff' }
          if (upRes.headers['content-type'] !== undefined) out['content-type'] = String(upRes.headers['content-type'])
          if (upRes.headers['cache-control'] !== undefined) out['cache-control'] = String(upRes.headers['cache-control'])
          res.writeHead(upRes.statusCode || 502, out)
          upRes.pipe(res)
        })
      up.on('error', () => {
        // 上游可能已经把响应头发出去了（流到一半才断）：这时只能断开，绝不能再写 503 ——
        // 否则 ERR_HTTP_HEADERS_SENT 会在错误处理里再抛一次，把宿主进程一起带走。
        if (res.headersSent === true || res.writableEnded === true) {
          try { res.destroy() } catch (err) { /* 只能断开 */ }
          return
        }
        sendJson(res, 503, {
          ok: false, unavailable: true,
          error: 'GBT总面板: 本机服务未启动（' + API_SERVICE.host + ':' + String(API_SERVICE.port) + '）',
          how: '跑 holo_pet/launch_panel.py --host 127.0.0.1 --port 8765 后重载本面板',
        })
      })
      req.pipe(up)
    },
  }), 'gbt-master 本机服务内嵌反代')

  // 只读白名单静态路由（前缀不带尾斜杠 —— DSH 的 prefix 匹配是 `=== prefix || startsWith(prefix + '/')`）
  ctx.effect(() => webServer.register({
    kind: 'prefix',
    path: BASE,
    handler: async (req, res) => {
      let rel = null
      try {
        const raw = String(req.url || '')
        const cut = raw.indexOf('?')
        const pathOnly = decodeURIComponent(cut < 0 ? raw : raw.slice(0, cut))
        if (pathOnly.indexOf(FS_BASE) === 0) rel = safeRel(pathOnly.slice(FS_BASE.length))
      } catch (err) {
        rel = null
      }
      if (rel === null) {
        sendText(res, 404, 'GBT总面板: 该路径不在可服务白名单内 · ' + String(req.url || '').slice(0, 120))
        return
      }
      try {
        const info = await statOf(rel)
        if (info === null) {
          sendText(res, 404, 'GBT总面板: 文件不在盘上 · ' + rel)
          return
        }
        const bytes = await fs.readBytes(await fs.resolve(WORKSPACE + '/' + rel), undefined, MAX_BYTES)
        let body = bytes
        if (extOf(rel) === 'html' && needsShim(rel)) {
          const html = new TextDecoder().decode(bytes)
          const at = html.search(/<head[^>]*>/i)
          const injected = at < 0 ? API_SHIM + html : html.slice(0, at) + html.slice(at).replace(/>/, '>' + API_SHIM)
          body = new TextEncoder().encode(injected)
        }
        res.writeHead(200, {
          'content-type': TYPES[extOf(rel)] || 'application/octet-stream',
          'content-length': String(body.length),
          'cache-control': 'no-store',
          'x-content-type-options': 'nosniff',
        })
        res.end(body)
      } catch (err) {
        sendText(res, 500, 'GBT总面板: 读取失败 · ' + String(err && err.message ? err.message : err).slice(0, 160))
      }
    },
  }), 'gbt-master 只读面板路由')

  // ── 面板上下文：装配提示词时现读的实况，重启后不必 Owner 再交代 ────────────────
  let snapshot = null

  function stamp() {
    return new Date().toISOString().replace('T', ' ').slice(0, 19)
  }

  function renderSnapshot(payload, at) {
    const missing = payload.panels.filter((p) => !p.exists).map((p) => p.name)
    // 🔴 2026-09-22 修：这一行原来**写死**"左栏品牌行＝土豆 Logo + GBT小土豆V8" ——
    // 那是"部署已就绪"、不是"已生效"。同一份 payload 里就有铁证 `clientDiag`：
    // 它为 null ⇒ **本代 bundle 还没在任何打开的页面里跑过**（页面是上一代、或还没重载）。
    // 写死会把"没生效"讲成"生效了"，等于**每一轮重启的模型都被这句话带偏**（报告层假绿）。
    // 现在按 clientDiag 现读分两种说法，谁也不冒充谁。
    const cd = payload.clientDiag
    const GEN = 'gbt-potato-master-v9'
    let brandLine
    if (cd && typeof cd === 'object' && cd.gen === GEN) {
      brandLine = '· 左栏品牌行＝土豆 Logo + GBT小土豆V8（**该页已按本代加载**：gen=' + String(cd.gen)
        + ' · 客户端诊断时间 ' + String(cd.at || '?') + '）'
    } else if (cd && typeof cd === 'object' && cd.gen) {
      // 收到过诊断、但 gen 与本代不符（旧页/自测包）——**照样如实说**，别folded 成"已加载"
      brandLine = '· 左栏品牌行＝土豆 Logo + GBT小土豆V8（**诊断里的 gen 与本代不符**：'
        + '现读 gen=' + String(cd.gen) + ' ≠ ' + GEN + ' ⇒ 那张页面是别的世代，要一次 F5）'
    } else {
      brandLine = '· 左栏品牌行＝土豆 Logo + GBT小土豆V8（**部署就绪、尚未在任何页面生效**：'
        + '现读 `clientDiag = null` ⇒ 页面还没按本代加载，需要一次 F5；自愈器已在首页注入、此后不再要人按）'
    }
    return [
      '【GBT小土豆V8 · 总面板（宿主插件 gbt-potato-master-v9 现读）】',
      '- 入口（2026-09-23 主人令后改：会话头那两条按钮已删）：左栏**品牌标可点** ⇒ 面板清单；'
      + '左栏**脚部**「面板」/「上帝视角」两条动作（走装机自己的 sidebar.footer.action 槽）。'
      + '面板本体一律嵌在 shell.overlay 浮层里，不跳转' + brandLine,
      '- 面板实况：在 ' + payload.present + ' / ' + payload.total + (missing.length ? '（缺：' + missing.join('、') + '）' : '（无缺）'),
      '- 口径/路由/品牌/验收读数：plugins/gbt-master/README.md · memory/2026-09-22-总面板接入.md',
      '- 读数 ' + at + '。重启后首次开口先确认「面板上下文已读 · ' + payload.present + '/' + payload.total + '」再继续正事。',
    ].join('\n')
  }

  function rememberSnapshot(payload) {
    try { snapshot = renderSnapshot(payload, stamp()) } catch (err) { /* 保底：保留上一份，不写半截 */ }
  }

  async function refreshSnapshot() {
    try {
      rememberSnapshot(await catalog())
    } catch (err) {
      snapshot = '【GBT小土豆V8 · 总面板】上下文读取失败：' + String(err && err.message ? err.message : err).slice(0, 160)
    }
    return snapshot
  }

  ctx.effect(() => ctx.systemPrompt.context({
    name: 'gbt-master-panels',
    order: 500,
    text: () => snapshot || '【GBT小土豆V8 · 总面板】上下文正在读取（宿主插件 gbt-potato-master-v9）。',
  }), 'gbt-master 面板上下文')

  void refreshSnapshot()
  const ticker = ctx.get('timer')
  if (ticker !== undefined && typeof ticker.interval === 'function') {
    ctx.effect(() => ticker.interval(() => { void refreshSnapshot() }, 90000), 'gbt-master 面板上下文定时刷新')
  }
  // ── 数字人工作流：唯一状态源（重启后不靠"我记得"，也不会被旧件带偏） ──────────
  //    状态只写一处：holo_pet/assets/digital-human/STATUS.json；别处不复述，只指向它。
  const DH_STATE_FILE = WORKSPACE + '/holo_pet/assets/digital-human/STATUS.json'
  let dhState = null

  function renderDhState(state, at) {
    const v = (state && state.current_asset_verdict) || {}
    // 🔴 2026-09-22 修：原来读的是 `v.readings.joints / .vertices / .textures_mb`，
    // 而状态源（`STATUS.json`，唯一真源）里是**平铺**的 `joints: 29 · verts: 16017 · textures_mb: 4.0`
    // ⇒ 注入给每一轮会话的上下文里长期写着「关节 undefined · 顶点 undefined · 贴图 undefinedMB」，
    // **看起来像资产读数坏了**，其实是读错了路径（报告层假绿的反面：把"好的"讲成"坏的"）。
    // 现在两种形态都认（有 `readings` 子对象就用它，否则用平铺字段），且**任何缺值都写「（未写）」**，
    // 绝不再把 `undefined` 注入上下文。
    const r = v.readings || v
    const pick = (names) => {
      for (let i = 0; i < names.length; i++) {
        const got = r[names[i]]
        if (got !== undefined && got !== null && got !== '') return got
      }
      return '（未写）'
    }
    const blocked = (state && state.blocked_on_owner) || []
    return [
      '【GBT小土豆V8 · 数字人工作流（唯一状态源现读）】',
      '- 阶段：' + String((state && state.stage) || '（未写）'),
      '- 现资产判定：' + String(v.verdict || '（未写）') + '（关节 ' + String(pick(['joints']))
        + ' · 顶点 ' + String(pick(['verts', 'vertices'])) + ' · 贴图 ' + String(pick(['textures_mb'])) + 'MB）',
      '- 下一步：' + String((state && state.next_step) || '（未写）'),
      '- 待 Owner 给：' + (blocked.length ? blocked.join(' · ') : '（无）'),
      '- 质量门限 / 自然度清单 / 证据路径 / 工具：见该文件全文',
      '- 读数 ' + at + '。重启后首次开口先确认「数字人工作流状态已读」再继续正事。',
    ].join('\n')
  }

  async function refreshDhState() {
    try {
      const text = await fs.readText(await fs.resolve(DH_STATE_FILE))
      dhState = renderDhState(JSON.parse(text), stamp())
    } catch (err) {
      // 读不到就如实说读不到，绝不猜内容
      dhState = '【GBT小土豆V8 · 数字人工作流】状态文件读不到：' + DH_STATE_FILE +
        '（' + String(err && err.message ? err.message : err).slice(0, 80) + '）—— 不猜内容，先请 Owner 确认。'
    }
    return dhState
  }

  ctx.effect(() => ctx.systemPrompt.context({
    name: 'gbt-digital-human',
    order: 501,
    text: () => dhState || '【GBT小土豆V8 · 数字人工作流】状态正在读取…',
  }), 'gbt-master 数字人工作流状态')

  void refreshDhState()
  if (ticker !== undefined && typeof ticker.interval === 'function') {
    ctx.effect(() => ticker.interval(() => { void refreshDhState() }, 90000), 'gbt-master 数字人工作流状态定时刷新')
  }

  // ── 排查台账：**进度唯一真源**（Owner 2026-09-25 令：「今天做到哪 / 哪没做 / 未清故障 /
  //    排查记录 + 时间点，重启之后自动读取」）──────────────────────────────────
  //    为什么要有（Owner 原话的意思）：一轮一轮修却不留账 ⇒ 重启后只能"我记得"，
  //    而"我记得"是本仓反复打过的假账。⇒ 台账只写一处：state/排查台账.json；
  //    这里**只渲染不编造**：缺字段写「（未写）」，读不到就如实说读不到。
  const LEDGER_FILE = WORKSPACE + '/state/排查台账.json'
  let ledgerState = null

  function renderLedger(led, at) {
    const w = (x) => (x === undefined || x === null || x === '') ? '（未写）' : String(x)
    const list = (arr, fmt, n) => (Array.isArray(arr) && arr.length)
      ? arr.slice(0, n).map(fmt).join(' · ')
      : '（无）'
    const notDone = list(led && led.not_done, (x) => w(x && x.id) + ' ' + w(x && x.what), 8)
    const faults = list(led && led.open_faults, (x) => w(x && x.id) + '[' + w(x && x.severity) + '] ' + w(x && x.what), 6)
    const ask = list(led && led.owner_decisions, (x) => w(x && x.id) + ' ' + w(x && x.ask), 6)
    const done = list(led && led.today_done, (x) => String(x).slice(0, 70), 4)
    const last = (Array.isArray(led && led.log) && led.log.length)
      ? led.log[led.log.length - 1] : null
    return [
      '【GBT小土豆V8 · 故障排查台账（唯一进度真源 · 现读）】',
      '- 台账时间点：' + w(led && led.updated_at) + '（已完成 ' + w(led && led.rounds_done) + ' 轮）',
      '- 现在在做：' + w(led && led.in_progress),
      '- 已做（近几条）：' + done,
      '- **没做**：' + notDone,
      '- **未清故障**：' + faults,
      '- **等你拍板**：' + ask,
      '- 最近一笔记录：' + (last ? (w(last.at) + ' ' + w(last.what)) : '（无）'),
      '- 全文：state/排查台账.json ｜ 详细账：output/blueprint-audit/生产推进-故障清单.md',
      '- **开机自检（一条命令跑完全部常设判据 + 两道闸）**：python tools/codex-scripts/boot-selfcheck.py',
      '- 读数 ' + at + '。重启后首次开口先确认「排查台账已读」并按台账继续，不许凭记忆接着干。',
    ].join('\n')
  }

  async function refreshLedger() {
    try {
      const text = await fs.readText(await fs.resolve(LEDGER_FILE))
      ledgerState = renderLedger(JSON.parse(text), stamp())
    } catch (err) {
      // 读不到就如实说读不到，绝不猜内容（与数字人状态同一条口径）
      ledgerState = '【GBT小土豆V8 · 故障排查台账】台账文件读不到：' + LEDGER_FILE +
        '（' + String(err && err.message ? err.message : err).slice(0, 80) + '）—— 不猜内容，先请 Owner 确认。'
    }
    return ledgerState
  }

  ctx.effect(() => ctx.systemPrompt.context({
    name: 'gbt-progress-ledger',
    order: 499,
    text: () => ledgerState || '【GBT小土豆V8 · 故障排查台账】台账正在读取…',
  }), 'gbt-master 排查台账')

  void refreshLedger()
  if (ticker !== undefined && typeof ticker.interval === 'function') {
    ctx.effect(() => ticker.interval(() => { void refreshLedger() }, 90000), 'gbt-master 排查台账定时刷新')
  }

  // ── 自愈：换代之后不再需要人按 F5 ──────────────────────────────────────────
  // 病根（踩了四轮才断对）：客户端模块 id 跟着换代变，而**已经开着的那张页面**拿的是旧包，
  // 服务端名册里旧 id 已下线 ⇒ 入口与品牌位整片消失，只能靠人按 F5。
  // 走的是 **DSH 官方公开的 `webServer.tapIndex(transform)`**（README 原文：
  //   "the escape hatch for markup no row expresses"，由 renderIndex 在**每次**首页渲染时应用）。
  //
  // 🔴 这里曾有一段"世代感知"的注入脚本，**它是错的，已删**（留着会误导后来的人）：
  //   它把 `EXPECT_GEN`（宿主自己的包名）**写进注入文本**，再拿页面的
  //   `documentElement.dataset.gbtGen` 跟它比。问题是——
  //   **注入文本是跟着首页一起发下去的**，页面一加载就固定成"当时那一代"的常量；
  //   对一张 v6 的页面来说，它自带的 GEN 是 v6、自己的戳也是 v6，**自比永远相等**
  //   ⇒ 自愈永不触发。实测：v6→v7 换代后 Owner 那张页面就卡在旧包上（左栏还是官方品牌行），
  //   而注入侧日志一切正常 —— **报告层是绿的，事实是没救到**（同类毛病的第五次）。
  //   更难堪的是：注入文本本身在包里，改自愈逻辑**又要换一代**，"自愈"每次修都得人按 F5。
  //
  // 现在断根成两条（别再退回旧写法）：
  //   ① 注入的只有**一行永不改变的标签**：`<script src="/gbt-master/heal.js" defer></script>`
  //      —— 逻辑住在磁盘上的 `lib/heal.js`，由上面的精确路由**每次现读**发出去。
  //   ② 判据改成 **"页面自己的戳" vs "宿主现报的 `plugin`"**（宿主那栏是现读的，任何旧页面
  //      都能认出自己旧了）；`dataset.gbtGen` 只由**当前这一代 bundle 的 apply()** 打上，
  //      所以它等于宿主现报的世代 ⇒ 这张页面跑的就是现在这一代。
  //   ⇒ 以后改自愈逻辑**只改 `lib/heal.js`**：不换代、不重装、不用求人按 F5。
  // 安全边界（写死，别放松）：只在 `/gbt-master` 答 200 才动 · 最多 3 次且间隔 ≥60s ·
  //   世代对上且入口在就清零 · `?gbt_noheal=1` 不介入 · 全程 try/catch 不定义全局。
  const HEAL_TAG = '<script src="' + BASE + '/heal.js" defer></script>'
  const HEAL_MARK = 'gbt-heal'

  // ⚠️ 必须**绑着 webServer 调**：`const tap = webServer.tapIndex` 会把方法摘下来，
  // 万一它内部用了 `this`（路由表是服务实例上的字段），裸调就会炸或静默不生效。
  if (!(webServer && typeof webServer.tapIndex === 'function')) {
    ctx.logger?.warn?.('gbt-master: webServer.tapIndex 不可用，跳过了自愈注入（换代后仍需手动刷新）')
  } else {
    ctx.effect(() => webServer.tapIndex((html) => {
      try {
        if (typeof html !== 'string' || html.indexOf(HEAL_MARK) >= 0) return html
        // 挂在 </body> 前；没有 body 就挂末尾（本来也不该发生）
        const at = html.lastIndexOf('</body>')
        return at < 0 ? html + HEAL_TAG : html.slice(0, at) + HEAL_TAG + html.slice(at)
      } catch (err) {
        return html
      }
    }), 'gbt-master 首页自愈注入')
  }

  ctx.logger?.info?.('gbt-master 总面板已装载 · 工作区 %s', WORKSPACE)
}
