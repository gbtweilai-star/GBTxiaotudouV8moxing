---
name: gbt-security
displayName: GBT 安全域（黑客大脑 · 红蓝双模）用法规程
version: 1.0.0
description: GBT小土豆V8 的「安全职业域」用法规程 —— 把图鉴里 domain=security 的 5 个能力位（sec_surface / sec_scan / sec_chain / sec_defenses / sec_llm）蒸馏成能照着跑的一页：每位写清用途、只读还是要授权、真命令模板、失败典型样子，并附一份**实测过的诚实账**（4 位本轮真跑通并带真实字段，sec_llm 缺 external_llm 被门拒、本体未验，绝不绕门）。同时把三条读数陷阱写死（风险分 100 不是警报 / critical 数要先看 location 落在哪棵树 / VULN-id 不是稳定追踪号）与凭据零明文红线（只报"已配/未配"）。当用户要「扫一下有没有漏洞 / 看攻击面 / 推攻击链 / 验证防御是否真生效 / 问黑客大脑 / 安全审计 / 蓝队红队」，或安全类能力位被门拦、读数看不懂、怀疑自己读错了地方时使用。
triggers:
  - "安全域"
  - "security"
  - "漏洞扫描"
  - "扫一下有没有漏洞"
  - "攻击面"
  - "利用链"
  - "防御验证"
  - "黑客大脑"
  - "红队"
  - "蓝队"
  - "安全审计"
  - "渗透"
  - "OWASP"
  - "能力位"
---

# GBT 安全域（security）用法规程

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属
>
> 这是「人类视角操控一切」在**安全这一格**的用法：`gbt-omni` 负责"人话落到哪个能力位"，
> 本规程负责"落到安全域这 5 位之后，命令长什么样、要不要授权、失败长什么样、**读数怎么念才不念错**"。

**唯一现读入口（别信任何二手描述，包括本文件）**：

```powershell
py -3.14 tools/codex-scripts/omni.py list --domain security          # 这 5 位是什么（图鉴现扫）
py -3.14 tools/codex-scripts/omni.py ask  "扫一下我自己的代码有没有漏洞"
py -3.14 tools/codex-scripts/omni.py ask  "验证一下防御措施是不是真的生效"
```

**本域实测**：`list` 把 4 位标 `✅`、`sec_llm` 标 `🔒`（`needs_confirmation: true`）——**这一域标对了**。
但 `✅` 是**图鉴旗标**（`enabled && safe && !requires_params && !needs_confirmation`）算出来的，
**不等于"门放行"**；判门一律用 `policy.evaluate`（见 §1）。

---

## 0. 五位一个门：`run_task`

5 个能力位**全走同一个门**，唯一入口：

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap <能力位> ['{"参数": ...}']
```

**没有第二条路**：不许直接 `import gbt_allinone.security.security_brain` 调函数、
不许自己写脚本绕过 `run_task` —— 那等于绕门（`policy.authorize` 在门外，绕过去就是违规）。

**域怎么定的**：以 `state/skill_atlas.json` 里 `domain == "security"` 的条目为**准**（现扫读数 5 条）。
不是谁记得的清单，也不是本文件说了算。

---

## 1. 五位总表（一页看全）

| 能力位 | 用途（图鉴原文） | 门 | 参数 | 实测判定 |
|---|---|---|---|---|
| `sec_surface` | 攻击面测绘（用户输入/网络/文件操作/入口点向量分析+风险评分） | 零作用域 | `target`（可选） | ✅ 真跑通（13.4s） |
| `sec_scan` | 漏洞扫描（OWASP Top 10 + CWE 模式库，扫描自有代码） | 零作用域 | `severity` / `limit` / `include_non_production`（都可选） | ✅ 真跑通（本轮 284.4s） |
| `sec_chain` | 利用链构建（从漏洞清单推演攻击路径+影响评估） | 零作用域 | `vulns`（可选，语义见 §2.3） | ✅ 真跑通（两支） |
| `sec_defenses` | 蓝队防御验证（检查防御措施是否真实生效） | 零作用域 | 无 | ✅ 真跑通（5/5） |
| `sec_llm` | 黑客大脑推理引擎（独立大模型+独立密钥，abliteration.ai） | 🔒 **`external_llm`** | **必需** `prompt` | ⛔ **本体未验**：缺授权被门拒 |

**门是静态查出来的，不必先撞一次才知道**：

```powershell
py -3.14 -c "import sys; sys.path.insert(0,'.'); from gbt_allinone.security import policy; [print(k, policy.evaluate(k,{}).scopes, policy.evaluate(k,{}).risk) for k in ('sec_surface','sec_scan','sec_chain','sec_defenses','sec_llm')]"
```

实测返回（逐条）：

```
sec_surface  | risk low  | scopes []            | restricted False
sec_scan     | risk low  | scopes []            | restricted False
sec_chain    | risk low  | scopes []            | restricted False
sec_defenses | risk low  | scopes []            | restricted False
sec_llm      | risk high | scopes ['external_llm'] | restricted True
```

⇒ **5 位里只有 `sec_llm` 要授权**，且它是唯一 `requires_params: ["prompt"]` 的一位。
**注意**：`scopes=[]` 只说明"门不拦"，**不说明"没有副作用"** —— `sec_defenses` 就带着探针写盘（§2.4）。

---

## 2. 逐位用法（真命令 → 真返回 → 失败样子）

### 2.1 `sec_surface` —— 攻击面测绘（只读）

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap sec_surface
```

