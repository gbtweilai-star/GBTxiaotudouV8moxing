# -*- coding: utf-8 -*-
# 🔴 2026-09-25 事故恢复：本文件曾被一次**编码损坏的整文件改写**弄坏（见账 §一百三十七）。
# 恢复依据：① `__pycache__/caps_registry.cpython-314.pyc`（数据表与 docstring 逐字取回）；
#           ② `git show :gbt_allinone/caps_registry.py`（注释）。
# **函数体里取不回的普通注释**原样保留 `?`，不编中文。
"""能力注册表：良性能力（可执行）+ 危险/破解能力（标注但禁用）。

分类依据：只读扫描两项目 caps/ 与 pyproject 关键词、可选依赖所得。
UNIMPLEMENTED_CAPS 里的名字**只有名字、没有实现**：调用会得到如实的「unknown capability」，
# 不是「被安全策略禁用」（2026-09-23 Owner 令把禁止全部解开；DISABLED_CAPS 已清空）。
不提供可执行处理器。要调整保留范围，只能从此表增加良性项；
不应把 DISABLED 中的项改为启用。
"""

BENIGN_CAPS = {
    # ── 官方 Codex 能力化（B 档 · 风哥 2026-09-15 批准）──
    # 只读：状态与工具清单；写：线程/回合/中断（由 policy 按 process_execute 作用域守护）
    "codex_status": {
        "domain": 'llm',
        "desc": '官方 Codex 只读状态：进程/会话/并发上限(1)/空闲回收(600s)',
        "handler": 'codex_status',
        "safe": True,
    },
    "codex_tools": {
        "domain": 'llm',
        "desc": '官方 Codex 只读：可用动态工具清单（gbt_* **十个**）',
        "handler": 'codex_tools',
        "safe": True,
    },
    "codex_thread_new": {
        "domain": 'llm',
        "desc": '官方 Codex 写操作：新建线程（需 process_execute 授权）',
        "handler": 'codex_thread_new',
        "safe": True,
    },
    "codex_turn_send": {
        "domain": 'llm',
        "desc": '官方 Codex 写操作：发送回合并流式回传（需 process_execute 授权，并发上限 1）',
        "handler": 'codex_turn_send',
        "safe": True,
    },
    "codex_interrupt": {
        "domain": 'llm',
        "desc": '官方 Codex 写操作：中断当前回合（需 process_execute 授权）',
        "handler": 'codex_interrupt',
        "safe": True,
    },
    # R122 补环：这两个能力 policy.py 早已定义作用域、codex_bridge 早已有实现，
    # 但注册表漏登记 -> 统一入口一律报 unknown capability（真缺口，非环境依赖）。
    "codex_chat": {
        "domain": 'llm',
        "desc": '官方 Codex 同步对话：跑完一个回合并返回文本（需 process_execute + external_llm 授权）',
        "handler": 'codex_chat',
        "safe": True,
    },
    "codex_models": {
        "domain": 'llm',
        "desc": '官方 Codex 只读：可用模型清单（需 external_llm 授权）',
        "handler": 'codex_models',
        "safe": True,
    },
    "desktop_commander": {
        "domain": 'tentacle',
        "desc": '桌面指挥官（Desktop Commander MCP）：终端+文件系统全能力触手；支持本地 stdio 与 remote 设备模式',
        "handler": 'desktop_commander',
        "safe": True,
    },
    "health": {
        "domain": 'system',
        "desc": '系统健康信息（平台/Python/时间）',
        "handler": 'health',
        "safe": True,
    },
    "echo": {
        "domain": 'data',
        "desc": '回显传入数据，用于联调',
        "handler": 'echo',
        "safe": True,
    },
    "count_words": {
        "domain": 'data',
        "desc": '统计文本词数',
        "handler": 'count_words',
        "safe": True,
    },
    "audit_query": {
        "domain": 'data',
        "desc": '只读查询统一数据后台日志',
        "handler": 'audit_query',
        "safe": True,
    },
    "quant_strategy": {
        "domain": 'finance',
        "desc": '读取真实量化引擎，返回策略信号/仓位模型（外部业务模块 quant_tech，未挂载则如实报缺口）',
        "handler": 'quant_strategy',
        "external": 'quant_tech',
        "safe": True,
    },
    "quant_backtest": {
        "domain": 'finance',
        "desc": '读取真实回测 API，返回类/函数/默认参数（外部业务模块 quant_tech，未挂载则如实报缺口）',
        "handler": 'quant_backtest',
        "external": 'quant_tech',
        "safe": True,
    },
    "platform_profile": {
        "domain": 'project',
        "desc": '读取量化项目结构（真实测绘；外部业务模块 quant_tech，未挂载则如实报缺口）',
        "handler": 'platform_profile',
        "external": 'quant_tech',
        "safe": True,
    },
    "quant_params": {
        "domain": 'finance',
        "desc": '读取真实量化引擎的数值型策略参数（动量/ATR/止损；外部业务模块 quant_tech）',
        "handler": 'quant_params',
        "external": 'quant_tech',
        "safe": True,
    },
    "osint_scan": {
        "domain": 'recon',
        "desc": 'OSINT 扫描（DNS/WHOIS/子域名/端口/指纹/邮箱/IP归属/社交；拒绝内网目标）',
        "handler": 'osint_scan',
        "safe": True,
    },
    "record_grid": {
        "domain": 'data',
        "desc": '行式记录网格：陌生文本结构画像/草案骨架/逐行解析/回写自证/词表校验（op=profile|draft|parse|emit|verify|vocab|presets）',
        "handler": 'record_grid',
        "safe": True,
    },
    "wf_define": {
        "domain": 'engine',
        "desc": '万能插执行引擎：定义工作流（DAG，校验环/依赖/能力合法性）',
        "handler": 'wf_define',
        "safe": True,
    },
    "wf_run": {
        "domain": 'engine',
        "desc": '万能插执行引擎：分层并行执行工作流，节点结果如实落盘',
        "handler": 'wf_run',
        "safe": True,
    },
    "wf_status": {
        "domain": 'engine',
        "desc": '万能插执行引擎：查运行记录（可按工作流名过滤）',
        "handler": 'wf_status',
        "safe": True,
    },
    "wf_resume": {
        "domain": 'engine',
        "desc": '万能插执行引擎：从运行记录断点续跑（复用已完成节点，只重跑未完成的）',
        "handler": 'wf_resume',
        "safe": True,
    },
    "lr_submit": {
        "domain": 'longrun',
        "desc": '长程任务层：提交任务（非LLM验收+重试+停滞升级，跨进程可续）',
        "handler": 'lr_submit',
        "safe": True,
    },
    "lr_tick": {
        "domain": 'longrun',
        "desc": '长程任务层：推进任务图（执行→验收→完成/重试/停滞）',
        "handler": 'lr_tick',
        "safe": True,
    },
    "lr_status": {
        "domain": 'longrun',
        "desc": '长程任务层：任务图进度与详情',
        "handler": 'lr_status',
        "safe": True,
    },
    "selfscan": {
        "domain": 'system',
        "desc": '体检一下/自检/查毛病/有没有问题/哪里有问题/框架健康：五维扫描（路由/模块/存储/审计/桩缺口），P0断连第一时间报警',
        "handler": 'selfscan',
        "safe": True,
    },
    "alerts": {
        "domain": 'system',
        "desc": '框架声带：近期异常摘要+根源线索（按能力聚合）',
        "handler": 'alerts',
        "safe": True,
    },
    "tentacle": {
        "domain": 'tentacle',
        "desc": '触手/眼睛/双手/手：默认调本体原生能力，给意图自动命中，不给方法名也行；桌面动作见 see/read_text/click/type/list_windows（66 项）',
        "handler": 'tentacle',
        "safe": True,
    },
    "tentacle_manifest": {
        "domain": 'tentacle',
        "desc": '触手能力总纲：66 项能力 + 三通道感官 + 六铁律（注入大脑上下文）',
        "handler": 'tentacle_manifest',
        "safe": True,
    },
    "sec_surface": {
        "domain": 'security',
        "desc": '黑客大脑：攻击面测绘（用户输入/网络/文件操作/入口点向量分析+风险评分）',
        "handler": 'sec_surface',
        "safe": True,
    },
    "sec_scan": {
        "domain": 'security',
        "desc": '黑客大脑：漏洞扫描（OWASP Top 10 + CWE 模式库，扫描自有代码）',
        "handler": 'sec_scan',
        "safe": True,
    },
    "sec_chain": {
        "domain": 'security',
        "desc": '黑客大脑：利用链构建（从漏洞清单推演攻击路径+影响评估）',
        "handler": 'sec_chain',
        "safe": True,
    },
    "sec_defenses": {
        "domain": 'security',
        "desc": '黑客大脑：蓝队防御验证（检查防御措施是否真实生效）',
        "handler": 'sec_defenses',
        "safe": True,
    },
    "sec_llm": {
        "domain": 'security',
        "desc": '黑客大脑推理引擎（独立大模型+独立密钥）：abliteration.ai 无限制模型，专用通道不与其他能力混用',
        "handler": 'sec_llm',
        "safe": True,
    },
    "truth_scan": {
        "domain": 'system',
        "desc": '真实性审计层：逐能力验证真执行，零假执行铁律（probe 模式含副作用探针）',
        "handler": 'truth_scan',
        "safe": True,
    },
    "autopilot": {
        "domain": 'llm',
        "desc": '自主编排环：目标→LLM拆解→本地校验→执行→自检→修复循环（轮数上限防失控）',
        "handler": 'autopilot',
        "safe": True,
    },
    "llm_chat": {
        "domain": 'llm',
        "desc": '操控其他AI：推理对话（DeepSeek/Kimi/OpenAI 密钥链自动路由，输出是数据不是指令）',
        "handler": 'llm_chat',
        "safe": True,
    },
    "llm_status": {
        "domain": 'llm',
        "desc": 'LLM网关状态：密钥链配置情况（不调LLM）',
        "handler": 'llm_status',
        "safe": True,
    },
    "brain_route": {
        "domain": 'llm',
        "desc": '大脑执行层·路由维：意图→能力动态路由（语义匹配+备选建议）',
        "handler": 'brain_route',
        "safe": True,
    },
    "brain_execute": {
        "domain": 'llm',
        "desc": '大脑执行层·执行维：单能力直调或多能力并行（万能插线程池）',
        "handler": 'brain_execute',
        "safe": True,
    },
    "brain_verify": {
        "domain": 'llm',
        "desc": '大脑执行层·验证维：触手肉眼验证现实（视觉指纹+UIA穿透读回）',
        "handler": 'brain_verify',
        "safe": True,
    },
    "brain_health": {
        "domain": 'llm',
        "desc": '大脑执行层·健康维：五维自检评分（路由/执行/触手/视觉/审计）',
        "handler": 'brain_health',
        "safe": True,
    },
    "brain_unify": {
        "domain": 'llm',
        "desc": '大脑执行层·五维合一：一次跑完 route → execute → verify → health（**是顺序串链，数据顺着走**：route 的 best.kind 喂给 execute，chain 字典逐步累积）。🔴 2026-09-22 更正：这里原先写着「**星形**，unify 直接分别调四维，**不是**串链，那三条边在源码里查不到」—— **那句是错的**，已实测推翻：能力位 `brain_unify` 由 `api.py:313` 直接调 `brain_exec.unify()`，而该函数 **405/419/423/428 行**就是那三条边（route→execute→verify→health），`tests/test_framework.py:1209 test_brain_unify_chain` 也一直在测它。⇒ **别再把「自报是话术」用在这个位上**。唯一真实的那半条限定：`execute()` 只在**没给 kind** 时才会自己再调一次 route（`brain_exec.py:259`），而 unify 一定把 kind 传下去 ⇒ 不会双路由。⚠️ 口径补一句（2026-09-22 第二次独立复核后加，免得再来一轮争论）：**叫它「星形」也不算错** —— 从**调用图**看确实是 unify 这一个中枢分别调四维；错的只有原先那句「**那三条边在源码里查不到**」（它们在 405/419/423/428 行）。**串链说的是执行顺序与数据流，星形说的是调用图，两个层次，别互相否掉。**',
        "handler": 'brain_unify',
        "safe": True,
    },
    "root_fix": {
        "domain": 'system',
        "desc": '根治环：症状五问诊断/补丁债量化/根治铁律——她自己必须懂的根源追踪纪律',
        "handler": 'root_fix',
        "safe": True,
    },
    "cross_scan": {
        "domain": 'system',
        "desc": '扫描一下/扫一下/深度扫描/交叉扫描/穿透式扫描/全框架扫：深度穿透式交叉验证（注册↔路由↔导入↔断链↔运行时↔多扫描器互证，十维），扫描器互相咬、不各报各的',
        "handler": 'cross_scan',
        "safe": True,
    },
    "inventory": {
        "domain": 'system',
        "desc": '全息盘点：一次输出你的视图+框架的视图（归属四分类：框架/环境/数据/异物）——对齐两个世界',
        "handler": 'inventory',
        "safe": True,
    },
    # R-H94 · 脑库接入（主人 2026-09-19 拍）：大模型接入大脑记忆，跟着一起上线
    "brain_vault": {
        "domain": 'mind',
        "desc": '脑库接入：Obsidian 记忆库的读（recall=记忆总纲+收集箱）/ 写（remember=追加一条）/ 体检（status）—— 追加式、**没有任何删除路径**，写进去的想忘都忘不了',
        "handler": 'brain_vault',
        "safe": True,
    },
    "think_loop": {
        "domain": 'llm',
        "desc": '推演环：理解需求→镜像维度推演→调用工具执行→自我纠错→反向延伸→反思进取→整理结果（完整心智循环）',
        "handler": 'think_loop',
        "safe": True,
    },
    "one_key_deploy": {
        "domain": 'pipeline',
        "desc": '一指定江山乾坤换位：抓取(GitHub/本地)→镜像→验证→晋升一条命令，一次性上线零修改',
        "handler": 'one_key_deploy',
        "safe": True,
    },
    "deploy_queue": {
        "domain": 'pipeline',
        "desc": 'AI 接管部署队列：submit 入队 / tick 部署下一个（完一个自动下一个）/ status 全景',
        "handler": 'deploy_queue',
        "safe": True,
    },
    "mirror_shape": {
        "domain": 'pipeline',
        "desc": '镜像空间：维度成形（假设/架构虚拟/反复打磨全在镜像维度，现实无感知）',
        "handler": 'mirror_shape',
        "safe": True,
    },
    "mirror_scan": {
        "domain": 'pipeline',
        "desc": '镜像空间：维度体检（完整性/署名/纪律/入口——跨维晋升前置）',
        "handler": 'mirror_scan',
        "safe": True,
    },
    "mirror_plan": {
        "domain": 'pipeline',
        "desc": '镜像空间：生产前排练计划（假设/架构/步骤/服务与环境契约/验收/回滚）',
        "handler": 'mirror_plan',
        "safe": True,
    },
    "mirror_simulate": {
        "domain": 'pipeline',
        "desc": '镜像空间：静态推演（文件/依赖图/端口/入口/契约/闭环定义，不碰生产）',
        "handler": 'mirror_simulate',
        "safe": True,
    },
    "mirror_parity": {
        "domain": 'pipeline',
        "desc": '镜像空间：沙盒与生产环境契约一致性（平台/Python/依赖/工具/密钥存在性/路径）',
        "handler": 'mirror_parity',
        "safe": True,
    },
    "mirror_rehearse": {
        "domain": 'pipeline',
        "desc": '镜像空间：生产前排练（静态推演→环境一致性→沙盒闭环→指纹绑定报告）',
        "handler": 'mirror_rehearse',
        "safe": True,
    },
    "mirror_release": {
        "domain": 'pipeline',
        "desc": '镜像空间：排练全绿后一次性全量晋升生产（树/计划指纹绑定，失败即阻断）',
        "handler": 'mirror_release',
        "safe": True,
    },
    "mirror_ascend": {
        "domain": 'pipeline',
        "desc": '镜像空间：跨维晋升（验证全绿才放行；一次性全量写入现实+护照+时间线；现实零修改）',
        "handler": 'mirror_ascend',
        "safe": True,
    },
    "mirror_status": {
        "domain": 'pipeline',
        "desc": '镜像空间：维度状态（镜像/现实指纹、现实漂移检测、时间线史）',
        "handler": 'mirror_status',
        "safe": True,
    },
    "mirror_rewind": {
        "domain": 'pipeline',
        "desc": '镜像空间：时间线回滚（回到过去的时间线，同样一次性全量替换）',
        "handler": 'mirror_rewind',
        "safe": True,
    },
    "auth_gate_status": {
        "domain": 'system',
        "desc": '人工授权门状态：各作用域可用授权数（只读；授权只能人发放）',
        "handler": 'auth_gate_status',
        "safe": True,
    },
    "transfer": {
        "domain": 'engine',
        "desc": '数据传输算子（核心传输工具）：map/filter/merge/unique/sort/pluck/collect 等 14 个纯变换算子',
        "handler": 'transfer',
        "safe": True,
    },
    "wf_cache_clear": {
        "domain": 'engine',
        "desc": '万能插：清空传输缓存（同输入复用的节点结果缓存）',
        "handler": 'wf_cache_clear',
        "safe": True,
    },
    "signature_guard": {
        "domain": 'system',
        "desc": '署名守卫：扫描全框架页面开发者署名完整性，缺失即报可按需自动补回（禁止删除）',
        "handler": 'signature_guard',
        "safe": True,
    },
    "file_hygiene": {
        "domain": 'system',
        "desc": '文件卫生层：按 LAYOUT.md 家规自检乱放+自动归位（散落/空壳/越界数据/缓存）',
        "handler": 'file_hygiene',
        "safe": True,
    },
    "devour_scan": {
        "domain": 'devour',
        "desc": '吞天：能力缺口扫描（域覆盖对照+进化方向）',
        "handler": 'devour_scan',
        "safe": True,
    },
    "devour_github": {
        "domain": 'devour',
        "desc": '吞天：吞噬 GitHub 仓库为知识胶囊（自我进化的核心——吸收外部能力）',
        "handler": 'devour_github',
        "safe": True,
    },
    "agency_tentacles": {
        "domain": 'tentacle',
        "desc": '职业触手中枢：吸收 Agency Agents 职业资料；每根触手独立统一大模型会话与隔离镜像房间；支持并发汇总',
        "handler": 'agency_tentacles',
        "safe": True,
    },
    "media_pipeline": {
        "domain": 'video',
        "desc": 'AI短视频/电影/音乐流水线：镜像房间编排、产物自审、版权/安全/品牌/质量检查、主人授权后发布',
        "handler": 'media_pipeline',
        "safe": True,
    },
    "edit_pipeline": {
        "domain": 'video',
        "desc": '剪辑引擎（蒸馏剪映时间线语义）：轨道→片段→目标/源时间区间→变速/音量/转场/文本，真渲染 1080x1920 成片（ffmpeg + libass 烧字幕）或导出剪映草稿；写面自收窄到 projects/·outputs/·.scratch/（policy 无条目 ⇒ 门内零作用域，故自钉）',
        "handler": 'edit_pipeline',
        "safe": False,
    },
    "tentacle_pipeline": {
        "domain": 'tentacle',
        "desc": '触手自动化流水线：四层七步、三公理、五红线；隔离执行、逐层汇报、dry-run 读数、终审只判不改、发布带回滚',
        "handler": 'tentacle_pipeline',
        "safe": True,
    },
    "long_run_supervisor": {
        "domain": 'tentacle',
        "desc": '长程无人值守任务监督：租约、心跳、检查点、有界重试、断点续作和主人升级',
        "handler": 'long_run_supervisor',
        "safe": True,
    },
    "devour_reflect": {
        "domain": 'devour',
        "desc": '吞天：反思（回顾吞噬历史学习模式，发现弱能力与重组机会）',
        "handler": 'devour_reflect',
        "safe": True,
    },
    "devour_pulse": {
        "domain": 'devour',
        "desc": '吞天：完整认知循环（吞噬→反思→消化→重组→进化）',
        "handler": 'devour_pulse',
        "safe": True,
    },
    "mcp_connect": {
        "domain": 'tentacle',
        "desc": '触手契约层：连接任意 MCP 工具服务器（学会契约协议=接入整个 MCP 生态）',
        "handler": 'mcp_connect',
        "safe": True,
    },
    "mcp_tools": {
        "domain": 'tentacle',
        "desc": '触手契约层：列出已连接服务器的工具契约清单（名称+参数 schema）',
        "handler": 'mcp_tools',
        "safe": True,
    },
    "mcp_call": {
        "domain": 'tentacle',
        "desc": '触手契约层：按契约调用已连接服务器的任意工具',
        "handler": 'mcp_call',
        "safe": True,
    },
    "coze_mail": {
        "domain": 'comms',
        "desc": '通信域：对主人自有的单一地址（@coze.email）收发与整理；白名单默认空（全拒）、confirm_token 绑定内容、正文不入档、独立通道 coze_mail',
        "handler": 'coze_mail',
        "safe": True,
    },
    "create": {
        "domain": 'creation',
        "desc": '创作出口：创作意图/产物登记 ＋ 仅限 outputs/ 的文本写入；文本出口待接线（如实报 pending、不发网络请求）、覆盖必带 confirm_token ＋ 写前备份 ＋ 双向 SHA、独立通道 create',
        "handler": 'create',
        "safe": True,
    },
    # 短剧/影视链路 · 模块1（Owner 2026-09-19）：十二个模块里唯一的链头 ——
    # 下游「资产锚定/图生视频/配音/音乐/合成」全吃它的输出，链头契约错了后面全错。
    # 触发词压进 desc[:60]：主人说"拆分镜/剧本转分镜/短剧分镜"直接命中，不必记能力名。
    "drama": {
        "domain": 'creation',
        "desc": '剧本转分镜/拆分镜/分镜/短剧/故事板/剧本理解：剧本 → 结构化镜头表（景别·运镜·时长·情绪·角色位置·描述），字段齐全度与时长和逐条如实报；确定性路径离线只做切分，语义路径走她的模型通道，两条不互相冒充',
        "handler": 'drama',
        "safe": True,
    },
    "tentacle_status": {
        "domain": 'tentacle',
        "desc": '触手自诊断：硬件层就绪度 + 依赖分层 + 邻域覆盖',
        "handler": 'tentacle_status',
        "safe": True,
    },
    "tactics_advise": {
        "domain": 'longrun',
        "desc": '察言观色层：识别沟通信号→给出表达分寸（只调怎么说，不改事实）',
        "handler": 'tactics_advise',
        "safe": True,
    },
    "pipeline_submit": {
        "domain": 'pipeline',
        "desc": '生产管线：镜像多维度空间→门禁审计→生产写入（唯一交付通道）',
        "handler": 'pipeline_submit',
        "safe": True,
    },
    "pipeline_versions": {
        "domain": 'pipeline',
        "desc": '生产管线：产物版本历史与当前指纹（.versions/ 链）',
        "handler": 'pipeline_versions',
        "safe": True,
    },
    "pipeline_rollback": {
        "domain": 'pipeline',
        "desc": '生产管线：回滚产物到历史版本（回滚也走审计留痕）',
        "handler": 'pipeline_rollback',
        "safe": True,
    },
    "pipeline_status": {
        "domain": 'pipeline',
        "desc": '生产管线：查发布记录（发布/阻断全留痕）',
        "handler": 'pipeline_status',
        "safe": True,
    },
    "ghost_guard": {
        "domain": 'pipeline',
        "desc": '防复发检测：幽灵目录/备份散件/攻击残留/注册表冲突扫描',
        "handler": 'ghost_guard',
        "safe": True,
    },
    "sched_define": {
        "domain": 'engine',
        "desc": '定时触发器：定义调度（工作流 + 间隔），无人值守自动执行',
        "handler": 'sched_define',
        "safe": True,
    },
    "sched_tick": {
        "domain": 'engine',
        "desc": '定时触发器：扫描到期调度并执行（可由循环/计划任务驱动）',
        "handler": 'sched_tick',
        "safe": True,
    },
    "sched_status": {
        "domain": 'engine',
        "desc": '定时触发器：查调度状态（上次执行/结果）',
        "handler": 'sched_status',
        "safe": True,
    },
    "svc_inspect": {
        "domain": 'pipeline',
        "desc": '服务巡检：探活已登记服务端口并落审计（只看不动）',
        "handler": 'svc_inspect',
        "safe": True,
    },
    "vision": {
        "domain": 'vision',
        "desc": '视觉/图像识别入口（良性子集，需外部依赖时留待接入）',
        "handler": 'vision',
        "safe": True,
    },
    "prompt_bridge": {
        "domain": 'llm',
        "desc": '提示词转化挂件（只读/纯本地）：大白话 -> 四段结构化提示词；compile / passthrough / status',
        "handler": 'prompt_bridge',
        "safe": True,
    },
    "audio_extract": {
        "domain": 'video',
        "desc": '从视频里取出声音（本机 ffmpeg，**零出网**）：probe/tracks 读流与音轨（只读）；extract 真出音频件（mp3/aac/m4a/wav/flac/ogg/opus/wma 八种，可切段/调音量/响度归一）。**产出即验证**：落盘后 ffprobe 回读产物，把真读数一并返回。写面自收窄到 projects/·outputs/·.scratch/（policy 无该 kind ⇒ 门内零作用域，故自钉）。格式知识来自 online-audio-converter.com/blog/audio-formats（容器≠编解码器 / 有损与无损两族）。',
        "handler": 'audio_extract',
        "safe": False,
    },
    "audio_mix": {
        "domain": 'video',
        "desc": '混音与母带（本机 ffmpeg，**零出网**）：`mix` 多轨合成（amix，逐路音量，显式 normalize=0）；`master` 响度归一（**两遍法 loudnorm**：先量后施加，第一遍的四个测量值随结果返回）。响度标准表 streaming -14 / podcast -16 / broadcast -23 / cinema -27 LUFS + 曲风动态预算（**与托管技能 music-production 的 -14 LUFS 口径对齐**，不另立第二套）。填的是 media_flow 的 music/04-mix、music/05-master、film/04-assets 三格。写面自收窄到 projects/·outputs/·.scratch/（policy 无该 kind ⇒ 门内零作用域，故自钉）；复用 audio_extract 的写面守卫与验证器（**不重写**）。',
        "handler": 'audio_mix',
        "safe": False,
    },
    "media_license": {
        "domain": 'video',
        "desc": '素材许可账（三方向流程台「家规第 2 条：没有许可的素材不许进成品格」的数据源）：`register` 逐件登记（**现算 sha256** + 出处 + 授权 + 时间）、`unregister` 撤销（**必须写 why**，留档在 removed）、`status`/`list`/`check` 只读核对（账↔盘：陈旧 / sha 对不上 / 漏登）。🔴 **source 与 license 为空一律拒绝**——空着的许可记录比没有记录更坏（让人以为查过了）。只登记盘上真有的仓内素材；写面只落 `projects/_shared/licenses/`。**只登记与核对，不判定授权是否真实/充分**（那是主人的事）。',
        "handler": 'media_license',
        "safe": False,
    },
    "datakit": {
        "domain": 'data',
        "desc": '本地数据工具（**只读**）：html→markdown · html→表格结构 · xlsx 字节→JSON · JSON 美化/排序 · 多段 CSV 合并（`op` 分派，见 `tools/datakit.py` 的 OPS）。🔴 **结果从返回里给、不落盘** ⇒ 作用域天然为空，**不需要也不该改 `policy.py`**。**为什么不给落盘版**：一个会写盘的新能力位若 policy 里没有分支，就是**绕过门**；`policy.py` 是安全文件，只有主人能改 —— 要落盘请他加分支。',
        "handler": 'datakit',
        "safe": True,
    },
    "media_run": {
        "domain": 'video',
        "desc": '三方向自动化工作流**执行器**：一次调用把一条链从头走到尾，每步落真件 + 同批登记许可。链取自 `media_pipeline.KINDS`（music: lyrics→arrangement→audio→master→export · short_video: script→storyboard→assets→edit→export · film: concept→script→shots→sound→edit→export）。🔴 **没有实现器的步如实标 `not_implemented`**（人/未实现的活不许当成跑过了）；自产输入（本机 ffmpeg 合成）⇒ 许可可如实写自有。落点只在 `projects/<方向>/<格>/`，命名合家规。',
        "handler": 'media_run',
        "safe": False,
    },
    "media_publish": {
        "domain": 'video',
        "desc": '三方向**发布到赚钱平台**的准备与授权门：`platforms <方向>` 读平台口径（**音乐复用能力位 `music_publishing` 的 13 平台，不另造**；短视频 7 / 电影 6 为内置候选表，**全部标「未核实」**）· `prepare` 备发布包（产物 sha256 + 许可摘录 + 元数据模板 + 目标平台 + 闸清单，落 `projects/_shared/publish/`，**不污染 18 格抽屉**）· `submit` **永远 blocked**（发布=不可逆外部动作，需主人 `deploy_publish` 一次性授权；本机零平台凭据；`media_pipeline.publish` 明写「不接受自带令牌绕门」）。**零出网、不发任何请求、绝不返回「已发布」** —— 自动化的终点站是主人的门。',
        "handler": 'media_publish',
        "safe": False,
    },
    "voice": {
        "domain": 'voice',
        "desc": '语音合成/识别入口（良性子集）',
        "handler": 'voice',
        "safe": True,
    },
    "voice_orchestra": {
        "domain": 'voice',
        "desc": '语音技能中枢（多维度场景编排，只读）：技能原子检索 / 场景 Pipeline / 本机可跑性；今日挂 tools tab，升格条件见模块 docstring',
        "handler": 'voice_orchestra',
        "safe": True,
    },
    "browser": {
        "domain": 'automation',
        "desc": '浏览器自动化入口（良性子集）。op=open/search/fetch/automate 走 browser_cap 三级后端；op=native（别名 deep/controller/cdp）走原生浏览器窗口 native_browser.py（Chrome DevTools Protocol，自带最小 RFC6455 客户端、零第三方依赖），动作放 action：status/list_tabs/get_title/get_url/get_text/dom_query/get_cookies/intercept_events/intercept_status 为只读免卡，launch/ensure/create_tab/close_tab/activate_tab/navigate/reload/back/forward/click_element/type_text/execute_script/inject_script/set_cookies/privacy_mode/intercept_requests/intercept_stop/pin_window 需 browser_control，screenshot 另需 filesystem_write',
        "handler": 'browser',
        "safe": True,
    },
    "bluetooth": {
        "domain": 'device',
        "desc": '蓝牙设备控制：扫描附近 BLE 设备、连接读写 GATT 特征（操控空调/灯/音箱等家居设备）、经典蓝牙状态报告',
        "handler": 'bluetooth',
        "safe": True,
    },
    "bt_control": {
        "domain": 'device',
        "desc": 'AI 智能蓝牙操控：自然语言意图→扫描识别设备→协议匹配→组装指令→写入执行→验证（协议库只收公开文档协议，未知如实报告）',
        "handler": 'bt_control',
        "safe": True,
    },
    "quant": {
        "domain": 'finance',
        "desc": '量化/回测入口（外部业务模块 quant_tech，未挂载则如实报缺口）',
        "handler": 'quant',
        "external": 'quant_tech',
        "safe": True,
    },
    "life": {
        "domain": 'life',
        "desc": '生命档案：事件记录、时光轴、每日回顾、章节、承诺、习惯、反思与 Vault 导出（写框架 store，不出网）',
        "handler": 'life',
        "safe": True,
    },
    "mind": {
        "domain": 'mind',
        "desc": '心智引擎：开工前预演 pre_work、评估、内部状态、经验召回与反思（写框架 store，不出网）',
        "handler": 'mind',
        "safe": True,
    },
    "project_context": {
        "domain": 'project',
        "desc": '项目上下文：**文档面**（blueprint 蓝图 / brief 简报 / search 只读检索 / status）＋ **代码结构四面**（2026-09-23 接，补上「专业级编程AI」缺的那半身）：`symbols` 符号（顶层 def/class，可按名问「在哪定义」）· `deps` 依赖（内部 import 边 + 外部三方名）· `calls` 调用图（**复用现成 `tools/call_graph.py`**：find/callers/callees/trace/dead_code，4.2s / 351 文件）· `tests` 测试面（模块被哪些测试**提到**过）· `structure` 三面速览（4.4s，**刻意不含调用图**）。全部只读。⚠️ 四处诚实边界随结果一起带出：符号只收**顶层**；依赖只看 **import 语句**；调用图带**未解析率**（本仓约 0.66，所以「没人调用」先天有缺口）；测试面是**提到过**的代理**不是行覆盖**。',
        "handler": 'project_context',
        "safe": True,
    },
    # 话题追踪（Owner 2026-09-18 批准 · 商店卡片「含 0 个技能」补环）
    # 为什么放这里：brain_exec.route 对 name+desc[:60] 做 2-gram 匹配，
    # 所以「关键词→能力」的映射就是这条 desc —— 不另建关键词表，避免两处口径打架。
    "topic_watch": {
        "domain": 'recon',
        "desc": '话题追踪：追踪/盯着/有变化/告诉/话题/持续关注/每天给我/早报/动态/最新/行业/新闻/股价/行情/视频。追踪你关心的话题，梳理最新动态，有变化就告诉我。触发词表全量见 topic_watch.INTENT_MAP；命中后转邻域技能链，不新增进程、不复制技能实现。',
        "handler": 'topic_watch',
        "safe": True,
    },
    # 爆火作品观察 + 用户偏好台账（Owner 2026-09-19：调用触手就要观察每日所有的，
    # 爆火作品观察细微点，至少要知道用户喜欢什么样的东西）。
    # 触发词压进 desc[:60]，主人说"爆火/热门/热搜/用户喜欢什么"直接命中，不必记能力名。
    # 与 topic_watch 的分工：那边管"我关心的变没变"（动态，会过期）；这边管"用户喜欢什么"
    # （偏好条目，是能反过来指导创作的资产）。两件事两张表，不互相冒充。
    "trend_watch": {
        "domain": 'recon',
        "desc": '爆火作品观察/热门爆款/热搜/点赞高/涨粉快/用户喜欢什么/什么受欢迎/偏好：每日观测爆火作品的细微点，落成用户偏好台账（作品·平台·热度·细微点·偏好条目），挂现成心跳、零新增进程；拿不到数据如实报缺口，绝不编偏好',
        "handler": 'trend_watch',
        "safe": True,
    },
    # ── 只读能力（R-H162 · 2026-09-19）：今日 5 个新模块接进万能插 ──
    # 全部**只读**：不带执行能力 · 不写盘 · 不出网；注册 ↔ 路由**同刀落地**（原子单元）
    "projection_card": {
        "domain": 'tools',
        "desc": '空间投射只读卡片：5 原语全标未核实 + ARM ≠ LIVE 红线（只呈现不执行）',
        "handler": 'projection_card',
        "safe": True,
    },
    "trace_store": {
        "domain": 'system',
        "desc": '痕迹库只读读数：五张表（wave_samples/traces/trace_links/promotes/obsessions）条数',
        "handler": 'trace_store',
        "safe": True,
    },
    "wave_probe": {
        "domain": 'system',
        "desc": '痕迹触手只读量一次波动（默认只量不写；trigger_mode 与盲区一并回报）',
        "handler": 'wave_probe',
        "safe": True,
    },
    "dream_replay": {
        "domain": 'brain',
        "desc": '做梦技能只读重演：五原语闭环，不写盘、不执行（巩固默认不开）',
        "handler": 'dream_replay',
        "safe": True,
    },
    "capability_net": {
        "domain": 'tools',
        "desc": '穿透网七栏只读读数：indexed/entry_known/reachable/verified×2/has_test/penetrate_ready',
        "handler": 'capability_net',
        "safe": True,
    },
    "director_mood": {
        "domain": 'mind',
        "desc": '导演 AI 情绪内核（只读）：七情六欲 + 半衰期；情绪只改『怎么看』，不改『看到什么』',
        "handler": 'director_mood',
        "safe": True,
    },
    "music_publishing": {
        "domain": 'creation',
        "desc": 'AI 音乐发布平台三层只读归位（生成端/Agent 原生端/分发端）；全部标『未核实』',
        "handler": 'music_publishing',
        "safe": True,
    },
    "music_intel": {
        "domain": 'recon',
        "desc": '音乐情报组（只读骨架）：合规红线/过审/流量/画像/竞品/**禁区清单** 六维覆盖',
        "handler": 'music_intel',
        "safe": True,
    },
    "video_intel": {
        "domain": 'recon',
        "desc": '短视频情报组（只读骨架）：六维覆盖；禁区清单优先于流量趋势',
        "handler": 'video_intel',
        "safe": True,
    },
    "film_intel": {
        "domain": 'recon',
        "desc": '影视情报组（只读骨架）：六维覆盖；情报是输入不是指令（生成端仍有过目权）',
        "handler": 'film_intel',
        "safe": True,
    },
    "account_registry": {
        "domain": 'data',
        "desc": 'AI 账号登记表只读校验：一人一号（不共用账号/不共用凭证/只记路径/不许无主账号）',
        "handler": 'account_registry',
        "safe": True,
    },
    "verification_watch": {
        "domain": 'recon',
        "desc": '人机验证情报台账（只读）：不主动绕做成机械闸；三部门各一张空台账',
        "handler": 'verification_watch',
        "safe": True,
    },
    "shared_resources": {
        "domain": 'system',
        "desc": '共享资源池（只读骨架）：虚拟号/邮箱按需租借——资源可共享、身份不共享、每次调用留痕',
        "handler": 'shared_resources',
        "safe": True,
    },
    "brand_outro": {
        "domain": 'creation',
        "desc": '品牌片尾只读渲染：署名/自述/致谢三层 + 四条红线（署名不造假·致谢不套话·承诺可追溯·观众不当流量）',
        "handler": 'brand_outro',
        "safe": True,
    },
    "emotion_projection": {
        "domain": 'creation',
        "desc": '情感投射只读骨架：叙事四问 → 投射细节 → 四项校验；『身临其境』只有人能判',
        "handler": 'emotion_projection',
        "safe": True,
    },
    "proactive_report": {
        "domain": 'mind',
        "desc": '主动汇报引擎只读判据层：四类汇报（新奇发现/主人需要/记忆命中/赚钱机会）+ 四维打分 + 不打扰门（静默时段/预算/去重/及格线）+ 短律成句；只判不说',
        "handler": 'proactive_report',
        "safe": True,
    },
    "observer_anchor": {
        "domain": 'mind',
        "desc": '观察者锚点律只读骨架：三公理 + 六短板补齐 + 五条红线（同一方不许既扫又报/审计器必须被审/递归封顶/终止点只能由人设/关键节点人在场）',
        "handler": 'observer_anchor',
        "safe": True,
    },
    "persona_kernel": {
        "domain": 'mind',
        "desc": '性格内核 v4.0：外温表达十律 + 内刚四基石（止损/主动/洞察/静待）+ 十条机械红线；四大基石原文一字不差；evolve 是唯一写口（驱动心智演化）',
        "handler": 'persona_kernel',
        "safe": True,
    },
    "hook_registry": {
        "domain": 'system',
        "desc": '钩子矩阵只读注册表：50 钩子/六类/三层 + 三条红线（L3 不许挂触手内·失败隔离·链可中断）',
        "handler": 'hook_registry',
        "safe": True,
    },
    "scene_anchor": {
        "domain": 'creation',
        "desc": '场景锚定只读骨架：8 大类场景 + 灵魂四要素 + 钩子锚场景不锚情绪（作品是为场景做的）',
        "handler": 'scene_anchor',
        "safe": True,
    },
    "code_art": {
        "domain": 'creation',
        "desc": '代码艺术内核（只读骨架）：INDEX/SEED/CANVAS/LAYER/EXPORT 五原语；无种子不许导出',
        "handler": 'code_art',
        "safe": True,
    },
    "orchestration_kernel": {
        "domain": 'system',
        "desc": '编排内核（三源蒸馏）：状态/动作空间 + 角色/流程 + 可存储图/挂起恢复；只读能力真执行',
        "handler": 'orchestration_kernel',
        "safe": True,
    },
    "render_evolution": {
        "domain": 'creation',
        "desc": '渲染进化内核（只读骨架）：五原语 + 三闭环 + 六红线；帕累托前沿机器画、人点',
        "handler": 'render_evolution',
        "safe": True,
    },
    "caps_called_audit": {
        "domain": 'system',
        "desc": '能力位调用点审计（只读）：动态算 called_by，列出零调用点孤儿清单（同名模块自称不算接线）',
        "handler": 'caps_called_audit',
        "safe": True,
    },
    "tentacle_cognition": {
        "domain": 'system',
        "desc": '触手认知包（只读骨架）：任务上下文/角色边界/自检三问/不确定上报/操作留痕 + 五条零容忍红线',
        "handler": 'tentacle_cognition',
        "safe": True,
    },
    "coverage_auditor": {
        "domain": 'system',
        "desc": '触手覆盖审计（只读骨架）：八短板↔八触手组 + 覆盖率读数 + 死角登记 + 五条红线',
        "handler": 'coverage_auditor',
        "safe": True,
    },
    "model_key_pool": {
        "domain": 'llm',
        "desc": '模型密钥池（只读骨架）：按 owner_ai_id 分池、触手只借不拥有、DPAPI 只存路径、超限只上报',
        "handler": 'model_key_pool',
        "safe": True,
    },
    "meta_cognition": {
        "domain": 'mind',
        "desc": '元认知循环（只读骨架）：自省→查内部→查外部→问主人→沉淀 + 五条红线（自省不是自责/不许硬猜/先查后问/问完沉淀/大脑也自省）',
        "handler": 'meta_cognition',
        "safe": True,
    },
    "libtv_skill": {
        "domain": 'video',
        "desc": 'LibTV 技能（只读骨架·门）：Agent 创作平台入口（会话进展/增量轮询 + 切项目 + 批量下载）；密钥走 model_key_pool、结果必须落 trace_store',
        "handler": 'libtv_skill',
        "safe": True,
    },
    "a1art_skill": {
        "domain": 'image_video',
        "desc": 'a1.art API 技能（只读骨架·门）：五原语 LOOKUP→UPLOAD→GENERATE→OPTIMIZE→POLL；密钥只走 DPAPI/密钥池、结果必须落盘、不调不支持组件、810012 如实报',
        "handler": 'a1art_skill',
        "safe": True,
    },
    "energy_pool": {
        "domain": 'system',
        "desc": '能源池（只读骨架·内调）：模型=燃料不是身份；能源抽象 EnergySource + 原生衍生器 + 按需分配；五条红线（模型非身份/能源可换栈不动/衍生码走原生路由/按需/没能源如实报缺）',
        "handler": 'energy_pool',
        "safe": True,
    },
    "local_brain": {
        "domain": 'mind',
        "desc": '本地原生脑（只读骨架·内调）：本地模型=脑皮层（可换）·主机=纪律层（不可换）；五层链路（模型只做意图解析与结果解释）；五条红线（不许直接执行命令/不可逆必卡/缺参不许猜/每次留痕/身份不许改写）',
        "handler": 'local_brain',
        "safe": True,
    },
    "auto_switch": {
        "domain": 'mind',
        "desc": '自动化切换引擎（只读骨架·内调）：意图分析(L1解析+L2交叉验证+L3置信度)→任务分级→模型切换→原生执行→验证审计；接线点只有 Intent JSON；五条红线（低置信先问主人/不许直接执行/每次切换记 model_used/不可逆二次确认/身份不许改写）',
        "handler": 'auto_switch',
        "safe": True,
    },
    "context_vault": {
        "domain": 'system',
        "desc": '上下文归档库（只读骨架·内调）：**索引+检索层，不是第四处存储**（只引用不复制正文）；内存多大上下文就多长（按**可用**内存算预算，不足则降级如实报）；快速搜索=倒排求交→打分→按预算裁剪',
        "handler": 'context_vault',
        "safe": True,
    },
    "feishu_embed": {
        "domain": 'integration',
        "desc": '飞书镶嵌窗口（只读骨架·门）：面板卡⑥，**走浏览器触手不用 API**；四条红线（飞书是副本本地是源/凭据不许明文/不绕验证/每次操作留痕 source_kind=feishu）',
        "handler": 'feishu_embed',
        "safe": True,
    },
    "libtv_workflow": {
        "domain": 'video',
        "desc": 'LibTV 节点式工作流（只读骨架·门）：五动作 create_node/connect/set_params/run/batch_run + 五大基础节点 + 参数契约（-s 走 schema / -u 顶层）+ 两条避坑（资源组绑定 / 终点抑制 stdout）；四条红线引用已有，不重造',
        "handler": 'libtv_workflow',
        "safe": True,
    },
    "gate_visibility": {
        "domain": 'framework',
        "desc": '门可见性审计（只读骨架·门）：三态=已纳入/显式不纳入/未决定 —— 回答『门看得见什么、看不见什么』（坑册 §60）；可见范围只从 framework_gate 读，不复刻第二份范围表；四条机械闸（三态不许漏/不纳必须带出处/已纳入必须命中门规则/空样本不许当绿）',
        "handler": 'gate_visibility',
        "safe": True,
    },
    "h3_video_gen": {
        "domain": 'video',
        "desc": 'H3mini 视频生成（只读骨架·门）：四原语 T2VA/I2VA/FL2VA/Ref2VA + 三条带牙用例（密钥不走明文 / 结果必须落盘 / 提示词必须走官方六段式不接受散文式）+ 五条红线（密钥DPAPI/结果落盘/不绕官方入口/硬件门槛先验/每次留痕）；**引用官方仓库技能，不复制 SKILL.md**；type=external',
        "handler": 'h3_video_gen',
        "safe": True,
    },
    "absorb_loop": {
        "domain": 'brain',
        "desc": '吞天闭环（只读骨架）：蒸馏 DISTILL → 提炼 REFINE → 吸收 ABSORB + 回灌 FED_BACK；四条机械闸（stage_dirty 阶段间不许留垃圾 / loop_not_closed 三阶段必须齐且回灌 / junk_left_silently 垃圾要么清要么登记 / not_resumable 中断必须留续跑点）+ 五条红线（吞完清场/闭环可续/每阶段留痕 source_kind=absorb/不吞未取证来源/垃圾不许静默留）',
        "handler": 'absorb_loop',
        "safe": True,
    },
    "cloud_pc": {
        "domain": 'infra',
        "desc": '云电脑独立窗口（只读骨架·门）：面板加一个**独立窗口**给她（数字人）**安装**云电脑（卡片 + 触手，**不是 iframe**）；五原语 PROVISION/CONNECT/STATUS/SNAPSHOT/RELEASE（逐个标花钱与不可逆）；五条红线（密钥DPAPI/先算账再花钱/每次留痕 source_kind=cloud_pc/不绕官方入口/身份内核不变）；type=external',
        "handler": 'cloud_pc',
        "safe": True,
    },
    "auto_publish": {
        "domain": 'social',
        "desc": '社交推广 / 发布作品 / 收益平台·**全自动执行**（只读骨架·门）：五原语 PLAN/COMPOSE/PUBLISH/TRACK/SETTLE；核心口径 = **全自动 = 除「发布/提现/改价」之外全自动**（那几下不可逆+涉钱 ⇒ 必须过门：逐条确认或有 TTL 的令牌，默认 0 张）；六条红线（发布过门/密钥DPAPI/每次留痕 source_kind=publish/一人一号/收益只汇总不代提/不刷量）；平台名单**主人未给 ⇒ 一个平台名都不编**；type=external',
        "handler": 'auto_publish',
        "safe": True,
    },
    "awesome_tools_index": {
        "domain": 'tools',
        "desc": 'Awesome Tools 蒸馏索引（只读骨架·地图）：四原语 INDEX/LOOKUP/MAP/VERIFY；三条带牙判据（**索引只读** index_not_readonly / **映射可追** map_without_source / **未核实不标绿** unverified_green）+ 五条红线（只读/映射带出处/未核实不标绿/只引用不复制/不绕官方入口）；主人明确配对的六个重点工具（CC Switch→auto_switch · MoneyPrinterTurbo/Huobao Drama/LocalMiniDrama→video_pipeline · CowAgent→im_multiplex · OpenClaw Monitor→god_view）**全部 unverified（盘上 0 命中）**；仓库内容未取证 ⇒ 索引池为空且**不编**；type=external',
        "handler": 'awesome_tools_index',
        "safe": True,
    },
    "stigmergy": {
        "domain": 'collab',
        "desc": '**协作层的间接通道**：Stigmergy（共识主动性 / 信息素场地）。四原语 DEPOSIT/READ/DECAY/FORAGE；只有 DEPOSIT 会写、且**只追加**（挥发是读数，账本可回放）。五条红线做成机械闸：**无源不许留** deposit_without_source · **种类白名单** deposit_kind_not_allowed · **只追加** pheromone_deleted_or_overwritten（静态核本模块源码）· **不留明文密钥** plaintext_key_in_pheromone · **只给读数**（FORAGE 只排序不执行）。与 collab_gateway **并排、不替代**：直连=会话/对等方/收件箱，间接=信息素场地；场地放在 store/collab/stigmergy/。type=internal',
        "handler": 'stigmergy',
        "safe": True,
    },
    "ledger_note": {
        "domain": 'system',
        "desc": '**台账登记**（R-H600 立）：三原语 RULES（读七道硬闸）/ PREVIEW（只读预演，不落盘）/ APPEND（**唯一写原语**）。七道机械闸全做成闸、不是口号：**目标固定**（只能写 gbt_allinone/docs/待落刀登记.md，**调用方传不了路径**）· **只追加**（目标末尾必须是换行，否则拒写，不修不补）· **单物理行**（行内不许换行 ⇒ 一刀一个物理行）· **禁半角双引号**（中文串用「」）· **行首形状**（`> **<label> 补记`，复核脚本按行首锚定）· **幂等**（同 label 已存在 ⇒ 拒写）· **缺前驱拒写**（给了 after 就必须是当前最后一条，防插队防回填）。⚠️ 它**不判内容对错**（那是取证 + 独立复核的活）；写失败一律抛错，不返回半成功。type=internal',
        "handler": 'ledger_note',
        "safe": True,
    },
    "code_patch": {
        "domain": 'tools',
        "desc": '**改代码的唯一过门入口**（2026-09-23 接）：此前 agent 直接 edit/write 落盘 ⇒ **不过门、没审计、没信封、没改前改后凭据**。三原语 dry_run（**默认，只算不写**）/ apply（落盘，挂 filesystem_write）/ rollback（按回执退回）。九道机械闸：**仓内**（路径解析后必须在仓内）· **find 恰好一次**（0 次 not_found；>1 次 ambiguous —— **绝不替你挑一个**）· **空改动拒写** · `expect_sha256` 对不上拒（防拿陈旧内容改）· **二进制拒改**（前 8KB 有 NUL）· >4MB 拒改 · **逐字节替换**（换行/BOM 一个字节不动 —— 文本层替换会把整个文件行尾改掉）· **原子写**（tmp+os.replace）· **回执可回滚**（记 find/replace/改前改后哈希；回滚前先核 after_sha256，对不上就拒）。type=internal',
        "handler": 'code_patch',
        "safe": False,
        "requires_params": True,
        "params": ['path', 'find', 'replace'],
        "params_hint": 'path=仓内相对路径；find=必须**恰好出现一次**的原文；replace=新文；默认 op=dry_run（只算不写），要落盘给 op=apply（要 filesystem_write 授权）',
    },
    "git_read": {
        "domain": 'tools',
        "desc": '**版本库只读面**（2026-09-23 接，补 `code_patch` 的另一半：「改完要能看、要能回滚」）：op=status/diff/log/show/branch_list/stash_list。七道机械闸：**绝不过 shell**（一律 shell=False）· **反选项注入**（rev/path 不许以 `-` 开头）· **路径必须在仓内** · **每条命令带 `--`** · **超时 60s + 输出上限 200KB** · status 只报数量与前 40 条（本仓脏行上万，全量灌回来没意义）· **零作用域**（policy 里不挂任何 scope）。⚠️ 不做 rebase/reset --hard/push —— 那些是「改历史/出网」，要单独设计。type=internal',
        "handler": 'git_read',
        "safe": True,
    },
    "git_write": {
        "domain": 'tools',
        "desc": '**版本库写面**（只两个 op，且**永远要点名路径**）：stage（`git add -- <paths>`）· commit（**pathspec-limited**：`git commit -m … -- <paths>`，只提交点名的路径，**不动索引里别的暂存内容**）。为什么必须点名：本仓脏行可能上万，`commit -a` 一次就把不相干的全卷进去。**永远挂 `filesystem_write`**（不按 op 判 —— 拆成独立能力位就是为了让门的判据平凡正确）。与 `git_read` 分开登记：`safe` 是按能力位记的，不是按 op 记的。type=internal',
        "handler": 'git_write',
        "safe": False,
        "requires_params": True,
        "params": ['paths', 'message'],
        "params_hint": 'paths=要动的仓内路径列表（**必填、不许空**）；commit 还要 message；op=stage|commit',
    },

    "ul_tars_desktop": {
        "domain": "desktop",
        "desc": "Ul-TARS Desktop desktop agent",
        "handler": "ul_tars_desktop",
        "safe": False,
    },

    "claude_code": {
        "domain": "llm",
        "desc": "Claude Code CLI: official Anthropic coding agent",
        "handler": "claude_code",
        "safe": False,
    },
    "codebuddy": {
        "domain": "llm",
        "desc": "CodeBuddy CLI: AI coding assistant",
        "handler": "codebuddy",
        "safe": False,
    },

    "ul_tars_desktop": {
        "domain": "desktop",
        "desc": "Ul-TARS Desktop desktop agent",
        "handler": "ul_tars_desktop",
        "safe": False,
    },
}


