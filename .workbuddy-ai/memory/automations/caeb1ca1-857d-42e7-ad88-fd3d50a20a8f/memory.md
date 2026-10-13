# GBT小土豆V8 · 6 小时自检环 — 执行记忆

## 2026-10-12 18:23（GMT+7）第八次执行
- 五步全跑。**红项 3 条**（面1/2/3 全绿；面4 ok=false 22 位缺腿；面5 红 2）。与 12:15 第七次完全同源同量。
- 面1 sweep：**全绿**。顶层树 70（扫60/排10）· 单元 35871 · 盲区 0 · 耗时 185.3s。面 E 视觉 7 位/帧追踪 0/锁在；面 F 3 位过门。读数刷新至 18:27:12。
- 面2 framework_state：**✅ 全绿**（registry=267=atlas · undispatched=[] · not_in_atlas=[] · unimplemented=1；绑定 7520 断连 0/0 · 有效触手标签 297；技能源装 89/89；矩阵年龄 0.0h）。
- 面3 tentacle_bind scan：全绿（7520 · 资产缺失 0 · 触手不在册 0）。
- 面4 binding_hook verify：**ok=false — 22 位缺「⑥记忆页」**（comfy_native / delivery_gate / fact_gate / god_view / media_stamp / omni_plug / page_scan / policy_gate / pulse_direct / remote_confinement / repo_publish / ring_context / skill_watch / tentacle_comfy_bridge / tentacle_equip / tool_bay / ux_doctrine / vision_grounding / vision_loop / vlx_flow / warm_switch / welcome）。台账 25 行。修法：`binding_hook.py sweep`。**连续四轮未动**。
- 面5 boot-selfcheck：**红 2** —
  - **判据/云端点闸行为**：rc=1，2 条失败（test_gate_exits_zero · test_json_readout_is_self_consistent）。⑦ 流式+已配 LLM_ENDPOINT 期望 `501 not_implemented`，实读 **`502 upstream_error`**；第二条同源（wired 读 `{"non_stream":true,"stream":true}`）。复跑命令：`python -m unittest gbt_allinone.tests.test_endpoint_gate`（须先设 GBT_STORE_DIR，否则 store 守卫拒跑）。与 06:03/12:15 同源未变。
  - **闸/重启验收单**：9 项**只差 ⑤ 旧 specifier 已清（可选）**（还在 v6/v8，规则要求先重启再清）。①②③④⑥⑦⑧⑨ 全绿（① version=1.9.0 · ② 0.08s · ③ 品牌位 hero/sideMark/sideName/footPanels/footGodview 全 ok · ⑨ 三块上下文全在且 ok=无缺）。
- 面5 其余全绿（护栏三道 · 部署法制 rc=3 不适用 · 编码守门 · 每一页都绑到触手【plugins-mesh 烤于 39.5h 前，仅提示】· 装机副本漂移逐字节一致 · 没有亲跑不许交付 11/15 · 上帝之眼 · 凭据自审 · 断言无恒真 等）。
- 全程只读，未改任何源码。红项留主人决定。
- 备注：G6 规则锁对 `verify-after-restart.py` 亦生效（首跑被拒，单独 Read ≥60 行后通过）。

## 2026-10-12 12:15（GMT+7）第七次执行
- 五步全跑。**红项 3 条**（面1/2/3 全绿；面4 ok=false 22 位缺腿；面5 红 2）。
- 面1 sweep：**全绿**。顶层树 70（扫60/排10）· 单元 35871 · 盲区 0 · 耗时 157.3s。面 E 视觉 7 位/帧追踪 0/锁在；面 F 3 位过门。读数刷新至 12:17:53。
- 面2 framework_state：**✅ 全绿**（registry=267=atlas · undispatched=[] · not_in_atlas=[]；绑定 7520 断连 0/0；技能源装 89/89；矩阵年龄 0.0h）。
- 面3 tentacle_bind scan：全绿（7520 · 资产缺失 0 · 触手不在册 0）。
- 面4 binding_hook verify：**ok=false — 22 位缺「⑥记忆页」**，与 06:03 完全同源同量（comfy_native / delivery_gate / fact_gate / god_view / media_stamp / omni_plug / page_scan / policy_gate / pulse_direct / remote_confinement / repo_publish / ring_context / skill_watch / tentacle_comfy_bridge / tentacle_equip / tool_bay / ux_doctrine / vision_grounding / vision_loop / vlx_flow / warm_switch / welcome）。台账 25 行。修法：`binding_hook.py sweep`。**连续两轮未动**。
- 面5 boot-selfcheck：**红 2** —
  - **判据/云端点闸行为**：rc=1，2 条失败。⑦ 流式+已配 LLM_ENDPOINT 期望 `501 not_implemented`，实读 **`502 upstream_error`**；第二条同源（wired 读 `{"non_stream":true,"stream":true}`）。与 06:03 同源未变。
  - **闸/重启验收单**：9 项**只差 ⑤ 旧 specifier 已清（可选）**（还在 v6/v8）。**较 06:03 大幅收敛**：①②③⑨ 全转绿（① version=**1.9.0** · ② 0.06s · ③ 品牌位 hero/sideMark/sideName/footPanels/footGodview 全 ok · ⑨ 三块上下文全在且 ok=无缺）⇒ `127.0.0.1:3080` 已起（06:03 被拒）。
