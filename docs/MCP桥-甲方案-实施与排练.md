# MCP 桥 · 甲方案 · 实施与排练

> 主人令（2026-10-08）：「补法甲或乙」→ 取**甲**；唯一硬要求「修改代码和部署必须走镜像多维度空间」。
> 甲方案 = 用**现装未用的官方包** `@deepseek-ai/dsh-mcp-client`，把我方 **`gbt_allinone.run_task` 唯一门**
> 桥成官方 APP 里**第一等 MCP 工具**（不再只经 preset 的 `tool-pwsh` 敲 CLI）。
>
> 本件口径：**只做到"排练全绿"，一个字节都没晋升**；`~/.dsh/**` 一个字节没动；
> `mirror_ascend` / `mirror_release` / `pipeline_submit` **一次没跑**。
> 仓内件全部落在新目录 `plugins/dsh-mcp-bridge/`（不污染别处）。
>
> 姊妹件：`docs/DSH隐藏能力普查与接入方案.md`（§3.3 那条"诚实缺口"就是甲方案要补的）
> · `plugins/dsh-mcp-bridge/README.md`（配置行以文本给出）
> · `docs/DSH未启用20包-逐个评估.md` + `state/dsh-20pk-assessment.json`（逐包评估）

---

## 〇 先答"镜内面覆盖什么"（按要求先跑 `mirror_status` + `mirror_scan` 看清）

**动手前现读（本次第一次跑，未改任何东西）**：

```
$ py -3.14 tools/codex-scripts/five-dim.py cap mirror_status --full
{"ok": true, "dimension": {"files": 19}, "reality": {"files": 19, "version": 29},
 "dimension_vs_reality": [], "reality_drift": [], "clean": true, "timelines": 29, ...}

$ py -3.14 tools/codex-scripts/five-dim.py cap mirror_scan --full
{"ok": true, "passed": 5, "total": 5,
 "checks": {"non_empty":{"detail":"19 文件"}, "no_empty_files":{"detail":"无"},
            "signature":{"detail":"全部携带"}, "discipline":{"detail":"干净"},
            "entry_point":{"detail":"入口: ['holo_pet_w25/main.py', 'holo_pet_w3/eigenflux/index.html', 'holo_pet_w3/h1/index.html']"}},
 "files": 19}
```

⇒ **塑形面原样是那棵 19 件树**：`holo_pet_w25/*`（3）+ `holo_pet_w3/*`（16），与上次 `mirror_shape` 一致；
`plugins/dsh-mcp-bridge/**` **当时不在镜内面里**（如实报：不覆盖）。

**本次怎么做（不许假装）**：用 `mirror_shape` 把 6 件新件**成形进同一维度**（维度内随便改、现实无感知），
然后用六步排练去覆盖它们。⇒ **现在镜内面覆盖这 6 件**（dimension 19 → 25 文件）；
**但仍有一条必须写清的边界**：镜内那份 `server.py` 里 `gbt_allinone` 是**导入真实仓**的
（桥自己的寻根逻辑向上命中仓根），store 被排练器隔离到
`gbt_allinone/store/mirror_space/rehearsal_runtimes/dsh-mcp-bridge/<ns>/bridge-selfcheck-<ns>/store/`
（实测该目录里有 `audit.jsonl`，真 store 的账没被排练污染）。**这不是"整件都在镜内跑"，如实写。**

---

## ① 桥的设计 + 最小自证（真读数）

### 1.1 设计（三件写死防漂移）

1. **读类优先**：默认只暴露 4 个读类工具；写类（`logbook_append`、白名单外的任何 kind）**默认整个不出现在 `tools/list`**。
2. **两道机械闸**：① 显式白名单 `READ_KINDS`（19 个 kind）② 框架自己的策略层
   `security/policy.evaluate(kind,payload)`（`scopes` 非空即拒，**payload 一级也拦**——
   例：`selfscan{autofix:true}`、`inventory{fix:true}` 在框架里是 fail-open，本桥不跟着 fail-open）。
3. **身份不继承主人的"全通"**：桥启动时主动摘掉 `GBT_OWNER_SESSION` ⇒ 框架眼里是**未受信会话**，
   要票的动作走真票闸（`auth_gate`）；桥自己不发授权。

