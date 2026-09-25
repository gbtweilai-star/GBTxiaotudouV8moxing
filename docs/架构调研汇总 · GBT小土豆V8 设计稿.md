# GBT小土豆V8 · 架构设计稿

> 汇编自六路调研（能力总账 / 授权三态 / 万能耗触手 / 自主运行链 / 谋划与策略 / 赚钱闭环）
> 本稿只写盘上能追到出处的事。凡"未读"一律标明，不用常识补。
> 汇编纪律：全程只用 read / grep / glob，未起任何本地进程（无 pwsh、无 python、无浏览器）。

---

## 0. 证据等级标记（读这份稿子前请先认这三个记号）

| 记号 | 含义 | 强度 |
|---|---|---|
| **[实测]** | 本汇编轮**亲自读过该行**并核对一致 | 最强：可复现 |
| **[触手]** | 来自六路调研的 `files_read` 内文件，本汇编**抽样复核过同族结论**，但该条具体行未逐行重读 | 中：出处可信，未逐字复验 |
| **[推断]** | 由已读代码推出，**未运行验证** | 弱：需实跑才能定性 |
| **[未读]** | 相关文件本轮及六路均未打开 | 无：写进"无法确认"清单 |

**本汇编的独立复核（[实测] 部分，共 9 项）**

| # | 复核项 | 结果 |
|---|---|---|
| 1 | `caps_registry.py` 能力字典键 | **147 个**（:13–:940，逐行列出） |
| 2 | `api.py` 中 `if kind ==` / `if kind in` | **135 条**（其中 :1080 是禁用闸，非路由 ⇒ 派单式子 134 条） |
| 3 | `auth_gate.SCOPES` 发卡名单 | **15 项键**（:30–:57） |
| 4 | `policy.SCOPE_DESCRIPTIONS` 说明表 | **15 项键**（:23–:38）——与发卡名单**不对称**，见 §1.5-④ |
| 5 | `policy._READ_ONLY_TENTACLE` 免卡名单 | **18 项元素**（17 个名字 + 空串 `""`，:40–:44） |
| 6 | `PARAM_REQUIRED` 入参契约 | **19 条键**（:972–:1014） |
| 7 | `policy.evaluate` 动作取值 | `op or action or method`，且 `str(...).lower()`（:122） |
| 8 | `api.py` 触手派单取值 | 只认 `action or method`，`op` 仅供 `caps` 快捷口（:267, :270） |
| 9 | `store/schedules.json` | **仅 1 条**：`persona-evolve` / 600 秒 / enabled / last_status=ok（:2–:11） |

> ⚠️ **一处更正（六路之一计数有误）**：触手二在 notes 里写"auth_gate.py:29-58（SCOPES 14 项）"。**实测为 15 项**（osint_private、owner_control、process_execute、filesystem_write、remote_device、deploy_publish、network_private、browser_control、desktop_control、device_control、external_llm、data_export、privacy_read、audio_output、audit_read）。本稿按 15 采用，其余结论不受影响。

---

# 一、任督二脉 —— 授权三态表

## 1.1 唯一真值路径（照 api.py 实序）

```
run_task(kind, payload)
 └─ api.py:1080    kind in DISABLED_CAPS ? ──── 是 → status=denied   ← 在授权门之前
 └─ api.py:1086    kind in BENIGN_CAPS ? ────── 否 → unknown capability
 └─ api.py:1098    policy.authorize(kind, payload)
      └─ policy.py:375  decision = evaluate(kind, payload)
           └─ policy.py:122  op = (op or action or method).lower()
           └─ policy.py:123-124  scopes=[]  risk="low"       ← 免卡是"默认值"
           └─ policy.py:129-141  只有 add() 被调用才产生作用域
      └─ policy.py:376  if not decision.restricted or is_trusted() → 放行，0 卡
      └─ policy.py:384-386  auth_gate.check_and_consume_many(scopes)  逐条消耗
 └─ api.py:1130    preflight.before_action(...)                      ← 第三层闸
```

**两个前置事实必须先说清，否则整张三态表会被读错：**

1. **三态只对"非受信路径"成立。** 可信主人会话（CLI / GUI / 已鉴权本地服务）走 `policy.py:376` 的 `is_trusted()` 分支，**对全部 158 位直通**。
2. **"免卡"不是判定出来的，是默认值。** `evaluate` 起手 `scopes=[] / risk="low"`（:123-124），**104 个能力位在 policy.py 里一行都没有** ⇒ 永远 scopes=()、risk=low ⇒ 免卡。免卡这一档由**策略层的沉默**定义。

## 1.2 总账（口径先定）

| 项 | 数 | 状态 |
|---|---|---|
| 良性能力位 | 147 | **[实测]** caps_registry.py:13–:940 |
| 禁用能力位 | 11 | **[实测]** :951–:963 |
| **合计** | **158** | **[实测]** |
| 领域标签（良性侧） | 29 | [触手] |
| 领域标签（运行时） | 30（多一个 `dangerous`） | [触手] caps_registry.py:1032 给禁用项现场贴 |

## 1.3 三态主表（**口径 = 空载荷默认态**）

| 态 | 位数 | 说明 | 证据 |
|---|---|---|---|
| **① 免卡** | **120** | 104 位 policy 零条目 + 16 位动态默认落此 | [触手] |
| **② 要授权** | **27** | 23 位恒挂 + 4 位动态默认落此 | **[实测]** policy.py:225-229 等 |
| **③ 禁用** | **11** | 无路 | **[实测]** caps_registry.py:951-963 |
| **合计** | **158** ✓ | | |

> **口径分歧请显式选用**：若改按"**任一调用形态的最大授权**"统计，则 ② 要授权 = **43 位**（23 恒挂 + 20 动态可挂），① 免卡 = **104 位**。两个口径都自洽，差的是那 20 个动态位算哪边。本稿主表用空载荷默认态。

### ② 要授权 · 恒挂 23 位（**[实测] 抽查**）