**本轮真实返回的关键字段**（`status ok · stamp true · denied false`，`elapsed_ms 13399.1`）：

```
attack_surface = {entry_points: 1568, file_operations: 1593, network: 894,
                  user_inputs: 550, auth_boundaries: 1618}
total_vectors  = 6223
risk_score     = 100      risk_level = "高危"
top_vectors[0..2] = [deploy_app_oneclick.py / entry_point,
                     deploy_app_oneclick.py / user_input,
                     .scratch\abl_models.py / file_operation]
```

- **读数怎么念**：`total_vectors` = 五类向量计数之和（1568+1593+894+550+1618 = **6223** ✔ 可当场验算）；
- ⚠️ **`risk_score: 100 / risk_level: "高危"` 不是警报**。源码自己写死了这条：
  `signal_patrol()` 的注释是「攻击面风险分是框架全量代码静态统计(400+cap必然高分)，**不是可行动警报**
  —— 不再按分数发 high 信号，只记录统计供执行者参考」。
  ⇒ **念法是"四类向量各多少、共多少"，不是"系统高危、被攻击了"。**（详见 §5 ②）
- **它读什么**：`<仓>/**/*.py` 的**文件名 + 全文**（逐行正则匹配 5 类特征）；
  跳过 `_*.py` 与路径含 `deploy_bak` 的文件。`top_vectors` 里出现 `.scratch\...` 说明
  **构建暂存目录也在扫**（它没有把 `.scratch` 排除）—— 念 `top_vectors` 时要认出这一点；
- **写什么**：**不写盘**、不出网；
- **失败典型**：位本身几乎不失败；翻车的是 **shell 引号**。`cap sec_surface '{\"target\":\"x\"}'`
  → `json.decoder.JSONDecodeError`（exit 1）。**正确写法**：PowerShell 单引号里直接写双引号 JSON。
  另：`target` 传的路径不存在时**不报错**，静默回落全仓 —— 那会让你以为"我只看了一个子目录"。

### 2.2 `sec_scan` —— 漏洞扫描（只读）

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap sec_scan
```

**本轮真实返回的关键字段**（`status ok · stamp true · denied false`，`elapsed_ms 284361.6`）：

```
ok true · total 508 · critical 55 · high 15 · medium 438 · low 0
scope "production" · tier_counts {production: 508}
non_production = {scanned: false,
                  skipped_files: {scratch: 523, test: 723, backup: 7},
                  total_skipped: 1253,
                  how_to_include: "传 include_non_production=True 可连这些层一起扫，逐层条数会照报。"}
exempted = {counts: {comment_or_doc_exec: 224829, generated_secret: 13,
                     pattern_table: 26, taint_safe: 8, json_pattern_def: 54},
            total: 224930}
shown 20 · truncated true · parse_warning_count 2
vulnerabilities[0..2] =
  {id VULN-0461, title 命令注入, severity critical, cwe CWE-78,
   location ".shadow-repo\tools\codex-scripts\verify_roothfix.py:113"}
  {id VULN-0462, title LLM API密钥泄露(OpenAI/DeepSeek), cwe CWE-798,
   location ".shadow-repo\tools\codex-scripts\verify_shapes_remaining.py:82"}
  {id VULN-0033, title 不安全反序列化, cwe CWE-502,
   location "_upstream\Scrapling\scrapling\spiders\checkpoint.py:74"}