- 面5 其余全绿（护栏三道 · 部署法制 rc=3 不适用 · 编码守门 · 每一页都绑到触手【plugins-mesh 烤于 33.3h 前，仅提示】· 装机副本漂移逐字节一致 · 没有亲跑不许交付 11/15 · 上帝之眼 等）。
- 全程只读，未改任何源码。红项留主人决定。
- 备注：G6 规则锁对 `verify-after-restart.py` 亦生效（首跑被拒，单独 Read ≥60 行后通过）。

## 2026-10-12 06:03（GMT+7）第六次执行
- 五步全跑。**红项 3 条**（面1/2/3 全绿；面4 ok=false；面5 红 2）。
- 面1 覆盖矩阵 sweep：**全绿**。绑定 7517 · 覆盖 1.0 · 盲区 0 · 顶层树 70（扫60/排10）· 单元 35866 · 耗时 158.6s。面 E 视觉 7 位/帧追踪 0/锁在；面 F 三件套 3 位过门。读数刷新至 06:06:43。
- 面2 framework_state：**✅ 全绿**（registry=267=atlas=267 · undispatched=[] · not_in_atlas=[]；绑定 7517 断连 0/0；技能源装 89/89；矩阵年龄 0.0h）。
- 面3 tentacle_bind scan：全绿（7517 · 资产缺失 0 · 触手不在册 0）。
- 面4 binding_hook verify：**ok=false** — **22 位缺「⑥记忆页」**（comfy_native / delivery_gate / fact_gate / god_view / media_stamp / omni_plug / page_scan / policy_gate / pulse_direct / remote_confinement / repo_publish / ring_context / skill_watch / tentacle_comfy_bridge / tentacle_equip / tool_bay / ux_doctrine / vision_grounding / vision_loop / vlx_flow / warm_switch / welcome）。台账 25 行。**较 10-11 16:04 的 11 位翻倍（新增 11 位）**。修法：`binding_hook.py sweep`。
- 面5 boot-selfcheck：**红 2** —
  - **判据/云端点闸行为（新红）**：闸 rc=1（55 条判据中 2 条失败）。⑦ 流式 + 已配 LLM_ENDPOINT 期望 `501 not_implemented`，实读 **`502 upstream_error`**；第二条同源（wired 读 `{"non_stream":true,"stream":true}` 而期望 `stream:false`）。
    **根因（已定位，非生产故障、是闸与实现不同步）**：`deploy/cloud-10/src/worker.js` L378–414 于 **2026-10-11** 把这个 501 换成**真自托管流式分支**（SSE 原样转发，连不上才返 502）；而闸 `deploy/cloud-10/tools/check-endpoint-gate.mjs` L326–330 **仍钉旧契约**（要求 501 + wired.stream=false）+ `wired` 现读 `stream:true`。闸**未打桩 fetch**（脚本内仅 mesh.fetch），故它真去连 `127.0.0.1:8111`（未监听）⇒ 502。修法（二选一并留主人定）：① 同步闸的判据到新契约（501→200 流式 + wired.stream=true，并给 fetch 打桩）；② 或回退 worker.js 的流式分支。
  - 闸/重启验收单：9 项差 **5 项**（① 宿主机代码换代 ② 目录路由提速 ③ 品牌位生效 ⑨ 三块上下文进进程 —— 均因 `127.0.0.1:3080` 未起「目标计算机积极拒绝」；⑤ 旧 specifier 未清 v6/v8，**可选**，规则要求先重启再清）。其余 ④⑥⑦⑧ 全绿。
