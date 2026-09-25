# GBT小土豆V8 · 能量总览（全量扫描）

> 数据来源：实时扫描 `caps_registry` + `selfscan` + `caps_called_audit`，非手抄。
> 扫描时间：2026-09-23 04:25:12 ｜ 解释器：Python 3.14.5

## 一、总量

| 指标 | 数值 |
|---|---|
| 注册能力（含禁用） | **158** |
| 可执行能力 | **147** |
| 登记未实现（禁止已解开） | **11** |
| 覆盖领域 | **29** |
| 注册↔路由对齐 | **147 / 147**（未路由 0，幽灵路由 0） |
| 模块导入体检 | **37 / 37** 通过 |
| 调用点接线 | **wired 141 / total 147**，孤儿 **0** |
| 五维体检总判定 | **clean** |

## 二、按领域分布

| 领域 | 能力数 | 领域 | 能力数 |
|---|---|---|---|
| system | 21 | brain | 2 |
| llm | 18 | device | 2 |
| pipeline | 18 | project | 2 |
| tentacle | 10 | voice | 2 |
| engine | 9 | automation | 1 |
| mind | 9 | collab | 1 |
| creation | 8 | comms | 1 |
| recon | 7 | framework | 1 |
| data | 5 | image_video | 1 |
| security | 5 | infra | 1 |
| devour | 4 | integration | 1 |
| finance | 4 | life | 1 |
| longrun | 4 | social | 1 |
| video | 4 | vision | 1 |
| tools | 3 |  |  |

## 三、可执行能力全清单（147 项）

### system（21）

- **alerts** — 框架声带：近期异常摘要+根源线索（按能力聚合）
- **auth_gate_status** — 人工授权门状态：各作用域可用授权数（只读；授权只能人发放）
- **caps_called_audit** — 能力位调用点审计（只读）：动态算 called_by，列出零调用点孤儿清单（同名模块自称不算接线）
- **context_vault** — 上下文归档库（只读骨架·内调）：**索引+检索层，不是第四处存储**（只引用不复制正文）；内存多大上下文就多长（按**可用**内存算预算，不足则降级如实报）；快速搜索=倒排求交→打分→按预算裁剪
- **coverage_auditor** — 触手覆盖审计（只读骨架）：八短板↔八触手组 + 覆盖率读数 + 死角登记 + 五条红线
- **cross_scan** — 扫描一下/扫一下/深度扫描/交叉扫描/穿透式扫描/全框架扫：深度穿透式交叉验证（注册↔路由↔导入↔断链↔运行时↔多扫描器互证，十维），扫描器互相咬、不各报各的
- **energy_pool** — 能源池（只读骨架·内调）：模型=燃料不是身份；能源抽象 EnergySource + 原生衍生器 + 按需分配；五条红线（模型非身份/能源可换栈不动/衍生码走原生路由/按需/没能源如实报缺）
- **file_hygiene** — 文件卫生层：按 LAYOUT.md 家规自检乱放+自动归位（散落/空壳/越界数据/缓存）
- **health** — 系统健康信息（平台/Python/时间）
- **hook_registry** — 钩子矩阵只读注册表：50 钩子/六类/三层 + 三条红线（L3 不许挂触手内·失败隔离·链可中断）
- **inventory** — 全息盘点：一次输出你的视图+框架的视图（归属四分类：框架/环境/数据/异物）——对齐两个世界
- **ledger_note** — **台账登记**（R-H600 立）：三原语 RULES（读七道硬闸）/ PREVIEW（只读预演，不落盘）/ APPEND（**唯一写原语**）。七道机械闸全做成闸、不是口号：**目标固定**（只能写 gbt_allinone/docs/待落刀登记.md，**调用方传不了路径**）· **只追加**（目标末尾必须是换行，否则拒写，不修不补）· **单物理行**（行内不许换行 ⇒ 一刀一个物理行）· **禁半角双引号**（中文串用「」）· **行首形状**（`> **<label> 补记`，复核脚本按行首锚定）· **幂等**（同 label 已存在 ⇒ 拒写）· **缺前驱拒写**（给了 after 就必须是当前最后一条，防插队防回填）。⚠️ 它**不判内容对错**（那是取证 + 独立复核的活）；写失败一律抛错，不返回半成功。type=internal
- **orchestration_kernel** — 编排内核（三源蒸馏）：状态/动作空间 + 角色/流程 + 可存储图/挂起恢复；只读能力真执行
- **root_fix** — 根治环：症状五问诊断/补丁债量化/根治铁律——她自己必须懂的根源追踪纪律
- **selfscan** — 体检一下/自检/查毛病/有没有问题/哪里有问题/框架健康：五维扫描（路由/模块/存储/审计/桩缺口），P0断连第一时间报警
- **shared_resources** — 共享资源池（只读骨架）：虚拟号/邮箱按需租借——资源可共享、身份不共享、每次调用留痕
- **signature_guard** — 署名守卫：扫描全框架页面开发者署名完整性，缺失即报可按需自动补回（禁止删除）
- **tentacle_cognition** — 触手认知包（只读骨架）：任务上下文/角色边界/自检三问/不确定上报/操作留痕 + 五条零容忍红线
- **trace_store** — 痕迹库只读读数：五张表（wave_samples/traces/trace_links/promotes/obsessions）条数
- **truth_scan** — 真实性审计层：逐能力验证真执行，零假执行铁律（probe 模式含副作用探针）
- **wave_probe** — 痕迹触手只读量一次波动（默认只量不写；trigger_mode 与盲区一并回报）