**工具面（现读 `tools/list`）**：`run_task`（唯一门读类子集）· `alerts` · `selfscan` · `capability_status`
（`logbook_append` 只在 `--enable-writes` 时出现）。
**传输**：stdio（无端口、无 HTTP 面、不监听任何东西）；**stdout 只走协议帧**（启动即把 `sys.stdout` 换成 stderr）。
**凭据**：**一个都不需要**（不读密钥服务、不读环境钥匙；官方包给子进程的环境是清洗过的）。

### 1.2 最小自证 A：自起自调（8 条判据）

```
$ py -3.14 plugins/dsh-mcp-bridge/selfcheck.py --timeout 300     # EXIT=0
── A · initialize 原文 ──
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {"listChanged": false}}, "serverInfo": {"name": "gbt-mcp-bridge", "version": "0.1.0"}, "instructions": "GBT小土豆V8 桥：默认只读。run_task 走我们的唯一门（读类白名单 + 框架策略层双闸）。写类工具默认不出现；要写得主人在本机发票。"}}
耗时 0.54s

── D · tools/call alerts 原文（3.72s） ──
{"gbt_stamp": {"framework": "GBT小土豆", "version": "8.0.0", "mark": "GBT", "developer": "自由的风", ...}, "gbt_result": {"status": "ok", "kind": "alerts", "result": {"quiet": true, "quiet_means": "窗口内确实什么都没有", "any_signal": false, "needs_a_look": false, "anomalies": 0, "note": "窗口期内无异常事件"}}, "ok_source": "status", "ok": true, "kind": "alerts", ...}

── E · tools/call capability_status 原文（0.02s） ──
{"ok": true, "total": 240, "domains": {"llm": 28, "mind": 16, "pipeline": 18, "security": 25, "system": 38, "tentacle": 11, ...}, "count": 240, "source": "gbt_allinone.caps_tables.all_caps()（静态目录，不含运行态）"}

── F · tools/call selfscan 原文（5.11s） ──
{"gbt_stamp": {...}, "gbt_result": {"status": "ok", "kind": "selfscan", "result": {"verdict": "clean", "checked_at": "2026-10-08T10:19:06", "findings": [], "sections": {"routing": {"registered": 240, "routed": 240, "unrouted": [], "ok": true}, "modules": {"checked": 37, "failed": [], "ok": true}, "store": {...}, "audit": {"window": 500, "anomalies": 0, "runtime_faults": 0, "ok": true}, "stub_gaps": []}, "capabilities_total": 240, ...}}}

── G · tools/call run_task(mirror_shape) 原文（0.00s） ──
{"ok": false, "kind": "mirror_shape", "refused_by": "gbt-mcp-bridge", "reason": "kind 不在本桥的读类白名单里（默认只读）", "note": "本桥默认只读；写类要么开 --enable-writes，要么让主人在终端发票。", "how_to_list": "调 capability_status 看 240 位目录；写类动作请主人在本机跑。", "did_you_mean": ["mirror_status", "mirror_scan"]}

== 判定 ==
  ✓ A/initialize   ✓ B/读类工具齐   ✓ C/写类默认不出现   ✓ D/alerts 真回 run_task 信封
  ✓ E/capability_status 240 位   ✓ F/selfscan 真回体检   ✓ G/写类 kind 被桥拒   ✓ H/logbook_append 未暴露

SELFCHECK OK（8/8）
```

> 首跑曾经红过一条（**如实记**）：D 的判据我原先写成 `gate == "run_task"`，而 `gate` 字段是
> `five-dim.py cap` **包装器**加的，唯一门 `run_task` 的信封里没有它 ⇒ 自证判 FAIL。
> 改判据为门自己的真身字段（`kind`/`status`/`gbt_stamp`）后全绿。**教训**：判据要按门的形状写，
> 不能按包装器的形状写。

### 1.3 最小自证 B：**官方同款 SDK** 真连一次（把最大的未知变成实测）

最大技术风险本来是"手写的服务端能不能被官方那份 SDK 认"。做法：用本机现装的
`@modelcontextprotocol/sdk`（**v1.30.1**，就是 `dsh-mcp-client` 依赖的那一份）真连。

