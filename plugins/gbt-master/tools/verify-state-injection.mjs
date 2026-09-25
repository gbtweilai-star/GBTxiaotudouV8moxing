/**
 * 进程外验证「注入上下文」三块（面板 / 数字人唯一状态源 / **排查台账**）：
 *   正对照：真状态文件 → 注入文本里能看到 阶段 / 判定 / 下一步 / 待 Owner 给，
 *           台账块能看到 时间点 / 没做 / 未清故障 / 等你拍板
 *   负对照：换一个不存在的工作区 → 必须如实报「状态文件读不到」，不许猜内容
 *
 * 🔴 2026-09-25 修**一处名不副实**：验收单 ④ 项写的是「**装机副本**实跑」，
 *    而本脚本原来 import 的是**工作区源稿**（`WS/plugins/.../host.js`）——
 *    ⇒ 它**测不出装机副本漂移**（当天实测：装机副本的 host.js 比源稿少 3,309 B，本脚本照样绿）。
 *    现在两个都跑：源稿（开发态）+ **装机副本**（真正被加载的那份，若存在），
 *    并打印 `HOST=` 行标明跑的是谁 —— 让"实跑的是哪一份"**看得见**。
 */
import { readFileSync, statSync, readdirSync, existsSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import { join } from 'node:path'
import { homedir } from 'node:os'

const WS = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const SRC = join(WS, 'plugins/gbt-master/lib/host.js')
const INSTALLED = join(homedir(), '.dsh/profiles/web/node_modules/gbt-potato-master-v9/lib/host.js')
// `--json`：机读模式（给 audit-injection-honesty.py 这类审计器用）——**同一套 ctx 假件**，不另造第二份。
const AS_JSON = process.argv.includes('--json')
const RESULTS = []

function makeCtx(ctxs) {
  return {
    fs: {
      async resolve(p) { return { targetKey: String(p).replace(/\\/g, '/'), displayPath: String(p) } },
      async stat(t) { try { const s = statSync(t.targetKey); return { type: s.isDirectory() ? 'directory' : 'file', size: s.size, version: 'v1' } } catch { return undefined } },
      async readBytes(t, sig, max) { const b = readFileSync(t.targetKey); if (b.length > max) throw new Error('FS_TOO_LARGE'); return new Uint8Array(b) },
      async readText(t) { return readFileSync(t.targetKey, 'utf8') },
      async listDir(t) { return readdirSync(t.targetKey, { withFileTypes: true }).map((e) => ({ name: e.name, type: e.isDirectory() ? 'directory' : 'file', target: { targetKey: t.targetKey + '/' + e.name, displayPath: '' } })) },
      async writeText() { return { operation: 'update', version: 'v1', before: null, after: '' } },
    },
    webServer: { register() { return () => {} } },
    systemPrompt: { context(c) { ctxs.push(c); return () => {} } },
    logger: { info() {} },
    effect(fn) { return fn() },
    get(name) { return name === 'timer' ? undefined : this[name] },
  }
}

async function run(hostPath, workspace, tag) {
  const ctxs = []
  const mod = await import(pathToFileURL(hostPath).href + '?tag=' + tag + '&ws=' + encodeURIComponent(workspace))
  const say = AS_JSON ? () => {} : (...a) => console.log(...a)
  say(`--- ${tag} · workspace=${workspace}`)
  say(`HOST=${hostPath}`)
  mod.apply(makeCtx(ctxs), { workspace })
  say('注册的上下文:', ctxs.map((c) => `${c.name}(order ${c.order})`).join('  |  '))
  await new Promise((r) => setTimeout(r, 400))   // 让 apply 里的现读跑完
  const blocks = []
  for (const c of ctxs) {
    const t = typeof c.text === 'function' ? c.text() : c.text
    blocks.push({ name: c.name, order: c.order, text: String(t) })
    say(`【${c.name}】`)
    say(String(t).split('\n').map((l) => '   ' + l).join('\n'))
  }
  RESULTS.push({ tag, host: hostPath, workspace, blocks })
}

await run(SRC, WS, '正对照·源稿')
if (existsSync(INSTALLED)) {
  console.log('')
  await run(INSTALLED, WS, '正对照·装机副本')
} else {
  console.log('')
  console.log(`⚠ 装机副本不在（${INSTALLED}）⇒ 只验了源稿；跑 verify-installed-copy.mjs --fix 同步后再验`)
}
console.log('')
await run(SRC, WS + '/__no_such_workspace__', '负对照')
if (AS_JSON) console.log(JSON.stringify({ runs: RESULTS }))