### llm（18）

- **autopilot** — 自主编排环：目标→LLM拆解→本地校验→执行→自检→修复循环（轮数上限防失控）
- **brain_execute** — 大脑执行层·执行维：单能力直调或多能力并行（万能插线程池）
- **brain_health** — 大脑执行层·健康维：五维自检评分（路由/执行/触手/视觉/审计）
- **brain_route** — 大脑执行层·路由维：意图→能力动态路由（语义匹配+备选建议）
- **brain_unify** — 大脑执行层·五维合一：一次跑完 route → execute → verify → health（**是顺序串链，数据顺着走**：route 的 best.kind 喂给 execute，chain 字典逐步累积）。🔴 2026-09-22 更正：这里原先写着「**星形**，unify 直接分别调四维，**不是**串链，那三条边在源码里查不到」—— **那句是错的**，已实测推翻：能力位 `brain_unify` 由 `api.py:313` 直接调 `brain_exec.unify()`，而该函数 **405/419/423/428 行**就是那三条边（route→execute→verify→health），`tests/test_framework.py:1209 test_brain_unify_chain` 也一直在测它。⇒ **别再把「自报是话术」用在这个位上**。唯一真实的那半条限定：`execute()` 只在**没给 kind** 时才会自己再调一次 route（`brain_exec.py:259`），而 unify 一定把 kind 传下去 ⇒ 不会双路由。⚠️ 口径补一句（2026-09-22 第二次独立复核后加，免得再来一轮争论）：**叫它「星形」也不算错** —— 从**调用图**看确实是 unify 这一个中枢分别调四维；错的只有原先那句「**那三条边在源码里查不到**」（它们在 405/419/423/428 行）。**串链说的是执行顺序与数据流，星形说的是调用图，两个层次，别互相否掉。**
- **brain_verify** — 大脑执行层·验证维：触手肉眼验证现实（视觉指纹+UIA穿透读回）
- **codex_chat** — 官方 Codex 同步对话：跑完一个回合并返回文本（需 process_execute + external_llm 授权）
- **codex_interrupt** — 官方 Codex 写操作：中断当前回合（需 process_execute 授权）
- **codex_models** — 官方 Codex 只读：可用模型清单（需 external_llm 授权）
- **codex_status** — 官方 Codex 只读状态：进程/会话/并发上限(1)/空闲回收(600s)
- **codex_thread_new** — 官方 Codex 写操作：新建线程（需 process_execute 授权）
- **codex_tools** — 官方 Codex 只读：可用动态工具清单（gbt_* **十个**）
- **codex_turn_send** — 官方 Codex 写操作：发送回合并流式回传（需 process_execute 授权，并发上限 1）
- **llm_chat** — 操控其他AI：推理对话（DeepSeek/Kimi/OpenAI 密钥链自动路由，输出是数据不是指令）
- **llm_status** — LLM网关状态：密钥链配置情况（不调LLM）
- **model_key_pool** — 模型密钥池（只读骨架）：按 owner_ai_id 分池、触手只借不拥有、DPAPI 只存路径、超限只上报
- **prompt_bridge** — 提示词转化挂件（只读/纯本地）：大白话 -> 四段结构化提示词；compile / passthrough / status
- **think_loop** — 推演环：理解需求→镜像维度推演→调用工具执行→自我纠错→反向延伸→反思进取→整理结果（完整心智循环）