```
$ node plugins/dsh-mcp-bridge/interop-check.mjs      # EXIT=0
SDK   : C:\Users\ADMIN\.dsh\profiles\node_modules\@modelcontextprotocol\sdk
服务器: C:\Users\ADMIN\Desktop\GBT小土豆V8\plugins\dsh-mcp-bridge\server.py
  ✓ A/connect（initialize 走通） — 用 `C:/Windows/py.exe -3.14 ...\server.py --repo-root ...`
── tools/list 原文（name 列表）──
["run_task","alerts","selfscan","capability_status"]
  ✓ B/读类工具齐      ✓ C/写类默认不出现
── callTool('alerts') 原文（前 700 字）──
{"gbt_stamp": {"framework": "GBT小土豆", ...}, "ok": true, "kind": "alerts", ...}
  ✓ D/alerts 真过唯一门（带 gbt_stamp）
── callTool('run_task', mirror_shape) 原文 ──
{"ok": false, "kind": "mirror_shape", "refused_by": "gbt-mcp-bridge", ...}
  ✓ E/写类 kind 被桥拒（负对照）

INTEROP OK（5/5）
```

**顺带抓到并修掉一处真缺陷（记这）**：官方 SDK 用 **cross-spawn** 起服务器，它按 `;` 拆 `PATH` 找命令；
**Git Bash 的 `PATH` 是 POSIX 形态**（`/c/WINDOWS:...`）⇒ 首跑报 `spawn py ENOENT`。
DSH 自己是原生 Windows PATH（桌面壳起的）能命中 `py`；但自证/排练要能在任意壳里跑 ⇒
候选表改成**绝对路径优先**（`C:/Windows/py.exe`），并把这坑写进 README §2/§3（含"必要时把配置里的
`command: py` 换成绝对路径"这句）。

---

## ② 晋升时要做的事清单（逐条：文件:行 / 改什么 / 回滚 / 复验）

> **本次全部未执行**（铁律：只到排练全绿）。下面每条都可在主人点头后**照抄执行**。

| # | 文件:行 | 改什么 | 回滚 | 复验判据 |
|---|---|---|---|---|
| P1 | `~/.dsh/.agent-presets/gbt-spine/agent.cordis.yml:287`（**文件末尾**，现读 287 行） | **append**（只加行，不改任何既有行）一段 `- id: mcp-gbt-bridge` / `name: '@deepseek-ai/dsh-mcp-client'` / `config: {serverName: gbt, transport: stdio, command: py, args: ['-3.14','C:/Users/ADMIN/Desktop/GBT小土豆V8/plugins/dsh-mcp-bridge/server.py','--repo-root','C:/Users/ADMIN/Desktop/GBT小土豆V8'], cwd: 'C:/Users/ADMIN/Desktop/GBT小土豆V8', toolCallTimeoutMs: 120000, failOnStartupError: false}`（原文见 `plugins/dsh-mcp-bridge/README.md` §3） | 删掉这一段（append-only ⇒ 回滚=删这几行）；重启宿主或让 `patchReload` 重挂 | 新会话工具列表出现 `mcp__gbt__run_task`/`__alerts`/`__selfscan`/`__capability_status`；调 `mcp__gbt__alerts` 返回体含 `gbt_stamp.framework="GBT小土豆"`（**钢印法**） |
| P2 | `~/.dsh/profiles/web/package.json`（**不需要改，写出来防误操作**） | **什么都不做**：`dsh-mcp-client` 与 SDK **已在** `~/.dsh/profiles/node_modules` 里（现读在装）。**不要** `npm install`、不要加 dependencies | — | `ls ~/.dsh/profiles/node_modules/@deepseek-ai/dsh-mcp-client` 有 `lib/index.js`；`ls ~/.dsh/profiles/node_modules/@modelcontextprotocol/sdk` 版本 1.30.1 |
| P3 | `state/desktop-shell-baseline.json` | **重记 B2 基线**（见 §③ 的"谁做、怎么做、判据"） | 用 `git show HEAD:state/desktop-shell-baseline.json` 还原（或用旧副本） | 重记后跑守卫：B2 从 PENDING/哈希差异回到 **PASS**，且 `.agent-presets` 的新哈希=现读哈希 |
| P4 | 仓内件 `plugins/dsh-mcp-bridge/{server.py,selfcheck.py,interop-check.mjs,rehearsal-plan.json,rehearse.py,README.md}` | **已在工作区落盘，本次未提交**（没有提交指令）。若要入库：`git add` 这 6 件 + commit | `git rm --cached` / `git checkout -- .`（未提交时最省事） | `git status` 干净；6 件 sha 与本文 §④ 的 `mirror_shape` 读数一致 |
| P5 | 镜像侧（**可选、要票**）：`store/mirror_space/` | 若要连"镜内件"也晋升：`mirror_release(name='dsh-mcp-bridge')` ⇒ 会把**整棵 25 件镜内树**（19 件 holo + 6 件桥）一次性写 `store/mirror_space/reality`。**票：`deploy_publish` 现读 0 张**（一次性票在主人手上） | `mirror_rewind(version=29)`（整树替换，回到现现实 v29） | `mirror_status` 里 `dimension`/`reality` 都 25 件、`reality_drift: []` |
| P6 | `docs/DSH未启用20包-逐个评估.md` + `state/dsh-20pk-assessment.json` | 仓内文档/台账，无需晋升动作；入库同 P4 | 删文件即可 | 复读 JSON：20 条、计数 `接 2 / 不接 15 / 先验证 3` |

