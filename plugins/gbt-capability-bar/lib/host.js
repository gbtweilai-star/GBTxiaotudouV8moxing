/**
 * GBT小土豆V8 · 能力栏 · 宿主半边（照 plugins/gbt-master/lib/host.js 的活样板写，**面更窄**）
 *
 * 干三件事，都只走 DSH 自己的公开面（`webServer.register`），不改 DSH 一行源码：
 *   ① `/gbt-capability-bar`            目录/健康 JSON（客户端据此判"接上没有" + 自报诊断读回）
 *   ② `/gbt-capability-bar/live.js`    **现读真源**的数据件（经典脚本、同源）：
 *                                     账本尾部有界窗口 → 每位三态证据；能量运行时；记录本读数
 *   ③ `/gbt-capability-bar/fs/*`       **只读白名单**：只放行
 *                                     `holo_pet_w3/capability-bar/**`（本页自身）
 *                                     + energy/capabilities 两个既有生成页（各 2 件）
 *                                     + 品牌标一台。别的一律 404（默认拒绝）。
 *
 * 与 gbt-master 的关系（**加装，不加锁**）：
 *   · 它占的左栏品牌两格 / 浮层 / footer 两格**一行都不动**；本件只**多注册** footer 一格 + 浮层一层，
 *     id 各自独立（`gbt-capbar` / `gbt-capbar-layer`），插槽是 list 语义 ⇒ 彼此不顶替。
 *   · **不注入首页**（不调 `webServer.tapIndex`）：gbt-master 的自愈器已占那一条路，两家都注会变双份刷新源。
 *     本件的页面只在**浮层 iframe 里**由 ② 的路由包装注入数据脚本（等价 gbt-master 的 W3 页包装法）。
 *   · **不发布 Cordis 服务、不占 fallback 席位、不写 systemPrompt 上下文**（少一个面就少一份互相干扰）。
 *
 * 只读纪律（写死）：
 *   · 本件**只读**：`readFileSync` / `fs.readBytes`；全文件**没有一处写盘**（判据 C9 机检）。
 *   · 不碰 `~/.dsh/**`（挂载点是主人的动作，本件从不自己动官方 APP 的落盘）。
 *   · 凭据只报掩码：能量通道的 `masked` 由数据件给，本件原样透传，不回显、不落第二份。
 *
 * 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
 */
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { readFileSync, statSync, openSync, readSync, closeSync } from 'node:fs'

const HERE = dirname(fileURLToPath(import.meta.url))
/**
 * 工作区根：优先取组合行显式声明的 `workspace`（部署事实属于组合层），
 * 没写才退回「跟着包走」的推导（上溯三级）；pnpm 的 file: 安装是硬链接，
 * import.meta.url 会落在 profile 的 node_modules 里 ⇒ 正式挂载写 config.workspace。
 */
const DERIVED = resolve(HERE, '..', '..', '..').replace(/\\/g, '/')
const FALLBACK = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const DEFAULT_WORKSPACE = DERIVED.indexOf('/node_modules/') < 0 ? DERIVED : FALLBACK

const BASE = '/gbt-capability-bar'
const FS_BASE = BASE + '/fs/'
const MAX_BYTES = 12 * 1024 * 1024

const PLUGIN = 'gbt-potato-capability-bar-v1'
const VERSION = '1.0.0'

/** 三态/四态类名 —— 与页面、判据（tools/codex-scripts/capability-bar-check.py）同一套说法 */
const STATE_CLASS = { 接上: 'on', 断连: 'off', 未探测: 'unk', 缺失: 'miss' }

/** 窗口口径（与 capability-bar-check.py 的常量**一字不差**；改就两边一起改） */
const WINDOW_HOURS = 24
const READ_CHUNK = 4 * 1024 * 1024
const READ_MAX = 24 * 1024 * 1024
const EVENTS = ['ok', 'denied', 'error']

/** 出网类型白名单（照 gbt-master；本件的白名单比它窄得多 —— 见 safeRel） */
const TYPES = {
  html: 'text/html; charset=utf-8',
  css: 'text/css; charset=utf-8',
  js: 'text/javascript; charset=utf-8',
  mjs: 'text/javascript; charset=utf-8',
  json: 'application/json; charset=utf-8',
  txt: 'text/plain; charset=utf-8',
  png: 'image/png',
  jpg: 'image/jpeg',
  jpeg: 'image/jpeg',
  webp: 'image/webp',
  svg: 'image/svg+xml',
  ico: 'image/x-icon',
}