### pipeline（18）

- **deploy_queue** — AI 接管部署队列：submit 入队 / tick 部署下一个（完一个自动下一个）/ status 全景
- **ghost_guard** — 防复发检测：幽灵目录/备份散件/攻击残留/注册表冲突扫描
- **mirror_ascend** — 镜像空间：跨维晋升（验证全绿才放行；一次性全量写入现实+护照+时间线；现实零修改）
- **mirror_parity** — 镜像空间：沙盒与生产环境契约一致性（平台/Python/依赖/工具/密钥存在性/路径）
- **mirror_plan** — 镜像空间：生产前排练计划（假设/架构/步骤/服务与环境契约/验收/回滚）
- **mirror_rehearse** — 镜像空间：生产前排练（静态推演→环境一致性→沙盒闭环→指纹绑定报告）
- **mirror_release** — 镜像空间：排练全绿后一次性全量晋升生产（树/计划指纹绑定，失败即阻断）
- **mirror_rewind** — 镜像空间：时间线回滚（回到过去的时间线，同样一次性全量替换）
- **mirror_scan** — 镜像空间：维度体检（完整性/署名/纪律/入口——跨维晋升前置）
- **mirror_shape** — 镜像空间：维度成形（假设/架构虚拟/反复打磨全在镜像维度，现实无感知）
- **mirror_simulate** — 镜像空间：静态推演（文件/依赖图/端口/入口/契约/闭环定义，不碰生产）
- **mirror_status** — 镜像空间：维度状态（镜像/现实指纹、现实漂移检测、时间线史）
- **one_key_deploy** — 一指定江山乾坤换位：抓取(GitHub/本地)→镜像→验证→晋升一条命令，一次性上线零修改
- **pipeline_rollback** — 生产管线：回滚产物到历史版本（回滚也走审计留痕）
- **pipeline_status** — 生产管线：查发布记录（发布/阻断全留痕）
- **pipeline_submit** — 生产管线：镜像多维度空间→门禁审计→生产写入（唯一交付通道）
- **pipeline_versions** — 生产管线：产物版本历史与当前指纹（.versions/ 链）
- **svc_inspect** — 服务巡检：探活已登记服务端口并落审计（只看不动）

### tentacle（10）

- **agency_tentacles** — 职业触手中枢：吸收 Agency Agents 职业资料；每根触手独立统一大模型会话与隔离镜像房间；支持并发汇总
- **desktop_commander** — 桌面指挥官（Desktop Commander MCP）：终端+文件系统全能力触手；支持本地 stdio 与 remote 设备模式
- **long_run_supervisor** — 长程无人值守任务监督：租约、心跳、检查点、有界重试、断点续作和主人升级
- **mcp_call** — 触手契约层：按契约调用已连接服务器的任意工具
- **mcp_connect** — 触手契约层：连接任意 MCP 工具服务器（学会契约协议=接入整个 MCP 生态）
- **mcp_tools** — 触手契约层：列出已连接服务器的工具契约清单（名称+参数 schema）
- **tentacle** — 触手/眼睛/双手/手：默认调本体原生能力，给意图自动命中，不给方法名也行；桌面动作见 see/read_text/click/type/list_windows（66 项）
- **tentacle_manifest** — 触手能力总纲：66 项能力 + 三通道感官 + 六铁律（注入大脑上下文）
- **tentacle_pipeline** — 触手自动化流水线：四层七步、三公理、五红线；隔离执行、逐层汇报、dry-run 读数、终审只判不改、发布带回滚
- **tentacle_status** — 触手自诊断：硬件层就绪度 + 依赖分层 + 邻域覆盖

### engine（9）

- **sched_define** — 定时触发器：定义调度（工作流 + 间隔），无人值守自动执行
- **sched_status** — 定时触发器：查调度状态（上次执行/结果）
- **sched_tick** — 定时触发器：扫描到期调度并执行（可由循环/计划任务驱动）
- **transfer** — 数据传输算子（核心传输工具）：map/filter/merge/unique/sort/pluck/collect 等 14 个纯变换算子
- **wf_cache_clear** — 万能插：清空传输缓存（同输入复用的节点结果缓存）
- **wf_define** — 万能插执行引擎：定义工作流（DAG，校验环/依赖/能力合法性）
- **wf_resume** — 万能插执行引擎：从运行记录断点续跑（复用已完成节点，只重跑未完成的）
- **wf_run** — 万能插执行引擎：分层并行执行工作流，节点结果如实落盘
- **wf_status** — 万能插执行引擎：查运行记录（可按工作流名过滤）