**P1/P5 的顺序纪律**：先做 P1（真接上、用钢印法复验）再谈 P5（镜内件进 reality）；
两者都动的是"对外生效面"，**动之前主人点头、动之后立刻复验 + 记账**。

---

## ③ 守卫基线同步（B2 盯着 `~/.dsh` 的哈希）

**现读（本次跑守卫，一个字节没动 `~/.dsh`）**：

```
$ py -3.14 tools/codex-scripts/desktop-shell-guard.py
  ⏳ B2    **结构变了**（键增删/缩进）：['settings.yaml'] —— 需人看一眼；默认档 danger-full-access
```

- `DSH_WATCH = ["settings.yaml", "settings.yaml.bak", "agent-presets", ".agent-presets"]`
  （`tools/codex-scripts/desktop-shell-guard.py:78`）；基线 `state/desktop-shell-baseline.json`
  现读 `at = 2026-09-23T06:15:57`，`.agent-presets` 哈希 `85a69baa…`。
- **这条 PENDING 不是本次造成的**：本次没碰 `~/.dsh`；`settings.yaml` 的结构变化是**本仓外**的主人的改动
  （基线停在 2026-09-23，settings.yaml 此后被改过）。
- **P1 晋升后会发生什么（照代码判，不猜）**：`.agent-presets` 目录哈希必变 ⇒ B2 的 `diff` 非空；
  但目录在 `_settings_structure()` 里落 `<unreadable>`（对目录 `read_text` 抛 OSError）⇒
  `struct_diff` 空、`perm_diff` 空 ⇒ 判据落进"哈希变了但结构指纹与安全相关键都一致"= **PASS**，
  默认档仍报 `danger-full-access`。

**谁来做、怎么做（明确）**：

- **谁**：**主人在终端**执行（重记基线 = 把这次 DSH 配置变更合法化，等价于一次批准）。
  AI 只能在主人**书面放行**后执行，并且必须：① 先跑一次守卫留"晋升前"原文
  ② 执行 `--record-baseline` ③ 再跑一次守卫留"晋升后"原文 ④ 把两段原文 + 命令写进本文附注 + 走 logbook 记账。
- **怎么做**：
  ```
  py -3.14 tools/codex-scripts/desktop-shell-guard.py                 # 晋升前：留 B2 原文
  py -3.14 tools/codex-scripts/desktop-shell-guard.py --record-baseline   # 重记基线（写 state/desktop-shell-baseline.json）
  py -3.14 tools/codex-scripts/desktop-shell-guard.py                 # 晋升后：B2 应为 PASS
  ```
- **判据（机器可核）**：重记后 `state/desktop-shell-baseline.json` 的
  `dsh_config_hashes[".agent-presets"]` == 现读哈希；B2 行从 ⏳/哈希差异回到 ✅；
  `dsh_structure["settings.yaml"]["defaultPreset"]` 仍为 `danger-full-access`（权限档不许被顺手改掉）。
- ⚠️ **重记会一并吸收既有的 `settings.yaml` 结构变化**（那条不是本次的）⇒ **主人先确认那条是他自己的改动**
  再重记；若不确定，先查清 `settings.yaml` 变了什么（守卫的备份 `~/.dsh/settings.yaml.bak-*` 在）。

---

## ④ 排练六步的真读数（`py -3.14 plugins/dsh-mcp-bridge/rehearse.py`，EXIT=0）