```

- **`total` 只数生产层**：非生产层（`.scratch` 备份/快照 / `.backups` / `archive` / `tests` 夹具）
  **默认不扫**，并**如实报跳过了几层各多少文件**（本轮 `scratch 523 / test 723 / backup 7 = 1253`）。
  这是**明说跳过**，不是静默丢弃 —— 传 `include_non_production=true` 可连它们一起扫；
- **`exempted` 要看**：本轮豁了 **224930** 行，其中 `comment_or_doc_exec` 占 224829（注释/文档串里的
  **执行类**模式 —— 注释不会被执行；但**泄露类**模式在注释里**照扫**，因为注释也会被读走、被提交）；
- **`shown 20 · truncated true`**：**默认只回 20 条**，但已按严重度排序（critical 在前），
  所以"前 20 条全是 critical"是排序的结果，**不是"只发现 20 条"**。要更多传 `limit`（上限 500），
  要更少传 `severity` 过滤；
- ⚠️ **`critical: 55` 不许直接当"自有代码有 55 个严重漏洞"念**：本轮排序后前 3 条的 `location`
  分别落在 **`.shadow-repo\`** 与 **`_upstream\Scrapling\`** —— 这两棵树实测存在（各 627 / 889 个 `.py`），
  而排除名单里没有它们（排除的是 `lib/site-packages/node_modules/.git/store/archive/__pycache__` 等）。
  ⇒ **念 critical 前先按 `location` 分类**（详见 §5 ③）；
- **`parse_warning_count`**：被扫文件里的坏转义序列（`ast.parse` 的 `SyntaxWarning`）——
  未来 Python 会报错，属真实缺陷，所以它记账上报（本轮 2 条）；
- **写什么**：**不写盘**、不出网，只回结果（读的是文件内容，读进内存做正则）；
- ⏱ **耗时别按旧口径设**：`gbt_allinone/README.md` 写「6 秒全仓」，**本轮实测 `elapsed_ms = 284361.6`
  ≈ 4 分 44 秒**。以现测为准，超时给足（建议 ≥600s）；另注 `sec_chain` 未给料时会**再扫一遍**（§2.3）；
- **失败典型**：未知 severity 会**静默回落 `medium`**（不报错）—— 你以为筛了 `critical`，其实没筛。

### 2.3 `sec_chain` —— 利用链构建（只读；未给料会自己扫）

```powershell
# ① 不给料（vulns 缺席）⇒ 自己按 high 及以上扫一遍当料
py -3.14 tools/codex-scripts/five-dim.py cap sec_chain
```

**本轮真实返回**（`elapsed` 与一次 full scan 同量级，别当秒回）：

```
ok true · scenario "full_compromise" · total_chains 1 · risk "存在攻击链"
chains[0] = {name "信息泄露→代码执行→持久化",
             steps [{vuln VULN-0070, action "探测信息泄露"},
                    {vuln VULN-0069, action "利用注入获取执行"},
                    {vuln VULN-0031, action "写入后门持久化"}],
             impact "完全控制系统", probability 0.6}
