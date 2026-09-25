/**
 * 宿主插件的**三道门一起跑**（一条命令，缺一条都算没验）。
 *
 *  ① `verify-client-apply.mjs`   —— 浏览器半边：bundleId / 6 个插槽注册 / 品牌两格 / 自报诊断挂钩 / CSS 防挤
 *  ② `verify-context-blocks.mjs` —— 注入上下文：不许出现 `undefined` · 数字必须与状态源一致 · 品牌三分支互不相同
 *  ③ `verify-installed-copy.mjs` —— 装机副本：源稿 vs DSH profile 里**真正被加载**的那份逐文件同哈希
 *
 * 为什么要把三条并成一条：本会话反复栽在"只跑了一条就下结论"（覆盖 / 同哈希 / 映射各管一段）。
 * 用法：node plugins/gbt-master/tools/verify-all.mjs
 * 退出码：0 = 三门全过；1 = 至少一门没过。
 */
import { spawnSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const HERE = dirname(fileURLToPath(import.meta.url))
const GATES = [
  ['① 浏览器半边（bundle / 插槽 / 品牌 / 诊断挂钩 / CSS）', 'verify-client-apply.mjs'],
  ['② 注入上下文（不许 undefined · 数字同源 · 品牌三分支）', 'verify-context-blocks.mjs'],
  ['③ 装机副本（源稿 vs DSH 真正加载的那份）', 'verify-installed-copy.mjs'],
]

const failed = []
for (const [label, file] of GATES) {
  const r = spawnSync(process.execPath, [join(HERE, file)], { encoding: 'utf8' })
  const out = (r.stdout || '') + (r.stderr || '')
  const verdict = /"verdict":\s*"PASS"/.test(out) || /^PASS/m.test(out)
  const ok = r.status === 0 && verdict
  console.log(`${ok ? '✅' : '🔴'} ${label}${ok ? '：PASS' : '：FAIL（exit ' + r.status + '）'}`)
  if (!ok) {
    failed.push(label)
    console.log(out.split('\n').filter((l) => /🔴|FAIL|problems|错误|Error/.test(l)).slice(0, 8)
      .map((l) => '     ' + l.trim()).join('\n'))
  }
}
console.log(failed.length
  ? `结论：宿主插件体检 **不通过** —— ${failed.length} 门没过：${failed.join(' · ')}`
  : '结论：宿主插件三门全过（浏览器半边 · 注入上下文 · 装机副本）')
process.exit(failed.length ? 1 : 0)