全文读数落在 `.scratch/mcp-bridge-rehearsal.json`（驱动器每次覆写；stdout 原文留在
`.scratch/mcp-bridge-rehearsal-stdout.txt`）。**六步全绿，没有一步红。**

**① `mirror_shape` × 6（成形进镜像维度；每件都真消耗了 `filesystem_write` 时段票）**

```
① mirror_shape server.py         -> {"ok": true, "path": "plugins/dsh-mcp-bridge/server.py", "sha": "7a353c056c273441", "stage": true, "auth_consumed": "grant-1791425395752"}
① mirror_shape selfcheck.py      -> {"ok": true, ..., "sha": "faf9002c1c79c814", ...}
① mirror_shape interop-check.mjs -> {"ok": true, ..., "sha": "6e03d263e91adbc4", ...}
① mirror_shape rehearsal-plan.json -> {"ok": true, ..., "sha": "a035f73479202244", ...}
① mirror_shape rehearse.py       -> {"ok": true, ..., "sha": "63008ee21f2cede1", ...}
① mirror_shape README.md         -> {"ok": true, ..., "sha": "153b4b164ee56ca5", ...}
```

**② `mirror_status`（2871.5 ms）** — 信封 ok=True · 能力载荷 ok=True

```
{"ok": true, "dimension": {"files": 25}, "reality": {"files": 19, "version": 29},
 "dimension_vs_reality": [{"file": "plugins/dsh-mcp-bridge/README.md", "kind": "not_yet_promoted", "detail": "镜像有、生产无（待晋升）"}, ... 共 6 条 ...],
 "reality_drift": [], "clean": true, "timelines": 29, "versions": 29}
```

> 读法：6 条 `not_yet_promoted` = **本次成形的 6 件在镜内等着晋升**（正常暂存态）；
> `reality_drift: []` / `clean: true` = **现实零漂移**（v29 那 19 件一字未动）。

**③ `mirror_scan`（27.3 ms）** — 体检 5/5

```
{"ok": true, "passed": 5, "total": 5,
 "checks": {"non_empty": {"ok": true, "detail": "25 文件"}, "no_empty_files": {"ok": true, "detail": "无"},
            "signature": {"ok": true, "detail": "全部携带"}, "discipline": {"ok": true, "detail": "干净"},
            "entry_point": {"ok": true, "detail": "入口: ['holo_pet_w25/main.py', 'holo_pet_w3/eigenflux/index.html', 'holo_pet_w3/h1/index.html']"}},
 "files": 25, "elapsed_ms": 15.0}
```

**④ `mirror_plan`（133.5 ms）** — 计划已定义

```
{"ok": true, "name": "dsh-mcp-bridge", "defined_at": "2026-10-08T10:30:36",
 "plan_sha": "cc10676ea5e11c4ec38cb454df4038e1abe673f821395913f574469bf0dee9a9"}
```

**⑤ `mirror_simulate`（199.0 ms）** — 静态推演 9/9，假设 7 条**全部 verified**

```
{"ok": true, "passed": 9, "total": 9, "files": 25,
 "checks": {"dimension_scan": {"ok": true, "detail": "5/5 镜像体检通过"},
            "assumptions_verified": {"ok": true, "detail": "假设 7 条：已验证 7", "contradicted": [], "unverified": []},
            "files_present": {"ok": true, "detail": "计划引用的镜像文件全部存在"},
            "entrypoints": {"ok": true, "detail": "入口契约完整"},
            "dependency_graph": {"ok": true, "detail": "架构组件与部署步骤均无环"},
            "service_contract": {"ok": true, "detail": "服务端口唯一且均有验证信号", "services": 0, "ports": []},
            "environment_contract": {"ok": true, "detail": "环境变量名与外部路径契约可满足"},
            "closed_loop_defined": {"ok": true, "detail": "验收命令 2 条", "acceptance": ["bridge-selfcheck", "bridge-interop"]},
            "rollback_defined": {"ok": true, "detail": "回滚策略已声明"}},
 "dimension_sha": "ca05a80365b45735e8f9c5a422cfbdfeeb7c3f60c74d90f502b625c1e1e997ff"}
```

**⑥ `mirror_parity`（5536.3 ms）** — 沙盒≡生产（same_host）无阻断