material_source "auto_scan" · material_counts {info_leak 34, injection 14, file_op 28, vulns 70}
scanned {total 70, critical 55, high 15, scope "production", shown 70}
note "未传 vulns ⇒ 本函数自己按 high 及以上扫了一遍当料（scope=production，总 70 条）—— 结论是**扫过之后**的结论，不是「没料所以没链」。"
```

```powershell
# ② 明说"没有漏洞"（vulns 传空清单）⇒ 尊重调用方结论，不再自己扫
py -3.14 tools/codex-scripts/five-dim.py cap sec_chain '{"vulns":[]}'
```

**本轮真实返回**：

```
ok true · total_chains 0 · chains [] · risk "未发现完整链"
material_source "supplied_empty"
material_counts {info_leak 0, injection 0, file_op 0, vulns 0} · scanned null
note "调用方明确传入空清单 ⇒ 按「没有漏洞」处理，未发现链；本函数未自行扫描。"
```

- 🔴 **"未发现完整链"有两种意思，看 `material_source`**：
  `auto_scan` = **扫过之后**没有链；`supplied_empty` = **调用方说没有漏洞**。
  两者此前走同一条路（把"我根本没拿到料"读成了"我看过了，没有链"），现已分开并各自写明 note。
  **念结论必须带上 `material_source`，否则就是把"不知道"说成"没问题"**；
- `scanned` 是它自己那轮扫描的元数据（`total 70` = critical 55 + high 15 及以上），
  与 §2.2 的默认读数（508/20 条截断）不是同一个口径 —— **别把两个 `total` 混着引用**；
- `probability 0.6` 是**链模板里的写死常量**，不是概率模型算出来的（源码里就是字面量）；
- **只读**、零作用域、不写盘；但**未给料时会触发一次全仓扫描**（≈5 分钟），别在急用路径上裸调。

### 2.4 `sec_defenses` —— 蓝队防御验证（**带探针写盘，跑完自清**）

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap sec_defenses
```

**本轮真实返回**（`status ok · stamp true · denied false`，`elapsed_ms 91.8`）：

```
ok true · defense_status "全部生效" · passed 5 · total 5
checks.danger_gate        {ok true, detail "keylogger -> unknown capability（解禁前为 denied）"}
checks.net_guard          {ok true, detail "127.0.0.1 -> denied (auth_gate denied)"}
checks.pipeline_gate      {ok true, detail "缺 actor -> blocked"}
checks.registry_integrity {ok true, detail "登记未实现 11 项 | 被拒名单 0 项（0=已全部解开）"}
checks.write_protection   {ok true, detail "生产区原子写入 (os.replace) 机制在位",
                           evidence_lines [397, 496]}
```

- **它在验证 5 件真事**：①危险能力如实（`keylogger` 这一类必须拿到**如实结果**：解禁前是
  `denied`，解禁后是 `unknown capability` —— **两种都不许是"跑成功了"**）；②内网护栏（`osint_scan 127.0.0.1`
  必须被拦）；③管线门禁（`pipeline_submit` 缺 actor 必须 `blocked`）；④名单完整性
  （`UNIMPLEMENTED_CAPS ≥ 11` 且 `DISABLED_CAPS == 0`，即"名字不丢、无人被拒"）；⑤生产区写保护（`pipeline` 里有 `os.replace`）；
- 🔴 **它不是"纯只读"**（门不拦 ≠ 没有写面）。`pipeline_gate` 那一枪会**以主人可信会话**
  （`policy.owner_session()`）提交一个**负对照探针** `_def_probe.txt`（`meta.probe=True`，本枪就指望被拦）。
  实测审计账本原文（`gbt_allinone/store/audit.jsonl`）：

  ```
  call               {"kind": "sec_defenses", "payload_keys": []}
  call               {"kind": "pipeline_submit", "payload_keys": ["name","content","meta"]}
  preflight_checked  {"kind": "pipeline_submit", "fingerprint": "8d82f45c...", "status": "acquired"}
  pipeline_blocked   {"rec_id": "_def_probe.txt-2d711642-1790089888", "name": "_def_probe.txt", "probe": true}
  ok                 {"kind": "sec_defenses"}
  ```

- 🔴 **它会自己清理探针残留**（这条必须写清，否则下一个人会把盘上的脏东西算到别人头上）：
  探针产物原本每跑一轮就在 `store/pipeline/{gate,mirror,quarantine,records}` 各留一份、堆到 96 轮 ×4 = 384 个；
  现在探针在**同一个函数的 `finally` 里**扫掉自己的产物（`_sweep_selftest_probe_artifacts()`，
  匹配 `_def_probe*`），**任何清理失败都不抛**（自检不该被清理失败带崩）。
  **实测**：本轮跑完 `store/pipeline` 下 `_def_probe*` 计数 = **0（已自清）**。
  ⇒ **盘上无残留，但账上有痕**（上面那四笔）—— "已清"指的是产物，不是"没有发生过"；
- **失败典型**：某项 `ok:false` 时 `defense_status` 会变成 `存在缺口 (N 项未过)`，且 `ok:false`。
  **本轮 5/5 全过，缺口分支未验**（§8 第 4 条）。