| 能力位 | 作用域 | 出处 |
|---|---|---|
| `mcp_connect` / `mcp_call` | `process_execute` | **[实测]** policy.py:155-158 |
| `pipeline_submit` / `pipeline_rollback` / `mirror_ascend` / `mirror_rewind` / `one_key_deploy` / `mirror_release` | `deploy_publish` | **[实测]** policy.py:225-227 |
| `one_key_deploy` / `mirror_release` | ＋`process_execute`＋`filesystem_write` | **[实测]** policy.py:228-229 |
| `mirror_simulate` / `mirror_parity` | `filesystem_write` | **[实测]** policy.py:233-236 |
| `mirror_rehearse` | `process_execute`＋`filesystem_write` | **[实测]** policy.py:237-238 |
| `devour_github` / `devour_pulse` | `data_export`＋… | [触手] policy.py:269-272 |
| `llm_chat` / `sec_llm` / `autopilot` / `think_loop` | `external_llm` | [触手] policy.py:273-274 |
| `audit_query` | `audit_read` | [触手] policy.py:303-304 |
| `codex_chat` / `codex_thread_new` / `codex_turn_send` / `codex_interrupt` / `codex_models` | `process_execute`（`turn_send` 与 `chat` 另加 `external_llm`） | [触手] policy.py:311-324 |

### ③ 禁用 · 11 位（不是"更硬的卡"，是"没有路"）

`paywallbuster` · `data_hijack` · `remote_domain` · `onboarding_gate` · `keylogger` · `screen_sniff` · `device_takeover` · `pentest` · `asset_vault_freeze` · `credential_steal` · `social_eng`

**[实测]** caps_registry.py:951-963（11 项键与理由逐条在册）；`api.py:1080` 在任何派单之前就拒。
**[触手]** 11 项**均不在 SCOPES**，`check_and_consume_many` 对未注册作用域一律拒 ⇒ **任何授权都解锁不了**；`cli_grant_interactive` 也先查 SCOPES，**连发卡动作都做不出来**。
**[触手]** "禁用名单只加不减"是成文纪律（CODING_DISCIPLINE.md:39）。

---

## 1.4 这条"脉"实际断在哪（五处，逐条点名）

### 断点 ① ★★★★★ 新增能力**默认免卡** —— 这是最大的结构性风险

- **机制**：免卡靠"policy 不提"，不是靠显式声明（**[实测]** policy.py:123-124 起手空 + :129-141 唯一 add 出口）。
- **后果**：任何新登记的能力位，**只要忘了在 policy.py 写一个 `elif kind ==`，它就是免卡的**。没有一处静态断言会拦住它。
- **对照**：政策要求的"该收口的收口"靠人记得写；写漏了没有任何噪声。
- **这是设计缺陷而非 bug**：它的失败形态是**静默**的。

### 断点 ② ★★★★★ "声明有写面"与"策略沉默"并存 —— 8 位漂移族

[触手] 以下 8 位在 policy.py 零条目（⇒ 免卡），但注册表 desc 自述有写面／花钱／不可逆：

`auto_publish`（"发布过门…默认 0 张令牌"）· `cloud_pc`（PROVISION/RELEASE"逐个标花钱与不可逆"）· `stigmergy`（DEPOSIT 会写；policy.py:348-350 注释**明确把它当零作用域先例引用**）· `persona_kernel`（"evolve 是唯一写口"）· `h3_video_gen` / `a1art_skill`（"结果必须落盘"）· `absorb_loop`（三阶段闭环含清场）· `libtv_workflow`（run/batch_run）。

> **诚实边界**：desc 里写了 ≠ 实现真的做了。要定性必须逐个读实现体 —— **本轮未读**，属"声明面与策略面漂移"，不属"已证实越权"。

### 断点 ③ ★★★★☆ 派单键位不一致（**本汇编最重要的代码级发现**）

| 层 | 取动作名的键 | 出处 |
|---|---|---|
| **policy 判权** | `op` → `action` → `method`（op 优先） | **[实测]** policy.py:122 |
| **api 派单** | `action` → `method`（**不看 op**） | **[实测]** api.py:270 |
| **preflight 判权** | 只看 `action` | [触手] preflight.py:167-169 |

**[推断]** 因三者不同源，载荷 `{"op":"see","action":"click"}` 会：
- 被 **policy 判为免卡**（读到 `op="see"`，`see` 在免卡名单 policy.py:41）→ 0 卡放行；
- 却被 **api 真派单成 `click`**（api.py:282 `TB.invoke(action, …)`）→ 桌面点击真的发生。

**这是权限模型级的键位错位**，不是文档瑕疵。**未实跑验证**（受本轮只读纪律约束），但两侧代码证据完整、方向一致 —— 建议列为**优先实跑对拍项**。

### 断点 ④ ★★★☆☆ 免卡名单的"名义 vs 实收"，且混进一个方向相反的

- **名义 18 项**（**[实测]** policy.py:40-44）。
- **[触手]** 真身上真实存在的只有 **9 个**：`see` `vision_snapshot` `screen_size` `screenshot_diff` `read_text` `list_windows` `process_list` `see_active_window` `monitor`。
- **[触手] 8 个是空壳名（幽灵名，这只手根本没有）**：`status`（只存在于另一套中枢 `OmniController`，不在 `OmniTentacle` 的 MRO 上）· `eye` / `manifest`（是 bridge 的模块级函数）· `window_list` · `window_info` · `active_window` · `detect`（`detect_dialog` 的残缺名）· `ocr`（**已于 2026-08-03 被明确移除**，omni_process.py:465-468）。
- **[触手] ★ `monitor` 方向反了**：它免卡，却按 `triggers[].action` 去 `getattr` 触手任意方法循环执行（omni_window.py:298-335），能驱动 `click_text` / `dismiss_dialog` / `type` ⇒ **免卡却能写**。这是免卡栏里**唯一需要立刻收紧**的一条。
- **[推断]** 空串 `""` 虽在免卡集，但 api 层无 action 时直接 `ValueError`（**[实测]** api.py:272-274）⇒ 这条空名免卡**不可达**。

### 断点 ⑤ ★★★☆☆ 门之外还有闸，且口径有三份