```
{"ok": true, "name": "dsh-mcp-bridge", "mode": "same_host",
 "sandbox": {"platform": "win32", "os": "windows", "machine": "amd64", "python": "3.14",
             "python_executable": "C:\\Users\\ADMIN\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
             "shell": "cmd.exe", "tools": {"python": true}, ...},
 "production": { 同上一份（same_host 由 gate 在晋升时刻复检漂移） },
 "blockers": [], "warnings": [{"field": "production.mode", "detail": "显式声明沙盒与生产同机同环境（未附显式断言，由 gate 在晋升时刻复检环境漂移）；非同机部署必须改用 profile"}]}
```

**⑦ `mirror_rehearse`（77647.8 ms）** — 沙盒闭环全绿（**在镜像维度里真跑了两条验收命令**）

```
{"ok": true, "name": "dsh-mcp-bridge", "report_id": "20261008T103153-1791430313196517700",
 "plan_sha": "cc10676ea5e11c4ec38cb454df4038e1abe673f821395913f574469bf0dee9a9",
 "dimension_sha": "ca05a80365b45735e8f9c5a422cfbdfeeb7c3f60c74d90f502b625c1e1e997ff",
 "dimension_files": 25, "blockers": [], "acceptance": ["bridge-selfcheck", "bridge-interop"],
 "commands": [
   {"id": "bridge-selfcheck", "ok": true, "exit_code": 0, "elapsed_ms": 45282.8,
    "passed_checks": {"exit_code": true, "not_timed_out": true, "stdout_contains": true, "workspace_isolated": true},
    "stdout": "... SELFCHECK OK（8/8）", "workspace_changes": []},
   {"id": "bridge-interop", "ok": true, "exit_code": 0, "elapsed_ms": 24702.7,
    "passed_checks": {"exit_code": true, "not_timed_out": true, "stdout_contains": true, "workspace_isolated": true},
    "stdout": "== GBT DSH MCP 桥 · 官方 SDK 互操作自证 ==\nSDK   : C:\\Users\\ADMIN\\.dsh\\profiles\\node_modules\\@modelcontextprotocol\\sdk\n服务器: ...\\gbt_allinone\\store\\mirror_space\\dimension\\plugins\\dsh-mcp-bridge\\server.py\n仓根  : (不传，交给 server.py 自己寻根)\n  ✓ A/connect ... INTEROP OK（5/5）", "workspace_changes": []}],
 "law": "镜像排练全绿 + 树/计划指纹绑定；任何变更都会使本次报告失效"}
```

> 要紧的两点（都是机器判的，不是自述）：
> ① `workspace_isolated: true` + `workspace_changes: []` ⇒ 两条命令**没改镜像树**（报告因此有效）；
> ② interop 那条跑的是**镜内那份** `server.py`（路径就是 `dimension/plugins/dsh-mcp-bridge/server.py`），
> 且 `仓根 = (不传，交给 server.py 自己寻根)` —— 这正是"镜内件 + 寻根回退"的实测证据。

**报告落盘**：`gbt_allinone/store/mirror_space/rehearsals/dsh-mcp-bridge/{latest.json, <report_id>.json, simulate-latest.json, parity-latest.json}`
· 计划落盘 `.../plans/dsh-mcp-bridge.json` · 时间线仍 29 条（**没新增**，因为没有晋升）。

### 4.1 票记账（本次真消耗，如实记）

| 作用域 | 动手前 used / avail | 收工 used / avail | 说明 |
|---|---|---|---|
| `filesystem_write` | 6 / 2 | **30 / 2** | 时段票（TTL 内可多次，用一次记一次）；本次 24 次=shape 6×3 轮 + plan/simulate/parity/rehearse 各 1×3 轮 |
| `process_execute` | 0 / 2 | **2 / 2** | 两次 `mirror_rehearse`（每轮沙盒闭环真起进程） |

**没有跑**：`mirror_ascend` / `mirror_release` / `pipeline_submit`（要 `deploy_publish` 一次性票，**现读 0 张**，票在主人手上）。
**没有绕门**：所有能力位调用都过 `run_task`；桥侧写类动作按 `auth_gate` 真票闸。

---

## ⑤ 做不到 / 未验证的（逐条明说，不粉饰）

1. **DSH 侧挂载从未实测**：本次不许动 `~/.dsh/**` ⇒ "追加 P1 那段配置后 `mcp__gbt__*` 真出现在官方 APP 工具列表里"
   **没有在真 DSH 上验证过**。已把能验的都验了（官方同款 SDK 真连 == 服务器侧协议正确；
   剩余不确定只在"DSH 侧那一行的解析与挂载"，用 §② P1 的**钢印法**一次就能判）。