### 2.5 `sec_llm` —— 黑客大脑推理引擎（🔒 要授权，**本体未验**）

```powershell
py -3.14 tools/codex-scripts/five-dim.py cap sec_llm
```

真返回（**exit 1**）—— 门打印的**原文**：

```json
{"gate": "run_task", "kind": "sec_llm", "status": "denied", "stamp": false, "denied": true,
 "result": {"status": "denied", "kind": "sec_llm", "denied": true,
            "message": "capability requires human authorization",
            "reason": "需要人工授权（external_llm）：把当前任务数据发送到外部大模型服务",
            "scopes": ["external_llm"], "missing": ["external_llm"],
            "how_to_grant": ["终端运行: python -m gbt_allinone auth grant --scope external_llm --ttl 600",
                             "或主人手写 store/auth_grants.jsonl 追加一行（格式见 auth_gate.SCOPES 与 README）"],
            "note": "授权一次性消耗；AI 调用路径无权自行发放"},
 "missing_scopes": ["external_llm"],
 "reason": "需要人工授权（external_llm）：把当前任务数据发送到外部大模型服务",
 "how_to_grant": ["终端运行: python -m gbt_allinone auth grant --scope external_llm --ttl 600",
                  "或主人手写 store/auth_grants.jsonl 追加一行（格式见 auth_gate.SCOPES 与 README）"],
 "note": "授权一次性消耗；AI 调用路径无权自行发放"}
```

同一次调用在审计账本里留下的三笔（实测）：

```
call         {"kind": "sec_llm", "payload_keys": []}
auth_denied  {"scope": "external_llm", "detail": "sec_llm:sec_llm", "missing": ["external_llm"]}
denied       {"kind": "sec_llm", "reason": "authorization required", "scopes": ["external_llm"], "missing": ["external_llm"]}
```

- **它的本体返回值我没验过** —— 缺 `external_llm`，被门挡住。**授权只能主人在终端发**，
  **AI 永远无权给自己发授权**；缺就**如实报缺**，**不找旁路、不改 `security/policy.py`**；
- **必带 `prompt`**（图鉴 `requires_params: ["prompt"]`，`params_hint`: 要问黑客大脑的问题）：
  缺 prompt 时 handler 先抛 `ValueError("缺少 prompt：请给出要问黑客大脑的问题")` ——
  **但授权门在它前面**，所以非受信路径上你看到的一律是上面的 `denied`，看不到那句 ValueError；
- **凭据只报"已配 / 未配"**：`gbt_allinone/security/abl_gateway.py` 的 `configured()` 实测 = **True（已配）**。
  **一个字都不许多说**（不报长度、不报前后缀、不报来源行）—— 密钥纪律写在它源码第 5 行：
  「只从 `.env` 读 `ABLITERATION_API_KEY`，**不进源码不进日志**」；
- **静态读出（未验，不许当实测用）**：端点 `https://api.abliteration.ai/v1`，
  默认模型 `abliterated-model-large-v2`，`urllib` 直连、`Authorization: Bearer <key>`，
  `configured()` 为假时返回 `{"ok": false, "error": "未配置 ABLITERATION_API_KEY"}`；
  源码注释另记：`max_tokens` 需给足（≥1500），否则 reasoning 耗尽预算导致 `content` 为空；
  正文为空而 reasoning 有值时**如实返回 reasoning 并标注**（不伪造正文）；
- **数据出机器**：这一位会把 prompt 送到**外部大模型服务**（这也是它要 `external_llm` 的原因）。
  **要发之前先问自己：这句话方不方便出机器？**

---

## 3. 本域唯一的作用域门：`external_llm`

| 项 | 值（门自己打印的原文） |
|---|---|
| 要门的位 | **只有** `sec_llm` |
| 作用域 | `external_llm` |
| 含义 | 把当前任务数据发送到外部大模型服务 |
| 缺了会怎样 | `status: "denied"` · `denied: true` · `stamp: false` · exit 1 |
| 怎么授权 | `终端运行: python -m gbt_allinone auth grant --scope external_llm --ttl 600` |
| 或者 | `主人手写 store/auth_grants.jsonl 追加一行（格式见 auth_gate.SCOPES 与 README）` |
| 纪律 | `授权一次性消耗；AI 调用路径无权自行发放` |