/**
 * 🔴 只读白名单（**默认拒绝**）：目录前缀 1 条 + 精确文件 5 条，就这些。
 * 为什么不照 gbt-master 那样放整棵树：能力栏只需要它自己 + 两张既有详页 + 一个品牌标；
 * 面越窄，"碰了不该碰的"这种事故发生的机会越小。
 */
const ALLOW_PREFIX = ['holo_pet_w3/capability-bar/']
const ALLOW_FILES = [
  'holo_pet_w3/energy/index.html',
  'holo_pet_w3/energy/energy-data.js',
  'holo_pet_w3/capabilities/index.html',
  'holo_pet_w3/capabilities/capabilities-data.js',
  'assets/brand/logo-potato-64.png',
]

/** 真源（只读） */
const SRC = {
  bindings: 'state/cap-bindings.json',
  audit: 'state/capability-audit.json',
  ledger: 'gbt_allinone/store/audit.jsonl',
  runtime: 'gbt_allinone/store/key_gateway/runtime.json',
  logbook: 'state/logbook.jsonl',
}

function extOf(p) {
  const i = p.lastIndexOf('.')
  return i < 0 ? '' : p.slice(i + 1).toLowerCase()
}

function nowIso() {
  const d = new Date()
  const p = (n) => String(n).padStart(2, '0')
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + 'T'
    + p(d.getHours()) + ':' + p(d.getMinutes()) + ':' + p(d.getSeconds())
}

export const inject = ['fs', 'webServer']

