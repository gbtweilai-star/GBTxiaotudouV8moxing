/**
 * 注入上下文的**报告层闸**（宿主半边）—— 现读 `lib/host.js` 里两个渲染函数，用真状态源跑一遍。
 *
 * 为什么要它（2026-09-22 实测踩到两处，都是"注入给每一轮会话的文字在骗人"）：
 *   ① `renderSnapshot` 曾**写死**"左栏品牌行＝土豆 Logo + GBT小土豆V8" —— 那是"部署就绪"，
 *      不是"已生效"（同一份 payload 里的 `clientDiag` 就能证明页面还没加载本代）。
 *   ② `renderDhState` 曾读 `v.readings.joints/.vertices` 而状态源里是**平铺**的
 *      `joints/verts` ⇒ 注入文本长期写着「关节 undefined · 顶点 undefined · 贴图 undefinedMB」。
 *   两处都不是崩溃型 bug，**不会让任何命令报错**，但会让每一轮重启的模型读错事实 ——
 *   所以必须有闸：**注入文本里不许出现 `undefined`，且数字必须与状态源一致**。
 *
 * 做法：从 `lib/host.js` 源码里**抽函数体**（不 import 插件、不起服务、不碰运行中的进程），
 * 用 `new Function` 组装后喂真数据跑。抽不到函数 = 直接失败（说明有人改了函数名，闸要跟着改）。
 *
 * 用法：node plugins/gbt-master/tools/verify-context-blocks.mjs
 * 退出码：0 = 三段都对；1 = 有假绿/假红。
 */
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(HERE, '..', '..', '..')            // <仓>/
const HOST = join(ROOT, 'plugins', 'gbt-master', 'lib', 'host.js')
const STATUS = join(ROOT, 'holo_pet', 'assets', 'digital-human', 'STATUS.json')

const problems = []
const src = readFileSync(HOST, 'utf8')

function extract(name) {
  const at = src.indexOf('function ' + name + '(')
  if (at < 0) return null
  // 从函数头扫到与之配对的收尾 `\n  }`（这两个函数都在 apply() 里，缩进两级）
  const rest = src.slice(at)
  const end = rest.indexOf('\n  }')
  if (end < 0) return null
  const decl = rest.slice(0, end + 4)
  // ⚠️ 参数名要**从声明里现读**：第一版写死成 `state, at`，抽 `renderSnapshot(payload, at)` 时
  // 直接 `ReferenceError: payload is not defined` —— 闸自己先炸了（这版修掉）。
  const params = decl.slice(decl.indexOf('(') + 1, decl.indexOf(')'))
    .split(',').map((s) => s.trim()).filter(Boolean)
  const body = decl.slice(decl.indexOf('{') + 1, decl.lastIndexOf('}'))
  return new Function(...params, body)
}

// ── ① 数字人状态块：数字必须与状态源一致，且不许出现 undefined ──────────────
const fnDh = extract('renderDhState')
if (fnDh === null) {
  problems.push('抽不到 renderDhState（函数被改名或挪走了？闸要跟着改）')
} else {
  const state = JSON.parse(readFileSync(STATUS, 'utf8'))
  const text = fnDh(state, 'SELFTEST')
  const v = state.current_asset_verdict || {}
  const r = v.readings || v
  if (text.includes('undefined')) problems.push('数字人状态块里出现了 undefined')
  const wantJoints = String(r.joints)
  const wantVerts = String(r.verts !== undefined ? r.verts : r.vertices)
  if (!text.includes('关节 ' + wantJoints)) problems.push('关节数与状态源不一致（状态源 ' + wantJoints + '）')
  if (!text.includes('顶点 ' + wantVerts)) problems.push('顶点数与状态源不一致（状态源 ' + wantVerts + '）')
  if (!text.includes('贴图 ' + String(r.textures_mb))) problems.push('贴图数与状态源不一致')
  // 缺值必须写「（未写）」，不许留空、不许 undefined
  const empty = fnDh({}, 'SELFTEST')
  if (empty.includes('undefined')) problems.push('状态源缺字段时仍注入了 undefined')
  if (!empty.includes('（未写）')) problems.push('状态源缺字段时没有写「（未写）」')
  console.log('① 数字人状态块：' + text.split('\n')[2].slice(0, 96))
}

// ── ② 面板上下文块：品牌行必须随 clientDiag 变，且不许出现 undefined ──────────
const fnSnap = extract('renderSnapshot')
if (fnSnap === null) {
  problems.push('抽不到 renderSnapshot（函数被改名或挪走了？闸要跟着改）')
} else {
  const base = { total: 12, present: 12, panels: [{ name: 'x', exists: true }] }
  const branch = (cd) => fnSnap({ ...base, clientDiag: cd }, 'SELFTEST').split('\n')[1]
  const bNull = branch(null)
  const bOk = branch({ gen: 'gbt-potato-master-v9', at: 'SELFTEST' })
  const bOld = branch({ gen: 'gbt-potato-master-v6', at: 'SELFTEST' })
  for (const [tag, line] of [['null', bNull], ['本代', bOk], ['异代', bOld]]) {
    if (line.includes('undefined')) problems.push('面板上下文块（' + tag + '）里出现了 undefined')
  }
  if (!bNull.includes('尚未在任何页面生效')) problems.push('clientDiag=null 时没说"尚未生效"（又写成已生效了？）')
  if (!bOk.includes('已按本代加载')) problems.push('clientDiag 命中本代时没说"已加载"')
  if (!bOld.includes('与本代不符')) problems.push('clientDiag 是异代时没如实报"不符"')
  if (bNull === bOk || bOk === bOld) problems.push('三种情形的说法没有区分开（等于又写死了）')
  console.log('② 面板上下文块：三分支互不相同 ✅')
}

console.log(JSON.stringify({ verdict: problems.length ? 'FAIL' : 'PASS', problems }, null, 1))
process.exit(problems.length ? 1 : 0)