**红线**：授权**只能主人在终端发**。缺授权就**如实报缺什么**，
**不绕门、不找旁路、不改 `security/policy.py`、不给自己发授权、不替别人发授权**。

另注（**实测**）：本会话报 `sec_llm` 得到的是"被门拒"，`stamp: false` ——
说明**本会话走的是非受信路径**（受信主人会话在 `policy.authorize` 里直接放行）。别把"我被拒"读成"这门坏了"。

---

## 4. 读什么 / 写什么 / 留痕（一张表说清）

| 能力位 | 读什么 | 写什么 | 留痕（`gbt_allinone/store/audit.jsonl`） |
|---|---|---|---|
| `sec_surface` | `<仓>/**/*.py` 的**文件名 + 全文**（5 类向量正则；跳 `_*.py`、`deploy_bak`） | **不写盘**；不出网 | 两笔：`call`（只记 `payload_keys`）+ `ok` |
| `sec_scan` | 同上（另跳 `lib/site-packages/node_modules/.git/store/archive/__pycache__` 等；非生产层默认跳并如实报） | **不写盘**；不出网 | 两笔：`call` + `ok` |
| `sec_chain` | 不额外读盘；**未给 `vulns` 时自己再全仓扫一遍** | **不写盘** | 两笔：`call` + `ok` |
| `sec_defenses` | 注册表常量 / `policy` / `pipeline` 源码；**跑 3 个负对照探针**（`keylogger` · `osint_scan 127.0.0.1` · `pipeline_submit` 缺 actor） | **短时写**：探针在 `store/pipeline/{gate,mirror,quarantine,records}` 落产物 | **多笔**：`sec_defenses` 的 `call`/`ok` + 探针的 `call`/`preflight_checked`/`pipeline_blocked(probe:true)`；**盘上产物跑完自清（实测 0）** |
| `sec_llm` | 把 `prompt` 送到 `api.abliteration.ai`（**外部、计费面**） | 不出本机文件 | 本轮：`call` → `auth_denied` → `denied` |

**审计口径（实测）**：进 `run_task` 先记 `call`，其中 `payload_keys` **只记键名、不记值** ——
所以 `sec_llm` 的 `prompt` 正文**不入账**；终态记 `ok` / `denied`（`denied` 另附 `scopes`/`missing`）。
**"没写盘"不等于"没留痕"**：4 位只读能力位同样每次都留两笔。

---

## 5. 🔴 报告层红线：读数先问「这是事实，还是我读错了地方」

五个**本域实测/可复现**的读错地方，五段都别再踩：

**① 被门拒时，`cap` 打的是扁平错误信封 —— 要读顶层，不要读 `gbt_result`。**
实测 `cap sec_llm` 的顶层键含 `denied / missing_scopes / reason / how_to_grant / note`，
而 `stamp` 是 `false`；被门拒时**根本不带 `gbt_result`**。
`five-dim.py` 已按此修过（源码注释 R-H299：改前只读 `r["gbt_result"]` ⇒ 门明明说"拒了"，
报表却打 `status: unknown · denied: false`，把"缺授权"读成"只是没跑通"）。
⇒ **判"是不是被门拒"，看顶层 `denied` 与 `missing_scopes`。**

**② `risk_score: 100 / 高危` 不是警报 —— 它是全仓静态统计。**
`sec_surface` 对**框架自己的全部 400+ 能力位代码**做静态统计，**必然高分**；
`signal_patrol()` 的注释明确写着「**不是可行动警报** —— 不再按分数发 high 信号」。
⇒ **念法是"四类向量各多少、共 6223 个向量"，不是"系统高危"。**
把统计读数当警报念 = 制造假事故。

**③ `critical: 55` 不是"自有代码有 55 个严重漏洞" —— 先看 `location` 落在哪棵树。**
本轮排序后前 3 条 critical 的 `location` 原文是
`.shadow-repo\tools\codex-scripts\verify_roothfix.py:113`（命令注入）·
`.shadow-repo\tools\codex-scripts\verify_shapes_remaining.py:82`（密钥泄露）·
`_upstream\Scrapling\scrapling\spiders\checkpoint.py:74`（反序列化）；
而这两棵树实测存在（`.shadow-repo` 627 个 `.py`、`_upstream` 889 个 `.py`），
且**不在排除名单里**（名单排的是 `lib/site-packages/node_modules/.git/store/archive/__pycache__` 等）。
⇒ 图鉴与 README 写的"扫描自有代码"是**相对口径**：**念数前先按 `location` 分树**，
把"镜像副本 / 上游 vendored 代码"与"框架自有代码"分开再报。