export function apply(ctx, config) {
  const cfg = (config && typeof config === 'object')
    ? config
    : (ctx.config && typeof ctx.config === 'object' ? ctx.config : {})
  const declared = typeof cfg.workspace === 'string' ? cfg.workspace.trim() : ''
  const WORKSPACE = (declared || DEFAULT_WORKSPACE).replace(/\\/g, '/').replace(/\/+$/, '')
  const fs = ctx.fs
  const webServer = ctx.webServer

  function readText(rel, cap) {
    try {
      const buf = readFileSync(WORKSPACE + '/' + rel)
      if (cap && buf.length > cap) return null
      return buf.toString('utf8')
    } catch (err) {
      return null
    }
  }

  function readJson(rel) {
    const t = readText(rel)
    if (t === null) return null
    try { return JSON.parse(t) } catch (err) { return null }
  }

  /** 在册能力位名（现读注册表台账；读不到就返回 null —— 不拿空集合冒充"零个"） */
  function capNames() {
    const b = readJson(SRC.bindings)
    if (!b || !Array.isArray(b.caps)) return null
    return b.caps.map((c) => String(c.name))
  }

  /**
   * 账本尾部**有界回读**：近 WINDOW_HOURS 小时、最多 READ_MAX 字节。
   * 与 tools/codex-scripts/capability-bar-check.py::read_evidence 是同一算法（口径必须一致）。
   * 同步读（openSync/readSync 小切片）—— 结果有 60s 缓存（见 liveBody）。
   */
  function readEvidence(names) {
    const out = {
      at: nowIso(), window_hours: WINDOW_HOURS, file_bytes: 0, read_bytes: 0,
      capped: false, reached_cutoff: false, records: 0, map: {}, ledger: SRC.ledger,
    }
    const path = WORKSPACE + '/' + SRC.ledger
    let fd = null
    try {
      const size = statSync(path).size
      out.file_bytes = size
      const cutoff = Date.now() / 1000 - WINDOW_HOURS * 3600
      fd = openSync(path, 'r')
      let end = size
      let text = ''
      let read = 0
      while (end > 0 && read < READ_MAX) {
        const start = Math.max(0, end - READ_CHUNK)
        const len = end - start
        const buf = Buffer.allocUnsafe(len)
        readSync(fd, buf, 0, len, start)
        const seg = buf.toString('utf8')
        read += len
        text = seg + text
        // 这一段的**最早一条**时间戳：过了 cutoff 就停（更早的不要了）
        let firstTs = null
        for (const ln of seg.split('\n')) {
          if (!ln.trim()) continue
          try { firstTs = JSON.parse(ln).ts; break } catch (e) { /* 坏行跳过，找下一条 */ }
        }
        if (typeof firstTs === 'number' && firstTs < cutoff) { out.reached_cutoff = true; break }
        end = start
      }
      closeSync(fd); fd = null
      out.read_bytes = read
      out.capped = !out.reached_cutoff && read >= READ_MAX
      if (read < size) {
        const nl = text.indexOf('\n')
        if (nl >= 0) text = text.slice(nl + 1)     // 回读是从尾部拼的 ⇒ 掐掉可能截半的首行
      }
      const last = {}
      let records = 0
      for (const ln of text.split('\n')) {
        if (!ln.trim()) continue
        let r = null
        try { r = JSON.parse(ln) } catch (e) { continue }
        if (EVENTS.indexOf(r.event) < 0) continue
        const meta = r.meta || {}
        const kind = String(meta.kind || '')
        if (names.indexOf(kind) < 0) continue         // 不在册的 kind 不收（不冒充）
        if (!(typeof r.ts === 'number' && r.ts >= cutoff)) continue
        records += 1
        const iso = String(r.iso || '')
        const cur = last[kind]
        if (cur === undefined || iso > cur.iso) {
          last[kind] = { iso, s: r.event, raw: JSON.stringify(meta).slice(0, 160) }
        }
      }
      out.records = records
      out.map = last
    } catch (err) {
      out.error = String((err && err.message) || err).slice(0, 160)
      if (fd !== null) { try { closeSync(fd) } catch (e) { /* 已关或没开成 */ } }
    }
    return out
  }

  /** 现读数据件（经典脚本）：页面**零远端取数**，一切从这一份来 */
  function buildLive() {
    const names = capNames()
    const b = readJson(SRC.bindings)
    const a = readJson(SRC.audit)
    const out = {
      at: nowIso(),
      readonly: true,
      plugin: PLUGIN,
      version: VERSION,
      state_class: STATE_CLASS,
      sources: {
        bindings: { file: SRC.bindings, at: (b && b.generated_at) || null },
        audit: { file: SRC.audit, at: (a && a.generated_at) || null },
        ledger: { file: SRC.ledger, at: null },
        runtime: { file: SRC.runtime, at: null },
        logbook: { file: SRC.logbook, at: null },
      },
    }
    if (names === null) {
      out.evidence = { error: '绑定台账读不到：' + SRC.bindings + ' —— 不判定任何位的通断' }
    } else {
      const ev = readEvidence(names)
      out.evidence = ev
      out.sources.ledger.at = ev.at
    }
    const rt = readJson(SRC.runtime)
    if (rt === null) {
      out.energy_runtime = { ok: false, error: '运行时文件读不到（不编）：' + SRC.runtime }
    } else {
      out.energy_runtime = {
        ok: true, at: nowIso(), file: SRC.runtime,
        active: rt.active || rt.current || null,
        switches: (rt.switches === undefined ? null : rt.switches),
        alive: (rt.alive === undefined ? null : rt.alive),
        total: (rt.total === undefined ? null : rt.total),
      }
    }
    // 记录本：只报**文件级**读数（条数 / 末条 / 末 hash）。
    // 🔴 链的自洽性判定归 `logbook.py verify`（那是它唯一的判据）——本件不替它下结论。
    try {
      const buf = readFileSync(WORKSPACE + '/' + SRC.logbook)
      const lines = buf.toString('utf8').split('\n').filter((x) => x.trim())
      let last = null
      for (let i = lines.length - 1; i >= 0; i--) {
        try { last = JSON.parse(lines[i]); break } catch (e) { /* 坏行往前找 */ }
      }
      out.logbook = {
        ok: true, at: nowIso(), file: SRC.logbook, file_bytes: statSync(WORKSPACE + '/' + SRC.logbook).size,
        lines: lines.length,
        last_n: last ? last.n : null, last_ts: last ? last.ts : null,
        last_kind: last ? last.kind : null, last_hash: last ? last.hash : null,
        verify: 'py -3.14 tools/codex-scripts/logbook.py verify',
      }
    } catch (err) {
      out.logbook = { ok: false, error: '记录本读不到：' + String((err && err.message) || err).slice(0, 120) }
    }
    return out
  }

  // 现读件缓存 60s：账本回读要 16 MB 上下，每请求都读一次是拿性能换一个不必要的新鲜
  let liveCache = { at: 0, body: null }
  function liveBody() {
    const t = Date.now()
    if (liveCache.body === null || t - liveCache.at > 60000) {
      let payload = null
      try { payload = buildLive() } catch (err) {
        payload = { at: nowIso(), readonly: true, error: String((err && err.message) || err).slice(0, 200) }
      }
      liveCache = { at: t, body: '/* gbt-capability-bar · 宿主现读数据件（只读）：账本尾部有界窗口 + 能量运行时 + 记录本读数。\n'
        + '   页面**不做任何远端取数**；票面时刻 at 就是这份数据的时刻，按它判断新鲜度。 */\n'
        + 'window.GBT_CAPBAR_LIVE = ' + JSON.stringify(payload) + ';\n' }
    }
    return liveCache.body
  }

  function sendJson(res, code, value) {
    const body = JSON.stringify(value)
    const bytes = Buffer.byteLength(body, 'utf8')       // 按**字节**报头（中文多时字符数会小于字节数）
    res.writeHead(code, {
      'content-type': TYPES.json,
      'content-length': String(bytes),
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    })
    res.end(body)
  }

  function sendText(res, code, text, type) {
    res.writeHead(code, {
      'content-type': type || TYPES.txt,
      'content-length': String(Buffer.byteLength(text, 'utf8')),
      'cache-control': 'no-store',
      'x-content-type-options': 'nosniff',
    })
    res.end(text)
  }

  // ── ① 目录/健康（精确路由）：客户端读它，也用来一眼判"接上没有" ──────────────
  var clientDiag = null
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE,
    handler: (req, res) => {
      try {
        const b = readJson(SRC.bindings)
        const a = readJson(SRC.audit)
        sendJson(res, 200, {
          ok: true,
          plugin: PLUGIN,
          version: VERSION,
          readonly: true,
          workspace: WORKSPACE,
          page: FS_BASE + 'holo_pet_w3/capability-bar/index.html',
          slots: ['sidebar.footer.action（左栏脚部一格 · id gbt-capbar）', 'shell.overlay（浮层内嵌 · id gbt-capbar-layer）'],
          counts: {
            caps: b && b.counts ? b.counts.caps : null,
            tentacle_domains: b && b.counts ? b.counts.tentacle_domains : null,
            energy_channels: b && b.counts ? b.counts.energy_channels : null,
            energy_alive: b && b.counts ? b.counts.energy_alive : null,
            audit_total: a && a.counts ? a.counts.total : null,
          },
          sources: {
            cap_bindings: { file: SRC.bindings, at: (b && b.generated_at) || null },
            capability_audit: { file: SRC.audit, at: (a && a.generated_at) || null },
            audit_ledger: { file: SRC.ledger, window_hours: WINDOW_HOURS, read_max: READ_MAX },
          },
          // 浏览器半边的自报（POST /gbt-capability-bar/diag）：两格插槽到底注册上没有、报了什么错
          clientDiag: clientDiag || null,
          note: '只读；不注入首页；不改 DSH 一行源码；与 gbt-master 各自独立（本件只多注册 footer 一格 + 浮层一层）',
        })
      } catch (err) {
        sendJson(res, 500, { ok: false, error: String((err && err.message) || err).slice(0, 200) })
      }
    },
  }), 'gbt-capability-bar 目录路由')

  // ── ② 现读数据件（精确路由）：经典脚本，页面零远端取数 ──────────────────────
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/live.js',
    handler: (req, res) => {
      sendText(res, 200, liveBody(), TYPES.js)
    },
  }), 'gbt-capability-bar 现读数据件（宿主读账本尾部有界窗口）')

  // ── ③ 页面包装（精确路由）：只做一件事 —— 在第一个 <script> 前注入现读数据脚本 ──
  // 为什么不直接改页面文件：Electron（file://）与本插件（同源 HTTP）读的是**同一份源文件**，
  // 注入只在宿主下发生 ⇒ **零分叉**（这句是这条路由存在的全部理由，照 gbt-master 的 W3 页包装法）。
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: FS_BASE + 'holo_pet_w3/capability-bar/index.html',
    handler: async (req, res) => {
      let html = null
      try { html = readFileSync(WORKSPACE + '/holo_pet_w3/capability-bar/index.html', 'utf8') } catch (err) { html = null }
      if (html === null) {
        sendText(res, 404, 'GBT能力栏: 页面读不到 · holo_pet_w3/capability-bar/index.html')
        return
      }
      const tag = '<script src="' + BASE + '/live.js"></script>'
      if (html.indexOf(tag) === -1) {
        const first = html.search(/<script\b/i)
        if (first >= 0) html = html.slice(0, first) + tag + '\n' + html.slice(first)
        else if (html.indexOf('</body>') >= 0) html = html.replace('</body>', tag + '\n</body>')
        else html = html + '\n' + tag + '\n'
      }
      sendText(res, 200, html, TYPES.html)
    },
  }), 'gbt-capability-bar 页面包装（宿主内注入现读数据）')

  // ── ③b 只读白名单静态路由（前缀**不带尾斜杠**：DSH 的 prefix 匹配是 === || startsWith(prefix + '/')）──
  function safeRel(raw) {
    let rel = String(raw || '').replace(/\\/g, '/')
    while (rel.charAt(0) === '/') rel = rel.slice(1)
    if (rel === '' || rel.length > 400) return null
    const parts = rel.split('/')
    for (let i = 0; i < parts.length; i++) {
      const seg = parts[i]
      if (seg === '' || seg === '.' || seg === '..') return null
      if (seg.charAt(0) === '.') return null
    }
    if (TYPES[extOf(rel)] === undefined) return null
    const okPrefix = ALLOW_PREFIX.some((p) => rel.indexOf(p) === 0)
    const okFile = ALLOW_FILES.indexOf(rel) >= 0
    if (!okPrefix && !okFile) return null            // 🔴 默认拒绝：名单之外，一个字节都不发
    return parts.join('/')
  }

  ctx.effect(() => webServer.register({
    kind: 'prefix',
    path: FS_BASE.slice(0, -1),
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
        sendText(res, 404, 'GBT能力栏: 该路径不在只读白名单内（本插件只放行能力栏自身 + 两张既有详页 + 品牌标）· ' + String(req.url || '').slice(0, 120))
        return
      }
      try {
        const bytes = await fs.readBytes(await fs.resolve(WORKSPACE + '/' + rel), undefined, MAX_BYTES)
        res.writeHead(200, {
          'content-type': TYPES[extOf(rel)] || 'application/octet-stream',
          'content-length': String(bytes.length),
          'cache-control': 'no-store',
          'x-content-type-options': 'nosniff',
        })
        res.end(Buffer.from(bytes))
      } catch (err) {
        sendText(res, 404, 'GBT能力栏: 文件不在盘上 · ' + rel)
      }
    },
  }), 'gbt-capability-bar 只读白名单静态路由')

  // ── ④ 浏览器半边自报（POST）：两格插槽注册成没成、报了什么错（不与 gbt-master 的 /diag 抢）──
  ctx.effect(() => webServer.register({
    kind: 'exact',
    path: BASE + '/diag',
    handler: (req, res) => {
      if (String(req.method || '').toUpperCase() !== 'POST') {
        sendJson(res, 200, { ok: true, note: 'POST {gen,diag}；读回查 /gbt-capability-bar 的 clientDiag 字段' })
        return
      }
      let raw = ''
      req.on('data', (c) => { raw += c; if (raw.length > 8192) raw = raw.slice(0, 8192) })
      req.on('end', () => {
        try {
          const body = JSON.parse(raw || '{}')
          clientDiag = {
            at: nowIso(),
            gen: String(body.gen || '').slice(0, 60),
            diag: Array.isArray(body.diag) ? body.diag.slice(0, 12).map((s) => String(s).slice(0, 120)) : [],
          }
        } catch (err) {
          clientDiag = { at: nowIso(), gen: '', diag: ['宿主收到非 JSON 自报：' + String((err && err.message) || err).slice(0, 80)] }
        }
        sendJson(res, 200, { ok: true })
      })
    },
  }), 'gbt-capability-bar 浏览器自报诊断路由')

  ctx.logger?.info?.('gbt-capability-bar 能力栏已装载 · 工作区 %s', WORKSPACE)
}