- 面5 其余全绿（护栏三道 · 部署法制 · 编码守门 · 每一页都绑到触手【plugins-mesh 烤于 27.1h 前，仅提示】· 装机副本漂移逐字节一致 · 三条铁律 · 上帝之眼 · 接线全连通 · 覆盖无死角且新鲜 · 新增能力双向绑定 · 没有亲跑不许交付 11/15 等）。
- 全程只读，未改任何源码（临时输出已清理）。红项留主人决定。
- 备注：G6 规则锁对 `.mjs` 亦生效；每工具须单独「从第 1 行起 ≥60 行」Read 才放行（并行 Read 不计账本）。

## 2026-10-04 16:26（GMT+7）首次执行
- 五步全跑，**红项 5 条**（步骤4 一条 + 步骤5 四条）。
- 步骤1 覆盖矩阵 sweep：全绿，顶层树 67（扫57/排10），单元 28080，耗时 249s，盲区 0。读数已刷新至 16:25。
- 步骤2 framework_state：✅ 全绿（能力位 217/217/217；绑定 6491，断连 0；技能源装 88/88；视觉面 ok）。
- 步骤3 tentacle_bind scan：全绿（资产缺失 0 · 触手不在册 0）。
- 步骤4 binding_hook verify：**ok=false** — 4 个能力位缺「⑥记忆页」腿：brain_council / collab_gateway / omni_web / room_space。
- 步骤5 boot-selfcheck：**红 4 条** —
  - 判据/部署前接线对账（test_cloud_config_wiring）：A_read_but_undeclared = IMAGE_API_KEY / IMAGE_MODEL / LLM_MODEL / SANDBOX / UNCENSORED_MODEL（均 modules.js）。
  - 判据/凭据自审有牙且在仓里（test_precommit_secret_scan）：.scratch\_baseline_wt\gbt_allinone\tests\test_precommit_secret_scan.py 仍指向 TEMP 副本。
  - 闸/装机副本漂移：v8 与 v9 两份装机副本各 2 文件内容不同（tools/model-turnaround.html、tools/skeleton-viewer.html）。
  - 闸/重启验收单：9 项有 6 项未到位（①宿主机换代②路由提速③品牌位⑦装机副本一致⑨三块上下文⑤旧specifier）——服务 127.0.0.1:3080 未起（连接被拒）。
- 全程只读，未改任何源码。红项均留主人决定。
- 备注：G6 规则锁要求跑工具前先通读说明书（≥60 行），本次已逐工具 Read 头部。

（本文件只记高层结论与红项清单，明细不复述。）

## 2026-10-11 16:04（GMT+7）第五次执行
- 五步全跑。**红项 4 条**（面1/2/3 全绿；面4 ok=false 11 位缺腿；面5 红 3）。较上轮（09:42，红 11）明显收敛。
- 面1 覆盖矩阵 sweep：**全绿**。bindings 7498 · missing 0（上轮 0.9897/missing 30，已消）· 覆盖 1.0 · 盲区 0 · 无理由排除 0 · 顶层树 70（扫60/排10）· 单元 35837 · 耗时 451.4s。面 E 视觉 ok（6 位·帧追踪 0·锁在）· 面 F 三件套 ok。读数刷新至 2026-10-11T16:12:25。
- 面2 framework_state：**✅ 全绿**（registry=254=atlas=254·undispatched=[]·not_in_atlas=[]·unimplemented_registered=1；绑定 7498 断连 0/0；技能源装 89/89；矩阵年龄 0.01h；视觉 ok；舰队在册 0/台账 58）。
- 面3 tentacle_bind scan：全绿（7498 · 资产缺失 0 · 触手不在册 0）。上轮 78 缺失已消。
- 面4 binding_hook verify：**ok=false** — 11 位缺「⑥记忆页」：delivery_gate / god_view / media_stamp / omni_plug / remote_confinement / tentacle_equip / tool_bay / ux_doctrine / vision_loop / vlx_flow / welcome。台账 22 行。修法：`binding_hook.py sweep`。**与 03:40、09:42 同源，连续三轮未动**。
- 面5 boot-selfcheck：**红 3** —
  - 判据/未清故障前提复核（test_reverify_open_faults，failures=2）：**F18 前提已垮**（进程自报 version=1.9.0 · 三块都在 · 缺=无）⇒ 回台账改账；另一条 test_human_review_set_is_pinned rc=1 同源。
  - 判据/没有亲跑不许交付（proof-of-run-check）：D9-框架门 verify **复跑 rc=1 · verdict=red** — 未认领 13（no_passport：gbt_allinone/bluetooth_cap.py · tests/test_iron_rules.py · voice_cap.py · holo_pet/assets/{console,freebuff,gallery,home,tentacle3d,wf-film,wf-movie,wf-music,wf-short-video,workbench}/index.html）＋认领但已过期 3（HEARTBEAT.md · api.py · caps_registry.py）。基线 2026-10-10T06:54:50 · 变更 36 件。
  - 闸/重启验收单：9 项还差 1 项 —— ⑤ 旧 specifier 已清（**可选**）：还在 gbt-potato-master-v6 / v8（规则：重启之后才允许清）。