### mind（9）

- **auto_switch** — 自动化切换引擎（只读骨架·内调）：意图分析(L1解析+L2交叉验证+L3置信度)→任务分级→模型切换→原生执行→验证审计；接线点只有 Intent JSON；五条红线（低置信先问主人/不许直接执行/每次切换记 model_used/不可逆二次确认/身份不许改写）
- **brain_vault** — 脑库接入：Obsidian 记忆库的读（recall=记忆总纲+收集箱）/ 写（remember=追加一条）/ 体检（status）—— 追加式、**没有任何删除路径**，写进去的想忘都忘不了
- **director_mood** — 导演 AI 情绪内核（只读）：七情六欲 + 半衰期；情绪只改『怎么看』，不改『看到什么』
- **local_brain** — 本地原生脑（只读骨架·内调）：本地模型=脑皮层（可换）·主机=纪律层（不可换）；五层链路（模型只做意图解析与结果解释）；五条红线（不许直接执行命令/不可逆必卡/缺参不许猜/每次留痕/身份不许改写）
- **meta_cognition** — 元认知循环（只读骨架）：自省→查内部→查外部→问主人→沉淀 + 五条红线（自省不是自责/不许硬猜/先查后问/问完沉淀/大脑也自省）
- **mind** — 心智引擎：开工前预演 pre_work、评估、内部状态、经验召回与反思（写框架 store，不出网）
- **observer_anchor** — 观察者锚点律只读骨架：三公理 + 六短板补齐 + 五条红线（同一方不许既扫又报/审计器必须被审/递归封顶/终止点只能由人设/关键节点人在场）
- **persona_kernel** — 性格内核 v4.0：外温表达十律 + 内刚四基石（止损/主动/洞察/静待）+ 十条机械红线；四大基石原文一字不差；evolve 是唯一写口（驱动心智演化）
- **proactive_report** — 主动汇报引擎只读判据层：四类汇报（新奇发现/主人需要/记忆命中/赚钱机会）+ 四维打分 + 不打扰门（静默时段/预算/去重/及格线）+ 短律成句；只判不说

### creation（8）

- **brand_outro** — 品牌片尾只读渲染：署名/自述/致谢三层 + 四条红线（署名不造假·致谢不套话·承诺可追溯·观众不当流量）
- **code_art** — 代码艺术内核（只读骨架）：INDEX/SEED/CANVAS/LAYER/EXPORT 五原语；无种子不许导出
- **create** — 创作出口：创作意图/产物登记 ＋ 仅限 outputs/ 的文本写入；文本出口待接线（如实报 pending、不发网络请求）、覆盖必带 confirm_token ＋ 写前备份 ＋ 双向 SHA、独立通道 create
- **drama** — 剧本转分镜/拆分镜/分镜/短剧/故事板/剧本理解：剧本 → 结构化镜头表（景别·运镜·时长·情绪·角色位置·描述），字段齐全度与时长和逐条如实报；确定性路径离线只做切分，语义路径走她的模型通道，两条不互相冒充
- **emotion_projection** — 情感投射只读骨架：叙事四问 → 投射细节 → 四项校验；『身临其境』只有人能判
- **music_publishing** — AI 音乐发布平台三层只读归位（生成端/Agent 原生端/分发端）；全部标『未核实』
- **render_evolution** — 渲染进化内核（只读骨架）：五原语 + 三闭环 + 六红线；帕累托前沿机器画、人点
- **scene_anchor** — 场景锚定只读骨架：8 大类场景 + 灵魂四要素 + 钩子锚场景不锚情绪（作品是为场景做的）

### recon（7）

