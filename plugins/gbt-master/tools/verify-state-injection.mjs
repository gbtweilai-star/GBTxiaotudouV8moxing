/**
 * 进程外验证「数字人工作流唯一状态源」注入：
 *   正对照：真状态文件 → 注入文本里能看到 阶段 / 判定 / 下一步 / 待 Owner 给
 *   负对照：换一个不存在的工作区 → 必须如实报「状态文件读不到」，不许猜内容
 */
import { readFileSync, statSync, readdirSync } from 'node:fs'
import { pathToFileURL } from 'node:url'
import { join } from 'node:path'

const WS = 'C:/Users/ADMIN/Desktop/GBT小土豆V8'
const HOST = join(WS, 'plugins/gbt-master/lib/host.js')

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

async function run(workspace, tag) {
  const ctxs = []
  const mod = await import(pathToFileURL(HOST).href + '?tag=' + tag)
  mod.apply(makeCtx(ctxs), { workspace })
  console.log(`--- ${tag} · workspace=${workspace}`)
  console.log('注册的上下文:', ctxs.map((c) => `${c.name}(order ${c.order})`).join('  |  '))
  await new Promise((r) => setTimeout(r, 400))   // 让 apply 里的现读跑完
  for (const c of ctxs) {
    const t = typeof c.text === 'function' ? c.text() : c.text
    console.log(`【${c.name}】`)
    console.log(String(t).split('\n').map((l) => '   ' + l).join('\n'))
  }
}

await run(WS, '正对照')
console.log('')
await run(WS + '/__no_such_workspace__', '负对照')