- **第二层：落点闸**。`one_key_deploy` 未显式声明落点直接 `blocked`，**有 `deploy_publish` 授权也过不去**（[触手] qiankun.py:258-266）。⇒ **要授权 ≠ 一定过。**
- **第三层：preflight**。api.py:1130 在授权通过后调 `before_action`（[触手]，其返回值处置方式**未读全文**）。
- **第二份范围表**：`room_space.py:55-61` 另有一份 19 项 `_ROOM_CAPABILITIES`（**[实测]**），而 `policy.py:242-251` 只覆盖其中 12 项；**7 项（`room_scan` `room_frame` `room_replay` `room_sync` `room_status` `room_registry` `room_resolve`）policy 无条目**。
- **19 个"有策略、无能力位"的孤儿**：policy.py 为 `room_*`（12）· `collab_*`（4）· `peer_register` / `peer_request` · `notion` 声明了作用域，但**这些名字都不在 158 位里** ⇒ 经 run_task 会在 api.py:1086 判 unknown，**根本走不到 policy**。

---

## 1.5 附表：四个"小口径但会咬人"的漂移

| # | 现象 | 证据 | 性质 |
|---|---|---|---|
| ① | **契约表行号大面积失真**：PARAM_REQUIRED 的 15 处 api.py 引用中 **14 处指错**（唯一准确是 `osint_scan` 的 :118） | **[实测]** caps_registry.py:973-1005 vs api.py 实际 raise 行——如 `sec_llm` 写 210 实际 **217**、`autopilot` 写 229 实际 **236**、`llm_chat` 无条目而实际 raise 在 **250** | "有据但不可核" |
| ② | **必挂缺参漏登记 3 项**：`llm_chat`（**[实测]** api.py:249-250 无 prompt 即 ValueError）· `mcp_connect`（**[实测]** :749-750 需 server+command）· `mcp_call`（**[实测]** :763-764 需 server+tool）——三项都注册、都有路由，却**都不在 PARAM_REQUIRED** | **[实测]** caps_registry.py:972-1014 无此三键 | **实质断链**：按契约表发空调用必失败 |
| ③ | **两份作用域表不对称**：policy 说明表 15 项**无 `osint_private`**（policy.py:23-38），auth_gate 发卡名单 15 项**无 `owner_control`**（auth_gate.py:30-57）。而 policy 的 `add()` 实际会产出 `osint_private`（**[实测]** policy.py:214），永不产出 `owner_control`（它只被 auth_gate 消费） | **[实测]** 三处 | 文档面漂移，功能不致命 |
| ④ | **死代码**：`pipeline_submit` 分支内 api.py:866-872 与 :858-865 **逐字重复且在 `return` 之后永不可达** | **[实测]** | 将来只改一份 → 静默走旧逻辑 |
| ⑤ | **风险档不一致**：`osint_private` **不在** policy.py:134-138 的高危名单 ⇒ `osint_scan` 命中内网 risk=**medium**；而同为"访问内网"的 browser 走 `network_private` ⇒ risk=**high**。同类动作两个档 | **[实测]** policy.py:134-138 | 口径不一致 |

---

# 二、能力栏 —— 面向主人的分栏设计

## 2.1 分栏原则

**必须分四栏，不能只分三栏。** 原因：三态表回答的是"**要不要卡**"，而主人真正问的是"**我现在能不能动**"。这两件事在盘上是**脱钩**的 —— 存在整整一族"免卡、却动不了"和"有路由、却必失败"的能力位。把这类塞进"免卡栏"是**把纸面能力说成真的**，违反铁律。

## 2.2 四栏表

### 栏 A · 免卡且真能动 —— "现在就动得了的手"

| 层 | 内容 |
|---|---|
| 148 个能力位里的免卡 120 位 | 见 §1.3 ① |
| **但其中"真能动"需再筛**：至少 8 位带"只读骨架·门"或"待接线"自述 | `libtv_skill` `a1art_skill` `libtv_workflow` `h3_video_gen`（"只读骨架·门"）· `create`（"文本出口**待接线**"）· `vision`（"**需外部依赖时留待接入**"）· 加上 [触手] 归为 D 档的一族 |
| **触手内层"真能动"的手（9 个真身方法）** | `see` `vision_snapshot` `screen_size` `screenshot_diff` `read_text` `list_windows` `process_list` `see_active_window` + ⚠️`monitor` |

> **栏 A 必须带一个红色小标**：`monitor` 虽在免卡栏，但它能驱动任意写动作（§1.4 断点④）。

### 栏 B · 过门可用 —— "拿一张卡就能用"

27 位（§1.3 ②）+ 动态带里默认落此的 4 位（`vision` `voice` `bluetooth` `bt_control`）。
**栏 B 的诚实提示**：`one_key_deploy` **即使拿到卡也可能被落点闸拦**（§1.4 断点⑤）⇒ 栏 B 内部要再标一档"卡之外还有闸"。

### 栏 C · 禁区 —— "永久封死"

11 位（§1.3 ③）。**读法提示**：这 11 位会以 `domain="dangerous"` 出现在能力清单里（caps_registry.py:1032），清单上看得见、**但永远调不动**。

### 栏 D · 看起来能、实际不能用 —— **本栏是本次调研最值钱的产出**