- 面5 其余全绿（护栏三道 · 部署法制 · 编码守门 · 每一页都绑到触手 · 装机副本漂移逐字节一致 · VLX-Flow 接入 · 重启硬指令 · 三条铁律 · 上帝之眼 · 凭据自审 · 部署前接线对账 等）。
- 全程只读，未改任何源码（临时输出文件已清理）。红项留主人决定。

## 2026-10-11 03:40（GMT+7）第三次执行
- 五步全跑。面1/面2/面3 全绿；面4 ok=false（11 位缺腿）、面5 红 1 条。**较上轮（10-10，红 8）大幅收敛**。
- 面1 覆盖矩阵 sweep：全绿。顶层树 70（扫60/排10）· 单元 34569 · 耗时 271.4s · 盲区 0。视觉面 6 位 / 帧追踪 0 / 锁在；F 三件套 3 位过门。读数刷新至 2026-10-11T03:32:44。
- 面2 framework_state：**✅ 全绿**。registry=254·atlas=254·undispatched=[]·not_in_atlas=[]·unimplemented_registered=1。绑定 7568 断连 0；技能源装 89/89；视觉面 ok；舰队在册 0/台账 58。**上轮 `welcome` 红项已消**。
- 面3 tentacle_bind scan：全绿（7568 · 缺失 0 · 不在册 0）。
- 面4 binding_hook verify：**ok=false** — 11 位缺「⑥记忆页」：delivery_gate / god_view / media_stamp / omni_plug / remote_confinement / tentacle_equip / tool_bay / ux_doctrine / vision_loop / **vlx_flow（新增）** / welcome。台账 22 行。工具自带修法：`binding_hook.py sweep`（自愈补页）。
- 面5 boot-selfcheck：**红 1** — 闸/重启验收单：9 项还有 5 项没到位（①宿主机代码换代 ②目录路由提速 ③品牌位生效 ⑨三块上下文进进程 ⑤旧 specifier 可选）。**上轮的面5 其余 6 条红已全消**（恒真判据/上帝之眼/双向绑定/接线对账/凭据自审/装机副本漂移 全绿）。
- 全程只读，未改任何源码。红项留主人决定。
- 备注：G6 规则锁需每工具「从第1行起 ≥60 行」Read 后才放行；并行 Read 不计入账本（本次 binding_hook 首跑被拒，单独重读 100 行后通过）。