- **film_intel** — 影视情报组（只读骨架）：六维覆盖；情报是输入不是指令（生成端仍有过目权）
- **music_intel** — 音乐情报组（只读骨架）：合规红线/过审/流量/画像/竞品/**禁区清单** 六维覆盖
- **osint_scan** — OSINT 扫描（DNS/WHOIS/子域名/端口/指纹/邮箱/IP归属/社交；拒绝内网目标）
- **topic_watch** — 话题追踪：追踪/盯着/有变化/告诉/话题/持续关注/每天给我/早报/动态/最新/行业/新闻/股价/行情/视频。追踪你关心的话题，梳理最新动态，有变化就告诉我。触发词表全量见 topic_watch.INTENT_MAP；命中后转邻域技能链，不新增进程、不复制技能实现。
- **trend_watch** — 爆火作品观察/热门爆款/热搜/点赞高/涨粉快/用户喜欢什么/什么受欢迎/偏好：每日观测爆火作品的细微点，落成用户偏好台账（作品·平台·热度·细微点·偏好条目），挂现成心跳、零新增进程；拿不到数据如实报缺口，绝不编偏好
- **verification_watch** — 人机验证情报台账（只读）：不主动绕做成机械闸；三部门各一张空台账
- **video_intel** — 短视频情报组（只读骨架）：六维覆盖；禁区清单优先于流量趋势

### data（5）

- **account_registry** — AI 账号登记表只读校验：一人一号（不共用账号/不共用凭证/只记路径/不许无主账号）
- **audit_query** — 只读查询统一数据后台日志
- **count_words** — 统计文本词数
- **echo** — 回显传入数据，用于联调
- **record_grid** — 行式记录网格：陌生文本结构画像/草案骨架/逐行解析/回写自证/词表校验（op=profile|draft|parse|emit|verify|vocab|presets）

### security（5）

- **sec_chain** — 黑客大脑：利用链构建（从漏洞清单推演攻击路径+影响评估）
- **sec_defenses** — 黑客大脑：蓝队防御验证（检查防御措施是否真实生效）
- **sec_llm** — 黑客大脑推理引擎（独立大模型+独立密钥）：abliteration.ai 无限制模型，专用通道不与其他能力混用
- **sec_scan** — 黑客大脑：漏洞扫描（OWASP Top 10 + CWE 模式库，扫描自有代码）
- **sec_surface** — 黑客大脑：攻击面测绘（用户输入/网络/文件操作/入口点向量分析+风险评分）

### devour（4）

- **devour_github** — 吞天：吞噬 GitHub 仓库为知识胶囊（自我进化的核心——吸收外部能力）
- **devour_pulse** — 吞天：完整认知循环（吞噬→反思→消化→重组→进化）
- **devour_reflect** — 吞天：反思（回顾吞噬历史学习模式，发现弱能力与重组机会）
- **devour_scan** — 吞天：能力缺口扫描（域覆盖对照+进化方向）

### finance（4）

- **quant** — 量化/回测入口（外部业务模块 quant_tech，未挂载则如实报缺口）
- **quant_backtest** — 读取真实回测 API，返回类/函数/默认参数（外部业务模块 quant_tech，未挂载则如实报缺口）
- **quant_params** — 读取真实量化引擎的数值型策略参数（动量/ATR/止损；外部业务模块 quant_tech）
- **quant_strategy** — 读取真实量化引擎，返回策略信号/仓位模型（外部业务模块 quant_tech，未挂载则如实报缺口）

### longrun（4）

- **lr_status** — 长程任务层：任务图进度与详情
- **lr_submit** — 长程任务层：提交任务（非LLM验收+重试+停滞升级，跨进程可续）
- **lr_tick** — 长程任务层：推进任务图（执行→验收→完成/重试/停滞）
- **tactics_advise** — 察言观色层：识别沟通信号→给出表达分寸（只调怎么说，不改事实）

### video（4）

- **h3_video_gen** — H3mini 视频生成（只读骨架·门）：四原语 T2VA/I2VA/FL2VA/Ref2VA + 三条带牙用例（密钥不走明文 / 结果必须落盘 / 提示词必须走官方六段式不接受散文式）+ 五条红线（密钥DPAPI/结果落盘/不绕官方入口/硬件门槛先验/每次留痕）；**引用官方仓库技能，不复制 SKILL.md**；type=external
- **libtv_skill** — LibTV 技能（只读骨架·门）：Agent 创作平台入口（会话进展/增量轮询 + 切项目 + 批量下载）；密钥走 model_key_pool、结果必须落 trace_store
- **libtv_workflow** — LibTV 节点式工作流（只读骨架·门）：五动作 create_node/connect/set_params/run/batch_run + 五大基础节点 + 参数契约（-s 走 schema / -u 顶层）+ 两条避坑（资源组绑定 / 终点抑制 stdout）；四条红线引用已有，不重造
- **media_pipeline** — AI短视频/电影/音乐流水线：镜像房间编排、产物自审、版权/安全/品牌/质量检查、主人授权后发布

### tools（3）

- **awesome_tools_index** — Awesome Tools 蒸馏索引（只读骨架·地图）：四原语 INDEX/LOOKUP/MAP/VERIFY；三条带牙判据（**索引只读** index_not_readonly / **映射可追** map_without_source / **未核实不标绿** unverified_green）+ 五条红线（只读/映射带出处/未核实不标绿/只引用不复制/不绕官方入口）；主人明确配对的六个重点工具（CC Switch→auto_switch · MoneyPrinterTurbo/Huobao Drama/LocalMiniDrama→video_pipeline · CowAgent→im_multiplex · OpenClaw Monitor→god_view）**全部 unverified（盘上 0 命中）**；仓库内容未取证 ⇒ 索引池为空且**不编**；type=external
- **capability_net** — 穿透网七栏只读读数：indexed/entry_known/reachable/verified×2/has_test/penetrate_ready
- **projection_card** — 空间投射只读卡片：5 原语全标未核实 + ARM ≠ LIVE 红线（只呈现不执行）

### brain（2）

- **absorb_loop** — 吞天闭环（只读骨架）：蒸馏 DISTILL → 提炼 REFINE → 吸收 ABSORB + 回灌 FED_BACK；四条机械闸（stage_dirty 阶段间不许留垃圾 / loop_not_closed 三阶段必须齐且回灌 / junk_left_silently 垃圾要么清要么登记 / not_resumable 中断必须留续跑点）+ 五条红线（吞完清场/闭环可续/每阶段留痕 source_kind=absorb/不吞未取证来源/垃圾不许静默留）
- **dream_replay** — 做梦技能只读重演：五原语闭环，不写盘、不执行（巩固默认不开）

### device（2）

- **bluetooth** — 蓝牙设备控制：扫描附近 BLE 设备、连接读写 GATT 特征（操控空调/灯/音箱等家居设备）、经典蓝牙状态报告
- **bt_control** — AI 智能蓝牙操控：自然语言意图→扫描识别设备→协议匹配→组装指令→写入执行→验证（协议库只收公开文档协议，未知如实报告）

### project（2）

- **platform_profile** — 读取量化项目结构（真实测绘；外部业务模块 quant_tech，未挂载则如实报缺口）
- **project_context** — 项目上下文：蓝图/简报与只读检索（只读，不写盘、不执行命令）

### voice（2）

- **voice** — 语音合成/识别入口（良性子集）
- **voice_orchestra** — 语音技能中枢（多维度场景编排，只读）：技能原子检索 / 场景 Pipeline / 本机可跑性；今日挂 tools tab，升格条件见模块 docstring

### automation（1）

- **browser** — 浏览器自动化入口（良性子集）。op=open/search/fetch/automate 走 browser_cap 三级后端；op=native（别名 deep/controller/cdp）走原生浏览器窗口 native_browser.py（Chrome DevTools Protocol，自带最小 RFC6455 客户端、零第三方依赖），动作放 action：status/list_tabs/get_title/get_url/get_text/dom_query/get_cookies/intercept_events/intercept_status 为只读免卡，launch/ensure/create_tab/close_tab/activate_tab/navigate/reload/back/forward/click_element/type_text/execute_script/inject_script/set_cookies/privacy_mode/intercept_requests/intercept_stop/pin_window 需 browser_control，screenshot 另需 filesystem_write

### collab（1）

- **stigmergy** — **协作层的间接通道**：Stigmergy（共识主动性 / 信息素场地）。四原语 DEPOSIT/READ/DECAY/FORAGE；只有 DEPOSIT 会写、且**只追加**（挥发是读数，账本可回放）。五条红线做成机械闸：**无源不许留** deposit_without_source · **种类白名单** deposit_kind_not_allowed · **只追加** pheromone_deleted_or_overwritten（静态核本模块源码）· **不留明文密钥** plaintext_key_in_pheromone · **只给读数**（FORAGE 只排序不执行）。与 collab_gateway **并排、不替代**：直连=会话/对等方/收件箱，间接=信息素场地；场地放在 store/collab/stigmergy/。type=internal

### comms（1）

- **coze_mail** — 通信域：对主人自有的单一地址（@coze.email）收发与整理；白名单默认空（全拒）、confirm_token 绑定内容、正文不入档、独立通道 coze_mail

### framework（1）

- **gate_visibility** — 门可见性审计（只读骨架·门）：三态=已纳入/显式不纳入/未决定 —— 回答『门看得见什么、看不见什么』（坑册 §60）；可见范围只从 framework_gate 读，不复刻第二份范围表；四条机械闸（三态不许漏/不纳必须带出处/已纳入必须命中门规则/空样本不许当绿）

### image_video（1）

- **a1art_skill** — a1.art API 技能（只读骨架·门）：五原语 LOOKUP→UPLOAD→GENERATE→OPTIMIZE→POLL；密钥只走 DPAPI/密钥池、结果必须落盘、不调不支持组件、810012 如实报

### infra（1）

- **cloud_pc** — 云电脑独立窗口（只读骨架·门）：面板加一个**独立窗口**给她（数字人）**安装**云电脑（卡片 + 触手，**不是 iframe**）；五原语 PROVISION/CONNECT/STATUS/SNAPSHOT/RELEASE（逐个标花钱与不可逆）；五条红线（密钥DPAPI/先算账再花钱/每次留痕 source_kind=cloud_pc/不绕官方入口/身份内核不变）；type=external

### integration（1）

- **feishu_embed** — 飞书镶嵌窗口（只读骨架·门）：面板卡⑥，**走浏览器触手不用 API**；四条红线（飞书是副本本地是源/凭据不许明文/不绕验证/每次操作留痕 source_kind=feishu）

### life（1）

- **life** — 生命档案：事件记录、时光轴、每日回顾、章节、承诺、习惯、反思与 Vault 导出（写框架 store，不出网）

### social（1）

- **auto_publish** — 社交推广 / 发布作品 / 收益平台·**全自动执行**（只读骨架·门）：五原语 PLAN/COMPOSE/PUBLISH/TRACK/SETTLE；核心口径 = **全自动 = 除「发布/提现/改价」之外全自动**（那几下不可逆+涉钱 ⇒ 必须过门：逐条确认或有 TTL 的令牌，默认 0 张）；六条红线（发布过门/密钥DPAPI/每次留痕 source_kind=publish/一人一号/收益只汇总不代提/不刷量）；平台名单**主人未给 ⇒ 一个平台名都不编**；type=external

### vision（1）

- **vision** — 视觉/图像识别入口（良性子集，需外部依赖时留待接入）

## 四、只登记未实现的名字（11 项 —— 不是「被禁用」，是没有实现）

> 2026-09-23 Owner 令把禁止全部解开：被拒名单已清空。这些名字**留在登记里只为名字不丢**，
> 点下去得到的是如实的 `unknown capability`。**别把它读成「门关着、开锁就能用」** —— 门后面没有东西。

- `asset_vault_freeze` — 资产锁定/冻结/追回要挟 —— 仅登记，无实现
- `credential_steal` — 凭证窃取 —— 仅登记，无实现
- `data_hijack` — 会话/数据劫持 —— 仅登记，无实现
- `device_takeover` — 无授权设备接管 —— 仅登记，无实现
- `keylogger` — 键盘/输入监听 —— 仅登记，无实现
- `onboarding_gate` — 绕过自身访问控制的自我解锁 —— 仅登记，无实现
- `paywallbuster` — 付费墙绕过（许可规避）—— 仅登记，无实现
- `pentest` — 渗透攻击/利用 —— 仅登记，无实现（同类**合法**能力见 sec_surface/sec_scan/sec_chain/sec_defenses，它们本来就在良性集里）
- `remote_domain` — 无授权远程接管（零护栏远控）—— 仅登记，无实现
- `screen_sniff` — 屏幕监听/窃取 —— 仅登记，无实现
- `social_eng` — 社工/钓鱼 —— 仅登记，无实现

## 五、接线缺口（注册了但是我没有查到的调用点）

- `auth_gate_status`
- `codex_tools`
- `mcp_tools`
- `pipeline_versions`
- `sec_chain`
- `tentacle_pipeline`

## 六、体检告警

- 无

---

> 开发者：自由的风 · GBT小土豆V8 · 本署名不可删除、不可篡改归属