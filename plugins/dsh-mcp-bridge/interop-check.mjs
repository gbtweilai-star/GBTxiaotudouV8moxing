// GBT小土豆V8 · DSH MCP 桥 · **官方同款 SDK 互操作自证**
//
// 为什么非做不可（这是本方案最大的技术风险）：`server.py` 按 MCP 规范手写，
// 从没和**官方那份 SDK** 对打过 —— 而官方 APP 侧 `@deepseek-ai/dsh-mcp-client`
// 用的就是 `@modelcontextprotocol/sdk` 的 `StdioClientTransport`。
// 本件用**本机现装的那份 SDK**（`~/.dsh/profiles/node_modules/@modelcontextprotocol/sdk`）
// 真连我们的桥：握手 → tools/list → tools/call(alerts) → 写类负对照。
//
// 判据（全过打 `INTEROP OK`，退出码 0；否则 `INTEROP FAIL`，退出码 1）：
//   A. connect 成功（initialize 走通）
//   B. listTools 里有 run_task / alerts / selfscan / capability_status
//   C. 没有 logbook_append（写类默认不出现）
//   D. callTool('alerts') 返回文本里带 `"gbt_stamp"`（真过唯一门）
//
// 用法：
//   node plugins/dsh-mcp-bridge/interop-check.mjs [--sdk <SDK包目录>] [--repo-root <仓根>] [--python py] [--pyargs -3.14]
//
// 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属

import { pathToFileURL, fileURLToPath } from 'node:url';
import { existsSync } from 'node:fs';
import path from 'node:path';
import os from 'node:os';

function arg(name, dflt) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}

// 🔴 实测坑（本件首跑的红灯，写死防重踩）：官方 SDK 用 **cross-spawn** 起服务器，
//   而 cross-spawn 按 `;` 拆 PATH 找命令；**Git Bash 下的 PATH 是 POSIX 形态**
//   （`/c/WINDOWS:...`）⇒ 它找不到 `py`，报 `spawn py ENOENT`。
//   DSH 自己的进程是原生 Windows PATH（宿主从桌面壳起），`py` 能命中；
//   但**自证/排练要能在任意壳里跑** ⇒ 候选表里优先给**绝对路径**。
const here = path.dirname(fileURLToPath(import.meta.url));
let repoRoot = path.resolve(arg('repo-root', path.resolve(here, '..', '..')));
// 传的仓根若不含 gbt_allinone（例如在镜像维度里跑），就**不传** --repo-root，
// 让 server.py 自己向上寻根 —— 免得传一个看起来对、其实错的路径。
const repoRootOk = existsSync(path.join(repoRoot, 'gbt_allinone', '__init__.py'));
const sdkDir = path.resolve(arg('sdk', path.join(os.homedir(), '.dsh', 'profiles', 'node_modules', '@modelcontextprotocol', 'sdk')));
const serverPath = path.join(here, 'server.py');

const checks = [];
const ok = (name, pass, note = '') => {
  checks.push([name, !!pass, note]);
  console.log(`  ${pass ? '✓' : '✗'} ${name}${note ? ' — ' + note : ''}`);
};

if (!existsSync(path.join(sdkDir, 'dist', 'esm', 'client', 'index.js'))) {
  console.log(`✗ 找不到官方 SDK 的 ESM 入口：${sdkDir}/dist/esm/client/index.js`);
  process.exit(1);
}
const sdkUrl = (p) => pathToFileURL(path.join(sdkDir, 'dist', 'esm', p)).href;

const { Client } = await import(sdkUrl('client/index.js'));
const { StdioClientTransport } = await import(sdkUrl('client/stdio.js'));

console.log('== GBT DSH MCP 桥 · 官方 SDK 互操作自证 ==');
console.log(`SDK   : ${sdkDir}`);
console.log(`服务器: ${serverPath}`);
console.log(`仓根  : ${repoRootOk ? repoRoot : '(不传，交给 server.py 自己寻根)'}`);
console.log();

// python 入口候选（按稳到脆排序；绝对路径优先，见上方"实测坑"）
const winPy = 'C:/Windows/py.exe';
const candidates = [];
if (arg('python', null)) {
  candidates.push([arg('python'), arg('pyargs', null)]);
} else {
  if (existsSync(winPy)) candidates.push([winPy, '-3.14']);
  if (process.env.GBT_MCP_BRIDGE_PYTHON) candidates.push([process.env.GBT_MCP_BRIDGE_PYTHON, null]);
  candidates.push(['py', '-3.14'], ['python', null]);
}

let client = null, lastErr = null, used = null;
for (const [cmd, pre] of candidates) {
  const args = repoRootOk ? [serverPath, '--repo-root', repoRoot] : [serverPath];
  const full = pre ? [pre, ...args] : args;
  const transport = new StdioClientTransport({ command: cmd, args: full, cwd: repoRoot, stderr: 'pipe' });
  transport.stderr?.on?.('data', (d) => process.stderr.write('[server] ' + d.toString()));
  client = new Client({ name: 'gbt-interop-check', version: '0.1.0' });
  try {
    await client.connect(transport);
    used = [cmd, ...full].join(' ');
    break;
  } catch (err) {
    lastErr = err;
    console.log(`  … 用 \`${[cmd, ...full].join(' ')}\` 连接失败：${String(err).slice(0, 200)}`);
    client = null;
  }
}

try {
  ok('A/connect（initialize 走通）', client !== null, used ? `用 \`${used}\`` : String(lastErr).slice(0, 200));

  if (client) {
    const listed = await client.listTools();
    const names = (listed.tools || []).map((t) => t.name);
    console.log(`\n── tools/list 原文（name 列表）──\n${JSON.stringify(names)}\n`);
    ok('B/读类工具齐', ['run_task', 'alerts', 'selfscan', 'capability_status'].every((n) => names.includes(n)));
    ok('C/写类默认不出现', !names.includes('logbook_append'));

    const res = await client.callTool({ name: 'alerts', arguments: { last: 200 } });
    const text = (res.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('\n');
    console.log(`── callTool('alerts') 原文（前 700 字）──\n${text.slice(0, 700)}\n`);
    ok('D/alerts 真过唯一门（带 gbt_stamp）', text.includes('"gbt_stamp"') && !res.isError);

    // 写类负对照：白名单外的 kind 必须被桥拒
    const neg = await client.callTool({ name: 'run_task', arguments: { kind: 'mirror_shape', payload: { path: 'x' } } });
    const ntext = (neg.content || []).filter((c) => c.type === 'text').map((c) => c.text).join('\n');
    console.log(`── callTool('run_task', mirror_shape) 原文 ──\n${ntext.slice(0, 400)}\n`);
    ok('E/写类 kind 被桥拒（负对照）', ntext.includes('gbt-mcp-bridge'));
  }
} catch (err) {
  ok('异常', false, String(err).slice(0, 300));
} finally {
  try { await client?.close(); } catch { /* 关不上不算失败 */ }
}

const pass = checks.every(([, p]) => p);
console.log(`== 判定 ==\n${checks.map(([n, p]) => `  ${p ? '✓' : '✗'} ${n}`).join('\n')}`);
console.log(`\n${pass ? 'INTEROP OK' : 'INTEROP FAIL'}（${checks.filter(([, p]) => p).length}/${checks.length}）`);
process.exit(pass ? 0 : 1);