| 子类 | 位数 | 表现 | 证据 |
|---|---|---|---|
| D1 免卡但会写 | 1 | `monitor` 可零授权驱动写动作 | [触手] omni_window.py:298-335 |
| D2 免卡名是空壳 | 8 | 幽灵名（含已被移除的 `ocr`） | [触手] policy.py:41-43 vs 真身 def 扫描 |
| D3 有路由但空调用**必失败**且契约漏登记 | 3 | `llm_chat` `mcp_connect` `mcp_call` | **[实测]** api.py:249 / :749 / :763 |
| D4 条件性缺参未登记 | 2 | `root_fix` op=diagnose 需 symptom（:517-519）· op=pit_check 需 keywords（:529-530） | [触手] |
| D5 有路由但后端自认未就绪却标 `enabled` | 2 | `create`（caps_registry.py:497 自述"待接线"）· `vision`（:580 自述"需外部依赖时留待接入"） | [触手] |
| D6 有路由但只给读数不执行（只读骨架/门） | 一族 | `mirror_*` 多位 · `libtv_*` · `cloud_pc` · `auto_publish` · `h3_video_gen` · `stigmergy`（文本自述） | [触手] |
| D7 **只读却要卡**（反向） | ~37 | `read_text_fast` `read_region_text` `read_console` `find_text` `see_window` `live` `detect_dialog` `wait_*` `get_log` `app_running` `domain_index` `domain_read` `grab_value` `extract_ui_elements` `self_diagnose` 等 | [触手] policy.py:40-44 名单对照真身 def |
| D8 **声明了动作、路由层把参数吞掉** | ≥9 | `wave_probe`（desc 说回报 trigger_mode 与盲区，api.py:328-330 只调 `measure()`，payload 完全不透传）· `trace_store`（:325-327 忽略 payload）· `dream_replay`（:331-333）· `capability_net`（:505-512）· `mirror_scan`（:612-614）· `ghost_guard`（:890-892）· `music_publishing`（:415-418 只透 op）· `cross_scan`（:542-544 只认 deep）· `inventory`（:547-549 只认 fix） | [触手] |

> **栏 D 的一句话**：**"入口在" ≠ "能用"**。D3/D4 是真正会咬人的（调用方按契约表发空调用，撞回一个看不懂的 `user_error`）；D7 是**让主人白掏卡**（只读动作也要消耗 `desktop_control`）；D8 是**能力缩水但没人知道**。

## 2.3 面板落地建议（三条，均为本稿设计判断而非盘上现状）

1. **每栏必须带"凭据列"**：能力行上直接标 `requires_params`（契约表已有，caps_registry.py:1024-1028）与一行 `params_hint`。**面板据此拒绝空调用** —— 这正是 PARAM_REQUIRED 注释里自己写的立项理由（caps_registry.py:966-969）。
2. **栏 D 必须显式存在**，不能把 D3–D6 混进栏 A/B。建议标签：`纸面（后端未就绪）` / `缺参（契约漏登记）` / `参数不可达`。
3. **栏 A 的"真能动"要用运行时读数刷新**，不能用静态表。权威清单在 `caps_called_audit`（注册于 caps_registry.py:820-825，路由于 api.py:350-353）与 `selfscan`、`capability_net`。**本轮受只读纪律约束未取该读数** —— 面板首版应先跑它，再定栏 A。

---

# 三、自主运行 + 谋划 + 策略

## 3.1 现有链子长什么样（实测读数）

**唯一真在转的环：`persona-evolve`（10 分钟一次）** — **[实测] store/schedules.json:2-11**

```
schedule.tick()  ── 读 store/schedules.json，到期跑 engine.run_workflow(name)
  └─ workflow "persona-evolve"，唯一节点 kind=persona_kernel op=evolve
       events=[idle_reflection, state_probe]                    [触手] store/workflows.json:448-464
       └─ persona_kernel.py:311-312  _me.observe(ev) + _me.mental_cycle(ev)
            └─ mind_engine.observe                         [触手] mind_engine.py:1496
                 ├─ locked_json_update → store/mind_state.json   :1546
                 ├─ audit("mind_event")                          :1551
                 ├─ life_archive.remember_mind_event             :1568
                 └─ _communication_decision（含 should_pause）    :1522
```

- **[实测]** 该条 `every_seconds=600`、`enabled=true`、`last_status="ok"`、`last_run_at="2026-09-22T09:01:39"`。
- **[触手]** mind_state.json:4 的 `updated_at` 与 `last_run_ts` **同一次运行**推进 ⇒ 链子是通的。
- **诚实边界**：这是**产物级证据**（时间戳 + wf_runs 记录），**不是活进程证据** —— 本轮不能读进程表。谁在驱动 `schedule.tick()`（常驻循环？外部心跳？）**未读到任何配置或入口**。

## 3.2 断在哪（逐条点名）

| # | 断点 | 证据 | 强度 |
|---|---|---|---|
| 1 | **autopilot 的"修复"是空转**：后续轮只把目标文本加一句后缀（`f"{goal}（第{rd}轮修复…）"`），**从不把上一轮 selfscan 的 findings 或失败节点名带进下一轮 plan**（`_llm_plan` 签名只有 goal） | autopilot.py:126 vs :62-91 | [触手] |
| 2 | **判据断**：唯一的继续/收工判据是**全局** selfscan verdict + body.status，**完全不看自己工作流的逐节点失败**（节点被门拒了也不触发修复） | autopilot.py:145-147 记 nodes vs :151-154 只读 verdict | [触手] |
| 3 | **触发面断**：`schedule.tick()` **只会** `engine.run_workflow`（schedule.py:99），**永远不调** `lr_tick` / `long_run_supervisor.tick` / `devour_pulse` | [触手] schedule.py:85-113；**[实测]** schedules.json 仅 1 条 | [触手]+[实测] |
| 4 | **longrun 执行器真、驱动假**：`lr_tick` 唯一非测试调用方是 **GUI 一颗按钮**（app.py:219 `run_task("lr_tick", {"max_tasks": 3})`）；`store/tasks.json` 58 条**全是 2026-09-13 起的测试任务**，**无一条 pending** | [触手] app.py:219、tasks.json 全量 | [触手] |
| 5 | **监督器只有账本没有腿**：`long_run_supervisor` 源码自述"只管理调度状态，不创建守护进程、不执行外部命令"，**外部调度器周期性调用 tick** —— 而这个前提在仓里不成立：产物目录 `store/long_runs/` **不存在** | [触手] long_run_supervisor.py:1-5, :233-249；glob 无结果 | [触手] |
| 6 | **devour 能力真、触发器假**：认知循环完整，但 `last_devour_at` 停在 **2026-09-15**（对比 schedules 最后运行 2026-09-22）；**没有任何 schedule 或工作流指向它**；且 `devour.py:345` 用 `gaps["gaps"].values()` 访问**列表**（:169 返回 list）⇒ 一旦 high-gap 分支被走到即 AttributeError，被 :372 吞成 `ok: False`；`scan_gaps` 的 gap 元素里**没有 priority 字段**，而 :345/:573 都在筛 `priority == "high"` —— **两条独立的断** | [触手] devour.py:169/343-347/372-373/573 | [触手] |
| 7 | **think_loop 的"先推演再执行"跑两遍 LLM**：dry_run 那次与实跑那次是**两次独立调用**，方案可以不一致；it 自身**无轮数/时长上限** | [触手] think_loop.py:53 vs :65、:130-131、:158-164 | [触手] |
| 8 | ★ **心智-执行断（最短的一根待接线）**：mind_engine **已经算得出** `should_pause`（:970-981）并给 `mode="ask"`，但 autopilot / think_loop / longrun **一处都没读它** —— 它只进 state、审计与 pulse 视图 | [触手] mind_engine.py:1522-1533；grep 三链全无引用 | [触手] |
| 9 | **停人等签全在纸上**：文档《长程无人值守协议》定了 2 小时限时（:253）、10 分钟心跳 / 20 分钟判失联（:255-256）、九条熔断含内存>90%（:211-225），而**四条链的代码里一条都没有**（无时长预算、无资源阈值、无依赖熔断分支）。文档自述该协议**尚未生效**（:352-353） | [触手] 四文件全文 + 协议 md | [触手] |
| 10 | **优先级无推导**：只有 `{"high":0,"medium":1,"low":2}` 标签排序 + created_at，priority 由提交方声明，入库只校验合法性 | **[实测]** longrun.py:26, :54-57 | [实测] |
| 11 | **验收标准由调用方给**：`acceptance` 缺省 `["status_ok"]`，未识别判据直接判失败 ⇒ "完成"的定义权在提交方，不在谋划层 | [触手] longrun.py:49, :68, :97-127 | [触手] |