## 2026-10-11 09:42（GMT+7）第四次执行
- 五步全跑。**五个面均有红，共 11 条**（较 03:40 明显回退，主因是一条**新根因**）。
- 面1 覆盖矩阵 sweep：**bindings 覆盖 0.9897 · missing 30 ⇒ 矩阵非全绿**（顶层树 70/已扫60/排除10 · 单元 35824 · 盲区 0 · 耗时 381.3s）。读数刷新至 2026-10-11T09:49:16。
- 面2 framework_state：**红 2** —— ① 绑定断连 资产缺失 78 · 触手不在册 0；② 覆盖矩阵不是全绿。
- 面3 tentacle_bind scan：**红** —— 资产缺失 78（全在 `_upstream/`：openhuman 66 · Scrapling 6 · career-ops 5 · CLIProxyAPI 1）· 触手不在册 0。**新根因**：上游参考树文件集变动 ⇒ 旧自动绑定悬空。工具自带修法：`tentacle_bind.py prune`（大批量需 `GBT_BIND_ALLOW_SHRINK=1`）／`autobind`。
- 面4 binding_hook verify：**ok=false** —— 11 位缺「⑥记忆页」（与 03:40 同源）：delivery_gate / god_view / media_stamp / omni_plug / remote_confinement / tentacle_equip / tool_bay / ux_doctrine / vision_loop / vlx_flow / welcome。修法：`binding_hook.py sweep`。
- 面5 boot-selfcheck：**红 6** —— ① 接线全连通（资产缺失78）② 覆盖无死角且新鲜（矩阵非全绿）③ 新增能力双向绑定（0!=78 + 状态红）④ 未清故障前提复核（F18 前提已垮 + 需人读集合 0!=1）⑤ 没有亲跑不许交付（D9 框架门 rc=1 · D11 能力位双向绑定 rc=1）⑥ 闸/重启验收单（⑤ 旧 specifier 可选未清）。
- 面5 其余全绿：护栏三道 · 部署法制 · 编码守门棘轮 · 每一页都绑到触手 · 装机副本漂移逐字节一致 · 部署前接线对账 · 凭据自审 · 上帝之眼 等均过。
- 全程只读（含未跑 prune / sweep 等写操作），红项留主人决定。
- 备注：直接 `python -m unittest gbt_allinone.tests.*` 会被 store 守卫拒（须先设 `GBT_STORE_DIR`）；模拟器内无需 key。

## 2026-10-10 21:27（GMT+7）第二次执行
- 五步全跑。面1/面3 全绿；面2 红 1、面4 ok=false（10 位缺腿）、面5 红 7 条。
- 面1 覆盖矩阵 sweep：全绿，顶层树 70（扫60/排10），单元 34541，耗时 195.1s，盲区 0。读数刷新至 21:15:07。
- 面2 framework_state：红 1 — `welcome` 不在图鉴且未登记 unimplemented.json（registry=253·atlas=252·undispatched=[]）。绑定 7534 断连 0；技能源装 89/89；视觉面 ok。
- 面3 tentacle_bind scan：全绿（7534 · 缺失 0 · 不在册 0）。
- 面4 binding_hook verify：**ok=false** — 10 位缺腿：delivery_gate / god_view / media_stamp / omni_plug / remote_confinement / tentacle_equip / tool_bay / ux_doctrine / vision_loop 各缺「⑥记忆页」；`welcome` 缺「③图鉴 + ⑥记忆页」。
- 面5 boot-selfcheck：**红 7** —
  ① 没有恒真判据：`gbt_allinone/tests/test_deepseek_bridge.py:262` 规则 `A/or True`（布尔吸收·整条恒真）。
  ② 上帝之眼：`TestJevDecides` 3 条被「预算闸：一分钟内已决策 6 次（上限 6）」拒。**根因**：`gbt_allinone/tools/gods_eye.py:53 _STATE = _ROOT/"state"` —— 决策台账落全局 state/，**不被 GBT_STORE_DIR 隔离**，判据自身写入即污染预算闸（可复现）。
  ③ 新增能力双向绑定：3 条，全部指向 `welcome`。
  ④ 部署前接线对账：A_read_but_undeclared = IMAGE_API_KEY(modules.js:455) / IMAGE_MODEL(447) / LLM_MODEL(350) / SANDBOX(583,596) / UNCENSORED_MODEL(421)。
  ⑤ 凭据自审有牙且在仓里：`.scratch\_baseline_wt\gbt_allinone\tests\test_precommit_secret_scan.py` 仍指向 TEMP 副本。
  ⑥ 闸/装机副本漂移：[web] profile 的 gbt-potato-master-v8 与 -v9 **各 8 个文件内容不同**（tools/audit-avatar-baseline.py、check-panel-syntax.py、cross-scan.py、phase1-owner.py …）。修法：跑该闸 `--fix` 或重跑 profile 的 npm install。
  ⑦ 闸/重启验收单：9 项中 6 项未到位（①②③⑨ 因 127.0.0.1:3080 未起；⑦ 装机副本漂移；⑤ 旧 specifier 可选）。
- 新增 36 个能力位（217→253），`welcome` 是漏走六条腿钩子的那一个 —— 面2/面4/判据③ 三条红同源。
- 全程只读，未改任何源码。跑判据会在 `state/gods_eye_decisions.jsonl` 追加决策行（判据自身副作用，非改码）。红项均留主人决定。