**④ `VULN-####` 不是稳定追踪号 —— 别拿它跨轮对账。**
`id` 是扫描过程中按 **append 顺序**生成的，之后才按（严重度, location）排序。
实测两轮读数不同：默认扫的前 3 条是 `VULN-0461 / VULN-0462 / VULN-0033`，
而 `sec_chain` 自动扫那轮给出的是 `VULN-0070 / VULN-0069 / VULN-0031`。
⇒ **跨轮追踪要用 `location`（文件:行）**，`id` 只在**同一份返回内部**有意义。

**⑤ 外层 `status: "ok"` ≠ 结论 —— 结论在本体字段里。**
`sec_scan` 的结论是 `total / critical / non_production / truncated`；
`sec_defenses` 的结论是 `defense_status` 与 `checks[].ok`；
`sec_chain` 的结论还要**带上 `material_source`**（`auto_scan` 与 `supplied_empty` 的"未发现链"不是一回事）。
⇒ 只看退出码或外层状态就下结论 = 把"发现了问题"或"我根本没看"读成"一切都好"。

---

## 6. 🔴 安全红线（这一节照做，不许变形）

1. **凭据零明文**：规程、日志、聊天、审计里**都不许出现任何明文凭据**。
   只报 **"已配 / 未配"**；连长度、前后缀、来源行都别报。
   （`sec_llm` 的密钥只从 `.env` 的 `ABLITERATION_API_KEY` 读，源码明文写着"不进源码不进日志"。）
   要给人看就按 `sk-a1b2****` 的掩码口径，且**仅在确有必要时**。
2. **不绕授权门**：`sec_llm` 缺 `external_llm` 就**如实报缺**；
   不许直接 `import abl_gateway` 调 `chat()`、不许绕过 `run_task`、不许找旁路。
   **绕门拿到的读数一律不许写进任何报告**。
3. **不改 `security/policy.py`**，不改验收器（`verify-distill.py`），不改 `omni.py` 的登记表
   （登记由主人统一做）。**不给自己发授权**，也不替别人发。
4. **扫面/取数要说清读什么写什么**：照 §4 那张表报 ——
   "读的是仓内 `.py` 全文 / 写的是无 / 留痕是审计两笔"，**不许含糊成"就是扫了一下"**。
5. **本域能力不许被用来"打别的东西"**：`sec_surface` / `sec_scan` 只扫**本仓自有代码**；
   `sec_llm` 是"问黑客大脑"的通道，**数据出机器**，要发之前先过人这一关。
6. **发现真漏洞不许声张式广播**：先如实报给主人（含 `location`），由主人定处置；
   **不许把含密钥原文的 `match` 字段贴到聊天里**（`sec_scan` 的 `match` 会带上命中行片段）。

---

## 7. 用法纪律（照做）

1. **调之前先静态查门**（`policy.evaluate`），别用"撞一次门"当发现手段。
2. **只读的位必须真跑一次再报**：`sec_surface` / `sec_scan` / `sec_chain` / `sec_defenses`
   都是零作用域可直跑 —— **有返回字段就不许靠猜**（本规程 §2 的每个数字都是真跑出来的）。
3. **要授权的不许绕**：报 `missing_scopes` / `reason` / `how_to_grant` 原文，
   **本体读数写"未验"并说明缺哪个作用域**。
4. **`sec_defenses` 按"带探针的写操作"对待**（门不拦 ≠ 纯只读）：知道它会短时落盘、会自清、账上留痕。
5. **`sec_scan` 给足超时**（本轮实测 ≈4 分 44 秒，不是 README 的 6 秒），
   且**不要在一次调用里反复全仓扫**（`sec_chain` 不给料还会再扫一遍）。
6. **不确定就复跑对比**：同一位连跑两次，比 `location` 集合而不是比 `VULN-id`（§5 ④）。

---

## 8. 诚实账（未验清单 —— **不许改写成"能"**）