## 3.3 谋划与策略：零件齐、座位缺

**谋划（定目标 / 拆路径 / 排优先级）**

| 环节 | 现状 | 证据 |
|---|---|---|
| 拆路径 | ✅ 有：`autopilot` LLM 提案 + **本地校验器**过滤（能力必须已注册、依赖存在、拓扑无环） | autopilot.py:25-47, :94-109 |
| 定目标 | ❌ **无能力位**：目标与验收标准一律调用方传参 | autopilot.py:114-115；longrun.py:49, :68 |
| 排优先级 | ⚠️ 只有标签排序，无推导 | **[实测]** longrun.py:26 |
| 开工前 | `root_fix.pre_work` 四看 + GO/BLOCK —— 回答"**能不能动手**"，不回答"先做什么" | [触手] root_fix.py:203-232 |

**策略（选打法 / 评风险代价 / 先做哪个）**

| 环节 | 现状 | 证据 |
|---|---|---|
| 选打法 | ✅ **全仓唯一"比较打法"的实现**：mind_engine 多方案预演，四候选各带 risk/reversibility/owner_burden/goal_progress，线性打分 | mind_engine.py:853-919 |
| 评风险 | ✅ 元认知检查：算 margin、confidence、should_pause、mode；**margin<0.08 如实报"判断摇摆"**，高风险+不可逆 ⇒ should_pause=True | mind_engine.py:923-1002（:965-966, :970-981） |
| 带方案 | ⚠️ 只一处：`tactics.escalate`，**方案写死三条**，只在 stalled/failed 触发 | tactics.py:147-175；longrun.py:155-163 |
| 做不做/复用 | ✅ `preflight.before_action` 三问四态（not_guarded/reuse/already_running/acquired），已接在 api 门上 | [触手] preflight.py:958-995；api.py:1130 |
| 措辞分寸 | ✅ `tactics.advise` —— 但**边界写死为只调怎么说**（honesty 明写"不改任何事实与结论"） | tactics.py:111-143 |

**两个座位缺口 + 三条接线缺口**

- **座位 1 · `plan`（谋划口，只读）** —— 缺。拆解可复用 autopilot 的"LLM 只提案 + 本地校验"，验收词表可复用 `_judge` 四种判据（longrun.py:105-127），拓扑校验用 engine 的拓扑层。
- **座位 2 · `weigh`（策略口，只读）** —— 缺。可复用 mind_engine 的打分与 should_pause，只改两处：**候选集由外部供给**（现写死四条）、**权重可审计**（现写死）。
- **接线 A · "先动手再提问"缺第三态 `probe`** —— 现在只有"查/问/做"里的查与问：meta_cognition 红线②把"有缺口"直接变成"**一律拒执行**"（meta_cognition.py:37, :130-141），与 SOUL 的"能试出来的先试"（SOUL.md:30）**口径冲突**。修法：二分之间插第三态——"缺口可被一次**可逆试探**消除 ⇒ 先试一手"，试探强制走 preflight。
- **接线 B · "给意见"缺座位** —— 唯一近似是 think_loop 第 5 步反向延伸，**LLM 一挂就降级跳过**（think_loop.py:98）。而这些读数盘上全都有（`root_fix.patch_debt` 债值、preflight 的 observation、longrun 的指纹停滞、`root_fix.pit_check` 的坑），只是散着。
- **接线 C · "不死板拒绝"缺路径字段** —— 全仓拒绝体是 `{denied, rule, why}`，**why 有、path 没有**；只有 `brain_vault._cannot` 带 `missing` 列表（brain_vault.py:44-46）。

**需要 Owner 拍的取舍点**：SOUL 的"干净利落""分寸感"两条，是否本就该由**表达层（tactics）**而非能力层承担 —— SOUL.md 没写死。

## 3.4 补哪一环能接上（按"改动小 / 收益大"排序）