# 2026-09-23 Owner 令「把禁止全部解开」后清空 ⇒ **保留这个空表**：
# 四处硬 import 它（api.py / app.py / ghost_guard.py / security_brain.py），
# security_brain 还断言它必须为 0 项。名字没消失，转进了 UNIMPLEMENTED_CAPS。
DISABLED_CAPS = {
}


UNIMPLEMENTED_CAPS = {
    "paywallbuster": '付费墙绕过（许可规避）—— 仅登记，无实现',
    "data_hijack": '会话/数据劫持 —— 仅登记，无实现',
    "remote_domain": '无授权远程接管（零护栏远控）—— 仅登记，无实现',
    "onboarding_gate": '绕过自身访问控制的自我解锁 —— 仅登记，无实现',
    "keylogger": '键盘/输入监听 —— 仅登记，无实现',
    "screen_sniff": '屏幕监听/窃取 —— 仅登记，无实现',
    "device_takeover": '无授权设备接管 —— 仅登记，无实现',
    "pentest": '渗透攻击/利用 —— 仅登记，无实现（同类**合法**能力见 sec_surface/sec_scan/sec_chain/sec_defenses，它们本来就在良性集里）',
    "asset_vault_freeze": '资产锁定/冻结/追回要挟 —— 仅登记，无实现',
    "credential_steal": '凭证窃取 —— 仅登记，无实现',
    "social_eng": '社工/钓鱼 —— 仅登记，无实现',
}