2. **协议面未穷举**：只实现/验证了 `initialize` / `notifications/initialized` / `tools/list` / `tools/call` / `ping`
   （`resources/list`、`prompts/list` 回空表，其余方法 -32601）。官方包本身只桥工具，但 **SDK 升级改形状**时要跟着改。
3. **镜内件 ≠ 仓内件逐字节相同**（实测发现的真差异，不许含糊）：`mirror_space.shape()` 用 `Path.write_text`
   ⇒ Windows 上换行被翻成 **CRLF**：`server.py` 28807→29372 字节、`README.md` 8324→8454 字节，
   其余同理（内容一致、仅换行）。功能无害（镜内两条验收命令都跑通），**但"镜像=逐字节相同"这句话本件不说**。
   要逐字节一致得走 `shape_bytes`（二进制安全入口）——本件**没有改** `mirror_space`（不许碰 `gbt_allinone/**`），
   留作主人的选择。
4. **写类路径只验了"关"没验"开"**：
   - 已验证：默认 `tools/list` 无 `logbook_append`；显式调用被拒（原文见 §1.2 G/H）；白名单外 kind 被拒（§1.2 G、§1.3 E）。
   - **未验证**：`--enable-writes` 下的真实写（`logbook_append` 真落一条、写类 kind 真过票）——
     那会消耗主人的票并写账，本次**未做**。要真验：主人发票后 `--enable-writes` 再跑一次，看 `auth_consumed`。
5. **非 probe 调用的框架副作用（既有行为，不是桥引入）**：每一次 `run_task` 都会跑"产出即绑"钩子
   （节流 3 秒，写仓内 `state/asset_bindings.*` 与 `state/.bind_watermark`；本次实测这些文件 mtime 变化）。
   它与桥无关，但**在排练里也会发生**，故写在这里。
6. **镜像维度是共享面**：现在是 19 件 holo + 6 件桥 = **25 件**；而 `mirror_ascend`/`mirror_release`
   是**整树**一次性写 `reality` ⇒ **"只晋升桥这一件"在这套设计里不存在**（P5 必须连那 19 件一起看）。
   本次没晋升：`reality` 仍 19 件 v29、`reality_drift: []`。
7. **B2 那条 PENDING 与本次无关**（见 §③），但**重记基线会把它一起吸收** —— 主人先确认再重记。
8. **`sys.stdout`/`sys.stderr` 编码**：桥启动即把两者转 UTF-8（否则 Git Bash/无 BOM 控制台下中文诊断变乱码，
   interop 首跑实测 `[gbt-mcp-bridge] ����`）。这条只治"看得见"，不改任何行为。

---

## 附：本件涉及的全部关键路径（便于复核）

```
plugins/dsh-mcp-bridge/server.py          最小 MCP 服务（stdio；只读白名单 + 框架策略层双闸）
plugins/dsh-mcp-bridge/selfcheck.py       自证 A：自起自调 8 条判据（SELFCHECK OK）
plugins/dsh-mcp-bridge/interop-check.mjs  自证 B：官方同款 SDK 真连 5 条判据（INTEROP OK）
plugins/dsh-mcp-bridge/rehearsal-plan.json 镜像排练计划（7 假设 / 2 验收命令）
plugins/dsh-mcp-bridge/rehearse.py        六步排练驱动器（可复跑；禁调晋升类 kind）
plugins/dsh-mcp-bridge/README.md          接法与边界（配置行以文本给出、不代改 ~/.dsh）
.scratch/mcp-bridge-selfcheck.txt         自证 A 全文读数（本次）
.scratch/mcp-bridge-interop.txt           自证 B 全文读数（本次）
.scratch/mcp-bridge-rehearsal.json        六步排练全文读数（本次）
.scratch/mcp-bridge-rehearsal-stdout.txt  六步排练 stdout 原文（本次）
gbt_allinone/store/mirror_space/dimension/plugins/dsh-mcp-bridge/**          镜内件（6 件，CRLF）
gbt_allinone/store/mirror_space/rehearsals/dsh-mcp-bridge/latest.json        排练报告
gbt_allinone/store/mirror_space/plans/dsh-mcp-bridge.json                    排练计划（镜侧留档）
```

---

开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