| 序 | 动作 | 为什么这一步最便宜 | 是否新建模块 |
|---|---|---|---|
| **1** | 把 `should_pause` 接到四条链入口做**前置只读闸** | 判定**已经现成**（mind_engine.py:970-981），只读、不停状态机、不新增授权边界 | 否 |
| **2** | 给 autopilot 补"体检→修复"回路：把上轮 selfscan findings 与失败节点名作为**数据**传进下一轮 `_llm_plan`；并按"同因重复即停"设终止条件 | 直接消灭"假修复" | 否 |
| **3** | 给 autopilot 收工判据加**节点级 denied/failed** 维度 | 别再看全局 verdict 就收工 | 否 |
| **4** | 给 `schedule` 加第二类被调对象（长程 tick），让 `lr_tick` 有节律；`long_run_supervisor.tick` 先只做只读巡检 | 执行体**一行不改**（它们本来就是能力，只缺"谁按时按它们一下"） | 否 |
| **5** | 修 §1.5-①② 的契约漂移（3 个漏登记 + 行号出处） | 面板/调用方立刻受益，纯本地 | 否 |
| **6** | 收敛 §1.4 断点③ 的三处键位口径 | 权限模型级问题，建议先**实跑对拍**再动 | 否 |

**④的门槛纪律（不可省）**：文档已明确 2 小时默认限时、到点自动停（协议:253），且"每个阶段一个原子单元、不跨阶段批量落刀"（:295）；**在阶段级检查点打点器就绪之前，不许把无回滚点覆盖的阶段纳入无人值守**（:352-353）。这条要给硬闸，不能靠自觉。

---

# 四、赚钱闭环（三方向：短视频 / 音乐 / 电影）

> **本稿不含任何收入数字、不含任何爆款承诺、不含任何平台算法判断。**
> 平台名单一处未编 —— 两处来源口径不同、**并排摆着、未做任何合并**（auto_publish.py:54 是**空元组**；music_publishing.py:28-63 的 17 个名字**全部 verified=False**）。

## 4.1 现状：骨架 + 闸是真的，肉是空的 —— **而且空得很有纪律**

**九段拆解**：调研 → 选题 → 创作/生成 → 加工 → 自审 → 发布 → 追踪 → 汇总 → 提现

### 真（六处）

| # | 真的东西 | 证据 |
|---|---|---|
| 1 | 情报的**记账格式 + 禁区优先闸**（禁区命中即 hold，哪怕趋势再多；明写"情报是输入不是指令"） | research_intel.py:151-157 |
| 2 | `media_pipeline` 的**编排 + 九项结构自审**（真读 assets sha256） | media_pipeline.py:148-160 |
| 3 | `account_registry` 的**四条红线机械校验**（不共用账号/不共用凭证容器/只记路径/无主账号不许登记） | account_registry.py:85-109 |
| 4 | `verification_watch` 的**不绕验证立场机械闸**（只允许 api/official_ai/human_in_loop/register_pending 四条路） | verification_watch.py:22, :74-81 |
| 5 | `auto_publish` 的**六道判据函数**（密钥明文/过门/留痕/一人一号/提现/不刷量） | auto_publish.py:69-171 |
| 6 | `platform_client` **这个 HTTP 客户端本身**（stdlib urllib，:8097，重试/幂等） | platform_client.py:71-343 |

### 空（六处）

| # | 空的东西 | 证据 |
|---|---|---|
| 1 | **情报 18 格全空**（`filled: 0 / unfilled: 18`，且注释写"不许假装有情报"） | research_intel.py:75, :85-87 |
| 2 | **生成器未接**（`external_generators_connected: False`）；四个候选生成端全是"只读骨架·门" | media_pipeline.py:80, :82；caps_registry.py:850-861, :892-909 |
| 3 | **发布/追踪/结算三个动作未实现**（一律 `not_implemented` + `requires_external_key`） | auto_publish.py:224-225, :174-179 |
| 4 | **账号表 0 条**（真表不存在，回落骨架，`accounts: []`） | ai_accounts.skeleton.json:20；account_registry.py:54-58, :115 |
| 5 | **收钱段**：钱包目录不在盘上；且 `gbt_allinone/bridge/` 不存在 ⇒ **记账半边断** | 见 §4.3 |
| 6 | **三方向真实产物只到第 1–2 格**：从原始素材到成片到发布版到封面**全部只有 .gitkeep** | glob results |

**三方向各自的卡点**：

- **短视频**：卡在 `03-raw`（生成的原始素材）—— 01-script / 02-storyboard 有真产物。
- **音乐**：卡在 `02-compose`（旋律/作曲）—— 01-lyrics 有真产物。
- **电影**：卡在 `03-shoot` —— 01-screenplay / 02-storyboard 有真产物；**框架侧连对应工序格都没有**（projects/README.md:118 已实测校正"本地抽屉名 = 框架工序名"的旧结论）。
- **共同卡在**：生成器 + 账号（0 条）+ 发布（三个动作未实现）。

> **"空得很有纪律"是什么意思**：每一处空都自带 `honest` / `HONEST_BOUNDARY` / `not_implemented` / `verified: False`，**没有一处假装能用**。现状不是"坏了"，是**诚实的空**。这个区别要保留。

## 4.2 ★ 收钱的闸门在哪：**不是"要卡"，是"这道门压根没建"**

| # | 事实 | 证据 | 强度 |
|---|---|---|---|
| 1 | **policy.py 对整条收钱链路零作用域**：`auto_publish` `media_pipeline` `music_publishing` `brand_outro` `proactive_report` `account_registry` `shared_resources` `verification_watch` `research_intel` `trend_watch` `drama` `*_intel` 全部**无条目** | grep policy.py ⇒ No matches | [触手] |
| 2 | **未列出的 kind 在策略层等于没有门**：起手 `scopes=[] / risk="low"`，空则 risk 保持 low；`authorize` 第一句就是 `if not decision.restricted or is_trusted(): return ok=True` ⇒ 非可信路径 **0 卡放行** | **[实测]** policy.py:123-124, :140-141, :376 | [实测] |
| 3 | **确实挂卡的是"写生产面"，不是"对外发布收钱"**：`deploy_publish` 管的是"部署、晋升、回滚或**写入生产交付区**"（SCOPE_DESCRIPTIONS:28）——**不管把作品发到别人的平台上** | **[实测]** policy.py:225-229, :245-246, :266-268 | [实测] |
| 4 | **发卡侧更硬：主人想发一张"发布卡"也发不出来** —— SCOPES 15 项里**没有 publish / withdraw / price_change 任何一个名字**，未注册名字 `cli_grant_interactive` 直接拒 | **[实测]** auth_gate.py:30-57；[触手] :236-237 | [实测]+[触手] |
| 5 | **收钱链路里唯一的卡是 `external_llm`**（pipeline_submit 带 review/refine_rounds>0 时）—— 那是"把数据发给外部大模型"，**不是"对外发布"** | **[实测]** policy.py:366-367 | [实测] |
| 6 | **auto_publish 自己的六道闸挂在一条不存在的路上**：六个 `check_*` 唯一调用处是 `run(op="gate_*")`，而 `publish` 本身走 `_not_implemented` ⇒ **没有任何执行路径把闸挡在动作前面**（因为动作不存在） | auto_publish.py:209-225 | [触手] |
| 7 | **仓库自己的审计已记录同一事实**："门状态：如实记录为空 … auto_publish %d 动作全无门" | tools/codex-scripts/verify_v21.py:423-426 | [触手] |