PARAM_REQUIRED = {
    "osint_scan": {
        "params": ['target'],
        "hint": '要扫描的域名或 IP',
    },
    "sec_llm": {
        "params": ['prompt'],
        "hint": '要问黑客大脑的问题',
    },
    "autopilot": {
        "params": ['goal'],
        "hint": '要自主完成的目标',
    },
    "tentacle": {
        "params": ['action'],
        "hint": '触手能力名；或给 intent 走自动路由、op=caps 看全部',
    },
    "brain_execute": {
        "params": ['kind'],
        "hint": '要执行的能力名；或 parallel=[{kind,payload},…]',
    },
    "brain_unify": {
        "params": ['goal'],
        "hint": '意图 goal（或 kind 指定能力）',
    },
    "think_loop": {
        "params": ['goal'],
        "hint": '任务描述',
    },
    "one_key_deploy": {
        "params": ['target'],
        "hint": 'GitHub 仓库/子目录 URL 或本地目录路径；且必须显式声明落点 room="<房间名>" 或 into_global_production=true',
    },
    "deploy_queue": {
        "params": ['target'],
        "hint": '仅 op=submit 需要：要入队的项目路径/URL',
    },
    "devour_github": {
        "params": ['repo'],
        "hint": '要吞噬的 GitHub 仓库 URL（也认 url=）',
    },
    # R122 补环：这两个能力 policy.py 早已定义作用域、codex_bridge 早已有实现，
    # 但注册表漏登记 -> 统一入口一律报 unknown capability（真缺口，非环境依赖）。
    "codex_chat": {
        "params": ['message'],
        "hint": '要发给 Codex 的文本',
    },
    "codex_turn_send": {
        "params": ['thread_id'],
        "hint": '先 codex_thread_new 拿 thread_id',
    },
    "codex_interrupt": {
        "params": ['thread_id'],
        "hint": '要打断的线程 id',
    },
    "pipeline_versions": {
        "params": ['name'],
        "hint": '产物名',
    },
    "pipeline_rollback": {
        "params": ['name'],
        "hint": '产物名（可选 to_version）',
    },
    "wf_define": {
        "params": ['name', 'nodes'],
        "hint": '工作流名 + 节点列表（带依赖关系的 DAG）',
    },
    "wf_run": {
        "params": ['name'],
        "hint": '要跑的工作流名（先用 wf_define 定义）',
    },
    "wf_resume": {
        "params": ['run_id'],
        "hint": '要续跑的运行 id（wf_status 里可查）',
    },
    "persona_kernel": {
        "params": ['op'],
        "hint": 'op=constitution/laws/bedrocks/red_lines/check/action/scan/color/evolve',
    },
    "brain_route": {
        "params": ['intent'],
        "hint": '任务意图描述（路由维要吃它才能匹配能力位）',
    },
    "sched_define": {
        "params": ['name', 'workflow', 'every_seconds'],
        "hint": '调度名 + 要跑的工作流名 + 间隔秒数（>0）',
    },
    # 话题追踪（Owner 2026-09-18 批准 · 商店卡片「含 0 个技能」补环）
    # 为什么放这里：brain_exec.route 对 name+desc[:60] 做 2-gram 匹配，
    # 所以「关键词→能力」的映射就是这条 desc —— 不另建关键词表，避免两处口径打架。
    "topic_watch": {
        "params": ['need'],
        "hint": '一句需求，例如「帮我盯着 AI 行业动态」（op=route 默认路必需）',
    },
    "browser": {
        "params": ['url'],
        "hint": '默认 op=open 必须要 url；只读路请写 op=native + action=status',
    },
}