| # | 没验的东西 | 卡在哪 |
|---|---|---|
| 1 | `sec_llm` 的**本体返回**（`content` / `reasoning` / `model` / 用量） | 缺 **`external_llm`**；授权只能主人在终端发，AI 无权自发 ⇒ **不绕门** |
| 2 | `sec_scan` 的 `severity` 过滤与 `limit` 分支 | 只跑了默认（`severity=medium`、`limit` 默认 20）；单轮 ≈5 分钟，本轮不重复烧 |
| 3 | `sec_scan` 的 `include_non_production=true` 分支 | 未跑（静态读出会连 `.scratch`/`.backups`/`archive`/`tests` 一起扫并逐层报数） |
| 4 | `sec_defenses` 的**缺口分支**（有防线不生效时长什么样） | 本轮 5/5 全过；不制造缺口就读不到缺口形态 |
| 5 | `sec_chain` 传**非空真实 `vulns` 清单**（`material_source="supplied"`）分支 | 只跑了 `auto_scan` 与 `supplied_empty` 两支 |
| 6 | `policy.authorize` 的**受信主人会话直通**分支 | 本会话是非受信路径（`sec_llm` 被门拒已证）；CLI/GUI 主人会话未跑 |
| 7 | `sec_surface` 的 `target`（指定子树）分支 | 只跑了默认全仓；且**不存在的 target 会静默回落全仓**（未单独验证回落行为） |
| 8 | `sec_surface` 的 `auth_boundaries` 是否计入 `risk_score` | **读数可推**（`risk_score` 公式里没有它，但 `total_vectors` 里有）—— 源码静态读出，**未用实验证实** |

**这份账与 §2 的"✅ 真跑通"是两回事**：§2 的 ✅ 都有上面的真实返回字段撑着；
本表 8 条**都没有**，不许在别处写成"能"。

---

## 9. 验收（做完怎么证明真的做了）

1. **机器复核**：
   `py -3.14 tools/codex-scripts/verify-distill.py --domain security --skill gbt-security`
   —— 它查：两份产物存在且**逐字节同哈希** / frontmatter 有 `name` + `description` /
   规程点名的能力位在图鉴里真存在 / **该域每个能力位都被点到**；
2. **五位逐个复跑**：4 位只读的必须看到真字段（`sec_surface` 的 `attack_surface`+`total_vectors` /
   `sec_scan` 的 `total,critical,non_production` / `sec_chain` 的 `material_source` /
   `sec_defenses` 的 `passed,total,checks`）；要授权的必须看到 `missing_scopes: ["external_llm"]`，
   **不许假装跑通**；
3. **两份 sha256 一致**（源稿 vs managed 安装件），字节数一致。

---

## 10. 固化与出处

| 什么 | 在哪 |
|---|---|
| 本规程（源） | `<仓>/skills/gbt-security/SKILL.md` |
| 本规程（装机） | `~/.openclaw-autoclaw/skills/gbt-security/SKILL.md`（本仓 AGENTS.md 指定的托管目录） |
| 能力位注册表（**唯一真相**） | `gbt_allinone/caps_registry.py`（`sec_*` 5 条） |
| 分派实现 | `gbt_allinone/api.py`（`sec_surface` / `sec_scan` / `sec_chain` / `sec_defenses` / `sec_llm` 五处） |
| 红蓝双模本体 | `gbt_allinone/security/security_brain.py`（`HackerBrain`：测绘/扫描/链路/防御自检 + 探针自清） |
| 推理网关 | `gbt_allinone/security/abl_gateway.py`（密钥只从 `.env` 读，不进日志） |
| 授权策略（只读） | `gbt_allinone/security/policy.py`（`sec_llm` → `external_llm`；**不许改**） |
| 审计账本 | `gbt_allinone/store/audit.jsonl`（`call` / `ok` / `denied` / `auth_denied` / `pipeline_blocked`） |
| 图鉴数据 | `state/skill_atlas.json`（现扫产物，可 `omni build` 重建） |
| 人话落点 | `omni.py ask "扫一下我自己的代码有没有漏洞"` → 落到 `sec_scan`（`ask` 会标 `✅ 只读无参，可直跑`） |

**纪律**：能力不许只活在**进程内**（动态插件 / 运行中的服务）—— 一重启就没了。
真身必须是盘上文件，且落在**会被读取的目录**；写完必须**验证它真被认出来**。