> **所以链路上的风险不是"卡住了"，而是"这一段的门压根没建"** —— 只是恰好在同一段上动作也没实现，**两者互相掩盖**。

## 4.3 ★ 三个"超出提问范围但必须报"的发现

1. **收钱闸门是真空（§4.2）** —— 提出假设是"要卡"，对照后真相更硬。
2. **六道闸挂在空路上（§4.2 第 6 条）** —— 将来补 publish 实现时若不显式接线，这六道闸会变成"文档里的闸"。
3. **收款链路的记账半边是断的，且断得很安静**：`platform_client.py` 是盘上唯一真客户端、实现完整，但它依赖的 `gbt_allinone/bridge/` **不存在**，两处 `deposit_bridge` 导入被 `try/except` 吞掉（:234-238 返 `{}`、:245-253 返 `False`）⇒ **发票→用户映射与到账记账都静默不发生**。这是七道缺口里**唯一"有实现、有依赖、失败无声"**的一处，比"未实现"更值得先修 —— **改成如实报缺即可，不必等钱包**。

## 4.4 必须人工的环节（不可代替）

| 环节 | 为什么必须人 | 出处 |
|---|---|---|
| 发布授权 | 不可逆 + 出网；默认 **0 张令牌**，只能逐条确认 | auto_publish.py:44-45, :59-64；media_pipeline.py:216-221 |
| 提现 / 改价 | "钱的动作"，模块默认只汇总、不代提 | auto_publish.py:41, :148-157 |
| 平台账号与凭据 | 一人一号；凭证必须指向 `*.dpapi`，记录只许写路径 | account_registry.py:104-106, :7-11 |
| 实名 / 人机验证 | 只允许四条路；**绕验证被写成机械闸** | verification_watch.py:22, :27-28, :74-81 |
| 出网取证（三方向情报） | 要过 auth_gate 出网授权，且**排在飞书云空间整理之后** | research_intel.py:19；待落刀登记.md:171 |
| 版权/安全/主人过目三断言 | ⚠️ **media_pipeline 收的是调用方传进来的布尔，模块不验出处** —— 这是缺口，不是保障 | media_pipeline.py:178-179, :192-196, :245-247 |
| 外部素材许可 | 没有许可的素材**不许进** 04-cut / 05-master / 06-final；`_shared/licenses/` 当前为空 | projects/README.md:49, :74 |

> **缺口**：以上七处**散在六个模块里，没有一张"哪一步必须人做、做完留什么痕"的汇总表** —— 否则链路上会出现"以为自动、其实没人做"的格子。

## 4.5 一条必须先由 Owner 拍板的架构边界

`gbt_wallet` 的处理方式**不是技术缺口，是架构归属问题**：

- `hygiene.py:210-219` 铁律 10 明确写："**GBT-V8 是单纯的全能 AI 框架。资金/钱包/支付类业务模块不属于框架本体**"，归档地是 `Workspace/03_收款钱包与支付/`，检测到实体即报 `foreign_module`，框架内**只允许优雅降级占位**。
- delivery 报告自报：gbt_wallet "独立项目未迁移（receive_* 优雅降级）"。

⇒ **"收钱"这一段在当前架构里被主动排除在框架之外，是设计意图，不是疏漏。** 所以这一条写成"**需先拍板归位方式**"，而不是"去把它接进来"。

**一处历史文档矛盾**：`docs/fusion-acceptance.md:14, :29` 声称"gbt_wallet 已并入 63/63""receive_* 驱动实测"，与盘上现状（目录已不存在）矛盾 ⇒ 建议标注为**已失效**，否则后来者会照着"已并入"去调一个不存在的模块。

---

# 五、可立即动刀的清单（按"不必新建模块"排序）

| 序 | 动作 | 类型 | 证据锚点 |
|---|---|---|---|
| 1 | 把 `monitor` 从 `_READ_ONLY_TENTACLE` 摘出，或改成**按将要执行的动作动态判风险** | 安全收紧 | policy.py:44 ↔ omni_window.py:298-335 |
| 2 | 补 3 条漏登记的入参契约：`llm_chat` / `mcp_connect` / `mcp_call` | 契约修复 | api.py:249, :749, :763 ↔ caps_registry.py:972-1014 |
| 3 | 修 PARAM_REQUIRED 的 14 处失效行号（并加一条"行号会漂"的机制性提示） | 文档修复 | caps_registry.py:973-1005 |
| 4 | 删 api.py:866-872 死代码 | 清理 | **[实测]** |
| 5 | `should_pause` 接四链入口做前置只读闸 | 接线 | mind_engine.py:970-981 |
| 6 | autopilot 体检 findings 回流下一轮 plan + 节点级 denied/failed 判据 | 接线 | autopilot.py:126, :151-154 |
| 7 | schedule 增加"长程 tick"第二类被调对象 | 接线 | schedule.py:99 ↔ app.py:219 |
| 8 | `platform_client` 在 bridge 缺失时**如实报缺**，不再静默返空 | 诚实性修复 | platform_client.py:234-253 |
| 9 | 修 `devour.py:345` 的 `.values()`（列表当字典用）与 `priority` 字段缺失 | bug 修复 | devour.py:169 ↔ :345, :573 |
| 10 | 新增 `publish_external` / `money_movement` 作用域并**同步注册进 auth_gate.SCOPES** | **需 Owner 拍板** | auth_gate.py:31-33 记着"只改 policy 不改本表 ⇒ 永久不可授权"的历史坑 |