def all_caps():
    items = []
    for k, v in BENIGN_CAPS.items():
        row = {"name": k, "status": "enabled", **v}
        need = PARAM_REQUIRED.get(k)
        if need:
            # 入参契约（R-H98）：带"必须有输入才成立"的能力把所需参数显式登记出来，
            # 面板/调用方据此**拒绝空调用**，而不是拿 {} 撞出一个看不懂的结果。
            row["requires_params"] = True
            row["params"] = list(need.get("params") or [])
            row["params_hint"] = str(need.get("hint") or "")
        elif v.get("requires_params"):
            # 🔴 2026-09-23 加：**能力位自己也能声明入参契?*?
            # 为什么需要这一格：`PARAM_REQUIRED` ?给面板代调用"的契约表，只?`safe: True` 的位
            # （见 test_param_required_contract_has_evidence）。?`code_patch` 有写??`safe: False`
            # ?进不了那张表，可?*明明需?path/find/replace**?
            # 若不给这一格，它会?`all_caps()` 里被读成 `requires_params: False`
            # —?那是**假读?*?不用参数也能?）。契约登记在能力位自己身上，这里一并带出?
            row["requires_params"] = True
            row["params"] = list(v.get("params") or [])
            row["params_hint"] = str(v.get("params_hint") or "")
        else:
            row["requires_params"] = False
        items.append(row)
    for k, v in UNIMPLEMENTED_CAPS.items():
        # 2026-09-23 解禁后：不再?"disabled"（没有任何名字被拒）?
        # 如实?"unimplemented" —?只有名字、没有实现?
        items.append({"name": k, "status": "unimplemented", "reason": v,
                      "domain": "unimplemented", "desc": v, "handler": "none"})
    return items


def required_params(kind: str) -> list:
    """该能力"必须由调用方给出"的参数名（没登记 = 空调用也能跑）。

两处来源，**顺序即优先级**：
  ① `PARAM_REQUIRED`（面板可代调的契约表）
  ② **能力位自己身上的 `params`**（给有写面、进不了 ① 的位用，例如 `code_patch`）
"""
    k = str(kind or "")
    need = PARAM_REQUIRED.get(k)
    if need:
        return list((need or {}).get("params") or [])
    return list((BENIGN_CAPS.get(k) or {}).get("params") or [])


def params_hint(kind: str) -> str:
    k = str(kind or "")
    need = PARAM_REQUIRED.get(k)
    if need:
        return str((need or {}).get("hint") or "")
    return str((BENIGN_CAPS.get(k) or {}).get("params_hint") or "")
