/**
 * **装机副本漂移闸**（宿主插件）—— 工作区源稿 vs DSH profile 里真正被加载的那份，逐文件比字节。
 *
 * 为什么必须有它（2026-09-22 现读实锤，属"改了不生效"那一类）：
 *   DSH 按组合行的 `name:`（`gbt-potato-master-v9`）去 **profile 的 node_modules** 里解析包，
 *   而那份是 `file:` 依赖装出来的**副本**，不是链接。实测：
 *     · 源 `lib/host.js` = 30,378 B / 549 行，装机副本 = 27,867 B / 516 行（**少 33 行、我的两处修正一行都没有**）
 *     · 源 `lib/heal.js` 有 `setInterval`（60s 复查），装机副本 **0 次**
 *     · 源 `tools/verify-context-blocks.mjs` 装机副本里**根本没有**
 *   ⇒ 光改工作区源稿，**重启也不会生效**（重启加载的还是那份旧副本）。
 *   这类漂移不会报错、不会红页，只会"看起来改了、其实没改"（本会话第三次撞同一族毛病：
 *   技能根漂移 → 注入上下文假绿 → 装机副本漂移，**根都是"源与在跑的那份不是一份"**）。
 *
 * 顺带报一个已知错标：profile 依赖里 `gbt-potato-master-v8` 指向的就是 v9 那个目录
 *   ⇒ `node_modules/gbt-potato-master-v8/package.json` 的 `name` 是 **v9**（specifier 与包名不符）。
 *   加载器按"解析出来的 manifest 包名"认浏览器模块，所以这条**等重启后应清掉**（本次只报不动，见 README §4.8）。
 *
 * 用法：node plugins/gbt-master/tools/verify-installed-copy.mjs          # 只核（改了源稿就该红）
 *       node plugins/gbt-master/tools/verify-installed-copy.mjs --fix    # 把源稿同步进装机副本
 * 退出码：0 = 每个装机副本都与源稿逐字节一致；1 = 有漂移。
 */
import { readFileSync, readdirSync, statSync, existsSync, mkdirSync, copyFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { fileURLToPath } from 'node:url'
import { dirname, join, resolve, relative } from 'node:path'
import { homedir } from 'node:os'

const HERE = dirname(fileURLToPath(import.meta.url))
const SOURCE = resolve(HERE, '..')                       // plugins/gbt-master
const PROFILES = join(homedir(), '.dsh', 'profiles')
const SKIP = new Set(['node_modules', '.git'])
// `--fix`：把源稿同步进装机副本（**改了源稿就得跑一次**，否则闸会一直红 —— 这正是它的用处）。
const FIX = process.argv.includes('--fix')

const sha = (p) => createHash('sha256').update(readFileSync(p)).digest('hex').toUpperCase()
function walk(root, base = root, out = []) {
  for (const name of readdirSync(root)) {
    if (SKIP.has(name)) continue
    const p = join(root, name)
    const st = statSync(p)
    if (st.isDirectory()) walk(p, base, out)
    else out.push(relative(base, p).replace(/\\/g, '/'))
  }
  return out
}

const problems = []
const notes = []
const sourceFiles = walk(SOURCE)

if (!existsSync(PROFILES)) {
  problems.push('找不到 profile 目录：' + PROFILES)
} else {
  for (const profile of readdirSync(PROFILES)) {
    const nm = join(PROFILES, profile, 'node_modules')
    if (!existsSync(nm)) continue
    for (const dir of readdirSync(nm)) {
      if (!/^gbt-potato-master-v\d+$/.test(dir)) continue
      const pkgPath = join(nm, dir, 'package.json')
      if (!existsSync(pkgPath)) continue
      let pkg
      try { pkg = JSON.parse(readFileSync(pkgPath, 'utf8')) } catch { continue }
      // 只核"指向本插件源码"的那几份（compat 壳是独立包，不核）
      const isOurs = pkg.name === 'gbt-potato-master-v9' || dir === 'gbt-potato-master-v9'
      if (!isOurs) continue
      if (pkg.name !== dir) {
        notes.push(`[${profile}] node_modules/${dir} 的 package.json name=${pkg.name}（specifier 与包名不符）`
          + ' ⇒ 重启后应清掉这条依赖（README §4.8）')
      }
      const inst = join(nm, dir)
      if (FIX) {
        for (const f of sourceFiles) {
          const target = join(inst, f)
          mkdirSync(dirname(target), { recursive: true })
          copyFileSync(join(SOURCE, f), target)
        }
        console.log(`🔧 [${profile}] ${dir}：已从源稿同步 ${sourceFiles.length} 个文件`)
      }
      const instFiles = walk(inst)
      const missing = sourceFiles.filter((f) => !instFiles.includes(f))
      const extra = instFiles.filter((f) => !sourceFiles.includes(f))
      const differ = sourceFiles.filter((f) => instFiles.includes(f)
        && sha(join(SOURCE, f)) !== sha(join(inst, f)))
      if (missing.length || extra.length || differ.length) {
        problems.push(`[${profile}] ${dir} 与源稿不一致`
          + `（源缺 ${extra.length} · 装机缺 ${missing.length} · 内容不同 ${differ.length}）`
          + (differ.length ? '：' + differ.slice(0, 4).join('、') : '')
          + (missing.length ? '；装机缺：' + missing.slice(0, 4).join('、') : ''))
      } else {
        console.log(`✅ [${profile}] ${dir}：${sourceFiles.length} 个文件与源稿逐字节一致`)
      }
    }
  }
}

for (const n of notes) console.log('⚠ ' + n)
if (problems.length) {
  for (const p of problems) console.log('🔴 ' + p)
  console.log('  修法：把源稿 `plugins/gbt-master/**` 同步到该装机目录（或重跑 profile 的 npm install）。')
}
console.log(JSON.stringify({ verdict: problems.length ? 'FAIL' : 'PASS', problems, notes }, null, 1))
process.exit(problems.length ? 1 : 0)