> 第 10 条**属生产面红线范围**（AGENTS.md：不许改 `security/policy.py`、不许找旁路）。本稿的表述是"**需要新增作用域并同步注册**"，**发放权仍在主人手里** —— 本稿不建议、也不代替 Owner 做这个决定。

---

# 六、"无法确认"清单（因读不到文件 / 不能运行）

## 6.1 因**文件未读**而无法确认

| # | 内容 | 影响 |
|---|---|---|
| 1 | **147 个 handler 的模块内真实实现**（是否真能跑通、签名是否与 payload 匹配、是否真如 desc 所述只读） | ⇒ "147 项全部真可执行"**无证据，本稿不作结论** |
| 2 | `engine.py` 全文（DAG 拓扑、并发度、检查点） | ⇒ "拆路径后的并行度/资源窗口"无法评价 |
| 3 | `mind_engine.run()` 的 op 白名单（只读到 1816-1817 两行） | ⇒ `weigh` 座位**不能假设** `simulate`/`metacognition` 现成可达 |
| 4 | `mind_engine._appraise_state` / `_infer_owner_mind` | ⇒ `weigh` 能否干净复用打分**未验证**；若强耦合，须重写打分 |
| 5 | `api.py:1120-1193` 的 preflight 接线区段全文 | ⇒ before_action 返回值在 api 里怎么处置（reuse 是否真不派单）**未核实** |
| 6 | `preflight.py` 全文（第三层闸） | ⇒ "拿到授权后能不能过"这一层**本稿完全未覆盖** |
| 7 | `mirror_space.py` / `room_space.py` 实现体（后者只读 48-77） | ⇒ `mirror_shape` 不带 path 是否也能写镜像（策略留口）**未取证**；room 的 7 项无策略能力是否落盘**未取证** |
| 8 | `cli.py` 实现 | ⇒ `auth_gate` "唯一发放入口"的**自述未被独立验证** |
| 9 | `omni_controller.py` 的另一套中枢（约 30 个方法） | ⇒ 它是否有别的入口（直接注册 / 别处 import）**未逐条核实** |
| 10 | `vision_bus.py` / `capture_environment.py` / `direction.py` / `desktop_commander.py` / `mcp_bridge.py` | ⇒ 触手派单链下游未读 |
| 11 | `store/audit.jsonl` | ⇒ "哪条链最近真的被调用过"**无审计级证据**，只有产物级证据 |
| 12 | `USER.md` / `MEMORY.md` / `memory/*.md` / `AGENTS.md` 正文 | ⇒ Owner 的决策风格偏好**无一手证据** |
| 13 | `holo_pet/panel_server.py` 与面板前端 | ⇒ 面板上"收钱"这段长什么样**未读** |
| 14 | 工作区根之外的配置（系统计划任务 / 外部 cron） | ⇒ 无法排除"别处在定时调 run_task" |

## 6.2 因**不能运行**而无法确认

- **运行时孤儿清单**：权威读数在 `caps_called_audit` / `selfscan` / `capability_net`，本轮受只读纪律约束**未取** ⇒ 本稿"注册↔路由双向差集 = 0"**仅为静态对账结论**。
- **§1.4 断点③ 的键位错位**：只给出 `policy.py:122` ↔ `api.py:270` 的口径差，**未做运行时验证**。
- **调度进程是否真在跑**：只有产物级证据（时间戳 + wf_runs），**无活进程证据**。
- **要授权 27 位的授权态**：全部来自**源码静态阅读**，**没有跑过 `evaluate()`**。
- **8097 端口是否在跑 / `auth_grants.jsonl` 里有几张卡 / tests 是否真绿 / compose 是否真落盘**：**全部未验**。
- **`allow_private` 载荷存废**：`auth_gate.py:18` 注释写"原 allow_private 直通开关废止"，但 `policy.py:187-211` 仍会置 `decision.allow_private=True`，tests 仍在传 ⇒ **未读 osint 实现，无法断言现在是否仍被消费**。

## 6.3 方法学边界（诚实声明）

- **目录存在性来自 glob，不是目录枚举。** glob 只返回文件、不返回目录 ⇒ `gbt_wallet/**`、`gbt_allinone/bridge/**`、`**/wallet_adapter.py` 的"No files found"严格说是"**无文件**"而非"目录必不存在"。但 `bridge/` 若存在则 `platform_client.py:234/:245` 的导入应能成功，而代码把它包在 `try/except` 里返回空 —— **两处证据同向**。
- **六路调研各自的"未读"清单已并入 §6.1**，本稿未做二次压缩，以免把不确定说成确定。

---

# 七、一句话结论（给主人）

1. **脉没断在"注册↔路由"上** —— 147 个登记名 100% 有派单分支，双向差集为 **0**（**[实测]** 147 键 ↔ 135 条 `if kind`）；**脉断在权限模型本身**：新增能力**默认免卡**，104 个能力位在策略层一行都没有，免卡由"沉默"定义。
2. **能力栏必须分四栏**，因为盘上存在整整一族"**免卡却动不了**"和"**有路由却必失败**"的能力位（D1–D8）；把它们塞进"免卡栏"就是把纸面当真的。
3. **自主运行：只有一条环真在转**（`persona-evolve`，**[实测]** 600 秒 / last_status ok）——但它的产物是**情感与阅历状态，不是任务产出**；autopilot / longrun / devour / 监督器四条"自主腿"**全部缺节律驱动**，最短的一根待接线是 `should_pause`（判定现成、没人读）。
4. **赚钱闭环：骨架 + 闸是真的，肉是空的 —— 空得很有纪律**（每处空都自带 honest 标记）；**收钱那一段的门压根没建**，而 `auth_gate.SCOPES` 里连 `publish` 这个名字都没有 ⇒ **不是"发布要卡"，是"想发卡也发不出来"**；记账半边**断得最安静**（有实现、有依赖、失败无声），建议先修它。
